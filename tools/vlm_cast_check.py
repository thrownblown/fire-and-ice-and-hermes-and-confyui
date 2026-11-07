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


def load_cache() -> dict:
    if not CACHE.exists():
        return {}
    out = {}
    for line in CACHE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["key"]] = r
    return out


def ask(frame: Path) -> dict:
    if BACKEND == "goldfishbowl":
        txt = gf.chat(MODEL, "How many people are in this frame?", system=SYSTEM,
                      images=[str(frame)], temperature=0.0, max_tokens=700, timeout=900)
    else:
        b64 = base64.b64encode(frame.read_bytes()).decode()
        body = {"model": MODEL, "temperature": 0.0, "max_tokens": 700,
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
    """What the queued prompt says per shot — from the graph it actually rendered."""
    t = f"{int(take):02d}" if str(take).strip().isdigit() else take   # files are zero-padded: _t06
    gdir = ROOT / "runs" / "T0016_s05_technicolor-audio-only-ref2va" / "graphs"
    # An explicit --seed lands in the graph name too (`_t02_s<seed>.json`), so match by take with
    # an optional seed suffix and prefer the newest — that is the graph the take actually rendered.
    pat = re.compile(r"^%s_audioOnly_t0*%s(?:_s\d+)?\.json$" % (re.escape(chunk), str(t)))
    cands = [p for p in gdir.glob(f"{chunk}_audioOnly_t*.json") if pat.match(p.name)]
    g = (max(cands, key=lambda p: p.stat().st_mtime) if cands
         else gdir / f"{chunk}_audioOnly_t{t}.json")
    if not g.exists():
        return {}
    data = json.loads(g.read_text(encoding="utf-8"))
    texts = [v["inputs"][k] for v in data.values() if isinstance(v, dict)
             for k in (v.get("inputs") or {}) if isinstance(v["inputs"][k], str)]
    txt = max(texts, key=len) if texts else ""
    out = {}
    ids = [sid for sid, _ in shot_midpoints(chunk)]
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
            frame = outdir / f"{sid}.jpg"
            if not frame.exists():
                subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{mid:.2f}",
                                "-i", str(clip_p), "-frames:v", "1", "-q:v", "3", str(frame), "-y"],
                               check=False)
            key = f"{frame.name}:{frame.stat().st_mtime_ns if frame.exists() else 0}:{MODEL}"
            hit = cache.get(key)
            if hit is None:
                try:
                    hit = {"key": key, "frame": str(frame), **ask(frame)}
                    with CACHE.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps(hit, ensure_ascii=False) + "\n")
                    cache[key] = hit
                except Exception as e:  # noqa: BLE001
                    print(f"    {sid}: VLM ERROR {type(e).__name__}: {str(e)[:120]}")
                    continue
            got = (hit.get("json") or {}).get("count")
            want = claimed.get(sid)
            if want is None or got is None:
                verdict = "UNCHECKED"      # never report an unchecked shot as agreement
            else:
                verdict = "OK" if int(got) == int(want) else "MISMATCH"
            ppl = (hit.get("json") or {}).get("people") or []
            desc = " | ".join(f"{(p.get('sex') or '?')}, {p.get('hair') or '?'}, {p.get('clothing') or '?'}"
                              for p in ppl[:4])
            print(f"    {sid}  prompt says {want}  frame shows {got}  -> {verdict}")
            if desc:
                print(f"        {desc[:220]}")
            rows.append({"clip": str(clip_p), "chunk": chunk, "take": take, "shot": sid,
                         "claimed": want, "observed": got, "verdict": verdict,
                         "people": ppl, "frame": str(frame), "model": MODEL})

    if rows:
        with LEDGER.open("a", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        bad = [r for r in rows if r["verdict"] == "MISMATCH"]
        unknown = [r for r in rows if r["verdict"] == "UNCHECKED"]
        print(f"\n{len(rows)} shot(s): {len(rows)-len(bad)-len(unknown)} ok, {len(bad)} mismatch, "
              f"{len(unknown)} unchecked -> {LEDGER}")
        if unknown:
            print("  a shot is UNCHECKED when the prompt's claimed count could not be read — that is "
                  "not agreement, fix the prompt record before reading this as a pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
