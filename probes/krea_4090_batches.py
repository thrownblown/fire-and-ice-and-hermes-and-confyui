#!/usr/bin/env python
"""Probe: Krea 2 batch driver for the 4090's ComfyUI (generalized).

Supersedes probes/krea_4090_test.py (batch a below reproduces its five tests).
Template: C:/Users/gsfny/Downloads/80sfantasykreatest.json (finepornV2TURBOKrea2_v20
+ retro-fantasy LoRA + optional 'rlyjada' character LoRA, style string
"retr0fantasy, 60s Soviet fantasy-film, subtle film grain, aged theatrical print
quality", 9 steps er_sde/sgm_uniform cfg 1, 16:9 2MP).

Batches (run: .venv/Scripts/python.exe probes/krea_4090_batches.py [batch|all])

  a  baseline + character tests (same seed as template):
     t0_control     exact template                     -> reproduction check
     t1_teegra      Teegra, retro-fantasy only
     t2_teegra      Teegra + jada char LoRA @1.0        -> identity-hijack check
     t3_darkwolf    Darkwolf, retro-fantasy only
     t4_larn        Larn, retro-fantasy only

  b  setup plates (paintings as set pieces), no people:
     plate_s05_filmic   Fire Keep study as a film still
     plate_s05_painted  same scene+seed as an oil painting -> one-variable A/B
     plate_s06_cavern   icy cavern, torch pool right, cold blue behind
     plate_icepeak      Ice Peak fortress, wide establishing

  c  identity stability + style-LoRA A/B (Teegra, retro-fantasy stays on):
     teegra_seed42  same description, seed 424242
     teegra_seed7   same description, seed 1337
     teegra_30stech + 30sTechnicolor LoRA @1.0
     teegra_80sfan  + 80sFantasy LoRA @1.0
     teegra_retro80 + retro-80s LoRA @1.0

Outputs land in renders/4090/krea-80sfantasy/.
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

COMFY = "http://127.0.0.1:8188"
TEMPLATE = Path("C:/Users/gsfny/Downloads/80sfantasykreatest.json")
DEST = Path(r"E:/FNI/renders/4090/krea-80sfantasy")
TEMPLATE_SEED = 82036621553915

STYLE = ("retr0fantasy, 60s Soviet fantasy-film, subtle film grain, "
         "aged theatrical print quality")
PAINTED = STYLE + ", oil painting, thick visible brushstrokes, painted canvas texture"

SUBJECTS = {
    "teegra": ("A stunningly beautiful young woman with long, flowing black hair and "
               "piercing green eyes. She has a delicate gold earring and a thin necklace "
               "with a small pendant. She wears a light blue wrap dress and is barefoot."),
    "darkwolf": ("A towering bare-chested warrior with a wild black mane and dark war "
                 "paint across his face, gripping a great axe, wearing a horned black "
                 "wolf cloak."),
    "larn": ("A handsome young muscular warrior with tanned skin and dark hair, wearing "
             "a fur loincloth and leather wrist wraps, holding a bronze sword."),
    "s05_study": ("Interior of a medieval castle study, warm torchlight and candles, "
                  "stone walls, wooden shelves full of scrolls and old books, a carved "
                  "wooden desk, empty room, no people, wide shot."),
    "s06_cavern": ("Interior of an icy cavern, a warm torch pool of light on the right "
                   "wall, cold blue light receding into the depth, frozen ice walls, "
                   "empty, no people, wide shot."),
    "icepeak": ("A vast frozen fortress of black obsidian spires rising from glaciers "
                "and snowfields, stormy sky, distant icy mountains, no people, wide "
                "establishing shot."),
}

# (name, style, subject_key, jada_on, extra_loras_on, seed)
BATCHES = {
    "a": [
        ("t0_control", None, None, True, [], None),
        ("t1_teegra", STYLE, "teegra", False, [], None),
        ("t2_teegra_jada", STYLE + ", caucasian, rlyjada", "teegra", True, [], None),
        ("t3_darkwolf", STYLE, "darkwolf", False, [], None),
        ("t4_larn", STYLE, "larn", False, [], None),
    ],
    "b": [
        ("plate_s05_filmic", STYLE, "s05_study", False, [], None),
        ("plate_s05_painted", PAINTED, "s05_study", False, [], None),
        ("plate_s06_cavern", STYLE, "s06_cavern", False, [], None),
        ("plate_icepeak", STYLE, "icepeak", False, [], None),
    ],
    "c": [
        ("teegra_seed42", STYLE, "teegra", False, [], 424242),
        ("teegra_seed7", STYLE, "teegra", False, [], 1337),
        ("teegra_30stech", STYLE, "teegra", False, [4], None),
        ("teegra_80sfan", STYLE, "teegra", False, [5], None),
        ("teegra_retro80", STYLE, "teegra", False, [6], None),
    ],
}


def api(path, body=None, timeout=60):
    if body is None:
        with urllib.request.urlopen(COMFY + path, timeout=timeout) as r:
            return json.loads(r.read().decode() or "null")
    req = urllib.request.Request(COMFY + path, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, data=json.dumps(body).encode(), timeout=timeout) as r:
        return json.loads(r.read().decode() or "null")


def build(style, subject_key, jada_on, extra_on, seed):
    g = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    if style is not None:
        g["137"]["inputs"]["positive"] = style + ","
    if subject_key is not None:
        g["135"]["inputs"]["positive"] = SUBJECTS[subject_key]
    loras = g["124"]["inputs"]
    for slot in range(1, 8):
        entry = loras.get(f"lora_{slot}")
        if isinstance(entry, dict):
            entry["on"] = False
    loras["lora_7"]["on"] = True                     # retro-fantasy always on
    loras["lora_1"]["on"] = jada_on                  # jada character LoRA
    for slot in extra_on:
        loras[f"lora_{slot}"]["on"] = True
    if seed is not None:
        g["102"]["inputs"]["seed"] = seed
    return g


def run(batch_names):
    DEST.mkdir(parents=True, exist_ok=True)
    queued = {}
    for b in batch_names:
        for name, style, subj, jada, extra, seed in BATCHES[b]:
            g = build(style, subj, jada, extra, seed)
            g["128"]["inputs"]["filename_prefix"] = f"fni_{name}"
            try:
                r = api("/prompt", {"prompt": g, "client_id": "hermes-krea-test"})
                queued[name] = r["prompt_id"]
                print(f"queued {name}: {r['prompt_id']}")
            except urllib.error.HTTPError as e:
                print(f"QUEUE FAILED {name}: HTTP {e.code} {e.read().decode()[:300]}")
            time.sleep(1)

    deadline = time.time() + 540
    done = {}
    while time.time() < deadline and len(done) < len(queued):
        for name, pid in queued.items():
            if name in done:
                continue
            h = api(f"/history/{pid}")
            if not h:
                continue
            rec = h.get(pid) or {}
            status = (rec.get("status") or {}).get("status_str", "")
            outs = rec.get("outputs") or {}
            imgs = [im for o in outs.values() for im in (o.get("images") or [])]
            if status == "success" or imgs:
                done[name] = imgs
                print(f"done {name}: {status} ({len(imgs)} images)")
            elif status == "error":
                done[name] = []
                print(f"ERROR {name}: {json.dumps(rec.get('status'))[:400]}")
        time.sleep(5)

    print("\n== pulling outputs ==")
    saved = []
    for name, imgs in done.items():
        for im in imgs:
            q = urllib.parse.urlencode({"filename": im["filename"],
                                        "subfolder": im.get("subfolder", ""),
                                        "type": im.get("type", "output")})
            data = urllib.request.urlopen(f"{COMFY}/view?{q}", timeout=300).read()
            out = DEST / im["filename"]
            out.write_bytes(data)
            saved.append((name, out, len(data)))
            print(f"  {out} ({len(data)/1048576:.1f} MB)")
    print(f"\n{len(saved)} files -> {DEST}")
    missing = [n for n in queued if n not in done]
    if missing:
        print("NOT FINISHED (still running?):", missing)
        return 2
    return 0


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    names = list(BATCHES) if which == "all" else [which]
    for n in names:
        if n not in BATCHES:
            print(f"unknown batch {n}; have {list(BATCHES)}")
            return 1
    return run(names)


if __name__ == "__main__":
    sys.exit(main())
