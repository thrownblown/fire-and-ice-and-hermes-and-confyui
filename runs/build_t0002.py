"""T0002: S03 split at action beats. Same refs and seed as T0001. No render."""
import csv
import json
import shutil
from pathlib import Path

ROOT = Path(r"E:/FNI")
SEED = 1125345046553186
CAP = 15.0

JULIANA = (
    "extremely pale white skin, angular face, crimson lips, long straight jet-black hair "
    "with small white beads at the crown, long silver dagger-shaped earrings, "
    "a deep purple long-sleeved gown with a plunging neckline and hip-high slits"
)
NEKRON = "pale skin, long white hair, a dark purple robe"
ENVOY = (
    "a hooded subhuman envoy in a dark robe, yellow eyes, dark skin, sometimes masked. "
    "Not the pale woman. Not the white-haired man."
)
DESC = {"JULIANA": JULIANA, "NEKRON": NEKRON, "ENVOY": ENVOY}
VISIBLE = {
    "shot:00067": ["JULIANA"], "shot:00068": ["NEKRON"], "shot:00069": ["JULIANA"],
    "shot:00070": ["NEKRON"], "shot:00071": ["JULIANA"], "shot:00072": ["NEKRON"],
    "shot:00073": ["JULIANA", "ENVOY"], "shot:00074": ["JULIANA", "NEKRON"],
}
CAMERA = {
    "shot:00067": "medium, three-quarter angle, static",
    "shot:00068": "medium, straight-on, static",
    "shot:00069": "medium, three-quarter angle, static",
    "shot:00070": "medium, three-quarter angle, static",
    "shot:00071": "medium, three-quarter angle, static",
    "shot:00072": "medium close-up, three-quarter angle, static",
    "shot:00073": "medium, straight-on, static",
    "shot:00074": "close-up, three-quarter angle, static",
}
GROUPS = [
    ("s03-c01", ["shot:00067"]),
    ("s03-c02", ["shot:00068", "shot:00069"]),
    ("s03-c03", ["shot:00070", "shot:00071"]),
    ("s03-c04", ["shot:00072"]),
    ("s03-c05", ["shot:00073", "shot:00074"]),
]
REF_FILES = {
    "JULIANA": ["juliana_portrait.jpeg", "juliana_chains.jpeg"],
    "NEKRON": ["nekron_shot_00068.jpg", "nekron_shot_00070.jpg"],
    "ENVOY": ["envoy_shot_00073.jpg", "envoy_shot_00075.jpg"],
}
REF_NODES = ["137", "139", "147", "148", "149", "150"]


def sec(tc):
    h, mi, rest = tc.replace(",", ".").split(":")
    return int(h) * 3600 + int(mi) * 60 + float(rest)


def h3_frames(seconds):
    seconds = max(4.0, min(CAP, seconds))
    raw = max(5, round(seconds * 24))
    return raw + (5 - (raw % 17)) % 17


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

    run = ROOT / "runs" / "T0002_s03_ref2v-actionsplit"
    (run / "input").mkdir(parents=True, exist_ok=True)
    for name in ["juliana_portrait.jpeg", "juliana_chains.jpeg", "nekron_shot_00068.jpg",
                 "nekron_shot_00070.jpg", "envoy_shot_00073.jpg", "envoy_shot_00075.jpg"]:
        shutil.copy(ROOT / "runs" / "T0001_s03_ref2v-srcstills" / "input" / name, run / "input" / name)
    template = json.loads((ROOT / "graphs" / "video_minimax_h3_r2v.json").read_text(encoding="utf-8"))

    for cid, sids in GROUPS:
        group = [shots[s] for s in sids]
        t0 = group[0]["start_pts"] / 24000
        dur = group[-1]["end_pts"] / 24000 - t0
        spoken = [(s, r) for s in group for r in lines_in(s["shot_id"])]
        names = []
        for _, r in spoken:
            if r["speaker"] not in names:
                names.append(r["speaker"])
        for s in group:
            for name in VISIBLE[s["shot_id"]]:
                if name not in names:
                    names.append(name)
        pic_of = {n: [] for n in names}
        pic_names = []
        for name in names:
            for _fn in REF_FILES.get(name, []):
                pic_names.append(name)
                pic_of[name].append(len(pic_names))
        subs = []
        for i, name in enumerate(names, 1):
            seen = ", ".join("<Picture %d>" % n for n in pic_of[name]) or "no reference still"
            subs.append("<Subject %d>: %s, %s. Seen in %s." % (i, name, DESC[name], seen))
        pic_lines = [
            "<Picture %d>: a still of %s. Anchors identity only. Do not import the pose or the action from this still."
            % (n, name) for n, name in enumerate(pic_names, 1)
        ]
        subject_of = {name: i for i, name in enumerate(names, 1)}
        shot_lines = []
        for idx, s in enumerate(group, 1):
            off = s["start_pts"] / 24000 - t0
            says = []
            for ss, r in spoken:
                if ss["shot_id"] != s["shot_id"]:
                    continue
                tag = "" if r["speaker"] in VISIBLE[s["shot_id"]] else " (off-screen)"
                says.append("<Subject %d>%s says, <d>[English] %s</d>" % (subject_of[r["speaker"]], tag, r["text"]))
            shot_lines.append("[Shot %d] (%.1fs) %s. %s" % (idx, off, CAMERA[s["shot_id"]], " ".join(says)))
        frames = h3_frames(dur)
        ids = [r["id"] for _, r in spoken]
        text = "\n".join([
            "# chunk: %s | test: T0002 | scene: S03" % cid,
            "# source: %s-%s | lines: %s" % (group[0]["start_tc"], group[-1]["end_tc"], " ".join(ids) or "none"),
            "# graph_length_seconds: %.3f" % (frames / 24.0),
            "# graph_length_frames: %d" % frames,
            "# source_duration_seconds: %.2f" % dur,
            "",
            "subject_definitions:", *subs, *pic_lines, "",
            "summary: reference generation + audio reference", "",
            "retention_analysis:",
            *["<Subject %d>: attribute_transfer — retains the traits listed above." % i for i in range(1, len(names) + 1)],
            "",
            "detailed_description: rotoscope painted animation, Ice Peak throne hall. Cool cavern light, painted backgrounds, inked figures.",
            *shot_lines, "",
            "overall_soundscape: cavernous hall reverb, distant wind. No music under the dialogue.", "",
            "non_diegetic_music: cold, sinister theme.", "",
        ])
        (run / ("%s.txt" % cid)).write_text(text, encoding="utf-8")
        g = json.loads(json.dumps(template))
        g["132"]["inputs"]["value"] = frames / 24.0
        g["138"]["inputs"]["value"] = text.split("\n\n", 1)[1]
        g["129"]["inputs"]["noise_seed"] = SEED
        g["92"]["inputs"]["filename_prefix"] = "video/%s_T0002_t01" % cid
        node = g["136"]["inputs"]
        for key in [k for k in node if k.startswith("ref_images.ref_image_")]:
            node.pop(key)
        files = []
        for name in names:
            files += REF_FILES.get(name, [])
        for i, image in enumerate(files):
            nid = REF_NODES[i]
            g[nid] = {"inputs": {"image": image}, "class_type": "LoadImage", "_meta": {"title": "Load Image %d" % i}}
            node["ref_images.ref_image_%d" % i] = [nid, 0]
        for nid in REF_NODES[len(files):]:
            g.pop(nid, None)
        (run / ("%s.json" % cid)).write_text(json.dumps(g, indent=2), encoding="utf-8")
        print(cid, "%.2fs" % dur, frames, ids, len(files))

    (run / "manifest.md").write_text(
        "# T0002 — S03 ref2v, split at action beats\n\n"
        "- Date: 2026-09-27\n"
        "- One variable vs T0001: chunk size. T0001 had 3 chunks. This has 5, split where the action changes.\n"
        "- Same refs, same seed (1125345046553186), same model, same sampler as T0001.\n"
        "- Question: does a smaller action beat stop the glitches a long prompt causes?\n\n"
        "| chunk | shots | lines |\n|---|---|---|\n"
        "| s03-c01 | 00067 | L023 L024 |\n"
        "| s03-c02 | 00068 00069 | L025 L026 |\n"
        "| s03-c03 | 00070 00071 | L027 L028 L029 |\n"
        "| s03-c04 | 00072 | L030 L031 |\n"
        "| s03-c05 | 00073 00074 | L032 L033 |\n\n"
        "## Verdict\n(Alex, after watching.)\n",
        encoding="utf-8")
    print("wrote", run)


if __name__ == "__main__":
    main()
