# Audio-led (yolo) batch — semantic audit of the group-scene failures (2026-11-04)

Ran because the batch's defining failure ("15–20 identical brown-leather women") was condemned by a
32B audit at **2026-10-27 19:43**, and the bounded-crowd `GROUP_CONSTRAINT` landed at **19:57** —
after it. Seven chunks had a **post-fix take (`00002`)** that nobody had ever audited, so "the crowd
guard works" had never been tested. Ledger: `runs/yolo_diag/takecmp.jsonl` (14 rows = 7 chunks ×
2 takes). Driver: `runs/diag_yolo_takes.py` — same four questions on both takes, images downscaled
to ≤1024 px JPEG, model id from the live list, transport errors skip-not-write.

## 1. Did the bounded-crowd clause fix it? **No — and my own numbers say so.**

| chunk | pre-fix `00001` (headcount / extras) | post-fix `00002` (headcount / extras) |
|---|---|---|
| G02-c01 | 6 / "4 identical background women — not intended" | 2 / **"No extra people are present — only NEKRON and TEEGRA"** |
| G03-c01 | 2 / extras "not intended" | 1 / "Frame 3 includes an unintended second woman" |
| G03-c02 | 6 / "5 additional women appear" | 5 / "4 males are added, not intended" |
| G03-c03 | 2 / "Male warrior in background" | 4 / "3 additional women not in reference sheet" |
| G03-c05 | 2 / "numerous identical figures (dozens)" | 5 / "4 extra people (3 males, 1 female lying down)" |
| G03-c06 | 1 / extras flagged | 4 / "3 extra males (total 4 instead of 1 intended)" |
| G03-c07 | 3 / "Person 4 (background) is an extra" | 5 / "5 people shown, but only 1 (TEEGRA) was intended" |

**Verdict: the clause is not a demonstrated improvement.** Count-wise it is **3 better / 4 worse** of
seven, extras are flagged in **6 of 7 post-fix takes** (and 6 of 7 pre-fix), and exactly one chunk
(`G02-c01`) is clean afterwards. Two chunks got a lot better (`G02-c01`, `G03-c05` — the two whose
pre-fix take had the extreme cloned crowd), four got worse.

**A caveat that cuts the other way, and it matters:** the "15–20 identical brown-leather women" that
condemned this batch came from the **2026-10-27 19:43** audit of the *same* `00001` takes. Re-reading
those same takes with fresh frames (this ledger) yields 1–6 people, not 15–20. So that severity figure
is at least partly an artifact of **which frames the auditor sampled** (the old driver's
`frames.json` sits at 10/50/90% of the clip; a crowd has to be *in* the sampled frames to be counted).
Every count in either audit is therefore soft: treat the quotes as evidence of a *class* of failure,
never as a headcount. What is solid in both readings is that extra people appear in the group chunks
and that the extras wear the same brown leather — which is section 3, not the clause.

## 2. Why extras survive: the prompt contradicts the blocking it ships with

`runs/build_technicolor_audio_only.py` picks the cast clause from the SCENE PREFIX
(`row["scene"].startswith("G")`, line 234) and nothing else. Every chunk in this family got
`GROUP_CONSTRAINT`: *"This is a gathering scene with a crowd present. The ONLY people in the shot
are the named characters and the crowd exactly as described in the blocking…"*

But no chunk in the family has a crowd in its blocking. All seven describe **1–5 specific figures**,
and `G03-c05` says outright *"In total, five figures are visible; none are background extras"*:

- G02-c01 "three figures … two main characters in the foreground and one background figure"
- G03-c01 "one person is visible in a close-up … three people are visible"
- G03-c02 "three figures … a woman in the center and two muscular men flanking her"
- G03-c03 "Three people are visible in total"
- G03-c05 "five figures are visible; none are background extras"
- G03-c06 "four male figures are visible in a jungle setting"
- G03-c07 "two large, muscular figures are visible"

So the prompt asserts a crowd, the blocking says 1–5 and no extras, and H3 resolves the contradiction
by populating a small crowd. That is the mechanism; the scene-prefix heuristic is the cause.
**Fix shape: choose the clause from the BLOCKING (headcount / "no extras" wording), not the prefix** —
and where the blocking describes ≤3 figures, the no-crowd clause is the truthful one. Note the
G-prefix heuristic was itself introduced from a 2026-10-27 measurement where GLOBAL produced 3–25
duplicated extras — so neither clause is the whole answer; the contradiction is.

## 3. Root cause of the repeated costume: the most-used sheet is off-canon

Every audit of this family, pre- and post-fix, reports the invented people wearing **the same brown
leather costume**. The skill's rule for "every invented extra wears the SAME wrong costume" is to
inspect the reference sheet — so I did, with the same 32B:

| artifact | 32B read |
|---|---|
| `refs/characters/TEEGRA/traits.txt` | "lightweight **purple** two-piece costume, gold necklace" (also the H3 prompt text) |
| 1983 source frame `refs/characters/TEEGRA/id_TEEGRA.jpg` | "two-piece outfit in **purple** … gold pendant necklace … soft flowing fabric" |
| 1983 source frame `shot_00270_f00000.jpg` | "**lavender** two-piece outfit … gold teardrop pendant" |
| **our generated sheet `TEEGRA_sheet_t01_00001_.png`** | "two-piece costume made of dark **brown, leather-like** material … fringed skirt with gold circular details" |

**The film and our prompt agree (purple); our sheet disagrees (brown leather).** And that sheet is
the single most-used reference in the batch — **137 of 276 graphs** list TEEGRA. So H3 is handed one
costume in text (purple) and another in the picture ref (brown), which is exactly the setup that
produces "Teegra in purple surrounded by extras in brown leather". The sheet is the wrong artifact,
not the prompt: the prompt matches the source film.

Consequence for the batch: any take containing TEEGRA carries this ambiguity, i.e. most of G01–G09.
A re-queue without fixing the sheet would reproduce the failure while looking like a fresh attempt.

**Action: audit all 13 sheets the batch consumed** — `tools/audit_sheets_vs_traits.py`, ledger
`manifests/sheet_traits_audit.jsonl`, one 32B call per character (sheet vs traits.txt, costume first).
TEEGRA came back MISMATCH on the first run; the other twelve were auditing at the time of writing.
A sheet that disagrees with its own traits is a generator of wrong people and should gate the run.

## 4. What to do next (cheapest first)

1. **Fix TEEGRA's sheet** (re-generate to the film's purple/lavender, or accept brown as canon and
   rewrite traits + prompts consistently — the mismatch is the bug, either direction). Then re-queue
   a TEEGRA chunk and re-run `runs/diag_yolo_takes.py` on it: one variable, one watchable verdict.
2. **Pick the cast clause from the blocking**, not `scene.startswith("G")`, and re-audit one G03 chunk.
3. Only then consider re-queueing the 134 missing takes (board row 11) — re-running the batch on the
   current sheet would reproduce section 3.
