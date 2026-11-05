# -*- coding: utf-8 -*-
"""Review Qwen-Edit SCENE stills (character composed into a setting) with the
32B VLM. Same strict gross-anatomy rubric as review_sweep.py, plus scene-specific
checks: the character must be present and intact, the background coherent, the
framing full, and no polished-metal anachronism or mangled weapon grip.

Reads runs/subhuman-krea2/scenes/stills/*.png, writes
runs/subhuman-krea2/scenes/scene_review.jsonl (resumable).

    .venv/Scripts/python.exe tools/review_scenes.py
"""
from __future__ import annotations

import base64
import io
import json
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(r"E:/FNI")
RUN = ROOT / "runs" / "subhuman-krea2"
STILLS = RUN / "scenes" / "stills"
REVIEW = RUN / "scenes" / "scene_review.jsonl"
GF = "http://<GOLDFISHBOWL_TS_IP>:11434/api/generate"
VLM = "qwen3-vl-32b-heretic:latest"

PROMPT = (
    "This is a generated scene still of a sword-and-sandals fantasy character placed into a "
    "setting (standing stones, ritual fire, megaliths, cliffs) at the dawn of the bronze age. "
    "Judge STRICTLY — most AI stills have at least one real flaw, so only mark GOOD if it is "
    "genuinely clean. Look for: (1) the subject character present and intact — exactly one "
    "character, face not fused/blended/melted; (2) GROSS anatomy errors only (a clearly "
    "mangled face, extra limbs, a limb missing or fused into the torso, a hand that is a "
    "visible blob or has six-plus clearly-separated fingers) — do NOT penalize small far-away "
    "hands you cannot resolve, they are below the resolution of a full-body shot; (3) "
    "anachronistic polished metal armour instead of fur/hide/bone/stone/wood/crude copper, or "
    "a weapon whose grip is fused into the hand; (4) background incoherence — mush, melting "
    "geometry, broken perspective, a horizon that does not line up; (5) framing faults "
    "(subject cropped at neck/chin, feet cut off); (6) text, watermark, or signature. If a "
    "real flaw is present, verdict is BAD; if unsure about a tiny detail, prefer GOOD.\n"
    "Answer EXACTLY in this format, nothing else:\n"
    "VERDICT=GOOD or BAD\nWHY=<one short clause naming the specific flaw, or 'clean'>"
)


def b64(path, max_side=1024):
    im = Image.open(path).convert("RGB")
    if max(im.size) > max_side:
        r = max_side / max(im.size)
        im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=85)
    return base64.b64encode(b.getvalue()).decode()


def judge(path):
    body = json.dumps({"model": VLM, "prompt": PROMPT, "images": [b64(path)],
                       "stream": False, "options": {"temperature": 0.0, "num_ctx": 8192}}).encode()
    req = urllib.request.Request(GF, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return (json.load(r).get("response") or "").strip()


def main():
    pngs = sorted(STILLS.glob("*.png"))
    if not pngs:
        print("no scene stills in", STILLS)
        return
    done = set()
    if REVIEW.exists():
        done = {json.loads(l)["file"] for l in REVIEW.read_text(encoding="utf-8").splitlines() if l.strip()}
    with REVIEW.open("a", encoding="utf-8") as fh:
        for p in pngs:
            if str(p) in done:
                continue
            try:
                resp = judge(p)
            except Exception as e:  # noqa: BLE001
                # a transport error is NOT a verdict — skip so a later run retries
                print("SKIP %s (judge unreachable, not written): %s" % (p.name, e), flush=True)
                continue
            verdict = "GOOD" if resp.startswith("VERDICT=GOOD") else "BAD"
            fh.write(json.dumps({"file": str(p), "verdict": verdict, "resp": resp}) + "\n")
            fh.flush()
            print("%-6s %-44s %s" % (verdict, p.name, resp.replace("\n", " | ")[:90]), flush=True)
    rows = [json.loads(l) for l in REVIEW.read_text(encoding="utf-8").splitlines() if l.strip()]
    good = [r for r in rows if r["verdict"] == "GOOD"]
    print("== %d/%d GOOD scene stills" % (len(good), len(rows)))


if __name__ == "__main__":
    main()
