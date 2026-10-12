"""T0009 — S02 continuity-packed rerender (the chaining pilot).

Variable under test: chunk boundaries from continuity analysis instead of
strict chronology. Same prompt builder, same FL2VA graph, same seed method,
same anchors — only the packing differs, so t01 (fullrun/stitched) vs T0009
is a clean side-by-side.

Packing rule (uniform):
  - CHAIN edge (SSIM >= chain-th): always merge (action continues).
  - CUT edge: close the segment IF it is >= H3's 4s floor; otherwise merge
    across the cut (floor forced) until >= 4s. Cap 15s.

S02 result: [16] [17,18,19] [20,21] [22] [23,24,25] [26,27] — both glacier
chains (17->18, 24->25) intact, vs chronological [16,17,18][19,20,21]
[22,23,24][25,26,27] which split 24->25 across chunks.

Run (background, ~1-2h):
  .venv/Scripts/python.exe runs/build_t0009.py
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r"E:/FNI")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "pipeline"))  # fullrun.py moved into pipeline/ (reorg 562c6a1)
import fullrun as fr  # noqa: E402

T9 = ROOT / "runs" / "T0009_s02_continuity"
SCENE = "S02"
MASTER_AUDIO = ROOT / "audio" / "master_audio_48k_stereo.wav"


def load():
    shots = {s["shot_id"]: s for s in fr.jl(ROOT / "shots.jsonl")}
    cont = None
    for r in fr.jl(ROOT / "manifests" / "continuity.jsonl"):
        if r["scene"] == SCENE:
            cont = r
    orig = [r for r in fr.jl(fr.CHUNK_LEDGER) if r["scene"] == SCENE]
    dialogue = list(fr.csv.DictReader(fr.TSV.open(encoding="utf-8"), delimiter="\t"))
    return shots, cont, orig, dialogue


def pack(shots, cont):
    """Uniform packing: chain always merges; cuts close only at/above floor."""
    scene_ids = [sid for sid in shots
                 if any(sid in g for g in cont["setups"].values())]
    scene_ids.sort(key=lambda sid: shots[sid]["start_frame"])
    chain = {(e["from"], e["to"]) for e in cont["edges"] if e["edge"] == "CHAIN"}
    segs, cur = [], [scene_ids[0]]
    cur_dur = shots[scene_ids[0]]["duration_seconds"]
    for a, b in zip(scene_ids, scene_ids[1:]):
        is_chain = (a, b) in chain
        if is_chain and cur_dur + shots[b]["duration_seconds"] <= fr.CHUNK_MAX_S:
            cur.append(b)
            cur_dur += shots[b]["duration_seconds"]
            continue
        if cur_dur >= fr.CHUNK_MIN_S and cur_dur + shots[b]["duration_seconds"] <= fr.CHUNK_MAX_S \
                and not is_chain:
            segs.append(cur)
            cur, cur_dur = [b], shots[b]["duration_seconds"]
            continue
        if cur_dur + shots[b]["duration_seconds"] <= fr.CHUNK_MAX_S:
            cur.append(b)  # floor-forced merge across a cut
            cur_dur += shots[b]["duration_seconds"]
            continue
        segs.append(cur)
        cur, cur_dur = [b], shots[b]["duration_seconds"]
    segs.append(cur)
    return segs


def build_rows(segs, shots, orig, dialogue):
    base = orig[0]
    # per-shot composition arrays, re-aligned from the chronological rows
    comp = {}
    for r in orig:
        for i, sid in enumerate(r["shots"]):
            comp[sid] = {k: (r[k][i] if i < len(r.get(k, [])) else "")
                         for k in ("shot_type", "angle", "motion", "people_count")}
    rows = []
    for n, seg in enumerate(segs, 1):
        cid = "%s-k%02d" % (SCENE, n)
        t0 = shots[seg[0]]["start_pts"] / 24000
        t1 = shots[seg[-1]]["end_pts"] / 24000
        dur = t1 - t0
        frames = fr.h3_frames(dur)
        line_ids = [d["id"] for d in dialogue
                    if d.get("scene", "").upper() == SCENE
                    and t0 <= (fr.sec(d["start"]) + fr.sec(d["end"])) / 2 < t1]
        rows.append({
            "chunk_id": cid, "scene": SCENE,
            "scene_kind": base["scene_kind"], "scene_title": base["scene_title"],
            "cast": base["cast"], "location": base["location"], "music": base["music"],
            "shots": seg, "shot_nums": [s.split(":")[1] for s in seg],
            "src_start": fr.tc_of(t0), "src_end": fr.tc_of(t1),
            "src_duration": round(dur, 3),
            "h3_frames": frames, "h3_seconds": round(frames / fr.FPS, 3),
            "seed": fr.seed_for(cid),
            "line_ids": line_ids,
            "speakers": sorted({d["speaker"] for d in dialogue if d["id"] in line_ids}),
            "stamped_names": sorted({n for r in orig for n in r["stamped_names"]}),
            "shot_type": [comp[s]["shot_type"] for s in seg],
            "angle": [comp[s]["angle"] for s in seg],
            "motion": [comp[s]["motion"] for s in seg],
            "people_count": [comp[s]["people_count"] for s in seg],
        })
    return rows


def retarget():
    for d in ("prompts", "graphs", "input", "output", "stitched"):
        (T9 / d).mkdir(parents=True, exist_ok=True)
    fr.CHUNK_LEDGER = T9 / "chunks.jsonl"
    fr.RENDER_LEDGER = T9 / "renders.jsonl"
    fr.PROMPT_DIR = T9 / "prompts"
    fr.GRAPH_DIR = T9 / "graphs"
    fr.INPUT_DIR = T9 / "input"
    fr.OUTPUT_DIR = T9 / "output"
    fr.STITCH_DIR = T9 / "stitched"


def overlay(video, start_tc, dst):
    rc = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-y",
                         "-i", str(video), "-ss", start_tc.replace(",", "."),
                         "-i", str(MASTER_AUDIO), "-map", "0:v", "-map", "1:a",
                         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                         str(dst)], capture_output=True, text=True)
    return rc.returncode == 0


def main():
    shots, cont, orig, dialogue = load()
    segs = pack(shots, cont)
    rows = build_rows(segs, shots, orig, dialogue)
    retarget()
    with fr.CHUNK_LEDGER.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print("segments:", [(r["chunk_id"], r["shot_nums"], r["h3_seconds"]) for r in rows], flush=True)

    fr.cmd_prompt(argparse.Namespace(scenes=SCENE, limit=0))
    fr.cmd_render(argparse.Namespace(scenes="", limit=0, max_pending=4, poll=60,
                                     gap=2, refresh=False, retry_rejected=False))
    # drain
    deadline = time.time() + 6 * 3600
    while time.time() < deadline:
        run, pend = fr.queue_state()
        if run + pend == 0:
            break
        time.sleep(60)
    got = 0
    for attempt in range(6):
        fr.cmd_collect(argparse.Namespace(scenes=""))
        got = len(list((T9 / "output").glob("*_full_t01.mp4")))
        if got == len(rows):
            break
        time.sleep(120)
    fr.cmd_stitch(argparse.Namespace(scenes=SCENE))

    stitched = T9 / "stitched" / ("%s_full_t01.mp4" % SCENE)
    if stitched.exists():
        overlay(stitched, rows[0]["src_start"], T9 / "S02_continuity_audioA.mp4")
    # comparison: original stitch + audio
    orig_stitch = ROOT / "fullrun" / "stitched" / ("%s_full_t01.mp4" % SCENE)
    if orig_stitch.exists():
        overlay(orig_stitch, rows[0]["src_start"], T9 / "S02_chronological_audioA.mp4")

    man = ["# T0009 — S02 continuity packing vs chronological", "",
           "Variable: chunk boundaries only. Same builder/graph/seeds/anchors.", "",
           "| seg | shots | h3 s | lines |", "|---|---|---|---|"]
    for r in rows:
        man.append("| %s | %s | %.2f | %s |" % (r["chunk_id"], ",".join(r["shot_nums"]),
                                                r["h3_seconds"], " ".join(r["line_ids"]) or "-"))
    man += ["", "Chronological (t01): " + "; ".join(",".join(r["shot_nums"]) for r in orig),
            "", "Collected: %d/%d" % (got, len(rows)),
            "Compare: S02_continuity_audioA.mp4 vs S02_chronological_audioA.mp4",
            "Look for: glacier chains 17->18 and 24->25 playing as continuous motion;",
            "cuts landing cleanly instead of morphing; setup B consistency on return."]
    (T9 / "manifest.md").write_text("\n".join(man) + "\n", encoding="utf-8")
    print("T0009 done: %d/%d collected, manifest written" % (got, len(rows)), flush=True)


if __name__ == "__main__":
    main()
