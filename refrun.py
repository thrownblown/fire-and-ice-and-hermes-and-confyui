"""refrun — ref2va (reference-video) full run, the successor to fullrun.py's FL2VA.

Where fullrun drives MiniMaxH3ImageToVideo from two stills and a 3-field
prompt, this drives MiniMaxH3ReferenceToVideo from the preprocessed 24fps
reference clip under refs/ plus the per-shot stills and the clip's own audio,
with a 6-field prompt (subject_definitions / summary / retention_analysis /
detailed_description / overall_soundscape / non_diegetic_music).

It imports fullrun for the loaders and trait helpers (ROSTER, people_phrase,
soundscape_line, style_line, camera_move, on_screen, first_sentence, jl, api,
upload, ...) so the roster and captions stay the single source of truth.

Run:
  .venv/Scripts/python.exe refrun.py prompt  --chunk S05-c04        # dry-run, no GPU
  .venv/Scripts/python.exe refrun.py render  --chunk S05-c04        # upload + queue
  .venv/Scripts/python.exe refrun.py render  --scene S05 --limit 3  # throttle
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

import fullrun as F

# ------------------------------------------------------------------ validate
def validate_ref_prompt(text):
    """6-field ref2va contract check (parallel to fullrun.validate_prompt, which
    targets the 3-field FL2VA form)."""
    issues = []
    for field in ("subject_definitions:", "summary:", "retention_analysis:",
                  "detailed_description:", "overall_soundscape:", "non_diegetic_music:"):
        if field not in text:
            issues.append("missing field '%s'" % field)
    if text.count("<d>") != text.count("</d>"):
        issues.append("unbalanced <d> ... </d> tags")
    spoken = re.findall(r"<d>\[(\w+)\]\s*(.*?)</d>", text, re.S)
    for _, s in spoken:
        if len(s) > 130:
            issues.append("line longer than 130 chars: '%s...'" % s[:40])
    if sum(len(s) for _, s in spoken) > 200:
        issues.append("more than 200 chars of dialogue in one clip; split the shot")
    if " <Video 1>" not in text:
        issues.append("missing <Video 1> reference")
    return issues

ROOT = Path(r"E:/FNI")
RUN = ROOT / "refrun"
GRAPH_DIR = RUN / "graphs"
PROMPT_DIR = RUN / "prompts"
INPUT_DIR = RUN / "input"
OUTPUT_DIR = RUN / "output"
REFS = ROOT / "refs"

# ref2va graph constants
REF2VA_WEIGHT = "h3/minimax_h3_ref2va_pruned_int8_convrot.safetensors"
REF2VA_LORA = "h3/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors"
STEPS_LIGHTNING = 4
STEPS_FULL = 20
REF_IMAGE_SIZE = "match"       # "max" = stronger identity, slower
V_VAE = "minimax_h3_video_vae_int8_convrot.safetensors"
A_VAE = "minimax_h3_audio_vae_fp32.safetensors"
CLIP = "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"

# How a chunk maps to a reference video: the chunk's shots are concatenated into
# one 24fps ref clip so <Video 1> is the actual source motion/identity of the
# chunk, not just one shot. Kept as a helper so it can be swapped for a single
# shot later.
MAX_REF_IMAGES = 8


def ref_video_name(chunk_id: str) -> str:
    return f"{chunk_id}_ref.mp4"


def build_ref_video(row) -> bool:
    """Concatenate a chunk's shot refs into one chunk-level ref clip.

    Returns True if the clip exists (or was built). Uses the concat demuxer so
    no re-encode; the per-shot refs are already 24fps / 1280x720 / same codec.
    """
    dst = REFS / ref_video_name(row["chunk_id"])
    if dst.exists() and dst.stat().st_size > 0:
        return True
    shots = [REFS / f"shot_{n}.mp4" for n in row["shot_nums"]]
    shots = [s for s in shots if s.exists() and s.stat().st_size > 0]
    if not shots:
        return False
    if len(shots) == 1:
        import shutil
        shutil.copy(shots[0], dst)
        return True
    lst = RUN / "_concat.txt"
    lst.write_text("".join(f"file '{s.as_posix()}'\n" for s in shots), encoding="utf-8")
    out = subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(dst),
    ], capture_output=True, text=True)
    return out.returncode == 0 and dst.exists() and dst.stat().st_size > 0


# ------------------------------------------------------------------ prompt
def subject_lines(subjects):
    """subject_definitions block: <Subject N> + <Picture N> for each named lead.

    subjects is a list of (name, traits, pic_indices). Traits come from the
    roster (curated) so we never re-describe a character from the VLM pass.
    """
    lines = []
    for i, (name, traits, pics) in enumerate(subjects, 1):
        pic = ", ".join(f"<Picture {p}>" for p in sorted(pics))
        extra = f" She is the one in <Video 1>." if i == 1 else ""
        lines.append(f"<Subject {i}> is {name}, {traits}, shown in {pic}.{extra}")
    return "\n".join(lines)


def retention_lines(subjects, n_shots):
    lines = []
    for i, (name, traits, pics) in enumerate(subjects, 1):
        appear = ", ".join(f"[Shot {s}]" for s in range(1, n_shots + 1))
        lines.append(f"<Subject {i}>: fully_preserved — keep {traits} consistent "
                     f"across {appear} and <Video 1>.")
    lines.append("<Video 1>: attribute_transfer — carry the posture, facial "
                 "performance, and exact spoken dialogue and delivery into the clip.")
    lines.append("Dialogue audio of <Video 1>: fully_copy — reuse the spoken lines and timing.")
    return "\n".join(lines)


def build_ref_prompt(row, caps, people, dialogue_by_id):
    """6-field ref2va prompt for one chunk."""
    subjects = []          # (name, traits, [picture indices])
    pic_of = {}            # name -> picture index
    n_pic = 0
    # Stills as <Picture N>, in shot order; first still of each shot is the anchor.
    for sid, snum in zip(row["shots"], row["shot_nums"]):
        stills = F.stills_for(snum)
        if stills and n_pic < MAX_REF_IMAGES:
            n_pic += 1
            pic_of[sid] = n_pic
    # Named leads -> <Subject N>. A speaker with roster traits becomes a subject;
    # the first on-screen named lead is Subject 1 (the <Video 1> sitter).
    stamped = set(row["stamped_names"])
    order = []
    for spk in row["speakers"]:
        if spk not in order:
            order.append(spk)
    # physical traits: roster first, else the character pass
    for spk in order:
        traits = F.ROSTER.get(spk)
        if not traits:
            # fall back to the pass for the first shot this speaker is on-screen
            for sid in row["shots"]:
                plist = people.get(sid, {}).get("people") or []
                if any((p.get("name") or "").upper() == spk for p in plist):
                    t = F.people_phrase(plist)
                    if t:
                        traits = t
                    break
        if not traits:
            continue
        # pictures for this subject = stills of shots they appear in
        pics = []
        for sid, snum in zip(row["shots"], row["shot_nums"]):
            if sid in pic_of:
                plist = people.get(sid, {}).get("people") or []
                on_sc = F.on_screen(spk, sid, people.get(sid, {}), stamped)
                if on_sc or spk in stamped:
                    pics.append(pic_of[sid])
        if not pics and pic_of:
            pics = [next(iter(pic_of.values()))]
        subjects.append((spk, traits, list(dict.fromkeys(pics)) or [1]))

    if not subjects:
        # no named lead -> nothing to pin; still emit a minimal subject
        subjects = [("the person shown in <Video 1>", "as in the reference video", [1])]

    sd = subject_lines(subjects)
    summ = ("[video editing + audio reuse] A single continuous 2D-animated rotoscope "
            f"scene of {subjects[0][0]} in <Video 1>, preserving appearance from the "
            "reference pictures and the timing, posture, and speech of the reference video.")
    rt = retention_lines(subjects, len(row["shots"]))

    # detailed_description: style + per-shot [Shot N] blocks with dialogue.
    style = F.style_line(row["location"])
    shot_lines = []
    for idx, (sid, snum) in enumerate(zip(row["shots"], row["shot_nums"]), 1):
        off = people.get(sid, {}).get("_off", 0.0)
        # camera move
        comp = {"shot_type": row["shot_type"][idx - 1], "angle": row["angle"][idx - 1]}
        cam = F.camera_move(comp, idx, len(row["shots"]))
        plist = people.get(sid, {}).get("people") or []
        phrase = F.people_phrase(plist)
        bits = []
        if idx == 1:
            bits.append(f"[Shot 1] {cam} {subjects[0][0]}.")
        else:
            mm, ss = divmod(off, 60)
            bits.append(f"[Shot {idx}] At {int(mm):02d}:{ss:06.3f}, {cam}")
        # dialogue for this shot
        sidx = {sub[0]: i + 1 for i, sub in enumerate(subjects)}
        for lid in row["line_ids"]:
            r = dialogue_by_id.get(lid)
            if not r:
                continue
            if not (people.get(sid, {}).get("_t0", 0) <=
                    (F.sec(r["start"]) + F.sec(r["end"])) / 2 < people.get(sid, {}).get("_t1", 0)):
                continue
            spk = r["speaker"]
            tag = f"(S{sidx[spk]})" if spk in sidx else "(S1)"
            desc = F.ROSTER.get(spk)
            if F.on_screen(spk, sid, people.get(sid, {}), stamped):
                bits.append(f"<Subject {sidx.get(spk, 1)}> {tag} says: <d>[English] {r['text']}</d>")
            else:
                bits.append(f"<Subject {sidx.get(spk, 1)}> {tag} speaks off-screen: "
                            f"<d>[English] {r['text']}</d>")
        shot_lines.append(" ".join(b for b in bits if b))

    dd = f"{style}\n\n" + "\n\n".join(shot_lines)
    return "\n\n".join([
        f"# ref_video: {ref_video_name(row['chunk_id'])}",
        "subject_definitions:",
        sd,
        "",
        "summary:",
        summ,
        "",
        "retention_analysis:",
        rt,
        "",
        "detailed_description:",
        dd,
        "",
        "overall_soundscape:",
        F.soundscape_line(row),
        "",
        "non_diegetic_music:",
        F.music_line(row["music"]),
    ])


# ------------------------------------------------------------------ graph
def build_ref_graph(row, still_names, use_lightning=True):
    """Build the MiniMaxH3ReferenceToVideo API graph from scratch.

    still_names is a list of uploaded image filenames ordered Picture 1..N.
    """
    steps = STEPS_LIGHTNING if use_lightning else STEPS_FULL
    g = {}
    def node(nid, class_type, inputs, title=None):
        g[str(nid)] = {"inputs": inputs, "class_type": class_type,
                       "_meta": {"title": title or class_type}}

    node(92, "SaveVideo", {"filename_prefix": f"video/{row['chunk_id']}_ref_t01",
                            "format": "auto", "format.codec": "auto", "codec": "auto",
                            "video": ["130", 0]}, "Save Video")
    node(115, "ResolutionSelector", {"aspect_ratio": "16:9 (Widescreen)",
                                      "megapixels": 0.98, "multiple": 32}, "Resolution Selector")
    node(119, "VAELoader", {"vae_name": V_VAE}, "Load VAE")
    node(120, "VAELoader", {"vae_name": A_VAE}, "Load Audio VAE")
    node(121, "VAEDecodeAudio", {"samples": ["125", 0], "vae": ["120", 0]}, "VAE Decode Audio")
    node(122, "VAEDecode", {"samples": ["125", 0], "vae": ["119", 0]}, "VAE Decode")
    node(123, "KSamplerSelect", {"sampler_name": "res_multistep"}, "KSamplerSelect")
    node(124, "BasicScheduler", {"scheduler": "simple", "steps": ["142", 0],
                                  "denoise": 1.0, "model": ["127", 0]}, "BasicScheduler")
    node(125, "SamplerCustomAdvanced", {"noise": ["129", 0], "guider": ["126", 0],
                                         "sampler": ["123", 0], "sigmas": ["124", 0],
                                         "latent_image": ["136", 1]}, "SamplerCustomAdvanced")
    node(126, "BasicGuider", {"model": ["141", 0], "conditioning": ["136", 0]}, "Basic Guider")
    node(127, "UNETLoader", {"unet_name": REF2VA_WEIGHT, "weight_dtype": "default"}, "Load Diffusion Model")
    node(128, "CLIPLoader", {"clip_name": CLIP, "type": "minimax", "device": "default"}, "Load CLIP")
    node(129, "RandomNoise", {"noise_seed": row["seed"]}, "RandomNoise")
    node(130, "CreateVideo", {"fps": 24, "bit_depth": 8, "color_space": "sRGB",
                               "codec": "none", "images": ["122", 0], "audio": ["121", 0]}, "Create Video")
    node(131, "ComfyMathExpression",
         {"expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
          "values.a": ["132", 0]}, "Math Expression")
    node(132, "PrimitiveFloat", {"value": row["h3_seconds"]}, "Float (Duration)")

    # reference wiring: stills + the ref video (GetVideoComponents)
    ref_images = {}
    for i, name in enumerate(still_names):
        nid = 137 + i
        node(nid, "LoadImage", {"image": name}, f"Load Image {i}")
        ref_images[f"ref_images.ref_image_{i}"] = [str(nid), 0]
    vid_pic_nid = 137 + len(still_names)
    node(148, "LoadVideo", {"file": ref_video_name(row["chunk_id"]), "video-preview": ""}, "Load Video")
    node(147, "GetVideoComponents", {"video": ["148", 0]}, "Get Video Components")

    node(136, "MiniMaxH3ReferenceToVideo", {
        "prompt": ["138", 0],
        "width": ["115", 0], "height": ["115", 1], "length": ["131", 1],
        "ref_image_size": REF_IMAGE_SIZE,
        "clip": ["128", 0], "vae": ["119", 0], "audio_vae": ["120", 0],
        **ref_images,
        "ref_videos.ref_video_0": ["147", 0],
        "ref_video_audios.ref_video_audio_0": ["147", 1],
    }, "MiniMax H3 Reference to Video")

    node(138, "PrimitiveStringMultiline", {"value": ""}, "Input Text (Prompt)")

    # lightning LoRA switch
    node(141, "ComfySwitchNode", {"switch": ["146", 0], "on_false": ["127", 0],
                                   "on_true": ["145", 0]}, "If/Else Switch (model)")
    node(142, "ComfySwitchNode", {"switch": ["146", 0], "on_false": ["143", 0],
                                   "on_true": ["144", 0]}, "If/Else Switch (Steps)")
    node(143, "PrimitiveInt", {"value": STEPS_FULL}, "Int (Full)")
    node(144, "PrimitiveInt", {"value": STEPS_LIGHTNING}, "Int (Lightning)")
    node(145, "LoraLoaderModelOnly", {"lora_name": REF2VA_LORA, "strength_model": 1.0,
                                       "model": ["127", 0]}, "Load LoRA")
    node(146, "PrimitiveBoolean", {"value": use_lightning}, "Enable Lightning LoRA")
    return g


# ------------------------------------------------------------------ commands
def load_rows(args):
    rows = [json.loads(l) for l in F.CHUNK_LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    if getattr(args, "chunk", None):
        rows = [r for r in rows if r["chunk_id"] == args.chunk]
    if getattr(args, "scene", None):
        want = set(args.scene.split(","))
        rows = [r for r in rows if r["scene"] in want]
    if getattr(args, "limit", None):
        rows = rows[: args.limit]
    return rows


def load_context():
    people = {r["shot_id"]: r for r in F.jl(ROOT / "manifests" / "character_pass.jsonl")}
    for r in F.jl(ROOT / "manifests" / "character_names.jsonl"):
        tgt = people.setdefault(r["shot_id"], {"shot_id": r["shot_id"], "people": []})
        for i, p in enumerate(tgt.get("people") or []):
            src = r.get("people") or []
            if i < len(src) and src[i].get("name"):
                p["name"] = src[i]["name"]
    shots = {s["shot_id"]: s for s in F.jl(ROOT / "shots.jsonl")}
    dialogue_by_id = {r["id"]: r for r in csv.DictReader(F.TSV.open(encoding="utf-8"), delimiter="\t")}
    for row in load_rows(argparse.Namespace(chunk=None, scene=None, limit=0)):
        t = shots[row["shots"][0]]["start_pts"] / 24000
        for sid in row["shots"]:
            s = shots[sid]
            people.setdefault(sid, {})["_t0"] = s["start_pts"] / 24000
            people[sid]["_t1"] = s["end_pts"] / 24000
            people[sid]["_off"] = s["start_pts"] / 24000 - t
    return people, dialogue_by_id


def cmd_prompt(args):
    people, dialogue = load_context()
    for d in (RUN, GRAPH_DIR, PROMPT_DIR, INPUT_DIR, OUTPUT_DIR):
        d.mkdir(parents=True, exist_ok=True)
    caps = F.load_captions()
    for row in load_rows(args):
        if not build_ref_video(row):
            print(f"  {row['chunk_id']}: no ref video, skipping")
            continue
        text = build_ref_prompt(row, caps, people, dialogue)
        for v in validate_ref_prompt(text):
            print(f"  {row['chunk_id']} prompt violation: {v}")
        (PROMPT_DIR / (row["chunk_id"] + ".txt")).write_text(text, encoding="utf-8")
        # stills for the graph
        still_names = []
        for snum in row["shot_nums"]:
            s = F.stills_for(snum)
            if s:
                still_names.append(f"{row['chunk_id']}_{snum}_f00000.jpg")
        g = build_ref_graph(row, still_names)
        g["138"]["inputs"]["value"] = text
        (GRAPH_DIR / (row["chunk_id"] + ".json")).write_text(json.dumps(g, indent=2), encoding="utf-8")
        print(f"  {row['chunk_id']}: {len(still_names)} stills, video {ref_video_name(row['chunk_id'])}, "
              f"prompt -> {PROMPT_DIR / (row['chunk_id'] + '.txt')}")
    print("dry-run complete; nothing queued")


def cmd_render(args):
    people, dialogue = load_context()
    for d in (RUN, GRAPH_DIR, PROMPT_DIR, INPUT_DIR, OUTPUT_DIR):
        d.mkdir(parents=True, exist_ok=True)
    caps = F.load_captions()
    rows = load_rows(args)
    print(f"to render: {len(rows)} chunks")
    for row in rows:
        if not build_ref_video(row):
            print(f"  {row['chunk_id']}: no ref video, skipping")
            continue
        text = build_ref_prompt(row, caps, people, dialogue)
        # upload ref video + stills
        names = []
        try:
            names.append(F.upload(REFS / ref_video_name(row["chunk_id"])))
        except Exception as e:  # noqa: BLE001
            print(f"  {row['chunk_id']} ref-video upload failed: {e}")
            continue
        still_names = []
        for snum in row["shot_nums"]:
            s = F.stills_for(snum)
            if s:
                try:
                    still_names.append(F.upload(s[0]))
                except Exception as e:  # noqa: BLE001
                    print(f"  {row['chunk_id']} still upload failed: {e}")
        g = build_ref_graph(row, still_names)
        g["138"]["inputs"]["value"] = text
        try:
            F.api("/prompt", {"prompt": g}, timeout=90)
            print(f"  {row['chunk_id']}: queued ({len(still_names)} stills, video ref)")
        except Exception as e:  # noqa: BLE001
            print(f"  {row['chunk_id']} queue failed: {e}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("prompt", cmd_prompt), ("render", cmd_render)):
        p = sub.add_parser(name)
        p.add_argument("--chunk")
        p.add_argument("--scene")
        p.add_argument("--limit", type=int)
        p.set_defaults(func=fn)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()