"""Re-render the plates the fp8 CLIP contaminated, on the rig that has the right CLIP, at the queue FRONT.

Why: the plate workflow is authored against `Huihui-...-int8_convrot.safetensors`, which exists only on the
5090. The 4090 has the fp8 quant, and `core/asset_reconcile` substitutes it — measured consequence: the
fp8 CLIP renders **human figures into plates whose prompt says "no people"** (three figures in the jungle
plate, same seed; a stronger "no people at all, no figures, no silhouettes" prompt did NOT remove them,
so it cannot be prompt-compensated). The 5090's queue is deep with H3 work, but ComfyUI accepts
`"front": true` on /prompt, so these tiny renders jump ahead and cost the batch ~40 s each.

It replays each location's own t01 graph (same prompt, same seed) with the int8 CLIP and writes take 02,
so the comparison against the dirty take 01 is like-for-like.

Usage:
  python tools/rerender_plates_int8.py --slugs jungle,swamp --dry
  python tools/rerender_plates_int8.py --slugs jungle,swamp
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RIG = "http://<TOMBSTONE_TS_IP>:8188"        # the 5090: the only box with the int8_convrot CLIP
BG = ROOT / "refs" / "backgrounds"
INT8 = "Huihui-Qwen3-VL-4B-Instruct-abliterated-int8_convrot.safetensors"


def post(url: str, payload: dict, timeout: int = 120) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slugs", required=True)
    ap.add_argument("--take", type=int, default=2)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    sys.path.insert(0, str(ROOT))
    from core.asset_reconcile import snap

    for slug in [s.strip() for s in a.slugs.split(",") if s.strip()]:
        d = BG / slug
        src = d / f"{slug}_plate_t01.graph.json"
        if not src.exists():
            print(f"[{slug}] no t01 graph sidecar — skipped (nothing to replay)")
            continue
        raw = json.loads(src.read_text(encoding="utf-8"))
        g = copy.deepcopy(raw.get("prompt") if isinstance(raw.get("prompt"), dict) else raw)
        seed = next((n["inputs"].get("seed") for n in g.values()
                     if isinstance(n, dict) and "seed" in (n.get("inputs") or {})), None)
        prefix = f"{slug}_plate_t{a.take:02d}"
        for n in g.values():
            if isinstance(n, dict):
                for k, v in (n.get("inputs") or {}).items():
                    if isinstance(v, str) and "Huihui" in v and v.endswith(".safetensors"):
                        n["inputs"][k] = INT8
                if "filename_prefix" in (n.get("inputs") or {}):
                    n["inputs"]["filename_prefix"] = prefix
        snap(g, RIG, verbose=False)
        used = next((v for n in g.values() if isinstance(n, dict)
                     for v in (n.get("inputs") or {}).values()
                     if isinstance(v, str) and "Huihui" in v), "?")
        print(f"[{slug}] seed={seed} prefix={prefix} clip={Path(str(used).replace(chr(92),'/')).name}")
        if a.dry:
            continue
        if "int8_convrot" not in str(used):
            print(f"[{slug}] ABORT — rig would use {used}, not the int8 CLIP")
            continue
        pid = post(RIG + "/prompt", {"prompt": g, "front": True})["prompt_id"]
        print(f"[{slug}] queued FRONT {pid[:8]}")
        deadline = time.time() + 1800
        got = None
        while time.time() < deadline and not got:
            time.sleep(5)
            try:
                rec = json.load(urllib.request.urlopen(f"{RIG}/history/{pid}", timeout=60)).get(pid)
            except Exception:  # noqa: BLE001
                continue
            if not rec:
                continue
            for out in (rec.get("outputs") or {}).values():
                for img in (out.get("images") or []):
                    fn = img.get("filename")
                    if not fn or not fn.lower().endswith(".png"):
                        continue
                    url = f"{RIG}/view?" + urllib.parse.urlencode(
                        {"filename": fn, "type": img.get("type") or "output", "subfolder": img.get("subfolder") or ""})
                    dest = d / f"{prefix}_00001_.png"
                    dest.write_bytes(urllib.request.urlopen(url, timeout=240).read())
                    got = dest
                    break
        print(f"[{slug}] {'got ' + got.name if got else 'TIMEOUT — nothing pulled'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
