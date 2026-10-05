"""Stage 5: group shots into 2-3 shot chunks a human can read.

No VLM. Reads shots.jsonl plus the character and composition jsonl.
Dialogue comes from ASR overlap (same clock as shot PTS), not cue order.

Output:
  reports/chunks/chunk_NNNN.md
  reports/chunk-index.html

Rules:
  - 2 or 3 shots, unless a single shot is already longer than 8s.
  - Stop adding when the next shot would push the chunk past 8s,
    once the chunk already has 2 shots.
  - A setting change starts a new chunk, once the current one has 2 shots.
  - A single shot longer than 8s is its own chunk.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(r"E:/FNI")
CHUNKS = ROOT / "reports" / "chunks"
INDEX = ROOT / "reports" / "chunk-index.html"
TARGET = 8.0
MIN_SHOTS = 2
MAX_SHOTS = 3


def load_jsonl(path):
    rows = {}
    p = Path(path)
    if not p.exists():
        return rows
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["shot_id"]] = row
    return rows


def stills(shot_id):
    stem = shot_id.replace(":", "_")
    return sorted((ROOT / "stills" / "full").glob(f"{stem}_f*.jpg"))[:3]


def setting_key(text):
    words = (text or "").lower().split()
    return " ".join(words[:3])


def overlap(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def best_shot_for(seg, group):
    """Attach a segment to the shot in this chunk with the largest overlap.

    A line that straddles two shots used to land in both. Pick one.
    """
    best = None
    best_ov = 0.0
    for shot in group:
        s0 = shot["start_pts"] / 24000
        s1 = shot["end_pts"] / 24000
        ov = overlap(s0, s1, seg["start"], seg["end"])
        if ov > best_ov:
            best_ov = ov
            best = shot["shot_id"]
    if best_ov < 0.3:
        return None
    return best


def assemble(shots, comp):
    chunks = []
    cur = []
    cur_dur = 0.0
    cur_set = None
    for shot in shots:
        dur = shot["duration_seconds"]
        key = setting_key(comp.get(shot["shot_id"], {}).get("setting", ""))
        if dur > TARGET:
            if cur:
                chunks.append(cur)
                cur, cur_dur, cur_set = [], 0.0, None
            chunks.append([shot])
            continue
        if not cur:
            cur, cur_dur, cur_set = [shot], dur, key
            continue
        too_long = len(cur) >= MIN_SHOTS and cur_dur + dur > TARGET
        full = len(cur) >= MAX_SHOTS
        if too_long or full:
            chunks.append(cur)
            cur, cur_dur, cur_set = [shot], dur, key
        else:
            cur.append(shot)
            cur_dur += dur
            if not cur_set:
                cur_set = key
    if cur:
        chunks.append(cur)
    return chunks


def person_line(person):
    bits = [
        person.get("sex") or "",
        person.get("build") or "",
        person.get("hair") or "",
        person.get("clothing") or "",
        person.get("action") or "",
    ]
    return ", ".join(b for b in bits if b)


def write_chunk(n, group, people, comp, asr, claimed):
    sid0 = group[0]["shot_id"]
    sid1 = group[-1]["shot_id"]
    dur = sum(s["duration_seconds"] for s in group)
    settings = []
    for s in group:
        setting = (comp.get(s["shot_id"], {}).get("setting") or "").strip()
        if setting and setting not in settings:
            settings.append(setting)
    who = []
    seen_names = []
    for s in group:
        for person in people.get(s["shot_id"], {}).get("people") or []:
            name = person.get("name") or ""
            line = person_line(person)
            label = f"{name}: {line}" if name else line
            if label and label not in who:
                who.append(label)
            if name and name not in seen_names:
                seen_names.append(name)
    lines = []
    lines.append(f"# Chunk {n:04d}")
    lines.append("")
    lines.append(f"Shots: {sid0} → {sid1} ({len(group)})")
    lines.append(f"Timecode: {group[0].get('start_tc','')} → {group[-1].get('end_tc','')}")
    lines.append(f"Duration: {dur:.2f}s")
    lines.append(f"Setting: {'; '.join(settings) or 'unknown'}")
    lines.append("")
    lines.append("## People")
    if who:
        for line in who:
            lines.append(f"- {line}")
    else:
        lines.append("- none noted")
    lines.append("")
    lines.append("## Shots")
    # One owner per ASR segment across the whole film, not per chunk.
    # Within the chunk, the shot with the larger overlap wins.
    owned = {}
    for seg in asr:
        key = (seg["start"], seg["end"], seg["text"].strip())
        if key in claimed:
            continue
        owner = best_shot_for(seg, group)
        if owner:
            owned.setdefault(owner, []).append(key)
    for keys in owned.values():
        for key in keys:
            claimed.add(key)
    for s in group:
        c = comp.get(s["shot_id"], {})
        dialogue = [k[2] for k in owned.get(s["shot_id"], [])]
        spoken = " / ".join(dialogue) if dialogue else "NO DIALOGUE"
        frames = stills(s["shot_id"])
        rels = " ".join(f.relative_to(ROOT).as_posix() for f in frames)
        lines.append(f"### {s['shot_id']}  {s.get('start_tc','')} → {s.get('end_tc','')}  ({s['duration_seconds']:.2f}s)")
        lines.append(f"- size: {c.get('shot_type','')} · angle: {c.get('angle','')}")
        lines.append(f"- setting: {c.get('setting','')}")
        lines.append(f"- motion: {c.get('motion','')}")
        for person in people.get(s["shot_id"], {}).get("people") or []:
            name = person.get("name") or "unnamed"
            lines.append(f"- person: {name} — {person_line(person)}")
        lines.append(f"- dialogue: {spoken}")
        if rels:
            lines.append(f"- frames: {rels}")
        lines.append("")
    path = CHUNKS / f"chunk_{n:04d}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "n": n,
        "path": path,
        "shots": group,
        "dur": dur,
        "setting": "; ".join(settings) or "unknown",
        "dialogue": any(owned.get(s["shot_id"]) for s in group),
        "names": seen_names,
    }


def write_index(rows):
    blocks = []
    for row in rows:
        thumbs = []
        for shot in row["shots"]:
            frames = stills(shot["shot_id"])
            if frames:
                rel = frames[0].relative_to(ROOT).as_posix()
                thumbs.append(f'<img src="../{rel}" alt="">')
        ids = " ".join(s["shot_id"] for s in row["shots"])
        flag = " ".join(row["names"]) if row["names"] else ("speech" if row["dialogue"] else "silent")
        blocks.append(
            "<article>"
            f"<h2><a href=\"chunks/{row['path'].name}\">Chunk {row['n']:04d}</a> "
            f"<span class='{flag}'>{flag}</span></h2>"
            f"<p>{row['shots'][0].get('start_tc','')} → {row['shots'][-1].get('end_tc','')} "
            f"· {row['dur']:.1f}s · {len(row['shots'])} shots</p>"
            f"<p>{html.escape(row['setting'])}</p>"
            f"<p class='ids'>{ids}</p>"
            f"<div class='strip'>{''.join(thumbs)}</div>"
            "</article>"
        )
    page = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Chunk index</title>
<style>
body {{ font-family: sans-serif; background: #111; color: #eee; margin: 0; }}
header {{ position: sticky; top: 0; background: #111; padding: 12px 16px; border-bottom: 1px solid #333; }}
article {{ padding: 12px 16px; border-bottom: 1px solid #222; }}
h2 {{ margin: 0 0 4px; font-size: 16px; }}
a {{ color: #9cf; }}
p {{ margin: 0 0 6px; color: #aaa; }}
.ids {{ color: #666; font-size: 12px; }}
img {{ width: 180px; margin-right: 8px; }}
.speech {{ color: #e6b84d; }}
.silent {{ color: #888; }}
</style></head><body>
<header>Chunk index — {len(rows)} chunks. Names come from the description rules, not the VLM. Unmatched stays unnamed.</header>
{''.join(blocks)}
</body></html>
"""
    INDEX.write_text(page, encoding="utf-8")


def load_srt(path):
    """Cues as {start, end, text} in seconds. Same shape stage 5 expects from ASR."""
    raw = Path(path).read_text(encoding="utf-8-sig")
    blocks = re.split(r"\n\s*\n", raw.strip())
    cues = []
    stamp = re.compile(
        r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)"
    )
    for block in blocks:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        m = stamp.search(lines[1] if not stamp.search(lines[0]) else lines[0])
        if not m:
            continue
        nums = [int(x) for x in m.groups()]
        def sec(h, mi, s, ms):
            return h * 3600 + mi * 60 + s + ms / 1000.0
        text_lines = lines[2:] if stamp.search(lines[1]) else lines[1:]
        text = " ".join(text_lines).replace("  ", " ").strip()
        text = text.replace(" - ", " / ")
        if text:
            cues.append({"start": sec(*nums[:4]), "end": sec(*nums[4:]), "text": text})
    return cues


def main():
    shots = [
        json.loads(line)
        for line in (ROOT / "shots.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    people = load_jsonl(ROOT / "manifests" / "character_names.jsonl")
    comp = load_jsonl(ROOT / "manifests" / "composition_pass.jsonl")
    srt = ROOT / "audio" / "Fire.and.Ice.1983.1080-en.srt"
    if srt.exists():
        asr = load_srt(srt)
        print(f"dialogue source: srt cues={len(asr)}")
    else:
        asr = [
            json.loads(line)
            for line in (ROOT / "audio" / "asr_segments.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        print(f"dialogue source: asr cues={len(asr)}")
    groups = assemble(shots, comp)
    CHUNKS.mkdir(parents=True, exist_ok=True)
    for old in CHUNKS.glob("chunk_*.md"):
        old.unlink()
    claimed = set()
    rows = [write_chunk(i, g, people, comp, asr, claimed) for i, g in enumerate(groups, 1)]
    write_index(rows)
    sizes = {}
    for row in rows:
        sizes[len(row["shots"])] = sizes.get(len(row["shots"]), 0) + 1
    spoken = sum(1 for row in rows if row["dialogue"])
    print(f"wrote {INDEX} chunks={len(rows)} sizes={sizes} with_speech={spoken}")


if __name__ == "__main__":
    main()
