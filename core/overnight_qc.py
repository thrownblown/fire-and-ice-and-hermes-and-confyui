"""Overnight test-run driver: measured QC of every rendered chunk, retakes of
failures on the 5090 with fresh seeds, T0008 (original audio over S03), then
collect + re-QC + morning report.

Run:  python core/overnight_qc.py            (background; logs to stdout)
Phases are independent enough that a crash in one does not lose the others:
QC results, retake ledger and T0008 files all land on disk as they happen.

QC thresholds (absorbed-prod-lessons "measured QC", now absorbed):
  FAIL-black   blackdetect time  >= 30% of duration
  FAIL-frozen  freezedetect time >= 40% of duration
  WARN-silent  chunk has dialogue and mean_volume < -45 dB (info only:
               audio plans A/C replace H3 audio anyway)
Retake = same graph, seed + take*7919, filename_prefix _full_tNN.
"""
import json
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(r"E:/FNI")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "core"))
import fullrun  # reuse api(), upload(), queue_state(), ledgers  # noqa: E402

RUN = ROOT / "fullrun"
OUTPUT = RUN / "output"
GRAPHS = RUN / "graphs"
INPUT = RUN / "input"
REPORTS = ROOT / "reports"
QC_LEDGER = RUN / "qc-results.jsonl"
RETAKE_LEDGER = RUN / "retakes.jsonl"
T0008_DIR = ROOT / "runs" / "T0008_audio-over-s03"
MASTER_AUDIO = ROOT / "audio" / "master_audio_48k_stereo.wav"
MAX_PENDING = 8
POLL = 60
DRAIN_TIMEOUT_H = 10
TAG = date.today().isoformat()


def ff(args, timeout=120):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin"] + args,
                       capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stderr


def duration(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True, timeout=60)
    try:
        return float(p.stdout.strip())
    except ValueError:
        return 0.0


def qc_video(path, has_dialogue):
    dur = duration(path)
    if dur <= 0:
        return {"file": path.name, "verdict": "ERROR", "detail": "no duration"}
    out = {"file": path.name, "dur": round(dur, 2)}
    verdicts = []

    _, err = ff(["-i", str(path), "-vf", "blackdetect=d=0.4:pix_th=0.10",
                 "-an", "-f", "null", "-"])
    black = sum(float(m) for m in re.findall(r"black_duration:([\d.]+)", err))
    out["black_s"] = round(black, 2)
    if dur and black / dur >= 0.30:
        verdicts.append("FAIL-black")

    _, err = ff(["-i", str(path), "-vf", "freezedetect=n=-55dB:d=0.8",
                 "-map", "0:v", "-f", "null", "-"])
    frozen = sum(float(m) for m in re.findall(r"freeze_duration:([\d.]+)", err))
    out["frozen_s"] = round(frozen, 2)
    if dur and frozen / dur >= 0.40:
        verdicts.append("FAIL-frozen")

    rc, err = ff(["-i", str(path), "-af", "volumedetect", "-vn", "-f", "null", "-"])
    m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", err)
    if m:
        out["mean_db"] = float(m.group(1))
        if has_dialogue and out["mean_db"] < -45:
            verdicts.append("WARN-silent")
    else:
        out["mean_db"] = None
        if has_dialogue:
            verdicts.append("WARN-noaudio")

    out["verdict"] = ",".join(verdicts) if verdicts else "PASS"
    return out


def phase_qc(chunks_by_id):
    print("== phase 1: QC %d videos ==" % len(list(OUTPUT.glob("*_full_t01.mp4"))), flush=True)
    results = []
    with QC_LEDGER.open("w", encoding="utf-8") as fh:
        for n, path in enumerate(sorted(OUTPUT.glob("*_full_t01.mp4")), 1):
            cid = path.name[: -len("_full_t01.mp4")]
            row = chunks_by_id.get(cid, {})
            try:
                r = qc_video(path, bool(row.get("speakers")))
            except Exception as e:  # noqa: BLE001
                r = {"file": path.name, "verdict": "ERROR", "detail": str(e)[:200]}
            r["chunk_id"] = cid
            results.append(r)
            fh.write(json.dumps(r) + "\n")
            fh.flush()
            if r["verdict"] != "PASS":
                print("  [%d] %s %s" % (n, cid, r["verdict"]), flush=True)
            elif n % 50 == 0:
                print("  ... %d done" % n, flush=True)
    bad = [r for r in results if r["verdict"].startswith("FAIL") or r["verdict"] == "ERROR"]
    warn = [r for r in results if r["verdict"].startswith("WARN")]
    print("QC: %d pass, %d warn, %d fail/error" % (len(results) - len(bad) - len(warn), len(warn), len(bad)), flush=True)
    return results, bad


def existing_take(cid):
    n = 1
    while (OUTPUT / ("%s_full_t%02d.mp4" % (cid, n + 1))).exists():
        n += 1
    if RETAKE_LEDGER.exists():
        for r in fullrun.jl(RETAKE_LEDGER):
            if r.get("chunk_id") == cid:
                n = max(n, r.get("take", 1))
    return n + 1


def phase_retakes(bad):
    print("== phase 2: queue %d retakes ==" % len(bad), flush=True)
    queued = []
    fh = RETAKE_LEDGER.open("a", encoding="utf-8")
    try:
        for r in bad:
            cid = r["chunk_id"]
            gpath = GRAPHS / (cid + ".json")
            if not gpath.exists():
                print("  %s: no graph, cannot retake" % cid, flush=True)
                continue
            while True:
                run, pend = fullrun.queue_state()
                if run + pend < MAX_PENDING:
                    break
                time.sleep(POLL)
            take = existing_take(cid)
            g = json.loads(gpath.read_text(encoding="utf-8"))
            orig = int(g["129"]["inputs"]["noise_seed"])
            g["129"]["inputs"]["noise_seed"] = (orig + take * 7919) & 0x7FFFFFFFFFFFFFFF
            g["92"]["inputs"]["filename_prefix"] = "video/%s_full_t%02d" % (cid, take)
            ok = True
            for key in ("first", "last"):
                img = INPUT / ("%s_%s.jpg" % (cid, key))
                if not img.exists():
                    ok = False
                    break
                try:
                    fullrun.upload(img)
                except Exception as e:  # noqa: BLE001
                    print("  %s upload failed: %s" % (cid, e), flush=True)
                    ok = False
            if not ok:
                continue
            try:
                res = fullrun.api("/prompt", {"prompt": g}, timeout=90)
            except Exception as e:  # noqa: BLE001
                body = getattr(e, "read", lambda: b"")()
                print("  %s rejected: %s" % (cid, str(body)[:300] or e), flush=True)
                continue
            pid = res.get("prompt_id")
            if not pid:
                print("  %s rejected: %s" % (cid, res.get("node_errors")), flush=True)
                continue
            rec = {"chunk_id": cid, "take": take, "state": "queued", "prompt_id": pid,
                   "seed": g["129"]["inputs"]["noise_seed"], "reason": r["verdict"],
                   "ts": time.time()}
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            queued.append(rec)
            print("  queued %s t%02d (%s)" % (cid, take, r["verdict"]), flush=True)
            time.sleep(2)
    finally:
        fh.close()
    return queued


def phase_t0008(chunks_by_id):
    print("== phase 3: T0008 original audio over S03 ==", flush=True)
    T0008_DIR.mkdir(parents=True, exist_ok=True)
    made = []
    for cid, row in sorted(chunks_by_id.items()):
        if row.get("scene") != "S03":
            continue
        vid = OUTPUT / ("%s_full_t01.mp4" % cid)
        if not vid.exists():
            continue

        def secs(tc):
            h, m, s = tc.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)

        dst = T0008_DIR / ("%s_audioA.mp4" % cid)
        rc, err = ff(["-y", "-i", str(vid), "-ss", "%.3f" % secs(row["src_start"]),
                      "-i", str(MASTER_AUDIO), "-map", "0:v", "-map", "1:a",
                      "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                      str(dst)], timeout=300)
        if rc == 0 and dst.exists():
            made.append(dst.name)
            print("  built %s" % dst.name, flush=True)
        else:
            print("  %s FAILED: %s" % (cid, err[-300:]), flush=True)
    return made


def phase_collect(queued):
    print("== phase 4: wait + collect %d retakes ==" % len(queued), flush=True)
    deadline = time.time() + DRAIN_TIMEOUT_H * 3600
    while time.time() < deadline:
        run, pend = fullrun.queue_state()
        if run + pend == 0:
            break
        time.sleep(POLL)
    got, failed = [], []
    for rec in queued:
        cid, take = rec["chunk_id"], rec["take"]
        name = "%s_full_t%02d_00001_.mp4" % (cid, take)
        dst = OUTPUT / ("%s_full_t%02d.mp4" % (cid, take))
        try:
            data = fullrun.fetch("/view", {"filename": name, "subfolder": "video",
                                           "type": "output"})
            if len(data) > 1000:
                dst.write_bytes(data)
                got.append(dst.name)
                print("  collected %s (%d KB)" % (dst.name, len(data) // 1024), flush=True)
                continue
        except Exception:  # noqa: BLE001
            pass
        failed.append(cid)
        print("  MISSING %s t%02d" % (cid, take), flush=True)
    return got, failed


def main():
    chunks = [json.loads(l) for l in (RUN / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    chunks_by_id = {r["chunk_id"]: r for r in chunks}

    results, bad = phase_qc(chunks_by_id)
    queued = phase_retakes(bad) if bad else []
    t8 = phase_t0008(chunks_by_id)
    got, failed = phase_collect(queued) if queued else ([], [])

    # re-QC the collected retakes
    retake_qc = []
    for name in got:
        cid = name[: -len("_full_t02.mp4")] if name.endswith("_full_t02.mp4") else name.split("_full_t")[0]
        row = chunks_by_id.get(cid, {})
        try:
            r = qc_video(OUTPUT / name, bool(row.get("speakers")))
        except Exception as e:  # noqa: BLE001
            r = {"file": name, "verdict": "ERROR", "detail": str(e)[:200]}
        r["chunk_id"] = cid
        retake_qc.append(r)

    # morning report
    REPORTS.mkdir(exist_ok=True)
    rep = REPORTS / ("overnight-%s.md" % TAG)
    lines = ["# Overnight run %s" % TAG, "",
             "- QC: %d videos, %d FAIL, %d WARN-silent/noaudio" % (
                 len(results),
                 sum(1 for r in results if r["verdict"].startswith("FAIL") or r["verdict"] == "ERROR"),
                 sum(1 for r in results if r["verdict"].startswith("WARN"))),
             "- Retakes queued: %d, collected: %d, missing: %s" % (len(queued), len(got), failed or "none"),
             "- T0008 (original audio over S03): %s" % (", ".join(t8) or "none"),
             "", "## Failures (t01)", ""]
    for r in results:
        if r["verdict"] not in ("PASS",):
            lines.append("- %s: %s (black %.1fs, frozen %.1fs, dur %.1fs, %s dB)" % (
                r.get("chunk_id", r["file"]), r["verdict"], r.get("black_s", 0),
                r.get("frozen_s", 0), r.get("dur", 0), r.get("mean_db")))
    lines += ["", "## Retake verdicts", ""]
    for r in retake_qc:
        lines.append("- %s t02: %s" % (r.get("chunk_id", r["file"]), r["verdict"]))
    rep.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("== report: %s ==" % rep, flush=True)

    # optmem entry (append-only; the project chat pumps later)
    try:
        import optmem
        optmem.append_msg("work", (
            "Overnight run %s: QC'd %d rendered chunks (%d FAIL, %d WARN), queued %d "
            "retakes with fresh seeds, collected %d. T0008 built for S03 (%d files, "
            "original audio over rendered video — plan-A baseline). Report: "
            "reports/overnight-%s.md; ledgers: fullrun/qc-results.jsonl, fullrun/retakes.jsonl."
            % (TAG, len(results), len(bad),
               sum(1 for r in results if r["verdict"].startswith("WARN")),
               len(queued), len(got), len(t8), TAG)))
    except Exception as e:  # noqa: BLE001
        print("optmem append failed:", e, flush=True)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
