"""Tight feedback loop for a render pass: pull the moment a take lands, extract frames at each
shot's midpoint, judge with the audit-grade VLM, record the verdict.

Two things make this "sooner" than the old pull:
  1. Completion is detected by PROBING THE DETERMINISTIC FILENAME, not by `/history` — the 5090
     keeps history in memory and a reboot wipes it (that is exactly why pass 2's 134 finished
     takes sat unpulled). Looking for the file also means we notice a take the second it lands.
  2. Frames + judgement happen per clip as it arrives, not in one pass at the end.

Judging: `tools/vlm_cast_check.py` with FNI_CAST_BACKEND=goldfishbowl — the box's 32B, its
designated description-only frame reader, and the audit-grade one. Counts and attribute
descriptions only; it never asks the model for a name (asked for one, it invents films and actors).

Batch size matters: goldfishbowl is single-resident, so a switch costs ~15-40 s. The loop waits
until `--batch` clips are ready (or `--max-wait` elapses) and then judges them in one window,
rather than evicting/loading per frame.

    .venv/Scripts/python.exe tools/yolo3_loop.py --once      # one sweep, then exit
    .venv/Scripts/python.exe tools/yolo3_loop.py --every 180 # keep sweeping
"""
from __future__ import annotations

import argparse
import json
import re
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(r"E:/FNI")
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
COMFY = os.environ.get("FNI_COMFY", "http://<TOMBSTONE_TS_IP>:8188").rstrip("/")
STATE3 = ROOT / "runs" / "yolo3_state.json"       # take-02 pass (legacy filename)


def state_for(take: int) -> Path:
    """The queue-state file for a take — yolo3_state.json is the LEGACY name for take 02."""
    return (ROOT / "runs" / "yolo3_state.json") if take == 2 else (ROOT / "runs" / ("yolo_t%02d_state.json" % take))
OUT = ROOT / "runs" / "yolo_output3"
FRAMES = ROOT / "runs" / "yolo3_frames"
CHECKER = ROOT / "tools" / "vlm_cast_check.py"
CHUNKS = ROOT / "fullrun" / "chunks.jsonl"
CAST_LEDGER = ROOT / "runs" / "vlm_cast_check.jsonl"
LOOP_LEDGER = ROOT / "runs" / "yolo3_loop.jsonl"
TAKE = 2        # default; override with --take (e.g. --take 3 for the plated pass)


def queued_chunks() -> list[str]:
    if not STATE3.exists():
        return []
    st = json.loads(STATE3.read_text(encoding="utf-8"))
    return sorted(c for c, v in st.get("chunks", {}).items() if v.get("queued"))


def seed_of(cid: str) -> int | None:
    """The seed pass 3 queued for this chunk — an explicit --seed becomes part of the filename."""
    if not STATE3.exists():
        return None
    return json.loads(STATE3.read_text(encoding="utf-8")).get("chunks", {}).get(cid, {}).get("seed")


def remote_names(cid: str) -> list[str]:
    """Candidate output names, best first.

    `build_technicolor_audio_only.finalize_graph` appends `_s<seed>` to the tag when a seed is
    passed explicitly (pass 3 does; passes 1-2 did not), so the seed-suffixed form is the one to
    expect — with the unsuffixed form kept as a fallback so the loop also works on a pass that
    used its ledger seed.
    """
    seed = seed_of(cid)
    names = []
    if seed is not None:
        names.append(f"{cid}_audioOnly_t{TAKE:02d}_s{seed}_00001_.mp4")
    names.append(f"{cid}_audioOnly_t{TAKE:02d}_00001_.mp4")
    return names


_HISTORY = {"t": 0.0, "names": set()}


def history_names(max_age: float = 30.0) -> set:
    """Every output filename ComfyUI has finished, in ONE request.

    Probing each of the 449 queued clips with its own HTTP request took minutes per round while the
    GPU was busy rendering (a 404 during a render can take seconds), so the loop sat silent with an
    empty log and looked dead. /history already lists completed outputs, so read it once and match.
    """
    now = time.time()
    if now - _HISTORY["t"] < max_age and _HISTORY["names"]:
        return _HISTORY["names"]
    names = set()
    try:
        with urllib.request.urlopen(f"{COMFY}/history", timeout=30) as r:
            for v in json.load(r).values():
                for o in (v.get("outputs") or {}).values():
                    for key in ("images", "videos", "gifs", "animated"):
                        for f in (o.get(key) or []):
                            if isinstance(f, dict) and f.get("filename"):
                                names.add(f["filename"])
    except Exception:  # noqa: BLE001
        pass
    if names:
        _HISTORY.update(t=now, names=names)
    return names


def ready(cid: str) -> bool:
    names = history_names()
    if names:
        return any(fn in names for fn in remote_names(cid))
    # no history available: fall back to probing the file endpoint
    for fn in remote_names(cid):
        try:
            with urllib.request.urlopen(f"{COMFY}/view?filename={fn}&subfolder=video&type=output",
                                        timeout=20) as r:
                if r.status == 200:
                    return True
        except urllib.error.HTTPError:
            continue
        except Exception:  # noqa: BLE001
            continue
    return False


def pull(cid: str) -> Path | None:
    for fn in remote_names(cid):
        dst = OUT / fn
        if dst.exists() and dst.stat().st_size > 1000:
            return dst
        url = f"{COMFY}/view?filename={fn}&subfolder=video&type=output"
        try:
            with urllib.request.urlopen(url, timeout=300) as r:
                data = r.read()
        except urllib.error.HTTPError:
            continue
        except Exception as e:  # noqa: BLE001
            print("   pull failed %s: %s" % (cid, str(e)[:80]))
            return None
        OUT.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        return dst
    return None


def analysed() -> set:
    """(chunk, take) pairs already judged — NOT chunks alone.

    Keying by chunk alone meant every chunk judged in take 2 was skipped forever: take 3's renders
    landed, `ready()` found them, and the loop still reported 'no clip ready' because the chunk was
    already in the ledger from the previous take. Old rows predate the `take` field, so the take is
    recovered from the clip filename (`..._t03_...`).
    """
    if not LOOP_LEDGER.exists():
        return set()
    out = set()
    for l in LOOP_LEDGER.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        cid = r.get("chunk")
        if not cid:
            continue
        take = r.get("take")
        if take is None:
            m = re.search(r"_t(\d+)(?:_s\d+)?_", str(r.get("file") or ""))
            take = int(m.group(1)) if m else 2      # rows written before the take field existed
        out.add((cid, str(take)))
    return out


def cast_rows(cid: str) -> list[dict]:
    """This chunk's take-2 rows from the cast ledger, newest run only, one row per shot.

    The checker APPENDS per run, so a chunk that has been judged twice has two rows per shot;
    taking them all would double-count in `extra_shots` and skew the max.
    """
    if not CAST_LEDGER.exists():
        return []
    by_shot = {}
    for l in CAST_LEDGER.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        if r.get("chunk") == cid and str(r.get("take")) == str(TAKE):
            by_shot[r.get("shot")] = r          # last write wins = newest run
    return list(by_shot.values())


def expected_cast(cid: str) -> list[str]:
    """The chunk's cast per the ledger: its dialogue speakers plus its stamped names.

    This is the fallback the per-shot claim cannot give us on a yolo pass. `vlm_cast_check`
    compares each shot against the prompt's per-shot "exactly N people" line — but that line
    only ever went into the T0017 S03 arms (queued with `--shot-presence`); the yolo passes
    never carried it, so every shot comes back UNCHECKED and UNCHECKED is NOT agreement.
    The ledger's cast still gives a real test: a shot cannot legitimately show MORE people
    than the chunk has cast — and "more people than cast" is the exact failure the audits
    keep finding (invented extras in the crowd/group chunks).
    """
    if not CHUNKS.exists():
        return []
    for l in CHUNKS.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        if r.get("chunk_id") == cid:
            names = list(r.get("speakers") or []) + list(r.get("stamped_names") or [])
            return sorted(dict.fromkeys(names))
    return []


def expected_counts(cid: str) -> dict[str, int]:
    """Per-shot people counts from the chunk ledger — what the SOURCE shot held.

    Better baseline than the named cast, and per-shot rather than chunk-level: a crowd chunk
    legitimately holds a crowd that nobody bothered to stamp as a character, so comparing
    against `len(named cast)` fires EXTRA_PEOPLE on every group scene. `people_count` is the
    number the film's own shot had, aligned with `shot_nums`.
    """
    if not CHUNKS.exists():
        return {}
    for l in CHUNKS.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        if r.get("chunk_id") == cid:
            nums = [str(n) for n in (r.get("shot_nums") or [])]
            counts = r.get("people_count") or []
            out = {}
            for n, c in zip(nums, counts):
                s = str(c).strip()
                if s.isdigit():
                    out[n] = int(s)
            return out
    return {}


def verdict_for(cid: str, rows: list[dict]) -> tuple[str, int, list[str], dict, list[dict]]:
    """(verdict, max people seen, expected cast, per-shot expectations, extra-people shots).

    The test is per shot, against the source shot's own count: the render may not put MORE
    people in a shot than the film had there. That is the invented-extras failure, and it needs
    no per-shot line in the prompt (the yolo prompts never had one).
    """
    seen = [r["observed"] for r in rows if isinstance(r.get("observed"), int)]
    obs_max = max(seen) if seen else 0
    exp = expected_cast(cid)
    exp_counts = expected_counts(cid)
    extras = []
    for r in rows:
        if not isinstance(r.get("observed"), int):
            continue
        num = str(r.get("shot", "")).split(":")[-1]
        want = exp_counts.get(num)
        if want is not None and r["observed"] > want:
            extras.append({"shot": num, "observed": r["observed"], "source": want})
    if not rows or not seen:
        return "NO_READ", obs_max, exp, exp_counts, extras
    if obs_max == 0:
        return "NOBODY", obs_max, exp, exp_counts, extras
    if extras:
        return "EXTRA_PEOPLE", obs_max, exp, exp_counts, extras
    if not exp_counts:
        # no source counts for this chunk — fall back to the cast-size screen, and say so
        return ("EXTRA_PEOPLE" if exp and obs_max > len(exp) else "COUNT_OK_SOFT"), obs_max, exp, exp_counts, extras
    return "COUNT_OK", obs_max, exp, exp_counts, extras


def bake_spa() -> None:
    """Re-bake browser/yolo2-data.js so the 'Yolo 2' tab is current without anyone remembering.

    Cheap (a few hundred ms over ~257 clips) and idempotent, so it is safe to run after every
    batch. Failure is reported and never fatal: the loop's own ledger is the record of truth,
    the data file is just the view of it.
    """
    r = subprocess.run([PY, str(ROOT / "tools" / "build_yolo2_data.py")],
                       capture_output=True, text=True, timeout=600)
    line = (r.stdout or r.stderr or "").strip().splitlines()
    print("   spa bake: %s" % (line[-1] if line else "(no output)"), flush=True)


def judge(cid: str, clip: Path) -> dict:
    env = dict(os.environ, FNI_CAST_BACKEND="goldfishbowl")
    fd = FRAMES / cid
    rc = subprocess.run([PY, str(CHECKER), "--clip", str(clip), "--chunk", cid,
                         "--take", str(TAKE), "--frames-dir", str(fd)],
                        capture_output=True, text=True, timeout=3600, env=env)
    rows = cast_rows(cid)
    ok = sum(1 for r in rows if r["verdict"] == "OK")
    bad = [r for r in rows if r["verdict"] == "MISMATCH"]
    unk = sum(1 for r in rows if r["verdict"] == "UNCHECKED")
    verdict, obs_max, exp, exp_counts, extras = verdict_for(cid, rows)
    return {"chunk": cid, "file": str(clip), "bytes": clip.stat().st_size,
            "shots": len(rows), "ok": ok, "mismatch": len(bad), "unchecked": unk,
            "verdict": verdict, "observed_max": obs_max, "expected_cast": exp,
            "expected_counts": exp_counts, "extra_shots": extras,
            "observations": [{"shot": r["shot"], "n": r.get("observed"),
                              "people": (r.get("people") or [])[:3]} for r in rows],
            "mismatch_shots": [{"shot": r["shot"], "claimed": r["claimed"], "observed": r["observed"]}
                               for r in bad],
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "checker_rc": rc.returncode}


def sweep(batch: int, max_wait: float, no_bake: bool = False) -> int:
    done = analysed()
    todo = [c for c in queued_chunks() if (c, str(TAKE)) not in done]
    if not todo:
        print("nothing new to analyse (%d queued, all analysed)" % len(queued_chunks()))
        return 0

    # gather a batch: wait for clips to land, so the VLM is loaded once per batch
    t0 = time.time()
    landing: list[str] = []
    while todo and (len(landing) < batch) and (time.time() - t0) < max_wait:
        for cid in list(todo):
            if ready(cid):
                landing.append(cid)
                todo.remove(cid)
                if len(landing) >= batch:
                    break
        if len(landing) < batch:
            time.sleep(20)
    if not landing:
        print("no clip ready yet (%d still rendering/queued)" % len(todo))
        return 0

    print("batch of %d ready: %s" % (len(landing), ", ".join(landing)), flush=True)
    got = 0
    for cid in landing:
        clip = pull(cid)
        if not clip:
            continue
        print("  judging %s (%d KB)..." % (cid, clip.stat().st_size // 1024), flush=True)
        try:
            row = judge(cid, clip)
        except Exception as e:  # noqa: BLE001
            print("   judge failed %s: %s" % (cid, str(e)[:120]))
            continue
        row["take"] = TAKE          # so 'already judged' can be keyed by (chunk, take)
        with LOOP_LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
        got += 1
        print("   %s: %s — %d shot(s) read, max %d people%s"
              % (cid, row["verdict"], row["shots"], row["observed_max"],
                 ("  <-- " + ", ".join("shot %s: %d vs source %d" % (e["shot"], e["observed"], e["source"])
                                       for e in row["extra_shots"][:3])) if row["extra_shots"] else ""),
              flush=True)
    if got and not no_bake:
        bake_spa()
    return got


def main() -> None:
    global TAKE, STATE3   # must precede the argparse default below, which reads module-level TAKE
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--take", type=int, default=TAKE, help="which take to pull/judge (default 2)")
    ap.add_argument("--once", action="store_true", help="one sweep, then exit")
    ap.add_argument("--every", type=int, default=180, help="seconds between sweeps (looping mode)")
    ap.add_argument("--batch", type=int, default=3, help="clips to judge per VLM window")
    ap.add_argument("--no-bake", action="store_true",
                    help="do not re-bake browser/yolo2-data.js after each batch")
    ap.add_argument("--max-wait", type=float, default=900, help="seconds to wait for a batch to land")
    args = ap.parse_args()
    global STATE3
    TAKE = args.take
    STATE3 = state_for(TAKE)      # else the loop reads take 02's queue while looking for take 03 files

    total = 0
    while True:
        total += sweep(args.batch, args.max_wait, args.no_bake)
        if args.once:
            break
        time.sleep(args.every)
    print("loop: %d clip(s) judged this run" % total)


if __name__ == "__main__":
    main()
