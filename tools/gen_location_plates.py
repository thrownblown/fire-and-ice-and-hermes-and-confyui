#!/usr/bin/env python
"""Generate canonical location background plates on the 5090 (Krea2 t2i).

Reuses the proven Krea2 still workflow (ComfyUI_00108_.json): Krea2 UNet + Wan2.1
VAE + krea2 CLIP + retro-fantasy style LoRA. For a location plate the prompt is an
EMPTY scene (no people), the character LoRA (person_27) stays OFF, retro-fantasy stays ON @1.0.

Usage:
    .venv/Scripts/python.exe tools/gen_location_plates.py --list
    .venv/Scripts/python.exe tools/gen_location_plates.py --loc jungle --queue
    .venv/Scripts/python.exe tools/gen_location_plates.py --all --queue   # all canonical locations

Plates land in refs/backgrounds/<slug>/ as <slug>_plate_t01.png (created if missing).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(r"E:/FNI")
COMFY = os.environ.get("FNI_COMFY", "http://<TOMBSTONE_TS_IP>:8188").rstrip("/")
WF = Path(r"C:/Users/gsfny/Downloads/ComfyUI_00108_.json")

POS_MAIN = "135"
POS_PRE = "137"
LORA_NODE = "124"
SAMPLER = "102"
SAVE = "128"
RESOLUTION = "126"   # ResolutionSelector: 16:9, 2MP
# note: the workflow resolves 16:9 @ 2 megapixels -> ~1888x1062

STYLE_PRE = "retr0fantasy, 60s Soviet fantasy-film, subtle film grain, aged theatrical print quality,"


def _post(url, payload, timeout=60):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        # ComfyUI explains itself in the body ("value_not_in_list", the node id, the legal values).
        # Without this the caller sees only "HTTP Error 400: Bad Request" and has to guess.
        body = e.read().decode(errors="replace")
        print(f"  HTTP {e.code} from {url}\n  {body[:1500]}", flush=True)
        raise


def _get(url, timeout=30):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode())


def load_locations() -> list[dict]:
    m = json.loads((ROOT / "manifests" / "locations.json").read_text(encoding="utf-8"))
    return m["canonical_locations"]


def build_graph(loc: dict, seed: int, prefix: str) -> dict:
    g = json.loads(WF.read_text(encoding="utf-8"))
    g[POS_MAIN]["inputs"]["positive"] = loc["prompt"]
    g[POS_PRE]["inputs"]["positive"] = STYLE_PRE
    # character LoRA OFF (identity is not wanted in a plate); retro-fantasy stays ON @1.0
    g[LORA_NODE]["inputs"]["lora_1"]["on"] = False
    g[LORA_NODE]["inputs"]["lora_1"]["strength"] = 0.0
    g[LORA_NODE]["inputs"]["lora_7"]["on"] = True
    g[LORA_NODE]["inputs"]["lora_7"]["strength"] = 1.0
    g[SAMPLER]["inputs"]["seed"] = seed
    g[SAVE]["inputs"]["filename_prefix"] = prefix
    return g


def run_one(loc: dict, seed: int, queue: bool, take: int = 1) -> int:
    slug = loc["slug"]
    out_dir = ROOT / "refs" / "backgrounds" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{slug}_plate_t{take:02d}"
    g = build_graph(loc, seed, prefix)
    # Snap model filenames to what THIS rig actually has before writing/queueing: a workflow authored on
    # the other box names its quants and paths differently and ComfyUI rejects the whole prompt with a
    # bare 400 (measured on the 4090: the int8 CLIP + a krea/ path prefix).
    sys.path.insert(0, str(ROOT))
    from core.asset_reconcile import snap
    changes = snap(g, COMFY)
    if changes:
        print(f"[{slug}] reconciled {len(changes)} asset path(s) to this rig", flush=True)
    # Force the save prefix: the workflow's own SaveImage node carries whatever prefix its author used
    # (measured: "ComfyUI_temp_..."), so a plate lands with a meaningless name unless we set it here.
    # Force the save prefix on ANY node that has one: this workflow's output node is not a SaveImage
    # class (it saves to temp, hence the ComfyUI_temp_* names), so matching on class name silently
    # did nothing.
    for node in g.values():
        if isinstance(node, dict) and "filename_prefix" in (node.get("inputs") or {}):
            node["inputs"]["filename_prefix"] = prefix
    gpath = out_dir / f"{prefix}.graph.json"
    gpath.write_text(json.dumps(g, indent=1), encoding="utf-8")
    print(f"[{slug}] graph -> {gpath}", flush=True)

    if not queue:
        return 0

    resp = _post(COMFY + "/prompt", {"prompt": g})
    if resp.get("node_errors"):
        raise RuntimeError(f"node_errors: {json.dumps(resp['node_errors'])}")
    pid = resp["prompt_id"]
    print(f"[{slug}] queued prompt_id={pid}", flush=True)

    deadline = time.time() + 900
    while time.time() < deadline:
        try:
            h = _get(COMFY + f"/history/{pid}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                time.sleep(3)
                continue
            raise
        rec = h.get(pid)
        if rec and rec.get("outputs"):
            for out in rec["outputs"].values():
                for im in out.get("images", []):
                    fn = im["filename"]
                    sub = im.get("subfolder", "")
                    stype = im.get("type", "output")
                    url = (COMFY + "/view?filename=" + urllib.parse.quote(fn) +
                           "&subfolder=" + urllib.parse.quote(sub) + "&type=" + stype)
                    dest = out_dir / fn
                    with urllib.request.urlopen(url, timeout=120) as r:
                        dest.write_bytes(r.read())
                    print(f"[{slug}] downloaded {dest} ({dest.stat().st_size} bytes)", flush=True)
                    return 0
        if rec and rec.get("status", {}).get("status_str") == "error":
            raise RuntimeError(f"render error: {rec['status']}")
        time.sleep(5)
    raise TimeoutError(f"[{slug}] prompt_id {pid} did not finish")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--loc", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--queue", action="store_true")
    ap.add_argument("--seed-base", type=int, default=800000000000000)
    ap.add_argument("--take", type=int, default=1)
    args = ap.parse_args()

    locs = load_locations()
    if args.list:
        for l in locs:
            print(f"{l['slug']:24s} {l['name']}")
        return 0

    if args.all:
        want = locs
    elif args.loc:
        want = [l for l in locs if l["slug"] == args.loc]
        if not want:
            ap.error(f"unknown location '{args.loc}' (see --list)")
    else:
        ap.error("pass --loc SLUG, --all, or --list")

    for i, l in enumerate(want):
        run_one(l, args.seed_base + i, args.queue, take=args.take)
    return 0


if __name__ == "__main__":
    sys.exit(main())
