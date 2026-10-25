# -*- coding: utf-8 -*-
"""Batch VLM descriptions for all sweepable FNI characters.

For each character: feed its id still + H3 cartoon sheet (or src stills when
there is no sheet) to goldfishbowl qwen3-vl-32b-heretic with the T2I
prompt-engineer system prompt + a per-character starter prompt, cache the
verbose pure description to runs/subhuman-krea2/descs/<CHAR>.txt.

    .venv/Scripts/python.exe tools/describe_all.py [--char NAME] [--dry-run]
"""
from __future__ import annotations

import base64
import importlib.util
import io
import json
import sys
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(r"E:/FNI")
RUN = ROOT / "runs" / "subhuman-krea2"
GF = "http://<GOLDFISHBOWL_TS_IP>:11434/api/generate"
VLM_MODEL = "qwen3-vl-32b-heretic:latest"
NUM_CTX = 32768

# (name, starter-subject-noun, [image rel-paths], optional trait hint)
CHARACTERS = [
    ("DARKWOLF", "an older heavily-muscled warrior with long black hair",
     ["refs/characters/DARKWOLF/id_DARKWOLF.jpg",
      "refs/characters/DARKWOLF/DARKWOLF_sheet_t01_00001_.png"], ""),
    ("ENVOYS", "a hooded subhuman envoy with yellow eyes and dark skin",
     ["refs/characters/ENVOYS/id_ENVOYS.jpg",
      "refs/characters/ENVOYS/ENVOYS_sheet_t01_00001_.png"], ""),
    ("JAROL", "an older king with gray-white hair and a full beard",
     ["refs/characters/JAROL/id_JAROL.jpg",
      "refs/characters/JAROL/JAROL_sheet_t01_00001_.png"], ""),
    ("JULIANA", "an older queen with long black hair and crimson lips",
     ["refs/characters/JULIANA/id_JULIANA.jpeg",
      "refs/characters/JULIANA/JULIANA_sheet_t01_00001_.png"], ""),
    ("LARN", "a young athletic man with shoulder-length blond hair",
     ["refs/characters/LARN/id_LARN.jpg"], ""),  # no sheet; id still only
    ("NEKRON", "a tall gaunt pale young man with long white hair and dark robes",
     ["refs/characters/NEKRON/id_NEKRON.jpg",
      "refs/characters/NEKRON/NEKRON_sheet6_00001_.png"],
     "long white hair, pale gray skin, dark purple robe"),
    ("OTWA", "a young man of gentle face and immense build",
     ["refs/characters/OTWA/id_OTWA.jpg",
      "refs/characters/OTWA/OTWA_sheet_t01_00001_.png"], ""),
    ("ROLIEL", "a woman with long red hair and fair skin",
     ["refs/characters/ROLIEL/id_ROLIEL.jpg",
      "refs/characters/ROLIEL/ROLIEL_sheet_t01_00001_.png"], ""),
    ("SHAITAN", "a small dark animal-like creature with bright eyes",
     ["refs/characters/SHAITAN/id_SHAITAN.jpg",
      "refs/characters/SHAITAN/SHAITAN_sheet_t01_00001_.png"], ""),
    ("SPIRIT", "a translucent pale humanoid figure with a faint glow",
     ["refs/characters/SPIRIT/id_SPIRIT.jpg",
      "refs/characters/SPIRIT/SPIRIT_sheet_t01_00001_.png"], ""),
    ("SUBHUMAN", "a hunched fur-covered ape-like humanoid",
     ["refs/characters/SUBHUMAN/id_SUBHUMAN.png",
      "refs/characters/SUBHUMAN/SUBHUMAN_sheet_t01_00001_.png"], ""),
    ("TEEGRA", "a young woman with pale skin and very long dark hair",
     ["refs/characters/TEEGRA/id_TEEGRA.jpg",
      "refs/characters/TEEGRA/TEEGRA_sheet_t01_00001_.png"],
     "green eyes, pale skin, long black hair, purple two-piece, gold necklace"),
    ("TARO", "a young prince with dark hair in Fire Keep dress with a high collar",
     ["refs/characters/TARO/id_TARO.webp",
      "refs/characters/TARO/TARO_sheet_t01_00001_.png"], ""),
    ("TUTOR", "an older man in plain Fire Keep robes",
     ["refs/characters/TUTOR/id_TUTOR.jpg",
      "refs/characters/TUTOR/TUTOR_sheet_t01_00001_.png"], ""),
]


def _sys_prompt():
    spec = importlib.util.spec_from_file_location("sk", ROOT / "tools" / "subhuman_krea2.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.SYSTEM_PROMPT


def b64(path, max_side=1280):
    im = Image.open(path).convert("RGB")
    if max(im.size) > max_side:
        r = max_side / max(im.size)
        im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=88)
    return base64.b64encode(b.getvalue()).decode()


def describe(subject, images, trait_hint, temperature=0.8):
    hint = (" Known canon: %s." % trait_hint) if trait_hint else ""
    starter = (
        "describe %s from 1983's fire and ice movie. this will be used for a krea2 prompt "
        "for a sword-and-sandals fantasy epic set at the dawn of the bronze age and the end "
        "of the neolithic: fur and hide garments, bone stone and wood weapons, the first "
        "crude copper, megalithic standing stones, ritual fire, shamanic magic and spirit "
        "totems — primal and mythic, not polished classical armour, not refined bronze-age "
        "metallurgy. rendered in a technicolor 80's/90's retro fantasy film style. pay "
        "attention to the system prompt. be verbose and descriptive. do not refer to the "
        "films and tv shows referenced. make this a pure description.%s" % (subject, hint))
    body = json.dumps({
        "model": VLM_MODEL, "system": _sys_prompt(), "prompt": starter,
        "images": [b64(ROOT / p) for p in images], "stream": False,
        "options": {"temperature": temperature, "num_ctx": NUM_CTX},
    }).encode()
    req = urllib.request.Request(GF, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return (json.load(r).get("response") or "").strip()


def main():
    only = sys.argv[2] if len(sys.argv) > 2 else None
    outdir = RUN / "descs"
    outdir.mkdir(parents=True, exist_ok=True)
    for name, subject, images, hint in CHARACTERS:
        if only and name != only:
            continue
        dest = outdir / ("%s.txt" % name)
        if dest.exists() and dest.stat().st_size > 100:
            print("%s: cached (%d chars)" % (name, dest.stat().st_size), flush=True)
            continue
        print("%s: describing (%d images)..." % (name, len(images)), flush=True)
        try:
            d = describe(subject, images, hint)
        except Exception as e:  # noqa: BLE001
            d = "ERROR: %s" % e
            print("  FAILED:", e, flush=True)
        dest.write_text(d, encoding="utf-8")
        print("  -> %d chars" % len(d), flush=True)


if __name__ == "__main__":
    main()
