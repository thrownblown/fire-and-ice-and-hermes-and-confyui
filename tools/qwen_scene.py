# spicy-ok: this file names a checkpoint the pipeline requires (Qwen-Rapid-AIO-NSFW-v22.safetensors) — a model id, not content
# -*- coding: utf-8 -*-
"""Qwen-Image-Edit scene setup: compose a character still INTO a scene still.

Reproduces the proven "qwedit" graph (renders/FNIgens/2026-10-16/qwedit_*.png):
checkpoint Qwen-Rapid-AIO-NSFW-v22 (a Qwen-Image-Edit 4-step rapid merge that
bundles its own CLIP + VAE), TextEncodeQwenImageEditPlus with up to three
reference images, sa_solver/beta 4-step sampler, tiled VAE decode.

The three image slots:
  image1 (--base) = the character still (the subject to keep).
  image2 (--ref2) = optional second reference (a pose / subject / prop photo).
  image3 (--ref3) = optional third reference (e.g. a source film frame for framing).

The prompt is the scene direction — place the character into a setting while
keeping their face/costume. This produces the INITIAL SHOT STILL that H3 I2V
then animates (tools/h3_scene.py --still <scene still>), instead of asking H3
to paint the scene from text alone.

    .venv/Scripts/python.exe tools/qwen_scene.py \
        --base runs/subhuman-krea2/output/darkwolf/darkwolf_30s+80s+rf_person_11_00002_.png \
        --prompt "place the dark-haired barbarian before a circle of standing stones under a storm sky, green shamanic fire coiling around his open hands, keep his face and fur-and-hide costume unchanged, full body, mid shot" \
        --char darkwolf --prefix scene_darkwolf_test
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(r"E:/FNI")
RUN = ROOT / "runs" / "subhuman-krea2"
OUTDIR = RUN / "scenes" / "stills"

CKPT = "Qwen-Rapid-AIO-NSFW-v22.safetensors"

# node ids, kept identical to the proven qwedit graph
N_CKPT = "1"       # CheckpointLoaderSimple -> model[0], clip[1], vae[2]
N_LORA = "16"      # Power Lora Loader (rgthree) -> model
N_POS = "3"        # TextEncodeQwenImageEditPlus (positive)
N_NEG = "4"        # TextEncodeQwenImageEditPlus (negative)
N_LATENT = "9"     # EmptyLatentImage
N_SAMPLER = "2"    # KSampler
N_DECODE = "12"    # VAEDecodeTiled
N_SAVE = "11"      # SaveImage
N_IMG1 = "10"      # LoadImage base
N_IMG2 = "18"      # LoadImage ref2
N_IMG3 = "17"      # LoadImage ref3


def _post(url, payload, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _get(url, timeout=120):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode())


def upload(path):
    """Upload an image to the render host's input/ and return its name."""
    fname = os.path.basename(path)
    with open(path, "rb") as f:
        data = f.read()
    boundary = "----fni"
    body = (f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="image"; filename="{fname}"\r\n'
            f"Content-Type: image/png\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(f"{COMFY}/upload/image", data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.loads(r.read().decode())
    return resp["name"]


def build_graph(args, up1, up2, up3):
    g = {
        N_CKPT: {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        N_LORA: {"class_type": "Power Lora Loader (rgthree)",
                 "inputs": {
                     "PowerLoraLoaderHeaderWidget": {"type": "PowerLoraLoaderHeaderWidget"},
                     "lora_1": {"on": False, "lora": "qwen/misc/Qwen-Image-Edit-2509-Lightning-8steps-V1.0-bf16.safetensors", "strength": 1},
                     "lora_2": {"on": False, "lora": "qwen/misc/Qwen-Image-Edit-2509-Lightning-8steps-V1.0-fp32.safetensors", "strength": 1},
                     "lora_3": {"on": False, "lora": "qwen/extract-outfit_v3.safetensors", "strength": 1.54},
                     "lora_4": {"on": False, "lora": "qwen/clothtransfer.safetensors", "strength": 1},
                     "\u2795 Add Lora": "",
                     "model": [N_CKPT, 0],
                 }},
        N_POS: {"class_type": "TextEncodeQwenImageEditPlus",
                "inputs": {"prompt": args.prompt, "clip": [N_CKPT, 1], "vae": [N_CKPT, 2],
                           "image1": [N_IMG1, 0]}},
        N_NEG: {"class_type": "TextEncodeQwenImageEditPlus",
                "inputs": {"prompt": "", "clip": [N_CKPT, 1], "vae": [N_CKPT, 2]}},
        N_LATENT: {"class_type": "EmptyLatentImage",
                   "inputs": {"width": args.width, "height": args.height, "batch_size": 1}},
        N_SAMPLER: {"class_type": "KSampler",
                    "inputs": {"seed": args.seed, "steps": args.steps, "cfg": args.cfg,
                               "sampler_name": args.sampler, "scheduler": args.scheduler,
                               "denoise": 1.0, "model": [N_LORA, 0], "positive": [N_POS, 0],
                               "negative": [N_NEG, 0], "latent_image": [N_LATENT, 0]}},
        N_DECODE: {"class_type": "VAEDecodeTiled",
                   "inputs": {"tile_size": 256, "overlap": 64, "temporal_size": 64,
                              "temporal_overlap": 8, "samples": [N_SAMPLER, 0],
                              "vae": [N_CKPT, 2]}},
        N_SAVE: {"class_type": "SaveImage",
                 "inputs": {"filename_prefix": args.prefix, "images": [N_DECODE, 0]}},
        N_IMG1: {"class_type": "LoadImage", "inputs": {"image": up1}},
    }
    if up2:
        g[N_IMG2] = {"class_type": "LoadImage", "inputs": {"image": up2}}
        g[N_POS]["inputs"]["image2"] = [N_IMG2, 0]
    if up3:
        g[N_IMG3] = {"class_type": "LoadImage", "inputs": {"image": up3}}
        g[N_POS]["inputs"]["image3"] = [N_IMG3, 0]
    return g


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", required=True, help="character still -> image1 (subject to keep)")
    ap.add_argument("--ref2", default=None, help="optional second reference -> image2")
    ap.add_argument("--ref3", default=None, help="optional third reference -> image3 (e.g. source frame)")
    ap.add_argument("--prompt", required=True, help="scene direction")
    ap.add_argument("--char", default="scene")
    ap.add_argument("--prefix", default=None)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=960)
    ap.add_argument("--steps", type=int, default=4)
    ap.add_argument("--cfg", type=float, default=1.0)
    ap.add_argument("--sampler", default="sa_solver")
    ap.add_argument("--scheduler", default="beta")
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--outdir", default=str(OUTDIR))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--comfy", default=os.environ.get("FNI_COMFY", "http://<TOMBSTONE_TS_IP>:8188"))
    args = ap.parse_args()

    global COMFY
    COMFY = args.comfy.rstrip("/")
    if not args.prefix:
        args.prefix = "scene_%s_%s" % (args.char, Path(args.base).stem)

    base = Path(args.base)
    if not base.exists():
        raise SystemExit("base still not found: %s" % base)

    if args.dry_run:
        print("comfy:", COMFY)
        print("base:", base)
        print("ref2:", args.ref2, "| ref3:", args.ref3)
        print("prompt:", args.prompt)
        print("size %dx%d steps=%d cfg=%s %s/%s prefix=%s seed=%d"
              % (args.width, args.height, args.steps, args.cfg, args.sampler,
                 args.scheduler, args.prefix, args.seed))
        return

    up1 = upload(str(base))
    print("uploaded base ->", up1, flush=True)
    up2 = upload(args.ref2) if args.ref2 else None
    if up2:
        print("uploaded ref2 ->", up2, flush=True)
    up3 = upload(args.ref3) if args.ref3 else None
    if up3:
        print("uploaded ref3 ->", up3, flush=True)

    g = build_graph(args, up1, up2, up3)
    cid = "fni-qwscene-%d" % int(time.time())
    resp = _post(f"{COMFY}/prompt", {"prompt": g, "client_id": cid})
    if resp.get("node_errors"):
        print("NODE ERRORS:", json.dumps(resp["node_errors"], indent=2))
        return 2
    pid = resp["prompt_id"]
    print("queued prompt_id=", pid, flush=True)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + 1200
    while time.time() < deadline:
        try:
            h = _get(f"{COMFY}/history/{pid}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                time.sleep(3)
                continue
            raise
        rec = h.get(pid)
        if rec and rec.get("outputs"):
            for node_id, out in rec["outputs"].items():
                for img in out.get("images", []):
                    fn = img["filename"]
                    if "ComfyUI_temp" in fn:
                        continue
                    sub = img.get("subfolder", "")
                    stype = img.get("type", "output")
                    url = f"{COMFY}/view?filename={fn}&subfolder={sub}&type={stype}"
                    dest = outdir / fn
                    with urllib.request.urlopen(url, timeout=120) as r:
                        dest.write_bytes(r.read())
                    print("downloaded scene still ->", dest, dest.stat().st_size, "bytes", flush=True)
            return 0
        if rec and rec.get("status", {}).get("status_str") == "error":
            print("RUNTIME ERROR:", json.dumps(rec["status"], indent=2))
            return 2
        time.sleep(4)
    print("TIMEOUT: scene setup did not finish")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
