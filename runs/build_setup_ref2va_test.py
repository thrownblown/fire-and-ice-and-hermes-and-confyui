"""Render a camera SETUP (not a chronological chunk) through refrun's REF2VA path.

Builds a synthetic "chunk" row whose shots are one setup's member shots, then
reuses refrun's validated build_ref_video / build_ref_prompt / build_ref_graph
so the reference video is the concat of the setup's shots (all the same camera
angle) instead of refrun's default chronological mix.

This is T0012 (approach X2: setup stitched-video). See docs/plans/setup-ref2va-tests.md.

Run:
  .venv/Scripts/python.exe runs/build_setup_ref2va_test.py --setup S06-A --seed 42 --dry
  .venv/Scripts/python.exe runs/build_setup_ref2va_test.py --setup S06-A --seed 42
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, r"E:/FNI/pipeline")  # fullrun.py/refrun.py live in pipeline/ now

import fullrun as F
import refrun as R

ROOT = Path(r"E:/FNI")
RUN_DIR = ROOT / "runs" / "T0012_s06_setup-stitched-video"


def load_setups():
    recs = [json.loads(l) for l in (ROOT / "manifests" / "setups.jsonl")
            .read_text(encoding="utf-8").splitlines() if l.strip()]
    return {r["setup_id"]: r for r in recs}


def build_setup_row(setup_id, seed, cap=15.0):
    setup = load_setups()[setup_id]
    scene = setup["scene"]
    nums = [int(n) for n in setup["shot_nums"]]
    shots = [f"shot:{n:05d}" for n in nums]
    rows = [json.loads(l) for l in F.CHUNK_LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    smeta = {s["shot_id"]: s for s in F.jl(ROOT / "shots.jsonl")}

    stype, ang, mot = {}, {}, {}
    speakers, line_ids = [], set()
    loc = mus = None
    for r in rows:
        if r["scene"] != scene:
            continue
        loc = loc or r.get("location")
        mus = mus or r.get("music")
        rn = [int(x) for x in r["shot_nums"]]
        st = r.get("shot_type") or []
        ag = r.get("angle") or []
        mt = r.get("motion") or []
        for i, n in enumerate(rn):
            stype[n] = st[i] if i < len(st) else "medium"
            ang[n] = ag[i] if i < len(ag) else "eye-level"
            mot[n] = mt[i] if i < len(mt) else "static"
        if set(rn) & set(nums):
            for s in r.get("speakers") or []:
                if s not in speakers:
                    speakers.append(s)
            line_ids.update(r.get("line_ids") or [])

    total = sum(smeta[f"shot:{n:05d}"]["duration_seconds"] for n in nums)
    h3 = min(total, cap)
    return dict(
        chunk_id=f"setup-{setup_id}",
        scene=scene,
        shots=shots,
        shot_nums=[f"{n:05d}" for n in nums],
        shot_type=[stype.get(n, "medium") for n in nums],
        angle=[ang.get(n, "eye-level") for n in nums],
        motion=[mot.get(n, "static") for n in nums],
        speakers=speakers,
        stamped_names=[],
        line_ids=sorted(line_ids),
        location=loc or "",
        music=mus or "",
        h3_seconds=h3,
        h3_frames=round(h3 * 24),
        seed=seed,
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--setup", required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--cap", type=float, default=15.0)
    ap.add_argument("--dry", action="store_true", help="build prompt+graph, no queue")
    args = ap.parse_args()

    row = build_setup_row(args.setup, args.seed, args.cap)
    print("Setup row: chunk_id=%s shots=%s h3_seconds=%.2f speakers=%s" % (
        row["chunk_id"], row["shot_nums"], row["h3_seconds"], row["speakers"]))

    if not R.build_ref_video(row):
        print("NO REF VIDEO (missing member shots) — abort")
        return

    people, dialogue = R.load_context()
    caps = F.load_captions()
    text = R.build_ref_prompt(row, caps, people, dialogue)
    for v in R.validate_ref_prompt(text):
        print("PROMPT violation:", v)

    (RUN_DIR / "prompts").mkdir(parents=True, exist_ok=True)
    (RUN_DIR / "graphs").mkdir(parents=True, exist_ok=True)
    (RUN_DIR / "prompts" / f"{row['chunk_id']}.txt").write_text(text, encoding="utf-8")

    if args.dry:
        names = [f"{row['chunk_id']}_{snum}_f00000.jpg"
                 for snum in row["shot_nums"] if F.stills_for(snum)]
        g = R.build_ref_graph(row, names)
        g["138"]["inputs"]["value"] = text
        (RUN_DIR / "graphs" / f"{row['chunk_id']}.json").write_text(json.dumps(g, indent=2))
        print("DRY RUN OK — prompt + graph written, nothing queued")
        return

    # render: upload ref video + stills, then queue
    try:
        vname = F.upload(R.REFS / R.ref_video_name(row["chunk_id"]))
    except Exception as e:  # noqa: BLE001
        print("ref video upload failed:", e)
        return
    up_stills = []
    for snum in row["shot_nums"]:
        s = F.stills_for(snum)
        if s:
            try:
                up_stills.append(F.upload(s[0]))
            except Exception as e:  # noqa: BLE001
                print("still upload failed:", e)
    g = R.build_ref_graph(row, up_stills)
    g["138"]["inputs"]["value"] = text
    (RUN_DIR / "graphs" / f"{row['chunk_id']}.json").write_text(json.dumps(g, indent=2))
    try:
        F.api("/prompt", {"prompt": g}, timeout=90)
        print("QUEUED %s (%d stills, video ref %s)" % (row["chunk_id"], len(up_stills), vname))
    except Exception as e:  # noqa: BLE001
        print("queue failed:", e)


if __name__ == "__main__":
    main()