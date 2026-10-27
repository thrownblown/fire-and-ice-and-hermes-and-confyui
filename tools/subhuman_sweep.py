# -*- coding: utf-8 -*-
"""Krea2 LoRA sweep, rig-aware: fixed description, grid over style LoRA x actor.

Renders on either the 5090 (tombstone) or the 4090 (mh370 local ComfyUI).
Each rig's clip/unet/vae names are fetched from that rig's own /object_info at
startup (no hand-copied paths, no escaping bugs), and every actor LoRA is
verified against the rig's LoRA Manager catalog before queueing — a missing
actor raises, it can never silently render as "none".

The sweep grid is style config x actor x base model, with --gens seeds per cell
(4 by default). Base models are the Krea2 checkpoint merges listed in
BASE_MODELS below; the sweep resolves each slug to the rig's real unet filename,
so the grid spans several base models instead of a single krea170277.

    .venv/Scripts/python.exe tools/subhuman_sweep.py --char taro --rig 4090 --dry-run
    .venv/Scripts/python.exe tools/subhuman_sweep.py --char darkwolf --rig 4090 --gens 4
    .venv/Scripts/python.exe tools/subhuman_sweep.py --char juliana --rig 5090 --base moody
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(r"E:/FNI")
RUN = ROOT / "runs" / "subhuman-krea2"

RIGS = {
    "5090": "http://<TOMBSTONE_TS_IP>:8188",
    "4090": "http://127.0.0.1:8188",
}

# --- style LoRAs: name -> (lora file, trigger words) ---------------------
STYLE_LORAS = {
    "30sTechnicolor": ("krea/30sTechnicolor_Krea2Raw.safetensors",
                       "ArsMovieStill, movie still from a 1930s technicolor movie"),
    "80sFantasy": ("krea/80sFantasy_Krea2Raw_000004500.safetensors",
                   "ArsMovieStill, 80s Fantasy Movie Still"),
    "retro-fantasy": ("krea/retro-fantasy.safetensors", "retr0fantasy"),
    "retro-80s": ("krea/retro-80s.safetensors", ""),  # Neon VHS Dreams: no trigger
}
STYLE_SLOT = {
    "30sTechnicolor": "lora_4",
    "80sFantasy": "lora_5",
    "retro-80s": "lora_6",
    "retro-fantasy": "lora_7",
}

# --- actor / ID LoRAs: name -> lora file ---------------------------------
ACTORS = {
    "person_07": "krea/krea2_person_07_v1_onetrainer.safetensors",
    "person_03": "krea/krea2_person_03_v1_onetrainer.safetensors",
    "person_08": "krea/krea2_person_08_v1_onetrainer.safetensors",
    "person_04": "krea/krea2_person_04_v1_onetrainer.safetensors",
    "person_01": "krea/krea2_person_01_v1_onetrainer.safetensors",
    "person_11": "krea/krea2_person_11_v1_onetrainer.safetensors",
    "person_12": "krea/krea2_person_12_v1_onetrainer.safetensors",
    "person_06": "krea/krea2_person_06_v1_onetrainer.safetensors",
    "person_13": "krea/krea2_person_13_v1_onetrainer.safetensors",
    "person_10": "krea/krea2_person_10_v1_onetrainer.safetensors",
    "person_14": "krea/krea2_person_14_v1_onetrainer.safetensors",
    "person_25": "krea/krea2_person_25_v1_onetrainer.safetensors",
    "person_15": "krea/krea2_person_15_v1_onetrainer.safetensors",
    "person_17": "krea/krea2_person_17_v1_onetrainer.safetensors",
    "person_23": "krea/krea2_person_23_v1_onetrainer.safetensors",
    "person_22": "krea/krea2_person_22_v1_onetrainer.safetensors",
    "person_09": "krea/krea2_person_09_v1_onetrainer.safetensors",
    "person_21": "krea/krea2_person_21_v1_onetrainer.safetensors",
    "person_05": "krea/krea2_person_05_v1_onetrainer.safetensors",
    "person_19": "krea/krea2_person_19_v1_onetrainer.safetensors",
    "person_20": "krea/krea2_person_20_v1_onetrainer.safetensors",
    "person_18": "krea/krea2_person_18_v1_onetrainer.safetensors",
    "person_24": "krea/krea2_person_24_v1_onetrainer.safetensors",
    "person_16": "krea/krea2_person_16_v1_onetrainer.safetensors",
    "person_02": "krea/krea2_person_02_v1_onetrainer.safetensors",
}
ACTOR_SLOTS = ["lora_10", "lora_11", "lora_12", "lora_13", "lora_14", "lora_15"]

# --- Krea2 base models: slug -> (unet substring, steps, sampler, scheduler) ---
# The substring is matched against the target rig's own UNETLoader list, so one
# entry resolves on both rigs regardless of path separator. Non-turbo merges use
# the proven 9-step er_sde recipe; the *Turbo* / *INT8TURBO* merges want 4 steps
# with sa_solver/beta (the 4-step convention) — that second recipe is OPT-IN and
# unverified per base, so turbo bases are NOT in the default set.
BASE_MODELS = {
    "krea170277": ("krea170277", 9, "er_sde", "sgm_uniform"),
    "moody": ("moodyKrea2Mix_v50", 9, "er_sde", "sgm_uniform"),
    "kreamania": ("kreamania_variant5", 9, "er_sde", "sgm_uniform"),
    "krast": ("krast_v20", 9, "er_sde", "sgm_uniform"),
    # turbo (opt-in via --base; 4-step recipe unverified per base)
    "dasiwa": ("DasiwaKrea2TurboRaw", 4, "sa_solver", "beta"),
    "muse30": ("museByStableYogi_v30TurboInt8", 4, "sa_solver", "beta"),
    "realism15": ("realismByStableYogi_v15INT8TURBO", 4, "sa_solver", "beta"),
    "krea2turbo": ("Krea2_Turbo_convrot_int8mixed", 4, "sa_solver", "beta"),
}
DEFAULT_BASES = ["krea170277", "moody", "kreamania", "krast"]

# --- per-character sweep config ------------------------------------------
def _c(rig, actors, desc=None, prefix=None):
    return {"rig": rig, "prefix": prefix,
            "actors": actors,
            "desc": str(RUN / desc) if desc else None}

CHARS = {
    # 4090 rig — keanu/person_11/person_12/person_06/person_13/person_10 live here
    "taro": _c("4090", ["none", "person_14", "person_11", "person_13"], "descs/TARO.txt", "taro"),
    "darkwolf": _c("4090", ["none", "person_11", "person_12", "person_13"], "descs/DARKWOLF.txt"),
    "jarol": _c("4090", ["none", "person_06", "person_12", "person_10"], "descs/JAROL.txt"),
    "tutor": _c("4090", ["none", "person_06", "person_12", "person_10"], "descs/TUTOR.txt"),
    "otwa": _c("4090", ["none", "person_13", "person_12", "person_10"], "descs/OTWA.txt"),
    "nekron": _c("4090", ["none", "person_14", "person_11", "person_13"], "descs/NEKRON.txt"),
    "envoys": _c("4090", ["none", "person_11", "person_06"], "descs/ENVOYS.txt"),
    "subhuman": _c("4090", ["none", "person_11", "person_13"], "descs/SUBHUMAN.txt"),
    # 5090 rig — person_08/person_03/person_07/person_04/person_01 + wide female pool
    "larn": _c("5090", ["none", "person_03", "person_08", "person_01"], "descs/LARN.txt"),
    "juliana": _c("5090", ["none", "person_25", "person_15", "person_17"], "descs/JULIANA.txt"),
    "roliel": _c("5090", ["none", "person_23", "person_22", "person_09"], "descs/ROLIEL.txt"),
    "teegra": _c("5090", ["none", "person_21", "person_05", "person_22"], "descs/TEEGRA.txt"),
    "shaitan": _c("5090", ["none"], "descs/SHAITAN.txt"),
    "spirit": _c("5090", ["none"], "descs/SPIRIT.txt"),
    # subhuman family (already swept)
    "leader": _c("5090", ["none", "person_07", "person_03", "person_08"], None, "sub_leader"),
    "captain": _c("5090", ["none", "person_07", "person_03", "person_08"], None, "sub_captain"),
}

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
TEMPLATE = RUN / "templates" / "leader_template.graph.json"


def _get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())


def _post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def rig_models(comfy):
    oi = _get(comfy + "/object_info/" + urllib.parse.quote("CLIPLoader"))
    clips = list(oi.values())[0]["input"]["required"]["clip_name"][0]
    oi = _get(comfy + "/object_info/" + urllib.parse.quote("VAELoader"))
    vaes = list(oi.values())[0]["input"]["required"]["vae_name"][0]

    def pick(items, *subs):
        for it in items:
            if all(s in it.lower() for s in subs):
                return it
        return None

    clip = pick(clips, "qwen3-vl-4b") or pick(clips, "huihui")
    vae = pick(vaes, "wan2_1_vae_fp32")
    assert clip and vae, "rig model resolution failed: clip=%s vae=%s" % (clip, vae)
    return {"clip": clip, "vae": vae}


def rig_bases(comfy, slugs):
    """Resolve each base-model slug to that rig's real unet filename (or skip)."""
    oi = _get(comfy + "/object_info/" + urllib.parse.quote("UNETLoader"))
    unets = list(oi.values())[0]["input"]["required"]["unet_name"][0]
    out = {}
    for slug in slugs:
        sub = BASE_MODELS[slug][0].lower()
        hit = next((u for u in unets if sub in u.lower()), None)
        if hit:
            out[slug] = hit
        else:
            print("  WARN: base %r (%s) NOT on rig — skipping" % (slug, BASE_MODELS[slug][0]))
    return out


def rig_loras(comfy):
    names = set()
    page = 1
    while True:
        d = _get(f"{comfy}/api/lm/loras/list?page={page}&page_size=100")
        b = d.get("items", [])
        for it in b:
            names.add(it.get("file_name", ""))
        if len(b) < 100 or page > 30:
            break
        page += 1
    return names


def pre_prompt(active_styles):
    trigs = []
    for sname, _s in active_styles:
        t = STYLE_LORAS[sname][1].rstrip(",").strip()
        if t:
            trigs.append(t)
    parts = list(dict.fromkeys(trigs)) + [QUALITY_TAIL]
    return ", ".join(parts) + ","


def build_graph(cfg, models, base_desc, unet, steps=9, sampler="er_sde", scheduler="sgm_uniform"):
    g = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    g[POS_MAIN]["inputs"]["positive"] = base_desc
    g[POS_PRE]["inputs"]["positive"] = pre_prompt(cfg["styles"])
    g["120"]["inputs"]["clip_name"] = models["clip"]
    g["121"]["inputs"]["unet_name"] = unet
    g["122"]["inputs"]["vae_name"] = models["vae"]
    g[SAMPLER]["inputs"]["steps"] = steps
    g[SAMPLER]["inputs"]["sampler_name"] = sampler
    g[SAMPLER]["inputs"]["scheduler"] = scheduler
    for slot in list(STYLE_SLOT.values()) + ACTOR_SLOTS:
        if slot in g[LORA_NODE]["inputs"] and isinstance(g[LORA_NODE]["inputs"][slot], dict):
            g[LORA_NODE]["inputs"][slot]["on"] = False
    for sname, strength in cfg["styles"]:
        slot = STYLE_SLOT[sname]
        if slot in g[LORA_NODE]["inputs"] and isinstance(g[LORA_NODE]["inputs"][slot], dict):
            g[LORA_NODE]["inputs"][slot]["on"] = True
            g[LORA_NODE]["inputs"][slot]["lora"] = STYLE_LORAS[sname][0]
            g[LORA_NODE]["inputs"][slot]["strength"] = strength
    if cfg["actor"] != "none":
        aslot = ACTOR_SLOTS[0]
        g[LORA_NODE]["inputs"][aslot] = {"on": True, "lora": ACTORS[cfg["actor"]], "strength": 1.0}
    return g


def render(comfy, g, outdir):
    out = _post(f"{comfy}/prompt", {"prompt": g, "client_id": "fni-sweep-%d" % int(time.time())})
    if out.get("node_errors"):
        raise RuntimeError(json.dumps(out["node_errors"]))
    pid = out["prompt_id"]
    outdir.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + 600
    while time.time() < deadline:
        rec = _get(f"{comfy}/history/{pid}").get(pid)
        if rec and rec.get("outputs"):
            for o in rec["outputs"].values():
                for img in o.get("images", []):
                    if "ComfyUI_temp" in img["filename"]:
                        continue
                    url = (f"{comfy}/view?filename={urllib.parse.quote(img['filename'])}"
                           f"&subfolder={urllib.parse.quote(img.get('subfolder',''))}"
                           f"&type={urllib.parse.quote(img.get('type','output'))}")
                    dest = outdir / img["filename"]
                    with urllib.request.urlopen(url, timeout=60) as r:
                        dest.write_bytes(r.read())
                    return str(dest)
        if rec and rec.get("status", {}).get("status_str") == "error":
            raise RuntimeError(f"render error {pid}")
        time.sleep(4)
    raise TimeoutError(g[SAVE]["inputs"]["filename_prefix"])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--char", choices=list(CHARS), default="taro")
    ap.add_argument("--rig", choices=list(RIGS), default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--actor", default=None)
    ap.add_argument("--style", default=None)
    ap.add_argument("--desc-file", default=None)
    ap.add_argument("--seed-base", type=int, default=SEED_BASE)
    ap.add_argument("--gens", type=int, default=4, help="seeds per style x actor x base cell")
    ap.add_argument("--base", default=None, choices=list(BASE_MODELS),
                    help="single base model; default = the DEFAULT_BASES variety set")
    args = ap.parse_args()

    char = CHARS[args.char]
    rig = args.rig or char["rig"]
    comfy = RIGS[rig]
    models = rig_models(comfy)
    loras = rig_loras(comfy)
    base_slugs = [args.base] if args.base else DEFAULT_BASES
    bases = rig_bases(comfy, base_slugs)
    if not bases:
        raise SystemExit("no base models resolved on rig %s" % rig)

    for aname in char["actors"]:
        if aname == "none":
            continue
        fname = ACTORS[aname].split("/")[-1].replace(".safetensors", "")
        if fname not in loras:
            raise SystemExit("actor %r (%s) NOT on rig %s" % (aname, fname, rig))
    for sname in STYLE_LORAS:
        fname = STYLE_LORAS[sname][0].split("/")[-1].replace(".safetensors", "")
        if fname not in loras:
            raise SystemExit("style %r (%s) NOT on rig %s" % (sname, fname, rig))

    if args.desc_file:
        base_desc = Path(args.desc_file).read_text(encoding="utf-8").strip()
    elif char["desc"]:
        base_desc = Path(char["desc"]).read_text(encoding="utf-8").strip()
    else:
        base_desc = json.loads(TEMPLATE.read_text(encoding="utf-8"))[POS_MAIN]["inputs"]["positive"]

    style_map = dict(STYLE_CONFIGS)
    style_sel = [args.style] if args.style else [s for s, _ in STYLE_CONFIGS]
    actor_sel = [args.actor] if args.actor else char["actors"]
    cells = []
    for sname in style_sel:
        conf = style_map[sname]
        for aname in actor_sel:
            for bslug in sorted(bases):
                cells.append({"style_cfg": sname, "styles": conf, "actor": aname, "base": bslug})

    outdir = RUN / "output" / args.char
    outdir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        print("rig %s (%s) models: %s" % (rig, comfy, models))
        print("base models:", ", ".join(sorted(bases)))
        print("base description (%d chars):" % len(base_desc), base_desc[:140] + "...")
        print("cells: %d = %d styles x %d actors x %d bases (x %d gens = %d renders)"
              % (len(cells), len(style_sel), len(actor_sel), len(bases), args.gens,
                 len(cells) * args.gens))
        for c in cells:
            print("  %-12s x %-14s x %-10s -> pre=%r"
                  % (c["style_cfg"], c["actor"], c["base"], pre_prompt(c["styles"])[:50]))
        return

    manifest = RUN / ("%s_sweep_manifest.jsonl" % args.char)
    done = set()
    if manifest.exists():
        done = {json.loads(l)["tag"] for l in manifest.read_text(encoding="utf-8").splitlines() if l.strip()}
    prefix = char["prefix"] or args.char
    with manifest.open("a", encoding="utf-8") as mf:
        for i, c in enumerate(cells):
            _sub, steps, sampler, scheduler = BASE_MODELS[c["base"]]
            unet = bases[c["base"]]
            for gi in range(args.gens):
                tag = "%s_%s_%s_%s_g%d" % (prefix, c["style_cfg"], c["actor"], c["base"], gi + 1)
                if tag in done:
                    continue
                seed = args.seed_base + i * args.gens + gi
                g = build_graph(c, models, base_desc, unet, steps, sampler, scheduler)
                g[SAMPLER]["inputs"]["seed"] = seed
                g[SAVE]["inputs"]["filename_prefix"] = tag
                print("[%s %d/%d] %s base=%s steps=%d seed=%d ..."
                      % (rig, i * args.gens + gi + 1, len(cells) * args.gens, tag,
                         c["base"], steps, seed), flush=True)
                try:
                    dest = render(comfy, g, outdir)
                except Exception as e:  # noqa: BLE001
                    dest = None
                    print("    FAILED:", e, flush=True)
                mf.write(json.dumps({"tag": tag, "rig": rig, "style_cfg": c["style_cfg"],
                                     "actor": c["actor"], "base": c["base"], "gen": gi + 1,
                                     "seed": seed, "pre": pre_prompt(c["styles"]),
                                     "file": dest}) + "\n")
                mf.flush()
    print("sweep done ->", manifest)


if __name__ == "__main__":
    main()
