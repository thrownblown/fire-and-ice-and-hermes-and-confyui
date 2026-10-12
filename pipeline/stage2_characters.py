"""Stage 2: physical character notes per shot. No names from the VLM.

Checkpoint: manifests/character_pass.jsonl
Report: reports/character-pass.html
Model: qwen3-vl-8b q4. Sequential. Resume skips shot_ids already in the jsonl.
"""
import json
from pathlib import Path

from core.vlm_correlate import describe_people

ROOT = Path(r"E:/FNI")
MODEL = "qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s"
JSONL = ROOT / "manifests" / "character_pass.jsonl"
HTML = ROOT / "reports" / "character-pass.html"


def stills(shot_id):
    stem = shot_id.replace(":", "_")
    return sorted((ROOT / "stills" / "full").glob(f"{stem}_f*.jpg"))[:3]


def done_ids():
    if not JSONL.exists():
        return set()
    ids = set()
    for line in JSONL.read_text(encoding="utf-8").splitlines():
        if line.strip():
            ids.add(json.loads(line)["shot_id"])
    return ids


def write_html(rows, total):
    blocks = []
    for row in rows:
        frames = stills(row["shot_id"])
        imgs = "".join(
            f'<img src="../{f.relative_to(ROOT).as_posix()}" alt="">' for f in frames
        )
        people = row.get("people") or []
        if row.get("error"):
            body = f"<p class='err'>{row['error']}</p>"
        elif not people:
            body = "<p>no people</p>"
        else:
            items = []
            for person in people:
                items.append(
                    "<li>"
                    f"{person.get('sex','')} · {person.get('build','')} · "
                    f"hair {person.get('hair','')} · skin {person.get('skin','')} · "
                    f"{person.get('clothing','')} · {person.get('action','')}"
                    "<br><em>name: </em>"
                    "</li>"
                )
            body = (
                f"<p>men {row.get('count_men', 0)} · women {row.get('count_women', 0)}</p>"
                f"<ul>{''.join(items)}</ul>"
            )
        blocks.append(
            f"<article><h2>{row['shot_id']}</h2>"
            f"<div class='strip'>{imgs}</div>{body}</article>"
        )
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Character pass</title>
<style>
body {{ font-family: sans-serif; background: #111; color: #eee; }}
header {{ position: sticky; top: 0; background: #111; padding: 12px; border-bottom: 1px solid #333; }}
article {{ padding: 12px; border-bottom: 1px solid #222; }}
img {{ width: 240px; margin-right: 8px; }}
.err {{ color: #f66; }}
em {{ color: #888; }}
</style></head><body>
<header>Character pass — {len(rows)} / {total} shots. Names are blank on purpose.</header>
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
    JSONL.parent.mkdir(parents=True, exist_ok=True)
    pending = [s for s in shots if s["shot_id"] not in seen]
    print(f"todo {len(pending)} already {len(seen)}", flush=True)
    with JSONL.open("a", encoding="utf-8") as out:
        for i, shot in enumerate(pending, 1):
            paths = stills(shot["shot_id"])
            if not paths:
                row = {"shot_id": shot["shot_id"], "people": [], "error": "no_stills"}
            else:
                try:
                    raw = describe_people(MODEL, paths)
                    row = {
                        "shot_id": shot["shot_id"],
                        "count_men": raw.get("count_men") or 0,
                        "count_women": raw.get("count_women") or 0,
                        "people": raw.get("people") or [],
                        "error": "",
                    }
                except Exception as exc:
                    row = {
                        "shot_id": shot["shot_id"],
                        "people": [],
                        "error": f"{type(exc).__name__}: {exc}",
                    }
            out.write(json.dumps(row) + "\n")
            out.flush()
            print(f"{i}/{len(pending)} {shot['shot_id']} err={row.get('error','')}", flush=True)
            if i % 25 == 0:
                rows = [json.loads(l) for l in JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
                write_html(rows, len(shots))
    rows = [json.loads(l) for l in JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    write_html(rows, len(shots))
    print(f"wrote {HTML}", flush=True)


if __name__ == "__main__":
    main()
