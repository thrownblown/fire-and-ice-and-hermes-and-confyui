"""Snap a ComfyUI graph's model filenames onto the rig that is actually going to run it.

Why: a saved workflow names the files its author had. The other rig has the same models under
different paths or quant spellings, and ComfyUI rejects the whole prompt with
`HTTP 400 value_not_in_list` — which the caller usually sees as a bare 400 with no explanation.
Measured 2026-11-05: a plate graph written on the 5090 asked for
`Huihui-Qwen3-VL-4B-Instruct-abliterated-int8_convrot.safetensors` and `krea/finepornV2TURBOKrea2_v10.safetensors`;
the 4090 has the fp8 CLIP and spells the LoRA path `krea\\...`. Same class of bug as the LoRA Manager
refiling that broke refrun's queueing.

The mapping is derived from the rig, never hardcoded: for every node input that looks like a model file,
ask `/object_info/<class_type>` for the legal list of that input and match by BASENAME (case-insensitive,
`/` and `\\` treated alike). A value that matches nothing is left alone and reported, so the following
400 still happens — but now you know which node caused it.

Usage:
    from core.asset_reconcile import snap
    changes = snap(graph, "http://127.0.0.1:8188")
    for c in changes: print(c)

CLI (dry run on a graph file):
    python core/asset_reconcile.py --graph path.json --rig http://127.0.0.1:8188
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.request
from pathlib import Path

MODEL_EXTS = (".safetensors", ".pt", ".pth", ".ckpt", ".gguf", ".bin")


def _norm(p: str) -> str:
    return Path(str(p).replace("\\", "/")).name.lower()


def _object_inputs(base: str, class_type: str) -> dict[str, list]:
    """{input_name: [legal values]} for one node class on that rig (empty on any failure)."""
    try:
        d = json.load(urllib.request.urlopen(f"{base}/object_info/{class_type}", timeout=60))
    except Exception:  # noqa: BLE001
        return {}
    spec = (d.get(class_type) or {}).get("input") or {}
    out: dict[str, list] = {}
    for group in ("required", "optional"):
        for name, val in (spec.get(group) or {}).items():
            if isinstance(val, list) and val and isinstance(val[0], list):
                out[name] = val[0]
    return out


def snap(graph: dict, base: str, verbose: bool = True) -> list[dict]:
    """Rewrite model-file inputs in `graph` to names the rig accepts. Returns the changes made."""
    cache: dict[str, dict[str, list]] = {}
    changes: list[dict] = []
    for node_id, node in list(graph.items()):
        if not isinstance(node, dict):
            continue
        ct = node.get("class_type")
        inputs = node.get("inputs")
        if not ct or not isinstance(inputs, dict):
            continue
        for key, val in list(inputs.items()):
            if not isinstance(val, str) or not val.lower().endswith(MODEL_EXTS):
                continue
            legal = cache.setdefault(ct, _object_inputs(base, ct)).get(key)
            if not legal:
                continue
            if val in legal:
                continue
            want = _norm(val)
            hit = next((c for c in legal if _norm(c) == want), None)
            kind = "path"
            if hit is None:                      # fall back to a contains match (path/quant suffixes vary)
                stem = want.rsplit(".", 1)[0]
                cands = [c for c in legal if stem in _norm(c) or _norm(c).rsplit(".", 1)[0] in stem]
                hit = cands[0] if len(cands) == 1 else None
            if hit is None:
                # Last resort: trim the requested name from the right, one token at a time, until what is
                # left is a prefix of EXACTLY ONE legal file. That is how a quant swap is found
                # (…-int8_convrot → …-fp8_scaled) without ever guessing between two candidates. It IS a
                # different quant, so the change is reported as a substitution, never silently.
                toks = re.split(r"[-_]", want.rsplit(".", 1)[0])
                for cut in range(len(toks) - 1, 3, -1):
                    pref = "-".join(toks[:cut])
                    cands = [c for c in legal if _norm(c).startswith(pref)]
                    if len(cands) == 1:
                        hit, kind = cands[0], "quant-substitute"
                        break
            if hit and hit != val:
                inputs[key] = hit
                changes.append({"node": node_id, "class_type": ct, "input": key,
                                "from": val, "to": hit, "kind": kind})
                if verbose:
                    tag = "SUBSTITUTE (different quant — check it)" if kind == "quant-substitute" else "path"
                    print(f"  [reconcile] {ct} node {node_id}.{key}: {val} -> {hit}   [{tag}]")
            elif not hit and verbose:
                print(f"  [reconcile] {ct} node {node_id}.{key}: '{val}' matches NOTHING on this rig "
                      f"({len(legal)} legal values) — left as-is, expect a 400 here")
    return changes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", required=True)
    ap.add_argument("--rig", default="http://127.0.0.1:8188")
    ap.add_argument("--write", action="store_true", help="write the snapped graph back to the file")
    a = ap.parse_args()
    g = json.loads(Path(a.graph).read_text(encoding="utf-8"))
    ch = snap(g, a.rig)
    print(f"{len(ch)} change(s)")
    if a.write and ch:
        Path(a.graph).write_text(json.dumps(g, indent=1), encoding="utf-8")
        print("written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
