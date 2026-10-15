#!/usr/bin/env python3
"""Queue ONE chunk's graph on the 5090, bypassing the render ledger.

`fullrun.py render` skips any chunk already recorded in `fullrun/renders.jsonl`
(state queued/done), which is right for a batch but blocks the thing we actually
need now: re-rendering the SAME chunk with a new style to compare against the
take already on disk. This is the A/B driver.

It does not build prompts or graphs — it consumes `fullrun/graphs/<chunk>.json`
as written by `fullrun.py prompt` (run that first, with FNI_STYLE_LORA set if you
want the style LoRA baked into the graph).

    # 1. rebuild the graph with the style LoRA
    FNI_STYLE_LORA="h3/models/retro-fantasy-step00003750.safetensors" \
      .venv/Scripts/python.exe pipeline/fullrun.py prompt --scenes S05

    # 2. queue one chunk of it with a distinct output prefix
    .venv/Scripts/python.exe tools/render_one.py --chunk S05-c01 \
        --prefix video/S05-c01_technicolor_t01 --wait

    # A/B: same seed, graph WITHOUT the LoRA (regenerate, or pass --strip-lora)
    .venv/Scripts/python.exe tools/render_one.py --chunk S05-c01 --strip-lora \
        --prefix video/S05-c01_baseline_t01 --wait
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(r"E:/FNI")
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT))
import urllib.error  # noqa: E402
import urllib.request  # noqa: E402

import fullrun  # noqa: E402  (COMFY/api/upload live there)

GRAPH_DIR = ROOT / "fullrun" / "graphs"
INPUT_DIR = ROOT / "fullrun" / "input"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunk", required=True, help="e.g. S05-c01")
    ap.add_argument("--prefix", default=None, help="output filename prefix")
    ap.add_argument("--seed", type=int, default=None, help="override the graph seed")
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--style-lora", default=None, help="inject/replace a LoraLoaderModelOnly")
    ap.add_argument("--style-strength", type=float, default=0.8)
    ap.add_argument("--strip-lora", action="store_true", help="remove any style LoRA node")
    ap.add_argument("--url", default=None, help="override the ComfyUI endpoint")
    ap.add_argument("--wait", action="store_true", help="poll /history and report the output")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.url:
        fullrun.COMFY = a.url
    print("endpoint:", fullrun.COMFY)

    gpath = GRAPH_DIR / (a.chunk + ".json")
    if not gpath.exists():
        raise SystemExit("no graph at %s - run: fullrun.py prompt --scenes %s"
                         % (gpath, a.chunk.split("-")[0]))
    g = json.loads(gpath.read_text(encoding="utf-8"))

    if a.seed is not None:
        for nid, n in g.items():
            if "noise_seed" in n.get("inputs", {}):
                n["inputs"]["noise_seed"] = a.seed
        print("seed ->", a.seed)
    if a.steps is not None and "124" in g:
        g["124"]["inputs"]["steps"] = a.steps
        print("steps ->", a.steps)

    # style LoRA: reuse node 147 if the graph already has one, else insert
    if a.strip_lora:
        if "147" in g:
            del g["147"]
            g["126"]["inputs"]["model"] = ["127", 0]
            print("stripped style LoRA")
    else:
        want = a.style_lora
        if want or "147" in g:
            name = want or g["147"]["inputs"]["lora_name"]
            g["147"] = {"inputs": {"model": ["127", 0], "lora_name": name,
                                   "strength_model": a.style_strength},
                        "class_type": "LoraLoaderModelOnly",
                        "_meta": {"title": "Style LoRA (%s @ %s)" % (name, a.style_strength)}}
            g["126"]["inputs"]["model"] = ["147", 0]
            print("style LoRA:", name, "@", a.style_strength)

    if a.prefix:
        for n in g.values():
            if n.get("class_type") in ("SaveVideo", "VHS_VideoCombine") \
                    and "filename_prefix" in n.get("inputs", {}):
                n["inputs"]["filename_prefix"] = a.prefix
        print("prefix ->", a.prefix)
    else:
        a.prefix = next((n["inputs"]["filename_prefix"] for n in g.values()
                         if n.get("class_type") in ("SaveVideo", "VHS_VideoCombine")), "?")

    # sanity: every LoadImage must name a file we are about to upload
    for nid, n in g.items():
        if n.get("class_type") == "LoadImage":
            nm = n["inputs"]["image"]
            if not (INPUT_DIR / nm).exists():
                hits = sorted(INPUT_DIR.glob(a.chunk + "*"))
                raise SystemExit("graph references %r but it is not in %s (have: %s)"
                                 % (nm, INPUT_DIR, [h.name for h in hits]))

    if a.dry_run:
        print("dry run: graph valid, %d nodes" % len(g))
        return

    for key in ("first", "last"):
        img = INPUT_DIR / ("%s_%s.jpg" % (a.chunk, key))
        if img.exists():
            try:
                fullrun.upload(img)
            except Exception as e:  # noqa: BLE001
                print("  upload %s failed: %s" % (key, e))
                return

    try:
        res = fullrun.api("/prompt", {"prompt": g}, timeout=90)
    except urllib.error.HTTPError as e:
        print("REJECTED:")
        print(e.read().decode("utf-8", "replace")[:1500])
        return
    pid = res.get("prompt_id")
    if not pid:
        print("REJECTED (node_errors):", json.dumps(res.get("node_errors"))[:800])
        return
    print("queued prompt_id", pid)
    print("output will be:", a.prefix)

    if not a.wait:
        return
    t0 = time.time()
    while True:
        time.sleep(10)
        try:
            h = fullrun.api("/history/" + pid, timeout=30)
        except Exception:  # noqa: BLE001
            continue
        if pid in h:
            e = h[pid]
            st = e.get("status", {})
            print("status:", st.get("status_str"), "in %.0fs" % (time.time() - t0))
            for out in (e.get("outputs") or {}).values():
                for v in (out.get("videos") or []) + (out.get("gifs") or []) + (out.get("images") or []):
                    print("  OUTPUT:", v.get("subfolder", ""), v.get("filename"))
            if st.get("status_str") == "error":
                for m in st.get("messages", [])[-3:]:
                    print("  ", json.dumps(m)[:400])
            return


if __name__ == "__main__":
    main()
