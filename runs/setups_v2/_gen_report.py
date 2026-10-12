import json
from pathlib import Path

ROOT = Path(r"E:/FNI")

def load(p):
    return {json.loads(l)["scene"]: json.loads(l)
            for l in open(p, encoding="utf-8") if l.strip()}

v1 = load(ROOT / "manifests" / "continuity.jsonl")
v2 = load(ROOT / "manifests" / "continuity_v2.jsonl")

def multis(r):
    return sum(1 for n in r["setups"].values() if len(n) > 1)

scenes = sorted(v1, key=lambda x: x)
rows = []
for sc in scenes:
    r1, r2 = v1[sc], v2[sc]
    rows.append(dict(
        scene=sc, shots=r1["shots"],
        v1s=len(r1["setups"]), v2s=len(r2["setups"]),
        d=r2["shots"] - 0,  # placeholder
        v1m=multis(r1), v2m=multis(r2),
        x1=bool(r1.get("crosscut")), x2=bool(r2.get("crosscut")),
        a2=r2.get("alternations", 0),
    ))

tot_v1 = sum(r["v1s"] for r in rows)
tot_v2 = sum(r["v2s"] for r in rows)
tot_v1m = sum(r["v1m"] for r in rows)
tot_v2m = sum(r["v2m"] for r in rows)
tot_shots = sum(r["shots"] for r in rows)

# biggest deltas
down = sorted([r for r in rows if r["v2s"] < r["v1s"]],
              key=lambda r: r["v1s"] - r["v2s"], reverse=True)
up = sorted([r for r in rows if r["v2s"] > r["v1s"]],
            key=lambda r: r["v2s"] - r["v1s"], reverse=True)
new_xcut = sorted([r["scene"] for r in rows if r["x2"] and not r["x1"]])
lost_xcut = sorted([r["scene"] for r in rows if r["x1"] and not r["x2"]])

L = []
L.append("# Setups v2 — continuity re-clustering (local VLM, relative grouping)")
L.append("")
L.append("Replaces v1's grayscale-SSIM first-frame clustering (setup-th=0.42) with")
L.append("semantic camera-setup grouping. Each scene's boundary stills are fed to")
L.append("qwen2.5-vl-32b (LM Studio, `--gpu 0.8 -c 8192`) which groups them into")
L.append("setups directly — same camera position + same background = same setup,")
L.append("pose/action ignored. Replaces the SSIM failure mode: v1 could not express")
L.append("\"same camera angle, different actor pose\", so dialogue scenes fragmented")
L.append("to ~1 setup per shot.")
L.append("")
L.append("## Summary")
L.append("")
L.append("- Shots: %d across %d scenes" % (tot_shots, len(rows)))
L.append("- Setups: %d (v1) -> %d (v2)  —  %d fewer (%.0f%%)" % (
    tot_v1, tot_v2, tot_v1 - tot_v2, 100.0 * (tot_v1 - tot_v2) / tot_v1))
L.append("- Multi-shot setups (recurrences correctly merged): %d -> %d  —  +%d" % (
    tot_v1m, tot_v2m, tot_v2m - tot_v1m))
L.append("- Cross-cut scenes: %d -> %d" % (
    sum(1 for r in rows if r["x1"]), sum(1 for r in rows if r["x2"])))
if new_xcut:
    L.append("- Newly flagged cross-cut: " + ", ".join(new_xcut))
if lost_xcut:
    L.append("- No longer flagged: " + ", ".join(lost_xcut))
L.append("")
L.append("## Per-scene comparison")
L.append("")
L.append("| Scene | Shots | v1 setups | v2 setups | d | v1 multi | v2 multi | alt | cross-cut |")
L.append("|---|---|---|---|---|---|---|---|---|")
for r in rows:
    d = r["v2s"] - r["v1s"]
    ds = ("+%d" % d) if d > 0 else ("%d" % d)
    x = ("new" if (r["x2"] and not r["x1"])
         else ("lost" if (r["x1"] and not r["x2"])
               else ("yes" if r["x2"] else "")))
    L.append("| %s | %d | %d | %d | %s | %d | %d | %d | %s |" % (
        r["scene"], r["shots"], r["v1s"], r["v2s"], ds,
        r["v1m"], r["v2m"], r["a2"], x))
L.append("")
L.append("## Biggest changes")
L.append("")
L.append("Most fragmentation fixed (v1 over-split -> v2 re-merged recurrences):")
L.append("")
for r in down[:12]:
    L.append("- %s: %d -> %d setups (%d shots; multi-shot %d -> %d)" % (
        r["scene"], r["v1s"], r["v2s"], r["shots"], r["v1m"], r["v2m"]))
L.append("")
L.append("Went up (gap/montage scenes where v1's SSIM over-merged distant frames;")
L.append("v2 splits them into more distinct backgrounds):")
L.append("")
for r in up:
    L.append("- %s: %d -> %d setups (%d shots; multi-shot %d -> %d)" % (
        r["scene"], r["v1s"], r["v2s"], r["shots"], r["v1m"], r["v2m"]))
L.append("")
L.append("## Known limitations (local-only)")
L.append("")
L.append("- The 32b merges SOME reverse angles and some distinct-but-similar")
L.append("  backgrounds (e.g. S02 rolls five cold backdrops into one setup). This is")
L.append("  the accepted cost of the local pass; SSIM and both local VLMs measurably")
L.append("  cannot split reverse angles — only a strong cloud VLM does (see the")
L.append("  vlm-image-labeling skill).")
L.append("- Partial-model-output salvage: where the 32b returned an incomplete")
L.append("  grouping, omitted shots are kept as singletons rather than dropped.")
L.append("- `edges` (chain/cut SSIM adjacency) are backfilled from v1 unchanged — that")
L.append("  signal was never the broken part.")
L.append("")
L.append("Generated from manifests/continuity.jsonl (v1) vs manifests/continuity_v2.jsonl (v2).")

out = ROOT / "reports" / "continuity_v2.md"
out.write_text("\n".join(L) + "\n", encoding="utf-8")
print("wrote", out)
print("totals: %d->%d setups, %d->%d multi" % (tot_v1, tot_v2, tot_v1m, tot_v2m))