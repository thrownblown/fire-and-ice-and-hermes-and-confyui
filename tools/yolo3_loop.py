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
STATE3 = ROOT / "runs" / "yolo3_state.json"
OUT = ROOT / "runs" / "yolo_output3"
FRAMES = ROOT / "runs" / "yolo3_frames"
CHECKER = ROOT / "tools" / "vlm_cast_check.py"
CHUNKS = ROOT / "fullrun" / "chunks.jsonl"
CAST_LEDGER = ROOT / "runs" / "vlm_cast_check.jsonl"
LOOP_LEDGER = ROOT / "runs" / "yolo3_loop.jsonl"
TAKE = 2


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


def ready(cid: str) -> bool:
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


def analysed() -> set[str]:
    if not LOOP_LEDGER.exists():
        return set()
    return {json.loads(l)["chunk"] for l in LOOP_LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()}


def cast_rows(cid: str) -> list[dict]:
    if not CAST_LEDGER.exists():
        return []
    return [json.loads(l) for l in CAST_LEDGER.read_text(encoding="utf-8").splitlines()
            if l.strip() and json.loads(l).get("chunk") == cid and str(json.loads(l).get("take")) == str(TAKE)]


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


def verdict_for(cid: str, rows: list[dict]) -> tuple[str, int, list[str]]:
    """(verdict, max people seen in any shot, expected cast)."""
    seen = [r["observed"] for r in rows if isinstance(r.get("observed"), int)]
    obs_max = max(seen) if seen else 0
    exp = expected_cast(cid)
    if not rows or not seen:
        return "NO_READ", obs_max, exp
    if obs_max == 0:
        return "NOBODY", obs_max, exp
    if exp and obs_max > len(exp):
        return "EXTRA_PEOPLE", obs_max, exp
    return "COUNT_OK", obs_max, exp


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
    verdict, obs_max, exp = verdict_for(cid, rows)
    return {"chunk": cid, "file": str(clip), "bytes": clip.stat().st_size,
            "shots": len(rows), "ok": ok, "mismatch": len(bad), "unchecked": unk,
            "verdict": verdict, "observed_max": obs_max, "expected_cast": exp,
            "observations": [{"shot": r["shot"], "n": r.get("observed"),
                              "people": (r.get("people") or [])[:3]} for r in rows],
            "mismatch_shots": [{"shot": r["shot"], "claimed": r["claimed"], "observed": r["observed"]}
                               for r in bad],
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "checker_rc": rc.returncode}


def sweep(batch: int, max_wait: float) -> int:
    done = analysed()
    todo = [c for c in queued_chunks() if c not in done]
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
        with LOOP_LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
        got += 1
        print("   %s: %s — %d shot(s) read, max %d people vs cast %s %s"
              % (cid, row["verdict"], row["shots"], row["observed_max"],
                 ",".join(row["expected_cast"]) or "?",
                 "" if row["verdict"] == "COUNT_OK"
                 else "  <-- EXTRA people vs cast" if row["verdict"] == "EXTRA_PEOPLE" else ""),
              flush=True)
    return got


def main() -> None:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--once", action="store_true", help="one sweep, then exit")
    ap.add_argument("--every", type=int, default=180, help="seconds between sweeps (looping mode)")
    ap.add_argument("--batch", type=int, default=3, help="clips to judge per VLM window")
    ap.add_argument("--max-wait", type=float, default=900, help="seconds to wait for a batch to land")
    args = ap.parse_args()

    total = 0
    while True:
        total += sweep(args.batch, args.max_wait)
        if args.once:
            break
        time.sleep(args.every)
    print("loop: %d clip(s) judged this run" % total)


if __name__ == "__main__":
    main()
