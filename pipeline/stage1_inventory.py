"""Stage 1: browsable shot inventory. No VLM."""
import json
from pathlib import Path

ROOT = Path(r"E:/FNI")
OUT = ROOT / "reports" / "shot-inventory.html"


def stills(shot_id):
    stem = shot_id.replace(":", "_")
    return sorted((ROOT / "stills" / "full").glob(f"{stem}_f*.jpg"))


def main():
    shots = [
        json.loads(line)
        for line in (ROOT / "shots.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows = []
    for shot in shots:
        frames = stills(shot["shot_id"])
        imgs = []
        for frame in frames[:3]:
            rel = frame.relative_to(ROOT).as_posix()
            imgs.append(f'<img src="../{rel}" alt="{frame.name}">')
        while len(imgs) < 3:
            imgs.append("<div class='missing'>no frame</div>")
        rows.append(
            "<article>"
            f"<h2>{shot['shot_id']}</h2>"
            f"<p>{shot.get('start_tc','')} → {shot.get('end_tc','')} "
            f"· {shot.get('duration_seconds', 0):.2f}s</p>"
            f"<div class='strip'>{''.join(imgs)}</div>"
            "</article>"
        )
    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Fire and Ice — shot inventory</title>
<style>
body {{ font-family: sans-serif; background: #111; color: #eee; margin: 0; }}
header {{ position: sticky; top: 0; background: #111; padding: 12px 16px; border-bottom: 1px solid #333; }}
article {{ padding: 12px 16px; border-bottom: 1px solid #222; }}
h2 {{ margin: 0 0 4px; font-size: 16px; }}
p {{ margin: 0 0 8px; color: #aaa; }}
.strip {{ display: flex; gap: 8px; }}
img {{ width: 280px; height: auto; background: #000; }}
.missing {{ width: 280px; height: 160px; background: #222; color: #666; display: flex; align-items: center; justify-content: center; }}
</style>
</head>
<body>
<header><strong>Shot inventory</strong> — {len(shots)} shots. Start | mid | end. No analysis.</header>
{''.join(rows)}
</body>
</html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} shots={len(shots)}")


if __name__ == "__main__":
    main()
