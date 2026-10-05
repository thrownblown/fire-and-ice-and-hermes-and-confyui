"""Stage 4: order-based script alignment. Low confidence unless reviewed.

Does not call the VLM. Matches cue order to shots that have people,
using character-pass + composition-pass already on disk.
"""
import json
from pathlib import Path

from core.script import extract_pdf_text, parse_script

ROOT = Path(r"E:/FNI")
OUT = ROOT / "reports" / "script-alignment.html"


def load_jsonl(path):
    rows = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["shot_id"]] = row
    return rows


def stills(shot_id):
    stem = shot_id.replace(":", "_")
    return sorted((ROOT / "stills" / "full").glob(f"{stem}_f*.jpg"))[:3]


def main():
    shots = [
        json.loads(line)
        for line in (ROOT / "shots.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    people = load_jsonl(ROOT / "manifests" / "character_pass.jsonl")
    comp = load_jsonl(ROOT / "manifests" / "composition_pass.jsonl")
    cues = parse_script(extract_pdf_text(ROOT / "docs" / "doc.pdf"))
    # Spread cues across shots that have people, in order. Action-only shots get no line.
    spoken = [s for s in shots if people.get(s["shot_id"], {}).get("people")]
    blocks = []
    cue_i = 0
    for shot in shots:
        sid = shot["shot_id"]
        p = people.get(sid, {})
        c = comp.get(sid, {})
        frames = stills(sid)
        imgs = "".join(f'<img src="../{f.relative_to(ROOT).as_posix()}">' for f in frames)
        notes = []
        for person in p.get("people") or []:
            notes.append(
                f"{person.get('sex','')} {person.get('hair','')} — {person.get('action','')}"
            )
        if sid in {s["shot_id"] for s in spoken} and cue_i < len(cues) and p.get("people"):
            # one cue per speaking-candidate shot, in order. Confidence stays LOW.
            line = cues[cue_i].text
            cue_i += 1
            conf = "LOW"
            dialogue = line
        else:
            conf = "UNMATCHED"
            dialogue = "NO DIALOGUE"
        blocks.append(
            "<article>"
            f"<h2>{sid} <span class='{conf.lower()}'>{conf}</span></h2>"
            f"<p>{shot.get('start_tc','')} → {shot.get('end_tc','')}</p>"
            f"<div class='strip'>{imgs}</div>"
            f"<p>{c.get('shot_type','')} · {c.get('setting','')}</p>"
            f"<ul>{''.join(f'<li>{n}</li>' for n in notes)}</ul>"
            f"<blockquote>{dialogue}</blockquote>"
            "</article>"
        )
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Script alignment</title>
<style>
body {{ font-family: sans-serif; background: #111; color: #eee; }}
header {{ position: sticky; top: 0; background: #111; padding: 12px; border-bottom: 1px solid #333; }}
article {{ padding: 12px; border-bottom: 1px solid #222; }}
img {{ width: 220px; margin-right: 8px; }}
.low {{ color: #e6b84d; }}
.unmatched {{ color: #888; }}
blockquote {{ border-left: 3px solid #444; margin: 8px 0; padding-left: 8px; color: #ddd; }}
</style></head><body>
<header>Script alignment — {len(shots)} shots, {len(cues)} cues. Order-based. Every match is LOW until a human confirms it. Names were not assigned.</header>
{''.join(blocks)}
</body></html>"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} cues_used={cue_i}/{len(cues)}")


if __name__ == "__main__":
    main()
