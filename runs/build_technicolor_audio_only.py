"""Render a chunk through REF2VA AUDIO-ONLY — no <Video 1>, no video reference.

Alex: "use like ref2v without video just audio". This is the backup mode named
earlier: character sheets + location plate as <Picture N> refs, plus the chunk's
ORIGINAL audio as a standalone ref_audio (LoadAudio on the source ref clip ->
audio only). No ref_videos / ref_video_audios, no GetVideoComponents.

Because there is no <Video 1>, the prompt carries NO video-reference lines (the
dead-reference rejection rule): subjects are pinned from the sheets, the reference
audio is copied, and the motion comes from the text + the sheet/plate look.

Reuses refrun.build_ref_graph then strips the video branch, so the sampler/save
chain stays the single validated path. Dry by default.

Run:
  .venv/Scripts/python.exe runs/build_technicolor_audio_only.py --chunk S05-c01
  .venv/Scripts/python.exe runs/build_technicolor_audio_only.py --chunk S05-c01 --queue
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, r"E:/FNI/pipeline")
sys.path.insert(0, r"E:/FNI/runs")
sys.path.insert(0, r"E:/FNI")

import fullrun as F  # noqa: E402
import refrun as R  # noqa: E402
import build_technicolor_ref2va as T  # noqa: E402  (TRAITS, sheet_path, plate_path, PLATE)
from core.prompt_guards import usable_blocking, lint_prompt  # noqa: E402
from core import dialogue_syntax as D  # noqa: E402
from core import identity_match as IM  # noqa: E402

ROOT = Path(r"E:/FNI")
RUN_DIR = ROOT / "runs" / "T0016_s05_technicolor-audio-only-ref2va"


def load_blocking() -> dict:
    """Per-chunk hand-authored blocking (manifests/blocking.json), grounded in the
    source stills. Overrides the ledger beat; motion[] only says 'static' and cannot
    express 'lounging on a couch'."""
    p = ROOT / "manifests" / "blocking.json"
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        return {k: v for k, v in d.items() if not k.startswith("_")}
    return {}


# Always-on cast/scene constraint. Kills the two failure modes seen in the first
# audio-only pass: H3 inventing background extras, and defaulting to a walk-in.
# INTIMATE SCENES ONLY — for a group/crowd scene this string is a lie and makes
# H3 invent an unconstrained cloned crowd (measured 2026-10-27).
GLOBAL_CONSTRAINT = (
    "ONLY the named characters are present in the shot — there are no other people, "
    "no crowd, no background figures and no extras at any point. The scene is quiet, "
    "intimate and relaxed. The characters stay where they are; nobody walks, enters, "
    "or moves toward the camera."
)

# Group-scene replacement: the crowd is EXPECTED, but bounded — every person must
# come from the blocking description, nobody gets invented beyond it.
GROUP_CONSTRAINT = (
    "This is a gathering scene with a crowd present. The ONLY people in the shot are "
    "the named characters and the crowd exactly as described in the blocking — its "
    "size, costume and arrangement must match that description. Do not add people "
    "beyond it: no duplicates of the named characters, no new foreground figures, "
    "and nobody walks toward the camera."
)


def _shot_presence(rec, subjects) -> str:
    """Who is ACTUALLY on screen in this shot, from `manifests/character_pass.jsonl`.

    Measured defect (Alex, 2026-11-05, on T0017): "nekron was speaking juliannas lines". The prompt
    was correct in every checkable way — the line→subject attribution matched the script (L023/24
    Juliana, L025/26 Nekron), `<Picture 1>` was JULIANA's sheet and `<Picture 2>` NEKRON's, and the
    dialogue timing landed each line inside the right shot. What the prompt never said was WHO IS IN
    THE FRAME per shot: shot 00067 is a close-up of ONE person (character_pass: "slender, long
    straight black hair, pale, purple top" — Juliana), but the chunk-level blocking told the model
    both characters were present and facing each other. With two figures in the same purple register
    and "tightening toward the face" naming no owner, the model can put S1's line on the other face.

    This clause makes the on-screen cast explicit per shot, and names the subject when the VLM's
    appearance descriptors match that subject's canon.
    """
    ppl = (rec or {}).get("people") or []
    if not ppl:
        return ""
    def label(p):
        hair = (p.get("hair") or "").strip()
        skin = (p.get("skin") or "").strip()
        cloth = (p.get("clothing") or "").strip()
        sex = (p.get("sex") or "").strip()
        bits = [b for b in (sex, skin, hair and f"{hair} hair", cloth) if b]
        who = ", ".join(bits)
        # match to a named subject on hair + clothing words (TRAITS is the canon text); the scorer is
        # shared with tools/check_name_stamps.py so the prompt and the audit never disagree
        best = IM.assertable(f"{hair} {cloth}", subjects, T.TRAITS,
                             hair=hair, sex=IM.sex_of(sex))
        return f"{who} (this is {best})" if best else who
    n = len(ppl)
    if n == 1:
        return f"On screen in this shot: exactly 1 person, alone — {label(ppl[0])}. Nobody else is visible."
    return (f"On screen in this shot: exactly {n} people — "
            + "; ".join(label(p) for p in ppl)
            + ". Nobody else is visible.")


def build_prompt(row, subjects, plate_count, dialogue, people, blocking=None,
                 group_scene=False, shot_presence=False) -> str:
    n_sub = len(subjects)
    sd = "\n".join(
        f"<Subject {i}> is {name}, {T.TRAITS.get(name, '')}, shown in <Picture {i}>."
        for i, name in enumerate(subjects, 1))

    summ = ("[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: "
            "a single continuous live-action scene of " + subjects[0] +
            ", preserving each character's appearance from their reference sheet and "
            "the spoken dialogue and timing of the reference audio.")

    rt = []
    span = f"[Shot 1] and [Shot {len(row['shots'])}]" if shot_presence else "[Shot 1] and [Shot 2]"
    for i, name in enumerate(subjects, 1):
        rt.append(f"<Subject {i}>: fully_preserved — keep {T.TRAITS.get(name, 'identity')} "
                  f"consistent across {span}.")
    rt.append("Reference audio: fully_copy — reuse the spoken lines and their exact timing.")
    for k in range(plate_count):
        p = n_sub + k + 1
        rt.append(f"<Picture {p}>: background_only — this is the location as a painted "
                  "environment, not people; keep ONLY the environment (layout, lighting, "
                  "color, architecture) and ignore any figures.")
    rt = "\n".join(rt)

    style = F.style_line(row["location"])
    # the shared style line says "epic practical sets and crowds" on EVERY location —
    # for an intimate interior that directly invites H3 to add background people.
    # Strip it here (do not touch the shared table; other tracks may want crowds).
    style = style.replace("epic practical sets and crowds", "practical sets")
    sidx = {name: i + 1 for i, name in enumerate(subjects)}
    # SPEAKER ids, not subject ids: number by first-speaking order (docs/h3-official ref guide §5.4,
    # and Alex's correction — "(S1) means the first speaker in that prompt … they stay s1 for the
    # whole prompt"). Deriving them from the subject index is only accidentally right when the
    # subjects speak in subject order.
    spk_idx = D.speaker_index(D.order_from_lines(dialogue, row["line_ids"], lambda r: F.sec(r["start"])))
    shot_lines = []
    for idx, (sid, snum) in enumerate(zip(row["shots"], row["shot_nums"]), 1):
        comp = {"shot_type": row["shot_type"][idx - 1], "angle": row["angle"][idx - 1]}
        cam = F.camera_move(comp, idx, len(row["shots"]))
        # the shared camera_move embeds "as the figure moves" — conflicts with an
        # explicit still/lounging blocking, so drop that clause
        cam = cam.replace(" as the figure moves", "").replace("as the figure moves", "")
        bits = [f"[Shot {idx}]", cam]
        if shot_presence:
            pres = _shot_presence(people.get(sid), subjects)
            if pres:
                bits.append(pres)
        for lid in row["line_ids"]:
            r = dialogue.get(lid)
            if not r:
                continue
            mid = (F.sec(r["start"]) + F.sec(r["end"])) / 2
            if not (people.get(sid, {}).get("_t0", 0) <= mid < people.get(sid, {}).get("_t1", 0)):
                continue
            spk = r["speaker"]
            tag = D.tag(spk_idx.get(spk, 1))     # speaker id, NOT the subject index
            bits.append(f"<Subject {sidx.get(spk, 1)}> {tag} says: <d>[English] {r['text']}</d>")
        shot_lines.append(" ".join(b for b in bits if b))
    constraint = GROUP_CONSTRAINT if group_scene else GLOBAL_CONSTRAINT
    dd = f"{style}\n\n{constraint}\n\n"
    if blocking:
        dd += blocking + "\n\n"
    dd += "\n\n".join(shot_lines)

    return "\n\n".join([
        "subject_definitions:", sd, "",
        "summary:", summ, "",
        "retention_analysis:", rt, "",
        "detailed_description:", dd, "",
        "overall_soundscape:", F.soundscape_line(row), "",
        "non_diegetic_music:", F.music_line(row["music"]),
    ])


def build_chunk_audio(row) -> Path | None:
    """Concat the chunk's shot refs' AUDIO into one audio-only mp4 (no video)."""
    srcs = [R.REFS / f"shot_{n}.mp4" for n in row["shot_nums"]]
    srcs = [s for s in srcs if s.exists() and s.stat().st_size > 0]
    if not srcs:
        return None
    tmp = ROOT / ".tmp"
    tmp.mkdir(exist_ok=True)
    out = tmp / f"{row['chunk_id']}_audio.mp4"
    if len(srcs) == 1:
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(srcs[0]),
               "-vn", "-ar", "32000", "-ac", "2", str(out)]
    else:
        ins = []
        for s in srcs:
            ins += ["-i", str(s)]
        flt = "".join(f"[{i}:a]" for i in range(len(srcs))) + f"concat=n={len(srcs)}:v=0:a=1[a]"
        cmd = ["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", flt,
               "-map", "[a]", "-ar", "32000", "-ac", "2", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return out if (r.returncode == 0 and out.exists()) else None


def build_audio_only_graph(row, sheet_names, plate_names, audio_name):
    """refrun's graph with the video branch removed and a single ref_audio added."""
    g = R.build_ref_graph(row, sheet_names, plate_names=plate_names)
    # strip the video reference branch
    g.pop("148", None)   # LoadVideo
    g.pop("147", None)   # GetVideoComponents
    g["136"]["inputs"].pop("ref_videos.ref_video_0", None)
    g["136"]["inputs"].pop("ref_video_audios.ref_video_audio_0", None)
    # add a standalone audio reference. NB: build_ref_graph numbers LoadImage nodes
    # from 149 up (one per still + plate, up to ~157) — use an id clear of that range
    # or a chunk with 4+ images collides and wires AUDIO into an IMAGE input.
    g["190"] = {"inputs": {"audio": audio_name}, "class_type": "LoadAudio",
                "_meta": {"title": "Load Reference Audio"}}
    g["136"]["inputs"]["ref_audios.ref_audio_0"] = ["190", 0]
    return g


def finalize_graph(g, chunk_id, take, text, seed=None):
    """Set prompt text, output prefix, ref_image_size, and optional seed override."""
    g["138"]["inputs"]["value"] = text
    tag = f"{chunk_id}_audioOnly_t{take:02d}"
    if seed is not None:
        g["129"]["inputs"]["noise_seed"] = seed
        tag += f"_s{seed}"
    g["92"]["inputs"]["filename_prefix"] = f"video/{tag}"
    g["136"]["inputs"]["ref_image_size"] = "max"
    return g, tag


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chunk", required=True)
    ap.add_argument("--audio", default=None, help="server-side audio filename (default: <chunk>_ref.mp4)")
    ap.add_argument("--queue", action="store_true")
    ap.add_argument("--take", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None, help="override the chunk seed (seed hunting)")
    ap.add_argument("--subjects", help="comma-list to override the ledger's subjects (fixes mis-stamps)")
    ap.add_argument("--force", action="store_true",
                    help="queue despite guardrail warnings (crowd scene without blocking, etc.)")
    ap.add_argument("--shot-presence", action="store_true",
                    help="state WHO is on screen per shot from manifests/character_pass.jsonl, and "
                         "fix the retention span to the chunk's real shot count. Off = byte-identical "
                         "to the T0017 prompt, so it can be A/B'd against a render.")
    args = ap.parse_args()

    rows = [json.loads(l) for l in F.CHUNK_LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    row = next(r for r in rows if r["chunk_id"] == args.chunk)

    order = []
    for spk in row["speakers"]:
        if spk not in order:
            order.append(spk)
    for nm in row["stamped_names"]:
        if nm not in order:
            order.append(nm)
    subjects = [n for n in order if T.sheet_path(n)]
    if args.subjects:
        subjects = [n.strip() for n in args.subjects.split(",") if n.strip()]
    if not subjects:
        print("no sheeted subjects; abort"); return

    plate = T.plate_path(T.PLATE.get(row["scene"], ""))
    plate_names = [plate.name] if plate else []

    audio_name = args.audio or f"{row['chunk_id']}_audio.mp4"

    people, dialogue = R.load_context()
    raw_blocking = load_blocking().get(args.chunk)
    if raw_blocking and not usable_blocking(raw_blocking):
        print(f"GUARD: blocking for {args.chunk} is an error/garbage string — dropped, "
              f"NOT injected into the prompt")
        raw_blocking = None
    blocking = raw_blocking

    # crowd-scene guard: the GLOBAL_CONSTRAINT bans crowds, so a group scene
    # (G##) rendered without a real blocking entry produces unconstrained cloned
    # crowds (measured 2026-10-27: 3-25 duplicated extras in every clip).
    is_group_scene = row["scene"].startswith("G")
    if is_group_scene and not blocking and args.queue and not args.force:
        print(f"GUARD: {args.chunk} is a group scene with no usable blocking — "
              f"refusing to queue (the no-crowd constraint would be a lie). "
              f"Draft blocking first (tools/vlm_blocking.py --chunk {args.chunk} --write) "
              f"or pass --force.")
        return

    text = build_prompt(row, subjects, 1 if plate else 0, dialogue, people, blocking,
                        group_scene=is_group_scene, shot_presence=args.shot_presence)

    # prompt lint: never queue a prompt that carries an error string or a
    # dead <Video N> reference — lint failures abort BOTH dry-run and queue.
    problems = lint_prompt(text, mode="audio_only")
    if problems:
        print(f"GUARD: prompt lint failed for {args.chunk}:")
        for p in problems:
            print(f"  - {p}")
        if not args.force:
            print("aborting (pass --force to override)")
            return

    (RUN_DIR / "prompts").mkdir(parents=True, exist_ok=True)
    (RUN_DIR / "graphs").mkdir(parents=True, exist_ok=True)
    # A DRY RUN must never overwrite a take's record. Measured 2026-11-05: a no-queue inspection
    # run of this driver replaced the graph (and prompt file) of S03-c01's ALREADY-RENDERED take 1,
    # so the review page would have shown a prompt that take was never rendered with. Prompt/graph
    # files are the provenance of a take; only the path that actually queues may write them.
    dry_suffix = "" if args.queue else ".dryrun"
    (RUN_DIR / "prompts" / f"{args.chunk}{dry_suffix}.txt").write_text(text, encoding="utf-8")

    sheet_names = [T.sheet_path(n).name for n in subjects]

    if not args.queue:
        g = build_audio_only_graph(row, sheet_names, plate_names, audio_name)
        g, tag = finalize_graph(g, args.chunk, args.take, text, args.seed)
        (RUN_DIR / "graphs" / f"{tag}{dry_suffix}.json").write_text(json.dumps(g, indent=2))
        inp = g["136"]["inputs"]
        print("DRY RUN OK — nothing queued, and no take record touched")
        print("  wrote (dry):", RUN_DIR / "prompts" / f"{args.chunk}{dry_suffix}.txt")
        print("  prefix:", tag, " seed:", g["129"]["inputs"]["noise_seed"])
        print("  subjects:", subjects)
        print("  plate:", plate_names)
        print("  ref_audios:", inp.get("ref_audios.ref_audio_0"), "->", audio_name)
        print("  any ref_videos left:", [k for k in inp if k.startswith("ref_video")])
        print("  any <Video 1> in prompt:", "<Video 1>" in text)
        return

    # build + upload the audio-only track, then the sheets + plate
    apath = build_chunk_audio(row)
    if apath is None and not args.audio:
        print("no source audio for this chunk; abort"); return
    if apath is not None:
        audio_name = F.upload(apath)
        print(f"  uploaded audio -> {audio_name}", flush=True)
    up_sheets = [F.upload(T.sheet_path(n)) for n in subjects]
    up_plates = [F.upload(plate)] if plate else []
    g = build_audio_only_graph(row, up_sheets, up_plates, audio_name)
    g, tag = finalize_graph(g, args.chunk, args.take, text, args.seed)
    (RUN_DIR / "graphs" / f"{tag}.json").write_text(json.dumps(g, indent=2))
    try:
        F.api("/prompt", {"prompt": g}, timeout=90)
        print(f"QUEUED {tag} ({len(up_sheets)} sheets + {len(up_plates)} plate, "
              f"audio {audio_name}, seed {g['129']['inputs']['noise_seed']})")
    except Exception as e:  # noqa: BLE001
        # ALWAYS print the HTTP body: a bare "HTTP Error 400: Bad Request" hides the one line that
        # names the fault (measured 2026-11-05: `value_not_in_list: lora_name ... not in (list of
        # length 855)` — a refiled LoRA — and the body was the only place it appeared).
        body = ""
        if hasattr(e, "read"):
            try:
                body = (e.read() or b"").decode("utf-8", "replace")
            except Exception:  # noqa: BLE001
                body = ""
        print(f"queue failed: {e}")
        if body:
            print("  server said:", body[:800])


if __name__ == "__main__":
    main()
