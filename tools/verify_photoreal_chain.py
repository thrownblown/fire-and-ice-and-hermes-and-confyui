"""Resolve `queued-sheet` rows in the photoreal sheet ledger — ask the RIG, then pull the artifact.

`photoreal_sheet_chain.py` only queues its stage-2 H3 sheet render, so its ledger row can say no more
than "queued" plus a prompt id. This closes that loop honestly:

  1. for every row still marked `queued-sheet`, ask the rig that took the job (see --rig) for the
     prompt id in `/history` — and in `/queue`, because still-pending is a different answer from
     failed;
  2. when the run finished, find the produced image in the history's outputs and pull it locally via
     `/view`;
  3. rewrite the ledger row to `wrote-sheet` with the local path, or to `error-sheet` with the rig's
     own error text, or leave it `queued-sheet` if it is genuinely still pending.

Never guesses: a sheet that is not in the rig's history is reported as unknown, not as success. The
ledger is rewritten in place (it is a machine ledger, not an append-only log) with a `.bak` copy of
the previous content kept beside it.

Usage:
  python tools/verify_photoreal_chain.py                 # 5090 (tombstone), the H3 rig
  python tools/verify_photoreal_chain.py --rig localhost # mh370
  python tools/verify_photoreal_chain.py --dry-run       # report only, do not rewrite the ledger
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "manifests" / "photoreal_sheet_chain.jsonl"
SHEET_DIR = ROOT / "refs" / "characters"

RIGS = {"5090": "http://<TOMBSTONE_TS_IP>:8188", "localhost": "http://127.0.0.1:8188"}


def get(base: str, path: str, timeout: int = 30):
    with urllib.request.urlopen(f"{base}{path}", timeout=timeout) as r:
        return json.load(r)


def rig_id(base: str) -> str:
    """Which machine answered — never assume (AGENTS.md): win32 = mh370/4090, linux = 5090."""
    try:
        s = get(base, "/system_stats", timeout=20).get("system", {})
        return "mh370(4090)" if s.get("os") == "win32" else f"{s.get('os')}(5090?)"
    except Exception as e:  # noqa: BLE001
        return f"unreachable ({e})"


def image_from_history(rec: dict) -> str | None:
    for out in (rec.get("outputs") or {}).values():
        for img in (out.get("images") or []):
            if (img.get("filename") or "").lower().endswith((".png", ".jpg", ".webp")):
                return img["filename"]
    return None


def error_from_history(rec: dict) -> str | None:
    st = rec.get("status") or {}
    for m in st.get("messages") or []:
        if m and m[0] == "execution_error":
            info = m[1] or {}
            return f"{info.get('node_type', '?')}: {info.get('exception_message', '')}"[:300]
    if st.get("status_str") == "error":
        return "status_str=error"
    return None


def download(base: str, filename: str, dest: Path) -> bool:
    url = f"{base}/view?" + urllib.parse.urlencode({"filename": filename, "type": "output"})
    try:
        with urllib.request.urlopen(url, timeout=120) as r, dest.open("wb") as fh:
            shutil.copyfileobj(r, fh)
        return dest.stat().st_size > 0
    except Exception as e:  # noqa: BLE001
        print(f"    pull failed: {e}")
        return False


def index_history(hist: dict) -> dict[str, tuple[str, dict]]:
    """filename -> (prompt_id, record) for every image the rig still remembers."""
    idx: dict[str, tuple[str, dict]] = {}
    for pid, rec in hist.items():
        for out in (rec.get("outputs") or {}).values():
            for img in (out.get("images") or []):
                if img.get("filename"):
                    idx[img["filename"]] = (pid, rec)
    return idx


def queued_prefixes(q: dict) -> dict[str, str]:
    """filename_prefix -> prompt_id for anything queued or running (so 'pending' is provable)."""
    out: dict[str, str] = {}
    for bucket in ("queue_running", "queue_pending"):
        for item in (q.get(bucket) or []):
            try:
                pid, graph = item[1], item[2]
            except Exception:  # noqa: BLE001
                continue
            for node in (graph or {}).values():
                if not isinstance(node, dict):
                    continue
                pref = (node.get("inputs") or {}).get("filename_prefix")
                if isinstance(pref, str) and pref:
                    out[pref.split("/")[-1]] = pid
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rig", default="5090", choices=sorted(RIGS))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    base = RIGS[args.rig]
    print(f"rig {args.rig} = {base} -> answering as {rig_id(base)}")

    rows = [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    # rows this tool can settle: anything that has an expected sheet but no confirmed local file
    todo = [r for r in rows
            if r.get("action") in ("queued-sheet", "error-stage2")
            and not (r.get("action") == "wrote-sheet")]
    print(f"ledger rows: {len(rows)} | unresolved sheet rows: {len(todo)}")
    if not todo:
        print("nothing to resolve")
        return 0

    hist = get(base, "/history?max_items=300")
    idx = index_history(hist)
    try:
        pending = queued_prefixes(get(base, "/queue"))
    except Exception as e:  # noqa: BLE001
        print(f"  (queue not readable: {e})")
        pending = {}

    changed = 0
    for r in todo:
        name, take = r["char"], int(r.get("take", 10))
        prefix = f"{name}_sheet_t{take:02d}"
        hn = next((fn for fn in idx if fn.startswith(prefix)), None)
        if hn:
            pid, rec = idx[hn]
            err = error_from_history(rec)
            if err:
                r["action"] = "error-sheet"; r["rig_error"] = err; r["prompt_id"] = pid
                print(f"  {name:<18} ERROR {err}")
                changed += 1
                continue
            dest = SHEET_DIR / name / f"{prefix}_00001_.png"
            dest.parent.mkdir(parents=True, exist_ok=True)
            ok = True if args.dry_run else download(base, hn, dest)
            if ok:
                r["action"] = "wrote-sheet"
                r["sheet"] = str(dest.relative_to(ROOT)).replace("\\", "/")
                r["pulled_from"] = f"{args.rig}:{hn}"
                r["rig"] = rig_id(base)
                size = dest.stat().st_size if dest.exists() else 0
                print(f"  {name:<18} OK {hn} -> {dest.name} ({size/1024:.0f} KB)")
            else:
                r["action"] = "unknown-sheet"; r["note"] = f"run ok but the pull failed ({hn})"
                print(f"  {name:<18} pull FAILED {hn}")
            changed += 1
            continue
        if prefix in pending:
            r["action"] = "queued-sheet"; r["prompt_id"] = pending[prefix]
            print(f"  {name:<18} still PENDING on the rig ({pending[prefix][:8]}) — leave as queued")
            continue
        r["action"] = "unknown-sheet"
        r["note"] = ("no sheet named %s in the rig's /history and nothing matching in /queue — "
                     "the render never produced a file as far as this rig can tell" % prefix)
        print(f"  {name:<18} UNKNOWN — not in history, not in queue (claiming nothing)")
        changed += 1

    if changed and not args.dry_run:
        shutil.copyfile(LEDGER, LEDGER.with_suffix(".jsonl.bak"))
        LEDGER.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                          encoding="utf-8")
        print(f"ledger rewritten ({changed} row(s)); previous content at {LEDGER.name}.bak")
    else:
        print(f"{changed} row(s) would change" + (" (dry run, ledger untouched)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
