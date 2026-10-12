"""Run describe_people + describe_location on a spread of stills to refine the prompts."""
import json
from pathlib import Path

from core.vlm_correlate import describe_creatures, describe_location, describe_people

MODEL = "qwen3-vl-8b-instruct-abliterated-v2.0@f16"
shots = [json.loads(l) for l in open("shots.jsonl", encoding="utf-8")]

blank = {"shot:00001", "shot:00003", "shot:00004", "shot:00005", "shot:01307", "shot:01308"}
pool = [s for s in shots if s["shot_id"] not in blank]

n = 6
step = len(pool) // n
picked = [pool[i * step] for i in range(n)]

for s in picked:
    sid = s["shot_id"].replace(":", "_")
    imgs = sorted(Path("stills/full").glob(f"{sid}_f*.jpg"))
    t = round(s["start_pts"] / 24000 / 60, 1)
    print(f"\n=== {s['shot_id']} @ {t} min ===")
    try:
        print("  people:  ", json.dumps(describe_people(MODEL, imgs[:3])))
        print("  location:", json.dumps(describe_location(MODEL, imgs[:3])))
        print("  creatures:", json.dumps(describe_creatures(MODEL, imgs[:3])))
    except Exception as e:
        print("  ERROR:", e)
