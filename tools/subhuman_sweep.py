# -*- coding: utf-8 -*-
"""Subhuman Krea2 LoRA sweep: fixed description, grid over style LoRA x actor.

Kick off ONE run and get a wide set of stills, each varying only the LoRA
configuration, so the effect of each style LoRA (and its combination with an
actor/ID LoRA) can be judged side by side.

  style axis: the 4 era LoRAs alone at 1.0/1.2, plus pairs and a triple
              (see STYLE_CONFIGS). Trigger words for each active style are
              written into node 137 so the graph actually invokes the LoRA.
  actor axis: none / person_07 / person_11 / person_03 (the krea2_*_onetrainer
              celebrity faces Alex used for leader/captain).

Base description: the verbatim description that produced his good leader still
(node 135 of the 00125 render), unless --desc-file overrides it.

    .venv/Scripts/python.exe tools/subhuman_sweep.py --char leader --dry-run
    .venv/Scripts/python.exe tools/subhuman_sweep.py --char leader --count 44
    .venv/Scripts/python.exe tools/subhuman_sweep.py --char leader --actor person_07 --style "80s-1.0"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(r"E:/FNI")
RUN = ROOT / "runs" / "subhuman-krea2"
COMFY = os.environ.get("FNI_COMFY", "http://<TOMBSTONE_TS_IP>:8188").rstrip("/")

# --- style LoRAs: name -> (lora file, trigger words) ---------------------
# Slot assignments mirror the extracted template graphs (node 124).
STYLE_LORAS = {
    "30sTechnicolor": ("krea\\30sTechnicolor_Krea2Raw.safetensors",
                       "ArsMovieStill, movie still from a 1930s technicolor movie"),
    "80sFantasy": ("krea\\80sFantasy_Krea2Raw_000004500.safetensors",
                   "ArsMovieStill, 80s Fantasy Movie Still"),
    "retro-fantasy": ("krea\\retro-fantasy.safetensors", "retr0fantasy"),
    "retro-80s": ("krea\\retro-80s.safetensors", ""),  # Neon VHS Dreams: no trigger on record
}
STYLE_SLOT = {
    "30sTechnicolor": "lora_4",
    "80sFantasy": "lora_5",
    "retro-80s": "lora_6",
    "retro-fantasy": "lora_7",
}

# --- actor / ID LoRAs: name -> lora file ---------------------------------
ACTORS = {
    "none": None,
    "person_07": "krea/krea2_person_07_v1_onetrainer.safetensors",
    "person_11": "krea/krea2_person_11_v1_onetrainer.safetensors",
    "person_03": "krea/krea2_person_03_v1_onetrainer.safetensors",
}
ACTOR_SLOT = {"person_07": "lora_10", "person_11": "lora_11", "person_03": "lora_12"}

# --- style configs (the grid's style axis) -------------------------------
# name -> list of (style, strength). Empty = no style LoRA (text-only style).
STYLE_CONFIGS = [
    ("none", []),
    ("30s-1.0", [("30sTechnicolor", 1.0)]),
    ("30s-1.2", [("30sTechnicolor", 1.2)]),
    ("80s-1.0", [("80sFantasy", 1.0)]),
    ("80s-1.2", [("80sFantasy", 1.2)]),
    ("rf-1.0", [("retro-fantasy", 1.0)]),
    ("r80-1.0", [("retro-80s", 1.0)]),
    ("30s+80s", [("30sTechnicolor", 1.0), ("80sFantasy", 1.0)]),
    ("80s+rf", [("80sFantasy", 1.0), ("retro-fantasy", 0.8)]),
    ("30s+rf", [("30sTechnicolor", 1.0), ("retro-fantasy", 0.8)]),
    ("30s+80s+rf", [("30sTechnicolor", 0.8), ("80sFantasy", 0.8), ("retro-fantasy", 0.8)]),
]

POS_MAIN = "135"
POS_PRE = "137"
SAMPLER = "102"
SAVE = "128"
LORA_NODE = "124"
SEED_BASE = 900000000000000
QUALITY_TAIL = "subtle film grain, aged theatrical print quality"


def load_graph(template: Path) -> dict:
    return json.loads(template.read_text(encoding="utf-8"))


def pre_prompt(active_styles) -> str:
    trigs = []
    for sname, _strength in active_styles:
        t = STYLE_LORAS[sname][1].rstrip(",").strip()
        if t:
            trigs.append(t)
    parts = list(dict.fromkeys(trigs)) + [QUALITY_TAIL]
    return ", ".join(parts) + ","


def build_graph(cfg: dict, template: Path, base_desc: str) -> dict:
    g = load_graph(template)
    g[POS_MAIN]["inputs"]["positive"] = base_desc
    # trigger words for exactly the active style LoRAs (was hardcoded retr0fantasy)
    g[POS_PRE]["inputs"]["positive"] = pre_prompt(cfg["styles"])
    # clear every known style + actor slot first, then set the active ones
    for slot in list(STYLE_SLOT.values()) + list(ACTOR_SLOT.values()):
        if slot in g[LORA_NODE]["inputs"] and isinstance(g[LORA_NODE]["inputs"][slot], dict):
            g[LORA_NODE]["inputs"][slot]["on"] = False
    for sname, strength in cfg["styles"]:
        slot = STYLE_SLOT[sname]
        if slot in g[LORA_NODE]["inputs"] and isinstance(g[LORA_NODE]["inputs"][slot], dict):
            g[LORA_NODE]["inputs"][slot]["on"] = True
            g[LORA_NODE]["inputs"][slot]["strength"] = strength
    if cfg["actor"] != "none":
        aslot = ACTOR_SLOT[cfg["actor"]]
        # add the slot if the template lacks it (leader template only has lora_10)
        if aslot not in g[LORA_NODE]["inputs"]:
            g[LORA_NODE]["inputs"][aslot] = {"on": True, "lora": ACTORS[cfg["actor"]], "strength": 1.0}
        else:
            g[LORA_NODE]["inputs"][aslot]["on"] = True
            g[LORA_NODE]["inputs"][aslot]["strength"] = 1.0
    return g


def _post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def _get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())


def render(g: dict, outdir: Path) -> str:
    out = _post(f"{COMFY}/prompt", {"prompt": g, "client_id": "fni-sweep-%d" % int(time.time())})
    if out.get("node_errors"):
        raise RuntimeError(json.dumps(out["node_errors"]))
    pid = out["prompt_id"]
    prefix = g[SAVE]["inputs"]["filename_prefix"]
    outdir.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + 600
    while time.time() < deadline:
        rec = _get(f"{COMFY}/history/{pid}").get(pid)
        if rec and rec.get("outputs"):
            for o in rec["outputs"].values():
                for img in o.get("images", []):
                    if "ComfyUI_temp" in img["filename"]:
                        continue
                    url = f"{COMFY}/view?filename={img['filename']}&subfolder={img.get('subfolder','')}&type={img.get('type','output')}"
                    dest = outdir / img["filename"]
                    with urllib.request.urlopen(url, timeout=60) as r:
                        dest.write_bytes(r.read())
                    return str(dest)
        if rec and rec.get("status", {}).get("status_str") == "error":
            raise RuntimeError(f"render error {pid}")
        time.sleep(4)
    raise TimeoutError(prefix)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--char", choices=["leader", "captain"], default="leader")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--count", type=int, default=0)
    ap.add_argument("--actor", choices=list(ACTORS), default=None)
    ap.add_argument("--style", default=None, help="style-config name, e.g. 80s-1.0")
    ap.add_argument("--desc-file", default=None)
    ap.add_argument("--seed-base", type=int, default=SEED_BASE)
    args = ap.parse_args()

    template = RUN / "templates" / ("%s_template.graph.json" % args.char)
    # base description: default = the verbatim good-leader description already in node 135
    if args.desc_file:
        base_desc = Path(args.desc_file).read_text(encoding="utf-8").strip()
    else:
        base_desc = load_graph(template)[POS_MAIN]["inputs"]["positive"]

    # build the grid
    style_map = dict(STYLE_CONFIGS)
    style_sel = [args.style] if args.style else [s for s, _ in STYLE_CONFIGS]
    actor_sel = [args.actor] if args.actor else list(ACTORS)
    cells = []
    for sname in style_sel:
        conf = style_map.get(sname)
        if conf is None:
            raise SystemExit("unknown style config %r (have: %s)" % (sname, list(style_map)))
        for aname in actor_sel:
            cells.append({"style_cfg": sname, "styles": conf, "actor": aname})

    outdir = RUN / "output" / args.char
    outdir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        print("base description (%d chars):" % len(base_desc), base_desc[:160] + "...")
        print("cells: %d = %d style-configs x %d actors" % (len(cells), len(style_sel), len(actor_sel)))
        for c in cells:
            trig = pre_prompt(c["styles"])
            print("  %-12s x %-12s -> pre=%r" % (c["style_cfg"], c["actor"], trig[:70]))
        return

    manifest = RUN / "%s_sweep_manifest.jsonl" % args.char
    done = set()
    if manifest.exists():
        done = {json.loads(l)["tag"] for l in manifest.read_text(encoding="utf-8").splitlines() if l.strip()}
    with manifest.open("a", encoding="utf-8") as mf:
        for i, c in enumerate(cells):
            tag = "%s_%s_%s" % (args.char, c["style_cfg"], c["actor"])
            if tag in done:
                continue
            seed = args.seed_base + i
            g = build_graph(c, template, base_desc)
            g[SAMPLER]["inputs"]["seed"] = seed
            g[SAVE]["inputs"]["filename_prefix"] = "sub_%s" % tag
            print("[%d] %s seed=%d ..." % (i, tag, seed), flush=True)
            try:
                dest = render(g, outdir)
            except Exception as e:  # noqa: BLE001
                dest = None
                print("    FAILED:", e, flush=True)
            mf.write(json.dumps({"tag": tag, "style_cfg": c["style_cfg"],
                                 "actor": c["actor"], "seed": seed,
                                 "pre": pre_prompt(c["styles"]), "file": dest}) + "\n")
            mf.flush()
    print("sweep done ->", manifest)


if __name__ == "__main__":
    main()
