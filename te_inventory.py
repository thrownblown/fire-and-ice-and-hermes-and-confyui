#!/usr/bin/env python3
"""Inventory ComfyUI text encoders and flag which could work as a VLM. Read-only."""
import os, re, sys, json, struct
from collections import Counter

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/ComfyUI/models")
DIRS = ["text_encoders", "clip", "LLM", "llm"]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "te-inventory.md")

def st_header(path):
    with open(path, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        return json.loads(f.read(n))

def gguf_arch(path):
    try:
        with open(path, "rb") as f:
            head = f.read(1 << 20)
        m = re.search(rb"general\.architecture.{12}([a-z0-9_]+)", head, re.S)
        return m.group(1).decode() if m else "?"
    except Exception:
        return "?"

def classify(keys, dtypes):
    k = " ".join(keys[:5000]).lower()
    has_lm = any(("lm_head" in x) or x.endswith("output.weight") for x in keys)
    has_vis = any(re.match(r"(model\.)?(visual|vision_tower|vision_model|vision_encoder|multi_modal_projector)", x) for x in keys)
    layers = {int(m.group(1)) for x in keys for m in [re.search(r"layers\.(\d+)\.", x)] if m}
    arch = "?"
    for name, pat in [("t5/umt5", "encoder.block"), ("clip", "text_model.encoder"), ("qwen", "qwen"),
                      ("gemma", "gemma"), ("mistral", "mistral"), ("llama", "llama")]:
        if pat in k: arch = name; break
    if arch == "?" and layers: arch = "decoder-LLM (arch ?)"
    quant = "fp8_scaled" if any("scale_weight" in x or "weight_scale" in x for x in keys) else ",".join(sorted(dtypes))
    encoder_only = arch in ("t5/umt5", "clip")
    if encoder_only:
        verdict = "no (encoder-only, can't generate text)"
    elif has_lm and has_vis:
        verdict = "CANDIDATE VLM (needs conversion to HF/GGUF)"
    elif has_lm:
        verdict = "text LLM only (no vision)"
    elif has_vis:
        verdict = "vision tower but no lm_head (can't talk)"
    else:
        verdict = "no (truncated encoder)"
    return arch, has_lm, has_vis, (max(layers) + 1 if layers else 0), quant, verdict

rows = []
for d in DIRS:
    p = os.path.join(ROOT, d)
    if not os.path.isdir(p): continue
    for dp, _, files in os.walk(p):
        for fn in sorted(files):
            fp = os.path.join(dp, fn); gb = os.path.getsize(fp) / 1e9
            if fn.endswith(".safetensors"):
                try:
                    h = st_header(fp); h.pop("__metadata__", None)
                    keys = list(h.keys()); dts = Counter(v["dtype"] for v in h.values())
                    arch, lm, vis, nl, q, v = classify(keys, set(dts))
                except Exception as e:
                    arch, lm, vis, nl, q, v = "?", "?", "?", 0, "?", "error: %s" % e
            elif fn.endswith(".gguf"):
                arch, lm, vis, nl, q, v = gguf_arch(fp), "?", "?", 0, "gguf", "GGUF: try LM Studio directly (vision needs an mmproj)"
            else:
                continue
            rows.append((os.path.relpath(fp, ROOT), "%.1f" % gb, arch, lm, vis, nl, q, v))

md = ["# Text encoder inventory", "Root: `%s`" % ROOT, "",
      "| file | GB | arch | lm_head | vision | layers | dtype/quant | verdict |", "|---|---|---|---|---|---|---|---|"]
md += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
open(OUT, "w").write("\n".join(md) + "\n")
print("\n".join(md))
print("\nwrote", OUT, "rows", len(rows))
