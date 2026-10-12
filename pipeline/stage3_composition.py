"""Stage 3: composition notes per shot. No invented location names.

Checkpoint: manifests/composition_pass.jsonl
Report: reports/composition-pass.html
"""
import json
from pathlib import Path

from core.vlm_correlate import call_vlm, SYSTEM_PROMPT

ROOT = Path(r"E:/FNI")
MODEL = "qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s"
JSONL = ROOT / "manifests" / "composition_pass.jsonl"
HTML = ROOT / "reports" / "composition-pass.html"

PROMPT = (
    "Describe the composition of these frames. "
    "shot_type is one of: extreme close-up, close-up, medium, wide, extreme wide. "
    "angle is one of: eye-level, low, high, bird's eye, dutch, unknown. "
    "setting is a short noun phrase for the place actually visible. Do not invent a proper name. "
    "lighting is one short phrase. "
    "elements is a list of visible things (fire, ice, weapons, creatures, architecture). "
    "motion is what changes across the frames, or 'static' if nothing obvious. "
    "Respond with JSON: "
    '{"shot_type": "", "angle": "", "setting": "", "lighting": "", '
    '"elements": [], "motion": ""}'
)


def stills(shot_id):
    stem = shot_id.replace(":", "_")
    return sorted((ROOT / "stills" / "full").glob(f"{stem}_f*.jpg"))[:3]


def done_ids():
    if not JSONL.exists():
        return set()
    return {
        json.loads(line)["shot_id"]
        for line in JSONL.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def write_html(rows, total):
    blocks = []
    for row in rows:
        frames = stills(row["shot_id"])
        imgs = "".join(
            f'<img src="../{f.relative_to(ROOT).as_posix()}" alt="">' for f in frames
        )
        if row.get("error"):
            body = f"<p class='err'>{row['error']}</p>"
        else:
            elems = ", ".join(row.get("elements") or [])
            body = (
                f"<p>{row.get('shot_type','')} · {row.get('angle','')}</p>"
                f"<p>{row.get('setting','')}</p>"
                f"<p>{row.get('lighting','')}</p>"
                f"<p>{elems}</p>"
                f"<p>{row.get('motion','')}</p>"
            )
        blocks.append(f"<article><h2>{row['shot_id']}</h2><div class='strip'>{imgs}</div>{body}</article>")
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Composition pass</title>
<style>
body {{ font-family: sans-serif; background: #111; color: #eee; }}
header {{ position: sticky; top: 0; background: #111; padding: 12px; border-bottom: 1px solid #333; }}
article {{ padding: 12px; border-bottom: 1px solid #222; }}
img {{ width: 240px; margin-right: 8px; }}
.err {{ color: #f66; }}
p {{ margin: 4px 0; }}
</style></head><body>
<header>Composition pass — {len(rows)} / {total}</header>
{''.join(blocks)}
</body></html>"""
    HTML.parent.mkdir(parents=True, exist_ok=True)
    HTML.write_text(html, encoding="utf-8")


def main():
    shots = [
        json.loads(line)
        for line in (ROOT / "shots.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    seen = done_ids()
    pending = [s for s in shots if s["shot_id"] not in seen]
    JSONL.parent.mkdir(parents=True, exist_ok=True)
    print(f"todo {len(pending)} already {len(seen)}", flush=True)
    with JSONL.open("a", encoding="utf-8") as out:
        for i, shot in enumerate(pending, 1):
            paths = stills(shot["shot_id"])
            if not paths:
                row = {"shot_id": shot["shot_id"], "error": "no_stills"}
            else:
                try:
                    raw = call_vlm(MODEL, PROMPT, paths, system=SYSTEM_PROMPT)
                    row = {
                        "shot_id": shot["shot_id"],
                        "shot_type": raw.get("shot_type") or "",
                        "angle": raw.get("angle") or "",
                        "setting": raw.get("setting") or "",
                        "lighting": raw.get("lighting") or "",
                        "elements": raw.get("elements") or [],
                        "motion": raw.get("motion") or "",
                        "error": "",
                    }
                except Exception as exc:
                    row = {"shot_id": shot["shot_id"], "error": f"{type(exc).__name__}: {exc}"}
            out.write(json.dumps(row) + "\n")
            out.flush()
            print(f"{i}/{len(pending)} {shot['shot_id']} {row.get('setting','')} err={row.get('error','')}", flush=True)
            if i % 25 == 0:
                rows = [json.loads(l) for l in JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
                write_html(rows, len(shots))
    rows = [json.loads(l) for l in JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    write_html(rows, len(shots))
    print(f"wrote {HTML}", flush=True)


if __name__ == "__main__":
    main()
