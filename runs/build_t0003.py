"""T0003: S03 in FL2VA (first/last frame) mode. Same chunks, seed, lengths as T0002.
First/last frames = source stills. Captions from local qwen3-vl-8b (LM Studio)."""
import base64
import csv
import json
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(r"E:/FNI")
SEED = 1125345046553186
CAP = 15.0
LM_URL = "http://127.0.0.1:1234/v1/chat/completions"
VLM_MODEL = "qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s"

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
CAMERA = {
    "shot:00067": "The camera holds a static medium three-quarter shot.",
    "shot:00068": "The camera holds a static medium straight-on shot.",
    "shot:00069": "The camera holds a static medium three-quarter shot.",
    "shot:00070": "The camera holds a static medium three-quarter shot.",
    "shot:00071": "The camera holds a static medium three-quarter shot.",
    "shot:00072": "The camera holds a static medium close-up, three-quarter angle.",
    "shot:00073": "The camera holds a static medium straight-on shot.",
    "shot:00074": "The camera holds a static close-up, three-quarter angle.",
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


def sec(tc):
    h, mi, rest = tc.replace(",", ".").split(":")
    return int(h) * 3600 + int(mi) * 60 + float(rest)


def h3_frames(seconds):
    seconds = max(4.0, min(CAP, seconds))
    raw = max(5, round(seconds * 24))
    return raw + (5 - (raw % 17)) % 17


def caption(path):
    b64 = base64.b64encode(path.read_bytes()).decode()
    body = json.dumps({
        "model": VLM_MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}},
            {"type": "text", "text": (
                "Describe this animation film still in 2-3 sentences: the visible subject "
                "(sex, hair, costume, pose, gesture), the framing, the background, and the "
                "lighting. Literal description only. No names, no story guesses.")}],
        }],
        "max_tokens": 200, "temperature": 0.2,
    }).encode()
    req = urllib.request.Request(LM_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.load(r)
    return d["choices"][0]["message"]["content"].strip()


def find_still(shot_num, which):
    pat = "shot_%s_f*.jpg" % shot_num
    files = sorted((ROOT / "stills" / "full").glob(pat))
    return files[0] if which == "first" else files[-1]


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

    run = ROOT / "runs" / "T0003_s03_fl2va-srcfflf"
    (run / "input").mkdir(parents=True, exist_ok=True)
    template = json.loads((ROOT / "graphs" / "video_minimax_h3_r2v.json").read_text(encoding="utf-8"))
    cap_file = run / "captions.json"
    captions = json.loads(cap_file.read_text(encoding="utf-8")) if cap_file.exists() else {}

    for cid, sids in GROUPS:
        group = [shots[s] for s in sids]
        t0 = group[0]["start_pts"] / 24000
        dur_frames = h3_frames(group[-1]["end_pts"] / 24000 - t0)
        duration = dur_frames / 24.0

        first_num = sids[0].split(":")[1]
        last_num = sids[-1].split(":")[1]
        first_src = find_still(first_num, "first")
        last_src = find_still(last_num, "last")
        first_dst = run / "input" / ("%s_first.jpg" % cid)
        last_dst = run / "input" / ("%s_last.jpg" % cid)
        shutil.copy(first_src, first_dst)
        shutil.copy(last_src, last_dst)

        for tag, p in (("first", first_dst), ("last", last_dst)):
            key = str(p.name)
            if key not in captions:
                captions[key] = caption(p)
                print("caption", key, "->", captions[key][:80], "...")

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

        shot_parts = []
        for idx, s in enumerate(group, 1):
            off = s["start_pts"] / 24000 - t0
            bits = []
            if idx == 1:
                bits.append("[Shot 1] %s. The opening frame matches <Picture 1>: %s" % (STYLE, first_sentence(captions[first_dst.name])))
            else:
                mm, ss = divmod(off, 60)
                bits.append("[Shot %d] At %02d:%06.3f, the camera cuts to a new angle." % (idx, int(mm), ss))
            bits.append(CAMERA[s["shot_id"]])
            who = ", ".join(DESC[n] for n in VISIBLE[s["shot_id"]])
            bits.append("On screen: %s." % who)
            for ss_shot, r in spoken:
                if ss_shot["shot_id"] != s["shot_id"]:
                    continue
                spk = r["speaker"]
                tag = sid_of[spk]
                if spk in VISIBLE[s["shot_id"]]:
                    bits.append("%s %s says: <d>[English] %s</d>" % (SHORT[spk], tag, r["text"]))
                else:
                    bits.append("%s %s speaks while off-screen: <d>[English] %s</d>" % (DESC[spk], tag, r["text"]))
            if idx == n_shots:
                bits.append("The action resolves into the exact pose, framing, and composition "
                            "established by <Picture 2>: %s" % first_sentence(captions[last_dst.name]))
            shot_parts.append(" ".join(bits))

        text = "\n\n".join([
            instr,
            "integrated_multimodal_description: " + " ".join(shot_parts),
            "overall_soundscape: Cavernous hall reverb under the dialogue, distant wind moving "
            "through stone corridors, soft fabric rustle as the robed figures move.",
            "non_diegetic_music: A cold, sinister orchestral theme: low sustained strings, sparse "
            "brass swells, slow tempo, quiet dynamics under the voices.",
        ])
        header = "\n".join([
            "# chunk: %s | test: T0003 | scene: S03 | mode: FL2VA" % cid,
            "# first_frame: %s | last_frame: %s" % (first_src.name, last_src.name),
            "# graph_length_seconds: %.3f" % duration,
            "# graph_length_frames: %d" % dur_frames,
            "# lines: %s" % (" ".join(r["id"] for _, r in spoken) or "none"),
            "", "",
        ])
        (run / ("%s.txt" % cid)).write_text(header + text, encoding="utf-8")

        g = json.loads(json.dumps(template))
        g["127"]["inputs"]["unet_name"] = "h3/minimax_h3_fl2va_pruned_int8_convrot.safetensors"
        g["132"]["inputs"]["value"] = duration
        g["138"]["inputs"]["value"] = text
        g["129"]["inputs"]["noise_seed"] = SEED
        g["92"]["inputs"]["filename_prefix"] = "video/%s_T0003_t01" % cid
        # replace ref2v node with ImageToVideo (fl2va)
        g["136"] = {
            "inputs": {
                "clip": ["128", 0],
                "vae": ["119", 0],
                "prompt": ["138", 0],
                "width": ["115", 0],
                "height": ["115", 1],
                "length": ["131", 1],
                "first_frame": ["137", 0],
                "last_frame": ["139", 0],
            },
            "class_type": "MiniMaxH3ImageToVideo",
            "_meta": {"title": "MiniMax H3 Image to Video (FL2VA)"},
        }
        g["137"] = {"inputs": {"image": first_dst.name}, "class_type": "LoadImage", "_meta": {"title": "First Frame"}}
        g["139"] = {"inputs": {"image": last_dst.name}, "class_type": "LoadImage", "_meta": {"title": "Last Frame"}}
        # remove turbo-lora branch (ref2v lora, never valid for fl2va) and wire guider straight to model
        for nid in ["141", "142", "143", "144", "145", "146"]:
            g.pop(nid, None)
        g["126"]["inputs"]["model"] = ["127", 0]
        g["124"]["inputs"]["steps"] = 20
        (run / ("%s.json" % cid)).write_text(json.dumps(g, indent=2), encoding="utf-8")
        print(cid, "frames=%d" % dur_frames, "shots=%d" % n_shots, "lines=%d" % len(spoken))

    (run / "captions.json").write_text(json.dumps(captions, indent=2), encoding="utf-8")
    (run / "manifest.md").write_text(
        "# T0003 — S03 FL2VA (first/last frame), source stills\n\n"
        "- Date: 2026-09-28\n"
        "- One variable vs T0002: mode. T0002 = ref2v with character refs; this = fl2va with the\n"
        "  chunk's first and last source stills as keyframes. Same chunks, same seed\n"
        "  (1125345046553186), same lengths, same dialogue assignment.\n"
        "- Weight: h3/minimax_h3_fl2va_pruned_int8_convrot.safetensors (official FL2VA).\n"
        "- Node: MiniMaxH3ImageToVideo (first_frame/last_frame). No turbo LoRA branch.\n"
        "- Prompt format: FL2VA instruction line + integrated_multimodal_description +\n"
        "  overall_soundscape + non_diegetic_music. Keyframe captions written by local\n"
        "  qwen3-vl-8b (LM Studio), stored in captions.json.\n"
        "- Question: is fflf a viable final-pipeline mode — does anchoring both ends of the\n"
        "  chunk hold composition and identity better than ref2v?\n\n"
        "| chunk | shots | first frame | last frame | lines |\n|---|---|---|---|---|\n"
        + "".join("| %s | %s | %s | %s | %s |\n" % (
            cid, " ".join(s.split(":")[1] for s in sids),
            find_still(sids[0].split(":")[1], "first").name,
            find_still(sids[-1].split(":")[1], "last").name,
            "") for cid, sids in GROUPS)
        + "\n## Verdict\n(Alex, after watching.)\n",
        encoding="utf-8")
    print("wrote", run)


if __name__ == "__main__":
    main()
