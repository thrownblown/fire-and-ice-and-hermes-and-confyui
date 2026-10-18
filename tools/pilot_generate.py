#!/usr/bin/env python
"""Pilot Stage-1: generate a clean Krea2 base still of Teegra on the 5090.

Reuses the saved Krea2 workflow graph (probes/krea2_5090_template.json) but replaces the
prompt with a clean SFW pilot prompt and disables the NSFW/celebrity character LoRAs
(lora_1 person_29 'person_29', lora_10 person_21), keeping only the house retro-fantasy LoRA.
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.request
import urllib.error

COMFY = os.environ.get("FNI_COMFY", "http://<TOMBSTONE_TS_IP>:8188").rstrip("/")


def _post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def _get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workflow", required=True)
    ap.add_argument("--seed", type=int, default=82036621553915)
    ap.add_argument("--outdir", default="renders/pilot/teegra-base")
    ap.add_argument("--main", required=True)
    ap.add_argument("--pre", required=True)
    args = ap.parse_args()

    g = json.load(open(args.workflow, encoding="utf-8"))

    # prompts
    g["135"]["inputs"]["positive"] = args.main   # main description
    g["137"]["inputs"]["positive"] = args.pre    # pre-prompt (style)
    g["136"]["inputs"]["positive"] = ""          # post

    # LoRAs: turn off person_29 (lora_1) and person_21 (lora_10); keep retro-fantasy (lora_7)
    g["124"]["inputs"]["lora_1"]["on"] = False   # RLY-person-KREA2-person_29 (NSFW)
    g["124"]["inputs"]["lora_10"]["on"] = False  # krea2_person_21 (celebrity)
    g["124"]["inputs"]["lora_7"]["on"] = True    # retro-fantasy (house style)
    g["124"]["inputs"]["lora_7"]["strength"] = 1.0

    g["102"]["inputs"]["seed"] = args.seed

    tag = f"teegra_pilot_s{args.seed}"
    g["128"]["inputs"]["filename_prefix"] = tag

    os.makedirs(args.outdir, exist_ok=True)
    cid = f"fni-pilot-{int(time.time())}"
    pid = _post(f"{COMFY}/prompt", {"prompt": g, "client_id": cid})["prompt_id"]
    print(f"queued prompt_id={pid}", flush=True)

    deadline = time.time() + 900
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
            return
        if rec and rec.get("status", {}).get("status_str") == "error":
            raise RuntimeError(f"render error: {json.dumps(rec['status'])}")
        time.sleep(3)
    raise TimeoutError("render timed out")


if __name__ == "__main__":
    main()
