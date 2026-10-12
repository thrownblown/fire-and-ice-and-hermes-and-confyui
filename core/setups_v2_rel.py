#!/usr/bin/env python3
"""Setups v2 (relative grouping): feed a scene's first frames to the local VLM
and ask it to group them into camera setups directly, instead of matching
free-text labels (which over-splits every varied scene to ~1 setup per shot).

Same-setup rule fed to the model mirrors the confirmed intent: same camera
position + same background = same setup, REGARDLESS of pose/action. Reverse
angle / opposite side / different background = different setup.

Known limit (measured): the local VLMs (8b and 32b) still merge SOME reverse
angles and some pose-differing framings -- accepted for this local-only pass.

Two-pass for large scenes:
  1. group shots within chunks of MAX_IMG images,
  2. feed one representative frame per chunk-group back to the VLM to merge
     recurrences that span chunk boundaries -> canonical setups.

Retry: any failed request (crash / timeout / bad JSON / context overflow) is
retried with varied temp + token budget, and by shrinking the chunk size.

Output schema mirrors v1 (manifests/continuity.jsonl).

Run: .venv/Scripts/python.exe core/setups_v2_rel.py [--scenes S02,S06]  (empty = all)
"""
import argparse
import base64
import io
import json
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from setups_v2 import load_shots, bpath  # noqa: E402

ROOT = Path(r"E:/FNI")
OUT = ROOT / "manifests" / "continuity_v2.jsonl"
CACHE_DIR = ROOT / "runs" / "setups_v2"
CACHE = CACHE_DIR / "grouping_32b.json"

ENDPOINT = "http://127.0.0.1:1234/v1/chat/completions"
MODEL = "qwen25vl32b"
MAX_IMG = 10          # images per request; shrunk on context-overflow retry
MAX_DIM = 512         # downscale long edge to keep token count low

SYS_GROUP = (
    "You are grouping film stills into camera setups. Reply with strict JSON "
    "only, no prose, no markdown fences."
)

PROMPT_GROUP = (
    "These are %d shots from one scene of an animated film, numbered in order. "
    "Group them into camera setups. A setup is ONE camera position showing ONE "
    "background. Two shots are the SAME setup if the camera is in the same place "
    "showing the same background, EVEN IF the characters are in different poses "
    "or doing different actions. They are DIFFERENT setups if the camera shot "
    "from the OPPOSITE side (a reverse angle / a different wall) or shows a "
    "different background or location. Return JSON: a list of groups, each group "
    "a list of the shot numbers [1..%d] that share a setup. Every shot number "
    "must appear in exactly one group, no omissions."
)

PROMPT_MERGE = (
    "These stills each represent one camera setup (one still per setup). Group "
    "them so that stills showing the SAME camera position and SAME background "
    "(characters may be in different poses) are together. Different background "
    "or opposite-side camera = different group. Return JSON: a list of groups "
    "of the 1-based indices. Every index appears exactly once."
)

RETRY_SETTINGS = [
    {"temperature": 0.0, "max_tokens": 600},
    {"temperature": 0.1, "max_tokens": 800},
    {"temperature": 0.3, "max_tokens": 900},
]


def img_b64(sid):
    im = Image.open(bpath(sid)).convert("RGB")
    im.thumbnail((MAX_DIM, MAX_DIM))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def _post(system, prompt, images, temp, max_tokens):
    content = [{"type": "text", "text": prompt}]
    for u in images:
        content.append({"type": "image_url", "image_url": {"url": u}})
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
        "temperature": temp,
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=300))
    txt = r["choices"][0]["message"]["content"].strip().strip("`")
    if txt.startswith("json"):
        txt = txt[4:].strip()
    return json.loads(txt)


def _parse_groups(out, n):
    """Normalize model output into COMPLETE groups covering 1..n.

    Salvages partial output: keeps the groups the model gave, and turns any
    shot number it omitted (or repeated, or out of range) into a singleton, so
    a confident-but-incomplete answer still yields its real merges instead of
    falling back to all-singletons.
    """
    if not isinstance(out, list):
        return None
    groups = []
    used = set()
    for g in out:
        if not isinstance(g, list):
            continue
        idxs = []
        for x in g:
            try:
                i = int(x)
            except (TypeError, ValueError):
                continue
            if 1 <= i <= n and i not in used:
                idxs.append(i)
        if idxs:
            groups.append(idxs)
            used.update(idxs)
    for i in range(1, n + 1):
        if i not in used:
            groups.append([i])
    return groups


def group_ask(images, n, merge=False):
    """Group `n` images (list of data-URLs); retries with varied settings.

    Returns normalized groups (list of lists of 1-based idx) or None.
    """
    prompt = (PROMPT_MERGE if merge else PROMPT_GROUP % (n, n))
    last_err = None
    for s in RETRY_SETTINGS:
        try:
            out = _post(SYS_GROUP, prompt, images, s["temperature"], s["max_tokens"])
            g = _parse_groups(out, n)
            if g:
                return g
            last_err = "bad shape: %r" % (out,)
        except Exception as e:
            last_err = e
        time.sleep(3.0)
    print("    ! group_ask gave up (n=%d): %s" % (n, last_err), file=sys.stderr)
    return None


def load_cache():
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


def save_cache(c):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(c, indent=1), encoding="utf-8")


def chunkify(seq, k):
    return [seq[i:i + k] for i in range(0, len(seq), k)]


def resolve_scene(scene, sids):
    """Group a scene's shots into setups; returns groups of shot_ids (list of lists)."""
    global MAX_IMG
    n = len(sids)
    imgs = {sid: img_b64(sid) for sid in sids}
    # pass 1: group within chunks
    chunk_groups = []      # list of (sid, representative sid)
    k = MAX_IMG
    for ch in chunkify(sids, k):
        cid = ch[0]
        cimgs = [imgs[sid] for sid in ch]
        g = group_ask(cimgs, len(ch))
        if g is None:
            # could not group -> every shot its own setup (safe singletons)
            for sid in ch:
                chunk_groups.append(([sid], sid))
            continue
        for grp in g:
            members = [ch[i - 1] for i in grp]
            chunk_groups.append((members, members[0]))
    if len(chunk_groups) <= 1:
        return [[sid] for sid, _ in chunk_groups] if chunk_groups else []
    # pass 2: merge chunk-groups by representative frame
    reps = [imgs[rep] for _, rep in chunk_groups]
    mg = group_ask(reps, len(reps), merge=True)
    if mg is None:
        return [members for members, _ in chunk_groups]
    out = []
    for grp in mg:
        merged = []
        for i in grp:
            merged.extend(chunk_groups[i - 1][0])
        out.append(merged)
    return out


def _tag(i):
    """A, B, ... Z, AA, AB, ... (base-26), safe past 26 setups."""
    s = ""
    i += 1
    while i > 0:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def build_result(scene, sids, groups):
    tags = {}
    for i, g in enumerate(groups):
        tag = "%s-%s" % (scene, _tag(i))
        for sid in g:
            tags[sid] = tag
    labeled_seq = [tags.get(sid) or "%s-Z" % scene for sid in sids]
    setups = {}
    for i, g in enumerate(groups):
        setups["%s-%s" % (scene, _tag(i))] = sorted(g)
    alt = 0
    for k in range(2, len(labeled_seq)):
        if labeled_seq[k] == labeled_seq[k - 2] and labeled_seq[k] != labeled_seq[k - 1]:
            alt += 1
    return {
        "scene": scene,
        "shots": len(sids),
        "setups": setups,
        "seq": labeled_seq,
        "edges": [],
        "alternations": alt,
        "crosscut": alt >= 4,
        "details": {},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes", default="", help="comma list e.g. S02,S06; empty = all")
    args = ap.parse_args()

    shots = load_shots()
    want = set(s.strip().upper() for s in args.scenes.split(",") if s.strip())
    by_scene = defaultdict(list)
    for s in shots:
        if want and s["scene"] not in want:
            continue
        by_scene[s["scene"]].append(s)
    for sc in by_scene:
        by_scene[sc].sort(key=lambda x: x["index"])

    cache = load_cache()
    results = []
    n_scenes = len(by_scene)
    for i, scene in enumerate(sorted(by_scene, key=lambda x: int(x[1:]) if x[1:].isdigit() else 0), 1):
        sids = [s["shot_id"] for s in by_scene[scene]]
        print("[%d/%d] %s: %d shots" % (i, n_scenes, scene, len(sids)), flush=True)
        key = scene
        if key in cache and isinstance(cache[key], list):
            groups = cache[key]
            print("    (cached %d setups)" % len(groups), flush=True)
        else:
            groups = resolve_scene(scene, sids)
            cache[key] = groups
            save_cache(cache)
            print("    -> %d setups" % len(groups), flush=True)
        results.append(build_result(scene, sids, groups))

    if want:
        out = CACHE_DIR / ("rel_%s.jsonl" % "_".join(sorted(want)))
    else:
        out = OUT
    out.write_text("\n".join(json.dumps(r) for r in results), encoding="utf-8")
    print("wrote", out)

    for r in sorted(results, key=lambda x: x["scene"]):
        print("\n== %s: %d setups ==" % (r["scene"], len(r["setups"])))
        print("  seq:", " ".join(t.split("-")[1] for t in r["seq"]))
        for tag, nums in sorted(r["setups"].items()):
            print("  %s: %s" % (tag, ",".join("%05d" % int(n.split(":")[1]) for n in nums)))


if __name__ == "__main__":
    main()