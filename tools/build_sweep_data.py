# -*- coding: utf-8 -*-
"""Generate browser/sweep-data.js for the shot-browser "Sweeps" view.

Catalogs the Krea2 character-sweep results: every still under
runs/subhuman-krea2/output/<char>/, joined with its style/actor (from the
sweep manifest) and its GOOD/BAD verdict (from the strict review), plus any
H3 scene videos under runs/subhuman-krea2/scenes/. Files are discovered, never
hard-coded, so re-running this after a new sweep/review just works.

Run: .venv/Scripts/python.exe tools/build_sweep_data.py
"""
import json
import re
from pathlib import Path

ROOT = Path(r"E:/FNI")
RUN = ROOT / "runs" / "subhuman-krea2"
OUT = ROOT / "browser" / "sweep-data.js"

DISPLAY = {
    "darkwolf": "Darkwolf", "envoys": "Envoys", "jarol": "Jarol",
    "juliana": "Juliana", "larn": "Larn", "nekron": "Nekron", "otwa": "Otwa",
    "roliel": "Roliel", "shaitan": "Shaitan", "spirit": "Spirit",
    "subhuman": "Subhuman", "taro": "Taro", "teegra": "Teegra", "tutor": "Tutor",
}


def rel(p):
    return p.relative_to(ROOT).as_posix()


def load_manifest(char):
    p = RUN / ("%s_sweep_manifest.jsonl" % char)
    if not p.exists():
        return {}
    out = {}
    for l in p.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        tag = r.get("tag", "")
        out[tag] = {"style": r.get("style_cfg", "?"), "actor": r.get("actor", "?"),
                    "rig": r.get("rig", "?")}
    return out


def load_review(char):
    p = RUN / ("%s_review.jsonl" % char)
    if not p.exists():
        return {}
    out = {}
    for l in p.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        # file is an absolute path; key by basename
        fn = Path(r["file"]).name
        out[fn] = {"verdict": r.get("verdict", "?"),
                   "why": (r.get("resp") or "").replace("VERDICT=", "").strip()[:160]}
    return out


def tag_of_still(fn):
    """<char>_<style>_<actor>_0000N_.png -> (char, style, actor) or None."""
    m = re.match(r"(.+)_(\d{5})_\.png$", fn)
    if not m:
        return None
    body = m.group(1)
    # split the last two underscores (actor may contain none, style may contain +)
    # style configs are none|30s-1.0|30s-1.2|80s-1.0|...|30s+80s|80s+rf|30s+rf|30s+80s+rf
    # actor is none|person_07|...|person_14. We already have the manifest; just
    # key by tag (body without the _NNNNN_ suffix is exactly the manifest tag).
    return body


def main():
    chars = []
    for d in sorted((RUN / "output").iterdir()):
        if not d.is_dir():
            continue
        name = d.name
        stills = []
        man = load_manifest(name)
        rev = load_review(name)
        for p in sorted(d.glob("*.png")):
            fn = p.name
            tag = tag_of_still(fn) or fn.rsplit("_0000", 1)[0]
            m = man.get(tag, {})
            rv = rev.get(fn, {})
            stills.append({
                "file": rel(p),
                "style": m.get("style", "?"),
                "actor": m.get("actor", "?"),
                "rig": m.get("rig", "?"),
                "verdict": rv.get("verdict", ""),
                "why": rv.get("why", ""),
            })
        # scene videos for this character
        scenes = []
        for mp4 in sorted((RUN / "scenes").glob("scene_%s_*.mp4" % name)):
            scenes.append(rel(mp4))
        # also catch any scenes whose name embeds the char differently
        for mp4 in sorted((RUN / "scenes").glob("*.mp4")):
            if name in mp4.name:
                r = rel(mp4)
                if r not in scenes:
                    scenes.append(r)
        good = sum(1 for s in stills if s["verdict"] == "GOOD")
        chars.append({
            "name": name, "display": DISPLAY.get(name, name),
            "good": good, "total": len(stills),
            "stills": stills, "scenes": scenes,
        })

    data = {"chars": chars}
    OUT.write_text("window.SWEEPDATA = " + json.dumps(data, indent=1) + ";\n", encoding="utf-8")
    print("wrote %s: %d characters, %d stills, %d scene videos"
          % (OUT, len(chars), sum(c["total"] for c in chars), sum(len(c["scenes"]) for c in chars)))
    for c in chars:
        print("  %-12s %2d/%2d GOOD  %d scenes" % (c["name"], c["good"], c["total"], len(c["scenes"])))


if __name__ == "__main__":
    main()
