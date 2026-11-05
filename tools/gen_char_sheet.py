#!/usr/bin/env python
"""Generate a technicolor-register character sheet on the 5090 (H3 ref2va still).

Proven recipe: graphs/H3CharSheet_technicolor.json (extracted from the Oct-18
Juliana regen) = H3 ref2va still + retro-fantasy LoRA @1.05 + a single identity
still as <Picture 1>. Style comes from the LoRA + the house-style wording; identity
comes from the still. Vary ONLY the identity still, the character name, and the seed.

Usage:
    .venv/Scripts/python.exe tools/gen_char_sheet.py --char LARN          # dry-run (graph only)
    .venv/Scripts/python.exe tools/gen_char_sheet.py --char LARN --queue  # upload + POST + pull
    .venv/Scripts/python.exe tools/gen_char_sheet.py --all --queue        # all 12, sequential

Identity stills are expected at refs/characters/<NAME>/id_<NAME>.* (staged by the
caller). Output lands in refs/characters/<NAME>/ as <NAME>_sheet_t<NN>.png.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(r"E:/FNI")
TEMPLATE = ROOT / "graphs" / "H3CharSheet_technicolor.json"
COMFY = os.environ.get("FNI_COMFY", "http://<TOMBSTONE_TS_IP>:8188").rstrip("/")

# node ids in the template
NODE_LOAD_IMAGE = "25"
NODE_PROMPT = "28"
NODE_SEED = "12"
NODE_SAVE = "68"
NODE_LORA = "22"

# the 12 characters in this pass (8 missing mains + 4 regenerations)
CHARACTERS = [
    "LARN", "JAROL", "TARO", "ROLIEL", "OTWA", "SHAITAN", "SPIRIT", "TUTOR",
    "TEEGRA", "JULIANA", "NEKRON", "DARKWOLF",
]

# house-style sheet prompt. <NAME> and <COSTUME> are the only variables; <Picture 1> is the
# identity still. The costume wording comes from the character's own traits.txt — the register
# sentence used to say "practical leather-and-brass costume", which every sheet obeyed over its own
# reference: 13 characters in purple robes, ochre hides, red tunics and white/blue garments all came
# back in brown leather with gold studs. Measured 2026-11-04 (TEEGRA): dropping that clause and
# naming the film's costume flips the sheet to canon at the same LoRA strength (1.05).
PROMPT_TMPL = """integrated_multimodal_description:

subject_definitions:
<NAME> character from <Picture 1>, rendered as a live-action 80s sword-and-sandals fantasy character.
CANON (authoritative, from the film — the costume and colours must match this, not a generic
sword-and-sandals look): <COSTUME>

summary:
[reference generation] static image of a character sheet. Keep the identity, face, hair, costume and proportions of <Picture 1>. Render it in the technicolor 80s sword-and-sandals register: broad theatrical performance, vivid saturated color with deep blacks. Do not restyle the costume as leather armour and do not add metal fittings, studs or plates the canon does not have.

retention_analysis:
<NAME>: fully_preserved.

detailed_description:
The target video is a static image of a character sheet on a plain white background. Each element is separate and does not overlap.

[Shot 1] static image. Neutral expression on every view.

1. On the left, a portrait (head and chest) of <NAME>, close up, neutral expression, white background.
2. In the center, four full-body views of <NAME>, neutral stance, arms slightly away from the body: straight from the front, straight from the side, three-quarter back, straight from the back.
3. On the right, exactly 6 circles, 2 columns by 3 rows, nothing else:
   circle 1: a single eye.
   circle 2: the mouth.
   circle 3: one ear with its earring.
   circle 4: a hair color swatch.
   circle 5: a skin color swatch.
   circle 6: an outfit fabric swatch.

overall_soundscape: N/A

non_diegetic_music: N/A"""


# Photographic sheet template — Alex's ruling 2026-11-05: "we need to give realistic not illustrated
# character sheets to H3". Measured the same day: all three audited t02 sheets read as ILLUSTRATION
# to the 32B ("flat shading, uniform skin texture, stylized line work, non-photorealistic lighting"),
# which is what a style LoRA at 1.05 plus design-sheet furniture ("6 circles", "colour swatches")
# invites. This variant asks for photographs of a person instead, and drops the swatch furniture.
REALISM_TMPL = """integrated_multimodal_description:

subject_definitions:
<NAME> character from <Picture 1>. CANON (authoritative, from the film — face, hair, costume and
colours must match this): <COSTUME>

summary:
[reference generation] photographic character reference sheet: a set of REAL PHOTOGRAPHS of a living
actor in costume, on a plain neutral studio backdrop under soft even daylight. Photographic realism:
35mm film still, natural skin texture with pores and fine imperfections, real fabric weave and
creasing, shallow depth of field, subtle film grain. NOT an illustration, NOT a painting, NOT a 3D
render, NOT cel-shaded, no line work, no flat colour fills, no stylisation of features.

retention_analysis:
<NAME>: fully_preserved.

detailed_description:
The target video is a set of photographs of one person, photographed on the same day on the same
neutral backdrop. Each photograph is separate and does not overlap.

[Shot 1] static. Natural, neutral expression.

1. On the left, a head-and-shoulders photograph of <NAME>, looking at camera, soft studio light.
2. In the centre, two full-length photographs of <NAME>, arms relaxed at the sides: one straight
   from the front, one from the side.
3. On the right, one closer photograph of the face in three-quarter view.

Everything is a photograph of a real person in real fabric; the backdrop is plain and slightly warm
grey, with no scenery, no props and no other people.

overall_soundscape: N/A

non_diegetic_music: N/A"""


def _get(url: str, timeout: int = 30) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _post(url: str, payload: dict, timeout: int = 60) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def find_identity_still(name: str) -> Path:
    d = ROOT / "refs" / "characters" / name
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = d / f"id_{name}{ext}"
        if p.exists():
            return p
    # fall back: any id_* file
    for p in sorted(d.glob("id_*")):
        return p
    raise SystemExit(f"no identity still in {d} (expected id_{name}.*)")


def upload(path: Path) -> str:
    boundary = "----fnisheet"
    fn = path.name
    data = path.read_bytes()
    body = b"".join([
        (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; "
         f"filename=\"{fn}\"\r\nContent-Type: application/octet-stream\r\n\r\n").encode(),
        data,
        (f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\n"
         f"true\r\n--{boundary}--\r\n").encode(),
    ])
    req = urllib.request.Request(COMFY + "/upload/image", data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.loads(r.read().decode())
    return out.get("name") or fn


def canon_costume(name: str) -> str:
    """The character's own costume line, straight from refs/characters/<NAME>/traits.txt.

    First non-empty line only: the draft files carry a provenance paragraph on line 2, and a
    provenance note has no business inside a render prompt.
    """
    p = ROOT / "refs" / "characters" / name / "traits.txt"
    if not p.exists():
        raise SystemExit(f"{name}: no traits.txt — refusing to generate a sheet with no canon "
                         f"(this is exactly how every sheet came back in leather-and-brass)")
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            return " ".join(line.split())
    raise SystemExit(f"{name}: traits.txt is empty — no canon to render")


def build_graph(name: str, still_name: str, seed: int, prefix: str, realism: bool = False,
                lora_strength: float = 1.05) -> dict:
    g = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    g[NODE_LOAD_IMAGE]["inputs"]["image"] = still_name
    tmpl = REALISM_TMPL if realism else PROMPT_TMPL
    g[NODE_PROMPT]["inputs"]["prompt"] = (tmpl.replace("<NAME>", name)
                                              .replace("<COSTUME>", canon_costume(name)))
    g[NODE_SEED]["inputs"]["noise_seed"] = seed
    g[NODE_SAVE]["inputs"]["filename_prefix"] = prefix
    if NODE_LORA in g and "strength_model" in (g[NODE_LORA].get("inputs") or {}):
        g[NODE_LORA]["inputs"]["strength_model"] = lora_strength
    return g


def run_one(name: str, seed: int, queue: bool, take: int = 1, realism: bool = False,
            lora_strength: float = 1.05, still_override: str | None = None) -> int:
    still = Path(still_override) if still_override else find_identity_still(name)
    if not still.exists():
        raise SystemExit(f"{name}: identity still not found: {still}")
    out_dir = ROOT / "refs" / "characters" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{name}_sheet_t{take:02d}"

    still_name = still.name
    if queue:
        still_name = upload(still)
        print(f"[{name}] uploaded identity still -> {still_name}", flush=True)

    g = build_graph(name, still_name, seed, prefix, realism=realism, lora_strength=lora_strength)
    gpath = out_dir / f"{prefix}.graph.json"
    gpath.write_text(json.dumps(g, indent=1), encoding="utf-8")
    print(f"[{name}] graph -> {gpath} (still={still_name}, seed={seed}, realism={realism}, "
          f"lora={lora_strength})", flush=True)

    if not queue:
        return 0

    resp = _post(COMFY + "/prompt", {"prompt": g})
    if resp.get("node_errors"):
        raise RuntimeError(f"node_errors: {json.dumps(resp['node_errors'])}")
    pid = resp["prompt_id"]
    print(f"[{name}] queued prompt_id={pid}", flush=True)

    # poll /history then download the PNG
    deadline = time.time() + 900
    while time.time() < deadline:
        try:
            h = _get(COMFY + f"/history/{pid}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                time.sleep(3)
                continue
            raise
        rec = h.get(pid)
        if rec and rec.get("outputs"):
            for out in rec["outputs"].values():
                for im in out.get("images", []):
                    fn = im["filename"]
                    sub = im.get("subfolder", "")
                    stype = im.get("type", "output")
                    url = (COMFY + "/view?filename=" + urllib.parse.quote(fn) +
                           "&subfolder=" + urllib.parse.quote(sub) + "&type=" + stype)
                    dest = out_dir / fn
                    with urllib.request.urlopen(url, timeout=120) as r:
                        dest.write_bytes(r.read())
                    print(f"[{name}] downloaded {dest} ({dest.stat().st_size} bytes)", flush=True)
                    return 0
        if rec and rec.get("status", {}).get("status_str") == "error":
            raise RuntimeError(f"render error: {rec['status']}")
        time.sleep(5)
    raise TimeoutError(f"[{name}] prompt_id {pid} did not finish")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--char", default=None, help="character name (or '--all')")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--chars", default="", help="comma-separated names (overrides --all/--char), "
                                                "e.g. the 13 the audio-led batch consumed")
    ap.add_argument("--queue", action="store_true", help="upload + POST + pull (default dry-run)")
    ap.add_argument("--seed-base", type=int, default=700000000000000)
    ap.add_argument("--take", type=int, default=1,
                    help="take number -> filename prefix <NAME>_sheet_t<NN> (use 2 to keep t01 on disk)")
    ap.add_argument("--skip-existing", action="store_true",
                    help="skip a character whose <NAME>_sheet_t<take>*.png is already rendered")
    ap.add_argument("--realism", action="store_true",
                    help="photographic sheet template (real actor, 35mm, skin texture) instead of the "
                         "design-sheet template — Alex's ruling: give H3 realistic, not illustrated, sheets")
    ap.add_argument("--lora-strength", type=float, default=1.05,
                    help="style LoRA strength (the retro-fantasy LoRA is the likely illustrator; "
                         "0.0 turns it off)")
    ap.add_argument("--still", default=None,
                    help="override the identity still (e.g. a Qwen-Edit PHOTOREAL pass of the film "
                         "frame) — H3 ref2va reproduces its reference's medium, so a photographic "
                         "input is the only way to a photographic sheet")
    args = ap.parse_args()

    if args.chars:
        names = [c.strip() for c in args.chars.split(",") if c.strip()]
    else:
        names = CHARACTERS if args.all else ([args.char] if args.char else [])
    if not names:
        ap.error("pass --char NAME, --chars A,B,C or --all")
    for i, name in enumerate(names):
        if args.skip_existing and list((ROOT / "refs" / "characters" / name).glob(
                f"{name}_sheet_t{args.take:02d}*.png")):
            print(f"[{name}] take {args.take} already on disk — skipped", flush=True)
            continue
        seed = args.seed_base + i
        run_one(name, seed, args.queue, take=args.take, realism=args.realism,
                lora_strength=args.lora_strength, still_override=args.still)
    return 0


if __name__ == "__main__":
    sys.exit(main())
