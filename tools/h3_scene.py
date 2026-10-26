# -*- coding: utf-8 -*-
"""H3 scene from a Krea2 character still: FL2VA image-to-video on the 5090.

Takes a winning character still as the first frame, a scene description, and
renders a short MiniMax H3 clip (I2V — no last frame, so H3 invents motion
from the first frame + the prompt). Reuses the proven T0003 FL2VA graph as the
scaffold; the prompt is the 3-field FL2VA grammar.

    .venv/Scripts/python.exe tools/h3_scene.py \
        --still runs/subhuman-krea2/output/darkwolf/darkwolf_30s-1.0_person_03_00001_.png \
        --char darkwolf --scene "stands before a ring of megaliths, ritual fire, shamanic magic"

The scene description is wrapped into integrated_multimodal_description with
the character's cached description (descs/<CHAR>.txt) as the subject anchor.
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(r"E:/FNI")
RUN = ROOT / "runs" / "subhuman-krea2"
SCENES = RUN / "scenes"
SCAFFOLD = ROOT / "runs" / "T0003_s03_fl2va-srcfflf" / "s03-c01.json"
COMFY = "http://<TOMBSTONE_TS_IP>:8188"

# node ids from the T0003 FL2VA graph
NODE_I2V = "136"      # MiniMaxH3ImageToVideo
NODE_FIRST = "137"    # LoadImage first frame
NODE_LAST = "139"     # LoadImage last frame (removed for I2V)
NODE_PROMPT = "138"   # PrimitiveStringMultiline (the prompt text)
NODE_DUR = "132"      # PrimitiveFloat seconds
NODE_SEED = "129"     # RandomNoise
NODE_SAVE = "92"      # SaveVideo

STYLE = ("a sword-and-sandals fantasy epic at the dawn of the bronze age and the end of the "
         "neolithic: fur and hide garments, bone stone and wood weapons, crude copper, megalithic "
         "standing stones, ritual fire, shamanic magic and spirit totems, rendered as a technicolor "
         "80's/90's retro fantasy film on 35mm, vivid saturated colour, deep blacks and high contrast")


def _post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def _get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())


def upload(path):
    """Upload the still to the 5090's input/ (must exist there for LoadImage)."""
    import subprocess
    tmp = Path(ROOT) / "runs" / "subhuman-krea2" / "scenes" / "upload" / path.name
    tmp.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(path, tmp)
    out = subprocess.run(["curl", "-4", "-s", "-m", "60", "-F", "image=@%s" % tmp,
                          "-F", "overwrite=true", COMFY + "/upload/image"],
                         capture_output=True, text=True)
    return json.loads(out.stdout or "{}").get("name")


def build_prompt(char_desc, scene):
    return "\n\n".join([
        "How the reference pictures align with the target video — Picture 1 aligns with the "
        "0.00-second mark of the target video.",
        "integrated_multimodal_description: [Shot 1] " + STYLE + ". " + scene + ". On screen: "
        + char_desc + ". The camera drifts in a slow, small push as the figure moves, and only in "
        "the final seconds does the movement slow and come to rest.",
        "overall_soundscape: Wind across open ground, cloth and hide rustling with the movement, "
        "distant low chanting and the crackle of ritual fire.",
        "non_diegetic_music: Low sustained strings and a slow hand-drum pulse, sparse and ominous, "
        "dynamics quiet.",
    ])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--still", required=True)
    ap.add_argument("--char", required=True)
    ap.add_argument("--scene", required=True)
    ap.add_argument("--seconds", type=float, default=6.0)
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    still = Path(args.still)
    desc_file = RUN / "descs" / ("%s.txt" % args.char.upper())
    char_desc = desc_file.read_text(encoding="utf-8").strip() if desc_file.exists() else args.char

    g = json.loads(SCAFFOLD.read_text(encoding="utf-8"))
    # I2V: first frame only; drop the last-frame reference and loader
    g[NODE_I2V]["inputs"].pop("last_frame", None)
    g.pop(NODE_LAST, None)
    # prompt text
    g[NODE_PROMPT]["inputs"]["value"] = build_prompt(char_desc, args.scene)
    # duration (snap to 17k+5)
    g[NODE_DUR]["inputs"]["value"] = args.seconds
    g[NODE_SEED]["inputs"]["noise_seed"] = args.seed
    tag = "scene_%s_%s" % (args.char, Path(args.still).stem)
    g[NODE_SAVE]["inputs"]["filename_prefix"] = "video/" + tag
    # resolution: keep the scaffold's 0.4 MP 16:9 (fine for a scene test)

    if args.dry_run:
        print("still:", still)
        print("char desc (%d chars):" % len(char_desc), char_desc[:120] + "...")
        print(g[NODE_PROMPT]["inputs"]["value"])
        print("tag:", tag, "| seconds:", args.seconds, "| seed:", args.seed)
        return

    name = upload(still)
    print("uploaded still ->", name)
    g[NODE_FIRST]["inputs"]["image"] = name

    out = _post(COMFY + "/prompt", {"prompt": g, "client_id": "fni-scene-%d" % int(time.time())})
    if out.get("node_errors"):
        raise RuntimeError(json.dumps(out["node_errors"]))
    pid = out["prompt_id"]
    print("queued scene prompt_id:", pid)

    outdir = SCENES
    outdir.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + 1200
    while time.time() < deadline:
        rec = _get(f"{COMFY}/history/{pid}").get(pid)
        if rec and rec.get("outputs"):
            for o in rec["outputs"].values():
                for v in o.get("videos", []) + o.get("images", []) + o.get("animated", []):
                    fn = v.get("filename", "")
                    if not fn or "ComfyUI_temp" in fn:
                        continue
                    if not fn.endswith(".mp4"):
                        continue
                    url = (f"{COMFY}/view?filename={urllib.parse.quote(fn)}"
                           f"&subfolder={urllib.parse.quote(v.get('subfolder',''))}"
                           f"&type={urllib.parse.quote(v.get('type','output'))}")
                    dest = outdir / fn
                    with urllib.request.urlopen(url, timeout=120) as r:
                        dest.write_bytes(r.read())
                    print("pulled scene ->", dest, dest.stat().st_size, "bytes")
                    return
        if rec and rec.get("status", {}).get("status_str") == "error":
            raise RuntimeError(f"scene render error {pid}")
        time.sleep(6)
    raise TimeoutError(tag)


if __name__ == "__main__":
    main()
