"""Generate project-data.js for the shot-browser SPA: "Status" + "Decisions" tabs.

Two kinds of content live here:
  * counts  — recomputed from disk every run (shots, renders, QC, stitches), so
              the Status page is never stale.
  * curated — the human narrative: what each pipeline stage means, and the open
              decisions awaiting Alex. Edited HERE, by hand, then re-built.

Run: .venv/Scripts/python.exe tools/build_project_data.py

The Status tab mirrors runs/INDEX.md + memory/VIEW.md; the Decisions tab is the
single place to trip over "what still needs a human". When a decision is made,
set its state to "decided" (optionally "resolved": note) and re-run — do NOT
delete it, so the page keeps the trail of what was ruled and when.
"""
import json
import re
from pathlib import Path

ROOT = Path(r"E:/FNI")
OUT = ROOT / "browser" / "project-data.js"

# The six plates no settled scene claims — they read as made for the G action stretches.
FREE_PLATES = ["frozen-landscape", "north-village-plain", "open-sky", "swamp", "wilderness", "ice-peak-cave"]


def plate_catalogue():
    """Every plate image on disk: slug, how many takes, newest filename, and a display URL.

    Count IMAGES only — `*_plate_*.graph.json` sidecars match the same substring and inflated the
    count to 108 when there are 73 plates. `img` prefers the small JPEG from
    tools/make_plate_thumbs.py: the raw plates are 3-5 MB PNGs and Chrome would not paint one in the
    chooser at all (the URL was fine — a fetch of it returned 200 and 3.17 MB).
    """
    bgs = ROOT / "refs" / "backgrounds"
    thumbs = bgs / "_thumbs"
    out = []
    if not bgs.exists():
        return out
    for d in sorted(p for p in bgs.iterdir() if p.is_dir() and p.name != "_thumbs"):
        fs = sorted((p for p in d.iterdir()
                     if "_plate_" in p.name and p.suffix.lower() in (".png", ".jpg", ".jpeg")),
                    key=lambda p: p.stat().st_mtime)
        if not fs:
            continue
        newest = fs[-1]
        t = thumbs / ("%s__%s.jpg" % (d.name, newest.stem))
        out.append({"slug": d.name, "files": len(fs), "newest": newest.name,
                    "img": "refs/backgrounds/_thumbs/" + t.name if t.exists()
                           else "refs/backgrounds/%s/%s" % (d.name, newest.name),
                    "thumb": t.exists()})
    return out


def scene_evidence():
    """Per scene: a few SOURCE stills and the distinct 'setting' strings from its shots.

    So a plate can be chosen against what the scene actually looks like, not from its name. Stills
    come from the shot data the SPA already ships (browser/shot-browser-data.js: each shot lists its
    stills + detail.setting); the scene is the chunk prefix ("G03-c07" -> G03). Stills are sampled
    across the scene's shots rather than taken from the first few, so a long scene is represented.
    """
    sd = _js_obj(ROOT / "browser" / "shot-browser-data.js")
    shots = sd.get("shots") if isinstance(sd, dict) else sd
    by: dict[str, dict] = {}
    for s in shots or []:
        sc = str(s.get("chunk") or "").split("-")[0]
        if not sc:
            continue
        e = by.setdefault(sc, {"all": [], "settings": [], "shots": 0})
        e["shots"] += 1
        st = (s.get("detail") or {}).get("setting")
        if st and st not in e["settings"]:
            e["settings"].append(st)
        for fn in (s.get("stills") or [])[:1]:
            e["all"].append(fn)
    out = {}
    thumbs = ROOT / "stills" / "_thumbs"
    for sc, e in by.items():
        n = len(e["all"])
        idx = sorted({0, n // 4, n // 2, (3 * n) // 4, n - 1}) if n else []
        picks = [e["all"][i] for i in idx if 0 <= i < n][:5]
        # stills/full averages ~215 KB (827 MB across 3926), so prefer a small JPEG from
        # tools/make_still_thumbs.py when one exists — same lesson as the plates.
        out[sc] = {"stills": [{"fn": fn,
                               "img": "stills/_thumbs/%s.jpg" % Path(fn).stem
                                      if (thumbs / (Path(fn).stem + ".jpg")).exists()
                                      else "stills/full/%s" % fn} for fn in picks],
                   "settings": e["settings"][:6], "shots": e["shots"]}
    return out


def plate_choices():
    """Per-scene plate choice rows: the 12 scenes with no settled plate (+ their chunk counts).

    `suggested` is ordered best-first and is only a suggestion — the UI offers EVERY slug in the
    catalogue, because a scene can legitimately borrow another location's plate.
    """
    p = ROOT / "manifests" / "scene_locations.json"
    if not p.exists():
        return []
    scenes = json.loads(p.read_text(encoding="utf-8")).get("scenes") or {}
    # what the SPA last wrote to disk — so the page can tell "picked" from "saved" from "applied"
    pend = {}
    pp = ROOT / "manifests" / "plate_picks.json"
    if pp.exists():
        try:
            pend = json.loads(pp.read_text(encoding="utf-8")).get("plate_picks") or {}
        except Exception:
            pend = {}
    ev = scene_evidence()
    rows = []
    for sc, rec in sorted(scenes.items()):
        if rec.get("status") not in ("UNMATCHED", "PROPOSED"):
            continue
        src = (rec.get("from") or "").lower()
        if sc.startswith("G"):
            sug = FREE_PLATES[:]
        elif "fire" in src:
            sug = ["fire-keep-throne-hall", "fire-keep-chamber", "fire-keep-pool",
                   "fire-keep-ramparts", "fire-keep-study"]
        elif "ice" in src:
            sug = ["ice-peak-cave", "ice-peak-throne-hall", "ice-peak-dungeon", "ice-peak-lava"]
        else:
            sug = []
        rows.append({"scene": sc, "chunks": rec.get("chunks", 0),
                     "ledger": rec.get("from") or "", "suggested": sug,
                     "applied": rec.get("status") or "", "applied_slug": rec.get("slug") or "",
                     "stills": (ev.get(sc) or {}).get("stills", []),
                     "settings": (ev.get(sc) or {}).get("settings", []),
                     "shots": (ev.get(sc) or {}).get("shots", 0),
                     "pending": pend.get(sc) or ""})
    return rows


def settled_scenes():
    """Scenes whose plate is already on disk — shown as the record of what was picked."""
    p = ROOT / "manifests" / "scene_locations.json"
    if not p.exists():
        return []
    scenes = json.loads(p.read_text(encoding="utf-8")).get("scenes") or {}
    out = []
    for sc, rec in sorted(scenes.items()):
        if rec.get("status") not in ("ruled", "from beat sheet", "inferred"):
            continue
        out.append({"scene": sc, "slug": rec.get("slug") or "", "chunks": rec.get("chunks", 0),
                    "status": rec.get("status") or "", "by": rec.get("from") or ""})
    return out


def _js_obj(p):
    txt = p.read_text(encoding="utf-8")
    txt = re.sub(r"^window\.\w+\s*=\s*", "", txt.strip())
    txt = re.sub(r";\s*$", "", txt)
    return json.loads(txt)


# --------------------------------------------------------------------------
# Curated narrative. States: done | active | pending | blocked.
# --------------------------------------------------------------------------
STATUS = [
    {
        "id": "extract",
        "name": "Extraction & chop",
        "state": "done",
        "note": "Whole film cut into frame-exact per-shot clips, stills, and audio stems.",
        "detail": "1308 shots. 3924 stills (3/shot). Per-shot audio stems + one 81-min "
                  "48k stereo master bed. Master source never touched.",
    },
    {
        "id": "chunk",
        "name": "Chunking",
        "state": "active",
        "note": "Shots packed into 15s-capped chunks. 10 shots are OVER the cap and need real splits.",
        "detail": "Hard 15s cap -> 494 chunks. OVER shots (need splitting before a re-render): "
                  "S01 shot:00004 is a 73s montage, plus others in S11/S14/S16.",
    },
    {
        "id": "render",
        "name": "Render (fullrun)",
        "state": "done",
        "note": "Every chunk rendered and downloaded from the 5090.",
        "detail": "603MB of output. 34 stitched scenes: 25 film scenes + 9 gap scenes G01-G09. "
                  "Scene 10 is the one hole — see its own status item.",
    },
    {
        "id": "qc",
        "name": "QC",
        "state": "done",
        "note": "Black/frozen/silent checks on all rendered chunks.",
        "detail": "Verdicts: PASS = no black >=30%, no frozen >=40%, no near-silent dialogue. "
                  "Failures get a fresh-seed retake (t02).",
    },
    {
        "id": "s10",
        "name": "Scene 10 (S10)",
        "state": "blocked",
        "note": "No renders — gap in the pipeline.",
        "detail": "Separate approach: run_scene10_ledger.py + manifests/scene10_ledger.jsonl. "
                  "Awaits an approach decision (see Decisions).",
    },
    {
        "id": "continuity",
        "name": "Continuity (SSIM)",
        "state": "done",
        "note": "Setup/chain clustering across shots so cross-cut scenes prompt coherently.",
        "detail": "core/continuity.py. Thresholds calibrated on S02/S03 (setup 0.42, chain 0.45). "
                  "Cross-cut scenes: S06, S11 (81 shots / 41 setups), S17, G03, G04, G08.",
    },
    {
        "id": "tests",
        "name": "Test runs",
        "state": "active",
        "note": "A/B experiments on the S03 pilot (and S02 continuity).",
        "detail": "T0001-T0009. Two judged, several still awaiting a look — see Decisions.",
    },
    {
        "id": "stylelora",
        "name": "Style-LoRA",
        "state": "active",
        "note": "Train a style LoRA so the film reads Frazetta-painting rather than comic.",
        "detail": "Plan A = 1983 comic/cel (3924 free stills). Plan B = Frazetti oil (gated on approved "
                  "styled sheets). Decision: do BOTH; three-way eval (no-LoRA vs comic vs painting) "
                  "on the same chunk+seed. Toolkit: Musubi-Tuner minimax-h3 fork, Ostris v3, rank 8, ~500 steps.",
    },
    {
        "id": "audio",
        "name": "Audio mix plan",
        "state": "pending",
        "note": "How voices get into the final picture.",
        "detail": "Plan A = original master audio over rendered video. Plan B = H3-cloned voices via "
                  "~4s vocal refs (RefMods). Plan C = mix of stems. Decision pending.",
    },
    {
        "id": "assembly",
        "name": "Final assembly",
        "state": "pending",
        "note": "Order + audio mix that turns stitched scenes into the film.",
        "detail": "Waiting on the audio plan and continuity decisions. A/B/C mix + non-chronological "
                  "reassembly for cross-cut scenes.",
    },
]

# --------------------------------------------------------------------------
# Open decisions. state: open | decided. Keep decided ones (trail), add what
# was ruled + when under "resolved".
# --------------------------------------------------------------------------
DECISIONS = [
    {
        "id": "plate-locations",
        "name": "Plate locations for 12 scenes",
        "category": "Plates",
        "state": "open",
        "owner": "Alex",
        "question": "Pick a plate for each of the 12 scenes that have none — the nine G action stretches "
                    "plus S15/S22/S24. One word each is enough.",
        "context": "21 location plates (73 files) existed but only 3 scenes were mapped, so 479 of 494 "
                   "chunks rendered with NO plate. 22 scenes / 213 chunks now resolve from the beat sheet's "
                   "'Canonical location' column; these 12 (281 chunks) have no location in the ledger, the "
                   "beat sheet, or the setup manifest. Six plates are unclaimed and look purpose-made for "
                   "the action stretches. Nothing attaches a guessed plate — undetermined scenes attach "
                   "nothing and are skipped by the next pass.",
        "docs": ["docs/plate-location-ruling.md", "manifests/scene_locations.json"],
    },
    # "voice-picks" (Voice-clip picks) moved to the character page: each
    # character's detail now lists their clean voice lines from
    # audio/voice-review.md with playable <audio> and keep-checkboxes
    # (localStorage fni.voicepicks.v1; builder tools/build_voice_data.py).
    {
        "id": "sheet-verdicts",
        "name": "Character sheet verdicts",
        "category": "Looks",
        "state": "open",
        "owner": "Alex",
        "question": "Pick the winning sheet among the seeded variants for Juliana / Nekron / Darkwolf.",
        "context": "23 sheets in library/char/sheet-runs/output/ (Juliana 7, Nekron 7, Darkwolf 9). "
                   "Darkwolf 'more Frazetta less Bakshi' test has 6 wording variants.",
        "docs": ["library/char/sheet-runs/seeds.tsv"],
    },
    {
        "id": "teegra-traits",
        "name": "Teegra traits",
        "category": "Looks",
        "state": "open",
        "owner": "Alex",
        "question": "Lock Teegra's earring / pendant / skin / body so sheets (and renders) are consistent.",
        "context": "VLM-reported colors outrank handwritten notes — fix silently, don't flag.",
        "docs": ["docs/character_descriptions.md"],
    },
    {
        "id": "s10-approach",
        "name": "Scene 10 approach",
        "category": "Pipeline",
        "state": "open",
        "owner": "Alex",
        "question": "Decide how to generate S10, the only scene with no renders.",
        "context": "run_scene10_ledger.py + manifests/scene10_ledger.jsonl is the scaffolding; the "
                   "generation path itself is undecided.",
        "docs": ["docs/plans/2026-09-21-scene10-ledger.md"],
    },
    {
        "id": "t0003-t0005",
        "name": "T0003-T0005 verdicts",
        "category": "Test runs",
        "state": "open",
        "owner": "Alex",
        "question": "Watch the FL2VA variants (T0003 first/last stills, T0004 motion-path, T0005 action) "
                    "and pick a rendering mode.",
        "context": "These three decide whether the full run's FL2VA mode is right. Watch in "
                   "index.html?view=tests.",
        "docs": ["docs/test-runs-plan.md"],
    },
    {
        "id": "t0008-audio",
        "name": "T0008 audio (plan A baseline)",
        "category": "Audio",
        "state": "open",
        "owner": "Alex",
        "question": "Audition original audio over T0001 video — how bad is the lip-sync mismatch really?",
        "context": "Free to build, nothing rendered. Per-chunk overlays from audio/master_audio_48k_stereo.wav.",
        "docs": ["docs/audio-plan.md"],
    },
    {
        "id": "t0009-continuity",
        "name": "T0009 continuity verdict",
        "category": "Test runs",
        "state": "open",
        "owner": "Alex",
        "question": "Continuity-packed (SSIM chains/setups) vs chronological packing — which reads better?",
        "context": "6/6 segments rendered + stitched, both audio overlays built (S02_continuity_audioA "
                   "vs S02_chronological_audioA). Compare glacier chains 17->18 and 24->25.",
    },
    {
        "id": "over-splits",
        "name": "OVER-shot splits",
        "category": "Pipeline",
        "state": "open",
        "owner": "Alex",
        "question": "Split the 10 shots flagged OVER the 15s cap into renderable pieces.",
        "context": "S01 shot:00004 (73s montage) is the worst, plus others in S11/S14/S16.",
    },
]


def rel(p):
    return p.relative_to(ROOT).as_posix()


def compute_counts():
    c = {}
    sd = _js_obj(ROOT / "browser" / "shot-browser-data.js")
    c["shots"] = len(sd["shots"])
    c["chunks"] = len(sd["chunks"])
    c["captions"] = len(sd.get("captions", {}))

    su = _js_obj(ROOT / "browser" / "setups-data.js")
    c["scenes"] = len(su.get("scenes", []))
    c["shot_setup"] = len(su.get("shot_setup", {}))

    # renders: distinct "done" chunks in the ledger
    renders = 0
    ledger = ROOT / "fullrun" / "renders.jsonl"
    if ledger.exists():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            try:
                if json.loads(line).get("state") == "done":
                    renders += 1
            except json.JSONDecodeError:
                pass
    c["renders"] = renders

    qc_pass = qc_fail = qc_warn = 0
    qc = ROOT / "fullrun" / "qc-results.jsonl"
    if qc.exists():
        for line in qc.read_text(encoding="utf-8").splitlines():
            try:
                v = json.loads(line).get("verdict", "")
            except json.JSONDecodeError:
                continue
            if v == "PASS":
                qc_pass += 1
            elif v == "FAIL":
                qc_fail += 1
            elif v == "WARN":
                qc_warn += 1
    c["qc_pass"], c["qc_fail"], c["qc_warn"] = qc_pass, qc_fail, qc_warn

    stitched = sorted((ROOT / "fullrun" / "stitched").glob("*.mp4"))
    c["stitched"] = len(stitched)
    c["film_scenes"] = sum(1 for p in stitched if re.match(r"S\d\d", p.stem.split("_")[0]))
    c["gap_scenes"] = sum(1 for p in stitched if re.match(r"G\d\d", p.stem.split("_")[0]))

    td = _js_obj(ROOT / "runs" / "testruns-data.js")
    runs = td.get("runs", [])
    c["test_runs"] = len(runs)
    c["test_pending"] = sum(1 for r in runs if r.get("status") != "judged")

    return c


def resolve_docs():
    """Embed each decision's referenced files as {path, text} so the SPA can
    render them inline (works over file:// — nothing is fetched at runtime).
    A missing path is dropped with a warning, not a crash."""
    for d in DECISIONS:
        resolved = []
        for p in d.get("docs", []):
            fp = ROOT / p
            if fp.is_file():
                resolved.append({"path": p, "text": fp.read_text(encoding="utf-8", errors="replace")})
            else:
                print("WARN: doc not found: %s" % p)
        if resolved:
            d["docs"] = resolved
        else:
            d.pop("docs", None)


def main():
    counts = compute_counts()
    resolve_docs()
    # the plate decision is the one decision that needs a PER-SCENE pick, so it carries its own data:
    # the full catalogue (every plate on disk) plus a row per undetermined scene.
    for d in DECISIONS:
        if d["id"] == "plate-locations":
            rows = plate_choices()
            d["choices"] = {"kind": "plate-per-scene", "scenes": rows,
                            "settled": settled_scenes()}
            # the decision closes itself once every scene has a plate on disk
            if not rows:
                d["state"] = "closed"
                d["name"] = "Plate locations — all scenes settled"
                d["question"] = "Every scene now has a plate on disk. Re-open this by clearing a " \
                                "scene's status in manifests/scene_locations.json."
    import datetime
    data = {
        "generated": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "counts": counts,
        "status": STATUS,
        "decisions": DECISIONS,
        "plateCatalogue": plate_catalogue(),
    }

    OUT.write_text(
        "window.PROJECTDATA = " + json.dumps(data, indent=1, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    open_dec = [d for d in DECISIONS if d["state"] == "open"]
    print("wrote %s" % rel(OUT))
    print("counts: %d shots, %d chunks, %d renders, QC %d/%d/%d (pass/fail/warn), "
          "%d stitched (%d film + %d gaps)" % (
              counts["shots"], counts["chunks"], counts["renders"],
              counts["qc_pass"], counts["qc_fail"], counts["qc_warn"],
              counts["stitched"], counts["film_scenes"], counts["gap_scenes"]))
    print("status: %d items (%s)" % (
        len(STATUS),
        ", ".join("%s=%s" % (s["id"], s["state"]) for s in STATUS)))
    print("decisions: %d total, %d open" % (len(DECISIONS), len(open_dec)))
    for d in DECISIONS:
        print("  [%s] %-28s %s" % ("x" if d["state"] == "open" else " ",
                                    d["id"], d["question"][:52]))


if __name__ == "__main__":
    main()