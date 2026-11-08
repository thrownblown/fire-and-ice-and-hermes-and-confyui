#!/usr/bin/env python
"""Small JPEG thumbnails of the SOURCE stills the plate chooser shows.

The chooser puts each undetermined scene's own stills next to the plate candidates so a plate is
picked against what the scene actually looks like. `stills/full/` is 827 MB across 3926 files (~215 KB
each), which is fine for a single still page and wasteful for a strip of 60 — so this thumbs only the
stills the chooser actually references, taken from the baked `browser/project-data.js`.

Run it after the builder, then run the builder again so the catalogue picks the thumb URLs up (it
prefers `stills/_thumbs/<stem>.jpg` when the file exists).

    .venv/Scripts/python.exe tools/make_still_thumbs.py
    .venv/Scripts/python.exe tools/make_still_thumbs.py --force --width 480
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from PIL import Image

ROOT = Path(r"E:/FNI")
FULL = ROOT / "stills" / "full"
THUMBS = ROOT / "stills" / "_thumbs"
PROJECT = ROOT / "browser" / "project-data.js"


def referenced_stills() -> list[str]:
    """Every still filename the plate chooser references, in order."""
    txt = PROJECT.read_text(encoding="utf-8")
    d = json.loads(re.search(r"window\.PROJECTDATA = (\{.*\});", txt, re.S).group(1))
    out = []
    for dec in d.get("decisions") or []:
        for s in ((dec.get("choices") or {}).get("scenes") or []):
            for st in (s.get("stills") or []):
                fn = st.get("fn") if isinstance(st, dict) else st
                if fn and fn not in out:
                    out.append(fn)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--width", type=int, default=480)
    args = ap.parse_args()

    THUMBS.mkdir(parents=True, exist_ok=True)
    made = skipped = missing = failed = 0
    for fn in referenced_stills():
        src = FULL / fn
        if not src.exists():
            print("  MISSING %s" % fn)
            missing += 1
            continue
        out = THUMBS / (src.stem + ".jpg")
        if out.exists() and not args.force and out.stat().st_mtime >= src.stat().st_mtime:
            skipped += 1
            continue
        try:
            im = Image.open(src)
            im.load()
            if im.width > args.width:
                resample = getattr(Image, "Resampling", Image).LANCZOS
                im = im.resize((args.width, round(im.height * args.width / im.width)), resample)
            im.convert("RGB").save(out, "JPEG", quality=82, optimize=True)
            made += 1
        except Exception as e:  # noqa: BLE001
            print("  FAILED %s: %s" % (fn, str(e)[:90]))
            failed += 1

    n = len(list(THUMBS.glob("*.jpg")))
    size = sum(p.stat().st_size for p in THUMBS.glob("*.jpg"))
    print("stills: %d made, %d current, %d missing, %d failed" % (made, skipped, missing, failed))
    print("  %s: %d files, %.2f MB (full-size equivalents would be ~%.0f MB)"
          % (THUMBS, n, size / 1e6, 0.215 * n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
