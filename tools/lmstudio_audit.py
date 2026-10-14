#!/usr/bin/env python
"""Empirical audit of the local LM Studio quiver.

Grades every model on the jobs it would actually be asked to do, with
deterministic checks in code (no LLM judge) plus raw outputs kept for human
review. One model loaded at a time, identical settings for every model.

Usage:
  python lmstudio_audit.py list
  python lmstudio_audit.py run [--models a,b,c] [--ctx 32768] [--out DIR] [--longctx]
  python lmstudio_audit.py report [--out DIR]
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HOST = os.environ.get("LMS_HOST", "http://127.0.0.1:1234")
OUT_DEFAULT = Path(r"E:\FNI\audit")
BASELINE_IMG = Path(
    r"C:\Users\gsfny\AppData\Local\hermes\images"
    r"\dashboard_20261013_072743_a12cc767_ComfyUI_00063.png"
)
BASELINE_W = 1536  # downscale width for vision tests

CAM_MOVES = [
    "pan", "truck", "tilt", "push-in", "push in", "pull-out", "pull out",
    "arc", "tracking", "static", "shake", "pov", "roll",
]


# ---------------------------------------------------------------- plumbing
def http_json(path: str, payload: dict | None = None, timeout: int = 900) -> dict:
    url = HOST + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def models() -> list[dict]:
    return http_json("/api/v0/models")["data"]


def unload_all() -> None:
    subprocess.run(["lms", "unload", "--all"], capture_output=True, text=True)


LOAD_LADDER = [
    ("default", []),
    ("gpu-max", ["--gpu", "max"]),
]


def _one_load(key: str, flags: list[str]) -> tuple[bool, float, str]:
    cmd = ["lms", "load", key, *flags, "-y"]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    except subprocess.TimeoutExpired:
        return False, time.time() - t0, "timeout waiting for load"
    dt = time.time() - t0
    log = (p.stdout + p.stderr).replace("\r", "")
    bad = ("Error:" in log or "error" in log.lower()
           or "exited before becoming healthy" in log)
    if bad:
        m = re.search(r"(Error:[^\n]*|.*exited before becoming healthy[^\n]*)", log)
        crashtail = m.group(0)[-400:] if m else log[-400:]
        return False, dt, crashtail
    # a load that returns 0 but never got healthy still reports the model absent
    try:
        loaded = {x["identifier"] for x in
                  json.loads(_lms_ps())}
    except Exception:
        loaded = set()
    if key not in loaded and not any(key in l for l in loaded):
        return False, dt, "not present in `lms ps` after load (silent failure)"
    return True, dt, "ok"


def _lms_ps() -> str:
    p = subprocess.run(["lms", "ps", "--json"], capture_output=True, text=True)
    return p.stdout


def load(key: str, ctx: int | None) -> tuple[bool, float, str, str]:
    """Try a ladder of load settings; report which one worked.

    Returns (ok, seconds, flags_used, log_of_last_attempt).
    """
    # Uniform settings first (same ctx for every model = one variable isolated),
    # then fall back to whatever LM Studio decides.
    attempts = []
    if ctx:
        attempts.append((f"gpu-max-ctx{ctx}", ["--gpu", "max", "-c", str(ctx)]))
    attempts += [(name, list(flags)) for name, flags in LOAD_LADDER]
    last = ""
    for name, fl in attempts:
        ok, dt, log = _one_load(key, fl)
        if ok:
            return True, dt, name, log
        last = log
        unload_all()
    return False, 0.0, "none", last


def chat(model: str, messages: list, *, tools=None, max_tokens=400,
         temperature=0.0, timeout=900) -> dict:
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    t0 = time.time()
    try:
        r = http_json("/v1/chat/completions", payload, timeout=timeout)
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:500]
        return {"error": f"HTTP {e.code}: {body}", "elapsed": time.time() - t0}
    except Exception as e:  # timeouts, resets, server death
        return {"error": f"{type(e).__name__}: {e}", "elapsed": time.time() - t0}
    r["elapsed"] = time.time() - t0
    return r


def text_of(resp: dict) -> str:
    try:
        return resp["choices"][0]["message"].get("content") or ""
    except Exception:
        return ""


def usage_of(resp: dict) -> dict:
    return resp.get("usage") or {}


def parse_json_loose(s: str):
    """Pull the first JSON object/array out of a model reply."""
    s = re.sub(r"^```(?:json)?|```$", "", s.strip(), flags=re.M).strip()
    for pat in (r"\{.*\}", r"\[.*\]"):
        m = re.search(pat, s, re.S)
        if not m:
            continue
        try:
            return json.loads(m.group(0))
        except Exception:
            continue
    return None


# ---------------------------------------------------------------- text tests
ECHO_ITEMS = [
    r"E:\FNI\refs\setups\S06-A_plate.jpg",
    "qwen3.8-flash-next@q8_0",
    "delegation.fallback_providers[0].model",
    "shot_01243_f00059.jpg",
    "S05-c04_ref.mp4",
    "text-embedding-nomic-embed-text-v1.5",
    "100.104.7.72:8188",
    "graph_length_frames",
    "integrated_multimodal_description",
    "retention_analysis",
    "0.00-second",
    "<d>[English] By the frozen sea.</d>",
]


def t_echo(model: str) -> dict:
    listing = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(ECHO_ITEMS))
    msg = (
        "Below is a numbered list of exact strings. Reproduce every string "
        "byte-for-byte, in the same order, with no additions, no corrections and "
        "no reformatting. Reply with ONLY a JSON object of the form "
        '{"echo": ["string1", "string2", ...]} and nothing else.\n\n' + listing
    )
    r = chat(model, [{"role": "user", "content": msg}], max_tokens=900)
    out = text_of(r)
    obj = parse_json_loose(out)
    got = obj.get("echo") if isinstance(obj, dict) else None
    matched = 0
    if isinstance(got, list):
        for i, want in enumerate(ECHO_ITEMS):
            if i < len(got) and isinstance(got[i], str) and got[i].strip() == want:
                matched += 1
    return {
        "name": "echo_identifiers",
        "score": matched / len(ECHO_ITEMS),
        "detail": f"{matched}/{len(ECHO_ITEMS)} exact",
        "raw": out[:4000],
        "error": r.get("error"),
        "elapsed": r.get("elapsed"),
    }


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "pull_render_outputs",
            "description": "Copy finished render outputs from the 5090 render box.",
            "parameters": {
                "type": "object",
                "properties": {
                    "run": {"type": "string", "description": "Run/chunk tag, e.g. S06"},
                    "shot": {"type": "integer", "description": "Shot number"},
                    "kind": {
                        "type": "string",
                        "enum": ["video", "audio", "plate"],
                    },
                },
                "required": ["run", "shot", "kind"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "queue_render",
            "description": "Queue a render job on the 5090 ComfyUI server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chunk": {"type": "string"},
                    "mode": {"type": "string", "enum": ["fl2va", "ref2va"]},
                },
                "required": ["chunk", "mode"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_render_box_models",
            "description": "List checkpoints/loras installed on the render box.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def t_tools(model: str) -> dict:
    msg = (
        "The render for chunk S06 shot 4 is finished and its video file is on the "
        "render box. Make the single tool call that fetches that finished video "
        "file back to this machine."
    )
    r = chat(model, [{"role": "user", "content": msg}], tools=TOOLS, max_tokens=400)
    calls = []
    try:
        calls = r["choices"][0]["message"].get("tool_calls") or []
    except Exception:
        pass
    ok, detail = 0.0, "no tool_calls in reply"
    if calls:
        try:
            fn = calls[0]["function"]["name"]
            args = json.loads(calls[0]["function"]["arguments"])
            want = {"run": "S06", "shot": 4, "kind": "video"}
            good_args = all(str(args.get(k)) == str(v) for k, v in want.items())
            ok = 1.0 if (fn == "pull_render_outputs" and good_args) else 0.5
            detail = f"{fn}({args})"
        except Exception as e:
            detail = f"unparseable call: {e}"
    return {
        "name": "tool_call",
        "score": ok,
        "detail": detail,
        "raw": text_of(r)[:2000] or json.dumps(calls)[:2000],
        "error": r.get("error"),
        "elapsed": r.get("elapsed"),
    }


def t_json_shape(model: str) -> dict:
    keys = ["shot_id", "setup_id", "camera", "action", "soundscape", "music"]
    msg = (
        "Return a JSON array of exactly 6 objects, one per shot of scene S06. "
        f"Every object must have exactly these keys, in this order: {keys}. "
        "camera is one camera move, action is one physical action, soundscape and "
        "music are short English sentences. Reply with the JSON array only."
    )
    r = chat(model, [{"role": "user", "content": msg}], max_tokens=1200)
    out = text_of(r)
    obj = parse_json_loose(out)
    score, detail = 0.0, "unparseable JSON"
    if isinstance(obj, list):
        score, detail = 0.3, f"array of {len(obj)}"
        if len(obj) == 6:
            score += 0.3
        keysets = [list(o.keys()) for o in obj if isinstance(o, dict)]
        if keysets and all(set(k) == set(keys) for k in keysets):
            score += 0.3
        if keysets and all(k == keys for k in keysets):
            score += 0.1
        detail += f", keys {'ok' if keysets and all(set(k) == set(keys) for k in keysets) else 'wrong'}"
    return {
        "name": "json_shape",
        "score": round(min(score, 1.0), 2),
        "detail": detail,
        "raw": out[:4000],
        "error": r.get("error"),
        "elapsed": r.get("elapsed"),
    }


H3_STUB = """Scene S06, setup S06-A. Interior — ice cavern, low camera, warm torch pool
on the right wall, cold blue falloff behind. Characters present: DARKWOLF (big, bare
chested, black mane, axe in right hand, war paint), TEEGRA (tall, dark hair, light blue
wrap, barefoot). Duration 5.00 seconds. Task: FL2VA, first frame = plate, last frame =
two-shot at the cavern mouth. Audio: wind, distant cracking ice, low drone under."""


def t_h3(model: str) -> dict:
    msg = (
        "Write the MiniMax-H3 prompt for this shot.\n\n" + H3_STUB +
        "\n\nReply with exactly three fields, in this order and with these exact "
        "names, one per line, each on a single line:\n"
        "integrated_multimodal_description:\noverall_soundscape:\n"
        "non_diegetic_music:"
    )
    r = chat(model, [{"role": "user", "content": msg}], max_tokens=1400)
    out = text_of(r)
    checks = {}
    idx = [out.find(f) for f in (
        "integrated_multimodal_description",
        "overall_soundscape",
        "non_diegetic_music",
    )]
    checks["all_three_fields"] = all(i >= 0 for i in idx)
    checks["field_order"] = all(i >= 0 for i in idx) and idx == sorted(idx)
    checks["no_dead_video_ref"] = "<video" not in out.lower()
    checks["no_shot1_timestamp"] = not re.search(
        r"\[shot 1\]\s*(at|@)\s*\d", out, re.I)
    cams = {c for c in CAM_MOVES if re.search(rf"\b{re.escape(c)}\b", out, re.I)}
    checks["single_camera_move"] = len(cams) == 1
    checks["substantive"] = len(out) > 400
    score = sum(checks.values()) / len(checks)
    return {
        "name": "h3_3field",
        "score": round(score, 2),
        "detail": ", ".join(f"{k}={'Y' if v else 'N'}" for k, v in checks.items())
        + f" [cams={sorted(cams)}]",
        "raw": out[:6000],
        "error": r.get("error"),
        "elapsed": r.get("elapsed"),
    }


# ---------------------------------------------------------------- vision tests
def b64_image(path: Path, width: int = BASELINE_W) -> tuple[str, str]:
    from PIL import Image

    im = Image.open(path).convert("RGB")
    if im.width > width:
        im = im.resize((width, int(im.height * width / im.width)))
    tmp = Path(os.environ.get("TMPDIR", ".")) / "audit_baseline.jpg"
    im.save(tmp, quality=92)
    return base64.b64encode(tmp.read_bytes()).decode(), str(tmp)


CAPTION_PROMPT = (
    "Look at this image and describe it for a production database. Then, on the "
    "final line, output ONE line of JSON with exactly these keys: "
    '{"shot_type": str, "subjects": int, "characters": [str], "weapon_visible": bool, '
    '"weapon": str, "colors": {"skin": str, "hair": str, "top": str, "bottom": str, '
    '"background": str}, "camera": str, "style": str}. '
    "Use plain color names. Describe what is actually visible; do not guess at names "
    "you cannot read."
)

COLOR_PROMPT = (
    "List the dominant color of each of these regions, as plain color words, one per "
    "line in the form 'region: color': hair, skin, top garment, bottom garment, "
    "background, any metal or accessory. Do not hedge."
)


def _vision_call(model: str, b64: str, prompt: str, temperature: float = 0.0,
                 max_tokens: int = 900) -> dict:
    msgs = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url",
             "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
        ],
    }]
    return chat(model, msgs, temperature=temperature, max_tokens=max_tokens)


def t_caption(model: str, b64: str) -> dict:
    r = _vision_call(model, b64, CAPTION_PROMPT)
    out = text_of(r)
    obj = parse_json_loose(out)
    checks = {
        "json_line": isinstance(obj, dict),
        "has_colors": isinstance(obj, dict)
        and all(isinstance(v, str) and v.strip()
                for v in (obj.get("colors") or {}).values()),
        "has_subjects": isinstance(obj, dict) and bool(obj.get("characters")),
        "prose": len(out) > 200,
    }
    return {
        "name": "vision_caption",
        "score": round(sum(checks.values()) / len(checks), 2),
        "detail": ", ".join(f"{k}={'Y' if v else 'N'}" for k, v in checks.items()),
        "raw": out[:6000],
        "parsed": obj if isinstance(obj, dict) else None,
        "error": r.get("error"),
        "elapsed": r.get("elapsed"),
    }


def t_color(model: str, b64: str) -> dict:
    r = _vision_call(model, b64, COLOR_PROMPT, max_tokens=300)
    out = text_of(r)
    pairs = {}
    for line in out.splitlines():
        m = re.match(r"\s*[-*]?\s*([A-Za-z ]+?)\s*[:=-]\s*(.+)", line)
        if m:
            pairs[m.group(1).strip().lower()] = m.group(2).strip().lower()
    return {
        "name": "vision_colors",
        "score": 0.0 if not pairs else 1.0,
        "detail": f"{len(pairs)} regions",
        "raw": out[:2000],
        "parsed": pairs,
        "error": r.get("error"),
        "elapsed": r.get("elapsed"),
    }


def t_stability(model: str, b64: str, first: str) -> dict:
    r = _vision_call(model, b64, CAPTION_PROMPT, temperature=0.9)
    second = text_of(r)
    words = lambda s: set(re.findall(r"[a-z]{4,}", s.lower()))
    a, b = words(first), words(second)
    jac = len(a & b) / max(1, len(a | b))
    return {
        "name": "vision_stability",
        "score": round(jac, 2),
        "detail": f"jaccard vs temp0 = {jac:.2f}",
        "raw": second[:3000],
        "error": r.get("error"),
        "elapsed": r.get("elapsed"),
    }


# ---------------------------------------------------------------- runner
def run(args) -> None:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "results.jsonl"

    allm = [m for m in models() if m.get("type") != "embeddings"]
    if args.models:
        want = {s.strip().lower() for s in args.models.split(",")}
        allm = [m for m in allm if m["id"].lower() in want]
    print(f"auditing {len(allm)} models -> {out_dir}", flush=True)

    b64, tmpjpg = b64_image(BASELINE_IMG)
    print(f"baseline image: {BASELINE_IMG.name} -> {tmpjpg} "
          f"({len(b64) // 1024}KB b64)", flush=True)

    for m in allm:
        mid, mtype = m["id"], m.get("type")
        row = {"model": mid, "type": mtype, "quant": m.get("quantization"),
               "params": m.get("arch"), "tests": {}}
        print(f"\n=== {mid} ({mtype}) ===", flush=True)
        unload_all()
        ok, load_s, flags_used, log = load(mid, args.ctx)
        row["load_ok"], row["load_s"] = ok, round(load_s, 1)
        row["load_flags"] = flags_used
        if not ok:
            row["error"] = log[-500:]
            print(f"  LOAD FAILED ({flags_used}): {log[-160:]}", flush=True)
            results_path.open("a", encoding="utf-8").write(
                json.dumps(row, ensure_ascii=False) + "\n")
            continue
        print(f"  loaded in {load_s:.0f}s", flush=True)

        for fn in (t_echo, t_tools, t_json_shape, t_h3):
            t = fn(mid)
            row["tests"][t["name"]] = t
            print(f"  {t['name']:20s} {t['score']:.2f}  {t['detail']}"
                  f"{'  ERR:' + str(t['error'])[:60] if t.get('error') else ''}",
                  flush=True)

        if mtype == "vlm":
            t = t_caption(mid, b64)
            row["tests"][t["name"]] = t
            print(f"  {t['name']:20s} {t['score']:.2f}  {t['detail']}", flush=True)
            row["tests"]["vision_colors"] = t_color(mid, b64)
            print(f"  vision_colors        {row['tests']['vision_colors']['detail']}",
                  flush=True)
            cap = t["raw"]
            row["tests"]["vision_stability"] = t_stability(mid, b64, cap)
            print(f"  vision_stability     "
                  f"{row['tests']['vision_stability']['detail']}", flush=True)

        us = usage_of({"usage": {}})  # placeholder for shape clarity
        results_path.open("a", encoding="utf-8").write(
            json.dumps(row, ensure_ascii=False) + "\n")
        unload_all()

    print("\ndone ->", results_path, flush=True)


def sweep(args) -> None:
    """Load-only pass over the quiver: which models even come up, and how fast."""
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "loadsweep.jsonl"
    allm = [m for m in models() if m.get("type") != "embeddings"]
    if args.models:
        want = {s.strip().lower() for s in args.models.split(",")}
        allm = [m for m in allm if m["id"].lower() in want]
    print(f"load sweep: {len(allm)} models", flush=True)
    for m in allm:
        mid = m["id"]
        unload_all()
        ok, dt, flags, log = load(mid, args.ctx)
        verdict = "LOADED" if ok else "CRASH/FAIL"
        print(f"{verdict:11s} {dt:6.1f}s  {flags:14s} {mid}"
              + ("" if ok else f"  <- {log[-120:]}"), flush=True)
        path.open("a", encoding="utf-8").write(json.dumps(
            {"model": mid, "type": m.get("type"), "quant": m.get("quantization"),
             "loaded": ok, "seconds": round(dt, 1), "flags": flags,
             "log": log[-500:]}, ensure_ascii=False) + "\n")
        unload_all()
    print("sweep ->", path, flush=True)


def report(args) -> None:
    out_dir = Path(args.out)
    rows = [json.loads(l) for l in (out_dir / "results.jsonl").read_text(
        encoding="utf-8").splitlines() if l.strip()]
    order = ["echo_identifiers", "tool_call", "json_shape", "h3_3field",
             "vision_caption", "vision_stability"]
    md = ["# LM Studio quiver audit", "",
          f"baseline image: `{BASELINE_IMG}`", "",
          "| model | load s | " + " | ".join(order) + " |",
          "|---" * (len(order) + 2) + "|"]
    for r in rows:
        cells = []
        for k in order:
            t = r["tests"].get(k)
            cells.append(f"{t['score']:.2f}" if t else "—")
        md.append(f"| {r['model']} | {r.get('load_s', 'FAIL')} | "
                  + " | ".join(cells) + " |")
    md += ["", "## Details", ""]
    for r in rows:
        md.append(f"### {r['model']}")
        md.append(f"load_ok={r.get('load_ok')} load_s={r.get('load_s')} "
                  f"quant={r.get('quant')}")
        for k, t in r["tests"].items():
            md.append(f"- **{k}** score={t['score']} — {t['detail']}")
            md.append(f"  ```\n  " + t["raw"][:2500].replace("\n", "\n  ") + "\n  ```")
        md.append("")
    (out_dir / "report.md").write_text("\n".join(md), encoding="utf-8")

    # cross-model colour agreement on the baseline image
    cols = {}
    for r in rows:
        p = (r["tests"].get("vision_colors") or {}).get("parsed")
        if p:
            cols[r["model"]] = {k: v for k, v in p.items()}
    if cols:
        agree = ["", "## Colour answers on the baseline image", ""]
        for mod, pairs in cols.items():
            agree.append(f"- **{mod}**: " + "; ".join(f"{k}={v}" for k, v in pairs.items()))
        (out_dir / "report.md").open("a", encoding="utf-8").write("\n".join(agree))
    print("report ->", out_dir / "report.md")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "run", "report", "sweep"])
    ap.add_argument("--models", default="")
    ap.add_argument("--ctx", type=int, default=32768)
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    ap.add_argument("--longctx", action="store_true")
    args = ap.parse_args()
    if args.cmd == "list":
        for m in models():
            print(f"{m['id']:52s} {m.get('type'):10s} {m.get('arch'):10s} "
                  f"{str(m.get('quantization')):8s} ctx={m.get('max_context_length')}")
    elif args.cmd == "run":
        run(args)
    elif args.cmd == "sweep":
        sweep(args)
    else:
        report(args)


if __name__ == "__main__":
    main()
