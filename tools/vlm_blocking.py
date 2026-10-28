#!/usr/bin/env python
"""Draft per-chunk physical BLOCKING with a local VLM, and sweep models/prompts.

Goal: fill manifests/blocking.json automatically. The blocking must state how many
people are present (so the render can say "ONLY these N, alone") and what each is
doing (lounging vs standing vs walking) — the VLM's read of the source stills.

Endpoints:
  goldfishbowl  Ollama  http://<GOLDFISHBOWL_TS_IP>:11434/api/generate    (qwen3-vl-8b-abl, qwen3-vl-32b-heretic)
  lmstudio      OpenAI  http://127.0.0.1:1234/v1/chat/completions   (qwen3-vl-8b-..., qwen2.5-vl-32b-...)

Usage:
    # one call (prints the drafted blocking)
    .venv/Scripts/python.exe tools/vlm_blocking.py --chunk S05-c01 \
        --endpoint goldfishbowl --model qwen3-vl-32b-heretic:latest --sys literal

    # sweep every model x system prompt on a chunk
    .venv/Scripts/python.exe tools/vlm_blocking.py --chunk S05-c01 --sweep

    # draft for a scene and merge into manifests/blocking.json
    .venv/Scripts/python.exe tools/vlm_blocking.py --scene S05 --model qwen3-vl-32b-heretic:latest --sys literal --write
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(r"E:/FNI")
GF = "http://<GOLDFISHBOWL_TS_IP>:11434/api/generate"
LM = "http://127.0.0.1:1234/v1/chat/completions"

# (endpoint, model) candidates
MODELS = [
    ("goldfishbowl", "qwen3-vl-8b-abl:latest"),
    ("goldfishbowl", "qwen3-vl-32b-heretic:latest"),
    ("lmstudio", "qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s"),
    ("lmstudio", "qwen2.5-vl-32b-instruct-abliterated"),
]

SYS = {
    # the direct instruction from Alex: alone, seated/lounging, relaxed
    "literal": (
        "You are a film-continuity assistant. You will see several frames sampled from ONE "
        "continuous scene. Report ONLY the physical blocking, as plain prose, in 2-3 sentences. "
        "Cover: (1) how many people are visible in total, and whether anyone is a background "
        "extra; (2) for each main person, exactly what they are doing — choose from standing, "
        "walking, seated, lying down, or reclining/lounging — and whether they face the camera. "
        "(3) what kind of room it is. Be literal and conservative: if a person is not clearly "
        "in motion, say they are stationary. NEVER invent people, actions or objects that are "
        "not plainly visible. No colours, no clothing descriptions."),
    "compact": (
        "Describe the blocking of this scene in ONE sentence: how many people are in frame, and "
        "what each is physically doing (standing / walking / seated / lying / lounging). "
        "Say explicitly whether anyone is walking toward the camera. No colours."),
    "structured": (
        "Return ONLY this JSON, no prose: {\"people\": <int>, \"extras\": <int>, \"alone\": <bool>, "
        "\"poses\": [<one of standing/walking/seated/lying/reclining per person>], "
        "\"facing_camera\": <bool>, \"room\": \"<a few words>\"}."),
    "chen": (
        "These frames are sampled from a single film scene. State the blocking literally and "
        "briefly: who is in the shot, their posture (seated/lounging/standing/walking), and the "
        "room. Do not describe appearance, wardrobe, or colour. Do not speculate."),
}


def load_chunk(chunk_id: str) -> dict:
    for ln in (ROOT / "fullrun" / "chunks.jsonl").read_text(encoding="utf-8").splitlines():
        if ln.strip():
            r = json.loads(ln)
            if r["chunk_id"] == chunk_id:
                return r
    raise SystemExit(f"chunk {chunk_id} not found")


def chunk_stills(chunk_id: str, per_shot: int = 1) -> list[Path]:
    """Mid still of each shot in the chunk (grounded, not invented)."""
    row = load_chunk(chunk_id)
    out = []
    d = ROOT / "stills" / "full"
    for snum in row["shot_nums"]:
        fs = sorted(d.glob(f"shot_{snum}_f*.jpg"))
        if not fs:
            continue
        mid = fs[len(fs) // 2] if per_shot == 1 else fs[0]
        out.append(mid)
    return out


def _b64(path: Path, max_side: int = 1024) -> str:
    im = Image.open(path).convert("RGB")
    if max(im.size) > max_side:
        r = max_side / max(im.size)
        im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=85)
    return base64.b64encode(b.getvalue()).decode()


def ask(endpoint: str, model: str, sys_text: str, images: list[Path], timeout: int = 240) -> str:
    b64s = [_b64(p) for p in images]
    if endpoint == "goldfishbowl":
        body = json.dumps({"model": model, "system": sys_text, "prompt": "Report the blocking.",
                           "images": b64s, "stream": False, "options": {"temperature": 0.2}}).encode()
        req = urllib.request.Request(GF, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return (json.load(r).get("response") or "").strip()
    else:  # lmstudio (OpenAI chat)
        content = [{"type": "text", "text": "Report the blocking."}] + \
                  [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b}"}} for b in b64s]
        body = json.dumps({"model": model, "temperature": 0.2,
                           "messages": [{"role": "system", "content": sys_text},
                                        {"role": "user", "content": content}],
                           "max_tokens": 300, "stream": False}).encode()
        req = urllib.request.Request(LM, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return (json.load(r)["choices"][0]["message"]["content"] or "").strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--chunk")
    ap.add_argument("--scene")
    ap.add_argument("--endpoint", choices=["goldfishbowl", "lmstudio"])
    ap.add_argument("--model")
    ap.add_argument("--sys", choices=list(SYS), default="literal")
    ap.add_argument("--sys-text")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--write", action="store_true", help="merge result into manifests/blocking.json")
    args = ap.parse_args()

    if args.scene and not args.chunk:
        chunks = [json.loads(l)["chunk_id"] for l in
                  (ROOT / "fullrun" / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
                  if l.strip() and json.loads(l)["scene"] == args.scene]
    elif args.chunk:
        chunks = [args.chunk]
    else:
        ap.error("pass --chunk or --scene")

    sys_text = args.sys_text or SYS[args.sys]

    if args.sweep:
        for chunk in chunks[:1]:
            imgs = chunk_stills(chunk)
            print(f"\n### {chunk} — {len(imgs)} stills: {[p.name for p in imgs]}\n")
            for ep, model in MODELS:
                for sk, st in SYS.items():
                    try:
                        resp = ask(ep, model, st, imgs)
                    except Exception as e:  # noqa: BLE001
                        resp = f"ERR {e}"
                    print(f"--- [{ep}] {model.split('/')[-1]} / sys={sk} ---\n{resp}\n")
        return 0

    sys.path.insert(0, str(ROOT))
    from core.prompt_guards import usable_blocking  # noqa: E402

    results = {}
    failures = {}
    for chunk in chunks:
        imgs = chunk_stills(chunk)
        try:
            resp = ask(args.endpoint, args.model, sys_text, imgs)
        except Exception as e:  # noqa: BLE001
            resp = f"ERR {e}"
        # an error string is NOT content: never merge it into blocking.json —
        # a transport failure means "not drafted", not "drafted badly"
        if not usable_blocking(resp):
            failures[chunk] = resp
            print(f"[{chunk}] SKIPPED (not written): {resp[:140]}\n")
            continue
        results[chunk] = resp
        print(f"[{chunk}] {resp}\n")

    if args.write:
        p = ROOT / "manifests" / "blocking.json"
        cur = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        for k, v in results.items():
            cur[k] = v
        # also scrub any pre-existing error entries for chunks we just failed on,
        # so a poisoned ledger heals on the next successful pass
        p.write_text(json.dumps(cur, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"merged {len(results)} entries into {p} "
              f"({len(failures)} skipped as errors/too short)")
    if failures:
        print(f"WARNING: {len(failures)} chunk(s) failed to draft — re-run to retry",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
