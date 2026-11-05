"""Make sure the local vision model is actually resident before a VLM batch.

Why this exists (log-confirmed 2026-11-05 from LM Studio's own server log):

  * `Unloading model qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s due to TTL expiration.` — the
    ejections are LM Studio's TTL, not a crash. In the same window a 32B was loaded and TTL-unloaded
    too, so the two models churn against each other on the one box.
  * While nothing is resident, an image request comes back `400 {'error': 'terminated'}`
    (previously `400 "Model is unloaded"`). Neither message says "nothing is loaded", and the failed
    request never reaches the model, so there is nothing in the model log either. From the caller it
    is indistinguishable from a broken server or a corrupt image — which is exactly how it was
    mis-diagnosed before.
  * `GET /v1/models` LISTS models whether or not they are loaded, so it proves nothing. `lms ps` is
    the authority on what is resident.

So: check residency, load if absent with an explicit TTL, and report what happened. Use before any
batch (cast checks, sheet audits, caption passes) rather than discovering the eject mid-run.

Usage:
  python tools/vlm_ready.py                     # ensure the configured id, 2 h TTL
  python tools/vlm_ready.py --id <other-id>     # ensure something else
  python tools/vlm_ready.py --check             # report only, never load
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

LMS = Path(r"C:/Users/gsfny/.lmstudio/bin/lms.exe")
DEFAULT_ID = "qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s"


def loaded_ids() -> list[str]:
    """IDs reported resident by `lms ps` (the authority — /v1/models lists unloaded ones too)."""
    try:
        out = subprocess.run([str(LMS), "ps"], capture_output=True, text=True, timeout=120).stdout
    except Exception as e:  # noqa: BLE001
        print(f"  lms ps failed: {type(e).__name__}: {e}")
        return []
    ids = []
    for line in out.splitlines():
        m = re.match(r"^(\S+)\s{2,}", line)
        if m and ("@" in m.group(1) or m.group(1).isalnum() is False):
            ids.append(m.group(1).strip())
    if "No models are currently loaded" in out:
        return []
    return ids


def ensure(model_id: str, ttl: int, check_only: bool, force: bool = False) -> int:
    ids = loaded_ids()
    print(f"resident: {ids or 'none'}")
    if model_id in ids and not force:
        print(f"  {model_id} is loaded — nothing to do (use --force to re-load it with this TTL)")
        return 0
    if check_only:
        print(f"  {model_id} is NOT loaded (check-only, not loading)")
        return 1
    if model_id in ids and force:
        print(f"  --force: unloading {model_id} to re-load it with --ttl {ttl}s")
        subprocess.run([str(LMS), "unload", model_id], capture_output=True, text=True, timeout=600)
    if ids and model_id not in ids:
        print(f"  note: {len(ids)} other model(s) resident — LM Studio will evict one to make room")
    t0 = time.time()
    print(f"  loading {model_id} with --ttl {ttl}s ...")
    r = subprocess.run([str(LMS), "load", model_id, "--ttl", str(ttl), "--yes"],
                       capture_output=True, text=True, timeout=1800)
    took = time.time() - t0
    ok = model_id in loaded_ids()
    tail = (r.stdout or "").strip().splitlines()[-1][:120] if (r.stdout or "").strip() else ((r.stderr or "")[-160:])
    print(f"  {'LOADED' if ok else 'FAILED'} in {took:.1f}s — {tail}")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", default=DEFAULT_ID)
    ap.add_argument("--ttl", type=int, default=7200, help="idle seconds before LM Studio unloads it")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="re-load even if resident, so the TTL actually applies to this instance")
    a = ap.parse_args()
    return ensure(a.id, a.ttl, a.check, a.force)


if __name__ == "__main__":
    sys.exit(main())
