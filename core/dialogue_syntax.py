"""Speaker IDs for H3 prompts — `(S1)`, `(S2)` are SPEAKER indices, not subject indices.

Official rule, cited from the guides we vendor:

* `docs/h3-official/VIDEO_PROMPT_WRITING_GUIDE_base_en.md` §4.4 — "Subjects who speak, sing, or
  produce an off-screen human voice use **stable IDs** such as `(S1)` and `(S2)` … **A speaker keeps
  the same ID across shots**; characters who never vocalize receive no speaker ID."
* `docs/h3-official/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md` §5.4 — "**The ID comes from the target
  video's global speaker order and is not independently assigned or renumbered**", and its own
  example is `<Subject 2> (S1) turns toward the woman and says, <d>…</d>` — i.e. the speaker index
  and the subject number are independent.

Alex, 2026-11-05 (correcting this for the second time): "\"(S1)\" … means the first speaker in that
prompt … if a prompt has three shots and the s1 is subject 3, they stay s3 for the full prompt" —
then corrected to "they stay s1 for the whole prompt". So: number speakers by the order they first
SPEAK in this prompt, consecutively from 1, and hold that ID across every shot of the prompt.

Why it bit: `build_technicolor_audio_only.py`, `build_technicolor_ref2va.py` and `refrun.py` all
wrote `(S<subject index>)`. That is accidentally correct whenever the subjects happen to speak in
subject order — which is why S03-c01 looked fine (Juliana is Subject 1 and speaks first) — and wrong
the moment the first speaker is not Subject 1, at which point the model reads the ID as "the Nth
speaker" and can put the line on the wrong face.
"""
from __future__ import annotations


def speaker_index(speakers_in_order) -> dict[str, int]:
    """`{'JULIANA': 1, 'NEKRON': 2}` from speakers listed in first-speaking order."""
    out: dict[str, int] = {}
    for spk in speakers_in_order:
        if spk and spk not in out:
            out[spk] = len(out) + 1
    return out


def tag(index: int) -> str:
    return f"(S{index})"


def order_from_lines(dialogue, line_ids, start_of) -> list[str]:
    """First-speaking order for one prompt, from its lines' real timings.

    `start_of(line_row)` returns seconds; sorting by it is what makes the order the *speaking* order
    rather than the shot or roster order. Lines with no timing keep their ledger position.
    """
    rows = [(i, dialogue[lid]) for i, lid in enumerate(line_ids) if dialogue.get(lid)]
    def key(item):
        i, r = item
        try:
            return (0, start_of(r), i)
        except Exception:  # noqa: BLE001 — a missing time must not reorder the rest
            return (1, 0.0, i)
    rows.sort(key=key)
    return [r.get("speaker") for _, r in rows]
