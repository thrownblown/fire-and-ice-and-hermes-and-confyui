# -*- coding: utf-8 -*-
"""Prompt jury — a panel of goldfishbowl models reviews every queued H3 prompt
like a PR review, BEFORE the next YOLO run burns GPU on them.

Alex (2026-10-28): "refine the prompts a lot more for the next yolo — there is
a lot of misalignment in the blocking and descriptions from the plot, and none
of the dialog. Build a pipeline to use a jury of the models on goldfishbowl to
review the prompts; the reviewer has the official prompting guides with correct
syntax and the community tips in its context."

Per chunk the juror sees: docs/prompt-jury-context.md (official speaker/dialog
syntax + community/house rules + output contract), the verbatim prompt, and the
ground truth (script lines from script/dialogue-timeline.tsv, the VLM blocking
draft, the ledger row). 3 jurors vote; a judge model merges their issues into a
final verdict + prioritized fix list. Resumable: manifests/prompt_review.jsonl,
one row per chunk.

    .venv/Scripts/python.exe tools/prompt_jury.py --chunk S05-c01     # one
    .venv/Scripts/python.exe tools/prompt_jury.py --limit 3           # smoke
    .venv/Scripts/python.exe tools/prompt_jury.py                     # all 260
    .venv/Scripts/python.exe tools/prompt_jury.py --stats             # tally only
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(r"E:/FNI")
RUN_DIR = ROOT / "runs" / "T0016_s05_technicolor-audio-only-ref2va"
CTX = (ROOT / "docs" / "prompt-jury-context.md").read_text(encoding="utf-8")
OUT = ROOT / "manifests" / "prompt_review.jsonl"
sys.path.insert(0, str(ROOT))
from core import gf_client as gf  # noqa: E402  — endpoint + token live there

JURORS = ["llama3.3-70b-chat-xlarge", "magnum-72b-rp-xlarge",
          "llama-cpp/qwen3.5-35b-a3b_latest"]   # last one has no published alias yet
JUDGE = "llama3.3-70b-chat-xlarge"
VOTES = ROOT / "manifests" / "prompt_jury_votes.jsonl"


def load_votes() -> dict:
    """chunk -> {model: {verdict, issues, raw}}"""
    v = {}
    if VOTES.exists():
        for l in VOTES.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                v.setdefault(r["chunk"], {})[r["model"]] = r
    return v


def ask(model: str, prompt: str, timeout: int = 600) -> str:
    return gf.chat(model, prompt, temperature=0.1, max_tokens=6144, timeout=timeout)


def _json_spans(text: str):
    """Yield balanced top-level {...} spans, so a reasoning model's thinking
    preamble doesn't drown the actual answer object."""
    depth = 0
    start = -1
    in_str = False
    esc = False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                yield text[start:i + 1]
                start = -1


def parse_json(text: str) -> dict | None:
    t = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.M).strip()
    best = None
    for span in _json_spans(t):
        try:
            d = json.loads(span)
        except Exception:
            continue
        if isinstance(d, dict) and ("verdict" in d or "final_verdict" in d):
            best = d  # keep the LAST verdict-shaped object (answer follows thinking)
    return best


def load_dialogue() -> dict:
    d = {}
    lines = (ROOT / "script" / "dialogue-timeline.tsv").read_text(encoding="utf-8").splitlines()
    for ln in lines[1:]:
        p = ln.split("\t")
        if len(p) >= 9:
            d[p[0]] = {"speaker": p[5], "conf": p[6], "text": p[7], "intent": p[8]}
    return d


def ground_truth(row: dict, dialogue: dict, blocking: dict) -> str:
    lines = []
    for lid in row.get("line_ids", []):
        r = dialogue.get(lid)
        if r:
            intent = f"  (delivery intent: {r['intent']})" if r["intent"] else ""
            lines.append(f"  {lid} {r['speaker']} [{r['conf']}]: \"{r['text']}\"{intent}")
    blk = blocking.get(row["chunk_id"], "(none drafted)")
    return (
        f"CHUNK LEDGER: scene {row.get('scene')}, location {row.get('location')}, "
        f"shots {row.get('shot_nums')}, ledger subjects {row.get('speakers')}+{row.get('stamped_names')}\n"
        f"SCRIPT LINES (the only dialogue allowed):\n" + ("\n".join(lines) if lines else "  (no dialogue in this chunk)") + "\n"
        f"VLM BLOCKING DRAFT (physical ground truth): {blk}")


def juror_prompt(model: str, prompt_text: str, truth: str) -> str:
    return (CTX + "\n\n# GROUND TRUTH FOR THIS PROMPT\n" + truth +
            "\n\n# PROMPT UNDER REVIEW (verbatim)\n" + prompt_text +
            "\n\nReturn ONLY the JSON verdict.")


def judge_prompt(votes: dict, truth: str) -> str:
    vs = "\n\n".join(f"## Juror {m}\n{v}" for m, v in votes.items())
    return ("You are the judge merging a 3-model jury's reviews of one H3 video prompt. "
            "Merge their issues: drop duplicates, keep every real blocker/major, resolve "
            "disagreements by the strictest reading of the official rules. Ground truth is "
            "repeated below the votes. Return ONLY JSON "
            '{"final_verdict":"APPROVE"|"NEEDS_FIX","issues":[...same shape...],"fix_summary":'
            '"one short paragraph: the ordered fix list"}\n\n' + vs +
            "\n\n# GROUND TRUTH\n" + truth)


def review_chunk(row, dialogue, blocking, log=print):
    cid = row["chunk_id"]
    pf = RUN_DIR / "prompts" / f"{cid}.txt"
    if not pf.exists():
        return {"chunk": cid, "final_verdict": "NO_PROMPT", "issues": [], "votes": {}}
    prompt_text = pf.read_text(encoding="utf-8")
    truth = ground_truth(row, dialogue, blocking)
    votes, raw = {}, {}
    for m in JURORS:
        try:
            resp = ask(m, juror_prompt(m, prompt_text, truth))
        except Exception as e:
            log(f"  {cid} juror {m} error: {e}")
            continue
        v = parse_json(resp)
        if v and "verdict" in v:
            votes[m] = v.get("verdict")
            raw[m] = resp
        else:
            votes[m] = "UNPARSEABLE"
            raw[m] = resp[:1500]
        time.sleep(1)
    if not raw:
        return {"chunk": cid, "final_verdict": "JURY_UNREACHABLE", "issues": [], "votes": votes}
    try:
        j = ask(JUDGE, judge_prompt(raw, truth))
        jd = parse_json(j) or {}
    except Exception as e:
        jd = {}
        log(f"  {cid} judge error: {e}")
    return {"chunk": cid,
            "final_verdict": jd.get("final_verdict", "JUDGE_FAILED"),
            "fix_summary": jd.get("fix_summary", ""),
            "issues": jd.get("issues", []),
            "votes": votes, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--chunk")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--phase", default="all",
                    help="juror model | judge | all (per-model phases keep the model hot — "
                         "per-chunk model rotation thrashes 40GB+ swaps)")
    args = ap.parse_args()

    rows = [json.loads(l) for l in (ROOT / "fullrun" / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if (RUN_DIR / "prompts" / f"{r['chunk_id']}.txt").exists()]
    if args.chunk:
        rows = [r for r in rows if r["chunk_id"] == args.chunk]
    dialogue = load_dialogue()
    blocking = json.loads((ROOT / "manifests" / "blocking.json").read_text(encoding="utf-8")) \
        if (ROOT / "manifests" / "blocking.json").exists() else {}
    votes = load_votes()
    judged = set()
    if OUT.exists():
        for l in OUT.read_text(encoding="utf-8").splitlines():
            if l.strip():
                judged.add(json.loads(l)["chunk"])

    if args.stats:
        from collections import Counter
        done = [json.loads(l) for l in OUT.read_text(encoding="utf-8").splitlines() if l.strip()] if OUT.exists() else []
        print("final:", Counter(r["final_verdict"] for r in done))
        print("votes:", Counter((m, r2.get("verdict")) for v in votes.values() for m, r2 in v.items()))
        return

    phases = JURORS + ["judge"] if args.phase == "all" else [args.phase]
    for phase in phases:
        n = 0
        err_streak = 0
        for row in rows:
            cid = row["chunk_id"]
            pf = RUN_DIR / "prompts" / f"{cid}.txt"
            prompt_text = pf.read_text(encoding="utf-8")
            truth = ground_truth(row, dialogue, blocking)
            if phase == "judge":
                have = votes.get(cid, {})
                if cid in judged or len(have) < len(JURORS):
                    continue
                raw = {m: r["raw"] for m, r in have.items() if m != "__judged__"}
                try:
                    j = ask(JUDGE, judge_prompt(raw, truth))
                    jd = parse_json(j) or {}
                except Exception as e:
                    err_streak += 1
                    print(f"  {cid} judge error ({err_streak} in a row): {e}", flush=True)
                    if err_streak >= 5:
                        print("CIRCUIT BREAKER: endpoint down mid-judge — ABORTING "
                              "(re-run to resume; votes are ledgered).", flush=True)
                        sys.exit(5)
                    continue
                err_streak = 0
                res = {"chunk": cid,
                       "final_verdict": jd.get("final_verdict", "JUDGE_FAILED"),
                       "fix_summary": jd.get("fix_summary", ""),
                       "issues": jd.get("issues", []),
                       "votes": {m: r.get("verdict") for m, r in have.items() if m != "__judged__"},
                       "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
                with OUT.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(res, ensure_ascii=False) + "\n")
                votes[cid]["__judged__"] = {"verdict": "done"}
                nb = sum(1 for i in res["issues"] if i.get("severity") == "blocker")
                n += 1
                print(f"[judge {n}] {cid}: {res['final_verdict']} ({nb} blockers)", flush=True)
            else:
                if phase in votes.get(cid, {}):
                    continue
                try:
                    resp = ask(phase, juror_prompt(phase, prompt_text, truth))
                except Exception as e:
                    err_streak += 1
                    print(f"  {cid} juror {phase} error ({err_streak} in a row): {e}", flush=True)
                    if err_streak >= 5:
                        print(f"CIRCUIT BREAKER: endpoint down mid-phase {phase} — "
                              f"ABORTING (re-run to resume; votes are ledgered).", flush=True)
                        sys.exit(5)
                    continue
                err_streak = 0
                v = parse_json(resp) or {"verdict": "UNPARSEABLE", "issues": []}
                rec = {"chunk": cid, "model": phase, "verdict": v.get("verdict"),
                       "issues": v.get("issues", []), "raw": resp[:4000]}
                with VOTES.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                votes.setdefault(cid, {})[phase] = rec
                n += 1
                nb = sum(1 for i in rec["issues"] if i.get("severity") == "blocker")
                print(f"[{phase.split(':')[0]} {n}] {cid}: {rec['verdict']} ({nb} blockers)", flush=True)
            if args.limit and n >= args.limit:
                break
        print(f"phase {phase}: {n} calls", flush=True)


if __name__ == "__main__":
    main()
