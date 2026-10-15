#!/usr/bin/env python
"""Sort the 5090's LoRA folder via the LoRA Manager API (metadata-driven).

The 5090 runs ComfyUI with the LoRA Manager web UI; its catalog
(http://<comfy>/loras, API under /api/lm/) is the metadata ground truth for
/home/thrownblown/comfyvenv/ComfyUI/models/loras. Sort deterministically from
civitai metadata (base_model + tags) instead of letting a local LLM guess from
preview images — that produced 98 inconsistent folders (act names mixed with
version names mixed with base models).

Scheme: <family>/<kind>/<file>.safetensors
  family = base_model family (h3, wan21, wan22, zimage, ltx, ...); the file's
           current top folder is the fallback when base_model is Unknown.
  kind   = first match in KIND_PRIORITY over the item's tags, else "misc".
           Most-specific-wins: character > style > tool > poses > action >
           concept > misc.

Commands (all idempotent, all ledgered):
  .venv/Scripts/python.exe tools/lora_sort_5090.py catalog   # pull -> manifests/lora_catalog_5090.jsonl
  .venv/Scripts/python.exe tools/lora_sort_5090.py plan      # compute moves -> manifests/lora_sort_5090_plan.jsonl
  .venv/Scripts/python.exe tools/lora_sort_5090.py apply [--limit N] [--dry-run]
  .venv/Scripts/python.exe tools/lora_sort_5090.py verify    # re-pull, count by folder
  .venv/Scripts/python.exe tools/lora_sort_5090.py revert    # undo moves from the ledger (newest first)

Moves are recorded to manifests/lora_sort_5090_moves.jsonl so any apply is
reversible. Files whose basename would collide in the target are left in place
and reported — never renamed.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(r"E:/FNI")
COMFY = os.environ.get("FNI_COMFY", "http://100.104.7.72:8188")
LORA_ROOT = "/home/thrownblown/comfyvenv/ComfyUI/models/loras"

CATALOG = ROOT / "manifests" / "lora_catalog_5090.jsonl"
PLAN = ROOT / "manifests" / "lora_sort_5090_plan.jsonl"
MOVES = ROOT / "manifests" / "lora_sort_5090_moves.jsonl"

FAMILY = {
    "MiniMax H3": "h3",
    "Wan Video 2.2 I2V-A14B": "wan22",
    "Wan Video 2.2 T2V-A14B": "wan22",
    "Wan Video 14B i2v 480p": "wan21",
    "Wan Video 14B i2v 720p": "wan21",
    "Wan Video 14B t2v": "wan21",
    "Wan Video": "wan?",
    "ZImageTurbo": "zimage",
    "LTXV": "ltx",
    "LTXV 2.3": "ltx",
    "Hunyuan Video": "hunyuan",
    "Flux.1 Kontext": "flux",
    "Illustrious": "illustrious",
    "Krea 2": "krea",
    "Qwen": "qwen",
    "SDXL 1.0": "sdxl",
    "Anima": "anima",
    "Unknown": "?",
    "": "?",
}
KIND_PRIORITY = ["character", "style", "tool", "poses", "action", "concept"]


def api_get(path, timeout=60):
    with urllib.request.urlopen(COMFY + path, timeout=timeout) as r:
        return json.loads(r.read().decode())


def api_post(path, body, timeout=120):
    req = urllib.request.Request(COMFY + path, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=json.dumps(body).encode(), timeout=timeout) as r:
            return r.status, json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:500]


def pull_catalog():
    items = []
    page = 1
    while True:
        d = api_get(f"/api/lm/loras/list?page={page}&page_size=100")
        batch = d.get("items", [])
        items.extend(batch)
        if len(batch) < 100 or page > 60:
            break
        page += 1
    return items


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.open(encoding="utf-8") if l.strip()]


def family_of(it):
    fam = FAMILY.get(it.get("base_model", ""), "misc")
    if fam in ("wan?", "?"):
        top = it["file_path"].split("/loras/")[-1].split("/")[0].lower()
        if top.startswith("wan22"):
            return "wan22"
        if top.startswith("wan21"):
            return "wan21"
        if top.startswith("wan"):
            return "wan21"
        return fam if fam != "?" else (top or "misc")
    return fam


def kind_of(it):
    tags = set(it.get("tags") or [])
    for k in KIND_PRIORITY:
        if k in tags:
            return k
    return "misc"


def target_of(it):
    return f"{family_of(it)}/{kind_of(it)}"


def cmd_catalog(_args):
    items = pull_catalog()
    write_jsonl(CATALOG, items)
    print(f"catalog: {len(items)} loras -> {CATALOG.relative_to(ROOT)}")
    return 0


def cmd_plan(_args):
    items = read_jsonl(CATALOG)
    if not items:
        print("no catalog — run catalog first")
        return 1
    plan, collisions = [], []
    seen = {}
    for it in items:
        cur_folder = it.get("folder", "")
        tgt = target_of(it)
        if cur_folder == tgt:
            continue  # already sorted
        base = it["file_name"]
        key = (tgt, base)
        if key in seen:
            collisions.append(it)  # never rename; leave in place
            continue
        seen[key] = True
        plan.append({
            "file_path": it["file_path"],
            "file_name": base,
            "from": cur_folder,
            "target": tgt,
            "base_model": it.get("base_model", ""),
            "tags": it.get("tags") or [],
        })
    write_jsonl(PLAN, plan)
    from collections import Counter
    c = Counter(p["target"] for p in plan)
    print(f"plan: {len(plan)} moves -> {PLAN.relative_to(ROOT)}")
    for k, v in c.most_common():
        print(f"  -> {k}: {v}")
    if collisions:
        print(f"collisions (left in place, never renamed): {len(collisions)}")
        for it in collisions[:10]:
            print(f"  {it['folder']}/{it['file_name']}")
    return 0


def cmd_apply(args):
    plan = read_jsonl(PLAN)
    if not plan:
        print("no plan — run plan first")
        return 1
    if args.limit:
        plan = plan[: args.limit]
    ok = failed = 0
    fh = MOVES.open("a", encoding="utf-8")
    try:
        # group by target: one bulk call per folder
        by_target = {}
        for p in plan:
            by_target.setdefault(p["target"], []).append(p)
        for tgt, group in sorted(by_target.items()):
            target_path = f"{LORA_ROOT}/{tgt}"
            if args.dry_run:
                print(f"DRY {tgt}: {len(group)} files")
                continue
            status, resp = api_post("/api/lm/loras/move_models_bulk",
                                    {"file_paths": [g["file_path"] for g in group],
                                     "target_path": target_path})
            if status != 200:
                print(f"  FAILED bulk {tgt}: HTTP {status} {resp}")
                failed += len(group)
                continue
            results = resp if isinstance(resp, list) else resp.get("results", [])
            per_file = {r.get("original_file_path"): r for r in results if isinstance(r, dict)}
            for g in group:
                r = per_file.get(g["file_path"], {})
                good = bool(r.get("success")) if r else (isinstance(resp, dict) and resp.get("success", False))
                fh.write(json.dumps({"ts": time.time(), "file_path": g["file_path"],
                                     "target": tgt, "ok": good,
                                     "new_file_path": r.get("new_file_path", ""),
                                     "resp": str(r)[:300]}) + "\n")
                if good:
                    ok += 1
                else:
                    failed += 1
            fh.flush()
            print(f"  {tgt}: {len(group)} attempted")
    finally:
        fh.close()
    print(f"apply: {ok} moved, {failed} failed")
    return 0


def cmd_verify(_args):
    items = pull_catalog()
    write_jsonl(CATALOG, items)
    from collections import Counter
    c = Counter(it.get("folder", "(root)") for it in items)
    print(f"verify: {len(items)} loras, {len(c)} folders")
    for k, v in c.most_common():
        print(f"  {k}: {v}")
    return 0


def cmd_revert(_args):
    moves = [m for m in read_jsonl(MOVES) if m.get("ok")]
    if not moves:
        print("no ledger entries to revert")
        return 0
    undone = failed = 0
    for m in reversed(moves):
        old_folder = m["from"] if "from" in m else None
        # target of the move back = the original folder (root if empty)
        src = m.get("new_file_path") or m["file_path"]
        status, resp = api_post("/api/lm/loras/move_model",
                                {"file_path": src,
                                 "target_path": f"{LORA_ROOT}/{old_folder}" if old_folder else LORA_ROOT})
        if status == 200:
            undone += 1
        else:
            failed += 1
            print(f"  FAILED revert {src}: HTTP {status} {resp}")
    print(f"revert: {undone} undone, {failed} failed")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["catalog", "plan", "apply", "verify", "revert"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    return {"catalog": cmd_catalog, "plan": cmd_plan, "apply": cmd_apply,
            "verify": cmd_verify, "revert": cmd_revert}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
