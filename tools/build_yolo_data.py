# -*- coding: utf-8 -*-
"""Bake the YOLO-run catalog for the shot browser: window.YOLODATA.

Joins, per chunk:
  - the rendered video          runs/yolo_output/<chunk>_audioOnly_t01_*.mp4
  - the exact prompt text        runs/T0016_s05_technicolor-audio-only-ref2va/prompts/<chunk>.txt
  - the queued graph             runs/T0016_s05_technicolor-audio-only-ref2va/graphs/<tag>.json
    (sheet image names, plate, seed, audio track)

Alex (2026-10-28): "when we assemble this test run in the SPA we need to
display the prompt next to the video so we can see where things went wrong."
Re-run this builder after any new renders land, then hard-reload the SPA.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"E:/FNI")
OUTDIR = ROOT / "runs" / "yolo_output"
RUN_DIR = ROOT / "runs" / "T0016_s05_technicolor-audio-only-ref2va"
CHUNKS = ROOT / "fullrun" / "chunks.jsonl"
DEST = ROOT / "browser" / "yolo-data.js"


def graph_meta(gpath: Path) -> dict:
    g = json.loads(gpath.read_text(encoding="utf-8"))
    sheets, plates, seed, audio = [], [], None, None
    for node in g.values():
        ct = node.get("class_type", "")
        inp = node.get("inputs", {})
        if ct == "LoadImage":
            img = inp.get("image", "")
            if "_plate_" in img:
                plates.append(img)
            else:
                sheets.append(img)
        elif ct == "RandomNoise":
            seed = inp.get("noise_seed")
        elif ct == "LoadAudio":
            audio = inp.get("audio")
    return {"sheets": sheets, "plates": plates, "seed": seed, "audio": audio,
            "graph": gpath.name}


def main():
    chunk_rows = {}
    for l in CHUNKS.read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            chunk_rows[r["chunk_id"]] = r

    # jury verdicts (manifests/prompt_review.jsonl), if the jury has run
    reviews = {}
    rv = ROOT / "manifests" / "prompt_review.jsonl"
    if rv.exists():
        for l in rv.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                reviews[r["chunk"]] = r

    graphs = {}
    gdir = RUN_DIR / "graphs"
    if gdir.exists():
        for gp in sorted(gdir.glob("*.json")):
            cid = gp.name.split("_audioOnly")[0]
            graphs.setdefault(cid, gp)  # first take wins; extend later if takes matter

    videos = {}
    if OUTDIR.exists():
        for mp4 in sorted(OUTDIR.glob("*_audioOnly_*.mp4")):
            cid = mp4.name.split("_audioOnly")[0]
            videos.setdefault(cid, []).append(mp4.name)

    pdir = RUN_DIR / "prompts"
    clips = []
    for cid, gp in sorted(graphs.items()):
        row = chunk_rows.get(cid, {})
        meta = graph_meta(gp)
        ptxt = ""
        pf = pdir / f"{cid}.txt"
        if pf.exists():
            ptxt = pf.read_text(encoding="utf-8")
        rev = reviews.get(cid, {})
        clips.append({
            "chunk": cid,
            "scene": row.get("scene", ""),
            "subjects": [n for n in dict.fromkeys(row.get("speakers", []) + row.get("stamped_names", []))],
            "shot_nums": row.get("shot_nums", []),
            "location": row.get("location", ""),
            "sheets": meta["sheets"],
            "plates": meta["plates"],
            "seed": meta["seed"],
            "audio": meta["audio"],
            "graph": meta["graph"],
            "videos": [f"runs/yolo_output/{v}" for v in videos.get(cid, [])],
            "prompt": ptxt,
            "verdict": rev.get("final_verdict"),
            "fix_summary": rev.get("fix_summary", ""),
            "issues": rev.get("issues", []),
            "votes": rev.get("votes", {}),
        })

    have_video = sum(1 for c in clips if c["videos"])
    DEST.write_text(
        "window.YOLODATA = " + json.dumps({"clips": clips}, ensure_ascii=False) + ";\n",
        encoding="utf-8")
    print(f"wrote {DEST}: {len(clips)} clips ({have_video} with video, "
          f"{len(videos)} mp4s in yolo_output)")


if __name__ == "__main__":
    main()
