#!/usr/bin/env python
"""Make small JPEG thumbnails of every scene plate, for the plate chooser in the SPA.

The plates are 1344x768 PNGs at 3-5 MB each. That is right for rendering and hopeless for a
thumbnail grid — Chrome would not paint one at all in the Decisions tab (a fetch of the same URL
returns 200 and 3.17 MB, so the URL was never the problem; the weight was). So: 480px JPEGs at
~40 KB, written to `refs/backgrounds/_thumbs/<slug>__<plate-stem>.jpg` and referenced by the builder's
plate catalogue (which prefers `img` over the raw plate).

Idempotent: skips a thumb whose source has not changed since it was written.

    .venv/Scripts/python.exe tools/make_plate_thumbs.py
    .venv/Scripts/python.exe tools/make_plate_thumbs.py --force
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

ROOT = Path(r"E:/FNI")
BGS = ROOT / "refs" / "backgrounds"
THUMBS = BGS / "_thumbs"
WIDTH = 480


def thumb_name(slug: str, plate: Path) -> str:
    return "%s__%s.jpg" % (slug, plate.stem)


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--width", type=int, default=WIDTH)
    args = ap.parse_args()

    THUMBS.mkdir(parents=True, exist_ok=True)
    made = skipped = failed = 0
    for d in sorted(p for p in BGS.iterdir() if p.is_dir() and p.name != "_thumbs"):
        plates = sorted((p for p in d.iterdir() if "_plate_" in p.name and p.suffix.lower() == ".png"),
                        key=lambda p: p.stat().st_mtime)
        for plate in plates:
            out = THUMBS / thumb_name(d.name, plate)
            if out.exists() and not args.force and out.stat().st_mtime >= plate.stat().st_mtime:
                skipped += 1
                continue
            try:
                im = Image.open(plate)
                im.load()
                if im.width > args.width:
                    resample = getattr(Image, "Resampling", Image).LANCZOS
                    im = im.resize((args.width, round(im.height * args.width / im.width)), resample)
                im.convert("RGB").save(out, "JPEG", quality=82, optimize=True)
                made += 1
            except Exception as e:  # noqa: BLE001
                print("  FAILED %s: %s" % (plate.name, str(e)[:90]))
                failed += 1

    total = sum(1 for _ in THUMBS.glob("*.jpg"))
    size = sum(p.stat().st_size for p in THUMBS.glob("*.jpg"))
    print("thumbs: %d made, %d already current, %d failed" % (made, skipped, failed))
    print("  %s: %d files, %.1f MB total" % (THUMBS, total, size / 1e6))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
