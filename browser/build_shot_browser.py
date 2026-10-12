#!/usr/bin/env python3
"""Build shot-browser-data.js for the fire-and-ice shot/chunk browser.

Sources (read-only):
  shots.jsonl               -> shot id, tc, duration
  reports/chunks/chunk_*.md -> per-shot richness (size/angle/setting/motion/persons/dialogue/frames)
                                + old-chunk -> shots mapping (for six-section prompt lookup)
  reports/h3-prompts/chunk_*.txt -> six-section prompt keyed by OLD chunk number
  fullrun/chunks.jsonl      -> shot -> fullrun chunk_id; chunk metadata (scene/cast/location/names)
  fullrun/prompts/<chunk_id>.txt -> integrated prompt keyed by fullrun chunk_id
  stills/full/shot_NNNNN_f*.jpg -> 3 stills per shot (disk listing)
  fullrun/captions.jsonl    -> caption per still (partial coverage)
  script/dialogue-timeline.tsv -> dialog lines keyed by timecode

Outputs (written to E:/FNI):
  shot-browser-data.js      -> single JS assignment window.SHOTDATA = {...}
"""

import json
import os
import re
import glob

ROOT = os.path.dirname(os.path.abspath(__file__))

FMT = re.compile(r"^(\d+):(\d+):(\d+)[.,](\d+)$")

def tc_to_s(tc):
    m = FMT.match(tc.strip())
    if not m:
        return None
    h, mi, s, frac = m.groups()
    return int(h) * 3600 + int(mi) * 60 + int(s) + float("0." + frac)

def text_of(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None

# ---------------------------------------------------------------- shots
shots = []
with open(os.path.join(ROOT, "shots.jsonl"), encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        shots.append({
            "id": r["shot_id"],                    # "shot:00001"
            "num": r["shot_id"].split(":")[1],     # "00001"
            "idx": r["index"],
            "start": r["start_tc"],
            "end": r["end_tc"],
            "dur": r["duration_seconds"],
        })
shots.sort(key=lambda s: s["idx"])
num2shot = {s["num"]: s for s in shots}

# ------------------------------------------------------- old chunks (.md)
old_chunk_shots = {}      # old chunk num (int) -> [shot nums]
shot_old_chunk = {}       # shot num -> old chunk num (int)
shot_detail = {}          # shot num -> {size, angle, setting, motion, persons, dialogue}

for path in glob.glob(os.path.join(ROOT, "reports", "chunks", "chunk_*.md")):
    cnum = int(re.search(r"chunk_(\d+)\.md$", os.path.basename(path)).group(1))
    txt = text_of(path)
    if txt is None:
        continue
    m = re.search(r"Shots:\s*shot:(\d+)", txt)
    if not m:
        continue
    shot_nums = sorted(set(re.findall(r"shot:(\d+)", txt)))
    old_chunk_shots[cnum] = shot_nums
    for sn in shot_nums:
        shot_old_chunk[sn] = cnum

    # per-shot block
    for block in re.split(r"\n### ", txt)[1:]:
        sm = re.match(r"shot:(\d+)", block)
        if not sm:
            continue
        sn = sm.group(1)
        lines = block.split("\n")
        def grab(prefix):
            for ln in lines:
                if ln.startswith("- " + prefix):
                    return ln.split(":", 1)[1].strip()
            return None
        size = grab("size")
        angle = grab("angle")
        setting = grab("setting")
        motion = grab("motion")
        dialogue = []
        persons = []
        for ln in lines:
            if ln.startswith("- dialogue:"):
                i = ln.find("dialogue:")
                dialogue.append(ln[i + len("dialogue:"):].strip())
            elif ln.startswith("- person:"):
                i = ln.find("person:")
                persons.append(ln[i + len("person:"):].strip())
        shot_detail[sn] = {
            "size": size, "angle": angle, "setting": setting,
            "motion": motion, "persons": persons, "dialogue": dialogue,
        }

# ------------------------------------------------- six-section prompts
six_prompt = {}   # old chunk num (int, stripped) -> text
for path in glob.glob(os.path.join(ROOT, "reports", "h3-prompts", "chunk_*.txt")):
    cnum = int(re.search(r"chunk_(\d+)\.txt$", os.path.basename(path)).group(1))
    six_prompt[cnum] = text_of(path) or ""

# ------------------------------------------------------- fullrun chunks
chunk_meta = {}      # chunk_id -> {scene, cast, location, names, shot_nums}
shot_chunk = {}      # shot num -> chunk_id
with open(os.path.join(ROOT, "fullrun", "chunks.jsonl"), encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        chunk_meta[r["chunk_id"]] = {
            "scene": r.get("scene"),
            "cast": r.get("cast"),
            "location": r.get("location"),
            "names": r.get("stamped_names"),
            "shot_nums": r.get("shot_nums"),
            "line_ids": r.get("line_ids"),
        }
        for sn in r.get("shot_nums", []):
            shot_chunk[sn] = r["chunk_id"]

integrated_prompt = {}  # chunk_id -> text
for path in glob.glob(os.path.join(ROOT, "fullrun", "prompts", "*.txt")):
    cid = os.path.splitext(os.path.basename(path))[0]
    integrated_prompt[cid] = text_of(path) or ""

# ---------------------------------------------------------------- stills
shot_stills = {}   # shot num -> [3 filenames sorted by frame]
for path in glob.glob(os.path.join(ROOT, "stills", "full", "shot_*.jpg")):
    m = re.match(r"shot_(\d+)_f(\d+)\.jpg$", os.path.basename(path))
    if m:
        shot_stills.setdefault(m.group(1), []).append((int(m.group(2)), os.path.basename(path)))
for sn, arr in shot_stills.items():
    arr.sort()
    shot_stills[sn] = [fn for _, fn in arr]

# ------------------------------------------------------------- captions
captions = {}   # still filename -> text
with open(os.path.join(ROOT, "fullrun", "captions.jsonl"), encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        captions[r["file"]] = r["text"]

# ---------------------------------------------------------------- dialog
dialog_lines = []   # [{start_s, end_s, speaker, text, id}]
with open(os.path.join(ROOT, "script", "dialogue-timeline.tsv"), encoding="utf-8") as f:
    header = f.readline().rstrip("\n").split("\t")
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 7:
            continue
        d = dict(zip(header, parts))
        s0, s1 = tc_to_s(d["start"]), tc_to_s(d["end"])
        if s0 is None or s1 is None:
            continue
        dialog_lines.append({"start": s0, "end": s1, "speaker": d["speaker"], "text": d["text"], "id": d["id"]})

# assign dialog to shots by time overlap
def assign_dialog():
    out = {sn: [] for sn in num2shot}
    sshots = []  # (num, start_s, end_s)
    for s in shots:
        ss = tc_to_s(s["start"]); ee = tc_to_s(s["end"])
        if ss is None or ee is None:
            continue
        sshots.append((s["num"], ss, ee))
    sshots.sort(key=lambda x: x[1])
    for dl in dialog_lines:
        mid = (dl["start"] + dl["end"]) / 2.0
        for num, ss, ee in sshots:
            if ss <= mid <= ee:
                out[num].append(dl)
                break
    return out

shot_dialog = assign_dialog()

# --------------------------------------------------------------- assemble
def esc(s):
    return s

data_shots = []
for s in shots:
    sn = s["num"]
    cid = shot_chunk.get(sn)
    oc = shot_old_chunk.get(sn)
    data_shots.append({
        "num": sn,
        "id": s["id"],
        "start": s["start"],
        "end": s["end"],
        "dur": round(s["dur"], 2),
        "chunk": cid,
        "old_chunk": oc,
        "stills": shot_stills.get(sn, []),
        "detail": shot_detail.get(sn, {}),
        "dialog": shot_dialog.get(sn, []),
    })

data_chunks = []
for cid, meta in sorted(chunk_meta.items()):
    data_chunks.append({
        "id": cid,
        "scene": meta["scene"],
        "cast": meta["cast"],
        "location": meta["location"],
        "names": meta["names"],
        "shot_nums": meta["shot_nums"],
        "line_ids": meta["line_ids"],
        "prompt": integrated_prompt.get(cid, ""),
    })

# six-section prompt: resolve per shot via old chunk
for s in data_shots:
    oc = s["old_chunk"]
    if oc is not None and oc in six_prompt:
        s["six_prompt"] = six_prompt[oc]

data_chunks.sort(key=lambda c: c["id"])
data_shots.sort(key=lambda s: s["num"])

out = {
    "shots": data_shots,
    "chunks": data_chunks,
    "captions": {k if isinstance(k, str) else str(k): v for k, v in captions.items()},
    "counts": {"shots": len(data_shots), "chunks": len(data_chunks)},
}

js = "window.SHOTDATA = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n"

outpath = os.path.join(ROOT, "shot-browser-data.js")
with open(outpath, "w", encoding="utf-8") as f:
    f.write(js)

print("wrote", outpath, f"({os.path.getsize(outpath):,} bytes)")
print("shots:", len(data_shots), "chunks:", len(data_chunks))
print("shots with six-section prompt:", sum(1 for s in data_shots if "six_prompt" in s))
print("shots with integrated prompt (via chunk):", sum(1 for s in data_shots if s["chunk"]))
print("shots with captioned stills:", sum(1 for s in data_shots if any(c in captions for c in s["stills"])))