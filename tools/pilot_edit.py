#!/usr/bin/env python
"""Pilot Stage-3: Qwen-Image-Edit-2509 garment/prop swap on the 5090.

Fix vs the original pilot: the CLIP is no longer taken from
CheckpointLoaderSimple (which returns null CLIP for the fp8 Qwen-Image-Edit
checkpoint). It is loaded explicitly via CLIPLoader(type=qwen_image) using the
Qwen2.5-VL-7B text encoder (qwen_2.5_vl_7b_fp8_scaled.safetensors). The reference
garment/prop image is handed in as image2 (dual semantic+appearance conditioning).

Native graph (index -> output index):
  CheckpointLoaderSimple -> model[1,0], vae[1,2]
  CLIPLoader(qwen_image) -> clip[2,0]
  VAELoader(qwen_image_vae) -> qwenvae[3,0]
  LoadImage(base) -> image[4,0]
  LoadImage(ref)  -> ref[5,0]                 (optional --ref)
  TextEncodeQwenImageEditPlus(clip[2,0], vae[3,0], image1[4,0], image2[5,0]) -> pos
  TextEncodeQwenImageEditPlus(clip[2,0]) (negative) -> neg
  EmptySD3LatentImage(1344x768, batch 1) -> latent
  ModelSamplingAuraFlow(model, shift 3.1) -> model       (Qwen-Image flow sampler)
  KSampler(model, ...) -> samples
  VAEDecode(qwenvae[3,0]) -> img
  SaveImage

Upload the base + ref, run, download the edited PNG. Prints node_errors/runtime
errors verbatim for iteration.
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.request
import urllib.error

COMFY = os.environ.get("FNI_COMFY", "http://<TOMBSTONE_TS_IP>:8188").rstrip("/")

CKPT = "qwen_image_edit_2509_fp8_e4m3fn_scaled.safetensors"
TEXTENC = "qwen_2.5_vl_7b_fp8_scaled.safetensors"
VAE = "qwen_image_vae.safetensors"


def _post(url, payload, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _get(url, timeout=120):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode())


def upload_image(path: str) -> str:
    boundary = "----fni"
    fname = os.path.basename(path)
    with open(path, "rb") as f:
        data = f.read()
    body = (f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="image"; filename="{fname}"\r\n'
            f"Content-Type: image/png\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(f"{COMFY}/upload/image", data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.loads(r.read().decode())
    return resp["name"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--ref", default=None, help="reference image (garment/prop) -> image2")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--negative", default="")
    ap.add_argument("--width", type=int, default=1344)
    ap.add_argument("--height", type=int, default=768)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--cfg", type=float, default=4.0)
    ap.add_argument("--seed", type=int, default=424242)
    ap.add_argument("--outdir", default="renders/pilot/teegra-edit")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    up_base = upload_image(args.base)
    print(f"uploaded base as {up_base}", flush=True)

    up_ref = None
    if args.ref:
        up_ref = upload_image(args.ref)
        print(f"uploaded ref as {up_ref}", flush=True)

    g = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        "2": {"class_type": "CLIPLoader",
              "inputs": {"clip_name": TEXTENC, "type": "qwen_image"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "4": {"class_type": "LoadImage", "inputs": {"image": up_base}},
        "6": {"class_type": "TextEncodeQwenImageEditPlus",
              "inputs": {"clip": ["2", 0], "prompt": args.prompt,
                         "vae": ["3", 0], "image1": ["4", 0]}},
        "7": {"class_type": "TextEncodeQwenImageEditPlus",
              "inputs": {"clip": ["2", 0], "prompt": args.negative}},
        "8": {"class_type": "EmptySD3LatentImage",
              "inputs": {"width": args.width, "height": args.height, "batch_size": 1}},
        "9": {"class_type": "ModelSamplingAuraFlow",
              "inputs": {"model": ["1", 0], "shift": 3.1}},
        "10": {"class_type": "KSampler",
               "inputs": {"model": ["9", 0], "seed": args.seed, "steps": args.steps,
                          "cfg": args.cfg, "sampler_name": "euler", "scheduler": "simple",
                          "positive": ["6", 0], "negative": ["7", 0],
                          "latent_image": ["8", 0], "denoise": 1.0}},
        "11": {"class_type": "VAEDecode", "inputs": {"samples": ["10", 0], "vae": ["3", 0]}},
        "12": {"class_type": "SaveImage",
               "inputs": {"filename_prefix": "teegra_edit", "images": ["11", 0]}},
    }
    if up_ref:
        g["5"] = {"class_type": "LoadImage", "inputs": {"image": up_ref}}
        g["6"]["inputs"]["image2"] = ["5", 0]

    cid = f"fni-edit-{int(time.time())}"
    resp = _post(f"{COMFY}/prompt", {"prompt": g, "client_id": cid})
    if resp.get("node_errors"):
        print("NODE ERRORS:", json.dumps(resp["node_errors"], indent=2))
        return 2
    pid = resp["prompt_id"]
    print(f"queued prompt_id={pid}", flush=True)

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
                    sub = img.get("subfolder", "")
                    stype = img.get("type", "output")
                    url = f"{COMFY}/view?filename={fn}&subfolder={sub}&type={stype}"
                    dest = os.path.join(args.outdir, fn)
                    with urllib.request.urlopen(url, timeout=60) as r:
                        open(dest, "wb").write(r.read())
                    print(f"downloaded {dest}", flush=True)
            return 0
        if rec and rec.get("status", {}).get("status_str") == "error":
            print("RUNTIME ERROR:", json.dumps(rec["status"], indent=2))
            return 2
        time.sleep(3)
    print("TIMEOUT: edit did not finish")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())