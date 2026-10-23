#!/usr/bin/env python
"""Generate a technicolor-register character sheet on the 5090 (H3 ref2va still).

Proven recipe: graphs/H3CharSheet_technicolor.json (extracted from the Oct-18
Juliana regen) = H3 ref2va still + retro-fantasy LoRA @1.05 + a single identity
still as <Picture 1>. Style comes from the LoRA + the house-style wording; identity
comes from the still. Vary ONLY the identity still, the character name, and the seed.

Usage:
    .venv/Scripts/python.exe tools/gen_char_sheet.py --char LARN          # dry-run (graph only)
    .venv/Scripts/python.exe tools/gen_char_sheet.py --char LARN --queue  # upload + POST + pull
    .venv/Scripts/python.exe tools/gen_char_sheet.py --all --queue        # all 12, sequential

Identity stills are expected at refs/characters/<NAME>/id_<NAME>.* (staged by the
caller). Output lands in refs/characters/<NAME>/ as <NAME>_sheet_t<NN>.png.
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
TEMPLATE = ROOT / "graphs" / "H3CharSheet_technicolor.json"
COMFY = os.environ.get("FNI_COMFY", "http://<TOMBSTONE_TS_IP>:8188").rstrip("/")

# node ids in the template
NODE_LOAD_IMAGE = "25"
NODE_PROMPT = "28"
NODE_SEED = "12"
NODE_SAVE = "68"
NODE_LORA = "22"

# the 12 characters in this pass (8 missing mains + 4 regenerations)
CHARACTERS = [
    "LARN", "JAROL", "TARO", "ROLIEL", "OTWA", "SHAITAN", "SPIRIT", "TUTOR",
    "TEEGRA", "JULIANA", "NEKRON", "DARKWOLF",
]

# house-style sheet prompt. <NAME> is the only variable; <Picture 1> is the identity still.
PROMPT_TMPL = """integrated_multimodal_description:

subject_definitions:
<NAME> character from <Picture 1>, rendered as a live-action 80s sword-and-sandals fantasy character:

summary:
[reference generation] static image of a character sheet. Keep the identity, face, hair, costume and proportions of <Picture 1>. Render it in the technicolor 80s sword-and-sandals register: practical leather-and-brass costume, broad theatrical performance, vivid saturated color with deep blacks.

retention_analysis:
<NAME>: fully_preserved.

detailed_description:
The target video is a static image of a character sheet on a plain white background. Each element is separate and does not overlap.

[Shot 1] static image. Neutral expression on every view.

1. On the left, a portrait (head and chest) of <NAME>, close up, neutral expression, white background.
2. In the center, four full-body views of <NAME>, neutral stance, arms slightly away from the body: straight from the front, straight from the side, three-quarter back, straight from the back.
3. On the right, exactly 6 circles, 2 columns by 3 rows, nothing else:
   circle 1: a single eye.
   circle 2: the mouth.
   circle 3: one ear with its earring.
   circle 4: a hair color swatch.
   circle 5: a skin color swatch.
   circle 6: an outfit fabric swatch.

overall_soundscape: N/A

non_diegetic_music: N/A"""


def _get(url: str, timeout: int = 30) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _post(url: str, payload: dict, timeout: int = 60) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def find_identity_still(name: str) -> Path:
    d = ROOT / "refs" / "characters" / name
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = d / f"id_{name}{ext}"
        if p.exists():
            return p
    # fall back: any id_* file
    for p in sorted(d.glob("id_*")):
        return p
    raise SystemExit(f"no identity still in {d} (expected id_{name}.*)")


def upload(path: Path) -> str:
    boundary = "----fnisheet"
    fn = path.name
    data = path.read_bytes()
    body = b"".join([
        (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; "
         f"filename=\"{fn}\"\r\nContent-Type: application/octet-stream\r\n\r\n").encode(),
        data,
        (f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\n"
         f"true\r\n--{boundary}--\r\n").encode(),
    ])
    req = urllib.request.Request(COMFY + "/upload/image", data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.loads(r.read().decode())
    return out.get("name") or fn


def build_graph(name: str, still_name: str, seed: int, prefix: str) -> dict:
    g = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    g[NODE_LOAD_IMAGE]["inputs"]["image"] = still_name
    g[NODE_PROMPT]["inputs"]["prompt"] = PROMPT_TMPL.replace("<NAME>", name)
    g[NODE_SEED]["inputs"]["noise_seed"] = seed
    g[NODE_SAVE]["inputs"]["filename_prefix"] = prefix
    return g


def run_one(name: str, seed: int, queue: bool, take: int = 1) -> int:
    still = find_identity_still(name)
    out_dir = ROOT / "refs" / "characters" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{name}_sheet_t{take:02d}"

    still_name = still.name
    if queue:
        still_name = upload(still)
        print(f"[{name}] uploaded identity still -> {still_name}", flush=True)

    g = build_graph(name, still_name, seed, prefix)
    gpath = out_dir / f"{prefix}.graph.json"
    gpath.write_text(json.dumps(g, indent=1), encoding="utf-8")
    print(f"[{name}] graph -> {gpath} (still={still_name}, seed={seed})", flush=True)

    if not queue:
        return 0

    resp = _post(COMFY + "/prompt", {"prompt": g})
    if resp.get("node_errors"):
        raise RuntimeError(f"node_errors: {json.dumps(resp['node_errors'])}")
    pid = resp["prompt_id"]
    print(f"[{name}] queued prompt_id={pid}", flush=True)

    # poll /history then download the PNG
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
                    print(f"[{name}] downloaded {dest} ({dest.stat().st_size} bytes)", flush=True)
                    return 0
        if rec and rec.get("status", {}).get("status_str") == "error":
            raise RuntimeError(f"render error: {rec['status']}")
        time.sleep(5)
    raise TimeoutError(f"[{name}] prompt_id {pid} did not finish")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--char", default=None, help="character name (or '--all')")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--queue", action="store_true", help="upload + POST + pull (default dry-run)")
    ap.add_argument("--seed-base", type=int, default=700000000000000)
    ap.add_argument("--take", type=int, default=1)
    args = ap.parse_args()

    names = CHARACTERS if args.all else ([args.char] if args.char else [])
    if not names:
        ap.error("pass --char NAME or --all")
    for i, name in enumerate(names):
        seed = args.seed_base + i
        run_one(name, seed, args.queue, take=args.take)
    return 0


if __name__ == "__main__":
    sys.exit(main())
