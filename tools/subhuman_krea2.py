# -*- coding: utf-8 -*-
"""Subhuman Krea2 stills: VLM description -> Krea2 render, automated.

Reproduces Alex's Open WebUI loop, end to end:
  1. Feed the subhuman's source movie stills + its H3 cartoon character sheet
     to goldfishbowl qwen3-vl-32b-heretic (large context), with the T2I
     prompt-engineer system prompt + the "describe this bronze age subhuman
     leader..." starter prompt.
  2. The returned verbose pure description becomes the Krea2 main prompt
     (node 135), rendered on the 5090 from the EXACT graph that produced his
     good stills (extracted from the PNG sidecar — graphs are artifacts).

Recipe (read from the good renders' PNG metadata):
  leader:  unet krea170277, style 80sFantasy_Krea2Raw @1.0, ID person_07 @1.0
  captain: unet finepornV2TURBOKrea2, style 30sTechnicolor @1.0 + retro-fantasy
           @1.15, ID person_11 @1.0

    .venv/Scripts/python.exe tools/subhuman_krea2.py --char leader --describe-only --count 1
    .venv/Scripts/python.exe tools/subhuman_krea2.py --char leader --count 10
    .venv/Scripts/python.exe tools/subhuman_krea2.py --char leader --render-only
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(r"E:/FNI")
RUN = ROOT / "runs" / "subhuman-krea2"
COMFY = os.environ.get("FNI_COMFY", "http://<TOMBSTONE_TS_IP>:8188").rstrip("/")
sys.path.insert(0, str(ROOT))
from core import gf_client as gf  # noqa: E402  — endpoint + token live there

VLM_MODEL = "qwen3-32b-vision-large"   # goldfishbowl alias (gf_client.ALIASES)

# System prompt Alex uses in Open WebUI (verbatim).
SYSTEM_PROMPT = (
    "You are an expert prompt engineer for text-to-image models. Your task is to expand the "
    "user's prompt into a highly effective image-generation prompt.\n\n"
    "Think step by step about the request before writing the answer:\n"
    "- What is the subject and mood?\n"
    "- What visual styles, mediums, and lighting options would fit? Consider two or three "
    "alternatives and pick the one that best serves the caption.\n"
    "- What composition, framing, and grounded details will help the text-to-image model?\n\n"
    "Then output a single expanded prompt paragraph.\n\n"
    "Follow these rules strictly:\n"
    "1. **Faithfulness First:** Preserve all original subjects, actions, colors, and spatial "
    "relationships. Do not add new objects, props, characters, or animals unless the user "
    "clearly implies them.\n"
    "2. **Practical T2I Structure:** Write a prompt that a text-to-image model can parse "
    "cleanly. Group subjects with their own attributes and actions. Use grounded phrasing for "
    "poses, interactions, and spatial layout.\n"
    "3. **Style Planning Stays Internal:** Use your internal reasoning to choose style, medium, "
    "framing, and lighting. Do not emit planning tags or wrappers in the visible answer body.\n"
    "4. **Text Rendering:** If the user requests visible text, quotes, labels, or typography, "
    "specify the exact text clearly and wrap requested words in quotes.\n"
    "5. **Avoid Over-Specification:** Do not invent highly specific clothing, colors, materials, "
    "or scene details unless the input supports them.\n"
    "6. **Structure:** Write one cohesive paragraph after the thinking block. No bullets, JSON, "
    "or markdown.\n"
    "7. **Respect Existing Detail:** If the user's prompt is already detailed, lightly polish and "
    "finalize rather than heavily expanding — preserve their phrasing and direction.\n"
    "8. **Respect the Human Form:** Treat depictions of people with dignity. Assume clothing "
    "covers genitals and intimate anatomy.\n"
    "9. **Preserve User Medium:** When the user explicitly requests a medium (e.g. \"photo of\", "
    "\"photograph of\", \"illustration of\", \"painting of\", \"sketch of\", \"3D render of\"), "
    "honor it. Do not pivot to a different medium to avoid difficulty — match the user's stated "
    "intent."
)

# Per-character: source stills, H3 sheet, starter prompt, render template.
CHARS = {
    "leader": {
        "label": "subhuman leader",
        "stills": [
            "refs/characters/SUBHUMAN LEADER/shot_00415_f00000.jpg",
            "refs/characters/SUBHUMAN LEADER/shot_00415_f00016.jpg",
            "refs/characters/SUBHUMAN LEADER/shot_00415_f00032.jpg",
        ],
        "sheet": "refs/characters/SUBHUMAN LEADER/SUBHUMAN LEADER_sheet_t01_00001_.png",
        "starter": (
            "describe this bronze age subhuman leader from 1983's fire and ice movie. this will "
            "be used for a krea2 prompt for a technicolor retro 80's/90's fantasy, ben hur meets "
            "Beastmaster, cleopatra meets xena warrior princess. pay attention to the system "
            "prompt. be verbose and descriptive. do not refer to the films and tv shows "
            "referenced. make this a pure description."
        ),
        "template": RUN / "templates" / "leader_template.graph.json",
        "prefix": "subhuman_leader",
    },
    "captain": {
        "label": "subhuman captain",
        "stills": [
            "refs/characters/SUBHUMAN CAPTAIN/shot_00414_f00000.jpg",
            "refs/characters/SUBHUMAN CAPTAIN/shot_00414_f00133.jpg",
            "refs/characters/SUBHUMAN CAPTAIN/shot_00414_f00265.jpg",
        ],
        "sheet": "refs/characters/SUBHUMAN CAPTAIN/SUBHUMAN CAPTAIN_sheet_t01_00001_.png",
        "starter": (
            "describe this bronze age subhuman captain from 1983's fire and ice movie. this will "
            "be used for a krea2 prompt for a technicolor retro 80's/90's fantasy, ben hur meets "
            "Beastmaster, cleopatra meets xena warrior princess. pay attention to the system "
            "prompt. be verbose and descriptive. do not refer to the films and tv shows "
            "referenced. make this a pure description."
        ),
        "template": RUN / "templates" / "captain_template.graph.json",
        "prefix": "subhuman_captain",
    },
}

# Node ids (from krea2_stills.py / the extracted graphs)
POS_MAIN = "135"
POS_PRE = "137"
SAMPLER = "102"
SAVE = "128"
SEED_BASE = 700000000000000


def _b64(path: Path, max_side: int = 1280) -> str:
    im = Image.open(path).convert("RGB")
    if max(im.size) > max_side:
        r = max_side / max(im.size)
        im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=88)
    return base64.b64encode(b.getvalue()).decode()


def describe(cfg: dict, temperature: float) -> str:
    images = [str(ROOT / p) for p in cfg["stills"]] + [str(ROOT / cfg["sheet"])]
    t0 = time.time()
    out = gf.chat(VLM_MODEL, cfg["starter"], system=SYSTEM_PROMPT, images=images,
                  temperature=temperature, max_tokens=8000, timeout=600)
    print("    VLM describe: %d chars in %.1fs" % (len(out), time.time() - t0), flush=True)
    return out.strip()


def _post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def _get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())


def render_one(cfg: dict, desc: str, seed: int, outdir: Path) -> str | None:
    g = json.loads((cfg["template"]).read_text(encoding="utf-8"))
    g[POS_MAIN]["inputs"]["positive"] = desc
    g[SAMPLER]["inputs"]["seed"] = seed
    prefix = "%s_s%012d" % (cfg["prefix"], seed)
    g[SAVE]["inputs"]["filename_prefix"] = prefix
    out = _post(f"{COMFY}/prompt", {"prompt": g, "client_id": "fni-subhuman-%d" % int(time.time())})
    if out.get("node_errors"):
        raise RuntimeError(f"node_errors: {json.dumps(out['node_errors'])}")
    pid = out["prompt_id"]

    outdir.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + 600
    while time.time() < deadline:
        h = _get(f"{COMFY}/history/{pid}")
        rec = h.get(pid)
        if rec and rec.get("outputs"):
            for node_id, o in rec["outputs"].items():
                for img in o.get("images", []):
                    if "ComfyUI_temp" in img["filename"]:
                        continue
                    url = (f"{COMFY}/view?filename={urllib.parse.quote(img['filename'])}"
                           f"&subfolder={urllib.parse.quote(img.get('subfolder',''))}"
                           f"&type={urllib.parse.quote(img.get('type','output'))}")
                    dest = outdir / img["filename"]
                    with urllib.request.urlopen(url, timeout=60) as r:
                        dest.write_bytes(r.read())
                    return str(dest)
        if rec and rec.get("status", {}).get("status_str") == "error":
            raise RuntimeError(f"render error: {rec['status']}")
        time.sleep(4)
    raise TimeoutError(f"{pid} did not finish in 600s")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--char", choices=list(CHARS), default="leader")
    ap.add_argument("--count", type=int, default=10)
    ap.add_argument("--describe-only", action="store_true")
    ap.add_argument("--render-only", action="store_true")
    ap.add_argument("--temperature", type=float, default=0.85)
    args = ap.parse_args()

    cfg = CHARS[args.char]
    desc_file = RUN / f"{args.char}_descriptions.jsonl"
    outdir = RUN / "output" / args.char
    RUN.mkdir(parents=True, exist_ok=True)
    outdir.mkdir(parents=True, exist_ok=True)

    if not args.render_only:
        # vary temperature a little per call so descriptions (and thus stills) differ
        temps = [max(0.4, args.temperature + (i % 5 - 2) * 0.12) for i in range(args.count)]
        with desc_file.open("w", encoding="utf-8") as fh:
            for i, t in enumerate(temps):
                print("[%d/%d] describing (temp %.2f)..." % (i + 1, args.count, t), flush=True)
                try:
                    d = describe(cfg, t)
                except Exception as e:  # noqa: BLE001
                    d = "ERROR: %s" % e
                    print("    FAILED:", e, flush=True)
                fh.write(json.dumps({"i": i, "temperature": t, "description": d}) + "\n")
                fh.flush()
        print("descriptions ->", desc_file)

    if args.describe_only:
        return

    rows = [json.loads(l) for l in desc_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    manifest = RUN / f"{args.char}_manifest.jsonl"
    with manifest.open("a", encoding="utf-8") as mf:
        for i, row in enumerate(rows):
            desc = row["description"]
            if desc.startswith("ERROR"):
                print("[%d] skipping errored description" % i, flush=True)
                continue
            seed = SEED_BASE + i
            print("[%d] rendering seed=%d ..." % (i, seed), flush=True)
            try:
                dest = render_one(cfg, desc, seed, outdir)
            except Exception as e:  # noqa: BLE001
                dest = None
                print("    render FAILED:", e, flush=True)
            mf.write(json.dumps({"i": i, "seed": seed, "file": dest,
                                 "temperature": row.get("temperature"),
                                 "description": desc}) + "\n")
            mf.flush()
    print("done. manifest:", manifest)


if __name__ == "__main__":
    main()
