#!/usr/bin/env python
"""Prompt editor STAGE — the semantic half, for the six-field reference-video prompts.

`tools/prompt_check.py` enforces what is mechanical. This runs the LLM editor
(`core/prompt_editor_system.md`) over what is not: prohibitions to rewrite as descriptions,
contradictions to resolve by deletion, references to bind, speaker order, and register.

It is MODE-AWARE, because the pipeline will mix modes for the final film:

    ref2v+audio+sheet+plate            audio + still character ref + scene plate   <- current run
    ref2v+audio+sheet
    fflf2v+audio+sheet+plate           first+last frame anchors alongside refs
    ref2v+audio+video+sheet+plate      a reference VIDEO plus stills
    fl2va+stills                       the older three-field shape

The mode is an INPUT, not a guess: it decides the grammar to emit and tells the editor which
reference labels (<Picture N>, <Video N>) are legitimately in play.

What the editor is given, per chunk: the mode, the refs actually attached (from the graph the take
rendered), the authored blocking, the ledger row (per-shot people counts, speakers, shot list), the
dialogue lines, the mechanically-repaired prompt, and the list of red flags found in it.

Output goes to a SEPARATE directory and is never written over a take's own prompt: a prompt file is
the provenance of the take that rendered with it.

    .venv/Scripts/python.exe tools/prompt_editor.py --chunk S05-c01 --dry-run
    .venv/Scripts/python.exe tools/prompt_editor.py --chunk S05-c01
    .venv/Scripts/python.exe tools/prompt_editor.py --scene S05 --limit 5
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"E:/FNI")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "runs"))       # build_technicolor_audio_only lives here
from core import gf_client as gf            # noqa: E402
import prompt_check as pc                   # noqa: E402  (the mechanical pass)

RUN_DIR = ROOT / "runs" / "T0016_s05_technicolor-audio-only-ref2va"
GRAPHS = RUN_DIR / "graphs"
EDITED = RUN_DIR / "prompts_edited"
CHUNKS = ROOT / "fullrun" / "chunks.jsonl"
BLOCKING = ROOT / "manifests" / "blocking.json"
SYSTEM_PROMPT = ROOT / "core" / "prompt_editor_system.md"
LEDGER = ROOT / "runs" / "prompt_editor.jsonl"

MODES = {
    "ref2v+audio+sheet+plate":        {"grammar": "ref2v6", "refs": ["Picture"], "audio": True},
    "ref2v+audio+sheet":              {"grammar": "ref2v6", "refs": ["Picture"], "audio": True},
    "fflf2v+audio+sheet+plate":       {"grammar": "ref2v6", "refs": ["Picture"], "audio": True},
    "ref2v+audio+video+sheet+plate":  {"grammar": "ref2v6", "refs": ["Picture", "Video"], "audio": True},
    "fl2va+stills":                   {"grammar": "3field", "refs": ["Picture"], "audio": False},
}
DEFAULT_MODE = "ref2v+audio+sheet+plate"
REWRITER = "llama3.3-70b-chat-xlarge"      # goldfishbowl alias; the strongest juror-rewriter
MAX_TOKENS = 6144                          # never below 2048 on goldfishbowl (thinking budget)


def load_rows() -> dict:
    out = {}
    for l in CHUNKS.read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            out[r["chunk_id"]] = r
    return out


def newest_graph(chunk: str) -> Path | None:
    cands = sorted(GRAPHS.glob(f"{chunk}_audioOnly_t*.json"), key=lambda p: p.stat().st_mtime)
    return cands[-1] if cands else None


def prompt_from_graph(gpath: Path) -> str:
    return json.loads(gpath.read_text(encoding="utf-8"))["138"]["inputs"]["value"]


def blocking_for(chunk: str) -> str:
    if not BLOCKING.exists():
        return ""
    b = json.loads(BLOCKING.read_text(encoding="utf-8")).get(chunk)
    if not b:
        return ""
    if isinstance(b, dict):
        return " ".join(str(b.get(k, "")) for k in ("blocking", "text", "description")).strip()
    return str(b)


def dialogue_lines(row: dict, chunk: str) -> list[str]:
    """The dialogue text the take was rendered with, from the graph the prompt itself came from."""
    return [m.group(2).strip() for m in pc.D_RE.finditer(row.get("_prompt", ""))] \
        if row.get("_prompt") else []


def user_message(chunk: str, mode: str, refs: list[str], row: dict, block: str,
                 prompt: str, flags: list[str]) -> str:
    pcounts = row.get("people_count") or []
    return f"""MODE: {mode}
GRAMMAR TO EMIT: {MODES[mode]['grammar']}
REFERENCES ACTUALLY ATTACHED (in <Picture N> order): {', '.join(refs) or 'none'}

LEDGER FACTS for this chunk (authoritative — do not invent beyond them)
  shot numbers            : {row.get('shot_nums')}
  people per source shot  : {pcounts}
  on-screen cast (stamped): {row.get('stamped_names')}
  dialogue speakers       : {row.get('speakers')}

AUTHORED BLOCKING (the ground truth for who is in frame and what they do):
{block or '(none authored)'}

RED FLAGS found mechanically in the prompt below (address every one):
{chr(10).join('  - ' + f for f in flags) or '  - (none)'}

PROMPT TO EDIT:
{prompt}

Return the corrected prompt only, in the six-field grammar, with no commentary."""


def validate(edited: str, original: str, row: dict) -> list[str]:
    """Mechanical contract on the editor's output. Anything here means we keep the input."""
    bad = []
    for f in pc.FIELDS:
        if f not in edited:
            bad.append("missing field %s" % f)
    idx = [edited.find(f) for f in pc.FIELDS]
    if all(i >= 0 for i in idx) and idx != sorted(idx):
        bad.append("fields out of order")
    if edited.count("<d>") != edited.count("</d>"):
        bad.append("unbalanced <d> tags")
    if "<Video" in edited and "Video" not in MODES[DEFAULT_MODE]["refs"]:
        bad.append("references <Video N> but no video ref is attached")
    # every dialogue line from the original must survive verbatim
    for lang, body in pc.D_RE.findall(original):
        if body.strip() and body.strip() not in edited:
            bad.append("dropped dialogue: %r" % body.strip()[:48])
    # every attached picture label must still be defined
    for m in re.finditer(r"<Picture (\d+)>", original):
        if m.group(0) not in edited:
            bad.append("dropped reference %s" % m.group(0))
    if len(edited) < 0.5 * len(original):
        bad.append("output is less than half the input length")
    return bad


def edit_one(chunk: str, row: dict, mode: str, model: str, dry: bool) -> dict:
    g = newest_graph(chunk)
    if not g:
        return {"chunk": chunk, "state": "no-graph"}
    original = row["_prompt"] = prompt_from_graph(g)
    refs = pc.attached_images(chunk)
    flags, repaired = pc.check_one(chunk, original, row)
    block = blocking_for(chunk)
    if dry:
        return {"chunk": chunk, "state": "dry", "flags": flags, "refs": refs,
                "repaired_chars": len(repaired), "original_chars": len(original)}
    # a prompt with nothing to fix is not worth a 70B call
    semantic = [f for f in flags if f.startswith("F:")]
    if not semantic:
        out, state = repaired, "repaired-only"
    else:
        try:
            out = gf.chat(model, user_message(chunk, mode, refs, row, block, repaired, flags),
                          system=SYSTEM_PROMPT.read_text(encoding="utf-8"),
                          max_tokens=MAX_TOKENS, temperature=0.15, timeout=900)
            state = "edited"
        except Exception as e:  # noqa: BLE001
            out, state = repaired, "llm-error: %s" % str(e)[:60]
    bad = validate(out, original, row)
    if bad and state == "edited":
        try:  # one retry with the failures fed back
            out2 = gf.chat(model, user_message(chunk, mode, refs, row, block, repaired, flags)
                           + "\n\nYOUR PREVIOUS ATTEMPT FAILED THESE CHECKS: " + "; ".join(bad)
                           + "\nReturn a corrected prompt that passes them.",
                           system=SYSTEM_PROMPT.read_text(encoding="utf-8"),
                           max_tokens=MAX_TOKENS, temperature=0.15, timeout=900)
            if not validate(out2, original, row):
                out, bad, state = out2, [], "edited-retry"
        except Exception:  # noqa: BLE001
            pass
    if bad:
        out, state = repaired, "kept-mechanical (%s)" % "; ".join(bad[:2])
    EDITED.mkdir(parents=True, exist_ok=True)
    (EDITED / f"{chunk}.txt").write_text(out, encoding="utf-8")
    return {"chunk": chunk, "state": state, "flags": flags, "refs": refs,
            "chars": [len(original), len(out)], "graph": g.name}


def main() -> None:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--chunk", default="")
    ap.add_argument("--scene", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--mode", default=DEFAULT_MODE, choices=sorted(MODES))
    ap.add_argument("--model", default=REWRITER)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--plated-only", action="store_true",
                    help="only chunks whose scene resolves to a SETTLED plate (the next pass's scope)")
    args = ap.parse_args()

    rows = load_rows()
    ids = sorted(rows)
    if args.plated_only:
        import build_technicolor_audio_only as B      # noqa: E402  (has_plate reads scene_locations.json)
        ids = [c for c in ids if B.has_plate(rows[c].get("scene", ""))]
    if args.chunk:
        ids = [args.chunk]
    elif args.scene:
        ids = [c for c in ids if rows[c].get("scene") == args.scene]
    if args.limit:
        ids = ids[:args.limit]

    print("mode %s | model %s | %d chunk(s)%s"
          % (args.mode, args.model, len(ids), "  [DRY RUN]" if args.dry_run else ""))
    fh = LEDGER.open("a", encoding="utf-8")
    tally: dict[str, int] = {}
    try:
        for cid in ids:
            r = edit_one(cid, rows[cid], args.mode, args.model, args.dry_run)
            tally[r["state"].split(" ")[0]] = tally.get(r["state"].split(" ")[0], 0) + 1
            print("  %-10s %-22s flags=%d refs=%s %s"
                  % (cid, r["state"], len(r.get("flags", [])), len(r.get("refs", [])),
                     r.get("chars", "")))
            fh.write(json.dumps(r) + "\n")
    finally:
        fh.close()
    print("\ntally:", tally, "| ledger:", LEDGER)


if __name__ == "__main__":
    main()
