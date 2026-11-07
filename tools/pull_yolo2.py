"""YOLO pass 2 (the "movie 2" run): probe the 5090 by NAME and pull what is there.

Why this exists: `/history` is memory-only on the 5090 and was wiped by the 2026-11-03
reboot, so `tools/pull_5090.py` (which enumerates /history) cannot see the 134 chunks
that were re-queued on 2026-11-05. Filenames are deterministic, so we probe
`/view?filename=<chunk>_audioOnly_t01_00001_.mp4&subfolder=video` directly.

Pass 1 (2026-10-27/28, 122 chunks) and pass 2 (2026-11-05, 134 chunks) are DISJOINT sets —
pass 2 is exactly the chunks pass 1 had skipped for "no sheeted subjects" — so there is no
filename collision. Kept in their own directory anyway so the SPA can label the pass.

    .venv/Scripts/python.exe tools/pull_yolo2.py --probe      # counts only, no download
    .venv/Scripts/python.exe tools/pull_yolo2.py              # probe + pull into runs/yolo_output2/
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(r"E:/FNI")
COMFY = os.environ.get("FNI_COMFY", "http://<TOMBSTONE_TS_IP>:8188").rstrip("/")
STATE = ROOT / "runs" / "yolo_state.json"
OUT = ROOT / "runs" / "yolo_output2"
LEDGER = ROOT / "runs" / "yolo2_pull.jsonl"
PASS2_DATE = "2026-11-05"


def pass2_chunks() -> list[str]:
    d = json.loads(STATE.read_text(encoding="utf-8"))
    ids = [cid for cid, v in d["chunks"].items()
           if str(v.get("queued", ""))[:10] == PASS2_DATE]
    return sorted(ids)


def pass1_chunks() -> set[str]:
    d = json.loads(STATE.read_text(encoding="utf-8"))
    return {cid for cid, v in d["chunks"].items()
            if str(v.get("queued", ""))[:10] in ("2026-10-27", "2026-10-28")}


def remote_name(cid: str) -> str:
    return f"{cid}_audioOnly_t01_00001_.mp4"


def view_url(fn: str) -> str:
    return f"{COMFY}/view?filename={fn}&subfolder=video&type=output"


def main() -> None:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--probe", action="store_true", help="only count what exists; download nothing")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    ids = pass2_chunks()
    if args.limit:
        ids = ids[:args.limit]
    p1 = pass1_chunks()
    overlap = sorted(set(ids) & p1)
    print("pass 2 chunks: %d | pass 1 chunks: %d | overlap: %d %s"
          % (len(ids), len(p1), len(overlap), "(should be 0)" if not overlap else "<-- COLLISION RISK"))
    OUT.mkdir(parents=True, exist_ok=True)

    present, missing, already, pulled, failed = [], [], [], 0, []
    fh = LEDGER.open("a", encoding="utf-8")
    try:
        for i, cid in enumerate(ids, 1):
            fn = remote_name(cid)
            dst = OUT / fn
            if dst.exists() and dst.stat().st_size > 1000:
                already.append(cid)
                continue
            try:
                with urllib.request.urlopen(view_url(fn), timeout=25) as r:
                    data = r.read()
            except urllib.error.HTTPError as e:
                (missing if e.code == 404 else failed).append((cid, e.code))
                continue
            except Exception as e:  # noqa: BLE001
                failed.append((cid, str(e)[:40]))
                continue
            present.append(cid)
            if args.probe:
                continue
            dst.write_bytes(data)
            pulled += 1
            fh.write(json.dumps({"chunk": cid, "file": fn, "bytes": len(data)}) + "\n")
            fh.flush()
            if i % 20 == 0:
                print("  ...%d/%d" % (i, len(ids)), flush=True)
    finally:
        fh.close()

    mb = sum((OUT / remote_name(c)).stat().st_size for c in already) / 1e6 if already else 0
    print("on the rig     : %d of %d" % (len(present) + len(already), len(ids)))
    print("  already local: %d (%.0f MB in %s)" % (len(already), mb, OUT))
    print("  just pulled  : %d" % pulled)
    print("  NOT on rig   : %d %s" % (len(missing), missing[:8]))
    if failed:
        print("  probe errors : %d %s" % (len(failed), failed[:5]))
    if len(present) and args.probe:
        print("  (--probe: nothing downloaded; re-run without --probe to pull %d)" % len(present))


if __name__ == "__main__":
    main()
