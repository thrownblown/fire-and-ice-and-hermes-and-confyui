"""Stamp lead names onto the character pass. Does not call the VLM.

The VLM pass was not supposed to name anyone. Asked for names, it
invented characters and collapsed different people into one. Stage 2
records only what is visible: count, sex, hair, clothing, action.
Names here are a later guess from those descriptions, applied by these
rules, not by the model. A miss stays unnamed.

Rules are what the pass actually wrote, not the design-doc wording.
Juliana is not stamped. The pass calls Nekron female often enough that a
"woman, white hair, robe" rule labeled him Juliana on the throne stills.
Leave her unnamed until a rule can tell them apart without sex.

Writes manifests/character_names.jsonl and refreshes the name line
in reports/character-pass.html. Does not edit character_pass.jsonl.
"""
import json
from pathlib import Path

ROOT = Path(r"E:/FNI")
SRC = ROOT / "manifests" / "character_pass.jsonl"
OUT = ROOT / "manifests" / "character_names.jsonl"
HTML = ROOT / "reports" / "character-pass.html"


def name_for(person):
    sex = (person.get("sex") or "").lower()
    hair = (person.get("hair") or "").lower()
    cloth = (person.get("clothing") or "").lower()
    skin = (person.get("skin") or "").lower()
    long_hair = "long" in hair
    dark_hair = "black" in hair or "dark" in hair
    white_hair = "white" in hair or "silver" in hair
    blond = "blond" in hair or "blonde" in hair
    pale = any(w in skin for w in ("pale", "white", "gray", "grey"))
    purple = any(w in cloth for w in ("purple", "lavender", "violet"))
    robe = any(w in cloth for w in ("robe", "gown", "coat"))
    larn_prop = "gold buckle" in cloth or "bone" in cloth
    if sex == "female" and long_hair and dark_hair and purple and not robe:
        return "Teegra"
    if sex == "female" and pale and white_hair and robe:
        return ""
    if pale and long_hair and white_hair and robe:
        return "Nekron"
    if sex == "male" and blond and larn_prop:
        return "Larn"
    return ""


def stills(shot_id):
    stem = shot_id.replace(":", "_")
    return sorted((ROOT / "stills" / "full").glob(f"{stem}_f*.jpg"))[:3]


def main():
    shots = [
        json.loads(line)["shot_id"]
        for line in (ROOT / "shots.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows = [
        json.loads(line)
        for line in SRC.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    counts = {}
    named_rows = []
    for row in rows:
        people = []
        for person in row.get("people") or []:
            stamped = dict(person)
            stamped["name"] = name_for(person)
            if stamped["name"]:
                counts[stamped["name"]] = counts.get(stamped["name"], 0) + 1
            people.append(stamped)
        named_rows.append({
            "shot_id": row["shot_id"],
            "count_men": row.get("count_men") or 0,
            "count_women": row.get("count_women") or 0,
            "people": people,
            "error": row.get("error") or "",
        })
    OUT.write_text(
        "\n".join(json.dumps(r) for r in named_rows) + "\n",
        encoding="utf-8",
    )
    by_id = {r["shot_id"]: r for r in named_rows}
    blocks = []
    for sid in shots:
        row = by_id.get(sid)
        if not row:
            continue
        frames = stills(sid)
        imgs = "".join(
            f'<img src="../{f.relative_to(ROOT).as_posix()}" alt="">' for f in frames
        )
        people = row["people"]
        if row["error"]:
            body = f"<p class='err'>{row['error']}</p>"
        elif not people:
            body = "<p>no people</p>"
        else:
            items = []
            for person in people:
                label = person["name"] or "unnamed"
                cls = "named" if person["name"] else "unnamed"
                items.append(
                    f"<li><strong class='{cls}'>{label}</strong> — "
                    f"{person.get('sex','')} · {person.get('hair','')} · "
                    f"{person.get('clothing','')} · {person.get('action','')}</li>"
                )
            body = f"<ul>{''.join(items)}</ul>"
        blocks.append(
            f"<article><h2>{sid}</h2><div class='strip'>{imgs}</div>{body}</article>"
        )
    page = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Character pass — names</title>
<style>
body {{ font-family: sans-serif; background: #111; color: #eee; margin: 0; }}
header {{ position: sticky; top: 0; background: #111; padding: 12px 16px; border-bottom: 1px solid #333; }}
article {{ padding: 12px 16px; border-bottom: 1px solid #222; }}
img {{ width: 220px; margin-right: 8px; }}
.named {{ color: #e6b84d; }}
.unnamed {{ color: #888; }}
.err {{ color: #f66; }}
</style></head><body>
<header>Names stamped from descriptions, not from the VLM. The character pass was told not to name anyone — free-form names came back invented. These labels are a rule match on hair and clothing: {', '.join(f'{k} {v}' for k,v in sorted(counts.items()))}. Unmatched stays unnamed. Not reviewed.</header>
{''.join(blocks)}
</body></html>
"""
    HTML.write_text(page, encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"wrote {HTML}")
    print("counts", counts)


if __name__ == "__main__":
    main()
