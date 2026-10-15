#!/usr/bin/env python3
"""Translate the real 1983 film stills into the 80s retro look.

For each real frame (refs/characters/TEEGRA/shot_*.jpg) we:
  1. caption it with the local VLM (pose / action / expression / setting / framing
     ONLY — identity is imposed below, not read from the noisy 1983 palette),
  2. re-render that composition through the Krea2 workflow with the CANON
     identity (green eyes, pale skin, long black hair, purple two-piece, gold
     necklace) + the retro-fantasy style LoRA,
  3. generate several variants per still (seed + lighting/framing tweak) so one
     real frame becomes many translated stills.

Captions are cached (manifests/teegra_translate_captions.jsonl) so re-runs are free.

    python tools/krea2_teegra_translate.py --variants-per-still 30
"""
import argparse
import base64
import io
import json
import os
import random
import sys
import time
import urllib.request

from PIL import Image

sys.path.insert(0, r"E:/FNI")
sys.path.insert(0, r"E:/FNI/tools")
import krea2_stills as k  # noqa: E402

ROOT = r"E:/FNI"
REFS = os.path.join(ROOT, "refs", "characters", "TEEGRA")
WF = r"C:/Users/gsfny/Downloads/ComfyUI_00108_.json"
CAP_CACHE = os.path.join(ROOT, "manifests", "teegra_translate_captions.jsonl")
API = "http://127.0.0.1:1234/v1/chat/completions"
CAP_MODEL = "qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s"

PRE = ("retr0fantasy, 60s Soviet fantasy-film, subtle film grain, "
       "aged theatrical print quality,")
IDENTITY = ("young adult woman with pale skin and green eyes, very long straight "
            "black hair with bangs, slim build")

LIGHTING = [
    "soft golden-hour light",
    "cool blue twilight",
    "harsh mid-day sun",
    "firelight",
    "diffuse overcast light",
    "moonlight",
]
FRAMING = [
    "medium shot",
    "wide shot",
    "close-up",
    "full-body shot",
    "three-quarter view",
]

CAP_SYS = (
    "You caption one frame from a 1983 rotoscoped fantasy film. Describe ONLY the "
    "composition that must be reproduced: the woman's pose and what she is doing, "
    "her facial expression, her hand/arm positions, the framing (close-up/medium/wide), "
    "and the background setting and mood. Do NOT mention hair color, eye color, skin "
    "tone, or clothing color — those are imposed separately. One plain prose sentence, "
    "no labels, no list."
)


def encode_image(path, max_side=1024):
    im = Image.open(path).convert("RGB")
    if max(im.size) > max_side:
        r = max_side / max(im.size)
        im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def caption(path):
    b64 = encode_image(path)
    body = json.dumps({
        "model": CAP_MODEL, "temperature": 0.3,
        "messages": [
            {"role": "system", "content": CAP_SYS},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                {"type": "text", "text": "Caption the composition."}]}],
        "max_tokens": 200, "stream": False,
    }).encode()
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()


def load_captions():
    caps = {}
    if os.path.exists(CAP_CACHE):
        with open(CAP_CACHE, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                r = json.loads(ln)
                caps[r["file"]] = r["caption"]
    return caps


def real_stills():
    return sorted(fn for fn in os.listdir(REFS)
                  if fn.startswith("shot_") and fn.lower().endswith((".jpg", ".jpeg", ".png")))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--variants-per-still", type=int, default=30)
    ap.add_argument("--seed-base", type=int, default=910000000000)
    ap.add_argument("--outdir", default=r"E:/FNI/renders/5090/teegra-translate")
    ap.add_argument("--workflow", default=WF)
    args = ap.parse_args(argv)

    stills = real_stills()
    print(f"[translate] {len(stills)} real stills, {args.variants_per_still} variants each "
          f"= {len(stills) * args.variants_per_still} stills", flush=True)

    caps = load_captions()
    cache_f = open(CAP_CACHE, "a", encoding="utf-8")
    os.makedirs(args.outdir, exist_ok=True)
    man_f = open(os.path.join(args.outdir, "prompts.jsonl"), "w", encoding="utf-8")

    rng = random.Random(args.seed_base)
    total = 0
    for still in stills:
        path = os.path.join(REFS, still)
        if still not in caps:
            c = caption(path)
            caps[still] = c
            cache_f.write(json.dumps({"file": still, "caption": c}) + "\n")
            cache_f.flush()
            print(f"[caption] {still}: {c}", flush=True)
        else:
            print(f"[caption-cache] {still}", flush=True)

        comp = caps[still]
        for v in range(args.variants_per_still):
            seed = args.seed_base + total
            prompt = (f"{IDENTITY}, {comp}. Lighting: {rng.choice(LIGHTING)}. "
                      f"{rng.choice(FRAMING)}.")
            g = k.load_workflow(args.workflow)
            k.set_prompt(g, main=prompt, pre=PRE)
            k.set_lora(g, "lora_1", on=False, strength=0.0)   # jada OFF
            k.set_lora(g, "lora_7", on=True, strength=1.0)    # retro-fantasy ON
            k.set_seed(g, seed)
            tag = f"tr_{still.split('_')[1]}_{v:02d}"
            k.set_prefix(g, tag)
            cid = f"fni-tr-{total}-{int(time.time())}"
            man_f.write(json.dumps({"i": total, "still": still, "seed": seed,
                                    "prompt": prompt, "prompt_id": None}) + "\n")
            try:
                pid = k.queue_graph(g, cid)
            except Exception as e:
                print(f"[{total}] queue fail {still}: {e}", flush=True)
                total += 1
                continue
            man_f.write(json.dumps({"i": total, "still": still, "seed": seed,
                                    "prompt": prompt, "prompt_id": pid}) + "\n")
            man_f.flush()
            try:
                k.wait_and_download(g, pid, args.outdir)
            except Exception as e:
                print(f"[{total}] download fail ({pid}): {e}", flush=True)
            if total % 25 == 0:
                print(f"[{total}] {tag}", flush=True)
            total += 1

    cache_f.close()
    man_f.close()
    print(f"TRANSLATE DONE: {total} stills from {len(stills)} frames", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))