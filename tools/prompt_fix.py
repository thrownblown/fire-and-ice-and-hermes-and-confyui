# -*- coding: utf-8 -*-
"""Prompt fix pass — llama3.3-70b (the strongest juror) REWRITES every prompt
the jury condemned, then verifies its own work mechanically.

Alex (2026-10-28): "if llama 70b has such strong opinions on prompts, it should
rewrite the prompt."

Per chunk: the rewriter sees the jury context pack (official speaker/dialog
syntax), the ORIGINAL prompt, the judge's merged issue list + fix_summary, and
the ground truth (script lines, VLM blocking, ledger). It must return the FULL
rewritten six-field prompt, not a diff. v2 prompts go to
runs/T0016.../prompts_v2/<chunk>.txt — originals are never clobbered.

Deterministic verification after every rewrite (no model): section order,
every script line present verbatim, no <Video N>, no error strings, length.
Failures are retried once with the verification errors fed back, then recorded
as FAILED_VERIFY (never silently shipped).

Gate: --wait-for-jury polls until no prompt_jury process is alive (model-churn
rule: the rewriter is the 70b and must not evict a running juror).

    .venv/Scripts/python.exe tools/prompt_fix.py --chunk S05-c01   # one, verbose
    .venv/Scripts/python.exe tools/prompt_fix.py                   # all NEEDS_FIX
    .venv/Scripts/python.exe tools/prompt_fix.py --wait-for-jury   # gate + all
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(r"E:/FNI")
RUN_DIR = ROOT / "runs" / "T0016_s05_technicolor-audio-only-ref2va"
V2DIR = RUN_DIR / "prompts_v2"
CTX = (ROOT / "docs" / "prompt-jury-context.md").read_text(encoding="utf-8")
FIXLEDGER = ROOT / "manifests" / "prompt_fixes.jsonl"
REVIEW = ROOT / "manifests" / "prompt_review.jsonl"

MODEL = "llama3.3-70b-chat-xlarge"          # goldfishbowl alias -> llama-cpp/llama3.3-70b_latest
MAX_TOKENS = 4096       # never below 2048: the abliterated arm thinks without a budget and
                        # would spend the whole allowance on reasoning, returning HTTP 400 whose
                        # body reads like prose (looks like a model fault; it is a budget artifact)
SECTIONS = ["subject_definitions", "summary", "retention_analysis",
            "detailed_description", "overall_soundscape", "non_diegetic_music"]

sys.path.insert(0, str(ROOT))
from core import gf_client as gf              # noqa: E402  (goldfishbowl transport: Studio /v1)
from core.prompt_guards import looks_like_error  # noqa: E402


def ask(prompt: str, timeout: int = 900) -> str:
    """Transport lives in core/gf_client.py (Unsloth Studio /v1/chat/completions + bearer).

    The old Ollama call was `{"prompt": ..., "options": {...}}` against
    /api/generate on :11434 — that endpoint and its model ids are gone (2026-11-01).
    gf.chat also refuses a reply that came from a DIFFERENT model than the one asked
    for, which is how an unknown id silently gets served by whatever is resident.
    """
    return gf.chat(MODEL, prompt, max_tokens=MAX_TOKENS, temperature=0.15, timeout=timeout)


def jury_alive() -> bool:
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object {$_.CommandLine -match 'prompt_jury'} | "
             "Select-Object -ExpandProperty ProcessId"],
            capture_output=True, text=True, timeout=30)
        return bool(r.stdout.strip())
    except Exception:
        return False


def jury_complete() -> bool:
    """True only when every prompt-file chunk has all 3 juror votes AND a
    judge row. Anything less and the rewrite phase must not start — a crashed
    jury is indistinguishable from a finished one if you only look at processes."""
    try:
        rows = [json.loads(l) for l in (ROOT / "fullrun" / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        chunks = [r["chunk_id"] for r in rows if (RUN_DIR / "prompts" / f"{r['chunk_id']}.txt").exists()]
        votes = {}
        vf = ROOT / "manifests" / "prompt_jury_votes.jsonl"
        if vf.exists():
            for l in vf.read_text(encoding="utf-8").splitlines():
                if l.strip():
                    r = json.loads(l)
                    votes.setdefault(r["chunk"], set()).add(r["model"])
        judged = set()
        if REVIEW.exists():
            for l in REVIEW.read_text(encoding="utf-8").splitlines():
                if l.strip():
                    judged.add(json.loads(l)["chunk"])
        return all(len(votes.get(c, set())) >= 3 for c in chunks) and \
               all(c in judged for c in chunks)
    except Exception:
        return False


def load_dialogue() -> dict:
    d = {}
    for ln in (ROOT / "script" / "dialogue-timeline.tsv").read_text(encoding="utf-8").splitlines()[1:]:
        p = ln.split("\t")
        if len(p) >= 9:
            d[p[0]] = {"speaker": p[5], "conf": p[6], "text": p[7], "intent": p[8]}
    return d


def ground_truth(row, dialogue, blocking):
    lines = []
    for lid in row.get("line_ids", []):
        r = dialogue.get(lid)
        if r:
            intent = f"  (delivery intent: {r['intent']})" if r["intent"] else ""
            lines.append(f"  {lid} {r['speaker']} [{r['conf']}]: \"{r['text']}\"{intent}")
    blk = blocking.get(row["chunk_id"], "(none drafted)")
    return (f"CHUNK LEDGER: scene {row.get('scene')}, location {row.get('location')}, "
            f"shots {row.get('shot_nums')}, ledger subjects {row.get('speakers')}+{row.get('stamped_names')}\n"
            f"SCRIPT LINES (every one must appear VERBATIM, attributed to its speaker, "
            f"each with a voice-identity phrase and a stable (Sx) ID):\n"
            + ("\n".join(lines) if lines else "  (no dialogue in this chunk)")
            + f"\nVLM BLOCKING DRAFT (physical ground truth — who is present, what each is "
              f"doing, the setting):\n{blk}")


def rewrite_prompt(original, issues_text, truth, feedback=None):
    fb = ("\n\nYour previous attempt FAILED mechanical verification:\n" + feedback +
          "\nFix exactly these problems and return the complete prompt again.") if feedback else ""
    return (CTX +
            "\n\n# YOUR TASK\nRewrite the H3 prompt below COMPLETELY, fixing every jury issue "
            "listed. Output the full rewritten six-field prompt and NOTHING else — no preamble, "
            "no commentary, no fences. Keep everything that was already correct (style register, "
            "camera moves, sound design) — change only what the issues and ground truth demand. "
            "Dialogue rules are absolute: every script line verbatim, one speaker per line, "
            "voice-identity phrase + stable (Sx) ID outside <d>, language tag + line inside <d>. "
            "Blocking must match the VLM draft. The cast constraint must fit the scene."
            "\n\n# GROUND TRUTH\n" + truth +
            "\n\n# JURY ISSUES TO FIX\n" + issues_text +
            "\n\n# ORIGINAL PROMPT\n" + original + fb)


def verify(text: str, row, dialogue) -> list[str]:
    problems = []
    if looks_like_error(text):
        problems.append("contains an error/transport string")
    for i, s in enumerate(SECTIONS):
        if not re.search(rf"(?m)^{re.escape(s)}\s*:", text):
            problems.append(f"missing section '{s}:'")
    pos = [text.find(s + ":") for s in SECTIONS]
    if pos != sorted(pos):
        problems.append("sections out of order")
    if "<Video" in text:
        problems.append("audio-only prompt must not reference <Video N>")
    for lid in row.get("line_ids", []):
        r = dialogue.get(lid)
        if r and r["text"] not in text:
            problems.append(f"script line {lid} missing or not verbatim: \"{r['text'][:60]}\"")
        if r and f"<d>" in text and "[English]" not in text:
            problems.append("dialogue present but no [Language] tag")
            break
    if len(text) < 400:
        problems.append(f"too short ({len(text)} chars)")
    return problems


def fix_chunk(row, dialogue, blocking, review, log=print):
    cid = row["chunk_id"]
    original = (RUN_DIR / "prompts" / f"{cid}.txt").read_text(encoding="utf-8")
    truth = ground_truth(row, dialogue, blocking)
    issues = review.get("issues", [])
    issues_text = (review.get("fix_summary", "") + "\n" +
                   "\n".join(f"- [{i.get('severity')}/{i.get('category')}] {i.get('detail')} "
                             f"FIX: {i.get('fix', '')}" for i in issues)).strip() or "(no issues listed)"
    feedback = None
    for attempt in (1, 2):
        try:
            out = ask(rewrite_prompt(original, issues_text, truth, feedback))
        except Exception as e:
            return {"chunk": cid, "status": "REWRITER_ERROR", "error": str(e),
                    "model": MODEL, "max_tokens": MAX_TOKENS}
        problems = verify(out, row, dialogue)
        if not problems:
            V2DIR.mkdir(parents=True, exist_ok=True)
            (V2DIR / f"{cid}.txt").write_text(out, encoding="utf-8")
            return {"chunk": cid, "status": "FIXED", "attempt": attempt,
                    "v2": str(V2DIR / f"{cid}.txt"), "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "model": MODEL, "max_tokens": MAX_TOKENS}
        feedback = "\n".join("- " + p for p in problems)
        log(f"    {cid} attempt {attempt} failed verify: {problems[:3]}")
    return {"chunk": cid, "status": "FAILED_VERIFY", "problems": problems,
            "model": MODEL, "max_tokens": MAX_TOKENS}


def main():
    global MODEL, MAX_TOKENS, V2DIR, FIXLEDGER
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--chunk")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--wait-for-jury", action="store_true")
    ap.add_argument("--model", default=MODEL,
                    help="rewriter model id — this is the A/B knob (arm vs control)")
    ap.add_argument("--max-tokens", type=int, default=MAX_TOKENS)
    ap.add_argument("--out-dir", default=None,
                    help="where rewritten prompts go (A/B: give each arm its own dir)")
    ap.add_argument("--ledger", default=None,
                    help="fix ledger to append to (A/B: give each arm its own ledger)")
    args = ap.parse_args()

    MODEL = args.model
    MAX_TOKENS = args.max_tokens
    if MAX_TOKENS < gf.MIN_TOKENS_FOR_THINKERS:
        print(f"WARNING: --max-tokens {MAX_TOKENS} is under the {gf.MIN_TOKENS_FOR_THINKERS} floor — "
              f"a thinking arm spends the whole allowance on reasoning and returns no answer",
              flush=True)
    if args.out_dir:
        V2DIR = Path(args.out_dir)
    if args.ledger:
        FIXLEDGER = Path(args.ledger)
    print(f"rewriter: {MODEL} | max_tokens: {MAX_TOKENS} | v2 -> {V2DIR} | ledger -> {FIXLEDGER}",
          flush=True)

    if args.wait_for_jury:
        print("waiting for the jury to COMPLETE (not just exit — a crash is not a drain) ...", flush=True)
        while True:
            time.sleep(60)
            if jury_complete():
                print("jury complete; starting rewrite phase", flush=True)
                break
            if not jury_alive():
                # jury died mid-run: the circuit-breaker rule, not a race —
                # restarting the jury is the scheduler's job, we just keep waiting
                print("jury not complete and not alive — still waiting", flush=True)

    reviews = {}
    if REVIEW.exists():
        for l in REVIEW.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                reviews[r["chunk"]] = r
    rows = [json.loads(l) for l in (ROOT / "fullrun" / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if (RUN_DIR / "prompts" / f"{r['chunk_id']}.txt").exists()]
    if args.chunk:
        rows = [r for r in rows if r["chunk_id"] == args.chunk]
    dialogue = load_dialogue()
    blocking = json.loads((ROOT / "manifests" / "blocking.json").read_text(encoding="utf-8")) \
        if (ROOT / "manifests" / "blocking.json").exists() else {}

    done = set()
    if FIXLEDGER.exists():
        for l in FIXLEDGER.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                if r.get("status") == "FIXED":
                    done.add(r["chunk"])

    n = 0
    err_streak = 0
    for row in rows:
        cid = row["chunk_id"]
        if cid in done:
            continue
        rev = reviews.get(cid)
        if rev and rev.get("final_verdict") == "APPROVE":
            continue  # nothing to fix
        res = fix_chunk(row, dialogue, blocking, rev or {})
        with FIXLEDGER.open("a", encoding="utf-8") as f:
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
        n += 1
        print(f"[{n}] {cid}: {res['status']}", flush=True)
        # circuit breaker: a dead endpoint must STOP the run, not record 255 errors
        if res["status"] == "REWRITER_ERROR":
            err_streak += 1
            if err_streak >= 5:
                print("CIRCUIT BREAKER: 5 consecutive rewriter errors — endpoint is down. "
                      "ABORTING (re-run to resume; FIXED entries are kept).", flush=True)
                sys.exit(5)
        else:
            err_streak = 0
        if args.limit and n >= args.limit:
            break
    print(f"rewrote {n} chunks; ledger {FIXLEDGER}; v2 dir {V2DIR}", flush=True)


if __name__ == "__main__":
    main()
