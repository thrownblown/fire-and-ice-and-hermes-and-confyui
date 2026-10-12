"""Build the T0013/T0014 plate-injection ref2va tests (approaches X3/X4).

X3 (T0013) = setup plate + ONE shot's video: render a setup's look from a short
  clip. X4 (T0014) = per-shot + shared plate: a single shot's video plus the
  setup's contact-sheet "master plate" image.

Both feed refrun's REF2VA path with:
  - ref video = a SINGLE member shot's clip (not the full setup concat),
  - the setup's plate image injected into the graph as an extra <Picture N>
    AFTER the stills (refrun.build_ref_graph(..., plate_names=[...])),
  - the shot's first still as the <Picture 1> anchor,
  - a retention line telling H3 the plate is a location collage (keep the
    environment, ignore the figures) — refrun.build_ref_prompt(..., plate_count=1).

DRY by default: builds prompt + graph, writes them, queues nothing. Pass --queue
to upload + queue. Do NOT queue until T0011/T0012 have a verdict
(docs/plans/setup-ref2va-tests.md "Don't").

Run:
  .venv/Scripts/python.exe runs/build_plate_ref2va_test.py --setup S06-A --shot 197 --seed 42
  .venv/Scripts/python.exe runs/build_plate_ref2va_test.py --t t0014 --setup S06-A --shot 197 --seed 42
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, r"E:/FNI/pipeline")  # fullrun.py/refrun.py live in pipeline/

import fullrun as F  # noqa: E402
import refrun as R  # noqa: E402

ROOT = Path(r"E:/FNI")

RUN_DIRS = {
    "t0013": "T0013_s06_setup-plate-shortvideo",
    "t0014": "T0014_s06_setup-pershot-plate",
}


def load_setup(setup_id):
    for l in (ROOT / "manifests" / "setups.jsonl").read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            if r["setup_id"] == setup_id:
                return r
    raise KeyError(setup_id)


def build_plate_row(test_id, setup_id, shot_num, seed, cap=15.0):
    """Single-shot row whose ref video is just shot_num's clip, plus the setup
    plate path. h3_seconds = the shot's own duration (the "short video" lever)."""
    setup = load_setup(setup_id)
    scene = setup["scene"]
    sid = f"shot:{shot_num:05d}"
    rows = [json.loads(l) for l in F.CHUNK_LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    smeta = {s["shot_id"]: s for s in F.jl(ROOT / "shots.jsonl")}

    stype, ang, mot = "medium", "eye-level", "static"
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
        if shot_num in rn:
            i = rn.index(shot_num)
            stype = st[i] if i < len(st) else "medium"
            ang = ag[i] if i < len(ag) else "eye-level"
            mot = mt[i] if i < len(mt) else "static"
        if set(rn) & {shot_num}:
            for s in r.get("speakers") or []:
                if s not in speakers:
                    speakers.append(s)
            line_ids.update(r.get("line_ids") or [])

    h3 = min(smeta[sid]["duration_seconds"], cap)
    return dict(
        chunk_id=f"{test_id}-{setup_id}-s{shot_num:03d}",
        scene=scene,
        shots=[sid],
        shot_nums=[f"{shot_num:05d}"],
        shot_type=[stype],
        angle=[ang],
        motion=[mot],
        speakers=speakers,
        stamped_names=[],
        line_ids=sorted(line_ids),
        location=loc or "",
        music=mus or "",
        h3_seconds=h3,
        h3_frames=round(h3 * 24),
        seed=seed,
        plate=ROOT / "refs" / "setups" / f"{setup_id}_plate.jpg",
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--t", choices=("t0013", "t0014"), default="t0013")
    ap.add_argument("--setup", required=True)
    ap.add_argument("--shot", type=int, required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--queue", action="store_true", help="upload + queue (default: dry)")
    args = ap.parse_args()

    run_dir = ROOT / "runs" / RUN_DIRS[args.t]
    row = build_plate_row(args.t.upper(), args.setup, args.shot, args.seed)
    print("plate row: chunk_id=%s shot=%s h3_seconds=%.2f plate=%s" % (
        row["chunk_id"], row["shot_nums"], row["h3_seconds"], row["plate"].name))

    if not R.build_ref_video(row):
        print("NO REF VIDEO (missing shot ref) — abort")
        return

    people, dialogue = R.load_context()
    caps = F.load_captions()
    text = R.build_ref_prompt(row, caps, people, dialogue, plate_count=1)
    for v in R.validate_ref_prompt(text):
        print("PROMPT violation:", v)

    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
    (run_dir / "graphs").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts" / f"{row['chunk_id']}.txt").write_text(text, encoding="utf-8")

    snum = row["shot_nums"][0]
    s = F.stills_for(snum)

    if not args.queue:
        # dry: build the graph against synthetic local names (no upload), inspect wiring
        still_names = [f"{row['chunk_id']}_{snum}_f00000.jpg"] if s else []
        g = R.build_ref_graph(row, still_names, plate_names=[row["plate"].name])
        g["138"]["inputs"]["value"] = text
        (run_dir / "graphs" / f"{row['chunk_id']}.json").write_text(json.dumps(g, indent=2))
        inputs = g["136"]["inputs"]
        n_img = sum(1 for k in inputs if k.startswith("ref_images.ref_image_"))
        print("DRY RUN OK — prompt + graph written, nothing queued")
        print("  still pics wired: %d   plate wired as ref_image_1: %s   total ref_images: %d" % (
            len(still_names), "ref_images.ref_image_1" in inputs, n_img))
        print("  prompt <Picture 2> (plate) present: %s   background_only present: %s" % (
            "<Picture 2>" in text, "background_only" in text))
        return

    # upload ref video + still + plate, then queue
    try:
        vname = F.upload(R.REFS / R.ref_video_name(row["chunk_id"]))
    except Exception as e:  # noqa: BLE001
        print("ref video upload failed:", e)
        return
    up_stills = []
    if s:
        try:
            up_stills.append(F.upload(s[0]))
        except Exception as e:  # noqa: BLE001
            print("still upload failed:", e)
    try:
        plate_name = F.upload(row["plate"])
    except Exception as e:  # noqa: BLE001
        print("plate upload failed:", e)
        return
    g = R.build_ref_graph(row, up_stills, plate_names=[plate_name])
    g["138"]["inputs"]["value"] = text
    (run_dir / "graphs" / f"{row['chunk_id']}.json").write_text(json.dumps(g, indent=2))
    try:
        F.api("/prompt", {"prompt": g}, timeout=90)
        print("QUEUED %s (%d stills + plate, video ref %s)" % (row["chunk_id"], len(up_stills), vname))
    except Exception as e:  # noqa: BLE001
        print("queue failed:", e)


if __name__ == "__main__":
    main()
