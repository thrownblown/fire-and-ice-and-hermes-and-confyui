"""T0005: S03 FL2VA with real physical action. One variable vs T0004 = action amplitude.

Identical to T0004: keyframes, seed 1125345046553186, weight, node, frame lengths,
dialogue assembly, soundscape, music, and the deferred-arrival structure. What changes
is the scale of the described action: body-level movement and gesture instead of
breathing and blinking, and large/fast camera moves instead of small/slow ones.

Where the two bookends of a chunk are close together (c01), the action is written as a
departure-and-return so the extra motion still lands on Picture 2 instead of fighting it.
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
# THE VARIABLE, part 1: camera moves with real travel instead of a slow creep
MOVE = {
    "shot:00067": "The camera arcs slowly around her from the front toward a stronger profile, then eases back to where it began.",
    "shot:00068": "The camera pulls out with large amplitude at fast speed, snapping from his eye to a wider view of his upper body, then pushes back in.",
    "shot:00069": "The camera arcs around her with large amplitude at fast speed, swinging from her clasped hands around to her face as she turns.",
    "shot:00070": "The camera trucks right with large amplitude at fast speed, carrying him across the frame as he paces, then settles.",
    "shot:00071": "The camera tracks her arm with a fast pan as she sweeps it outward and upward, then whips back to her face.",
    "shot:00072": "The camera arcs behind him with large amplitude as he turns away, then comes back around to his profile as he turns to face the room again.",
    "shot:00073": "The camera trucks right with large amplitude at fast speed along the row of envoys as they turn and shuffle, then pushes in on her.",
    "shot:00074": "The camera arcs around her with large amplitude at fast speed, swinging from her profile around toward the front as her head turns.",
}
# THE VARIABLE, part 2: body-level action instead of micro-motion
BEATS = {
    "shot:00067": (
        "She speaks the first line seated and still, then thrusts one arm out from her body toward the far "
        "side of the hall, the sleeve falling open and the silver beads at her crown catching the light as her "
        "head snaps to follow the gesture. Her hand opens, fingers spread, and sweeps down and across in a "
        "broad arc before she draws the arm back in and presses it to her side. She leans forward in the "
        "throne as the second line begins, then sits back, her hair and gown swinging with the movement, and "
        "returns to the upright position she started from."
    ),
    "shot:00068": (
        "He keeps his hand over his face for a beat, then drags it down and away in one sharp motion, baring "
        "his whole face; his head snaps up and his mouth opens wide as he speaks. He steps forward out of the "
        "shadow, throwing one arm up and out with the palm turned up, then drops to a knee, the white hair and "
        "the dark robe swinging out around him. His head comes down, his shoulders hunch, and by the end of the "
        "shot he is kneeling low with his hand near his chest, still turned toward the figure he addresses."
    ),
    "shot:00069": (
        "Her hands are clasped at her chest and she holds them there, listening; then her fingers break apart "
        "and both hands open, palms up, as she turns sharply toward the off-screen voice. One arm lifts and "
        "sweeps outward to the side with the sleeve trailing, and she rises a little from her seat, her hair "
        "swinging across her shoulder. The arm comes back down and her hands meet again lower, at her waist, "
        "and her head turns to follow the gesture before settling."
    ),
    "shot:00070": (
        "He turns his head sharply to the side and paces a step across the frame, the hem of his dark robe "
        "swinging out behind the movement and the long white hair sliding off his shoulder. He stops, whirls "
        "back with both arms thrown out and palms open, and speaks with his whole body angled forward, then "
        "drives one fist down and the arm back to his side. His chest rises and he holds the turned stance, "
        "weight on the front foot, before the movement settles."
    ),
    "shot:00071": (
        "Her right arm is already extended and she drives it further outward, the hand opening and the fingers "
        "spreading wide, then sweeps the arm up and across above her shoulder in a single fast arc. She leans "
        "into the gesture, head tilted back, then brings the arm down hard to her side, the beads at her crown "
        "flashing as her head comes forward. Her hand rises once more with the index finger up, holds, and "
        "drops; the sleeve settles against her arm and her gaze steadies forward."
    ),
    "shot:00072": (
        "At the off-screen line he snaps his head toward the speaker, then turns his whole body away, showing "
        "his back to the room as the camera arcs behind him. One arm lifts and drops in a single dismissive "
        "sweep; the robe's hem swings out and the white hair swings with it. He pivots back on his heel, "
        "steps forward, and answers with his chin raised and one hand open at chest height, then lets the arm "
        "fall. His head turns a little further into profile and the movement stops."
    ),
    "shot:00073": (
        "She lowers her hand from her mouth, steps toward the three hooded figures, and thrusts her other arm "
        "out at them, pointing; the gown's slit opens with the stride. The three envoys turn together, shuffle "
        "a step, and the figure at the far right lifts the rolled scroll and holds it up, the yellow glow of "
        "their eyes swinging across the frame as they move. She draws her arm back, brings both hands up near "
        "her chest, and turns her body between them and the hall, hair and gown still swinging."
    ),
    "shot:00074": (
        "Her head snaps around toward the right and her body turns with it, the row of pale ornaments in her "
        "hair flashing as it moves; she steps forward out of the seated figure's line and her shoulder leads the "
        "turn. One arm comes up and gestures outward, palm open, then drops; her chin lifts and her gaze fixes "
        "on something off-screen. She draws her arms in to her sides, squares her shoulders, and comes to rest "
        "in the position established by <Picture 2>."
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
         "cold blue-grey cavern light, broad graphic acting with strong gesture and clear body poses")
NARROW = ("Only in the last seconds do these movements slow and stop, and the figure comes to rest in the "
          "pose, spacing, framing, and lighting established by <Picture 2>.")
TAIL = ("overall_soundscape: Cavernous hall reverb under the dialogue, distant wind moving "
        "through stone corridors, heavy fabric and robe movement, footsteps on stone.")
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
    run = ROOT / "runs" / "T0005_s03_fl2va-action"
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
            "# chunk: %s | test: T0005 | scene: S03 | mode: FL2VA | variable: action amplitude" % cid,
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
        g["92"]["inputs"]["filename_prefix"] = "video/%s_T0005_t01" % cid
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
        "# T0005 — S03 FL2VA, action-amplitude prompts\n\n"
        "- Date: 2026-09-29\n"
        "- One variable vs T0004: the scale of the action described in the prompt. Same keyframes,\n"
        "  seed (1125345046553186), weight, node, frame lengths, dialogue, soundscape, music, and the\n"
        "  deferred-arrival structure.\n"
        "- T0004 wrote micro-action (breathing, blinking, a few degrees of head turn) with small-amplitude\n"
        "  slow camera moves. It worked mechanically — frozen-frame fraction fell in all 5 chunks — but the\n"
        "  clips read flat, because nothing in them moved at body scale.\n"
        "- What changed: arm sweeps, steps, turns of the whole body, kneeling, a fist driven down, hair and\n"
        "  robe swinging with the movement, and large-amplitude fast camera moves with real travel. The style\n"
        "  line now asks for broad graphic acting. The soundscape adds footsteps and heavy fabric.\n"
        "- Where a chunk's two bookends are close (c01), the action is a departure-and-return so the extra\n"
        "  motion still lands on Picture 2 rather than fighting it.\n"
        "- These actions are staging choices for the remake, not claims about the source footage. They stay\n"
        "  inside what is visible in the keyframes (who is on screen, what they wear, where they are).\n"
        "- Question: does body-scale action remove the flatness without losing the keyframe anchoring?\n"
        "- Compare: frozen-frame fraction and anchor MSE vs T0003/T0004 frame metrics.\n\n"
        "## Verdict\n(Alex, after watching.)\n",
        encoding="utf-8")
    print("wrote", run)


if __name__ == "__main__":
    main()
