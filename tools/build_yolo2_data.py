# -*- coding: utf-8 -*-
"""Bake the pass-2/pass-3 catalog for the shot browser: window.YOLO2DATA.

Companion to tools/build_yolo_data.py (pass 1 -> window.YOLODATA). Same record shape, so the
SPA's existing yolo renderer can drive both views, plus two things pass 3 adds:

  * `takes`  — pass 2 (take 01) and pass 3 (take 02, new seed) side by side, each with its own
               seed and graph, so the seed is the only difference a reader has to hold in mind;
  * `vlm`    — the tight-loop verdict for the take-2 clip: verdict, the max number of people the
               VLM saw in any sampled frame, the chunk's cast from the ledger, and the per-shot
               reads. Source: runs/yolo3_loop.jsonl.

Why the verdict is "people vs cast" and not "per shot vs prompt": the yolo prompts carry no
per-shot cast claim (that clause only went into the T0017 S03 arms via --shot-presence), so
vlm_cast_check returns UNCHECKED for every shot — and UNCHECKED is not agreement.

    .venv/Scripts/python.exe tools/build_yolo2_data.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"E:/FNI")
RUN_DIR = ROOT / "runs" / "T0016_s05_technicolor-audio-only-ref2va"
DIRS = {1: ROOT / "runs" / "yolo_output2", 2: ROOT / "runs" / "yolo_output3"}
CHUNKS = ROOT / "fullrun" / "chunks.jsonl"
LOOP_LEDGER = ROOT / "runs" / "yolo3_loop.jsonl"
DEST = ROOT / "browser" / "yolo2-data.js"


def graph_meta(gpath: Path) -> dict:
    g = json.loads(gpath.read_text(encoding="utf-8"))
    sheets, plates, seed, audio = [], [], None, None
    for node in g.values():
        ct = node.get("class_type", "")
        inp = node.get("inputs", {})
        if ct == "LoadImage":
            img = inp.get("image", "")
            (plates if "_plate_" in img else sheets).append(img)
        elif ct == "RandomNoise":
            seed = inp.get("noise_seed")
        elif ct == "LoadAudio":
            audio = inp.get("audio")
    return {"sheets": sheets, "plates": plates, "seed": seed, "audio": audio, "graph": gpath.name}


def main() -> None:
    chunk_rows = {}
    for l in CHUNKS.read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            chunk_rows[r["chunk_id"]] = r

    vlm = {}
    if LOOP_LEDGER.exists():
        for l in LOOP_LEDGER.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                vlm[r["chunk"]] = r          # last write wins = newest verdict

    gdir = RUN_DIR / "graphs"
    graphs = {}
    if gdir.exists():
        for gp in sorted(gdir.glob("*_audioOnly_t*.json")):
            cid = gp.name.split("_audioOnly")[0]
            take = 2 if "_t02" in gp.name else 1
            graphs.setdefault(cid, {})[take] = gp

    videos = {t: {} for t in DIRS}
    for t, d in DIRS.items():
        if d.exists():
            for mp4 in sorted(d.glob("*_audioOnly_*.mp4")):
                videos[t].setdefault(mp4.name.split("_audioOnly")[0], []).append(mp4.name)

    clips = []
    for cid in sorted(graphs):
        row = chunk_rows.get(cid, {})
        takes, rec = [], None
        for t in (1, 2):
            gp = graphs[cid].get(t)
            if not gp:
                continue
            meta = graph_meta(gp)
            files = videos.get(t, {}).get(cid, [])
            takes.append({"take": t, "seed": meta["seed"], "graph": meta["graph"],
                          "sheets": meta["sheets"], "plates": meta["plates"],
                          "files": files, "present": bool(files)})
            if t == 2 or rec is None:
                rec = meta
        if rec is None:
            continue
        ptxt = ""
        pf = RUN_DIR / "prompts" / f"{cid}.txt"
        if pf.exists():
            ptxt = pf.read_text(encoding="utf-8")
        v = vlm.get(cid)
        clips.append({
            "chunk": cid,
            "scene": row.get("scene", ""),
            "subjects": [n for n in dict.fromkeys(list(row.get("speakers") or []) +
                                                  list(row.get("stamped_names") or []))],
            "shot_nums": row.get("shot_nums", []),
            "location": row.get("location", ""),
            "sheets": rec["sheets"],
            "plates": rec["plates"],
            "seed": rec["seed"],
            "audio": rec["audio"],
            "graph": rec["graph"],
            "videos": [f"runs/yolo_output2/{f}" for f in videos.get(1, {}).get(cid, [])] +
                      [f"runs/yolo_output3/{f}" for f in videos.get(2, {}).get(cid, [])],
            "prompt": ptxt,
            "takes": takes,
            "vlm": ({"verdict": v.get("verdict"), "observed_max": v.get("observed_max"),
                     "expected_cast": v.get("expected_cast"),
                     "observations": v.get("observations")} if v else None),
        })

    have2 = sum(1 for c in clips if any(t["take"] == 2 and t["present"] for t in c["takes"]))
    judged = sum(1 for c in clips if c["vlm"])
    DEST.write_text("window.YOLO2DATA = " + json.dumps({"clips": clips}, ensure_ascii=False) + ";\n",
                    encoding="utf-8")
    print(f"wrote {DEST}: {len(clips)} clips | take-2 present {have2} | vlm-judged {judged}")


if __name__ == "__main__":
    main()
