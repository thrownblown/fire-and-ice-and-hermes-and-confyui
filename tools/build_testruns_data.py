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
    "T0010": {
        "scope": "S02", "title": "motion-context chaining / bridging",
        "question": "Can a clip be extended by feeding the previous clip's tail back as motion context (chaining/bridging) instead of fresh latents?",
        "verdict": "awaiting Alex", "status": "pending",
        "notes": "Skill reference: fni-h3-pipeline references/chaining.md.",
    },
    "T0011": {
        "scope": "S06", "title": "setup-ref2va baseline (chronological chunk S06-c01)",
        "question": "Control for the setup experiments: the ordinary chronological chunk (shots 197,198,199) as one reference.",
        "verdict": "awaiting Alex", "status": "pending", "notes": "",
    },
    "T0012": {
        "scope": "S06", "title": "setup-ref2va stitched-video (setup S06-A as one ref)",
        "question": "Re-group by camera angle: concat one setup's shots (A/A/A) into a single reference video instead of a chronological A/B/A mix — does angle consistency improve the render?",
        "verdict": "awaiting Alex", "status": "pending",
        "notes": "Approach X2. See docs/plans/setup-ref2va-tests.md.",
    },
    "T0013": {
        "scope": "S06", "title": "setup plate + ONE shot's video",
        "question": "Can a still 'master plate' of the setup stand in for part of the video reference — plate image + a single shot's clip, to cut the reference-encode cost?",
        "verdict": "awaiting Alex", "status": "pending",
        "notes": "Approach X3. Setup plate injected as an extra <Picture> with a background_only retention line.",
    },
    "T0014": {
        "scope": "S06", "title": "per-shot + shared plate",
        "question": "Shared setup plate WITHOUT re-grouping: a single shot's video plus the setup's plate image — is the shared plate alone enough?",
        "verdict": "awaiting Alex", "status": "pending", "notes": "Approach X4.",
    },
    "T0015": {
        "scope": "S05", "title": "Track A ref2va — technicolor sheets + plate, WITH video ref",
        "question": "With the technicolor character sheets + location plate wired as <Picture> refs, does REF2VA hold the live-action 80s register while the raw 1983 video ref conditions the motion?",
        "verdict": "NEGATIVE — reads flat 2D rotoscope cel, not live-action (every sampled frame)",
        "status": "judged",
        "notes": ("The video reference dominates appearance, so styling only the PICTURE refs is not enough — the same "
                  "failure as the FL2VA TEST-1 pinning result, one stage up. Resolved by T0016 (drop the video ref). "
                  "Driver: runs/build_technicolor_ref2va.py."),
    },
    "T0016": {
        "scope": "S05", "title": "ref2va AUDIO-ONLY (no video ref) + authored blocking + clean plate",
        "question": "Drop the video reference, keep only the source AUDIO (ref_audios + audio_vae): do the technicolor sheets + plate then hold the live-action register, and does an explicit per-chunk blocking line stop H3 inventing a walk-in and a background crowd?",
        "verdict": ("register HOLDS — live-action 80s technicolor; exactly two characters, no background extras, "
                    "lounging/seated as authored. Residual: a brief mid-clip stand."),
        "status": "judged",
        "notes": ("Take ladder on one scene: t01 = walking to camera + crowd; t03 = two people seated (blocking added, "
                  "but the plate still had painted figures); t04 = clean plate -> exactly two people, no crowd. "
                  "Per-chunk takes in output/t02, output/t03; the 4x6 seed sweep in output/seedhunt/. "
                  "Driver: runs/build_technicolor_audio_only.py. Stitched: S05_audioOnly_T0016_t04_stitched.mp4."),
    },
    "T0017": {
        "scope": "S03", "title": "audio-only REF2VA — Ice Peak throne hall (Juliana / Nekron)",
        "question": "Does the audio-only recipe carry to a second scene — different location plate, different cast — and land an authored sitting/standing blocking?",
        "verdict": "register holds; two characters; Nekron seated on the ice throne per the authored blocking",
        "status": "judged",
        "notes": ("One blurred background figure in frame 1 (that chunk also carries a TEEGRA mis-stamp in the ledger). "
                  "Driver: runs/build_technicolor_audio_only.py --chunk S03-c01 --subjects JULIANA,NEKRON."),
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

_S05_FOUR = {"s05-c01": ["00188", "00189"],
             "s05-c02": ["00190", "00191"],
             "s05-c03": ["00192", "00193", "00194"],
             "s05-c04": ["00195", "00196"]}
# S03 "Ice Peak: Juliana & Nekron send envoys" — the renderable interior chunks.
_S03_TECH = {"s03-c01": ["00067", "00068", "00069"],
             "s03-c02": ["00070", "00071", "00072"]}
# S06 setup experiments (S06-A = shots 197,199,201,203,205).
_S06_SETUP = {"s06-c01": ["00197", "00198", "00199"],
              "setup-s06-a": ["00197", "00199", "00201", "00203", "00205"],
              "t0013-s06-a-s197": ["00197"],
              "t0014-s06-a-s197": ["00197"]}

CHUNK_SHOTS = {
    "T0001": _S03_THREE,
    "T0002": _S03_FIVE,
    "T0003": _S03_FIVE,
    "T0004": _S03_FIVE,
    "T0005": _S03_FIVE,
    "T0008": _S03_THREE,
    "T0009": _S02_SIX,
    "T0011": _S06_SETUP,
    "T0012": _S06_SETUP,
    "T0013": _S06_SETUP,
    "T0014": _S06_SETUP,
    "T0015": _S05_FOUR,
    "T0016": _S05_FOUR,
    "T0017": _S03_TECH,
}


def rel(p):
    return p.relative_to(ROOT).as_posix()


# --------------------------------------------------------------------------
# Prompts beside the clips. Alex's standing ask: the review page must show the
# VERBATIM prompt next to the video, or judging a take is guesswork. The Tests
# tab used to carry no prompt at all (he asked for T0017 and got clips only).
#
# Source order, most authoritative first:
#   1. the take's own GRAPH (an artifact: what was actually queued)
#   2. the driver's prompts/<chunk>.txt
#   3. fullrun/prompts/<chunk>.txt
# The chosen source is recorded per clip as `prompt_source`, so the page never
# implies a provenance it does not have.
# --------------------------------------------------------------------------
GRAPH_DIRS = [ROOT / "runs" / "T0016_s05_technicolor-audio-only-ref2va" / "graphs",
              ROOT / "fullrun" / "graphs"]
PROMPT_DIRS = [ROOT / "runs" / "T0016_s05_technicolor-audio-only-ref2va" / "prompts",
               ROOT / "fullrun" / "prompts"]


def _prompt_from_graph(path: Path) -> str:
    """Pull the queued prompt out of a ComfyUI API-format graph."""
    try:
        g = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return ""
    best = ""
    for node in g.values():
        if not isinstance(node, dict):
            continue
        ct = str(node.get("class_type", ""))
        ins = node.get("inputs") or {}
        cand = ""
        if "ReferenceToVideo" in ct or "MiniMaxH3" in ct:
            cand = str(ins.get("prompt") or "")
        elif ct == "PrimitiveStringMultiline":
            cand = str(ins.get("value") or "")
        if len(cand) > len(best):
            best = cand
    return best.strip()


def clip_meta(f: str) -> dict:
    """Prompt + provenance for one clip path (`runs/<run>/.../<chunk>_<mode>_t<NN>_*.mp4`)."""
    p = ROOT / f
    name = p.name
    # the S03 arm collector names files `take<N>__<chunk>_<mode>_t<NN>_...` so they sort together;
    # strip that prefix before parsing
    name = re.sub(r"^take\d+__", "", name)
    m = re.match(r"(?P<chunk>[A-Za-z]\d{2}-[ck]\d{2})_(?P<mode>[A-Za-z]+)_t(?P<take>\d{2})", name)
    if not m:
        return {}
    chunk, mode, take = m.group("chunk"), m.group("mode"), m.group("take")
    tag = f"{chunk}_{mode}_t{take}"
    # both graph naming forms exist in this repo: `<chunk>_<mode>_t<NN>.json` (the audio-only
    # driver) and bare `<chunk>.json` (earlier pilot graphs)
    cands = [d / f"{tag}.json" for d in GRAPH_DIRS] + [d / f"{chunk}.json" for d in GRAPH_DIRS] \
        + [p.parent / f"{tag}.json", p.parent / f"{chunk}.json"]
    for g in cands:
        if g.exists():
            text = _prompt_from_graph(g)
            if text:
                return {"prompt": text, "prompt_source": rel(g), "take": take, "chunk": chunk}
    for d in PROMPT_DIRS:
        q = d / f"{chunk}.txt"
        if q.exists():
            text = q.read_text(encoding="utf-8").strip()
            if text:
                return {"prompt": text, "prompt_source": rel(q), "take": take, "chunk": chunk,
                        "warning": "prompt file is per-chunk, not per-take — this may not be the "
                                   "exact text this take was rendered with"}
    return {"take": take, "chunk": chunk, "warning": "no graph or prompt file found for this take"}


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
    # local run folders — recurse so nested take dirs (output/t03, output/seedhunt)
    # are picked up too. Glob T####_ not T000*: the old glob silently missed T0010+.
    for d in sorted((ROOT / "runs").glob("T[0-9][0-9][0-9][0-9]_*")):
        rid = d.name[:5]
        for p in sorted(d.rglob("*.mp4")):
            if p.is_file():
                add(rid, p)
    # T0009 comparison baseline (chronological stitch) belongs to T0009
    base = ROOT / "fullrun" / "stitched" / "S02_full_t01.mp4"
    if base.exists():
        add("T0009", base)
    def order(path):
        b = path.rsplit("/", 1)[-1].lower()
        # stitched deliverables first, then per-chunk takes, then seed sweeps
        if "seedhunt" in path:
            return (2, path)
        if "stitched" in b:
            return (0, path)
        return (1, path)

    for k in found:
        found[k] = sorted(set(found[k]), key=order)
    return found


def main():
    files = scan()
    runs = []
    for rid, meta in RUNS.items():
        rec: dict = {"id": rid}
        rec.update(meta)
        rec["files"] = files.get(rid, [])
        rec["chunks"] = CHUNK_SHOTS.get(rid, {})
        # per-clip prompt + provenance, keyed by the same path the page links
        rec["clipmeta"] = {f: clip_meta(f) for f in rec["files"]}
        runs.append(rec)
    # any discovered run with no curated record still gets shown
    for rid in sorted(set(files) - set(RUNS)):
        runs.append({"id": rid, "scope": "", "title": "(unrecorded run)", "question": "",
                     "verdict": "unrecorded", "status": "pending", "notes": "",
                     "files": files[rid],
                     "clipmeta": {f: clip_meta(f) for f in files[rid]}})
    runs.sort(key=lambda r: r["id"])
    OUT.write_text("window.TESTDATA = " + json.dumps({"runs": runs}, indent=1) + ";\n",
                   encoding="utf-8")
    n_prompt = sum(1 for r in runs for m in r.get("clipmeta", {}).values() if m.get("prompt"))
    n_files = sum(len(r["files"]) for r in runs)
    print("wrote %s: %d runs, %d files (%d with a prompt resolved)" % (OUT, len(runs), n_files, n_prompt))
    for r in runs:
        withp = sum(1 for m in r.get("clipmeta", {}).values() if m.get("prompt"))
        print("  %s %-8s %2d files  %2d prompts  %s" % (r["id"], r["scope"], len(r["files"]), withp,
                                                        r["title"][:40]))


if __name__ == "__main__":
    main()
