"""T0010 — Motion-Context CHAIN vs frame anchoring (the chain A/B).

T0009 packed S02 by continuity and rendered six independent FL2VA segments
(first/last-frame anchored). T0010 renders the SAME six segments, same seeds,
same anchors, but as ONE Motion Context chain: each link pins the previous
link's sampler-output latent as never-denoised head frames, so the model reads
REAL motion (and the previous clip's real tail sound) across each join instead
of re-generating from a still.

Only the chaining mechanism differs, so it is a clean A/B:
  S02_continuity_audioA.mp4  (T0009, anchored)
  S02_chain_audioA.mp4       (T0010, chained)

Serial on purpose: link N loads link N-1's saved latent, so links queue one at
a time and each waits for the previous to finish.

Run (background, ~1-2h, uses the 5090 via Tailscale):
  .venv/Scripts/python.exe runs/build_t0010.py
"""
import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.error
from pathlib import Path

ROOT = Path(r"E:/FNI")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "pipeline"))  # fullrun.py moved into pipeline/ (reorg 562c6a1)
import fullrun as fr  # noqa: E402
from core.h3_chain import chainify  # noqa: E402

T10 = ROOT / "runs" / "T0010_s02_chain"
T9 = ROOT / "runs" / "T0009_s02_continuity"
SCENE = "S02"
CHAIN = "t0010_s02"
MASTER_AUDIO = ROOT / "audio" / "master_audio_48k_stereo.wav"


def retarget():
    for d in ("graphs", "input", "output", "stitched"):
        (T10 / d).mkdir(parents=True, exist_ok=True)
    fr.CHUNK_LEDGER = T10 / "chunks.jsonl"
    fr.RENDER_LEDGER = T10 / "renders.jsonl"
    fr.GRAPH_DIR = T10 / "graphs"
    fr.INPUT_DIR = T10 / "input"
    fr.OUTPUT_DIR = T10 / "output"
    fr.STITCH_DIR = T10 / "stitched"


def load_rows():
    return [json.loads(l) for l in (T9 / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]


def prep(rows):
    retarget()
    with fr.CHUNK_LEDGER.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    for i, r in enumerate(rows, 1):
        src_graph = T9 / "graphs" / (r["chunk_id"] + ".json")
        g = json.loads(src_graph.read_text(encoding="utf-8"))
        g = chainify(g, i, CHAIN, clip_id=r["chunk_id"])
        (fr.GRAPH_DIR / (r["chunk_id"] + ".json")).write_text(json.dumps(g, indent=2))
        for key in ("first", "last"):
            src = T9 / "input" / ("%s_%s.jpg" % (r["chunk_id"], key))
            if src.exists():
                shutil.copy(src, fr.INPUT_DIR / src.name)
    print("prepared %d chain graphs in %s" % (len(rows), fr.GRAPH_DIR), flush=True)


def clip_done(pid):
    try:
        h = fr.api("/history/" + pid, timeout=30)
    except Exception:  # noqa: BLE001
        return False
    if not h:
        return False
    v = list(h.values())[0]
    return v.get("status", {}).get("status_str") in ("success", "error")


def render_serial(rows):
    fh = fr.RENDER_LEDGER.open("a", encoding="utf-8")
    try:
        for i, r in enumerate(rows, 1):
            cid = r["chunk_id"]
            graph = json.loads((fr.GRAPH_DIR / (cid + ".json")).read_text(encoding="utf-8"))
            ok = True
            for key in ("first", "last"):
                img = fr.INPUT_DIR / ("%s_%s.jpg" % (cid, key))
                if not img.exists():
                    print("  %s missing %s image, skipping" % (cid, key)); ok = False; break
                try:
                    fr.upload(img)
                except Exception as e:  # noqa: BLE001
                    print("  %s upload %s failed: %s" % (cid, key, e)); ok = False
            if not ok:
                continue
            # wait for a clean box (this link must start after the previous finished)
            while True:
                run, pend = fr.queue_state()
                if run + pend == 0:
                    break
                print("  waiting for queue to drain (%d run %d pend)..." % (run, pend), flush=True)
                time.sleep(15)
            try:
                res = fr.api("/prompt", {"prompt": graph}, timeout=90)
            except urllib.error.HTTPError as e:
                print("  %s rejected: %s" % (cid, e.read().decode("utf-8", "replace")[:500]))
                continue
            pid = res.get("prompt_id")
            if not pid:
                print("  %s rejected: %s" % (cid, res.get("node_errors")))
                continue
            fh.write(json.dumps({"chunk_id": cid, "state": "queued", "prompt_id": pid,
                                 "clip_index": i, "ts": time.time()}) + "\n")
            fh.flush()
            print("  queued %s (link %d) %s" % (cid, i, pid[:8]), flush=True)
            deadline = time.time() + 45 * 60
            while time.time() < deadline:
                if clip_done(pid):
                    state = list(fr.api("/history/" + pid, timeout=30).values())[0]["status"]["status_str"]
                    print("  %s finished (%s)" % (cid, state), flush=True)
                    break
                time.sleep(15)
    finally:
        fh.close()


def overlay(video, start_tc, dst):
    if not video.exists():
        return False
    rc = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-y",
                         "-i", str(video), "-ss", start_tc.replace(",", "."),
                         "-i", str(MASTER_AUDIO), "-map", "0:v", "-map", "1:a",
                         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                         str(dst)], capture_output=True, text=True)
    return rc.returncode == 0


def main():
    rows = load_rows()
    prep(rows)
    print("segments:", [(r["chunk_id"], r["shot_nums"]) for r in rows], flush=True)

    # build prompts the same way T0009 did (reuse its prompt text verbatim)
    (T10 / "prompts").mkdir(exist_ok=True)
    fr.PROMPT_DIR = T10 / "prompts"
    for r in rows:
        src = T9 / "prompts" / (r["chunk_id"] + ".txt")
        if src.exists():
            shutil.copy(src, fr.PROMPT_DIR / src.name)

    render_serial(rows)

    # collect + stitch (same as T0009)
    for attempt in range(6):
        fr.cmd_collect(argparse.Namespace(scenes=""))
        got = len(list(fr.OUTPUT_DIR.glob("*_full_t01.mp4")))
        if got == len(rows):
            break
        time.sleep(30)
    fr.cmd_stitch(argparse.Namespace(scenes=SCENE))

    stitched = fr.STITCH_DIR / ("%s_full_t01.mp4" % SCENE)
    if stitched.exists():
        overlay(stitched, rows[0]["src_start"], T10 / "S02_chain_audioA.mp4")
    # reference arm (T0009 anchored)
    ref = ROOT / "runs" / "T0009_s02_continuity" / "S02_continuity_audioA.mp4"
    out_ref = T10 / "S02_anchored_audioA.mp4"
    if ref.exists() and not out_ref.exists():
        shutil.copy(ref, out_ref)

    man = ["# T0010 — motion-context chain vs frame anchoring", "",
           "Same six S02 segments, seeds, and anchors as T0009; only the chaining",
           "mechanism differs (context_latent pinned head vs first/last stills).", "",
           "Note: links 2-6 are each 22 frames (0.92s) shorter than their sampled",
           "length — the pinned head replaces the previous clip's tail, so total",
           "video runs ~4.6s short vs T0009. The master-audio overlay starts at the",
           "same source timecode either way.", "",
           "Compare: T0010/S02_chain_audioA.mp4  vs  T0010/S02_anchored_audioA.mp4", "",
           "Look for: joins playing as continuous MOTION (no restart), setup B",
           "holding on return, and whether the 22-frame pinned head reads as a",
           "seam or as a held beat. SeamProbe (seam_probe.py) quantifies the audio",
           "joins from the *_untrimmed sidecars."]
    (T10 / "manifest.md").write_text("\n".join(man) + "\n", encoding="utf-8")
    print("T0010 done. compare S02_chain_audioA vs S02_anchored_audioA", flush=True)


if __name__ == "__main__":
    main()