#!/usr/bin/env python3
"""Scan refs/ on disk and bake the file lists into refs/refs-data.js.

Run after uploading refs via the shot-browser "connect refs folder" path
(or after copying images in by hand). Reads refs/roster.json (created if
missing), lists refs/characters/<NAME>/*.jpg|png|webp and
refs/backgrounds/<slug>/*, writes refs/refs-data.js for the browser.

    python tools/scan_refs.py
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS = os.path.join(ROOT, "refs")
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")


def load_roster():
    path = os.path.join(REFS, "roster.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"version": 1, "characters": [], "backgrounds": []}


def list_imgs(d):
    if not os.path.isdir(d):
        return []
    return sorted(
        fn for fn in os.listdir(d)
        if fn.lower().endswith(IMG_EXT)
    )


def main():
    roster = load_roster()
    nfiles = 0

    for c in roster.get("characters", []):
        d = os.path.join(REFS, "characters", c["name"])
        c["refs"] = list_imgs(d)
        nfiles += len(c["refs"])
        # traits.txt written from the browser is on-disk truth
        tpath = os.path.join(d, "traits.txt")
        if os.path.exists(tpath):
            with open(tpath, encoding="utf-8") as f:
                c["traits"] = f.read().strip()

    for b in roster.get("backgrounds", []):
        d = os.path.join(REFS, "backgrounds", b["slug"])
        b["refs"] = list_imgs(d)
        nfiles += len(b["refs"])

    # pick up orphan directories not in the roster
    known_chars = {c["name"] for c in roster.get("characters", [])}
    cdir = os.path.join(REFS, "characters")
    if os.path.isdir(cdir):
        for name in sorted(os.listdir(cdir)):
            if name not in known_chars and os.path.isdir(os.path.join(cdir, name)):
                imgs = list_imgs(os.path.join(cdir, name))
                if imgs:
                    roster["characters"].append({
                        "name": name,
                        "display": name.replace("_", " ").title(),
                        "aliases": [name.lower()],
                        "traits": "",
                        "refs": imgs,
                    })
                    nfiles += len(imgs)
                    print(f"  + new character from disk: {name} ({len(imgs)} refs)")

    known_bgs = {b["slug"] for b in roster.get("backgrounds", [])}
    bdir = os.path.join(REFS, "backgrounds")
    if os.path.isdir(bdir):
        for slug in sorted(os.listdir(bdir)):
            if slug not in known_bgs and os.path.isdir(os.path.join(bdir, slug)):
                imgs = list_imgs(os.path.join(bdir, slug))
                if imgs:
                    roster["backgrounds"].append({
                        "slug": slug,
                        "name": slug.replace("-", " ").title(),
                        "settings": [],
                        "refs": imgs,
                    })
                    nfiles += len(imgs)
                    print(f"  + new background from disk: {slug} ({len(imgs)} refs)")

    with open(os.path.join(REFS, "roster.json"), "w", encoding="utf-8") as f:
        json.dump(roster, f, indent=2, ensure_ascii=False)

    js = "window.REFSDATA = " + json.dumps(roster, ensure_ascii=False, separators=(",", ":")) + ";\n"
    with open(os.path.join(REFS, "refs-data.js"), "w", encoding="utf-8") as f:
        f.write(js)

    print(f"scanned: {len(roster['characters'])} characters, {len(roster['backgrounds'])} backgrounds, {nfiles} ref images")
    print("wrote refs/roster.json + refs/refs-data.js")


if __name__ == "__main__":
    main()
