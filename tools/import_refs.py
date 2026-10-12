#!/usr/bin/env python3
"""Import a shot-browser export bundle into refs/ on disk.

The browser page (index.html, the former shot-browser) keeps edits in localStorage when it
can't write files directly (Firefox, or Chrome without the refs folder
connected). Its "export bundle" button downloads fni-refs-bundle.json;
this script folds that bundle into on-disk truth:

  refs[].dataUrl            -> refs/characters/<KEY>/<name>  (or backgrounds/<slug>/)
  traits{}                  -> roster.json characters[].traits
  bg_settings{}             -> roster.json backgrounds[].settings
  prompt_inputs{}           -> refs/prompt-inputs.json  (chunk -> Picture/Video bindings)

Then it rewrites refs/refs-data.js (same as tools/scan_refs.py).

    python tools/import_refs.py path/to/fni-refs-bundle.json
"""
import base64
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS = os.path.join(ROOT, "refs")


def main(path):
    with open(path, encoding="utf-8") as f:
        bundle = json.load(f)

    roster_path = os.path.join(REFS, "roster.json")
    roster = {"version": 1, "characters": [], "backgrounds": []}
    if os.path.exists(roster_path):
        with open(roster_path, encoding="utf-8") as f:
            roster = json.load(f)

    chars = {c["name"]: c for c in roster["characters"]}
    bgs = {b["slug"]: b for b in roster["backgrounds"]}

    # 1. ref images from dataUrls
    n_imgs = 0
    for r in bundle.get("refs", []):
        kind, key, name, data_url = r["kind"], r["key"], r["name"], r.get("dataUrl")
        if not data_url or "," not in data_url:
            continue
        sub = "characters" if kind == "char" else "backgrounds"
        d = os.path.join(REFS, sub, key)
        os.makedirs(d, exist_ok=True)
        raw = base64.b64decode(data_url.split(",", 1)[1])
        with open(os.path.join(d, os.path.basename(name)), "wb") as f:
            f.write(raw)
        n_imgs += 1
    print(f"imported {n_imgs} ref images")

    # 2. traits
    n_traits = 0
    for name, text in bundle.get("traits", {}).items():
        if name in chars and text:
            chars[name]["traits"] = text
            n_traits += 1
        elif name not in chars and text:
            chars[name] = {"name": name, "display": name.title(), "aliases": [name.lower()], "traits": text, "refs": []}
            roster["characters"].append(chars[name])
            n_traits += 1
    print(f"applied {n_traits} trait edits")

    # 3. background setting lists
    n_bg = 0
    for slug, settings in bundle.get("bg_settings", {}).items():
        if slug in bgs:
            bgs[slug]["settings"] = settings
            n_bg += 1
    print(f"applied {n_bg} background setting lists")

    # 4. chunk prompt-input bindings
    inputs = bundle.get("prompt_inputs") or {}
    if inputs:
        with open(os.path.join(REFS, "prompt-inputs.json"), "w", encoding="utf-8") as f:
            json.dump(inputs, f, indent=2, ensure_ascii=False)
        print(f"saved prompt inputs for {len(inputs)} chunks -> refs/prompt-inputs.json")

    # 5. refresh refs lists + refs-data.js (same logic as scan_refs.py)
    IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")
    def list_imgs(d):
        if not os.path.isdir(d):
            return []
        return sorted(fn for fn in os.listdir(d) if fn.lower().endswith(IMG_EXT))

    nfiles = 0
    for c in roster["characters"]:
        c["refs"] = list_imgs(os.path.join(REFS, "characters", c["name"]))
        nfiles += len(c["refs"])
    for b in roster["backgrounds"]:
        b["refs"] = list_imgs(os.path.join(REFS, "backgrounds", b["slug"]))
        nfiles += len(b["refs"])

    with open(roster_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, indent=2, ensure_ascii=False)
    js = "window.REFSDATA = " + json.dumps(roster, ensure_ascii=False, separators=(",", ":")) + ";\n"
    with open(os.path.join(REFS, "refs-data.js"), "w", encoding="utf-8") as f:
        f.write(js)
    print(f"wrote roster.json + refs-data.js ({len(roster['characters'])} chars, {len(roster['backgrounds'])} bgs, {nfiles} images)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
