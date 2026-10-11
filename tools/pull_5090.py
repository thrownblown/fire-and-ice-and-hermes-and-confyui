"""Pull ComfyUI outputs off the 5090 into the FNI folder via /view.

ComfyUI keeps its queue and /history in memory, so a host reboot loses the
record of finished work even though the files survive on disk. Run this soon
after a batch finishes (or before any planned restart).

  .venv/Scripts/python.exe tools/pull_5090.py                # everything in /history
  .venv/Scripts/python.exe tools/pull_5090.py --filter mm_   # only filenames containing
  .venv/Scripts/python.exe tools/pull_5090.py --dry-run      # list what would be pulled

Files land in renders/5090/<subfolder>/<filename>, mirroring ComfyUI's output
tree (e.g. renders/5090/video/S02-k01_full_t01_00001_.mp4,
renders/5090/2026-10-06/mm_20261006_182927_00001.mp4). Every pulled file is
recorded in renders/5090/INDEX.jsonl (filename, subfolder, bytes, prompt_id,
class_types) — that ledger is the durable record of what the 5090 produced.
"""
import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(r"E:/FNI")
COMFY = "http://192.168.12.177:8188"
DEST = ROOT / "renders" / "5090"
INDEX = DEST / "INDEX.jsonl"

# what counts as an output artifact
KINDS = ("videos", "images", "gifs", "audio")


def api(path, timeout=60):
    with urllib.request.urlopen(COMFY + path, timeout=timeout) as r:
        return json.loads(r.read().decode() or "{}")


def fetch(path, params, timeout=600):
    url = COMFY + path + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


def enumerate_outputs():
    """Every output artifact in /history, deduped, with its provenance."""
    hist = api("/history", timeout=120)
    seen = {}
    for pid, h in hist.items():
        nodes = h.get("prompt")
        class_types = []
        if isinstance(nodes, list) and len(nodes) > 2 and isinstance(nodes[2], dict):
            class_types = sorted({n.get("class_type", "") for n in nodes[2].values()
                                  if isinstance(n, dict)})
        for o in (h.get("outputs") or {}).values():
            for kind in KINDS:
                for v in (o.get(kind) or []):
                    fn = v.get("filename")
                    if not fn:
                        continue
                    sub = v.get("subfolder", "")
                    otype = v.get("type", "output")
                    key = (otype, sub, fn)
                    seen[key] = {"filename": fn, "subfolder": sub, "type": otype,
                                 "kind": kind, "prompt_id": pid, "class_types": class_types,
                                 "status": h.get("status", {}).get("status_str")}
                    # the workflow sidecar (a PNG with the graph embedded) is the
                    # only durable record of how a render was made
                    wf = v.get("workflow")
                    if wf:
                        seen[(otype, sub, wf)] = {"filename": wf, "subfolder": sub,
                                                  "type": otype, "kind": "workflow",
                                                  "prompt_id": pid, "class_types": class_types,
                                                  "status": h.get("status", {}).get("status_str")}
    return sorted(seen.values(), key=lambda r: (r["subfolder"], r["filename"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--filter", default="", help="only filenames containing this")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="re-download even if present")
    args = ap.parse_args()

    try:
        entries = enumerate_outputs()
    except Exception as e:  # noqa: BLE001
        print("cannot reach %s: %s" % (COMFY, e))
        return 1
    if args.filter:
        entries = [e for e in entries if args.filter in e["filename"]]
    if not entries:
        print("nothing in /history matches (queue/history is wiped on 5090 reboot; "
              "files already on disk must be pulled by explicit filename)")
        return 0

    DEST.mkdir(parents=True, exist_ok=True)
    fh = INDEX.open("a", encoding="utf-8")
    got = skipped = failed = 0
    total_bytes = 0
    try:
        for e in entries:
            out = DEST / e["subfolder"] / e["filename"] if e["subfolder"] else DEST / e["filename"]
            if e.get("type") and e["type"] != "output":
                out = DEST / e["type"] / e["subfolder"] / e["filename"] if e["subfolder"] \
                    else DEST / e["type"] / e["filename"]
            out.parent.mkdir(parents=True, exist_ok=True)
            if out.exists() and not args.force and out.stat().st_size > 1000:
                skipped += 1
                continue
            if args.dry_run:
                print("  would pull %s" % out.relative_to(ROOT))
                continue
            try:
                data = fetch("/view", {"filename": e["filename"],
                                       "subfolder": e["subfolder"], "type": e["type"]})
            except Exception as ex:  # noqa: BLE001
                print("  FAILED %s: %s" % (e["filename"], ex))
                failed += 1
                continue
            if len(data) < 1000:
                print("  empty/short response for %s (%d bytes)" % (e["filename"], len(data)))
                failed += 1
                continue
            out.write_bytes(data)
            got += 1
            total_bytes += len(data)
            fh.write(json.dumps({"file": str(out.relative_to(ROOT)).replace("\\", "/"),
                                 "filename": e["filename"], "subfolder": e["subfolder"],
                                 "bytes": len(data), "prompt_id": e["prompt_id"],
                                 "class_types": e["class_types"], "ts": time.time()}) + "\n")
            fh.flush()
            print("  pulled %s (%.1f MB)" % (out.relative_to(ROOT), len(data) / 1048576))
    finally:
        fh.close()
    print("pull: %d new, %d already present, %d failed, %.1f MB" %
          (got, skipped, failed, total_bytes / 1048576))
    return 0


if __name__ == "__main__":
    sys.exit(main())