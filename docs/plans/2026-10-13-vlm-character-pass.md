# Plan — Multi-lens VLM character pass (build)

Date: 2026-10-13. Design: 2026-10-13-vlm-character-pass-design.md.
Execution: subagent-driven (superpowers), TDD mandatory, pytest via
E:\FNI\.venv\Scripts\python.exe -m pytest. NO git commits.

## Contracts every task must honor

- LM Studio: POST http://127.0.0.1:1234/v1/chat/completions, model
  qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s (overridable via --model).
- Images: JPEG downscale, long edge 1024 default (reuse the PIL encode pattern in
  tools/vlm_traits.py encode_image — read it first).
- Cache key: (char, lens, image basename, mtime, size, model). A cached row is
  never re-queried.
- Ledger row (manifests/vlm_charpass.jsonl, append-only):
  {"ts", "char", "lens", "image", "model", "ok", "attempts", "text" (raw), "json" (normalized or null)}
- Normalization failures keep the raw text and set json=null — never throw away an answer.
- All machine paths use forward slashes in JSON (repo convention).

## Task 1 — core/vlm_charpass.py (pure library) + tests

TDD: tests/test_vlm_charpass.py first (failing), then implement.
- LENSES: ordered dict of 7 lenses (physique, face, hair, wardrobe, props, colors,
  signature), each with schema dict + lens instruction text per the design doc.
- build_messages(lens, image_b64) -> chat messages (system invariants shared).
- normalize(lens, text) -> dict|None: strip fences/prose, json.loads, coerce keys per
  lens schema, tolerate extra keys (kept under "_extra"), return None on junk.
- consensus(values: list[str]) -> {"value", "share", "n", "outliers"}: lowercase-
  collapse, substring-merge (e.g. "long black" in "long, straight, black hair"),
  majority vote.
- No network imports beyond stdlib; no LM Studio calls in this module.

## Task 2 — tools/vlm_character_pass.py (runner) + tests

TDD with a fake transport (injectable callable; tests never hit the network).
- --char NAME (repeatable / "all"), --lens NAME (repeatable / "all"), --limit N,
  --max-side N, --model ID, --dry-run (list (image,lens) work items + cache hits).
- Corpus: every image in refs/characters/<NAME>/ (sorted). (Solo-shot stills
  extension is a later task — not built now.)
- Call sequence strictly serial; retry ladder on HTTP 400/429/5xx/timeouts:
  3 attempts, temp 0.0->0.5, max_tokens 600->900, 3s sleep between.
- Writes cache files + ledger rows; resume-safe (re-run continues from cache).
- Exit code 0 on full success, 2 if any call failed after retries.

## Task 3 — tools/vlm_profile_synth.py (aggregation) + tests

TDD with a fixture ledger (no network).
- Reads manifests/vlm_charpass.jsonl (or --ledger), groups by char+lens+trait key.
- Per trait: consensus() -> stable (share >= 0.6) / disputed sections.
- Writes library/char/profiles/<CHAR>.json (machine) and <CHAR>.md (human sheet
  with a prompt_block paragraph: composed specific description for Krea 2 prompts).
- --char / --all, deterministic output ordering (traits alphabetical).

## Task 4 — integration smoke (parent runs, not a subagent)

- .venv/Scripts/python.exe -m pytest (all green)
- 5 real calls against LM Studio (one still x 5 lenses), read the rows, sanity-check
  grounding (no invented names), then launch the full batch as a background terminal
  job and hand results to Task 3.

## Review

One spec+quality reviewer subagent over the three modules after tests pass (compressed
from superpowers' two-reviewer loop — Alex prefers momentum; correction welcome).
