"""Build the scene-10 ledger for the 35-55 minute window.

Does not write chunks. Does not call ComfyUI.
"""
import json
from pathlib import Path

from core.cluster import cluster_people
from core.ledger import is_unreliable, normalize_location, normalize_person
from core.vlm_correlate import describe_creatures, describe_location, describe_people

ROOT = Path(r"E:/FNI")
MODEL = "qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s"
LEDGER = ROOT / "manifests" / "scene10_ledger.jsonl"
CLUSTERS = ROOT / "manifests" / "scene10_clusters.json"


def window_shots(shots):
    picked = []
    for shot in shots:
        mid = (shot["start_pts"] + shot["end_pts"]) / 2 / 24000 / 60
        if 35 <= mid <= 55:
            picked.append(shot)
    return picked


def stills_for(shot_id):
    stem = shot_id.replace(":", "_")
    return sorted((ROOT / "stills" / "full").glob(f"{stem}_f*.jpg"))[:3]


def label_shot(shot, model=MODEL):
    paths = stills_for(shot["shot_id"])
    people = describe_people(model, paths)
    location = describe_location(model, paths)
    creatures = describe_creatures(model, paths)
    people_list = people.get("people") or []
    loc_text = location.get("location") if isinstance(location, dict) else ""
    row = {
        "shot_id": shot["shot_id"],
        "start_pts": shot["start_pts"],
        "end_pts": shot["end_pts"],
        "location_raw": loc_text or "",
        "location_token": normalize_location(loc_text or ""),
        "people_raw": people_list,
        "people_tokens": [sorted(normalize_person(p)) for p in people_list],
        "creatures_raw": creatures.get("creatures") or [],
        "people_unreliable": is_unreliable(
            people.get("count_men") or 0,
            people.get("count_women") or 0,
            people_list,
        ),
        "error": "",
    }
    return row


def main():
    shots = [json.loads(line) for line in (ROOT / "shots.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    picked = window_shots(shots)
    print(f"window shots: {len(picked)}", flush=True)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text("", encoding="utf-8")
    rows = []
    with LEDGER.open("a", encoding="utf-8") as out:
        for i, shot in enumerate(picked, 1):
            paths = stills_for(shot["shot_id"])
            if not paths:
                row = {
                    "shot_id": shot["shot_id"],
                    "start_pts": shot["start_pts"],
                    "end_pts": shot["end_pts"],
                    "location_token": "",
                    "people_tokens": [],
                    "people_unreliable": False,
                    "error": "no_stills",
                }
            else:
                try:
                    row = label_shot(shot)
                except Exception as exc:
                    row = {
                        "shot_id": shot["shot_id"],
                        "start_pts": shot["start_pts"],
                        "end_pts": shot["end_pts"],
                        "location_token": "",
                        "people_tokens": [],
                        "people_unreliable": True,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
            out.write(json.dumps(row) + "\n")
            out.flush()
            rows.append(row)
            print(f"{i}/{len(picked)} {shot['shot_id']} {row.get('location_token','')} err={row.get('error','')}", flush=True)
    clusters = cluster_people(rows)
    CLUSTERS.write_text(json.dumps(clusters, indent=2), encoding="utf-8")
    print(f"clusters: {len(clusters)}", flush=True)


if __name__ == "__main__":
    main()
