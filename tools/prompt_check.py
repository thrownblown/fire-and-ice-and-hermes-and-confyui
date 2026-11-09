#!/usr/bin/env python
"""Deterministic prompt checker / repairer for the six-field ref2v prompts.

The LLM editor (core/prompt_editor_system.md) judges meaning; this tool enforces the rules that
are mechanical, so the expensive pass only sees prompts that are already structurally sound. It
exists because three defects were measured across the yolo prompts on 2026-11-06:

  * 87 of 258 carried the GROUP crowd clause ("This is a gathering scene with a crowd present")
    while their own blocking describes one or two people — the prompt contradicted itself, and a
    contradiction renders as a UNION (the model adds a crowd rather than choosing);
  * 221 of 258 said "the figures" — an unbound reference the model is free to invent occupants
    for;
  * 5 of 258 declared that the attached sheet is ONE person from several angles, so the model
    read the sheet's panels as several similar people.

Checks (R = repairable in place, F = flag only):

  R skeleton      six fields present, in order, spelled right
  R crowd-vs-blocking   crowd clause present while the ledger says <=2 people
  R unbound refs  "the figures" / "the characters" with no <Subject N>
  R sheet line    a sheet is attached but the prompt never says it is one person
  R reference-generation   summary claims keyframe completion instead of reference generation
  F negations     prohibition density (rewriting these is the LLM editor's job)
  F adverbs       "slightly", "a little", "subtle" — invisible to the model, pure noise
  F speakers      (S#) must be first-speaking order, max S2, never a fake S3
  F dialogue      <d>[Language] …</d> balanced, <=130 chars/line, <=200/clip

    .venv/Scripts/python.exe tools/prompt_check.py --report            # all prompts
    .venv/Scripts/python.exe tools/prompt_check.py --report --chunk S05-c01
    .venv/Scripts/python.exe tools/prompt_check.py --apply             # rewrite in place (--out-dir to be safe)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"E:/FNI")
sys.path.insert(0, str(ROOT))
RUN_DIR = ROOT / "runs" / "T0016_s05_technicolor-audio-only-ref2va"
PROMPTS = RUN_DIR / "prompts"
GRAPHS = RUN_DIR / "graphs"
CHUNKS = ROOT / "fullrun" / "chunks.jsonl"
LEDGER = ROOT / "runs" / "prompt_check.jsonl"

FIELDS = ["subject_definitions:", "summary:", "retention_analysis:",
          "detailed_description:", "overall_soundscape:"]
# `non_diegetic_music` was removed from the contract (Alex, 2026-11-07: "the non diegetic audio needs to
# go, we are using the audio from the movie"). Requiring it here is what made the editor re-insert the
# field as "No non-diegetic music is present" — itself a prohibition, i.e. exactly the noise the editor
# exists to remove. Mirrors runs/build_technicolor_audio_only.py.
NARRATION_RE = re.compile(r"\bin (the )?(first|second|third|fourth|last|next) (frame|shot)\b|"
                          r"\bthe (first|second|third) frame (shows|is)\b|\bin total,?\b", re.I)
# An "empty shot" written as a negation: "[Shot 2] The frame is empty of people." Same failure class as
# the source narration (it asks for the absence of content), one level down.
EMPTY_RE = re.compile(r"\b(frame|shot) is (empty|devoid)\b|\bempty of people\b|\bno one is in (this|the)\b",
                      re.I)

# Mirrors build_technicolor_audio_only.py; asserted below so the two cannot drift silently.
GROUP_CLAUSE = "This is a gathering scene with a crowd present."
GLOBAL_CLAUSE = ("ONLY the named characters are present in the shot — there are no other people, "
                 "no crowd, no background figures and no extras at any point.")
SHEET_LINE = ("{pic} is a reference sheet of {subj}, the same person shown from several angles. "
              "Do not treat the panels as different people.")

NEG_RE = re.compile(r"\b(no|not|never|without|nobody|nothing|avoid)\b", re.I)
ADV_RE = re.compile(r"\b(slightly|a little|a bit|subtle|subtly|very|softly)\b", re.I)
D_RE = re.compile(r"<d>\s*\[([A-Za-z ]+)\]\s*([^<]*)</d>")


def ledger_rows() -> dict:
    out = {}
    if CHUNKS.exists():
        for l in CHUNKS.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                out[r["chunk_id"]] = r
    return out


def attached_images(chunk: str) -> list[str]:
    """LoadImage filenames for the newest take's graph, in node-id order (= <Picture N> order)."""
    if not GRAPHS.exists():
        return []
    cands = sorted(GRAPHS.glob(f"{chunk}_audioOnly_t*.json"),
                   key=lambda p: ("_t02" in p.name, p.stat().st_mtime))
    if not cands:
        return []
    g = json.loads(cands[-1].read_text(encoding="utf-8"))
    nodes = sorted(g.items(), key=lambda kv: int(kv[0]) if str(kv[0]).isdigit() else 0)
    return [n["inputs"].get("image", "") for _, n in nodes
            if n.get("class_type") == "LoadImage" and n.get("inputs", {}).get("image")]


def check_one(chunk: str, text: str, row: dict) -> tuple[list[str], str]:
    """Return (issues, repaired_text). Issues carry a leading 'F:' for flag-only."""
    issues: list[str] = []
    out = text
    subjects = [n for n in dict.fromkeys(list(row.get("speakers") or []) +
                                         list(row.get("stamped_names") or []))]

    # --- skeleton ------------------------------------------------------------------------
    idx = [out.find(f) for f in FIELDS]
    if any(i < 0 for i in idx):
        issues.append("R:skeleton missing field(s): %s"
                      % ", ".join(f for f, i in zip(FIELDS, idx) if i < 0))
    elif idx != sorted(idx):
        issues.append("R:skeleton fields out of order")

    # --- crowd clause vs the blocking ----------------------------------------------------
    pcounts = [int(c) for c in (row.get("people_count") or []) if str(c).strip().isdigit()]
    if GROUP_CLAUSE in out and pcounts and max(pcounts) <= 2:
        out = out.replace(GROUP_CLAUSE + " ", "").replace(GROUP_CLAUSE, "")
        issues.append("R:crowd-clause removed (ledger max people = %d)" % max(pcounts))
    elif GROUP_CLAUSE in out and not pcounts:
        issues.append("F:crowd clause but no people_count in the ledger — cannot verify")

    # --- unbound references --------------------------------------------------------------
    generic = re.findall(r"\bthe figures\b|\bthe characters\b(?!\s*\()", out, re.I)
    if generic:
        if len(subjects) == 1:
            out = re.sub(r"\bthe figures\b", "<Subject 1>", out, flags=re.I)
            out = re.sub(r"\bthe characters\b(?!\s*\()", "<Subject 1>", out, flags=re.I)
            issues.append("R:unbound references bound to <Subject 1> (%d)" % len(generic))
        elif subjects:
            bound = "the characters (" + " and ".join("<Subject %d>" % i
                                                      for i in range(1, len(subjects) + 1)) + ")"
            out = re.sub(r"\bthe figures\b|\bthe characters\b(?!\s*\()", bound, out, flags=re.I)
            issues.append("R:unbound references bound to the %d subjects (%d)" % (len(subjects), len(generic)))
        else:
            issues.append("F:unbound references and no subjects in the ledger")

    # --- sheet declaration ---------------------------------------------------------------
    imgs = attached_images(chunk)
    sheet_idx = [i + 1 for i, name in enumerate(imgs) if "_sheet" in name.lower()]
    if sheet_idx and "same person" not in out:
        added = 0
        for i in sheet_idx:
            line = SHEET_LINE.format(pic="<Picture %d>" % i, subj="<Subject %d>" % min(i, max(1, len(subjects))))
            # insert right after that subject's definition line
            pat = re.compile(r"(<Subject %d> is [^\n]*?shown in <Picture %d>\.)" % (min(i, max(1, len(subjects))), i))
            if pat.search(out):
                out = pat.sub(lambda m: m.group(1) + " " + line, out, count=1)
                added += 1
        if added:
            issues.append("R:sheet declared as one person (%d line(s))" % added)
        else:
            issues.append("F:sheet attached but its definition line could not be located")
    elif sheet_idx:
        pass  # already declared
    elif "same person" in out:
        issues.append("F:sheet line present but no sheet attached")

    # --- reference generation vs keyframe completion -------------------------------------
    if "keyframe completion" in out.lower():
        out = re.sub(r"\[\s*keyframe completion\s*\]", "[reference generation]", out, flags=re.I)
        issues.append("R:summary said keyframe completion -> reference generation")
    elif "[reference generation]" not in out.lower() and "summary:" in out:
        issues.append("F:summary does not state [reference generation]")

    # --- flags only (semantic; the LLM editor rewrites these) ----------------------------
    negs = len(NEG_RE.findall(out))
    if negs >= 6:
        issues.append("F:negations x%d — prohibitions are ignored; describe the frame instead" % negs)
    # Frame-by-frame narration of the SOURCE clip ("In the first frame…", "In total, one main character…").
    # Alex 2026-11-07: it "serves no value to the video model … it only confuses the model" — the graph
    # already carries the reference, and "the second frame shows no people" instructs an empty shot.
    narr = len(NARRATION_RE.findall(out))
    if narr:
        issues.append("F:source-narration x%d — the blocking is a reading of the ORIGINAL clip; "
                      "write the per-shot lines instead of pasting it" % narr)
    empty = len(EMPTY_RE.findall(out))
    if empty:
        issues.append("F:empty-frame x%d — 'the frame is empty of people' asks for absence; describe "
                      "what fills the frame" % empty)
    advs = ADV_RE.findall(out)
    if advs:
        issues.append("F:degree adverbs x%d %s" % (len(advs), sorted(set(a.lower() for a in advs))[:4]))
    tags = re.findall(r"\((S\d)\)", out)
    if tags and tags != sorted(set(tags)):
        issues.append("F:(S#) tags out of first-speaking order: %s" % tags[:6])
    if any(t not in ("S1", "S2") for t in tags):
        issues.append("F:(S#) beyond S2 — split the shot instead of faking a speaker")
    lines = D_RE.findall(out)
    if len(lines) > 2:
        issues.append("F:%d speakers in dialogue (max 2)" % len(lines))
    for lang, body in lines:
        if len(body) > 130:
            issues.append("F:dialogue line >130 chars (%d)" % len(body))
    if sum(len(b) for _, b in lines) > 200:
        issues.append("F:total dialogue >200 chars")
    if out.count("<d>") != out.count("</d>"):
        issues.append("R:skeleton <d> tags unbalanced")

    return issues, out


def main() -> None:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--report", action="store_true", help="check only (default)")
    ap.add_argument("--apply", action="store_true", help="write repaired prompts")
    ap.add_argument("--out-dir", default="", help="with --apply: write here instead of in place")
    ap.add_argument("--chunk", default="", help="one chunk id")
    args = ap.parse_args()

    # keep the mirrored clause honest
    builder = (ROOT / "runs" / "build_technicolor_audio_only.py").read_text(encoding="utf-8")
    if GROUP_CLAUSE not in builder:
        print("WARNING: the crowd clause in this tool no longer matches the builder's text")

    rows = ledger_rows()
    files = sorted(PROMPTS.glob("*.txt"))
    if args.chunk:
        files = [f for f in files if f.stem == args.chunk]

    counts: dict[str, int] = {}
    repaired = 0
    fh = LEDGER.open("a", encoding="utf-8")
    for p in files:
        cid = p.stem
        text = p.read_text(encoding="utf-8")
        issues, fixed = check_one(cid, text, rows.get(cid, {}))
        for i in issues:
            counts[i.split(":")[0] + ":" + i.split(":")[1].split()[0]] = \
                counts.get(i.split(":")[0] + ":" + i.split(":")[1].split()[0], 0) + 1
        if issues:
            print("%-10s %s" % (cid, "; ".join(issues[:6])))
        if args.apply and fixed != text:
            dst = (Path(args.out_dir) / p.name) if args.out_dir else p
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(fixed, encoding="utf-8")
            repaired += 1
        fh.write(json.dumps({"chunk": cid, "issues": issues}) + "\n")
    fh.close()

    print("\n%d prompt(s) checked | %d repaired%s" % (len(files), repaired,
          "" if not args.apply else " -> %s" % (args.out_dir or "in place")))
    for k in sorted(counts, key=lambda k: -counts[k]):
        print("   %-42s %d" % (k, counts[k]))


if __name__ == "__main__":
    main()
