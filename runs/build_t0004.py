"""T0004: S03 FL2VA with a real motion path. One variable vs T0003 = prompt motion language.

Identical to T0003: keyframes (chunk first/last source stills), seed 1125345046553186,
weight minimax_h3_fl2va_pruned_int8_convrot, node MiniMaxH3ImageToVideo, frame lengths,
dialogue assembly, soundscape, music. Only integrated_multimodal_description changes:
static cameras become slow moves, and each shot gains observable intermediate change
with arrival at Picture 2 deferred and narrowed to the final seconds.

Intermediate states are grounded in the mid-shot stills that local qwen3-vl-8b already
captioned (captions.json). No new VLM calls; no new keyframes.
"""
import csv
import json
import shutil
from pathlib import Path

ROOT = Path(r"E:/FNI")
SEED = 1125345046553186
CAP = 15.0

DESC = {
    "JULIANA": ("a young woman with extremely pale white skin, an angular face, crimson lips, "
                "long straight jet-black hair with small white beads at the crown, long silver "
                "dagger-shaped earrings, and a deep purple long-sleeved gown"),
    "NEKRON": "a pale man with long white hair in a dark purple robe",
    "ENVOY": "a hooded subhuman envoy in a dark robe with yellow eyes and dark skin",
}
SHORT = {
    "JULIANA": "the pale young woman with long jet-black hair",
    "NEKRON": "the white-haired man in the dark purple robe",
    "ENVOY": "the hooded envoy",
}
VISIBLE = {
    "shot:00067": ["JULIANA"], "shot:00068": ["NEKRON"], "shot:00069": ["JULIANA"],
    "shot:00070": ["NEKRON"], "shot:00071": ["JULIANA"], "shot:00072": ["NEKRON"],
    "shot:00073": ["JULIANA", "ENVOY"], "shot:00074": ["JULIANA", "NEKRON"],
}
# the variable: a camera move per shot instead of a static hold
MOVE = {
    "shot:00067": "The camera pushes in with small amplitude at slow speed, tightening from her shoulders toward her face.",
    "shot:00068": "The camera pushes in with small amplitude at slow speed, closing in on his raised hand and the single visible eye.",
    "shot:00069": "The camera pulls out with small amplitude at slow speed, opening from her clasped hands to her head and shoulders.",
    "shot:00070": "The camera pushes in with small amplitude at slow speed, closing on his face as his gaze drops.",
    "shot:00071": "The camera trucks right with small amplitude at slow speed, following the line of her extended arm.",
    "shot:00072": "The camera pushes in with small amplitude at slow speed, tightening on his profile.",
    "shot:00073": "The camera trucks right with small amplitude at slow speed, drifting along the row of hooded figures.",
    "shot:00074": "The camera pushes in with small amplitude at slow speed, closing on her eyes as her head turns.",
}
# the variable: observable intermediate change per shot, grounded in the VLM mid-still captions
BEATS = {
    "shot:00067": (
        "She breathes visibly through the whole shot, her shoulders rising and falling under the gown, "
        "and her hair shifts at the temple with each movement. She blinks once and her gaze drifts down "
        "away from the figure she is addressing, then returns to level. While the first line is spoken "
        "her head stays in profile; as the second line begins her chin lifts a few degrees and her "
        "eyebrows rise, and the hair at her cheek swings forward and settles."
    ),
    "shot:00068": (
        "His right hand stays pressed across his face and the fingers shift against his brow; the one "
        "visible eye blinks and its blue glow pulses brighter and then dims. He breathes, his chest "
        "lifting under the dark robe, and his head tilts a few degrees downward as he speaks, the white "
        "hair at his shoulder sliding with the tilt. In the last second of the shot his hand begins to "
        "lower, uncovering more of his cheek."
    ),
    "shot:00069": (
        "Her hands stay clasped at her chest and her fingers tighten once; she blinks and her gaze drops "
        "to her hands, then lifts again toward the off-screen voice. Her shoulders rise and fall with her "
        "breathing and the loose black hair at her temple shifts as she turns her head a few degrees "
        "toward the sound. By the end her chin has lifted and her eyes are level."
    ),
    "shot:00070": (
        "His jaw works as he listens and his brow furrows; he breathes and the white hair falling over "
        "his shoulders sways slightly as his head turns a few degrees. His gaze drops toward the floor "
        "and stays there for a moment before lifting again, and the greenish buttons on his shoulder "
        "strap shift with the movement of the robe."
    ),
    "shot:00071": (
        "Her right arm stays extended and the fingers of her raised hand close slightly, then open again; "
        "her head tilts upward and eases back down, the beads at her crown catching the cold light as she "
        "moves. She blinks, her chest rising and falling with her breathing, and by the end of the shot "
        "her gaze has steadied forward."
    ),
    "shot:00072": (
        "He shifts his weight and the collar of his dark robe moves across his chest; his jaw sets as the "
        "off-screen line finishes and he breathes out before answering. His gaze drops, then returns to "
        "the level, and the long white hair past his shoulders sways and settles against the robe. In the "
        "final seconds his head turns a little further into profile and then stops."
    ),
    "shot:00073": (
        "The three hooded figures shift their weight almost imperceptibly and the yellow glow of their eyes "
        "moves as their heads turn a few degrees; the figure at the far right adjusts the rolled scroll in "
        "its hands. She lowers her raised hand from her mouth toward her side, then brings her other hand "
        "up in a small gesture, her shoulders rising and falling with her breathing and the slit of her "
        "gown shifting as she turns toward them."
    ),
    "shot:00074": (
        "Her head turns a few degrees toward the right and her gaze follows, the row of pale ornaments in "
        "her hair catching the light as it moves; she blinks once and breathes, her shoulders settling. "
        "Out of focus behind her, the seated figure beside the winged statue shifts slightly. By the end "
        "her head has come to rest in the position established by <Picture 2>."
    ),
}
GROUPS = [
    ("s03-c01", ["shot:00067"]),
    ("s03-c02", ["shot:00068", "shot:00069"]),
    ("s03-c03", ["shot:00070", "shot:00071"]),
    ("s03-c04", ["shot:00072"]),
    ("s03-c05", ["shot:00073", "shot:00074"]),
]
STYLE = ("2D-animated rotoscope painted animation in the style of a 1983 fantasy film: "
         "inked figures over cool-toned painted cavern backgrounds, Ice Peak throne hall, "
         "cold blue-grey cavern light")
NARROW = ("Only in the last seconds do these changes slow and narrow, and the figure comes to rest in "
          "the pose, spacing, framing, and lighting established by <Picture 2>.")
TAIL = ("overall_soundscape: Cavernous hall reverb under the dialogue, distant wind moving "
        "through stone corridors, soft fabric rustle as the robed figures move.")
MUSIC = ("non_diegetic_music: A cold, sinister orchestral theme: low sustained strings, sparse "
         "brass swells, slow tempo, quiet dynamics under the voices.")


def sec(tc):
    h, mi, rest = tc.replace(",", ".").split(":")
    return int(h) * 3600 + int(mi) * 60 + float(rest)


def h3_frames(seconds):
    seconds = max(4.0, min(CAP, seconds))
    raw = max(5, round(seconds * 24))
    return raw + (5 - (raw % 17)) % 17


def first_sentence(cap):
    for end in (". ", ".\n"):
        if end in cap:
            return cap.split(end)[0] + "."
    return cap.rstrip(".") + "."


def main():
    shots = {}
    for line in (ROOT / "shots.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            s = json.loads(line)
            shots[s["shot_id"]] = s
    rows = list(csv.DictReader((ROOT / "script" / "dialogue-timeline.tsv").open(encoding="utf-8"), delimiter="\t"))

    def lines_in(sid):
        s = shots[sid]
        got = []
        for r in rows:
            if r["scene"] != "S03":
                continue
            mid = (sec(r["start"]) + sec(r["end"])) / 2
            if s["start_pts"] / 24000 <= mid < s["end_pts"] / 24000:
                got.append(r)
        return got

    prev_run = ROOT / "runs" / "T0003_s03_fl2va-srcfflf"
    run = ROOT / "runs" / "T0004_s03_fl2va-motionpath"
    (run / "input").mkdir(parents=True, exist_ok=True)
    (run / "output").mkdir(parents=True, exist_ok=True)
    captions = json.loads((prev_run / "captions.json").read_text(encoding="utf-8"))
    template = json.loads((ROOT / "graphs" / "video_minimax_h3_r2v.json").read_text(encoding="utf-8"))

    for cid, sids in GROUPS:
        group = [shots[s] for s in sids]
        t0 = group[0]["start_pts"] / 24000
        frames = h3_frames(group[-1]["end_pts"] / 24000 - t0)
        duration = frames / 24.0

        first_dst = run / "input" / ("%s_first.jpg" % cid)
        last_dst = run / "input" / ("%s_last.jpg" % cid)
        shutil.copy(prev_run / "input" / first_dst.name, first_dst)
        shutil.copy(prev_run / "input" / last_dst.name, last_dst)

        spoken = [(s, r) for s in group for r in lines_in(s["shot_id"])]
        speakers = []
        for _, r in spoken:
            if r["speaker"] not in speakers:
                speakers.append(r["speaker"])
        sid_of = {n: "(S%d)" % (i + 1) for i, n in enumerate(speakers)}

        n_shots = len(group)
        instr = ("How the reference pictures align with the target video — Picture 1 (from Shot 1) "
                 "aligns with the 0.00-second mark of the target video; Picture 2 (from Shot %d) "
                 "aligns with the %.2f-second mark of the target video." % (n_shots, duration))

        parts = []
        for idx, s in enumerate(group, 1):
            sid = s["shot_id"]
            off = s["start_pts"] / 24000 - t0
            bits = []
            if idx == 1:
                bits.append("[Shot 1] %s. The opening frame matches <Picture 1>: %s"
                            % (STYLE, first_sentence(captions[first_dst.name])))
            else:
                mm, ss = divmod(off, 60)
                bits.append("[Shot %d] At %02d:%06.3f, the camera cuts to a new angle." % (idx, int(mm), ss))
            bits.append(MOVE[sid])
            bits.append("On screen: %s." % ", ".join(DESC[n] for n in VISIBLE[sid]))
            for sshot, r in spoken:
                if sshot["shot_id"] != sid:
                    continue
                spk, tag = r["speaker"], sid_of[r["speaker"]]
                if spk in VISIBLE[sid]:
                    bits.append("%s %s says: <d>[English] %s</d>" % (SHORT[spk], tag, r["text"]))
                else:
                    bits.append("%s %s speaks while off-screen: <d>[English] %s</d>" % (DESC[spk], tag, r["text"]))
            bits.append(BEATS[sid])
            if idx == n_shots:
                bits.append(NARROW)
            parts.append(" ".join(bits))

        text = "\n\n".join([instr, "integrated_multimodal_description: " + " ".join(parts), TAIL, MUSIC])
        header = "\n".join([
            "# chunk: %s | test: T0004 | scene: S03 | mode: FL2VA | variable: motion path" % cid,
            "# first_frame: %s | last_frame: %s" % (first_dst.name, last_dst.name),
            "# graph_length_seconds: %.3f" % duration,
            "# graph_length_frames: %d" % frames,
            "# lines: %s" % (" ".join(r["id"] for _, r in spoken) or "none"),
            "# words: %d" % len(text.split()), "", "",
        ])
        (run / ("%s.txt" % cid)).write_text(header + text, encoding="utf-8")

        g = json.loads(json.dumps(template))
        g["127"]["inputs"]["unet_name"] = "h3/minimax_h3_fl2va_pruned_int8_convrot.safetensors"
        g["132"]["inputs"]["value"] = duration
        g["138"]["inputs"]["value"] = text
        g["129"]["inputs"]["noise_seed"] = SEED
        g["92"]["inputs"]["filename_prefix"] = "video/%s_T0004_t01" % cid
        g["136"] = {
            "inputs": {
                "clip": ["128", 0], "vae": ["119", 0], "prompt": ["138", 0],
                "width": ["115", 0], "height": ["115", 1], "length": ["131", 1],
                "first_frame": ["137", 0], "last_frame": ["139", 0],
            },
            "class_type": "MiniMaxH3ImageToVideo",
            "_meta": {"title": "MiniMax H3 Image to Video (FL2VA)"},
        }
        g["137"] = {"inputs": {"image": first_dst.name}, "class_type": "LoadImage", "_meta": {"title": "First Frame"}}
        g["139"] = {"inputs": {"image": last_dst.name}, "class_type": "LoadImage", "_meta": {"title": "Last Frame"}}
        for nid in ["141", "142", "143", "144", "145", "146"]:
            g.pop(nid, None)
        g["126"]["inputs"]["model"] = ["127", 0]
        g["124"]["inputs"]["steps"] = 20
        (run / ("%s.json" % cid)).write_text(json.dumps(g, indent=2), encoding="utf-8")
        print(cid, "frames=%d" % frames, "words=%d" % len(text.split()))

    (run / "manifest.md").write_text(
        "# T0004 — S03 FL2VA, motion-path prompts\n\n"
        "- Date: 2026-09-29\n"
        "- One variable vs T0003: the prompt's motion language. Same keyframes (chunk first/last\n"
        "  source stills), same seed (1125345046553186), same weight, same node, same frame\n"
        "  lengths, same dialogue assembly, same soundscape and music lines.\n"
        "- What changed in integrated_multimodal_description:\n"
        "  1. Every 'camera holds a static shot' became a slow single move (push in / pull out /\n"
        "     truck right, small amplitude, slow speed).\n"
        "  2. Each shot gained an observable-intermediate-change passage (breathing, gaze, hair,\n"
        "     hand and head movement), grounded in the mid-shot stills local qwen3-vl-8b captioned\n"
        "     for T0003. Those are visible things, not invented plot.\n"
        "  3. The old 'the action resolves into the exact pose established by <Picture 2>' was\n"
        "     replaced by arrival deferred to the last seconds, with the differences narrowing.\n"
        "- Why: T0003 metrics showed the model reaching the last keyframe by 25-50% of the clip and\n"
        "  then holding it; 4 of 5 chunks were more frozen than their ref2v counterparts. A static\n"
        "  camera plus no intermediate states left the model nothing to do between the anchors.\n"
        "- Question: does a written motion path wake up the middle of the clip without losing the\n"
        "  keyframe anchoring that T0003 got right?\n"
        "- Renders: video/<chunk>_T0004_t01 on the 5090. Compare against T0003 with the same\n"
        "  frame metrics (frame-metrics.json in the T0003 run).\n\n"
        "## Verdict\n(Alex, after watching.)\n",
        encoding="utf-8")
    print("wrote", run)


if __name__ == "__main__":
    main()
