#!/usr/bin/env python
"""Generate Krea2 character stills on the 5090 from a saved ComfyUI workflow JSON.

Vary ONLY the prompt text and the LoRA strengths (the user's workflow runs fine).
Edit the two knobs that matter and POST the graph; poll /history and download PNGs.

Usage:
    .venv/Scripts/python.exe tools/krea2_stills.py --workflow <json> --name teegra [--variants-built-in]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

COMFY = os.environ.get("FNI_COMFY", "http://100.104.7.72:8188").rstrip("/")


def _post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def _get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode())


def load_workflow(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# --- node accessors (keyed by the IDs in ComfyUI_00108_.json) ---
POS_MAIN = "135"      # easy positive -> main description
POS_PRE = "137"       # easy positive -> PRE-PROMPT (style + LoRA triggers)
POS_POST = "136"      # easy positive -> POST-PROMPT (empty)
LORA_NODE = "124"     # Power Lora Loader (rgthree): lora_1..lora_7 {on, lora, strength}
SAMPLER = "102"       # KSampler -> seed
SAVE = "128"          # SaveImage -> filename_prefix


def set_prompt(g: dict, main: str | None = None, pre: str | None = None, post: str | None = None) -> None:
    if main is not None:
        g[POS_MAIN]["inputs"]["positive"] = main
    if pre is not None:
        g[POS_PRE]["inputs"]["positive"] = pre
    if post is not None:
        g[POS_POST]["inputs"]["positive"] = post


def set_lora(g: dict, slot: str, on: bool, strength: float | None = None) -> None:
    s = g[LORA_NODE]["inputs"][slot]
    s["on"] = on
    if strength is not None:
        s["strength"] = strength


def set_seed(g: dict, seed: int) -> None:
    g[SAMPLER]["inputs"]["seed"] = seed


def set_prefix(g: dict, prefix: str) -> None:
    g[SAVE]["inputs"]["filename_prefix"] = prefix


def queue_graph(g: dict, client_id: str) -> str:
    resp = _post(f"{COMFY}/prompt", {"prompt": g, "client_id": client_id})
    if resp.get("node_errors"):
        raise RuntimeError(f"node_errors: {json.dumps(resp['node_errors'])}")
    return resp["prompt_id"]


def wait_and_download(g: dict, prompt_id: str, outdir: str, timeout_s: int = 600) -> list[str]:
    """Poll /history/<id> until SaveImage outputs exist, then download each PNG."""
    os.makedirs(outdir, exist_ok=True)
    prefix = g[SAVE]["inputs"]["filename_prefix"]
    deadline = time.time() + timeout_s
    outputs = []
    while time.time() < deadline:
        try:
            h = _get(f"{COMFY}/history/{prompt_id}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                time.sleep(2)
                continue
            raise
        rec = h.get(prompt_id)
        if rec and rec.get("outputs"):
            for node_id, out in rec["outputs"].items():
                for img in out.get("images", []):
                    fn = img["filename"]
                    sub = img.get("subfolder", "")
                    stype = img.get("type", "output")
                    url = f"{COMFY}/view?filename={fn}&subfolder={sub}&type={stype}"
                    dest = os.path.join(outdir, fn)
                    with urllib.request.urlopen(url, timeout=60) as r:
                        open(dest, "wb").write(r.read())
                    outputs.append(dest)
            if outputs:
                return outputs
        if rec and rec.get("status", {}).get("status_str") == "error":
            raise RuntimeError(f"render error: {rec['status']}")
        time.sleep(3)
    raise TimeoutError(f"prompt_id {prompt_id} did not finish in {timeout_s}s")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workflow", required=True)
    ap.add_argument("--name", default="teegra")
    ap.add_argument("--seed", type=int, default=82036621553915)
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--prompt-main")
    ap.add_argument("--pre-prompt")
    ap.add_argument("--jada-strength", type=float, default=None)   # None = leave as-is; 0 = off
    ap.add_argument("--retro-strength", type=float, default=None)
    args = ap.parse_args()

    g = load_workflow(args.workflow)
    if args.prompt_main:
        set_prompt(g, main=args.prompt_main)
    if args.pre_prompt is not None:
        set_prompt(g, pre=args.pre_prompt)
    if args.jada_strength is not None:
        set_lora(g, "lora_1", on=(args.jada_strength > 0), strength=args.jada_strength)
    if args.retro_strength is not None:
        set_lora(g, "lora_7", on=(args.retro_strength > 0), strength=args.retro_strength)
    set_seed(g, args.seed)

    tag = (
        f"{args.name}_j{args.jada_strength if args.jada_strength is not None else 'x'}"
        f"_r{args.retro_strength if args.retro_strength is not None else 'x'}"
        f"_s{args.seed}"
    )
    set_prefix(g, tag)
    outdir = args.outdir or f"renders/5090/{args.name}-stills"
    cid = f"fni-krea2-{args.name}-{int(time.time())}"
    pid = queue_graph(g, cid)
    print(f"queued prompt_id={pid} tag={tag}", flush=True)
    files = wait_and_download(g, pid, outdir)
    for f in files:
        print(f"downloaded {f}", flush=True)


if __name__ == "__main__":
    main()