"""Stage 6: H3 prompts for chunks that already have a named lead.

No VLM. No ComfyUI. Reads the chunk markdown stage 5 just wrote and
the name jsonl. A chunk with nobody named is skipped — text-only
subjects drift, and that was the failure this pipeline is avoiding.

Output:
  reports/h3-prompts/chunk_NNNN.txt
  reports/h3-prompt-review.html
"""
import html
import re
from pathlib import Path

ROOT = Path(r"E:/FNI")
CHUNKS = ROOT / "reports" / "chunks"
OUT = ROOT / "reports" / "h3-prompts"
REVIEW = ROOT / "reports" / "h3-prompt-review.html"

TRAITS = {
    "Teegra": "the woman with long black hair and a light purple two-piece, gold earrings",
    "Larn": "the blond man, muscular, brown belt with a gold buckle, bone necklace",
    "Nekron": "the pale man with long white hair in a dark purple robe",
}


def parse_chunk(path):
    text = path.read_text(encoding="utf-8")
    shots = []
    cur = None
    names = []
    duration = None
    for line in text.splitlines():
        if line.startswith("Duration: ") and duration is None:
            try:
                duration = float(line.split(":", 1)[1].strip().rstrip("s"))
            except ValueError:
                duration = None
        if line.startswith("### "):
            if cur:
                shots.append(cur)
            cur = {"head": line[4:], "people": [], "dialogue": "", "setting": "", "frames": []}
        elif cur is None:
            if line.startswith("- Teegra:") or line.startswith("- Larn:") or line.startswith("- Nekron:"):
                name = line.split(":", 1)[0][2:]
                if name not in names:
                    names.append(name)
        else:
            if line.startswith("- person: "):
                cur["people"].append(line[len("- person: "):])
                name = line.split("—")[0].replace("- person: ", "").strip()
                if name in TRAITS and name not in names:
                    names.append(name)
            elif line.startswith("- dialogue: "):
                cur["dialogue"] = line[len("- dialogue: "):]
            elif line.startswith("- setting: "):
                cur["setting"] = line[len("- setting: "):]
            elif line.startswith("- frames: "):
                cur["frames"] = line[len("- frames: "):].split()
    if cur:
        shots.append(cur)
    return names, shots, duration


def h3_frames(seconds):
    """Snap to the 17k+5 grid H3 was trained on, clamped to 4–15s.

    Graph length was hardcoded at 15s, which snapped to ~11s and ignored
    the chunk. Drive it from the chunk duration instead.
    """
    seconds = max(4.0, min(15.0, seconds))
    raw = max(5, round(seconds * 24))
    snapped = raw + (5 - (raw % 17)) % 17
    return snapped, snapped / 24.0


def prompt_for(names, shots, duration):
    subs = []
    pics = []
    n_pic = 1
    pic_of = {}
    for name in names:
        pic_of[name] = n_pic
        subs.append(
            f"<Subject {len(subs)+1}>: {TRAITS[name]}. Seen in <Picture {n_pic}>."
        )
        pics.append(
            f"<Picture {n_pic}>: a still of {TRAITS[name]}. "
            f"Anchors their first appearance. Do not import the pose or the action from this still."
        )
        n_pic += 1
    retains = []
    for i, name in enumerate(names, 1):
        appears = []
        for si, shot in enumerate(shots, 1):
            if any(name in p for p in shot["people"]):
                appears.append(f"[Shot {si}]")
        if not appears:
            appears = ["[Shot 1]"]
        retains.append(
            f"<Subject {i}> (appears in {', '.join(appears)}): "
            f"attribute_transfer — retains the traits listed above."
        )
    shot_lines = []
    t = 0.0
    for i, shot in enumerate(shots, 1):
        who = ", ".join(p.split("—")[0].strip() for p in shot["people"] if "unnamed" not in p) or "the figures"
        setting = shot["setting"] or "the location"
        spoken = ""
        if shot["dialogue"] and shot["dialogue"] != "NO DIALOGUE":
            line = shot["dialogue"].split(" / ")[0].strip().rstrip(".")
            if len(line) > 90:
                line = line[:87].rsplit(" ", 1)[0]
            spoken = f' <Subject 1> (S1) says, <d>[English] {line}.</d>'
        if i == 1:
            shot_lines.append(
                f"[Shot 1] The camera holds. {who} in {setting}.{spoken}"
            )
        else:
            t += 2.5
            shot_lines.append(
                f"[Shot {i}] At 00:00:{t:04.1f}, the camera pushes in slowly. {who} in {setting}.{spoken}"
            )
    place = shots[0]["setting"] or "the scene"
    frames, length_s = h3_frames(duration or 8.0)
    header = [
        f"# graph_length_seconds: {length_s:.3f}",
        f"# graph_length_frames: {frames}",
        f"# source_duration_seconds: {duration if duration is not None else 'unknown'}",
        "",
    ]
    return "\n".join(header + [
        "subject_definitions:",
        *subs,
        *pics,
        "",
        "summary: reference generation + audio reference",
        "",
        "retention_analysis:",
        *retains,
        "",
        "detailed_description: rotoscope painted animation, "
        f"{place}. Cool light, painted backgrounds, inked figures.",
        *shot_lines,
        "",
        "overall_soundscape: wind, footsteps, and the room tone of the place. No music.",
        "",
        "non_diegetic_music: N/A",
        "",
    ])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("chunk_*.txt"):
        old.unlink()
    blocks = []
    written = 0
    skipped = 0
    for path in sorted(CHUNKS.glob("chunk_*.md")):
        names, shots, duration = parse_chunk(path)
        if not names or not shots:
            skipped += 1
            continue
        text = prompt_for(names, shots, duration)
        dest = OUT / (path.stem + ".txt")
        dest.write_text(text, encoding="utf-8")
        written += 1
        thumbs = []
        for shot in shots:
            if shot["frames"]:
                thumbs.append(f'<img src="../{shot["frames"][0]}" alt="">')
        blocks.append(
            "<article>"
            f"<h2><a href=\"h3-prompts/{dest.name}\">{path.stem}</a> "
            f"<span class='who'>{html.escape(', '.join(names))}</span></h2>"
            f"<div class='strip'>{''.join(thumbs)}</div>"
            f"<pre>{html.escape(text)}</pre>"
            "</article>"
        )
    page = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>H3 prompt review</title>
<style>
body {{ font-family: sans-serif; background: #111; color: #eee; margin: 0; }}
header {{ position: sticky; top: 0; background: #111; padding: 12px 16px; border-bottom: 1px solid #333; }}
article {{ padding: 12px 16px; border-bottom: 1px solid #222; }}
h2 {{ margin: 0 0 8px; font-size: 16px; }}
a {{ color: #9cf; }}
.who {{ color: #e6b84d; }}
img {{ width: 200px; margin-right: 8px; }}
pre {{ white-space: pre-wrap; color: #ccc; font-size: 13px; }}
</style></head><body>
<header>H3 prompts — {written} written, {skipped} skipped for having no named lead. Names are rule matches, not reviewed. Read the prompt next to the frames before queueing anything.</header>
{''.join(blocks)}
</body></html>
"""
    REVIEW.write_text(page, encoding="utf-8")
    print(f"wrote {written} skipped {skipped} review {REVIEW}")


if __name__ == "__main__":
    main()
