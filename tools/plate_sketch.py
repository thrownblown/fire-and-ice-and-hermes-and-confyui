#!/usr/bin/env python3
"""Sketch -> master plate, on the 4090. Z-Image Turbo + Fun ControlNet Union.

Turn a rough hand drawing of a camera setup (framing, subject placement, camera
height) into a finished environment plate. This is the plate generator the v3.1
plan needs — one plate per setup — and it runs on the 4090, NOT the 5090, so it
never competes with the H3 render queue.

Graph is the ComfyUI core blueprint "ControlNet (Z-Image-Turbo)"
(`ComfyUI/blueprints/ControlNet (Z-Image-Turbo).json`) in API form:
  UNETLoader(z_image_turbo) + CLIPLoader(qwen3-4b, type=lumina2) + VAELoader(ae)
  + ModelPatchLoader(Z-Image-Turbo-Fun-Controlnet-Union) -> ZImageFunControlnet
  -> ModelSamplingAuraFlow(shift 3) -> KSampler(res_multistep/simple, 8 steps, cfg 1)
  -> VAEDecode. Negative conditioning is zeroed; latent size follows the sketch.

Usage
-----
  # inspect the graph without a server (default when ComfyUI is not reachable)
  .venv/Scripts/python.exe tools/plate_sketch.py --sketch path/to/sketch.png \
      --prompt "empty Fire Keep study, painted matte, no people" --dry-run

  # queue it (ComfyUI must be running on the 4090)
  .venv/Scripts/python.exe tools/plate_sketch.py --sketch ... --prompt ... \
      --out S05-A-plate

Notes
-----
- The control image should be an ENVIRONMENT sketch with no characters — the
  plate is the shared background for a setup; characters are added at H3 time.
- `--strength` 1.0 holds the sketch tightly; drop to ~0.6 to let the model
  invent more while keeping the layout.
- The text encoder is a Qwen3-4B. The official file is `qwen_3_4b.safetensors`
  (from Comfy-Org/z_image_turbo); this box has `Qwen3-4B-abliterated.safetensors`,
  which is a finetune of the same base. Both are offered, abliterated first if
  the official one is absent.
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request

DEFAULT_URL = os.environ.get("FNI_PLATE_COMFY", "http://127.0.0.1:8188")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UNET_PREF = ["zit/z_image_turbo_bf16.safetensors", "z_image_turbo_bf16.safetensors",
             "zit/zImageTurboAIO_zImageTurboBF16AIO.safetensors"]
CLIP_PREF = ["qwen_3_4b.safetensors", "Qwen3-4B-abliterated.safetensors",
             "Qwen3-4B-abliterated-v2.safetensors"]
VAE_PREF = ["ae.safetensors", "z-image-vae.safetensors"]
PATCH_PREF = ["Z-Image-Turbo-Fun-Controlnet-Union.safetensors"]


def get(base, path, timeout=30):
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return json.load(r)


def first_present(prefs, available, label):
    for p in prefs:
        if p in available:
            return p
    raise SystemExit(
        "no %s found on the server.\n  wanted one of: %s\n  server has: %s"
        % (label, ", ".join(prefs),
           ", ".join(sorted(available)[:12]) or "(none)"))


def build_graph(unet, clip, vae, patch, image_name, prompt, seed, steps,
                cfg, sampler, scheduler, shift, strength, prefix,
                width=None, height=None):
    """API-format graph, node ids as strings."""
    g = {
        "1": {"class_type": "UNETLoader",
              "inputs": {"unet_name": unet, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader",
              "inputs": {"clip_name": clip, "type": "lumina2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": vae}},
        "4": {"class_type": "ModelPatchLoader", "inputs": {"name": patch}},
        "5": {"class_type": "LoadImage", "inputs": {"image": image_name, "upload": "image"}},
        "6": {"class_type": "CLIPTextEncode",
              "inputs": {"clip": ["2", 0], "text": prompt}},
        "7": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "10": {"class_type": "ZImageFunControlnet",
               "inputs": {"model": ["1", 0], "model_patch": ["4", 0], "vae": ["3", 0],
                          "image": ["5", 0], "strength": strength}},
        "11": {"class_type": "ModelSamplingAuraFlow",
               "inputs": {"model": ["10", 0], "shift": shift}},
        "12": {"class_type": "KSampler",
               "inputs": {"model": ["11", 0], "positive": ["6", 0], "negative": ["7", 0],
                          "latent_image": ["8", 0], "seed": seed, "steps": steps,
                          "cfg": cfg, "sampler_name": sampler, "scheduler": scheduler,
                          "denoise": 1.0}},
        "13": {"class_type": "VAEDecode",
               "inputs": {"samples": ["12", 0], "vae": ["3", 0]}},
        "14": {"class_type": "SaveImage",
               "inputs": {"images": ["13", 0], "filename_prefix": prefix}},
    }
    if width and height:
        g["8"] = {"class_type": "EmptySD3LatentImage",
                  "inputs": {"width": width, "height": height, "batch_size": 1}}
    else:
        # size follows the sketch, matching the blueprint
        g["9"] = {"class_type": "GetImageSize", "inputs": {"image": ["5", 0]}}
        g["8"] = {"class_type": "EmptySD3LatentImage",
                  "inputs": {"width": ["9", 0], "height": ["9", 1], "batch_size": 1}}
    return g


def upload(base, path):
    """POST the sketch to /upload/image, return the server-side filename."""
    boundary = "----fniplate"
    fn = os.path.basename(path)
    with open(path, "rb") as f:
        data = f.read()
    body = b"".join([
        ("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
         "Content-Type: application/octet-stream\r\n\r\n" % (boundary, fn)).encode(),
        data,
        ("\r\n--%s\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n"
         "--%s--\r\n" % (boundary, boundary)).encode(),
    ])
    req = urllib.request.Request(base + "/upload/image", data=body, method="POST")
    req.add_header("Content-Type", "multipart/form-data; boundary=%s" % boundary)
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.load(r)
    return out.get("name") or fn


def main():
    ap = argparse.ArgumentParser(description="Sketch -> master plate (Z-Image Turbo + Fun ControlNet)")
    ap.add_argument("--sketch", required=True, help="rough drawing of the setup (png/jpg)")
    ap.add_argument("--prompt", required=True, help="plate description (environment only, no people)")
    ap.add_argument("--out", default=None, help="output filename prefix (default: plate_<sketch>)")
    ap.add_argument("--seed", type=int, default=0, help="0 = random")
    ap.add_argument("--steps", type=int, default=8)
    ap.add_argument("--cfg", type=float, default=1.0)
    ap.add_argument("--sampler", default="res_multistep")
    ap.add_argument("--scheduler", default="simple")
    ap.add_argument("--shift", type=float, default=3.0)
    ap.add_argument("--strength", type=float, default=1.0,
                    help="controlnet strength; 1.0 = hold the sketch tightly")
    ap.add_argument("--width", type=int, default=None)
    ap.add_argument("--height", type=int, default=None)
    ap.add_argument("--unet", default=None)
    ap.add_argument("--clip", default=None)
    ap.add_argument("--vae", default=None)
    ap.add_argument("--patch", default=None)
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--dry-run", action="store_true", help="write the graph, do not queue")
    a = ap.parse_args()

    prefix = a.out or ("plate_" + os.path.splitext(os.path.basename(a.sketch))[0])
    seed = a.seed if a.seed else 1

    try:
        oi = get(a.url, "/object_info", timeout=15)
        live = True
    except Exception as e:  # noqa: BLE001
        print("ComfyUI not reachable at %s (%s)" % (a.url, e))
        live = False
        oi = None

    if live:
        assert oi is not None  # set above whenever live is True
        unet = a.unet or first_present(UNET_PREF, oi["UNETLoader"]["input"]["required"]["unet_name"][0], "Z-Image diffusion model")
        clip = a.clip or first_present(CLIP_PREF, oi["CLIPLoader"]["input"]["required"]["clip_name"][0], "Qwen3-4B text encoder")
        vae = a.vae or first_present(VAE_PREF, oi["VAELoader"]["input"]["required"]["vae_name"][0], "VAE")
        patch = a.patch or first_present(PATCH_PREF, oi["ModelPatchLoader"]["input"]["required"]["name"][0], "Fun ControlNet patch")
        missing = [n for n in ("ZImageFunControlnet", "ModelPatchLoader", "ModelSamplingAuraFlow")
                   if n not in oi]
        if missing:
            raise SystemExit("server is missing nodes: %s (update ComfyUI)" % ", ".join(missing))
    else:
        unet = a.unet or UNET_PREF[0]
        clip = a.clip or CLIP_PREF[1]
        vae = a.vae or VAE_PREF[0]
        patch = a.patch or PATCH_PREF[0]

    image_name = os.path.basename(a.sketch)
    if live and not a.dry_run:
        image_name = upload(a.url, a.sketch)
        print("uploaded sketch ->", image_name)

    g = build_graph(unet, clip, vae, patch, image_name, a.prompt, seed, a.steps,
                    a.cfg, a.sampler, a.scheduler, a.shift, a.strength, prefix,
                    a.width, a.height)

    print("graph: unet=%s\n       clip=%s (lumina2)\n       vae=%s\n       patch=%s"
          % (unet, clip, vae, patch))
    outdir = os.path.join(ROOT, "plates", "graphs")
    os.makedirs(outdir, exist_ok=True)
    gpath = os.path.join(outdir, prefix + ".json")
    with open(gpath, "w", encoding="utf-8") as f:
        json.dump(g, f, indent=1)
    print("wrote", gpath)

    if a.dry_run or not live:
        if not live:
            print("ComfyUI is not running — start it on the 4090 and re-run without --dry-run.")
        return

    req = urllib.request.Request(a.url + "/prompt",
                                data=json.dumps({"prompt": g}).encode(),
                                method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as r:
        pid = json.load(r)["prompt_id"]
    print("queued prompt_id", pid)
    # wait for it
    while True:
        time.sleep(3)
        try:
            h = get(a.url, "/history/" + pid)
        except Exception:  # noqa: BLE001
            continue
        if pid in h:
            entry = h[pid]
            status = entry.get("status", {})
            if status.get("status_str") == "error" or not status.get("completed", True):
                print("ERROR:", json.dumps(status)[:600])
                return
            for node_out in entry.get("outputs", {}).values():
                for im in node_out.get("images", []):
                    print("OUTPUT: %s/%s  (subfolder=%r type=%r)"
                          % (a.url, im.get("filename"), im.get("subfolder"), im.get("type")))
            return


if __name__ == "__main__":
    main()
