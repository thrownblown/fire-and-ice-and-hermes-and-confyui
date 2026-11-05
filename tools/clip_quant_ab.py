"""A/B one knob across rigs: the CLIP quant — int8_convrot vs fp8_scaled — same seed, same prompt.

Why: the plate/Krea workflows were authored on the 5090 with `Huihui-...-int8_convrot.safetensors`. The
4090 does not have that file (only `...-fp8_scaled`), so `core/asset_reconcile.py` silently-but-loudly
substitutes it, and every image rendered on the 4090 today differs from the reference generation by that
one file. This renders the SAME graph twice — once against the int8 CLIP where it exists (5090), once
with the fp8 name (4090) — and asks the VLM to compare the two results.

Confound to state, not hide: the two quants live on different rigs, so a difference can come from the
CLIP OR from the hardware (4090 vs 5090, different llama-gguf/driver stack). With the seed fixed, the
sampler is deterministic per rig, so any difference is attributable to {CLIP quant + rig}; only a
same-rig test can isolate the quant alone. Reported as such.

Usage:
  python tools/clip_quant_ab.py --graph refs/backgrounds/jungle/jungle_plate_t01.graph.json \
      --int8-rig http://<TOMBSTONE_TS_IP>:8188 --fp8-rig http://127.0.0.1:8188
"""
from __future__ import annotations

import argparse
import base64
import copy
import json
import re
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INT8 = "Huihui-Qwen3-VL-4B-Instruct-abliterated-int8_convrot.safetensors"
FP8 = "Huihui-Qwen3-VL-4B-Instruct-abliterated-fp8_scaled.safetensors"
GF = os.environ.get("FNI_GF", "http://goldfishbowl:8888").rstrip("/")
JUDGE = os.environ.get("FNI_JUDGE_MODEL", "llama-cpp/qwen3-vl-32b-heretic_ctx128k")

SYSTEM = ("Compare two generated images made from the same prompt and seed. Describe ONLY what is "
          "visually present. Never name characters, actors or films. Reply with strict JSON: "
          '{"same_scene": bool, "differences": [str], "image_a": {"description": str}, '
          '"image_b": {"description": str}, "which_is_sharper": "a"|"b"|"same", '
          '"which_better_matches_prompt": "a"|"b"|"same", "reason": str}')


def queue(graph: dict, base: str, tag: str, outdir: Path, want_clip: str) -> Path | None:
    g = copy.deepcopy(graph)
    for node in g.values():
        if isinstance(node, dict) and "filename_prefix" in (node.get("inputs") or {}):
            node["inputs"]["filename_prefix"] = tag
    # Reconcile against the TARGET rig, always: a graph carries absolute/spelled filenames of the rig it
    # was written on, so replaying the 4090's graph on the 5090 is rejected on the VAE path before the
    # CLIP even matters (measured: "wan\\Wan2_1_VAE_fp32.safetensors not in list").
    sys.path.insert(0, str(ROOT))
    from core.asset_reconcile import snap
    snap(g, base, verbose=False)
    used = next((v for n in g.values() if isinstance(n, dict)
                 for v in (n.get("inputs") or {}).values()
                 if isinstance(v, str) and "Huihui" in v), "?")
    print(f"  {tag}: CLIP after reconcile = {used}")
    if want_clip and Path(str(used).replace("\\", "/")).name != Path(want_clip).name:
        print(f"  {tag}: ABORT — this rig cannot render {Path(want_clip).name} (has {used})")
        return None
    req = urllib.request.Request(f"{base}/prompt", data=json.dumps({"prompt": g}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        pid = json.load(urllib.request.urlopen(req, timeout=120))["prompt_id"]
    except urllib.error.HTTPError as e:
        print(f"  {tag}: queue FAILED {e.code}: {e.read().decode(errors='replace')[:300]}")
        return None
    print(f"  {tag}: queued {pid[:8]} on {base}")
    deadline = time.time() + 1200
    while time.time() < deadline:
        time.sleep(4)
        try:
            rec = json.load(urllib.request.urlopen(f"{base}/history/{pid}", timeout=60)).get(pid)
        except Exception:  # noqa: BLE001
            continue
        if not rec:
            continue
        if (rec.get("status") or {}).get("status_str") == "error":
            print(f"  {tag}: render ERROR {json.dumps((rec.get('status') or {}).get('messages'))[:300]}")
            return None
        for out in (rec.get("outputs") or {}).values():
            for img in (out.get("images") or []):
                fn = img.get("filename")
                if not fn or not fn.lower().endswith(".png"):
                    continue
                outdir.mkdir(parents=True, exist_ok=True)
                dest = outdir / fn
                url = f"{base}/view?" + urllib.parse.urlencode(
                    {"filename": fn, "type": img.get("type") or "output", "subfolder": img.get("subfolder") or ""})
                try:
                    with urllib.request.urlopen(url, timeout=240) as r, dest.open("wb") as fh:
                        fh.write(r.read())
                except urllib.error.HTTPError as e:
                    print(f"  {tag}: download FAILED {e.code} {url}")
                    return None
                print(f"  {tag}: got {fn} ({dest.stat().st_size/1e6:.1f} MB)")
                return dest
    print(f"  {tag}: TIMEOUT")
    return None


def judge(a: Path, b: Path, prompt: str) -> dict:
    def enc(p: Path) -> dict:
        return {"type": "image_url",
                "image_url": {"url": "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()}}
    body = {"model": JUDGE, "temperature": 0.0, "max_tokens": 1200,
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": [
                             {"type": "text", "text": "Original prompt: " + prompt[:600] +
                                                      "\nImage A is first, image B second."},
                             enc(a), enc(b)]}]}
    req = urllib.request.Request(f"{GF}/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          **({"Authorization": "Bearer " + os.environ["GOLDFISHBOWL_API_KEY"]}
                                             if os.environ.get("GOLDFISHBOWL_API_KEY") else {})})
    with urllib.request.urlopen(req, timeout=900) as r:
        d = json.load(r)
    txt = d["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", txt, re.S)
    return {"raw": txt, "json": json.loads(m.group(0)) if m else None, "model": d.get("model")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", required=True)
    ap.add_argument("--int8-rig", default="http://<TOMBSTONE_TS_IP>:8188")
    ap.add_argument("--fp8-rig", default="http://127.0.0.1:8188")
    ap.add_argument("--outdir", default=str(ROOT / "runs" / "clip_quant_ab"))
    a = ap.parse_args()

    raw = json.loads(Path(a.graph).read_text(encoding="utf-8"))
    graph = raw.get("prompt") if isinstance(raw.get("prompt"), dict) else raw
    # the seed/prompt come from the graph that produced the reference image
    seed = next((n["inputs"].get("seed") for n in graph.values()
                 if isinstance(n, dict) and "seed" in (n.get("inputs") or {})), None)
    prompt = ""
    for n in graph.values():
        if isinstance(n, dict):
            v = (n.get("inputs") or {}).get("positive")
            if isinstance(v, str) and len(v) > len(prompt):
                prompt = v
    print(f"seed={seed}  prompt={prompt[:90]}...")

    def with_clip(name: str) -> dict:
        g = copy.deepcopy(graph)
        for n in g.values():
            if isinstance(n, dict):
                for k, v in (n.get("inputs") or {}).items():
                    if isinstance(v, str) and "Huihui" in v and v.endswith(".safetensors"):
                        n["inputs"][k] = name
        return g

    out = Path(a.outdir)
    print("\nA = int8_convrot (the quant the workflow was authored with, on the rig that has it):")
    pa = queue(with_clip(INT8), a.int8_rig, "clipquant_int8", out, INT8)
    print("\nB = fp8_scaled (what the 4090 actually has, i.e. today's plates):")
    pb = queue(with_clip(FP8), a.fp8_rig, "clipquant_fp8", out, FP8)
    if not (pa and pb):
        print("\ncannot compare — a render failed (see above)")
        return 1

    print("\njudging with", JUDGE)
    v = judge(pa, pb, prompt)
    j = v.get("json") or {}
    print(f"  same_scene: {j.get('same_scene')}  sharper: {j.get('which_is_sharper')}  "
          f"better_match: {j.get('which_better_matches_prompt')}")
    for d in (j.get("differences") or [])[:6]:
        print("   -", str(d)[:150])
    print("  reason:", str(j.get("reason"))[:300])
    with (ROOT / "manifests" / "clip_quant_ab.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"graph": a.graph, "seed": seed, "a": str(pa.relative_to(ROOT)).replace("\\", "/"),
                             "b": str(pb.relative_to(ROOT)).replace("\\", "/"), "judge": v.get("model"),
                             "verdict": j}, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
