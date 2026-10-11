# FNI project memory (OptMem pattern)

Shared memory for every agent working on E:\FNI: this long-lived Discord chat,
the short-lived Hermes agents Alex spawns per task, and any future session.
Pattern from Victor Taelin's OptChat/OptMem spec; compactor is local LM Studio.

## Roles (refined for the FNI multi-agent setup)

Taelin's spec assumes one chat, one process, one Unix-socket lock. FNI has a
long-lived project chat, multiple short-lived agents, and Windows. So:

- **Appenders (any agent, any time):** `add` only. Id assignment + write are
  serialized by a Windows byte-lock (`memory/append.lock` via msvcrt), so two
  agents appending at once cannot collide on message ids. Never edit the log.
- **Pumper (one at a time):** `pump` holds `memory/pump.lock` non-blocking; a
  second pump exits with a message instead of racing the tree. Short-lived
  agents should NOT pump — they append and leave; the long-lived project chat
  (or a scheduled job) pumps and regenerates the view.
- **Readers (everyone, always safe):** VIEW.md and `zoom` are read-only.
  GhstClwd vets read-only.
- Staleness is fine: a short-lived agent may read a view that lags the last
  few appends. The log is truth; the view is a cache.

## Ledgers (what lives where — do not duplicate)

- `memory/log/` — the memory ledger: rulings, verdicts, decisions, session
  reports. Durable meaning.
- `fullrun/renders.jsonl`, `library/char/sheet-runs/seeds.tsv`,
  `manifests/*.jsonl` — machine ledgers: render state, seeds, per-shot data.
  Memory entries POINT at these (names, counts), never copy their rows.
- `docs/*.md` — settled plans and specs. A doc is a decision frozen into
  prose; the log records that it happened and any later ruling that amends it.

## For any agent starting work on FNI

1. **Read `memory/VIEW.md` first.** It is the whole project history compressed:
   recent events one line each, older events coarser. ~16 KB, cheap to load.
2. Lines are addressed `id+span`. To open one:
   `python core/optmem.py zoom <id> <span>` — shows its two halves; zoom again
   to reach the verbatim original.
3. Authoritative detail still lives where the view says it does: ledgers
   (`fullrun/renders.jsonl`), docs (`docs/*.md`), the skill `fni-h3-pipeline`.

## For any agent finishing work on FNI

Append what happened, then rebuild:

```
python core/optmem.py add --kind user --text "Alex ruled: ..."     # his words, near-verbatim
python core/optmem.py add --kind work --text "<session report>"    # what you did, what changed on disk, what failed and why
python core/optmem.py pump    # compress new messages into the tree (LM Studio, ~1 min per few merges)
python core/optmem.py view    # regenerate memory/VIEW.md
```

Priority discipline (from the spec, enforced by the COMPACT prompt):
Alex's own words first and near-verbatim; then lasting effects (files changed,
counts, seeds, verdicts, failures); then findings; tool noise last, described
not copied. Never make anything look further along than it was.

## Layout

- `memory/log/YYYY-MM-DD.jsonl` — append-only, verbatim, never edit
- `memory/tree.jsonl` — summary nodes {l, i, text}, 512-byte lines, binary tree
- `memory/VIEW.md` — generated; do not hand-edit
- `core/optmem.py` — the tool; `memory/seed.jsonl` — the imported history

## Known quirks

- Compactor model: mistral-7b-instruct-v0.3-abliterated via LM Studio
  (non-reasoning, ~45s/merge). gemma-4-26b-heretic is UNUSABLE as compactor:
  its reasoning never converges on the long COMPACT prompt (empty content even
  at 12800 tokens; reasoning effort:none ignored). lm_chat escalates the token
  budget on empty finish=length replies and raises loudly if none appear —
  empty replies are never silently skipped. Set `OPTMEM_MODEL` to override.
- One writer at a time: `memory/append.lock` serializes id assignment +
  append; `memory/pump.lock` keeps a single compactor. Both are msvcrt
  byte-locks (the spec's Unix socket does not exist on Windows).
- Level-0 messages ≤512 bytes are free nodes (verbatim, no model call) — keep
  `add` entries short and dense; long reports cost merge calls up the tree.
