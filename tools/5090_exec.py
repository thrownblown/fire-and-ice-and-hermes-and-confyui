#!/usr/bin/env python
"""Run arbitrary Python ON the 5090 via the GODMT_Exec node (comfyui-list-utils).

The render box has no SSH; this node (deliberately "use only in trusted workflows")
executes Python inside the ComfyUI server process and is the only remote-exec
primitive available. GODMT_Exec -> PreviewAny returns the string form of `result`.

Usage:
    .venv/Scripts/python.exe tools/5090_exec.py 'code...'
    .venv/Scripts/python.exe tools/5090_exec.py --file path.py      # run a local .py body
    .venv/Scripts/python.exe tools/5090_exec.py --poll <size> <path>  # convenience: file size vs bytes

You must set `result = <anything JSON/str-serializable>` in the code; its str()
comes back via PreviewAny's text output. The Python runs with the ComfyUI embedded
interpreter (full subprocess/os/urllib access).

This is a purpose-built remote-exec helper for the pinned 5090 (env FNI_COMFY).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
import urllib.error

COMFY = "http://<TOMBSTONE_TS_IP>:8188"


def _post(url, payload, timeout=60):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _get(url, timeout=60):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode())


def run(code: str, timeout_s: int = 180) -> dict:
    """Execute `code` on the 5090, return {'result': str, 'raw': history_record}."""
    g = {
        "1": {"class_type": "GODMT_Exec", "inputs": {"FUNC": code}},
        "2": {"class_type": "PreviewAny", "inputs": {"source": ["1", 0]}},
    }
    r = _post(f"{COMFY}/prompt", {"prompt": g, "client_id": "fni-5090-exec"})
    if r.get("node_errors"):
        return {"error": "node_errors", "detail": r["node_errors"]}
    pid = r["prompt_id"]
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        h = _get(f"{COMFY}/history/{pid}")
        rec = h.get(pid)
        if rec and rec.get("outputs"):
            text = rec["outputs"].get("2", {}).get("text", [])
            val = text[0] if text else json.dumps(rec["outputs"])
            return {"result": val, "raw": rec}
        if rec and rec.get("status", {}).get("status_str") == "error":
            return {"error": "runtime", "detail": rec["status"]}
        time.sleep(2)
    return {"error": "timeout"}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("code", nargs="*", help="python body (sets `result = ...`)")
    p.add_argument("--file", dest="file", default=None)
    p.add_argument("--timeout", type=int, default=180)
    p.add_argument("--poll", nargs=2, metavar=("BYTES", "PATH"),
                   help="poll remote file size against BYTES until reached")
    args = p.parse_args(argv)

    if args.poll:
        want, path = args.poll
        want = int(want)
        code = (
            "import os\n"
            "p = " + repr(path) + "\n"
            "sz = os.path.getsize(p) if os.path.exists(p) else 0\n"
            "done = sz >= " + str(want) + "\n"
            "result = {'size': sz, 'want': " + str(want) + ", 'done': done}\n"
        )
        deadline = time.time() + args.timeout
        while time.time() < deadline:
            out = run(code, timeout_s=60)
            if "error" in out:
                print(json.dumps(out)); return 2
            print(json.dumps({"remote": out["result"]}))
            if '"done": true' in out["result"].lower():
                return 0
            time.sleep(20)
        return 1

    code = " ".join(args.code)
    if args.file:
        code = open(args.file).read()
    if not code.strip():
        p.error("no code given")
    out = run(code, timeout_s=args.timeout)
    if "error" in out:
        print(json.dumps(out, indent=2), file=sys.stderr)
        return 2
    print(out["result"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())