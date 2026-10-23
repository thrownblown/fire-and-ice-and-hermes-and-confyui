#!/usr/bin/env python
"""Bulk-generate reference stills on the 4090 (Krea2 turbo + retro-fantasy).

~10 variants per character (12) and per canonical location (21) — the "lots more
refs" batch. Grounds every character prompt in CANONICAL identity (the stable
trait set, never color/wardrobe read off the 1983 palette), varies ONLY the
non-identity dimensions (pose, gaze, framing, lighting, background) with a unique
seed each. Location prompts come from manifests/locations.json (canonical).

Template: C:/Users/gsfny/Downloads/80sfantasykreatest.json (finepornV2TURBOKrea2_v20
+ retro-fantasy LoRA, 9 steps er_sde/sgm_uniform cfg 1, 16:9 2MP). Node ids as in
probes/krea_4090_batches.py: 135=main, 137=pre/style, 124=lora loader, 102=sampler,
128=save. retro-fantasy (lora_7) always ON @1.0; person_27 (lora_1) OFF (identity hijack).

Usage:
    .venv/Scripts/python.exe tools/gen_refs_batch_4090.py --count 10 --dry-run
    .venv/Scripts/python.exe tools/gen_refs_batch_4090.py --count 10
Output: renders/4090/refs-batch-<ts>/ with chars/ + plates/ + manifest.jsonl.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(r"E:/FNI")
COMFY = "http://127.0.0.1:8188"          # the 4090 (mh370), NOT the 5090
TEMPLATE = Path(r"C:/Users/gsfny/Downloads/80sfantasykreatest.json")

STYLE = ("retr0fantasy, 60s Soviet fantasy-film, subtle film grain, "
         "aged theatrical print quality")

# canonical identity cores — STABLE traits only. Never re-describe from VLM reads.
CHARACTERS = {
    "TEEGRA": "young adult woman, slim, pale skin, green eyes, very long straight "
              "black hair with bangs, wearing a light purple two-piece costume and a "
              "gold necklace",
    "TUTOR": "young adult woman, slender, light brown skin, dark brown eyes, black hair "
             "in a bob with bangs, wearing a light blue bandeau top and matching skirt, "
             "a broad gold collar and a belt of gold medallions",
    "DARKWOLF": "a towering middle-aged man, deep tanned bronze skin, yellow eyes, long "
                "black hair in two thick braids, a wolf-head helmet, bare oiled chest, "
                "a wide fur-lined belt with bronze plates and a leather loincloth, a "
                "necklace of teeth and a small skull",
    "LARN": "a young man, sun-tanned bronze skin, blue eyes, blond shoulder-length hair "
            "in a braid, gold hoop earrings, bare chest, a brown leather belt with a gold "
            "buckle and a bone necklace",
    "JAROL": "an older king, light brown skin, a bald head, a long white beard, wearing "
             "a red sleeveless tunic and gold armbands and a gold hoop earring",
    "TARO": "a young man, tanned skin, long straight black hair, thick dark brows, "
            "wearing a red vest and gold armbands",
    "ROLIEL": "a woman, light beige skin, orange eyes, long red hair, wearing a flowing "
              "white robe with a dark belt, a blue beaded choker and blue bracelets",
    "OTWA": "a huge muscular middle-aged man, pale skin, a gaunt weathered face, long "
            "red hair, wearing a brown loincloth",
    "SHAITAN": "a large black panther with yellow eyes and white whiskers",
    "SPIRIT": "a skeletal humanoid figure, white hair, black eye sockets, wearing a "
              "black garment",
    "JULIANA": "a pale woman, stark white skin, an angular face, very long straight "
               "jet-black hair, red lips, wearing a deep purple long-sleeved gown with "
               "high leg slits and long silver drop earrings",
    "NEKRON": "a pale man, very long straight white hair, narrow intense eyes, wearing "
              "dark purple robes with black trim",
}

POSES = [
    "standing confidently facing the viewer",
    "in a three-quarter side profile",
    "walking forward",
    "hands resting on the hips",
    "turning back over the shoulder toward the viewer",
    "seated, one hand resting on a knee",
    "arms crossed over the chest",
    "reaching forward with one hand",
]
GAZES = [
    "looking directly at the viewer",
    "gazing off to the side",
    "calm, even expression",
    "a faint knowing half-smile",
    "lips slightly parted",
    "eyes wide and watchful",
]
FRAMING = ["medium shot", "wide shot", "close-up", "full-body shot", "three-quarter view"]
LIGHTING = [
    "soft golden-hour light", "cool blue twilight", "harsh mid-day sun", "firelight",
    "diffuse overcast light", "moonlight",
]
BACKGROUNDS = [
    "a lush dark jungle with heavy foliage", "a steaming swamp with still water",
    "the blue-lit mouth of an ice cave", "a dense forest clearing at dusk",
    "rocky terrain under a storm sky", "a firelit cave interior",
    "a matte-painted fantasy vista", "a stone hall with heavy drapery",
]


def load_locations() -> list[dict]:
    m = json.loads((ROOT / "manifests" / "locations.json").read_text(encoding="utf-8"))
    return m["canonical_locations"]


def _post(path, body, timeout=90):
    req = urllib.request.Request(COMFY + path, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, data=json.dumps(body).encode(), timeout=timeout) as r:
        return json.loads(r.read().decode() or "null")


def _get(path, timeout=60):
    with urllib.request.urlopen(COMFY + path, timeout=timeout) as r:
        return json.loads(r.read().decode() or "null")


def build_char_prompt(name, rng):
    c = CHARACTERS[name]
    extra = (f"{rng.choice(POSES)}, {rng.choice(GAZES)}. "
             f"Background: {rng.choice(BACKGROUNDS)}. {rng.choice(FRAMING)}.")
    return f"{c}, {extra}"


def build_plate_prompt(loc, rng):
    return f"{loc['prompt']}. Lighting: {rng.choice(LIGHTING)}. {rng.choice(FRAMING)}."


def build_graph(main_prompt):
    g = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    g["135"]["inputs"]["positive"] = main_prompt
    g["137"]["inputs"]["positive"] = STYLE + ","
    loras = g["124"]["inputs"]
    for slot in range(1, 8):
        e = loras.get(f"lora_{slot}")
        if isinstance(e, dict):
            e["on"] = False
    loras["lora_7"]["on"] = True          # retro-fantasy
    loras["lora_7"]["strength"] = 1.0
    return g


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--count", type=int, default=10)
    ap.add_argument("--seed-base", type=int, default=910000000000000)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = ROOT / "renders" / "4090" / f"refs-batch-{ts}"
    (dest / "chars").mkdir(parents=True, exist_ok=True)
    (dest / "plates").mkdir(parents=True, exist_ok=True)
    man_path = dest / "manifest.jsonl"
    man = open(man_path, "w", encoding="utf-8")

    jobs = []   # (prefix, main_prompt, subdir, seed)
    rng = random.Random(args.seed_base)
    for name in CHARACTERS:
        for i in range(args.count):
            seed = rng.randrange(0, 1 << 60)
            jobs.append((f"ch_{name}_{i:02d}", build_char_prompt(name, rng), "chars", seed))
    for loc in load_locations():
        for i in range(args.count):
            seed = rng.randrange(0, 1 << 60)
            jobs.append((f"pl_{loc['slug']}_{i:02d}", build_plate_prompt(loc, rng), "plates", seed))

    print(f"{len(jobs)} jobs ({len(CHARACTERS)} chars x{args.count} + "
          f"{len(load_locations())} locations x{args.count}) -> {dest}")

    queued = {}
    for prefix, prompt, sub, seed in jobs:
        man.write(json.dumps({"prefix": prefix, "subdir": sub, "seed": seed,
                              "prompt": prompt, "prompt_id": None}) + "\n")
        if args.dry_run:
            continue
        g = build_graph(prompt)
        g["102"]["inputs"]["seed"] = seed
        g["128"]["inputs"]["filename_prefix"] = prefix
        try:
            r = _post("/prompt", {"prompt": g, "client_id": "hermes-refs-batch"})
            queued[prefix] = r["prompt_id"]
        except urllib.error.HTTPError as e:
            print(f"QUEUE FAILED {prefix}: HTTP {e.code} {e.read().decode()[:200]}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"QUEUE FAILED {prefix}: {e}", flush=True)
        time.sleep(0.5)

    if args.dry_run:
        man.close()
        print("dry-run: manifest written, nothing queued")
        return 0

    man.close()

    # poll + download
    done = {}
    deadline = time.time() + 3600 * 6
    while time.time() < deadline and len(done) < len(queued):
        for prefix, pid in list(queued.items()):
            if prefix in done:
                continue
            try:
                h = _get(f"/history/{pid}")
            except Exception:  # noqa: BLE001
                continue
            rec = h.get(pid) or {}
            status = (rec.get("status") or {}).get("status_str", "")
            # only the SaveImage output (type output); skip PreviewImage (type temp)
            # which duplicates every frame under ComfyUI_temp_*.png
            imgs = [im for o in (rec.get("outputs") or {}).values()
                    for im in (o.get("images") or [])
                    if im.get("type", "output") != "temp"]
            if status == "success" or imgs:
                for im in imgs:
                    q = urllib.parse.urlencode({"filename": im["filename"],
                                                "subfolder": im.get("subfolder", ""),
                                                "type": im.get("type", "output")})
                    data = urllib.request.urlopen(f"{COMFY}/view?{q}", timeout=300).read()
                    sub = "chars" if prefix.startswith("ch_") else "plates"
                    out = dest / sub / im["filename"]
                    out.write_bytes(data)
                done[prefix] = len(imgs)
                print(f"done {prefix}: {status} ({len(imgs)})", flush=True)
            elif status == "error":
                done[prefix] = 0
                print(f"ERROR {prefix}: {json.dumps(rec.get('status'))[:300]}", flush=True)
        time.sleep(5)

    n_ok = sum(1 for v in done.values() if v > 0)
    n_fail = sum(1 for v in done.values() if v == 0)
    print(f"\nDONE: {n_ok} ok, {n_fail} failed, {len(queued) - len(done)} unfinished")
    print(f"output: {dest}")
    return 0 if n_fail == 0 and len(done) == len(queued) else 1


if __name__ == "__main__":
    sys.exit(main())
