#!/usr/bin/env python3
"""Contact-sheet the translated Teegra stills into one viewable grid, grouped by
source frame. Letterbox to a uniform tile (never crop — project convention).

    python tools/contact_sheet.py --dir renders/5090/teegra-translate \
        --out renders/5090/teegra-translate/contact_sheet.jpg --cols 15
"""
import argparse
import os
import re
import sys
from collections import defaultdict

from PIL import Image

TILE = 288
BORDER = 6
LABEL_H = 20


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cols", type=int, default=15)
    ap.add_argument("--pattern", default=r"tr_(\d+)_\d+.*\.png")
    args = ap.parse_args(argv)

    files = sorted(fn for fn in os.listdir(args.dir)
                   if fn.lower().endswith(".png") and re.match(args.pattern, fn))
    groups = defaultdict(list)
    for fn in files:
        m = re.match(args.pattern, fn)
        key = m.group(1) if m else "_other"
        groups[key].append(fn)

    # flat, grouped by frame, each frame a labelled run of tiles
    ordered = []
    for key in sorted(groups, key=lambda k: int(k) if k.isdigit() else 1 << 30):
        ordered.append((key, groups[key]))

    cols = args.cols
    rows = 0
    tiles = []  # (key, img)
    for key, fns in ordered:
        for fn in fns:
            tiles.append((key, fn))
    rows = (len(tiles) + cols - 1) // cols

    cell = TILE + 2 * BORDER
    label_area = LABEL_H + BORDER
    sheet_w = cols * cell
    sheet_h = rows * (cell + label_area) + BORDER
    sheet = Image.new("RGB", (sheet_w, sheet_h), (24, 24, 24))

    # caption font (fallback to default if PIL lacks truetype)
    try:
        from PIL import ImageDraw, ImageFont
        font = ImageFont.truetype("arial.ttf", 13)
    except Exception:
        font = None

    for idx, (key, fn) in enumerate(tiles):
        r, c = divmod(idx, cols)
        x = c * cell + BORDER
        y = r * (cell + label_area) + BORDER
        im = Image.open(os.path.join(args.dir, fn)).convert("RGB")
        # letterbox to tile (fit, never crop)
        im.thumbnail((TILE, TILE), Image.LANCZOS)
        ox = x + (TILE - im.width) // 2
        oy = y + (TILE - im.height) // 2
        sheet.paste(im, (ox, oy))
        d = ImageDraw.Draw(sheet)
        d.text((x, y + TILE + 2), f"{fn}", fill=(220, 220, 220), font=font)

    sheet.save(args.out, quality=88)
    print(f"wrote {args.out} ({sheet_w}x{sheet_h}, {len(tiles)} tiles)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))