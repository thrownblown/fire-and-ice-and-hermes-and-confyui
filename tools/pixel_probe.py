#!/usr/bin/env python3
"""Pixel-measurement probe for reference stills — no vision model involved.

Answers color/shape questions with numbers instead of a VLM's guess:
  grid   <img>                 coarse median-color grid (locate regions numerically)
  probe  <img> x0 y0 x1 y1     dominant palette + HSV bucket counts in a crop
  glow   <img>                 bright saturated blobs (eyes/gems): bbox + hex
  rows   <img>                 per-row dark/bright/hue profile (find a belt band)

Colors are reported as hex + counts so a color-blind curator can adjudicate
without naming hues. Coordinates are in the DOWNSCALED space printed by
`grid` (default max side 900); use `--max-side 0` for original pixels.

    python tools/pixel_probe.py grid refs/characters/DARKWOLF/x.jpg
    python tools/pixel_probe.py glow refs/characters/DARKWOLF/x.jpg
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image


def load(path, max_side):
    im = Image.open(path).convert("RGB")
    if max_side and max(im.size) > max_side:
        r = max_side / max(im.size)
        im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    return im


def hexes(rgb):
    return "#%02x%02x%02x" % tuple(int(c) for c in rgb)


def palette(im, n=8):
    p = im.convert("P", palette=Image.ADAPTIVE, colors=n)
    pal = p.getpalette()
    counts = np.bincount(np.asarray(p).ravel(), minlength=n)
    order = np.argsort(counts)[::-1]
    total = counts.sum()
    out = []
    for i in order:
        if counts[i] == 0:
            continue
        rgb = pal[i * 3:i * 3 + 3]
        out.append((hexes(rgb), round(100.0 * counts[i] / total, 1)))
    return out


def cmd_grid(args):
    im = load(args.img, args.max_side)
    W, H = im.size
    a = np.asarray(im).astype(np.int16)
    print(f"{os.path.basename(args.img)}  {W}x{H} (scaled)  grid {args.gx}x{args.gy}")
    hdr = "     " + " ".join(f"{c:>7d}" for c in range(args.gx))
    print(hdr + "   x0->x1 px per col: " + str(round(W / args.gx)))
    for r in range(args.gy):
        cells = []
        for c in range(args.gx):
            y0, y1 = int(r * H / args.gy), int((r + 1) * H / args.gy)
            x0, x1 = int(c * W / args.gx), int((c + 1) * W / args.gx)
            blk = a[y0:y1, x0:x1].reshape(-1, 3)
            cells.append(hexes(np.median(blk, axis=0)))
        print(f"{r:>3d}  " + " ".join(f"{h:>7s}" for h in cells))
    print(f"y0->y1 px per row: {round(H / args.gy)}  | cell(r,c) bbox = "
          f"({round(args.gx and 0)}..)  x=[c*{round(W/args.gx)},{(c+1)*round(W/args.gx)}] y=[r*{round(H/args.gy)},{(r+1)*round(H/args.gy)}]")


def cmd_probe(args):
    im = load(args.img, args.max_side)
    x0, y0, x1, y1 = args.bbox
    crop = im.crop((x0, y0, x1, y1))
    W, H = crop.size
    hsv = np.asarray(crop.convert("HSV")).astype(np.int16)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    n = h.size
    print(f"probe {os.path.basename(args.img)} [{x0},{y0},{x1},{y1}]  {W}x{H} = {n} px")
    print("  palette:", ", ".join(f"{c} {p}%" for c, p in palette(crop)))
    # hue buckets (PIL HSV: H 0..255)
    buckets = [("red", 0, 11), ("orange", 11, 22), ("yellow", 22, 43),
               ("green", 43, 96), ("cyan", 96, 128), ("blue", 128, 171),
               ("magenta", 171, 213), ("red2", 213, 256)]
    sat_ok = s > 60
    print("  saturated px (S>60) by hue bucket:")
    for name, lo, hi in buckets:
        c = int(((h >= lo) & (h < hi) & sat_ok).sum())
        if c:
            print(f"    {name:8s} {c:7d} px  {100.0*c/n:5.2f}% of crop")
    print(f"  grayish (S<=60): {int((~sat_ok).sum())} px ({100.0*int((~sat_ok).sum())/n:.1f}%)")
    print(f"  brightness: mean V={v.mean():.0f}  dark(V<60)={100.0*int((v<60).sum())/n:.1f}%  bright(V>200)={100.0*int((v>200).sum())/n:.1f}%")


def cmd_glow(args):
    """Find SMALL bright blobs = glowing eyes/gems. Connected components on
    V>min_val (catches white glows too, not just saturated), then keep only
    blobs with area <= max_px so large bright backgrounds (sky) are rejected.
    Reports each blob's exact median/mean hex so color is numeric, not named."""
    import cv2
    im = load(args.img, args.max_side)
    rgb = np.asarray(im).astype(np.uint8)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    v = hsv[..., 2]
    mask = (v > args.min_val).astype(np.uint8)
    n, labels, stats, cents = cv2.connectedComponentsWithStats(mask, connectivity=8)
    H, W = mask.shape
    rows = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < args.min_px or area > args.max_px:
            continue
        sel = labels[y:y + h, x:x + w] == i
        px = rgb[y:y + h, x:x + w][sel].astype(np.int16)
        med = hexes(np.median(px, axis=0))
        mean = hexes(px.mean(axis=0))
        sat = int(hsv[y:y + h, x:x + w][sel][..., 1].mean()) if sel.ndim == 2 else int(hsv[..., 1][y:y+h, x:x+w][sel].mean())
        cx, cy = int(cents[i][0]), int(cents[i][1])
        rows.append((area, (int(x), int(y), int(x + w), int(y + h)), (cx, cy), med, mean, sat))
    rows.sort(key=lambda r: r[0])
    print(f"small bright blobs in {os.path.basename(args.img)} "
          f"({W}x{H}, V>{args.min_val}, area {args.min_px}..{args.max_px}):")
    if not rows:
        print("  none — try raising --max-px (eyes may be larger) or lowering --min-val")
        return
    for area, bbox, c, med, mean, sat in rows[:args.top]:
        print(f"  area={area:4d}  bbox={bbox}  centroid={c}  median={med}  mean={mean}  sat={sat}")
    # eye-pair heuristic: two similar-color blobs near same y, close in x
    print("  (eye pair = two blobs at similar y, small dx, matching hex)")


def cmd_rows(args):
    """Per-row profile: dark fraction + dominant saturated hue -> locate bands."""
    im = load(args.img, args.max_side)
    a = np.asarray(im.convert("HSV")).astype(np.int16)
    rgb = np.asarray(im).astype(np.int16)
    W0 = a.shape[1]
    xa = args.x0
    xb = args.x1 if args.x1 > xa else W0
    a = a[:, xa:xb]
    rgb = rgb[:, xa:xb]
    h, s, v = a[..., 0], a[..., 1], a[..., 2]
    H, W = v.shape
    step = max(1, H // args.rows)
    print(f"row profile {os.path.basename(args.img)} x[{xa},{xb}] ({W}x{H}, every {step}px)")
    print("   y  dark%  bright%  sat%  domHueBucket  medianRGB")
    buckets = [(0, 11, "red"), (11, 22, "orange"), (22, 43, "YELLOW"),
               (43, 96, "GREEN"), (96, 128, "cyan"), (128, 171, "blue"),
               (171, 213, "magenta"), (213, 256, "red")]
    for y in range(0, H, step):
        y1 = min(H, y + step)
        vv, ss, hh = v[y:y1], s[y:y1], h[y:y1]
        dark = 100.0 * (vv < 60).mean()
        bright = 100.0 * (vv > 200).mean()
        satm = ss > 60
        satp = 100.0 * satm.mean()
        dom = "gray"
        if satm.sum() > 0:
            best, bc = None, 0
            for lo, hi, name in buckets:
                c = int(((hh >= lo) & (hh < hi) & satm).sum())
                if c > bc:
                    bc, dom = c, name
        med = hexes(np.median(rgb[y:y1].reshape(-1, 3), axis=0))
        print(f"{y:4d}  {dark:5.1f}  {bright:6.1f}  {satp:5.1f}  {dom:12s}  {med}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("grid")
    g.add_argument("img")
    g.add_argument("--max-side", type=int, default=900)
    g.add_argument("--gx", type=int, default=8)
    g.add_argument("--gy", type=int, default=8)

    p = sub.add_parser("probe")
    p.add_argument("img")
    p.add_argument("bbox", nargs=4, type=int, metavar=("X0", "Y0", "X1", "Y1"))
    p.add_argument("--max-side", type=int, default=900)

    gl = sub.add_parser("glow")
    gl.add_argument("img")
    gl.add_argument("--max-side", type=int, default=900)
    gl.add_argument("--min-val", type=int, default=180)
    gl.add_argument("--min-px", type=int, default=8)
    gl.add_argument("--max-px", type=int, default=1200)
    gl.add_argument("--top", type=int, default=12)

    r = sub.add_parser("rows")
    r.add_argument("img")
    r.add_argument("--max-side", type=int, default=900)
    r.add_argument("--rows", type=int, default=40)
    r.add_argument("--x0", type=int, default=0)
    r.add_argument("--x1", type=int, default=0, help="x-range to scan (0 = full width)")

    args = ap.parse_args()
    {"grid": cmd_grid, "probe": cmd_probe, "glow": cmd_glow, "rows": cmd_rows}[args.cmd](args)


if __name__ == "__main__":
    main()
