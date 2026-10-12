"""FNI full-film H3 pipeline: plan -> caption -> prompt -> graph -> render -> collect.

One script, resumable, local-first. Every stage writes a ledger so a crash resumes
instead of restarting, and every stage is a subcommand so you can run them apart.

  plan      shots -> scenes -> chunks, writes manifests/fullrun_chunks.jsonl
  caption   local qwen3-vl-8b (LM Studio) captions every still a chunk needs
  prompt    FL2VA prompt text + graph JSON per chunk
  render    upload keyframes, queue graphs on the 5090, throttled
  collect   download renders, stitch per scene, frame metrics
  status    progress across all of the above

Decisions baked in (see DECISIONS at the bottom of this file):
  mode FL2VA, 20 steps, int8, 864x480, 24fps, deterministic per-chunk seed.

Usage
  python fullrun.py plan
  python fullrun.py caption --limit 20
  python fullrun.py prompt --scenes S03
  python fullrun.py render --scenes S03 --max-pending 8
  python fullrun.py collect --scenes S03
  python fullrun.py status
"""
import argparse
import base64
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zlib
from pathlib import Path

ROOT = Path(r"E:/FNI")
COMFY = os.environ.get("FNI_COMFY", "http://100.104.7.72:8188")
LM = os.environ.get("FNI_LM", "http://127.0.0.1:1234/v1/chat/completions")
VLM_MODEL = os.environ.get("FNI_VLM", "qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s")

RUN = ROOT / "fullrun"
CHUNK_LEDGER = RUN / "chunks.jsonl"
CAPTION_CACHE = RUN / "captions.jsonl"
RENDER_LEDGER = RUN / "renders.jsonl"
GRAPH_DIR = RUN / "graphs"
PROMPT_DIR = RUN / "prompts"
INPUT_DIR = RUN / "input"
OUTPUT_DIR = RUN / "output"
STITCH_DIR = RUN / "stitched"
STILLS = ROOT / "stills" / "full"
TEMPLATE = ROOT / "graphs" / "video_minimax_h3_r2v.json"
TSV = ROOT / "script" / "dialogue-timeline.tsv"
BEATSHEET = ROOT / "beat-sheet.md"

H3_WEIGHT = "h3/minimax_h3_fl2va_pruned_int8_convrot.safetensors"
STEPS = 20
WIDTH, HEIGHT = 864, 480
FPS = 24
CHUNK_MIN_S, CHUNK_MAX_S = 4.0, 15.0
CHUNK_MIN_SHOTS, CHUNK_MAX_SHOTS = 2, 3

# ---------------------------------------------------------------- source data


def jl(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def sec(tc):
    h, mi, rest = tc.replace(",", ".").split(":")
    return int(h) * 3600 + int(mi) * 60 + float(rest)


def tc_of(sec_):
    m, s = divmod(sec_, 60)
    h, m = divmod(int(m), 60)
    return "%02d:%02d:%06.3f" % (h, m, s)


def h3_frames(seconds):
    """Snap a duration onto H3's 17k+5 grid, clamped to the published 4-15s range."""
    seconds = max(CHUNK_MIN_S, min(CHUNK_MAX_S, seconds))
    raw = max(5, round(seconds * FPS))
    return raw + (5 - (raw % 17)) % 17


def seed_for(chunk_id):
    """Deterministic per-chunk seed, so a re-run reproduces the same render."""
    return zlib.crc32(chunk_id.encode()) & 0x7FFFFFFFFFFFFFFF


def _tc_min(tc):
    """'00:04:44' -> seconds. Tolerates the en dashes used in the tables."""
    tc = tc.replace("–", "-").replace("—", "-").replace(",", ".")
    h, mi, rest = tc.strip().split(":")
    return int(h) * 3600 + int(mi) * 60 + float(rest)


def parse_beatsheet():
    """scene id -> {title, start, end, lines, cast, location, music}, plus the
    action-only stretches as their own pseudo-scenes so no footage is orphaned."""
    out, gaps = {}, []
    if not BEATSHEET.exists():
        return out, gaps
    text = BEATSHEET.read_text(encoding="utf-8")
    in_gaps = False
    for line in text.splitlines():
        if line.startswith("## Long action-only stretches"):
            in_gaps = True
            continue
        if in_gaps and line.startswith("## "):
            in_gaps = False
        if in_gaps and line.strip().startswith("- "):
            m = re.search(r"(\d\d:\d\d:\d\d)\D+(\d\d:\d\d:\d\d)", line)
            if m:
                gaps.append((_tc_min(m.group(1)), _tc_min(m.group(2))))
            continue
        if not line.startswith("| S"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 7:
            continue
        sid, title, span, lines, cast, loc, music = cells[:7]
        m = re.search(r"(\d\d:\d\d:\d\d)\D+(\d\d:\d\d:\d\d)", span)
        if not m:
            continue
        out[sid] = {
            "title": title, "start": _tc_min(m.group(1)), "end": _tc_min(m.group(2)),
            "lines": lines, "cast": cast, "location": loc, "music": music,
        }
    return out, gaps


# Beat-sheet music is mood words. H3 wants instrumentation, tempo, dynamics.
MUSIC_MAP = [
    (r"battle|raid|march|climax|assault|violent", "Heavy percussion and low brass at a fast, driving tempo, rising steadily in volume through the passage and cutting off hard at the end."),
    (r"ominous|dread|menace|sinister|psychic|eerie|doomed|grave", "Low sustained strings and slow woodwind pulses at a slow tempo, with sparse bell tones above; dynamics stay quiet and grow only slightly."),
    (r"tender|light|wry|gentle|resolve|reunion", "Soft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close."),
    (r"lively|playful|warm", "Light hand percussion and a plucked string figure at a moderate tempo, joined by a brief flute phrase that repeats once."),
    (r"ghostly|spirit|mourn|somber|tragic", "Solo flute and bowed vibraphone at a slow tempo with wide spacing between notes, held at very low volume."),
    (r"soaring|heroic|hopeful", "Full string section and brass at a moderate tempo, swelling to a broad sustained chord and fading."),
]


def music_line(scene_music, fallback=False):
    for pat, line in MUSIC_MAP:
        if re.search(pat, (scene_music or "").lower()):
            return line
    return ("Low sustained strings at a slow tempo with widely spaced woodwind notes, "
            "dynamics held quiet throughout.")


# ------------------------------------------------------------------ characters
# Roster traits, used for the speaking subject. Names stay out of the description
# per the H3 spec: identity is physical traits, never a character name.
ROSTER = {
    "LARN": ("a young athletic man with shoulder-length blond hair, bare-chested in a brown "
             "loincloth with a gold buckle, arm bands and black boots, carrying a sword"),
    "TEEGRA": ("a young woman with pale skin and very long dark hair in a light purple "
               "sleeveless top and skirt"),
    "DARKWOLF": ("an older warrior, very large and heavily muscled, dark weathered skin, long "
                 "black hair, bare-chested with a loincloth and wrist and ankle bands, carrying a sword"),
    "NEKRON": ("a tall gaunt pale young man with sharp features and long hair, in dark robes, "
               "carrying a staff"),
    "JULIANA": ("an older woman with long straight black hair and crimson lips, in a deep purple "
                "long-sleeved gown with long silver dagger-shaped earrings"),
    "JAROL": ("an older king with gray-white hair and a full beard, in regal robes"),
    "TARO": ("a young prince with dark hair, in Fire Keep dress with a high collar"),
    "ROLIEL": ("a woman with long red hair, fair skin, red-orange eyes, a white flowing robe with "
              "a dark belt, a blue teardrop pendant and matching earrings and bracelets"),
    "OTWA": ("a young man of gentle face and immense build, in simple dark travel clothes"),
    "SHAITAN": ("a small dark animal-like creature with bright eyes"),
    "TUTOR": ("an older man in plain Fire Keep robes"),
    "ENVOY": ("a hooded subhuman envoy in a dark robe with yellow eyes and dark skin"),
    "SPIRIT": ("a translucent pale humanoid figure with a faint glow"),
    "NARRATOR": None,
    "VILLAGE CHIEF": ("an older man in rough furs"),
    "VILLAGE ELDER": ("an older man in rough furs"),
    "SUBHUMAN": ("a hunched fur-covered ape-like humanoid with primitive weapons"),
    "SUBHUMAN CAPTAIN": ("a large hunched fur-covered ape-like humanoid with heavy shoulder armor"),
}

STYLE_BY_LOCATION = [
    (r"jungle|woods|forest|hut", "2D-animated rotoscope painted animation in the style of a 1983 fantasy film: inked figures over lush painted jungle and forest backgrounds, dappled green and gold light"),
    (r"throne hall|ice peak|keep|fortress|citadel", "2D-animated rotoscope painted animation in the style of a 1983 fantasy film: inked figures over cool-toned painted stone interiors, cold blue-grey cavern light"),
    (r"camp|tent|village|ruin|dock|harbor|plain|ground|outdoor|cliff|volcano|lava", "2D-animated rotoscope painted animation in the style of a 1983 fantasy film: inked figures over wide painted exteriors, wind and dust in the air, hard natural light"),
    (r"cell|dungeon|prison", "2D-animated rotoscope painted animation in the style of a 1983 fantasy film: inked figures over painted stone interiors lit by a single weak source, deep shadow"),
]


def style_line(location):
    for pat, line in STYLE_BY_LOCATION:
        if re.search(pat, (location or "").lower()):
            return line
    return ("2D-animated rotoscope painted animation in the style of a 1983 fantasy film: inked "
            "figures over painted backgrounds, broad graphic acting with strong gesture and clear "
            "body poses")


# ----------------------------------------------------------------- scene spans
# The dialogue timeline gives each scene a first and last cue. Scene N owns the
# footage from the midpoint to scene N-1's last cue up to the midpoint to scene
# N+1's first cue, so every shot in the film lands in exactly one scene.
def scene_spans(dialogue, beat, gaps):
    """Every shot in the film belongs to exactly one span.

    Dialogue scenes take their own first/last cue. The action-only stretches the
    beat sheet lists become their own spans (G01, G02, ...) so the long silent
    passages are not swallowed by the scene that happens to follow them. Anything
    still uncovered goes to the nearest span by midpoint distance.
    """
    sids = sorted({r["scene"] for r in dialogue})
    wins = {}
    for sid in sids:
        rows = [r for r in dialogue if r["scene"] == sid]
        wins[sid] = (min(sec(r["start"]) for r in rows), max(sec(r["end"]) for r in rows))

    spans = {}
    for sid in sids:
        spans[sid] = {"start": wins[sid][0], "end": wins[sid][1],
                      "kind": "dialogue", "title": beat.get(sid, {}).get("title", ""),
                      "location": beat.get(sid, {}).get("location", ""),
                      "music": beat.get(sid, {}).get("music", ""),
                      "cast": beat.get(sid, {}).get("cast", "")}
    for i, (a, b) in enumerate(sorted(gaps), 1):
        spans["G%02d" % i] = {"start": a, "end": b, "kind": "action",
                              "title": "action stretch", "location": "", "music": "",
                              "cast": ""}

    # trim dialogue spans so they stop before an action stretch begins
    for sid in sids:
        for gid, g in spans.items():
            if gid.startswith("G") and g["start"] >= spans[sid]["start"] and g["start"] < spans[sid]["end"]:
                spans[sid]["end"] = g["start"]

    keys = list(spans)
    def nearest(t):
        return min(keys, key=lambda k: 0 if spans[k]["start"] <= t < spans[k]["end"]
                   else min(abs(t - spans[k]["start"]), abs(t - spans[k]["end"])))
    return spans, nearest


# ------------------------------------------------------------------- the beats
# Body-scale action, keyed on what the composition pass actually saw. These are
# staging choices for the remake, not claims about the source footage.
GESTURE = {
    "JULIANA": "She turns sharply toward the figure she is addressing, thrusts one arm out from "
               "her body, and holds it there with the hand open before drawing it back to her side.",
    "NEKRON": "He steps forward, throws one arm up and out with the palm turned up, then drives it "
              "back down to his side as his head snaps up.",
    "LARN": "He plants his feet, swings one arm up and across his body, and drives it down hard, "
            "his weight shifting onto the front foot.",
    "TEEGRA": "She steps toward the others, sweeps one arm outward above her shoulder, and brings "
              "it down to her side, her hair swinging across her shoulder with the movement.",
    "DARKWOLF": "He hefts his weapon arm up and back, holds it raised, then brings it down in a "
                "single heavy arc, his whole body turning with the swing.",
    "JAROL": "He rises a little from his seat, opens one hand at chest height in a measured "
             "gesture, and lowers it again as he settles back.",
    "TARO": "He steps forward, lifts a hand toward the figure before him, and holds it out while "
            "his head turns to follow.",
    "ROLIEL": "She leans in, one hand rising and falling with her words, her long red hair shifting "
              "across her shoulder as she turns her head.",
    "OTWA": "He shifts his weight, bends forward slightly, and straightens again, his shoulders "
            "rolling with the movement.",
    "ENVOY": "The hood dips forward a few degrees, then lifts again, the yellow glow of the eyes "
             "moving with the head.",
    "SUBHUMAN": "The hunched figure shifts its weight, one arm coming up and across its chest.",
    "TUTOR": "He turns his head to the side, one hand lifting in a small correcting gesture.",
    "SPIRIT": "The glowing figure drifts, its outline flickering as the arms spread slightly.",
    "SHAITAN": "The small creature shifts on its feet, head turning to follow the movement around it.",
}

LOCOMOTION = {
    "person running": "The figure runs, arms pumping and body leaning forward into the stride, the "
                      "whole frame carrying the motion.",
    "characters moving forward": "The figures advance toward the camera, growing in frame, arms and "
                                "shoulders swinging with the approach.",
    "person moving forward": "The figure moves forward, upper body tilted into the advance, one arm "
                            "reaching ahead.",
    "person walking": "The figure walks, the body rising and settling with each step and the arms "
                      "swinging at the sides.",
    "person moving": "The figure crosses the frame, the torso twisting to lead the movement and the "
                     "coat or robe trailing behind.",
    "person climbing": "The figure climbs, arms reaching and pulling the body upward, legs braced "
                       "against the surface.",
    "person falling": "The figure falls, body tumbling downward and out of the frame, limbs trailing.",
    "person crawling": "The figure crawls forward on hands and knees, shoulders rocking with the pull.",
    "person picking up weapon": "The figure reaches down, closes a hand around the weapon, and hauls "
                                "it up into a ready position, the whole body rising with it.",
}

EXPRESSION = {
    "changing facial expression": "The face changes hard through the passage, jaw and brow moving "
                                  "through more than one shape while the head turns with it.",
    "mouth opening": "The mouth opens wide and the head lifts, the jaw held open through the change "
                     "before it closes again.",
    "head tilting back": "The head tilts back and holds, the throat exposed, the shoulders lifting "
                         "with the motion.",
}

CAMERA_BY_TYPE = {
    "wide": "The camera pulls out with small amplitude at slow speed, opening the space around the figures.",
    "extreme wide": "The camera pulls out with large amplitude at slow speed, opening the space until the figures are small in it.",
    "medium": "The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage.",
    "close-up": "The camera pushes in with small amplitude at slow speed, tightening toward the face.",
    "extreme close-up": "The camera pushes in with large amplitude at slow speed, closing in until the frame is filled with the face.",
}

CAMERA_BY_ANGLE = {
    "low": "The camera stays low and tilts up slightly as the figure moves.",
    "high": "The camera looks down, holding above the figures as they move.",
    "bird's eye": "The camera looks straight down from above as the figures move below it.",
}


def camera_move(comp, idx, n_shots):
    """One move per shot. Falls back to the shot type when angle says nothing."""
    parts = []
    if comp.get("angle") in CAMERA_BY_ANGLE:
        parts.append(CAMERA_BY_ANGLE[comp["angle"]])
    if comp.get("shot_type") in CAMERA_BY_TYPE:
        parts.append(CAMERA_BY_TYPE[comp["shot_type"]])
    if idx == n_shots:
        parts.append("The move slows and stops as the figure settles.")
    return " ".join(parts) or "The camera holds the framing as the figure moves."


def action_beat(speakers_here, motion, plist, single_shot):
    """Body-scale action for one shot, driven by what the composition pass saw."""
    beats = []
    m = (motion or "").strip().lower()
    for key, text in LOCOMOTION.items():
        if key in m:
            beats.append(text)
            break
    if not beats:
        for key, text in EXPRESSION.items():
            if key in m:
                beats.append(text)
                break
    if not beats:
        for spk in speakers_here:
            g = GESTURE.get(spk)
            if g:
                beats.append(g)
                break
    if not beats and plist:
        crowd = " in a tight group" if len(plist) > 3 else ""
        if dominant_sex(plist) == "male":
            beats.append("He shifts his weight%s, turns his shoulders, and brings one arm up across "
                         "his chest before letting it fall." % crowd)
        else:
            beats.append("She turns her head%s, lifts one hand near her chest, and lowers it again, "
                         "her hair and clothing shifting with the movement." % crowd)
    if not beats:
        beats.append("The figure turns and steps, the body leading the movement and the clothing "
                     "trailing behind.")
    if single_shot:
        # Both bookends are the same framing, so the action is a departure and a
        # return: the extra motion still has to land on Picture 2.
        beats.append("The movement carries through and then settles back, and in the closing seconds "
                     "everything slows and stops.")
    return " ".join(beats)


# ------------------------------------------------------------------ still picking
def stills_for(shot_num):
    return sorted(STILLS.glob("shot_%s_f*.jpg" % shot_num))


def keyframes_for(group):
    """First still of the first shot, last still of the last shot."""
    f = stills_for(group[0]["shot_id"].split(":")[1])
    l = stills_for(group[-1]["shot_id"].split(":")[1])
    return (f[0] if f else None), (l[-1] if l else None)


def mid_still_for(shot_num):
    s = stills_for(shot_num)
    return s[len(s) // 2] if s else None


# --------------------------------------------------------------------- planning
def cmd_plan(args):
    shots = jl(ROOT / "shots.jsonl")
    dialogue = list(csv.DictReader(TSV.open(encoding="utf-8"), delimiter="\t"))
    beat, gaps = parse_beatsheet()
    comp = {r["shot_id"]: r for r in jl(ROOT / "manifests" / "composition_pass.jsonl")}
    people = {r["shot_id"]: r for r in jl(ROOT / "manifests" / "character_pass.jsonl")}
    names = {r["shot_id"]: r for r in jl(ROOT / "manifests" / "character_names.jsonl")}
    spans, nearest = scene_spans(dialogue, beat, gaps)

    RUN.mkdir(parents=True, exist_ok=True)
    for d in (GRAPH_DIR, PROMPT_DIR, INPUT_DIR, OUTPUT_DIR, STITCH_DIR):
        d.mkdir(parents=True, exist_ok=True)

    def scene_of(t0, t1):
        return nearest((t0 + t1) / 2)

    def sort_key(sid):
        m = re.search(r"(\d+)", sid)
        return (0, int(m.group(1))) if sid.startswith("S") else (1, int(m.group(1)))

    # group shots per span, then chunk
    by_scene = {}
    for s in shots:
        by_scene.setdefault(scene_of(s["start_pts"] / 24000, s["end_pts"] / 24000), []).append(s)

    rows = []
    for sid in sorted(by_scene, key=sort_key):
        group_shots = by_scene[sid]
        chunks = []
        cur, cur_d = [], 0.0
        for s in group_shots:
            d = s["duration_seconds"]
            if d > CHUNK_MAX_S:
                if cur:
                    chunks.append(cur)
                    cur, cur_d = [], 0.0
                chunks.append([s])
                continue
            if not cur:
                cur, cur_d = [s], d
                continue
            if (len(cur) >= CHUNK_MIN_SHOTS and cur_d + d > CHUNK_MAX_S) or len(cur) >= CHUNK_MAX_SHOTS:
                chunks.append(cur)
                cur, cur_d = [s], d
            else:
                cur.append(s)
                cur_d += d
        if cur:
            chunks.append(cur)

        meta = spans.get(sid, {})
        for i, g in enumerate(chunks, 1):
            cid = "%s-c%02d" % (sid, i)
            t0 = g[0]["start_pts"] / 24000
            dur = g[-1]["end_pts"] / 24000 - t0
            frames = h3_frames(dur)
            lines = [r for r in dialogue
                     if r["scene"] == sid
                     and g[0]["start_pts"] / 24000 <= (sec(r["start"]) + sec(r["end"])) / 2 < g[-1]["end_pts"] / 24000]
            stamped = set()
            for s in g:
                for p in names.get(s["shot_id"], {}).get("people") or []:
                    if p.get("name"):
                        stamped.add(p["name"].upper())
            rows.append({
                "chunk_id": cid,
                "scene": sid,
                "scene_kind": meta.get("kind", "dialogue"),
                "scene_title": meta.get("title", ""),
                "cast": meta.get("cast", ""),
                "location": meta.get("location", ""),
                "music": meta.get("music", ""),
                "shots": [s["shot_id"] for s in g],
                "shot_nums": [s["shot_id"].split(":")[1] for s in g],
                "src_start": tc_of(t0),
                "src_end": tc_of(g[-1]["end_pts"] / 24000),
                "src_duration": round(dur, 3),
                "h3_frames": frames,
                "h3_seconds": round(frames / FPS, 3),
                "seed": seed_for(cid),
                "line_ids": [r["id"] for r in lines],
                "speakers": sorted({r["speaker"] for r in lines}),
                "stamped_names": sorted(stamped),
                "shot_type": [comp.get(s["shot_id"], {}).get("shot_type", "") for s in g],
                "angle": [comp.get(s["shot_id"], {}).get("angle", "") for s in g],
                "motion": [comp.get(s["shot_id"], {}).get("motion", "") for s in g],
                "people_count": [len(people.get(s["shot_id"], {}).get("people") or []) for s in g],
            })

    with CHUNK_LEDGER.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    total_frames = sum(r["h3_frames"] for r in rows)
    print("chunks: %d  scenes: %d  h3 frames: %d  clip seconds: %.0f" %
          (len(rows), len({r['scene'] for r in rows}), total_frames, total_frames / FPS))
    print("gpu estimate at 0.9 s/frame: %.1f h (%.1f days)" %
          (total_frames * 0.9 / 3600, total_frames * 0.9 / 86400))
    sizes = {}
    for r in rows:
        k = len(r["shots"])
        sizes[k] = sizes.get(k, 0) + 1
    print("chunks by shot count:", dict(sorted(sizes.items())))
    print("chunks with dialogue: %d / %d" % (sum(1 for r in rows if r["line_ids"]), len(rows)))
    return rows


# --------------------------------------------------------------------- caption
def vlm_caption(path, prompt, max_tokens=220):
    b64 = base64.b64encode(Path(path).read_bytes()).decode()
    body = json.dumps({
        "model": VLM_MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}},
            {"type": "text", "text": prompt}]}],
        "max_tokens": max_tokens, "temperature": 0.2,
    }).encode()
    req = urllib.request.Request(LM, data=body, headers={"Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                return json.load(r)["choices"][0]["message"]["content"].strip()
        except Exception as e:  # noqa: BLE001
            if attempt == 2:
                return "ERROR: %s" % e
            time.sleep(3 * (attempt + 1))
    return "ERROR"


def load_captions():
    cache = {}
    if CAPTION_CACHE.exists():
        for r in jl(CAPTION_CACHE):
            cache[r["file"]] = r["text"]
    return cache


def cmd_caption(args):
    rows = [json.loads(l) for l in CHUNK_LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.scenes:
        want = set(args.scenes.split(","))
        rows = [r for r in rows if r["scene"] in want]
    if args.limit:
        rows = rows[:args.limit]
    cache = load_captions()

    # Only the two bookends are consumed by the prompt. The mid-stills were used
    # by an earlier draft of the action-beat logic; captioning them cost ~8h of
    # local GPU for text nothing read.
    todo = {}
    for r in rows:
        f, l = keyframes_for([{"shot_id": s} for s in r["shots"]])
        if f:
            todo.setdefault(f.name, f)
        if l:
            todo.setdefault(l.name, l)
    need = {k: v for k, v in todo.items() if k not in cache}
    print("keyframes needed: %d  already cached: %d  to caption: %d"
          % (len(todo), len(todo) - len(need), len(need)))

    from concurrent.futures import ThreadPoolExecutor

    # One caption pass at a time. Two processes writing this ledger duplicate work
    # and contend for the same local VLM slot, which is how the first attempt at a
    # delegated caption pass died on a model-load abort.
    lock_file = RUN / "caption.lock"
    try:
        fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
    except FileExistsError:
        print("another caption pass holds %s — delete it if that process is dead" % lock_file)
        return

    t0 = time.time()
    done = [0]
    lock = __import__("threading").Lock()

    def one(item):
        name, path = item
        cap = vlm_caption(path, "Describe this animation film still in 2-3 sentences: the "
                                "visible subject (sex, hair, costume, pose, gesture), the "
                                "framing, the background, and the lighting. Literal description "
                                "only. No names, no story guesses.")
        with lock:
            done[0] += 1
            i = done[0]
            if i % 20 == 0 or i == len(need):
                el = time.time() - t0
                print("  %d/%d  %.1f s each  eta %.0f min"
                      % (i, len(need), el / i, (len(need) - i) * el / i / 60), flush=True)
        return {"file": name, "text": cap}

    if need:
        with CAPTION_CACHE.open("a", encoding="utf-8") as fh, \
                ThreadPoolExecutor(max_workers=args.workers) as pool:
            for rec in pool.map(one, sorted(need.items())):
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
    lock_file.unlink(missing_ok=True)
    print("captions cached:", len(load_captions()))


# ---------------------------------------------------------------------- prompt
def first_sentence(cap):
    for end in (". ", ".\n"):
        if end in cap:
            return cap.split(end)[0] + "."
    return cap.rstrip(".") + "."


def person_traits(p):
    bits = [p.get("build") or "", p.get("hair") or "", p.get("skin") or "", p.get("clothing") or ""]
    return ", ".join(b for b in bits if b)


def people_phrase(plist, limit=3):
    """Distinct trait strings, deduped and capped.

    A crowd shot returns eight near-identical men. Writing all eight into the
    prompt wastes the word budget and confuses the model, so collapse repeats
    and say how many there are.

    A stamped person uses the curated roster traits instead of the VLM's. The
    character doc records cases where the VLM description was simply wrong (it
    called Teegra's costume a fur bikini; she wears a two-piece), so the
    curated line overrides the pass wherever the two disagree.
    """
    if not plist:
        return ""
    seen, uniq = set(), []
    for p in plist:
        roster = ROSTER.get((p.get("name") or "").upper())
        t = roster or person_traits(p)
        key = t.lower()
        if t and key not in seen:
            seen.add(key)
            uniq.append(t)
    if not uniq:
        return ""
    uniq = uniq[:limit]
    if len(seen) == 1 and len(plist) > 1:
        return "%s, and %d others with the same build and dress" % (uniq[0], len(plist) - 1)
    return "; ".join(uniq)


def dominant_sex(plist):
    m = sum(1 for p in plist if (p.get("sex") or "").lower().startswith("m"))
    w = len(plist) - m
    return "male" if m > w else "female"


def on_screen(spk, shot, people_row, stamped):
    """On-screen if stamped for the shot, or if it is the only visible person and
    the sex matches. Off-screen otherwise."""
    if spk in stamped:
        return True
    plist = people_row.get("people") or []
    if len(plist) == 1:
        sex = (plist[0].get("sex") or "").lower()
        want = "male" if spk not in ("TEEGRA", "JULIANA", "ROLIEL") else "female"
        return sex.startswith(want[0])
    return False


SOUNDSCAPE = [
    (r"jungle|woods|forest", "Birdsong and insect noise close to the mic, leaves and undergrowth moving, air moving through the canopy."),
    (r"throne hall|keep|hall|citadel|fortress|interior|hut|cave|stone", "Room reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement."),
    (r"camp|plain|ground|beach|cliff|volcano|lava|outdoor|field|mountain", "Wind across open ground, grit and small debris moving, cloth snapping, footsteps on hard ground."),
    (r"cell|dungeon|prison", "A tight damp space with almost no reverb, close breathing, water dripping, chain and cloth movement."),
]
DEFAULT_SOUND = ("Room tone and air movement throughout, cloth rustle with every body movement, "
                 "footsteps wherever anyone moves.")


def soundscape_line(row):
    hay = " ".join([row.get("location") or "", row.get("cast") or "", row.get("scene_title") or ""]).lower()
    for pat, line in SOUNDSCAPE:
        if re.search(pat, hay):
            return line
    return DEFAULT_SOUND


def build_prompt(row, caps, people, dialogue_by_id, names_row):
    sid = row["scene"]
    style = style_line(row["location"])
    loc = (row["location"] or "the scene").lower()
    instr = ("How the reference pictures align with the target video — Picture 1 (from Shot 1) "
             "aligns with the 0.00-second mark of the target video; Picture 2 (from Shot %d) "
             "aligns with the %.2f-second mark of the target video."
             % (len(row["shots"]), row["h3_seconds"]))

    stamped = set(row["stamped_names"])
    speaker_ids = {}
    for spk in row["speakers"]:
        if spk not in speaker_ids:
            speaker_ids[spk] = "(S%d)" % (len(speaker_ids) + 1)

    parts = []
    for idx, shot_id in enumerate(row["shots"], 1):
        off = people.get(shot_id, {}).get("_off", 0.0)
        bits = []
        if idx == 1:
            f, _ = keyframes_for([{"shot_id": s} for s in row["shots"]])
            cap = first_sentence(caps.get(f.name, "")) if f else ""
            lead = ("[Shot 1] %s." % style if cap else
                    "[Shot 1] %s. The opening frame matches <Picture 1>." % style)
            if cap:
                lead += " The opening frame matches <Picture 1>: %s" % cap
            bits.append(lead)
        else:
            mm, ss = divmod(off, 60)
            bits.append("[Shot %d] At %02d:%06.3f, the camera cuts to a new angle." % (idx, int(mm), ss))
        comp = {"shot_type": row["shot_type"][idx - 1], "angle": row["angle"][idx - 1]}
        bits.append(camera_move(comp, idx, len(row["shots"])))

        plist = people.get(shot_id, {}).get("people") or []
        phrase = people_phrase(plist)
        if phrase:
            bits.append("On screen: %s." % phrase)
        spk_here = []

        for lid in row["line_ids"]:
            r = dialogue_by_id.get(lid)
            if not r:
                continue
            # the line belongs to the shot that holds its midpoint
            if not (people.get(shot_id, {}).get("_t0", 0) <=
                    (sec(r["start"]) + sec(r["end"])) / 2 < people.get(shot_id, {}).get("_t1", 0)):
                continue
            spk = r["speaker"]
            desc = ROSTER.get(spk) or "an off-screen %s" % spk.lower()
            if on_screen(spk, shot_id, people.get(shot_id, {}), stamped):
                bits.append("%s %s says: <d>[English] %s</d>" % (desc, speaker_ids[spk], r["text"]))
                spk_here.append(spk)
            else:
                bits.append("%s %s speaks while off-screen: <d>[English] %s</d>"
                            % (desc, speaker_ids[spk], r["text"]))

        bits.append(action_beat(spk_here, row["motion"][idx - 1], plist,
                                len(row["shots"]) == 1))
        if idx == len(row["shots"]):
            bits.append("Only in the last seconds do these movements slow and stop, and the figure "
                        "comes to rest in the pose, spacing, framing, and lighting established by "
                        "<Picture 2>.")
        parts.append(" ".join(b for b in bits if b))

    text = "\n\n".join([
        instr,
        "integrated_multimodal_description: " + " ".join(parts),
        "overall_soundscape: " + soundscape_line(row),
        "non_diegetic_music: " + music_line(row["music"]),
    ])
    return text


def validate_prompt(text):
    """Mechanical H3 prompt contract check, adapted from OpenCineAgent's
    validate_video_prompt to FNI's integrated_multimodal_description grammar.

    Returns a list of violations (empty = valid). Non-fatal: callers log the
    violations and keep going, but a broken prompt is surfaced before it costs a
    GPU render, never silently passed. FNI emits multiple [Shot N], so unlike the
    source project we do NOT reject shots after [Shot 1].
    """
    issues = []
    if text.count("<d>") != text.count("</d>"):
        issues.append("unbalanced <d> ... </d> tags")
    spoken = re.findall(r"<d>\[(\w+)\]\s*(.*?)</d>", text, re.S)
    if text.count("<d>") != len(spoken):
        issues.append("every <d> must start with a [Language] tag, e.g. <d>[English] ...</d>")
    for _, s in spoken:
        if len(s) > 130:
            issues.append("line longer than 130 chars (H3 rushes or cuts it): '%s...'" % s[:40])
    if sum(len(s) for _, s in spoken) > 200:
        issues.append("more than 200 chars of dialogue in one clip; split the shot")
    for field in ("integrated_multimodal_description:", "overall_soundscape:", "non_diegetic_music:"):
        if field not in text:
            issues.append("missing field '%s'" % field)
    if len(set(re.findall(r"\((S\d)\)", text))) > 2:
        issues.append("more than two speakers in one clip")
    return issues


def build_graph(row, first_name, last_name):
    g = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    g["127"]["inputs"]["unet_name"] = H3_WEIGHT
    g["132"]["inputs"]["value"] = row["h3_seconds"]
    g["138"]["inputs"]["value"] = ""
    g["129"]["inputs"]["noise_seed"] = row["seed"]
    g["92"]["inputs"]["filename_prefix"] = "video/%s_full_t01" % row["chunk_id"]
    g["136"] = {
        "inputs": {
            "clip": ["128", 0], "vae": ["119", 0], "prompt": ["138", 0],
            "width": ["115", 0], "height": ["115", 1], "length": ["131", 1],
            "first_frame": ["137", 0], "last_frame": ["139", 0],
        },
        "class_type": "MiniMaxH3ImageToVideo",
        "_meta": {"title": "MiniMax H3 Image to Video (FL2VA)"},
    }
    g["137"] = {"inputs": {"image": first_name}, "class_type": "LoadImage", "_meta": {"title": "First Frame"}}
    g["139"] = {"inputs": {"image": last_name}, "class_type": "LoadImage", "_meta": {"title": "Last Frame"}}
    for nid in ("141", "142", "143", "144", "145", "146"):
        g.pop(nid, None)
    g["126"]["inputs"]["model"] = ["127", 0]
    g["124"]["inputs"]["steps"] = STEPS
    return g


def cmd_prompt(args):
    rows = [json.loads(l) for l in CHUNK_LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.scenes:
        want = set(args.scenes.split(","))
        rows = [r for r in rows if r["scene"] in want]
    if args.limit:
        rows = rows[:args.limit]
    caps = load_captions()
    people = {r["shot_id"]: r for r in jl(ROOT / "manifests" / "character_pass.jsonl")}
    # the name stamps live in a separate pass; fold them onto the people so the
    # roster traits can override a wrong VLM description
    for r in jl(ROOT / "manifests" / "character_names.jsonl"):
        tgt = people.setdefault(r["shot_id"], {"shot_id": r["shot_id"], "people": []})
        for i, p in enumerate(tgt.get("people") or []):
            src = (r.get("people") or [])
            if i < len(src) and src[i].get("name"):
                p["name"] = src[i]["name"]
    shots = {s["shot_id"]: s for s in jl(ROOT / "shots.jsonl")}
    dialogue_by_id = {r["id"]: r for r in csv.DictReader(TSV.open(encoding="utf-8"), delimiter="\t")}

    made, skipped = 0, 0
    for row in rows:
        # per-shot absolute time window, for line->shot assignment
        t = shots[row["shots"][0]]["start_pts"] / 24000
        for i, sid in enumerate(row["shots"]):
            s = shots[sid]
            people.setdefault(sid, {})["_t0"] = s["start_pts"] / 24000
            people[sid]["_t1"] = s["end_pts"] / 24000
            people[sid]["_off"] = s["start_pts"] / 24000 - t

        f, l = keyframes_for([{"shot_id": s} for s in row["shots"]])
        if not f or not l:
            skipped += 1
            continue
        first_dst = INPUT_DIR / (row["chunk_id"] + "_first.jpg")
        last_dst = INPUT_DIR / (row["chunk_id"] + "_last.jpg")
        for src, dst in ((f, first_dst), (l, last_dst)):
            if not dst.exists() or dst.stat().st_size != src.stat().st_size:
                shutil.copy(src, dst)

        text = build_prompt(row, caps, people, dialogue_by_id, None)
        for v in validate_prompt(text):
            print("  %s prompt violation: %s" % (row["chunk_id"], v))
        # The graph must name the file we actually uploaded, which is the copy in
        # fullrun/input, not the original still under stills/full.
        g = build_graph(row, first_dst.name, last_dst.name)
        g["138"]["inputs"]["value"] = text

        header = "\n".join([
            "# chunk: %s | scene: %s | %s" % (row["chunk_id"], row["scene"], row["scene_title"]),
            "# shots: %s" % " ".join(row["shot_nums"]),
            "# src: %s-%s  lines: %s" % (row["src_start"], row["src_end"], " ".join(row["line_ids"]) or "none"),
            "# h3: %d frames / %.3fs  seed: %d" % (row["h3_frames"], row["h3_seconds"], row["seed"]),
            "# words: %d" % len(text.split()), "", "",
        ])
        (PROMPT_DIR / (row["chunk_id"] + ".txt")).write_text(header + text, encoding="utf-8")
        (GRAPH_DIR / (row["chunk_id"] + ".json")).write_text(json.dumps(g, indent=2), encoding="utf-8")
        made += 1
    print("prompts+graphs written: %d   skipped (no stills): %d" % (made, skipped))


# ---------------------------------------------------------------------- render
def api(path, data=None, method=None, timeout=60):
    url = COMFY + path
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method or ("POST" if data is not None else "GET"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or "{}")


def upload(path):
    """POST /upload/image multipart, from TEMP (curl -F on an E: path fails, and so
    does urllib on some builds, so shell out to curl)."""
    src = Path(path)
    tmp = Path(os.environ["LOCALAPPDATA"]) / "Temp" / src.name
    shutil.copy(src, tmp)
    out = subprocess.run(
        ["curl", "-s", "-m", "60", "-F", "image=@%s" % tmp, "-F", "overwrite=true",
         COMFY + "/upload/image"],
        capture_output=True, text=True)
    return json.loads(out.stdout or "{}").get("name")


def queue_state():
    q = api("/queue")
    return len(q.get("queue_running", [])), len(q.get("queue_pending", []))


def refresh_one(chunk_id):
    """Rebuild one chunk's prompt and graph from the current caption cache.

    Called by render immediately before queueing, so a chunk rendered hours into
    a run still gets whatever captions have landed since the last full pass.
    """
    rows = [json.loads(l) for l in CHUNK_LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    row = next((r for r in rows if r["chunk_id"] == chunk_id), None)
    if not row:
        return False
    people = {r["shot_id"]: r for r in jl(ROOT / "manifests" / "character_pass.jsonl")}
    for r in jl(ROOT / "manifests" / "character_names.jsonl"):
        tgt = people.setdefault(r["shot_id"], {"shot_id": r["shot_id"], "people": []})
        for i, p in enumerate(tgt.get("people") or []):
            src = (r.get("people") or [])
            if i < len(src) and src[i].get("name"):
                p["name"] = src[i]["name"]
    shots = {s["shot_id"]: s for s in jl(ROOT / "shots.jsonl")}
    dialogue_by_id = {r["id"]: r for r in csv.DictReader(TSV.open(encoding="utf-8"), delimiter="\t")}
    t = shots[row["shots"][0]]["start_pts"] / 24000
    for sid in row["shots"]:
        s = shots[sid]
        people.setdefault(sid, {})["_t0"] = s["start_pts"] / 24000
        people[sid]["_t1"] = s["end_pts"] / 24000
        people[sid]["_off"] = s["start_pts"] / 24000 - t
    f, l = keyframes_for([{"shot_id": s} for s in row["shots"]])
    if not f or not l:
        return False
    first_dst = INPUT_DIR / (row["chunk_id"] + "_first.jpg")
    last_dst = INPUT_DIR / (row["chunk_id"] + "_last.jpg")
    for src, dst in ((f, first_dst), (l, last_dst)):
        if not dst.exists() or dst.stat().st_size != src.stat().st_size:
            shutil.copy(src, dst)
    text = build_prompt(row, load_captions(), people, dialogue_by_id, None)
    for v in validate_prompt(text):
        print("  %s prompt violation: %s" % (chunk_id, v))
    g = build_graph(row, first_dst.name, last_dst.name)
    g["138"]["inputs"]["value"] = text
    (PROMPT_DIR / (row["chunk_id"] + ".txt")).write_text(text, encoding="utf-8")
    (GRAPH_DIR / (row["chunk_id"] + ".json")).write_text(json.dumps(g, indent=2), encoding="utf-8")
    return True


def cmd_render(args):
    rows = [json.loads(l) for l in CHUNK_LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.scenes:
        want = set(args.scenes.split(","))
        rows = [r for r in rows if r["scene"] in want]
    if args.limit:
        rows = rows[:args.limit]

    done = {}
    if RENDER_LEDGER.exists():
        for r in jl(RENDER_LEDGER):
            done[r["chunk_id"]] = r
    todo = [r for r in rows if done.get(r["chunk_id"], {}).get("state") not in ("queued", "done")]
    if args.retry_rejected:
        todo = [r for r in rows if done.get(r["chunk_id"], {}).get("state") != "done"]
    print("chunks: %d  already handled: %d  to queue: %d" % (len(rows), len(rows) - len(todo), len(todo)))

    max_pending = args.max_pending
    fh = RENDER_LEDGER.open("a", encoding="utf-8")
    try:
        for r in todo:
            # wait for a queue slot rather than stacking hundreds of graphs
            while True:
                run, pend = queue_state()
                if run + pend < max_pending:
                    break
                print("  queue full (%d running, %d pending), waiting..." % (run, pend), flush=True)
                time.sleep(args.poll)
            gpath = GRAPH_DIR / (r["chunk_id"] + ".json")
            if args.refresh and refresh_one(r["chunk_id"]):
                pass
            elif not gpath.exists():
                print("  %s no graph, skipping" % r["chunk_id"])
                continue
            graph = json.loads(gpath.read_text(encoding="utf-8"))
            ok = True
            for key in ("first", "last"):
                img = INPUT_DIR / ("%s_%s.jpg" % (r["chunk_id"], key))
                if not img.exists():
                    ok = False
                    break
                try:
                    upload(img)
                except Exception as e:  # noqa: BLE001
                    print("  %s upload %s failed: %s" % (r["chunk_id"], key, e))
                    ok = False
            if not ok:
                continue
            try:
                res = api("/prompt", {"prompt": graph}, timeout=90)
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "replace")
                print("  %s rejected: %s" % (r["chunk_id"], body[:600]))
                fh.write(json.dumps({"chunk_id": r["chunk_id"], "state": "rejected",
                                     "error": body[:600], "ts": time.time()}) + "\n")
                fh.flush()
                continue
            pid = res.get("prompt_id")
            if not pid:
                print("  %s rejected: %s" % (r["chunk_id"], res.get("node_errors")))
                continue
            fh.write(json.dumps({"chunk_id": r["chunk_id"], "state": "queued",
                                 "prompt_id": pid, "ts": time.time()}) + "\n")
            fh.flush()
            print("  queued %s %s" % (r["chunk_id"], pid[:8]), flush=True)
            time.sleep(args.gap)
    finally:
        fh.close()


# --------------------------------------------------------------------- collect
def fetch(path, params):
    url = COMFY + path + "?" + "&".join("%s=%s" % kv for kv in params.items())
    with urllib.request.urlopen(url, timeout=180) as r:
        return r.read()


# -------------------------------------------------------------------- recover
def cmd_recover(args):
    """Rebuild the render ledger from files on the 5090's disk.

    ComfyUI holds its queue and /history in memory, so a host reboot loses the
    completed-work record even though the mp4s survive on disk. Filenames are
    deterministic — <chunk_id>_full_t01_00001_.mp4 in the video/ output subdir —
    so we can probe /view by name, pull every survivor, and rewrite renders.jsonl
    so a following render pass re-queues only what is genuinely missing.
    """
    rows = [json.loads(l) for l in CHUNK_LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.scenes:
        want = set(args.scenes.split(","))
        rows = [r for r in rows if r["scene"] in want]
    final, recv, miss = [], 0, 0
    for r in rows:
        cid = r["chunk_id"]
        dst = OUTPUT_DIR / ("%s_full_t01.mp4" % cid)
        data = b""
        if dst.exists() and dst.stat().st_size > 1000:
            final.append({"chunk_id": cid, "state": "done", "file": dst.name,
                          "bytes": dst.stat().st_size, "ts": dst.stat().st_mtime, "via": "local"})
            recv += 1
            continue
        name = "%s_full_t01_00001_.mp4" % cid
        try:
            data = fetch("/view", {"filename": name, "subfolder": "video", "type": "output"})
        except Exception:  # noqa: BLE001
            data = b""
        if data and len(data) > 1000:
            dst.write_bytes(data)
            final.append({"chunk_id": cid, "state": "done", "file": dst.name,
                          "bytes": len(data), "ts": time.time(), "via": "recover"})
            recv += 1
        else:
            miss += 1
    RENDER_LEDGER.write_text("\n".join(json.dumps(x) for x in final) + ("\n" if final else ""),
                             encoding="utf-8")
    print("recovered done: %d   lost (will re-queue): %d" % (recv, miss))


def cmd_collect(args):
    rows = [json.loads(l) for l in CHUNK_LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.scenes:
        want = set(args.scenes.split(","))
        rows = [r for r in rows if r["scene"] in want]
    recs = {r["chunk_id"]: r for r in jl(RENDER_LEDGER)} if RENDER_LEDGER.exists() else {}
    got, missing = 0, []
    fh = RENDER_LEDGER.open("a", encoding="utf-8")
    try:
        for r in rows:
            cid = r["chunk_id"]
            dst = OUTPUT_DIR / ("%s_full_t01.mp4" % cid)
            rec = recs.get(cid, {})
            if dst.exists() and dst.stat().st_size > 1000:
                got += 1
                continue
            if not rec.get("prompt_id"):
                missing.append(cid)
                continue
            try:
                hist = api("/history/" + rec["prompt_id"], timeout=30)
            except Exception:  # noqa: BLE001
                missing.append(cid)
                continue
            if not hist:
                missing.append(cid)
                continue
            v = list(hist.values())[0]
            if v.get("status", {}).get("status_str") != "success":
                missing.append(cid)
                continue
            name = None
            for o in v.get("outputs", {}).values():
                for vid in o.get("videos", o.get("images", [])):
                    if vid.get("filename", "").endswith(".mp4"):
                        name = vid["filename"]
                        sub = vid.get("subfolder", "")
            if not name:
                missing.append(cid)
                continue
            data = fetch("/view", {"filename": name, "subfolder": sub, "type": "output"})
            dst.write_bytes(data)
            fh.write(json.dumps({"chunk_id": cid, "state": "done", "prompt_id": rec["prompt_id"],
                                 "file": dst.name, "bytes": len(data), "ts": time.time()}) + "\n")
            fh.flush()
            got += 1
            print("  got %s (%d KB)" % (cid, len(data) // 1024), flush=True)
    finally:
        fh.close()
    print("collected: %d   still missing: %d" % (got, len(missing)))
    if missing[:10]:
        print("  missing sample:", ", ".join(missing[:10]))


def cmd_stitch(args):
    rows = [json.loads(l) for l in CHUNK_LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    scenes = sorted({r["scene"] for r in rows}, key=lambda s: int(s[1:]))
    if args.scenes:
        scenes = [s for s in scenes if s in set(args.scenes.split(","))]
    for sid in scenes:
        files = sorted(OUTPUT_DIR.glob("%s-*_full_t01.mp4" % sid))
        if not files:
            continue
        lst = STITCH_DIR / ("%s_concat.txt" % sid)
        lst.write_text("\n".join("file '%s'" % f.as_posix() for f in files), encoding="utf-8")
        out = STITCH_DIR / ("%s_full_t01.mp4" % sid)
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                        "-c", "copy", str(out)], capture_output=True, text=True)
        print("%s: %d chunks -> %s" % (sid, len(files), out.name))


def cmd_status(args):
    if not CHUNK_LEDGER.exists():
        print("no plan yet — run: python fullrun.py plan")
        return
    rows = jl(CHUNK_LEDGER)
    caps = load_captions()
    recs = jl(RENDER_LEDGER) if RENDER_LEDGER.exists() else []
    queued = {r["chunk_id"] for r in recs if r.get("state") == "queued"}
    done = {r["chunk_id"] for r in recs if r.get("state") == "done"}
    graphs = len(list(GRAPH_DIR.glob("*.json")))
    vids = len(list(OUTPUT_DIR.glob("*.mp4")))
    total = sum(r["h3_frames"] for r in rows)
    print("chunks planned:  %d  (%d h3 frames, %.0f s of clip)" % (len(rows), total, total / FPS))
    print("stills captioned: %d cache entries" % len(caps))
    print("graphs built:    %d" % graphs)
    print("renders queued:  %d" % len(queued))
    print("renders done:    %d" % len(done))
    print("mp4 on disk:     %d" % vids)
    if done:
        print("progress: %.1f%% of chunks, gpu cost so far ~%.1f h"
              % (100.0 * len(done) / len(rows), sum(r["h3_frames"] for r in rows
                                                    if r["chunk_id"] in done) * 0.9 / 3600))
    try:
        run, pend = queue_state()
        print("comfy queue:     %d running, %d pending" % (run, pend))
    except Exception as e:  # noqa: BLE001
        print("comfy queue:     unreachable (%s)" % e)
    per_scene = {}
    for r in rows:
        s = per_scene.setdefault(r["scene"], [0, 0])
        s[0] += 1
        if r["chunk_id"] in done:
            s[1] += 1
    for sid in sorted(per_scene, key=lambda s: int(s[1:])):
        tot, d = per_scene[sid]
        print("  %s %3d chunks  %3d done  %s" % (sid, tot, d, "#" * int(20 * d / tot)))


DECISIONS = """
Decisions taken without asking (a test run, not a final film):
  * mode FL2VA on source-still bookends. T0003 showed anchoring holds (14-28 MSE);
    T0004/T0005 showed the middle needs a written motion path. ref2v stays available
    but is not in this script.
  * 20 steps, int8 weight, 864x480, 24fps, 17k+5 grid, 4-15s clamp.
  * per-chunk seed from crc32 of the chunk id, so a re-run reproduces the render.
  * scene spans from the dialogue timeline, boundaries at cue midpoints, so every
    shot in the film belongs to exactly one scene.
  * chunks never cross a scene: 2-3 shots, 4-15s, a lone long shot is its own chunk.
  * a line belongs to the shot holding its midpoint; never split across a cut.
  * speaker on-screen if stamped for the shot, or if it is the only visible person
    and the sex matches. Off-screen otherwise.
  * identity is physical traits, never a name. Names live only in the roster lookup
    that produces the traits.
  * action beats are staging choices, keyed on the composition pass's own motion
    field, plus per-character gesture banks.
  * music line is derived from the beat-sheet mood word through an instrumentation map.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan")
    p = sub.add_parser("caption")
    p.add_argument("--scenes")
    p.add_argument("--limit", type=int)
    p.add_argument("--workers", type=int, default=2)
    sub.add_parser("decisions").set_defaults(func=lambda a: print(DECISIONS))
    p = sub.add_parser("prompt")
    p.add_argument("--scenes")
    p.add_argument("--limit", type=int)
    p = sub.add_parser("render")
    p.add_argument("--scenes")
    p.add_argument("--limit", type=int)
    p.add_argument("--max-pending", type=int, default=8)
    p.add_argument("--poll", type=int, default=60)
    p.add_argument("--gap", type=float, default=3.0)
    p.add_argument("--retry-rejected", action="store_true")
    p.add_argument("--refresh", action="store_true",
                   help="rebuild each chunk's prompt from the current caption cache before queueing")
    p = sub.add_parser("recover")
    p.add_argument("--scenes")
    p = sub.add_parser("collect")
    p.add_argument("--scenes")
    p = sub.add_parser("stitch")
    p.add_argument("--scenes")
    sub.add_parser("status")
    args = ap.parse_args()
    if not hasattr(args, "func"):
        {"plan": cmd_plan, "caption": cmd_caption, "prompt": cmd_prompt,
         "render": cmd_render, "recover": cmd_recover, "collect": cmd_collect,
         "stitch": cmd_stitch, "status": cmd_status}[args.cmd](args)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
