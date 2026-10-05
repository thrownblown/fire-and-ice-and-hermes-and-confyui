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
    """Find small bright saturated blobs — glowing eyes, gems, magic."""
    im = load(args.img, args.max_side)
    a = np.asarray(im.convert("HSV")).astype(np.int16)
    h, s, v = a[..., 0], a[..., 1], a[..., 2]
    mask = (s > args.min_sat) & (v > args.min_val)
    ys, xs = np.nonzero(mask)
    if len(xs) < args.min_px:
        print(f"no glow blobs (need >= {args.min_px} px with S>{args.min_sat}, V>{args.min_val})")
        return
    # cluster by simple grid binning then merge adjacent bins
    rgb = np.asarray(im).astype(np.int16)
    H, W = mask.shape
    binx, biny = 16, 16
    gx = np.clip(xs // binx, 0, W // binx)
    gy = np.clip(ys // biny, 0, H // biny)
    keys = {}
    for x, y in zip(gx, gy):
        keys.setdefault((y, x), 0)
        keys[(y, x)] += 1
    blobs = []
    for (by, bx), cnt in sorted(keys.items(), key=lambda kv: -kv[1]):
        y0, y1 = by * biny, min(H, (by + 1) * biny)
        x0, x1 = bx * binx, min(W, (bx + 1) * binx)
        sel = mask[y0:y1, x0:x1]
        if sel.sum() < args.min_px // 4:
            continue
        px = rgb[y0:y1, x0:x1][sel]
        med = np.median(px, axis=0)
        blobs.append((cnt, (x0, y0, x1, y1), hexes(med), px.mean(axis=0)))
        if len(blobs) >= args.top:
            break
    print(f"glow blobs in {os.path.basename(args.img)} (S>{args.min_sat}, V>{args.min_val}):")
    for cnt, bbox, med, mean in blobs:
        print(f"  {cnt:5d} px  bbox={bbox}  median={med}  mean={hexes(mean)}")


def cmd_rows(args):
    """Per-row profile: dark fraction + dominant saturated hue -> locate bands."""
    im = load(args.img, args.max_side)
    a = np.asarray(im.convert("HSV")).astype(np.int16)
    rgb = np.asarray(im).astype(np.int16)
    h, s, v = a[..., 0], a[..., 1], a[..., 2]
    H, W = v.shape
    step = max(1, H // args.rows)
    print(f"row profile {os.path.basename(args.img)} ({W}x{H}, every {step}px)")
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
    gl.add_argument("--min-sat", type=int, default=100)
    gl.add_argument("--min-val", type=int, default=180)
    gl.add_argument("--min-px", type=int, default=12)
    gl.add_argument("--top", type=int, default=8)

    r = sub.add_parser("rows")
    r.add_argument("img")
    r.add_argument("--max-side", type=int, default=900)
    r.add_argument("--rows", type=int, default=40)

    args = ap.parse_args()
    {"grid": cmd_grid, "probe": cmd_probe, "glow": cmd_glow, "rows": cmd_rows}[args.cmd](args)


if __name__ == "__main__":
    main()
