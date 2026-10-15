#!/usr/bin/env python3
"""Hundreds of Krea2 Teegra stills, prompts composed from the VLM lens profile.

Grounds every prompt in the STABLE traits from library/char/profiles/TEEGRA.json
(young adult female, slim, light brown skin, long straight black hair with bangs,
oval face, near-black eyes, purple garment, gold necklace) and varies only the
non-identity dimensions: pose, gaze, wardrobe wording, background, framing.

jada char LoRA stays OFF (identity hijack — see prior batch); retro-fantasy
style LoRA stays ON @1.0. Seed varies per still.

    python tools/krea2_teegra_many.py --count 300 [--seed-base N] [--outdir PATH]
"""
import argparse
import json
import random
import sys
import os
import time

sys.path.insert(0, r"E:/FNI")
sys.path.insert(0, r"E:/FNI/tools")
import krea2_stills as k  # noqa: E402

ROOT = r"E:/FNI"
WF = r"C:/Users/gsfny/Downloads/ComfyUI_00108_.json"

PRE_NO_JADA = ("retr0fantasy, 60s Soviet fantasy-film, subtle film grain, "
               "aged theatrical print quality, caucasian,")

# --- stable identity core (from the VLM profile: stable traits only) ---
IDENTITY = (
    "young adult woman, slim build, light brown skin, "
    "very long straight black hair with bangs, oval face"
)

GARMENTS = [
    "wearing a light purple upside-down string bikini top and matching bottoms",
    "wearing a light purple bikini top with a gathered center seam and thin halter ties",
    "wearing a purple bikini top and light purple bottoms",
    "wearing a lavender bikini top and a small gold necklace",
    "wearing a purple tunic that leaves her midriff and legs bare",
]
JEWELRY = [
    "a thin gold necklace with a small pendant",
    "a gold necklace with a pendant and gold hoop earrings",
    "gold hoop earrings and a gold pendant necklace",
    "a gold chain necklace",
    "gold teardrop earrings",
]
POSES = [
    "standing confidently facing the viewer",
    "reclining on a low stone ledge",
    "arms outstretched to her sides",
    "in a three-quarter side profile",
    "squatting low, one hand resting on her knee",
    "walking forward, hair trailing behind her",
    "hands resting on her hips",
    "turning back over her shoulder toward the viewer",
]
GAZES = [
    "looking directly at the viewer",
    "gazing off to the side",
    "eyes wide and watchful",
    "calm, even expression",
    "a faint, knowing half-smile",
    "lips slightly parted",
]
EYES = [
    "dark eyes",
    "brown eyes",
    "near-black eyes",
    "green eyes",      # disputed trait — sampled less
]
BACKGROUNDS = [
    "a lush dark jungle with heavy foliage",
    "a steaming swamp with still water",
    "the blue-lit mouth of an ice cave",
    "a dense forest clearing at dusk",
    "rocky terrain under a storm sky",
    "a firelit cave interior",
]
FRAMING = [
    "medium shot",
    "wide shot",
    "close-up",
    "full-body shot",
]


def compose(idx, rng):
    inner = f"{IDENTITY}, {rng.choice(GARMENTS)}, {rng.choice(JEWELRY)}, " \
            f"{rng.choice(EYES)}, {rng.choice(POSES)}, {rng.choice(GAZES)}. " \
            f"Background: {rng.choice(BACKGROUNDS)}. {rng.choice(FRAMING)}."
    return inner


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--count", type=int, default=300)
    ap.add_argument("--seed-base", type=int, default=82036621553915)
    ap.add_argument("--workflow", default=WF)
    ap.add_argument("--outdir", default=r"E:/FNI/renders/5090/teegra-many")
    args = ap.parse_args(argv)

    rng = random.Random(args.seed_base)
    g0 = k.load_workflow(args.workflow)   # verify loadable once
    del g0
    os.makedirs(args.outdir, exist_ok=True)

    # manifest of prompt <-> seed for reproducibility
    man = os.path.join(args.outdir, "prompts.jsonl")
    mf = open(man, "w", encoding="utf-8")

    for i in range(args.count):
        seed = args.seed_base + i
        prompt = compose(i, rng)
        g = k.load_workflow(args.workflow)
        k.set_prompt(g, main=prompt, pre=PRE_NO_JADA)
        k.set_lora(g, "lora_1", on=False, strength=0.0)   # jada OFF
        k.set_lora(g, "lora_7", on=True, strength=1.0)    # retro-fantasy ON
        k.set_seed(g, seed)
        tag = f"teegra_many_{i:04d}"
        k.set_prefix(g, tag)
        cid = f"fni-many-{i}-{int(time.time())}"
        try:
            pid = k.queue_graph(g, cid)
        except Exception as e:
            print(f"[{i}] queue fail: {e}", flush=True)
            mf.write(json.dumps({"i": i, "seed": seed, "prompt": prompt,
                                 "prompt_id": None, "error": str(e)}) + "\n")
            continue
        mf.write(json.dumps({"i": i, "seed": seed, "prompt": prompt,
                             "prompt_id": pid}) + "\n")
        mf.flush()
        try:
            files = k.wait_and_download(g, pid, args.outdir)
        except Exception as e:
            print(f"[{i}] download fail ({pid}): {e}", flush=True)
        else:
            if i % 25 == 0 or i == args.count - 1:
                print(f"[{i}/{args.count}] {tag} -> {len(files)} file(s)", flush=True)

    mf.close()
    print(f"MANY DONE: {args.count} queued; manifest {man}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))