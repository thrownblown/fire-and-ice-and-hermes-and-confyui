"""Does a rendered clip actually show the cast its prompt claims, shot by shot?

The prompt for an audio-only chunk states, per shot, "On screen in this shot: exactly N person(s) ...
(this is NAME)". Nothing checked that the render honoured it — motion QC passes happily on a clip
where three people stand in a shot the prompt says holds one (measured 2026-11-05, take 6 of S03).

Method, per `vlm-image-labeling`:
  * sample one frame at each shot's midpoint (midpoints from `shots.jsonl` PTS minus the chunk's first
    shot start, so shot 1 is always at 0 s of the clip);
  * ask the local VLM for PHYSICAL OBSERVATIONS ONLY — count, and per person sex/hair/clothing — with
    a fixed system prompt that forbids names, actors and film titles. A VLM asked for names invents
    them: the 8B called a 1983 cel frame "The Lion King, 95% confident, the character is Zazu" and this
    project's own render "The Huntsman: Winter's War, Charlize Theron and Chris Hemsworth". That
    invention is expected and harmless ONLY as long as nothing downstream reads its names — the counts
    and attribute descriptions are the signal, and identity is mapped by our own tables;
  * compare the count with the number the prompt claims for that shot.

Calls are strictly serial (one resident model; parallel calls contend and drop) and cached per frame
file, so re-running after a prompt rebuild costs nothing.

Usage:
  python tools/vlm_cast_check.py --clip <file.mp4> --chunk S03-c01            # one clip
  python tools/vlm_cast_check.py --clip <a.mp4> --chunk S03-c01 --clip <b.mp4> --chunk S03-c02
  python tools/vlm_cast_check.py --clip ... --chunk ... --frames-dir <dir>   # keep the frames
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import gf_client as gf  # noqa: E402  — goldfishbowl transport (alias + bearer)

# Backend: local LM Studio 8B by default (cheap, cached). Set FNI_CAST_BACKEND=goldfishbowl to
# judge with goldfishbowl's audit-grade 32B — its designated description-only frame reader — which
# is the right reader for a QC pass that decides whether a take gets re-rendered. The cache key
# includes MODEL (see below), so switching readers never reuses the other reader's verdicts.
BACKEND = (os.environ.get("FNI_CAST_BACKEND") or "lmstudio").lower()
MODEL = os.environ.get("FNI_CAST_MODEL") or (
    "qwen3-32b-vision-large" if BACKEND == "goldfishbowl"
    else "qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s")
ENDPOINT = os.environ.get("FNI_CAST_ENDPOINT", "http://127.0.0.1:1234/v1/chat/completions")
CACHE = ROOT / "runs" / "vlm_cast_cache.jsonl"
LEDGER = ROOT / "runs" / "vlm_cast_check.jsonl"

SYSTEM = (
    "Describe only what is visually present. Report the number of people and, for each, their sex, "
    "build, hair and clothing. NEVER name characters, actors, film titles, franchises or artists — "
    "physical attributes only. If a region is unclear, say unclear. "
    'Reply with strict JSON only: {"count": int, "people": [{"sex": str, "hair": str, "clothing": str}]}'
)


# One sample per item cannot separate a real effect from noise (goldfishbowl, inbox 2026-11-05 (9):
# "one pass per frame is not a measurement"), and temperature 0 is NOT deterministic on GPU with
# batching. So a decision-driving verdict is the MAJORITY of N samples across this ladder, and the
# agreement fraction is reported with it; below 4/5 the verdict is UNSTABLE and must not become a
# ledger fact.
TEMP_LADDER = [0.0, 0.3, 0.7, 1.0, 0.3]


def load_cache() -> dict:
    if not CACHE.exists():
        return {}
    out = {}
    for line in CACHE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["key"]] = r
    return out


def ask(frame: Path, temperature: float = 0.0) -> dict:
    """One VLM read. Transient 400/429/5xx are RETRIED, not treated as a verdict.

    Found 2026-11-08: the same request on the same frame returned HTTP 400 five times in a row, then
    succeeded on a re-run minutes later (LM Studio briefly busy/reloading). A transient backend fault
    must not silently become an UNCHECKED shot, so retry before giving up.
    """
    last = None
    for attempt in range(3):
        try:
            return _ask_once(frame, temperature)
        except urllib.error.HTTPError as e:
            last = e
            if e.code not in (400, 408, 409, 425, 429, 500, 502, 503, 504):
                raise
        except urllib.error.URLError as e:
            last = e
        time.sleep(2 * (attempt + 1))
    raise last if last else RuntimeError("ask failed")


def _ask_once(frame: Path, temperature: float = 0.0) -> dict:
    if BACKEND == "goldfishbowl":
        txt = gf.chat(MODEL, "How many people are in this frame?", system=SYSTEM,
                      images=[str(frame)], temperature=temperature, max_tokens=700, timeout=900)
    else:
        b64 = base64.b64encode(frame.read_bytes()).decode()
        body = {"model": MODEL, "temperature": temperature, "max_tokens": 700,
                "messages": [{"role": "system", "content": SYSTEM},
                             {"role": "user", "content": [
                                 {"type": "text", "text": "How many people are in this frame?"},
                                 {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}]}
        req = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=900) as r:
            txt = json.load(r)["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", txt, re.S)
    parsed = json.loads(m.group(0)) if m else None
    return {"raw": txt, "json": parsed}


def shot_midpoints(chunk: str) -> list[tuple[str, float]]:
    shots = {s["shot_id"]: s for s in
             (json.loads(l) for l in (ROOT / "shots.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}
    rows = [json.loads(l) for l in (ROOT / "fullrun" / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
            if l.strip()]
    row = next((r for r in rows if r["chunk_id"] == chunk), None)
    if not row:
        raise SystemExit(f"chunk {chunk} not in fullrun/chunks.jsonl")
    ids = row["shots"]
    t0 = shots[ids[0]]["start_pts"] / 24000
    return [(sid, ((shots[sid]["start_pts"] / 24000 - t0) + (shots[sid]["end_pts"] / 24000 - t0)) / 2)
            for sid in ids]


def claimed_counts(chunk: str, take: str) -> dict[str, int]:
    """What the queued prompt claims per shot — FROM THE LEDGER, not from prompt prose.

    The ledger carries `shot_nums` and `people_count` as aligned lists, which is data. Reading the
    claim out of the prompt text was tried twice and failed twice: the corpus says it per-shot
    ('[Shot N] ... exactly N people'), as one global line ('There is one person visible in all
    frames'), and sometimes not at all — and every miss surfaced as `claimed: None`, i.e. a verdict
    that quietly could not be checked (S02-c02 measured 3/9/17 against a ledger of 3/0/12 while the
    prose parse returned nothing at all).

    Shot numbers here are the GLOBAL 5-digit shot ids, which is also what shot_midpoints() yields,
    so no translation is needed. FNI_CHUNK_LEDGER selects the ledger, same as the renderer.
    """
    import os
    cand = os.environ.get("FNI_CHUNK_LEDGER") or ""
    paths = ([ROOT / cand] if cand else []) + [ROOT / "fullrun" / "chunks_named.jsonl",
                                               ROOT / "fullrun" / "chunks.jsonl"]
    for p in paths:
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("chunk_id") != chunk:
                continue
            nums, counts = r.get("shot_nums") or [], r.get("people_count") or []
            out = {}
            for i, num in enumerate(nums):
                if i < len(counts) and counts[i] is not None:
                    out["shot:%s" % num] = int(counts[i])
            if out:
                return out
    # last resort: the old prose parse, per-shot then the single global claim
    t = f"{int(take):02d}" if str(take).strip().isdigit() else take
    gdir = ROOT / "runs" / "T0016_s05_technicolor-audio-only-ref2va" / "graphs"
    pat = re.compile(r"^%s_audioOnly_t0*%s(?:_s\d+)?\.json$" % (re.escape(chunk), str(t)))
    cands = [p for p in gdir.glob(f"{chunk}_audioOnly_t*.json") if pat.match(p.name)]
    g = (max(cands, key=lambda p: p.stat().st_mtime) if cands else gdir / f"{chunk}_audioOnly_t{t}.json")
    if not g.exists():
        return {}
    data = json.loads(g.read_text(encoding="utf-8"))
    texts = [v["inputs"][k] for v in data.values() if isinstance(v, dict)
             for k in (v.get("inputs") or {}) if isinstance(v["inputs"][k], str)]
    txt = max(texts, key=len) if texts else ""
    out = {}
    ids = [sid for sid, _ in shot_midpoints(chunk)]
    g2 = re.search(r"There (?:is|are) (\d+|one|two|three|four|five) (?:person|people) visible", txt)
    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
    if g2:
        n = words.get(g2.group(1)) or (int(g2.group(1)) if g2.group(1).isdigit() else None)
        if n is not None:
            out = {sid: n for sid in ids}
    for i, sid in enumerate(ids, 1):
        m = re.search(rf"\[Shot {i}\][^\[]*?exactly (\d+) (?:person|people)", txt)
        if m:
            out[sid] = int(m.group(1))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip", action="append", required=True)
    ap.add_argument("--chunk", action="append", required=True)
    ap.add_argument("--take", action="append", default=[])
    ap.add_argument("--frames-dir", default="")
    ap.add_argument("--samples", type=int, default=5,
                    help="VLM samples per shot across TEMP_LADDER; the verdict is the MAJORITY and "
                         "agreement is reported. Below 4/5 the verdict is UNSTABLE. --samples 1 restores "
                         "the old single-pass behaviour (which goldfishbowl's inbox calls unmeasured).")
    args = ap.parse_args()
    if len(args.clip) != len(args.chunk):
        raise SystemExit("--clip and --chunk must be paired")
    takes = args.take or ["?"] * len(args.clip)

    cache = load_cache()
    rows = []
    for clip, chunk, take in zip(args.clip, args.chunk, takes):
        clip_p = Path(clip)
        if not clip_p.exists():
            print(f"  {clip}: MISSING (nothing checked)")
            continue
        outdir = Path(args.frames_dir) if args.frames_dir else Path(
            rf"C:/Users/gsfny/AppData/Local/Temp/vlm_cast/{clip_p.stem}")
        outdir.mkdir(parents=True, exist_ok=True)
        claimed = claimed_counts(chunk, take) if take != "?" else {}
        mids = shot_midpoints(chunk)
        print(f"\n{clip_p.name}  ({chunk}, take {take})")
        for sid, mid in mids:
            # A colon is ILLEGAL in a Windows filename, so `shot:00031.jpg` silently truncates to a
            # 0-byte file called `shot` — the VLM then answers a BLIND frame and returns a confident
            # count (measured 2026-11-08: counts=[6,6,6,6,6] — 5/5 agreement on an empty image, which
            # is why agreement alone is not a validity check). Sanitize, and guard the input below.
            frame = outdir / f"{sid.replace(':', '_')}.jpg"
            if not frame.exists():
                subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{mid:.2f}",
                                "-i", str(clip_p), "-frames:v", "1", "-q:v", "3", str(frame), "-y"],
                               check=False)
            if not frame.exists() or frame.stat().st_size < 1024:
                print(f"    {sid}  NO_FRAME  ({'missing' if not frame.exists() else '0-byte'}) — "
                      f"an empty frame must never produce a verdict")
                rows.append({"clip": str(clip_p), "chunk": chunk, "take": take, "shot": sid,
                             "claimed": claimed.get(sid), "observed": None, "verdict": "NO_FRAME",
                             "samples": 0, "agreement": 0.0, "counts": [],
                             "people": [], "frame": str(frame), "model": MODEL})
                continue
            stamp = frame.stat().st_mtime_ns if frame.exists() else 0
            samples, counts = [], []
            for t in TEMP_LADDER[:max(1, args.samples)]:
                k = f"{frame.name}:{stamp}:{MODEL}:t{t}"
                hit = cache.get(k)
                if hit is None:
                    try:
                        hit = {"key": k, "frame": str(frame), "temp": t, **ask(frame, t)}
                        with CACHE.open("a", encoding="utf-8") as fh:
                            fh.write(json.dumps(hit, ensure_ascii=False) + "\n")
                        cache[k] = hit
                    except Exception as e:  # noqa: BLE001
                        print(f"    {sid}: VLM ERROR at t={t} {type(e).__name__}: {str(e)[:100]}")
                        continue
                samples.append(hit)
                c = (hit.get("json") or {}).get("count")
                if c is not None:
                    counts.append(int(c))
            # MAJORITY verdict + agreement fraction, never the first answer
            got, agreement, hit = None, 0.0, samples[0] if samples else {}
            if counts:
                got = max(set(counts), key=counts.count)
                agreement = counts.count(got) / len(samples)
                hit = next((s for s in samples if (s.get("json") or {}).get("count") == got), hit)
            want = claimed.get(sid)
            if want is None or got is None:
                verdict = "UNCHECKED"      # never report an unchecked shot as agreement
            elif args.samples > 1 and agreement < 0.8:
                verdict = "UNSTABLE"       # <4/5 agreement: not a fact, feed it a better frame
            else:
                verdict = "OK" if int(got) == int(want) else "MISMATCH"
            ppl = (hit.get("json") or {}).get("people") or []
            desc = " | ".join(f"{(p.get('sex') or '?')}, {p.get('hair') or '?'}, {p.get('clothing') or '?'}"
                              for p in ppl[:4])
            print(f"    {sid}  prompt says {want}  frame shows {got}  "
                  f"[{counts.count(got) if counts else 0}/{len(samples)} agree]  -> {verdict}")
            if desc:
                print(f"        {desc[:220]}")
            rows.append({"clip": str(clip_p), "chunk": chunk, "take": take, "shot": sid,
                         "claimed": want, "observed": got, "verdict": verdict,
                         "samples": len(samples), "agreement": round(agreement, 2), "counts": counts,
                         "people": ppl, "frame": str(frame), "model": MODEL})

    if rows:
        with LEDGER.open("a", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        bad = [r for r in rows if r["verdict"] == "MISMATCH"]
        unknown = [r for r in rows if r["verdict"] == "UNCHECKED"]
        unstable = [r for r in rows if r["verdict"] == "UNSTABLE"]
        noframe = [r for r in rows if r["verdict"] == "NO_FRAME"]
        print(f"\n{len(rows)} shot(s): {len(rows)-len(bad)-len(unknown)-len(unstable)-len(noframe)} ok, "
              f"{len(bad)} mismatch, {len(unstable)} unstable, {len(noframe)} NO_FRAME, "
              f"{len(unknown)} unchecked -> {LEDGER}")
        if noframe:
            print("  NO_FRAME = the extracted still was missing or empty, so the VLM never saw an image "
                  "— a verdict there would be invention, not observation (found 2026-11-08: a colon in "
                  "the frame name truncated every still to 0 bytes and the VLM answered 5/5 anyway)")
        if unstable:
            print(f"  {len(unstable)} shot(s) below 4/5 agreement — ambiguous frames, NOT facts: "
                  + ", ".join(r["shot"] for r in unstable[:8]))
        if unknown:
            print("  a shot is UNCHECKED when the prompt's claimed count could not be read — that is "
                  "not agreement, fix the prompt record before reading this as a pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
