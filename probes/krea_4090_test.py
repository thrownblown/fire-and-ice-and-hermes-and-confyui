#!/usr/bin/env python
"""Probe: run Alex's favorite Krea 2 workflow on the 4090's ComfyUI.

Template: C:/Users/gsfny/Downloads/80sfantasykreatest.json (finepornV2TURBOKrea2_v20
+ retro-fantasy LoRA + optional 'rlyjada' character LoRA, style string
"retr0fantasy, 60s Soviet fantasy-film, subtle film grain, aged theatrical print
quality", 9 steps er_sde/sgm_uniform cfg 1, 16:9 2MP).

Tests (same seed as the template for comparability):
  t0_control   exact template, unchanged            -> reproduction check
  t1_teegra    Teegra, retro-fantasy only (no char LoRA)
  t2_teegra    Teegra, + jada char LoRA at 1.0       -> identity-hijack check
  t3_darkwolf  Darkwolf, retro-fantasy only
  t4_larn      Larn, retro-fantasy only

Outputs are pulled via /view into renders/4090/krea-80sfantasy/.
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

STYLE = ("retr0fantasy, 60s Soviet fantasy-film, subtle film grain, "
         "aged theatrical print quality")

SUBJECTS = {
    "teegra": ("A stunningly beautiful young woman with long, flowing black hair and "
               "piercing green eyes. She has a delicate gold earring and a thin necklace "
               "with a small pendant. She wears a light blue wrap dress and is barefoot."),
    "darkwolf": ("A towering bare-chested warrior with a wild black mane and dark war "
                 "paint across his face, gripping a great axe, wearing a horned black "
                 "wolf cloak."),
    "larn": ("A handsome young muscular warrior with tanned skin and dark hair, wearing "
             "a fur loincloth and leather wrist wraps, holding a bronze sword."),
}

TESTS = [
    # (name, style_string, subject, jada_on)
    ("t0_control", None, None, True),                       # template unchanged
    ("t1_teegra", STYLE, SUBJECTS["teegra"], False),
    ("t2_teegra_jada", STYLE + ", caucasian, rlyjada", SUBJECTS["teegra"], True),
    ("t3_darkwolf", STYLE, SUBJECTS["darkwolf"], False),
    ("t4_larn", STYLE, SUBJECTS["larn"], False),
]


def api(path, body=None, timeout=60):
    if body is None:
        with urllib.request.urlopen(COMFY + path, timeout=timeout) as r:
            return json.loads(r.read().decode() or "null")
    req = urllib.request.Request(COMFY + path, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, data=json.dumps(body).encode(), timeout=timeout) as r:
        return json.loads(r.read().decode() or "null")


def build(name, style, subject, jada_on):
    g = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    if style is not None:
        g["137"]["inputs"]["positive"] = style + ","
    if subject is not None:
        g["135"]["inputs"]["positive"] = subject
    g["124"]["inputs"]["lora_1"]["on"] = jada_on          # jada character LoRA
    g["124"]["inputs"]["lora_7"]["on"] = True             # retro-fantasy stays on
    g["128"]["inputs"]["filename_prefix"] = f"fni_{name}"
    return g


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    queued = {}
    for name, style, subject, jada in TESTS:
        g = build(name, style, subject, jada)
        try:
            r = api("/prompt", {"prompt": g, "client_id": "hermes-krea-test"})
            queued[name] = r["prompt_id"]
            print(f"queued {name}: {r['prompt_id']}")
        except urllib.error.HTTPError as e:
            print(f"QUEUE FAILED {name}: HTTP {e.code} {e.read().decode()[:300]}")
        time.sleep(1)

    deadline = time.time() + 480
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


if __name__ == "__main__":
    sys.exit(main())
