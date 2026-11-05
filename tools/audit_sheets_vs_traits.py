# -*- coding: utf-8 -*-
"""Audit a character sheet against its canonical traits — one 32B VLM call per character.

Why: the audio-led batch fed H3 13 character sheets. `TEEGRA_sheet_t01_00001_.png` — the
single most-used ref in the run (137 of 276 graphs) — shows a BROWN leather two-piece with
gold studs, while `refs/characters/TEEGRA/traits.txt` says "lightweight purple two-piece
costume" and the 1983 source frames (`id_TEEGRA.jpg`, `shot_00270_f00000.jpg`) are read by the
same VLM as purple/lavender. The H3 prompt carries the traits text, so the model received TWO
costumes for one character — and the invented background figures in the G03 renders all wear
the sheet's brown leather. A mis-costumed sheet is not cosmetic: it is a generator of wrong
people, and it silently conditions every chunk that lists that character.

So this checks, per character: does the SHEET show what traits.txt says (costume colour +
material first, then hair/eyes/skin), and is there any SECOND figure or second costume on the
sheet that a model could clone.

    .venv/Scripts/python.exe tools/audit_sheets_vs_traits.py                # all chars used by the batch
    .venv/Scripts/python.exe tools/audit_sheets_vs_traits.py --chars TEEGRA,NEKRON
    .venv/Scripts/python.exe tools/audit_sheets_vs_traits.py --limit 1      # smoke

Ledger: manifests/sheet_traits_audit.jsonl (resumable per character). Model id resolved from
the LIVE `GET /v1/models`; images downscaled to <=1024 px because the 32B serves 32,768 tokens
of context and an image costs context too. One model, sequential — goldfishbowl is a consumer
box where a model switch costs minutes, so this never touches a second id.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT))

from core import gf_client  # noqa: E402

CHARS_DIR = ROOT / "refs" / "characters"
LEDGER = ROOT / "manifests" / "sheet_traits_audit.jsonl"
SCALED = ROOT / "runs" / "yolo_diag" / "sheet_audit_scaled"

# the 13 sheets the audio-led batch consumed, most-used first
BATCH_CHARS = ["TEEGRA", "LARN", "NEKRON", "TUTOR", "JAROL", "TARO", "DARKWOLF",
               "ROLIEL", "JULIANA", "SPIRIT", "ENVOY", "SUBHUMAN CAPTAIN", "SUBHUMAN"]

PROMPT = """You are auditing an AI character reference sheet for a film remake.

CANONICAL TRAITS (the authoritative description the film's prompts use): {traits}

Answer precisely, in this order, and quote what you actually SEE on the sheet:
1. COSTUME: colour and material of the garment(s) as drawn, and any ornaments. Then say MATCH or
   MISMATCH against the canonical traits, naming the specific difference.
2. HAIR / EYES / SKIN against the canonical traits: MATCH or MISMATCH each, with the reason.
3. FIGURES: how many distinct human figures are on the sheet? Is there a SECOND character, a
   variant, or a second costume design a model could copy onto other people?
4. BACKGROUND: what is behind the figure(s) (plain backdrop, or scenery/props)?
5. BOTTOM LINE: one line - does this sheet actually show the canonical character, yes or no, and
   the single most important thing to fix if not."""


def pick_model(want: str | None = None) -> str:
    if want:
        return want
    ids = [m.get("id") for m in gf_client.models() if m.get("id")]
    for pref in ("llama-cpp/qwen3-vl-32b", "qwen3-vl-32b"):
        for i in ids:
            if i.startswith(pref):
                return i
    raise SystemExit(f"no 32B VLM id live; ids: {ids}")


def prep(src: Path, max_px: int = 1024) -> Path:
    out = SCALED / f"{src.stem}_{max_px}.jpg"
    if out.exists() and out.stat().st_size > 0:
        return out
    SCALED.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-i", str(src),
                    "-vf", f"scale='min({max_px},iw)':-2", "-q:v", "4", "-y", str(out)], check=True)
    return out


def sheet_for(name: str, pattern: str = "{name}_sheet_t*.png") -> Path | None:
    """Newest take matching the pattern — NOT the alphabetically first.

    Measured 2026-11-04: SUBHUMAN already had a t02 sheet from 2026-10-24, so a name-sorted glob
    returned that old file instead of the fresh re-render (`..._t02_00002_`). Within a generation the
    newest take is the one that reflects the current recipe.
    """
    hits = sorted((CHARS_DIR / name).glob(pattern.format(name=name)),
                  key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[0] if hits else None


def traits_for(name: str) -> str:
    p = CHARS_DIR / name / "traits.txt"
    if not p.exists():
        return ""
    return " ".join(p.read_text(encoding="utf-8").split())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chars", default=",".join(BATCH_CHARS))
    ap.add_argument("--model", default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--redo", default="", help="comma-separated chars whose existing ledger row "
                                               "should be dropped and re-audited (use after a "
                                               "character GAINS a traits.txt: its NO_CANON row is "
                                               "otherwise resumed forever)")
    ap.add_argument("--sheet-pattern", default="{name}_sheet_t*.png",
                    help="which sheet generation to audit, e.g. '{name}_sheet_t02*.png' to judge a "
                         "new re-render instead of the original")
    ap.add_argument("--ledger", default="", help="alternate ledger path (keep generations apart)")
    args = ap.parse_args()

    global LEDGER  # noqa: PLW0603 — the tool is a script, one process, one target
    if args.ledger:
        LEDGER = Path(args.ledger)

    chars = [c.strip() for c in args.chars.split(",") if c.strip()]
    if args.redo:
        drop = {c.strip() for c in args.redo.split(",") if c.strip()}
        if LEDGER.exists():
            rows = [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
            keep = [r for r in rows if r.get("char") not in drop]
            LEDGER.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in keep),
                              encoding="utf-8")
            print(f"re-do: dropped {len(rows) - len(keep)} row(s) for {sorted(drop)}", flush=True)
    model = args.model  # resolved lazily: a NO_CANON row needs no model at all
    done = set()
    if LEDGER.exists():
        for line in LEDGER.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["char"])

    todo = [c for c in chars if c not in done and sheet_for(c, args.sheet_pattern)]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(todo)} sheet(s) to audit, {len(done)} done", flush=True)

    for name in todo:
        sheet = sheet_for(name, args.sheet_pattern)
        assert sheet is not None
        traits = traits_for(name)
        # A character with no canon file CANNOT be audited against canon — and asking the VLM
        # anyway produced fabricated verdicts (given an EMPTY traits.txt it asserted "the canonical
        # costume is maroon"). Record the GAP; that is the finding, not a verdict.
        if not traits:
            with LEDGER.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"char": name, "sheet": sheet.name, "traits": "",
                                     "model": None, "verdict_kw": "NO_CANON",
                                     "raw": f"not auditable: no non-empty refs/characters/{name}/traits.txt"},
                                    ensure_ascii=False) + "\n")
            print(f"  {name}: NO_CANON (no non-empty traits.txt — the gap IS the finding)", flush=True)
            continue
        if not model:
            model = pick_model(None)
        try:
            resp = gf_client.chat(model, PROMPT.format(traits=traits), images=[str(prep(sheet))],
                                  max_tokens=1200)
        except Exception as e:  # noqa: BLE001 — transport error is not a verdict
            print(f"  {name}: VLM ERROR {type(e).__name__}: {str(e)[:160]} (nothing written)", flush=True)
            continue
        verdict = "MISMATCH" if re.search(r"mismatch", resp, re.I) else "match?"
        with LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"char": name, "sheet": sheet.name, "traits": traits,
                                 "model": model, "verdict_kw": verdict, "raw": resp},
                                ensure_ascii=False) + "\n")
        print(f"  {name}: {verdict} | {' '.join(resp.split())[:180]}", flush=True)
    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
