"""Render a scene chunk through REF2VA with the NEW technicolor refs swapped in.

Track A probe (first technicolor test video on the 5090). Unlike refrun's
default (per-shot 1983 source stills as <Picture N>), this feeds H3:
  - each on-screen character's GENERATED sheet as their identity <Picture N>,
  - the canonical location PLATE as an extra background_only <Picture>,
  - the chunk's concat source ref video for motion + original audio.

This is the direction doc's "style the endpoints first" consequence, now that the
technicolor sheets + plates exist. The question under test: does REF2VA hold the
live-action 80s register when the endpoint refs are technicolor (rather than
source rotoscope frames), or does the source <Video 1> drag it back to cel?

Reuses refrun.build_ref_graph + build_ref_video + validate_ref_prompt so the graph
and video wiring stay the single validated path. Dry by default.

Run:
  .venv/Scripts/python.exe runs/build_technicolor_ref2va.py --chunk S05-c01            # dry
  .venv/Scripts/python.exe runs/build_technicolor_ref2va.py --chunk S05-c01 --queue
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, r"E:/FNI/pipeline")

import fullrun as F  # noqa: E402
import refrun as R  # noqa: E402

ROOT = Path(r"E:/FNI")
RUN_DIR = ROOT / "runs" / "T0015_s05_technicolor-sheets-ref2va"

# canonical traits (technicolor register) — do not re-derive from VLM/captions
TRAITS = {
    "TEEGRA": "very long black hair, pale skin, green eyes, a lightweight purple "
              "two-piece costume, and a gold necklace",
    "TUTOR": "a black bob with bangs, light brown skin, a light blue bandeau top and "
             "skirt, and a broad gold collar and belt",
    "DARKWOLF": "deep tanned bronze skin, long black hair in braids, a wolf-head helmet, "
                "a bare oiled chest, and a fur-lined belt with bronze plates",
    "LARN": "blond braided hair, sun-tanned bronze skin, gold hoop earrings, a leather "
            "belt with a gold buckle, and a bone necklace",
    "JULIANA": "pale skin, very long straight jet-black hair, and a deep purple gown",
    "NEKRON": "very long white hair, pale skin, and dark purple robes",
    "JAROL": "a bald head, a long white beard, and a red tunic with gold accents",
    "TARO": "long straight black hair, a red vest, and gold armbands",
    "ROLIEL": "long red hair, pale skin, a flowing white robe, and blue jewellery",
    "OTWA": "long red hair, a gaunt weathered face, and a brown loincloth",
    "SHAITAN": "a large black panther with yellow eyes and white whiskers",
    "SPIRIT": "a skeletal figure with long white hair and a black garment",
}

# location plate per scene (slug in refs/backgrounds/)
PLATE = {
    "S05": "fire-keep-chamber",       # royal bedchamber (Teegra lounging), not the study
    "S03": "ice-peak-throne-hall",
    "S06": "fire-keep-throne-hall",
}


def sheet_path(name: str) -> Path | None:
    d = ROOT / "refs" / "characters" / name
    for p in sorted(d.glob(f"{name}_sheet_t*.png")):
        return p
    return None


def plate_path(slug: str) -> Path | None:
    d = ROOT / "refs" / "backgrounds" / slug
    for p in sorted(d.glob(f"{slug}_plate_t*.png")):
        return p
    return None


def build_sheet_prompt(row, subjects, plate_count, dialogue, people) -> str:
    """6-field prompt whose subject pictures are the GENERATED sheets, not source stills."""
    n_sub = len(subjects)
    sd_lines = []
    for i, name in enumerate(subjects, 1):
        traits = TRAITS.get(name, "")
        sd_lines.append(f"<Subject {i}> is {name}, {traits}, shown in <Picture {i}>."
                        + (" She is the one in <Video 1>." if i == 1 else ""))
    sd = "\n".join(sd_lines)

    summ = ("[video editing + audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: "
            "a single continuous live-action scene preserving each character's appearance from "
            "their reference sheet and the timing, posture, and speech of the reference video.")

    rt_lines = []
    for i, name in enumerate(subjects, 1):
        rt_lines.append(f"<Subject {i}>: fully_preserved — keep {TRAITS.get(name, 'identity')} "
                        f"consistent across [Shot 1] and <Video 1>.")
    rt_lines.append("<Video 1>: attribute_transfer — carry the posture, facial performance, and "
                    "exact spoken dialogue and delivery into the clip.")
    rt_lines.append("Dialogue audio of <Video 1>: fully_copy — reuse the spoken lines and timing.")
    for k in range(plate_count):
        p = n_sub + k + 1
        rt_lines.append(f"<Picture {p}>: background_only — this is the location as a painted "
                        "environment, not people; keep ONLY the environment (layout, lighting, "
                        "color, architecture) and ignore any figures.")
    rt = "\n".join(rt_lines)

    style = F.style_line(row["location"])
    # one shot block per chunk shot, with dialogue assigned by midpoint (mirrors refrun)
    shot_lines = []
    sidx = {name: i + 1 for i, name in enumerate(subjects)}
    for idx, (sid, snum) in enumerate(zip(row["shots"], row["shot_nums"]), 1):
        comp = {"shot_type": row["shot_type"][idx - 1], "angle": row["angle"][idx - 1]}
        cam = F.camera_move(comp, idx, len(row["shots"]))
        bits = [f"[Shot {idx}] {cam}"]
        for lid in row["line_ids"]:
            r = dialogue.get(lid)
            if not r:
                continue
            mid = (F.sec(r["start"]) + F.sec(r["end"])) / 2
            if not (people.get(sid, {}).get("_t0", 0) <= mid < people.get(sid, {}).get("_t1", 0)):
                continue
            spk = r["speaker"]
            tag = f"(S{sidx.get(spk, 1)})"
            bits.append(f"<Subject {sidx.get(spk, 1)}> {tag} says: <d>[English] {r['text']}</d>")
        shot_lines.append(" ".join(b for b in bits if b))

    dd = f"{style}\n\n" + "\n\n".join(shot_lines)

    return "\n\n".join([
        f"# ref_video: {R.ref_video_name(row['chunk_id'])}",
        "subject_definitions:", sd, "",
        "summary:", summ, "",
        "retention_analysis:", rt, "",
        "detailed_description:", dd, "",
        "overall_soundscape:", F.soundscape_line(row), "",
        "non_diegetic_music:", F.music_line(row["music"]),
    ])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chunk", required=True)
    ap.add_argument("--queue", action="store_true", help="upload + queue (default dry)")
    args = ap.parse_args()

    rows = [json.loads(l) for l in F.CHUNK_LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    row = next(r for r in rows if r["chunk_id"] == args.chunk)

    # on-screen subjects: stamped names + speakers, in stable order, with a sheet on disk
    order = []
    for spk in row["speakers"]:
        if spk not in order:
            order.append(spk)
    for nm in row["stamped_names"]:
        if nm not in order:
            order.append(nm)
    subjects = [n for n in order if sheet_path(n)]
    if not subjects:
        print("no sheeted subjects for this chunk; abort")
        return

    scene = row["scene"]
    plate = plate_path(PLATE.get(scene, ""))
    plate_name = plate.name if plate else None
    plate_count = 1 if plate else 0

    if not R.build_ref_video(row):
        print("no ref video; abort")
        return

    people, dialogue = R.load_context()
    text = build_sheet_prompt(row, subjects, plate_count, dialogue, people)
    for v in R.validate_ref_prompt(text):
        print("PROMPT violation:", v)

    (RUN_DIR / "prompts").mkdir(parents=True, exist_ok=True)
    (RUN_DIR / "graphs").mkdir(parents=True, exist_ok=True)
    (RUN_DIR / "prompts" / f"{args.chunk}.txt").write_text(text, encoding="utf-8")

    sheet_names = [sheet_path(n).name for n in subjects]
    plates = [plate_name] if plate_name else []

    def _finish_graph(g, text):
        g["138"]["inputs"]["value"] = text
        g["92"]["inputs"]["filename_prefix"] = f"video/{args.chunk}_technicolor_t01"
        # identity fidelity: max, never match (see skill identity-anchors rule)
        g["136"]["inputs"]["ref_image_size"] = "max"
        return g

    if not args.queue:
        g = _finish_graph(R.build_ref_graph(row, sheet_names, plate_names=plates), text)
        (RUN_DIR / "graphs" / f"{args.chunk}.json").write_text(json.dumps(g, indent=2))
        inputs = g["136"]["inputs"]
        n_img = sum(1 for k in inputs if k.startswith("ref_images.ref_image_"))
        print("DRY RUN OK — nothing queued")
        print("  subjects:", subjects, "-> pictures 1..", len(subjects))
        print("  plate:", plate_name, "-> background_only picture", len(subjects) + 1)
        print("  ref video:", R.ref_video_name(row["chunk_id"]))
        print("  total ref_images:", n_img)
        return

    # upload: ref video, sheets, plate, then queue
    try:
        R.REFS.joinpath(R.ref_video_name(row["chunk_id"])).stat()
    except OSError:
        print("ref video missing; abort")
        return
    try:
        vname = F.upload(R.REFS / R.ref_video_name(row["chunk_id"]))
    except Exception as e:  # noqa: BLE001
        print("ref video upload failed:", e)
        return
    up_sheets = []
    for n in subjects:
        try:
            up_sheets.append(F.upload(sheet_path(n)))
        except Exception as e:  # noqa: BLE001
            print(f"sheet upload failed ({n}):", e)
    up_plates = []
    if plate:
        try:
            up_plates.append(F.upload(plate))
        except Exception as e:  # noqa: BLE001
            print("plate upload failed:", e)

    g = _finish_graph(R.build_ref_graph(row, up_sheets, plate_names=up_plates), text)
    (RUN_DIR / "graphs" / f"{args.chunk}.json").write_text(json.dumps(g, indent=2))
    try:
        F.api("/prompt", {"prompt": g}, timeout=90)
        print(f"QUEUED {args.chunk} ({len(up_sheets)} sheets + {len(up_plates)} plate, "
              f"video ref {vname})")
    except Exception as e:  # noqa: BLE001
        print("queue failed:", e)


if __name__ == "__main__":
    main()
