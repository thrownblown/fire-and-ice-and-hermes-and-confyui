"""S03 stage 5 prompts and stage 6 validator. Does not queue ComfyUI."""
import csv
import json
from pathlib import Path

ROOT = Path(r"E:/FNI")
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
ACTION = {
    "shot:00067": "The pale woman in the purple gown stands and looks up, a slight smile.",
    "shot:00068": "The white-haired man lowers his hand from his face.",
    "shot:00069": "The pale woman in the purple gown gestures, then crosses her arms.",
    "shot:00070": "The white-haired man, seated, speaks.",
    "shot:00071": "The pale woman in the purple gown extends an arm as she speaks.",
    "shot:00072": "The white-haired man turns his head slightly while speaking.",
    "shot:00073": "The pale woman in the purple gown holds a scroll and addresses three hooded envoys.",
    "shot:00074": "The pale woman is in front. The white-haired man sits behind her and gestures.",
}
VISIBLE = {
    "shot:00067": ["JULIANA"],
    "shot:00068": ["NEKRON"],
    "shot:00069": ["JULIANA"],
    "shot:00070": ["NEKRON"],
    "shot:00071": ["JULIANA"],
    "shot:00072": ["NEKRON"],
    "shot:00073": ["JULIANA", "ENVOY"],
    "shot:00074": ["JULIANA", "NEKRON"],
}
DESC = {"JULIANA": JULIANA, "NEKRON": NEKRON, "ENVOY": ENVOY}
REFS = {
    "JULIANA": ["juliana_portrait.jpeg", "juliana_chains.jpeg"],
    "NEKRON": ["nekron_shot_00068.jpg", "nekron_shot_00070.jpg"],
    "ENVOY": ["envoy_shot_00073.jpg", "envoy_shot_00075.jpg"],
}
CHUNKS = {
    "s03-c01": ["shot:00067", "shot:00068", "shot:00069"],
    "s03-c02": ["shot:00070", "shot:00071", "shot:00072"],
    "s03-c03": ["shot:00073", "shot:00074"],
}
PREV = {
    "s03-c01": "The glacier has taken the North Village.",
    "s03-c02": "Nekron thanks his mother. The Great Plain is all that stands before Fire Keep.",
    "s03-c03": "Juliana says Jarol will not submit. Nekron says perhaps.",
}
NXT = {
    "s03-c01": "Juliana calls the distance long. Nekron says they may not have to travel it.",
    "s03-c02": "Nekron tells the envoys to present the demands at Fire Keep.",
    "s03-c03": "The envoys leave for Fire Keep.",
}


def sec(tc):
    h, mi, rest = tc.replace(",", ".").split(":")
    return int(h) * 3600 + int(mi) * 60 + float(rest)


def h3_frames(seconds):
    seconds = max(4.0, min(15.0, seconds))
    raw = max(5, round(seconds * 24))
    snapped = raw + (5 - (raw % 17)) % 17
    return snapped, snapped / 24.0


def main():
    shots = []
    for line in (ROOT / "shots.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        s = json.loads(line)
        n = int(s["shot_id"].split(":")[1])
        if 67 <= n <= 74:
            shots.append(s)
    by_id = {s["shot_id"]: s for s in shots}
    rows = list(csv.DictReader((ROOT / "script" / "dialogue-timeline.tsv").open(encoding="utf-8"), delimiter="\t"))
    s03 = [r for r in rows if r["scene"] == "S03"]

    def lines_in(shot):
        got = []
        for r in s03:
            mid = (sec(r["start"]) + sec(r["end"])) / 2
            if shot["start_pts"] / 24000 <= mid < shot["end_pts"] / 24000:
                got.append(r)
        return got

    out_dir = ROOT / "s03" / "prompts"
    out_dir.mkdir(exist_ok=True)
    review = ["# S03 prompt review", ""]

    for cid, sids in CHUNKS.items():
        group = [by_id[s] for s in sids]
        t0 = group[0]["start_pts"] / 24000
        dur = sum(s["duration_seconds"] for s in group)
        frames, length_s = h3_frames(dur)
        spoken = [(s, r) for s in group for r in lines_in(s)]
        names = []
        for _, r in spoken:
            if r["speaker"] not in names:
                names.append(r["speaker"])
        for s in group:
            for name in VISIBLE[s["shot_id"]]:
                if name not in names:
                    names.append(name)
        pics = []
        pic_of = {name: [] for name in names}
        for name in names:
            for fn in REFS.get(name, []):
                pics.append((name, fn))
                pic_of[name].append(len(pics))
        subs = []
        for i, name in enumerate(names, 1):
            seen = ", ".join("<Picture %d>" % n for n in pic_of[name]) or "no reference still"
            subs.append("<Subject %d>: %s, %s. Seen in %s." % (i, name, DESC[name], seen))
        pic_lines = []
        for n, (name, _fn) in enumerate(pics, 1):
            pic_lines.append(
                "<Picture %d>: a still of %s. Anchors identity only. "
                "Do not import the pose or the action from this still." % (n, name)
            )
        subject_of = {name: i for i, name in enumerate(names, 1)}
        shot_lines = []
        for idx, s in enumerate(group, 1):
            off = s["start_pts"] / 24000 - t0
            says = []
            for ss, r in spoken:
                if ss["shot_id"] != s["shot_id"]:
                    continue
                visible = r["speaker"] in VISIBLE[s["shot_id"]]
                tag = "" if visible else " (off-screen)"
                says.append(
                    "<Subject %d>%s says, <d>[English] %s</d>"
                    % (subject_of[r["speaker"]], tag, r["text"])
                )
            shot_lines.append(
                "[Shot %d] (%.1fs) %s. %s %s"
                % (idx, off, CAMERA[s["shot_id"]], ACTION[s["shot_id"]], " ".join(says))
            )
        ids = [r["id"] for _, r in spoken]
        header = [
            "# chunk: %s | scene: S03 Ice Peak: Juliana and Nekron send envoys" % cid,
            "# source: %s-%s | lines: %s-%s" % (group[0]["start_tc"], group[-1]["end_tc"], ids[0], ids[-1]),
            "# prev: %s | next: %s" % (PREV[cid], NXT[cid]),
            "# graph_length_seconds: %.3f" % length_s,
            "# graph_length_frames: %d" % frames,
            "# source_duration_seconds: %.2f" % dur,
            "",
        ]
        body = ["subject_definitions:", *subs, *pic_lines, "",
                "summary: reference generation + audio reference", "", "retention_analysis:"]
        for i, name in enumerate(names, 1):
            appears = []
            for idx, s in enumerate(group, 1):
                on_screen = name in VISIBLE[s["shot_id"]]
                speaks = any(r["speaker"] == name and ss["shot_id"] == s["shot_id"] for ss, r in spoken)
                if on_screen or speaks:
                    appears.append("[Shot %d]" % idx)
            body.append(
                "<Subject %d> (appears in %s): attribute_transfer — retains the traits listed above."
                % (i, ", ".join(appears))
            )
        body += [
            "",
            "detailed_description: rotoscope painted animation, Ice Peak throne hall. "
            "Cool cavern light, painted backgrounds, inked figures.",
            *shot_lines,
            "",
            "overall_soundscape: cavernous hall reverb, distant wind. No music under the dialogue.",
            "",
            "non_diegetic_music: cold, sinister theme.",
            "",
        ]
        text = "\n".join(header + body)
        (out_dir / ("%s.txt" % cid)).write_text(text, encoding="utf-8")
        review += ["## %s" % cid, "", text, ""]
    (ROOT / "s03" / "5-review.md").write_text("\n".join(review), encoding="utf-8")

    checks = []

    def add(ok, msg):
        checks.append(("OK" if ok else "FAIL", msg))

    seen = []
    for cid in CHUNKS:
        text = (out_dir / ("%s.txt" % cid)).read_text(encoding="utf-8")
        add("Ice Peak throne hall" in text, "%s uses the canonical location" % cid)
        add("At 00:00:02.5" not in text, "%s has no placeholder 2.5s offset" % cid)
        for r in s03:
            if ("<d>[English] %s</d>" % r["text"]) in text:
                seen.append(r["id"])
                head = text.split("detailed_description")[0]
                add(r["speaker"] in head, "%s speaker %s is defined" % (r["id"], r["speaker"]))
                add(r["text"] in text, "%s text is complete" % r["id"])
    add(seen == ["L%03d" % n for n in range(23, 34)], "lines once, in order: " + " ".join(seen))
    c02 = (out_dir / "s03-c02.txt").read_text(encoding="utf-8")
    c01 = (out_dir / "s03-c01.txt").read_text(encoding="utf-8")
    add("He will not submit." in c02 and "Perhaps." in c02, "L030 and L031 share s03-c02")
    add("He will not submit." not in c01, "L030 is not in s03-c01")
    fails = sum(1 for mark, _ in checks if mark == "FAIL")
    report = ["# S03 validation", ""]
    for mark, msg in checks:
        report.append("- %s %s" % (mark, msg))
    report += ["", "%d passed, %d failed." % (len(checks) - fails, fails)]
    (ROOT / "s03" / "6-validation.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("prompts", len(list(out_dir.glob("*.txt"))), "fails", fails)


if __name__ == "__main__":
    main()
