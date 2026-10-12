"""Generate runs/testruns-data.js for the shot-browser SPA's "Test runs" tab.

Scans every test-run artifact on disk (thumbdrive copies in runs/testruns/,
local run outputs under runs/T000*/output/, T0008 audio overlays, T0009
continuity artifacts) and merges them with the curated run metadata below.

Curated metadata is the human record: what each run varied, its verdict.
Files are discovered, never hard-coded, so a new render shows up by re-running
this script (and a fresh copy from the thumbdrive is just more files).

Run: .venv/Scripts/python.exe tools/build_testruns_data.py
"""
import json
import re
from pathlib import Path

ROOT = Path(r"E:/FNI")
OUT = ROOT / "runs" / "testruns-data.js"

# id -> curated record. verdict/status are the human state, updated by hand or
# by whoever watches the render (Alex; see runs/INDEX.md for the same record).
RUNS = {
    "T0001": {
        "scope": "S03", "title": "ref2v, original film stills",
        "question": "Does a straight reference-to-video render of the pilot scene play back at all?",
        "verdict": "decent — Alex, 2026-09-27", "status": "judged",
        "notes": "First scene that played back. 31/31 validator checks passed.",
    },
    "T0002": {
        "scope": "S03", "title": "ref2v, split at action beats",
        "question": "Same refs and seed as T0001, but chunks cut at action beats instead of even time — does motion improve?",
        "verdict": "pretty good, on the right track — Alex, 2026-09-28", "status": "judged",
        "notes": "Action-beat chunking adopted as the chunking rule.",
    },
    "T0003": {
        "scope": "S03", "title": "fl2va, first/last source stills",
        "question": "Same chunks and seed as T0002, but generated as first-frame/last-frame video instead of reference-to-video — does anchoring both ends beat reference mode?",
        "verdict": "awaiting Alex", "status": "pending",
        "notes": "This is the mode the full run (fullrun.py) uses.",
    },
    "T0004": {
        "scope": "S03", "title": "fl2va, motion-path variant",
        "question": "Do source-frame deltas (motion path) between the anchor stills drive better motion? Two takes.",
        "verdict": "awaiting Alex", "status": "pending",
        "notes": "2 takes rendered.",
    },
    "T0005": {
        "scope": "S03", "title": "fl2va, action variant",
        "question": "Action-oriented prompt variant on the same chunks — does it help fight/action beats?",
        "verdict": "awaiting Alex", "status": "pending", "notes": "",
    },
    "T0008": {
        "scope": "S03", "title": "original audio over T0001 video",
        "question": "Audio plan A baseline: the film's own audio laid over the rendered video at exact source timecodes — how bad is the lip-sync mismatch really?",
        "verdict": "audition pending", "status": "pending",
        "notes": "Free to build, nothing rendered. Per-chunk overlays from audio/master_audio_48k_stereo.wav.",
    },
    "T0009": {
        "scope": "S02", "title": "continuity packing (glacier chains intact) vs chronological",
        "question": "Do chunk boundaries derived from setup/chain analysis (SSIM) beat strict chronological packing? Variable: boundaries only.",
        "verdict": "renders in flight", "status": "running",
        "notes": ("Continuity: [16][17,18,19][20,21][22][23,24,25][26,27] vs chronological "
                  "[16,17,18][19,20,21][22,23,24][25,26,27]. Compare the two audioA files: "
                  "glacier chains 17->18 and 24->25 should read as continuous motion."),
    },
}


# --------------------------------------------------------------------------
# chunk -> [source shot nums] per run. Copy these from each run's manifest.md
# (the chunk/shots table). The S03 pilot is shots 00067-00074: T0001/T0008 use
# a 3-chunk split, T0002-T0005 a 5-chunk action-beat split over the same 8
# shots. T0009 packs S02 shots 00016-00027 into 6 continuity segments.
# Keys are lowercased chunk ids to match clip filenames case-insensitively.
# --------------------------------------------------------------------------
_S03_THREE = {"s03-c01": ["00067", "00068", "00069"],
              "s03-c02": ["00070", "00071", "00072"],
              "s03-c03": ["00073", "00074"]}
_S03_FIVE = {"s03-c01": ["00067"],
             "s03-c02": ["00068", "00069"],
             "s03-c03": ["00070", "00071"],
             "s03-c04": ["00072"],
             "s03-c05": ["00073", "00074"]}
_S02_SIX = {"s02-k01": ["00016"],
            "s02-k02": ["00017", "00018", "00019"],
            "s02-k03": ["00020", "00021"],
            "s02-k04": ["00022"],
            "s02-k05": ["00023", "00024", "00025"],
            "s02-k06": ["00026", "00027"]}

CHUNK_SHOTS = {
    "T0001": _S03_THREE,
    "T0002": _S03_FIVE,
    "T0003": _S03_FIVE,
    "T0004": _S03_FIVE,
    "T0005": _S03_FIVE,
    "T0008": _S03_THREE,
    "T0009": _S02_SIX,
}


def rel(p):
    return p.relative_to(ROOT).as_posix()


def scan():
    """id -> [relative file paths], discovered from disk."""
    found = {}

    def add(rid, p):
        if p.suffix.lower() != ".mp4" or not p.exists() or p.stat().st_size < 1000:
            return
        found.setdefault(rid, []).append(rel(p))

    # thumbdrive copies: s03-c01_T0002_t01_00001_.mp4 -> T0002
    for p in sorted((ROOT / "runs" / "testruns").glob("*.mp4")):
        m = re.match(r".*_(T\d{4})_t\d+", p.name)
        if m:
            add(m.group(1), p)
    # local run folders
    for d in sorted((ROOT / "runs").glob("T000*")):
        rid = d.name[:5]
        for sub in ("output", "stitched", ""):
            for p in sorted((d / sub).glob("*.mp4")):
                if p.is_file():
                    add(rid, p)
    # T0009 comparison baseline (chronological stitch) belongs to T0009
    base = ROOT / "fullrun" / "stitched" / "S02_full_t01.mp4"
    if base.exists():
        add("T0009", base)
    for k in found:
        found[k] = sorted(set(found[k]))
    return found


def main():
    files = scan()
    runs = []
    for rid, meta in RUNS.items():
        rec = {"id": rid}
        rec.update(meta)
        rec["files"] = files.get(rid, [])
        rec["chunks"] = CHUNK_SHOTS.get(rid, {})
        runs.append(rec)
    # any discovered run with no curated record still gets shown
    for rid in sorted(set(files) - set(RUNS)):
        runs.append({"id": rid, "scope": "", "title": "(unrecorded run)", "question": "",
                     "verdict": "unrecorded", "status": "pending", "notes": "",
                     "files": files[rid]})
    runs.sort(key=lambda r: r["id"])
    OUT.write_text("window.TESTDATA = " + json.dumps({"runs": runs}, indent=1) + ";\n",
                   encoding="utf-8")
    print("wrote %s: %d runs, %d files" % (OUT, len(runs), sum(len(r["files"]) for r in runs)))
    for r in runs:
        print("  %s %-8s %2d files  %s" % (r["id"], r["scope"], len(r["files"]), r["title"][:44]))


if __name__ == "__main__":
    main()
