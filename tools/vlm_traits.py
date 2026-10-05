#!/usr/bin/env python3
"""VLM trait pass for a character's reference stills.

Pass 1: literal per-image description (qwen3-vl-8b via LM Studio), no names,
        no inference — cached in refs/characters/<NAME>/vlm/<img>.json so
        reruns never re-query unchanged files.
Pass 2: synthesis — all per-image descriptions + the user's traits.txt go to
        the VLM together with the images for a consensus trait sheet, written
        to refs/characters/<NAME>/vlm/traits-vlm.md. traits.txt is NEVER
        overwritten; the synthesis flags agreements and conflicts for the
        user to adjudicate.

    python tools/vlm_traits.py --char TUTOR [--model <id>] [--max-side 1024]
"""
import argparse
import base64
import io
import json
import os
import sys
import time
import urllib.request

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "http://127.0.0.1:1234/v1/chat/completions"
DEFAULT_MODEL = "qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s"
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")

PER_IMAGE_PROMPT = (
    "You are looking at ONE frame from a 1983 rotoscoped fantasy animation. "
    "Describe the single most prominent human figure literally. Report only "
    "what is visible: apparent sex, age range, build, skin tone, hair (color, "
    "length, style), face shape and notable features, costume (each garment, "
    "color, cut, accessories), pose, and what they appear to be doing. "
    "Do NOT name the character, guess their identity, or infer personality. "
    "If the image contains multiple panels or figures, describe the most "
    "prominent one and note the others briefly. Plain prose, max 120 words."
)

SYNTH_PROMPT = (
    "These {n} images are reference stills for ONE character from a 1983 "
    "rotoscoped fantasy animation. Below are literal per-image descriptions "
    "and the user's own trait notes.\n\n"
    "Write a consensus trait sheet for this character: hair, skin, build, "
    "face, costume, distinguishing marks. For each trait state the consensus "
    "and note any images that disagree. Then a short section 'Conflicts with "
    "user notes' listing every place the images contradict the user's traits "
    "(or 'none' if they agree). Physical traits only, no names, no "
    "personality. Max 250 words.\n\n"
    "== USER TRAIT NOTES ==\n{traits}\n\n== PER-IMAGE DESCRIPTIONS ==\n{descs}"
)


def encode_image(path, max_side):
    im = Image.open(path)
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    if max(im.size) > max_side:
        r = max_side / max(im.size)
        im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def vlm(model, messages, max_tokens=600, timeout=300):
    body = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "stream": False,
    }).encode()
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        out = json.load(r)
    text = out["choices"][0]["message"]["content"].strip()
    return text, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--char", required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--max-side", type=int, default=1024)
    ap.add_argument("--synth-only", action="store_true")
    args = ap.parse_args()

    cdir = os.path.join(ROOT, "refs", "characters", args.char)
    if not os.path.isdir(cdir):
        sys.exit(f"no such character dir: {cdir}")
    vdir = os.path.join(cdir, "vlm")
    os.makedirs(vdir, exist_ok=True)

    imgs = sorted(fn for fn in os.listdir(cdir) if fn.lower().endswith(IMG_EXT))
    if not imgs:
        sys.exit("no images in " + cdir)

    descs = {}
    # ---- pass 1: per-image, cached by (mtime, size)
    for fn in imgs:
        cache = os.path.join(vdir, fn + ".json")
        st = os.stat(os.path.join(cdir, fn))
        if os.path.exists(cache) and not args.synth_only:
            with open(cache, encoding="utf-8") as f:
                c = json.load(f)
            if c.get("mtime") == st.st_mtime and c.get("size") == st.st_size and c.get("model") == args.model:
                descs[fn] = c["text"]
                print(f"[cache] {fn}")
                continue
        if args.synth_only:
            if os.path.exists(cache):
                with open(cache, encoding="utf-8") as f:
                    descs[fn] = json.load(f)["text"]
            continue
        b64 = encode_image(os.path.join(cdir, fn), args.max_side)
        msgs = [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                {"type": "text", "text": PER_IMAGE_PROMPT},
            ],
        }]
        text, dt = vlm(args.model, msgs)
        descs[fn] = text
        with open(cache, "w", encoding="utf-8") as f:
            json.dump({"file": fn, "model": args.model, "mtime": st.st_mtime,
                       "size": st.st_size, "text": text}, f, indent=1, ensure_ascii=False)
        print(f"[vlm {dt:.0f}s] {fn}\n  {text[:200]}")

    if args.synth_only and len(descs) < len(imgs):
        sys.exit("synth-only but not all images are cached; run the full pass first")

    # ---- ref tiers (optional refs/characters/<NAME>/ref_tiers.json):
    # canonical+pose images drive the consensus; inspiration-tier images are
    # style/ethos refs excluded from trait consensus (they would drag it).
    tiers_path = os.path.join(cdir, "ref_tiers.json")
    tiers = {}
    lineage = ""
    if os.path.exists(tiers_path):
        tj = json.load(open(tiers_path, encoding="utf-8"))
        tiers = {fn: v.get("tier", "canonical") for fn, v in tj.get("refs", {}).items()}
        lineage = tj.get("lineage", "")
    def tier_of(fn):
        return tiers.get(fn, "canonical")
    synth_imgs = [fn for fn in imgs if fn in descs and tier_of(fn) in ("canonical", "pose")]
    skipped = [fn for fn in imgs if fn in descs and tier_of(fn) == "inspiration"]

    # ---- pass 2: synthesis with canonical/pose images
    traits_path = os.path.join(cdir, "traits.txt")
    user_traits = open(traits_path, encoding="utf-8").read().strip() if os.path.exists(traits_path) else "(none)"
    desc_block = "\n\n".join(f"[{fn}] (tier: {tier_of(fn)})\n{descs[fn]}" for fn in synth_imgs)
    if skipped:
        desc_block += ("\n\n(EXCLUDED inspiration-tier refs, style/ethos only — do not derive "
                       "literal traits from them: " + ", ".join(skipped) + ")")
    if lineage:
        user_traits += f"\n\n(curator lineage note: {lineage})"
    prompt = SYNTH_PROMPT.format(n=len(synth_imgs), traits=user_traits, descs=desc_block)

    content = [{"type": "text", "text": prompt}]
    for fn in synth_imgs:
        b64 = encode_image(os.path.join(cdir, fn), args.max_side)
        content.insert(0, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    text, dt = vlm(args.model, [{"role": "user", "content": content}], max_tokens=900)

    out = os.path.join(vdir, "traits-vlm.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# VLM consensus traits — {args.char}\n"
                f"model: {args.model} · images: {len(imgs)} "
                f"(consensus from {len(synth_imgs)} canonical/pose"
                + (f", {len(skipped)} inspiration-tier excluded: {', '.join(skipped)}" if skipped else "")
                + f") · {time.strftime('%Y-%m-%d %H:%M')}\n\n"
                + (f"## Lineage note\n{lineage}\n\n" if lineage else "")
                + f"## User traits.txt\n{user_traits.split('(curator lineage note:')[0].strip()}\n\n## VLM synthesis\n{text}\n")
    print(f"\n[synth {dt:.0f}s] wrote {out}\n")
    print(text)


if __name__ == "__main__":
    main()
