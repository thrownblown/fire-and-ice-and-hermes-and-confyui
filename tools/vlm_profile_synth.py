#!/usr/bin/env python3
"""Aggregate the multi-lens VLM character ledger into per-character profiles.

Reads manifests/vlm_charpass.jsonl (or --ledger), groups ok rows by
char+lens+trait, applies deterministic majority vote (core.vlm_charpass
consensus), and writes:

    library/char/profiles/<CHAR>.json   machine profile
    library/char/profiles/<CHAR>.md     human sheet + prompt_block paragraph

Stable = share >= 0.6. No LLM, no network — pure deterministic aggregation.

    python tools/vlm_profile_synth.py --char TUTOR
    python tools/vlm_profile_synth.py --all
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.vlm_charpass import LENSES, consensus, is_nullish  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STABLE_SHARE = 0.6


def load_ledger(path):
    """Read a JSONL ledger, skipping malformed lines."""
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"[warn] skipping malformed ledger line: {line[:80]}", file=sys.stderr)
    return rows


def _item_key(obj):
    """Canonical identity of an objlist entry (its 'item' name, lowercased)."""
    v = obj.get("item") or obj.get("name") or json.dumps(obj, sort_keys=True)
    return str(v).strip().lower()


def _aggregate_list(lens_rows, key):
    """Frequency of each pooled string item across rows."""
    n_rows = len(lens_rows)
    counts, surface = {}, {}
    for r in lens_rows:
        val = r.get(key)
        if not isinstance(val, list):
            continue
        seen = set()
        for item in val:
            if not isinstance(item, str) or not item.strip() or is_nullish(item):
                continue
            k = item.strip().lower()
            if k in seen:
                continue
            seen.add(k)
            counts[k] = counts.get(k, 0) + 1
            surface.setdefault(k, item.strip())
    stable = sorted(k for k, c in counts.items() if n_rows and c / n_rows >= STABLE_SHARE)
    disputed = sorted(k for k, c in counts.items() if k not in set(stable))
    return {
        "kind": "list",
        "n_rows": n_rows,
        "stable_items": [surface[k] for k in stable],
        "disputed_items": [surface[k] for k in disputed],
        "counts": {surface[k]: counts[k] for k in sorted(counts)},
    }


def _aggregate_objlist(lens_rows, key):
    """Group objects by their 'item' name; per-item value disagreement kept."""
    n_rows = len(lens_rows)
    counts, surface, values = {}, {}, {}
    for r in lens_rows:
        val = r.get(key)
        if not isinstance(val, list):
            continue
        seen = set()
        for obj in val:
            if not isinstance(obj, dict):
                continue
            k = _item_key(obj)
            if k in seen:
                continue
            seen.add(k)
            counts[k] = counts.get(k, 0) + 1
            surface.setdefault(k, str(obj.get("item") or k))
            v = obj.get("color") or ", ".join(
                f"{kk}={obj[kk]}" for kk in sorted(obj) if kk != "item" and isinstance(obj[kk], str))
            values.setdefault(k, []).append(str(v))
    stable = sorted(k for k, c in counts.items() if n_rows and c / n_rows >= STABLE_SHARE)
    disputed = sorted(k for k, c in counts.items() if k not in set(stable))
    return {
        "kind": "objlist",
        "n_rows": n_rows,
        "stable_items": [surface[k] for k in stable],
        "disputed_items": [surface[k] for k in disputed],
        "detail": {surface[k]: {"n": counts[k], "values": values[k]} for k in sorted(counts)},
    }


def _aggregate_str(lens_rows, key):
    vals = [r[key] for r in lens_rows
            if isinstance(r.get(key), str) and r[key].strip() and not is_nullish(r[key])]
    c = consensus(vals)
    return {
        "kind": "str",
        "value": c["value"],
        "share": c["share"],
        "n": c["n"],
        "outliers": c["outliers"],
        "all_values": vals,
        "stable": bool(c["n"]) and c["share"] >= STABLE_SHARE,
    }


def synthesize(rows, char):
    """Build the deterministic profile dict for one character."""
    char_rows = [r for r in rows if r.get("char") == char]
    ok_rows = [r for r in char_rows if r.get("ok") and isinstance(r.get("json"), dict)]

    by_lens = {}
    for r in ok_rows:
        by_lens.setdefault(r["lens"], []).append(r["json"])

    lenses_out, stable, disputed, stable_map = {}, [], [], {}
    for lens in LENSES:                       # LENSES order, traits alphabetical
        if lens not in by_lens:
            continue
        lens_rows = by_lens[lens]
        schema = LENSES[lens]["schema"]
        traits = {}
        for key in sorted(schema):
            kind = schema[key]
            if kind == "str":
                agg = _aggregate_str(lens_rows, key)
                if agg["n"] and agg["stable"]:
                    stable.append(f"{lens}.{key}")
                    stable_map[(lens, key)] = agg["value"]
                elif agg["n"]:
                    disputed.append(f"{lens}.{key}")
            elif kind == "list":
                agg = _aggregate_list(lens_rows, key)
                for it in agg["stable_items"]:
                    stable.append(f"{lens}.{key}:{it}")
                for it in agg["disputed_items"]:
                    disputed.append(f"{lens}.{key}:{it}")
            elif kind == "objlist":
                agg = _aggregate_objlist(lens_rows, key)
                for it in agg["stable_items"]:
                    stable.append(f"{lens}.{key}:{it}")
                for it in agg["disputed_items"]:
                    disputed.append(f"{lens}.{key}:{it}")
            else:                              # unknown schema kind — keep raw
                agg = {"kind": kind, "value": None}
            traits[key] = agg
        lenses_out[lens] = traits

    return {
        "char": char,
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rows": {"total": len(char_rows), "ok": len(ok_rows)},
        "lenses": lenses_out,
        "stable": sorted(stable),
        "disputed": sorted(disputed),
        "prompt_block": compose_prompt_block(stable_map, lenses_out),
    }


def compose_prompt_block(stable_map, lenses_out):
    """Deterministic composed description for Krea 2 stills prompts.

    Only stable string traits and stable list/objlist items are used; a
    disputed or single-answer trait never enters the block.
    """
    g = lambda lens, trait: stable_map.get((lens, trait))  # noqa: E731
    frags = []

    subj = " ".join(x for x in [g("physique", "age_range"), g("physique", "sex")] if x)
    if subj:
        frags.append(subj)
    if g("physique", "build"):
        frags.append(f"{g('physique', 'build')} build")
    if g("physique", "height_impression"):
        frags.append(f"{g('physique', 'height_impression')} height impression")
    if g("physique", "skin_neutral_light"):
        frags.append(f"{g('physique', 'skin_neutral_light')} skin")

    hair = " ".join(x for x in [g("hair", "color"), g("hair", "length"),
                                g("hair", "texture"), g("hair", "style")] if x)
    if hair:
        frags.append(f"{hair} hair")
    if g("face", "face_shape"):
        frags.append(f"{g('face', 'face_shape')} face")
    eyes = g("face", "eyes") or g("colors", "eyes")
    if eyes:
        frags.append(f"{eyes} eyes")

    gp, gs = g("colors", "garment_primary"), g("colors", "garment_secondary")
    if gp and gs:
        frags.append(f"dressed in {gp} and {gs}")
    elif gp:
        frags.append(f"dressed in {gp}")

    for lens, key, verb in (("wardrobe", "garments", "wearing"),
                            ("props", "items", "carrying"),
                            ("props", "weapons", "armed with")):
        agg = lenses_out.get(lens, {}).get(key)
        if agg and agg.get("stable_items"):
            frags.append(f"{verb} " + ", ".join(agg["stable_items"]))

    sig = lenses_out.get("signature", {}).get("memorable_traits")
    if sig and sig.get("stable_items"):
        frags.append("memorable for " + ", ".join(sig["stable_items"]))
    if g("signature", "unmistakable_because"):
        frags.append(f"unmistakable: {g('signature', 'unmistakable_because')}")

    if not frags:
        return ""
    return ", ".join(frags) + "."


def render_md(prof):
    lines = [f"# VLM profile — {prof['char']}",
             f"generated {prof['generated']} · rows: {prof['rows']['ok']} ok of {prof['rows']['total']} · model: multi-lens VLM pass",
             "",
             "## Stable traits"]
    any_stable = False
    for lens in prof["lenses"]:
        for trait in sorted(prof["lenses"][lens]):
            agg = prof["lenses"][lens][trait]
            if agg["kind"] == "str" and agg["stable"]:
                lines.append(f"- {lens}.{trait}: {agg['value']} ({agg['n'] * agg['share']:.0f}/{agg['n']})")
                any_stable = True
            elif agg["kind"] in ("list", "objlist") and agg.get("stable_items"):
                lines.append(f"- {lens}.{trait}: " + ", ".join(agg["stable_items"]))
                any_stable = True
    if not any_stable:
        lines.append("- (none)")

    lines += ["", "## Disputed traits"]
    any_disputed = False
    for lens in prof["lenses"]:
        for trait in sorted(prof["lenses"][lens]):
            agg = prof["lenses"][lens][trait]
            if agg["kind"] == "str" and agg["n"] and not agg["stable"]:
                vals = ", ".join(sorted(set(v.lower() for v in agg["all_values"])))
                lines.append(f"- {lens}.{trait}: {vals} (share {agg['share']:.2f})")
                any_disputed = True
            elif agg["kind"] in ("list", "objlist") and agg.get("disputed_items"):
                lines.append(f"- {lens}.{trait}: " + ", ".join(agg["disputed_items"]))
                any_disputed = True
    if not any_disputed:
        lines.append("- (none)")

    lines += ["", "## Prompt block", prof["prompt_block"] or "(no stable traits to compose)", ""]
    return "\n".join(lines)


def run_synth(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--char", action="append", default=None, help="character(s) in the ledger")
    ap.add_argument("--all", action="store_true", help="every character in the ledger")
    ap.add_argument("--ledger", default=None, help="ledger path (default: manifests/vlm_charpass.jsonl)")
    ap.add_argument("--root", default=ROOT)
    args = ap.parse_args(argv)

    ledger_path = args.ledger or os.path.join(args.root, "manifests", "vlm_charpass.jsonl")
    rows = load_ledger(ledger_path)
    if not rows:
        print(f"ledger empty or missing: {ledger_path}", file=sys.stderr)
        return 2

    if args.all:
        chars = sorted({r.get("char") for r in rows if r.get("char")})
    elif args.char:
        have = {r.get("char") for r in rows}
        missing = [c for c in args.char if c not in have]
        if missing:
            print(f"not in ledger: {', '.join(missing)}", file=sys.stderr)
            return 2
        chars = list(dict.fromkeys(args.char))
    else:
        print("select --char NAME (repeatable) or --all", file=sys.stderr)
        return 2

    outdir = os.path.join(args.root, "library", "char", "profiles")
    os.makedirs(outdir, exist_ok=True)
    for char in chars:
        prof = synthesize(rows, char)
        pj = os.path.join(outdir, f"{char}.json")
        pm = os.path.join(outdir, f"{char}.md")
        with open(pj, "w", encoding="utf-8") as f:
            json.dump(prof, f, indent=1, ensure_ascii=False)
        with open(pm, "w", encoding="utf-8") as f:
            f.write(render_md(prof))
        print(f"[profile] {char}: {prof['rows']['ok']} ok rows, "
              f"{len(prof['stable'])} stable / {len(prof['disputed'])} disputed traits -> "
              f"{pj.replace(os.sep, '/')}")
    return 0


def main():
    sys.exit(run_synth(sys.argv[1:]))


if __name__ == "__main__":
    main()
