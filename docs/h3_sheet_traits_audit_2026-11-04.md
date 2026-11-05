# Sheet-vs-canon audit — the 13 character sheets the audio-led batch consumed (2026-11-04)

Follows from `docs/h3_audit_audio_led_group_scenes_2026-11-04.md`: the invented extra people in the
group-scene takes all wear the **same brown leather**, and the skill's rule for that is to inspect the
reference the invention is seeded from. TEEGRA's sheet turned out to be off-canon, so all 13 sheets the
batch used were audited against their own canon.

- Tool: `tools/audit_sheets_vs_traits.py` — one 32B call per character (the sheet + its `traits.txt`,
  costume first, then hair/eyes/skin, then "how many figures / any second costume").
- Ledger: `manifests/sheet_traits_audit.jsonl` (13 rows). Images downscaled to ≤1024 px JPEG
  (the 32B serves 32,768 tokens of context now and an image costs context too). One model,
  sequential — no evictions.

## Result 1: only 4 of the 13 sheets were auditable at all

**Nine of the thirteen characters have no non-empty `refs/characters/<NAME>/traits.txt`** — eight have
no file at all (`NEKRON`, `JAROL`, `TARO`, `ROLIEL`, `JULIANA`, `ENVOY`, `SUBHUMAN CAPTAIN`,
`SUBHUMAN`), and `LARN`'s is a 0-byte file. There is no canon to enforce, so there is nothing to
compare a sheet against.

**A trap found while doing this, worth keeping:** asked to compare a sheet against an *empty* traits
file, the 32B **fabricated the canon** — for LARN it asserted "the canonical costume is maroon (not
black)" out of a 0-byte file, and for the no-file characters it invented "typical tribal warrior attire
described in the film's reference". Nine confident MATCH/MISMATCH verdicts that meant nothing. The tool
now writes a **`NO_CANON`** row instead of asking, and the nine fabricated rows were deleted from the
ledger rather than reported. Any audit that hands a model an absent ground truth gets an invented one.

## Result 2: all four sheets that *can* be checked disagree with their canon

| character | canon (`traits.txt`) | sheet (32B read) | verdict |
|---|---|---|---|
| **TEEGRA** | "very long black hair, **pale skin**, green eyes, **lightweight purple two-piece** costume, gold necklace" | "two-piece costume made of **dark brown, leather-like** material … fringed skirt with gold circular details"; reads as tan skin | **MISMATCH** — costume colour, and skin tone |
| **TUTOR** | "TUTOR is an elderly WOMAN (canon: Alex 2026-10-28) … **Ochre hide robe**, woven vest with bone toggles" | "brown leather or hide, with **metallic bronze or gold accents** … a two-piece ensemble: a bra-like top with a central circular emblem, a short pleated skirt, arm bracers" | **MISMATCH** — reads as leather armour, not a hide robe; the canon is a 2026-10-28 ruling |
| **DARKWOLF** | "tall, dark tanned skin, **wearing a wolf's head as a hood or helmet, his yellow eyes looking through the wolf's**; wears a teeth and skull pendant necklace" | "brown leather with bronze circular plates … fringed loincloth"; **"there are no visible teeth and skull pendant necklace"**, no wolf's-head hood, no yellow eyes | **MISMATCH** — the character's defining feature is missing entirely |
| **SPIRIT** | "SPIRIT is **ROLIEL'S GHOST** (canon: Alex 2026-10-28) — **long crimson hair, amber eyes**, oval face, **hide top, blue woven collar, hide skirt**" | "black, made of fabric (top and pants) with leather-like accents"; reads as **white** hair | **MISMATCH** — hair colour and costume both; the canon is a 2026-10-28 ruling |

Two distinct mechanisms, and they need different fixes:

1. **Stale by ruling.** `TUTOR` and `SPIRIT` carry canon dated **2026-10-28**, and their sheets were
   rendered **2026-10-23**. The sheets are simply older than the decisions — a re-render, not a prompt
   tweak. (Both traits files are uncommitted working-tree changes, i.e. written recently.)
2. **Never carried the feature.** `DARKWOLF`'s sheet has no wolf's-head hood, no yellow eyes and no
   teeth-and-skull pendant, and `TEEGRA`'s sheet has the wrong costume colour — these are not stale,
   they never matched.

## Why this is upstream of the render failures, not cosmetic

A character sheet is the identity anchor for every take that lists that character, and these sheets are
heavily reused: **TEEGRA alone appears in 137 of the 276 graphs** of the audio-led batch. Feeding H3 a
sheet whose costume contradicts the prompt's costume gives the model two plausible looks for one
character — and in the group chunks it dresses the invented extra people in the sheet's version while
naming the subject in the prompt's version. So sheet drift does not stay in the sheet.

## What to do

1. **Write the missing canon** — 9 of 13 characters have no `traits.txt`. Content is Alex's call; the
   *existence* of the file is mechanical, and without it nothing downstream can be checked.
2. **Re-render the four mismatched sheets** (TEEGRA, TUTOR, DARKWOLF, SPIRIT), each against its
   `traits.txt` text, then re-run this audit on those four — one cheap loop, watchable.
3. **Gate a batch on this audit.** 13 VLM calls catch a whole class of "the references were wrong"
   before 256 renders are paid for. It belongs next to the existing pre-batch checks (sheet glob,
   asset-generation line).
4. Only then consider re-queueing the 134 missing takes (board row 11): re-running them on today's
   sheets would reproduce the same wrong-people failure.

## Caveats, stated so nobody over-reads this

- "MISMATCH" here is a keyword summary; the full per-character verdict (and the model's own MATCH/
  MISMATCH per element) is in `manifests/sheet_traits_audit.jsonl`.
- The VLM's **skin-tone** reads are the weakest part of the evidence — the same reader that called
  TEEGRA's sheet tan also called her `id_TEEGRA.jpg` frame purple-clad but said nothing about tone.
  Treat costume and missing-feature findings as solid; treat tone as a flag to check by eye.
- Nothing here says the *prompts* are wrong. Where prompt and film agree (TEEGRA purple), the prompt is
  the correct side and the sheet is the outlier.
