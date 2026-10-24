# -*- coding: utf-8 -*-
"""T0019 drain: collect -> verify -> metrics -> source-audio overlays -> scene stitch.

Run once the 5090 queue is empty (the batch is running server-side; this is a
collect-only pass — no re-queueing, even if a render looks lost here).

    .venv/Scripts/python.exe runs/t0019_drain.py
"""
import sys, os, json, time, subprocess, urllib.parse, urllib.request, csv
from pathlib import Path

sys.path.insert(0, r"E:/FNI/pipeline")
sys.path.insert(0, r"E:/FNI")
import fullrun  # noqa: E402

ROOT = Path(r"E:/FNI")
T0003 = ROOT / "runs" / "T0003_s03_fl2va-srcfflf"
RUN = ROOT / "runs" / "T0019_s03_vlm-prompt-sweep"
COMFY = os.environ.get("FNI_COMFY", "http://<TOMBSTONE_TS_IP>:8188")
FULLRUN_COMFY = fullrun.COMFY

CHUNK_SHOTS = {
    "s03-c02": ["00068", "00069"],
    "s03-c03": ["00070", "00071"],
    "s03-c04": ["00072"],
    "s03-c05": ["00073", "00074"],
}
# render lengths (seconds) straight from the reused T0003 graphs
RENDER_S = {}
for c in CHUNK_SHOTS:
    g = json.loads((T0003 / (c + ".json")).read_text(encoding="utf-8"))
    RENDER_S[c] = g["132"]["inputs"]["value"]

REPORT = []


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode and "report" not in str(cmd):
        sys.stderr.write("cmd failed: %s\n%s\n" % (cmd, r.stderr[:400]))
    return r.returncode == 0, r.stdout


def ffprobe_dur(p):
    ok, out = sh("ffprobe -v error -show_entries format=duration -of csv=p=0 \"%s\"" % p)
    return float(out.strip()) if ok and out.strip() else None


def collect(chunk, pid):
    fullrun.COMFY = COMFY
    h = fullrun.api("/history/" + pid)
    rec = h.get(pid, {})
    st = rec.get("status_str") or rec.get("status")
    mp4 = None
    for o in rec.get("outputs", {}).values():
        for okey in ("videos", "images", "animated"):
            for v in o.get(okey, []) or []:
                if isinstance(v, dict) and "filename" in v and v["filename"].endswith(".mp4"):
                    mp4 = v
    if not mp4:
        return {"chunk": chunk, "status": st, "error": "no mp4 in history record"}
    url = "%s/view?filename=%s&subfolder=%s&type=output" % (
        COMFY, urllib.parse.quote(mp4["filename"]), urllib.parse.quote(mp4.get("subfolder", "")))
    dest = RUN / "output" / mp4["filename"]
    dest.parent.mkdir(exist_ok=True)
    subprocess.run(["curl", "-4", "-s", "-o", str(dest), url], check=True)
    dur = ffprobe_dur(dest)
    return {"chunk": chunk, "status": st, "file": str(dest), "dur": dur,
            "expected_dur": RENDER_S[chunk], "size": dest.stat().st_size,
            "ok": bool(dur) and abs(dur - RENDER_S[chunk]) < 0.25}


def source_audio(chunk, dest):
    """Concat the chunk's source shot clips, trim to the render length."""
    parts = []
    for n in CHUNK_SHOTS[chunk]:
        p = ROOT / "clips/full" / ("shot_%s.mp4" % n)
        if p.exists():
            parts.append("file '%s'" % p)
    lst = RUN / "scratch" / ("audio_list_%s.txt" % chunk)
    lst.parent.mkdir(parents=True, exist_ok=True)
    lst.write_text("\n".join(parts), encoding="utf-8")
    ok1, _ = sh("ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i \"%s\" -vn "
                "-t %.3f \"%s\"" % (lst, RENDER_S[chunk], dest))
    return ok1


def overlay(chunk, render, audio, out):
    ok, _ = sh("ffmpeg -hide_banner -loglevel error -y -i \"%s\" -i \"%s\" -map 0:v:0 "
               "-map 1:a:0 -c:v copy -c:a aac -shortest \"%s\"" % (render, audio, out))
    return ok


def concat_mp4(files, out, tag):
    lst = Path(out).parent / (tag + "_concat.txt")
    lst.write_text("\n".join("file '%s'" % f for f in files), encoding="utf-8")
    return sh("ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i \"%s\" "
              "-c copy \"%s\"" % (lst, out))[0]


def main():
    fullrun.COMFY = COMFY
    queued = json.loads((RUN / "queued.json").read_text(encoding="utf-8"))
    results = []
    # c01 is T0018's output — include it in the scene stitch
    all_chunks = ["s03-c01"] + list(CHUNK_SHOTS)
    vlm_files = {}
    t0003_files = []

    for chunk in all_chunks:
        if chunk == "s03-c01":
            f = ROOT / "runs/T0018_s03_vlm-prompt-fl2va/output/s03-c01_T0018_t01_00001_.mp4"
            if f.exists():
                vlm_files[chunk] = f
            ref = T0003 / "output/s03-c01_T0003_t01.mp4"
            if ref.exists():
                t0003_files.append(ref)
            continue
        pid = queued[chunk]["prompt_id"]
        r = collect(chunk, pid)
        results.append(r)
        if r.get("ok"):
            vlm_files[chunk] = Path(r["file"])
            ref = T0003 / ("output/%s_T0003_t01.mp4" % chunk)
            if ref.exists():
                t0003_files.append(ref)
            # source-audio overlay for the compare
            audio = RUN / "scratch" / ("%s_src_audio.m4a" % chunk)
            source_audio(chunk, audio)
            overlay(chunk, r["file"], audio, RUN / "output" / ("compare_%s_vlm_srcAudio.mp4" % chunk))
        time.sleep(2)  # stable-size: let the host finish writing before next ops

    # scene stitches, story order
    if len(vlm_files) == 5:
        vlm_files_sorted = [vlm_files[c] for c in sorted(vlm_files)]
        concat_mp4(vlm_files_sorted, RUN / "output" / "S03_vlm_T0019+T0018_stitched.mp4", "vlm")
    if len(t0003_files) == 5:
        t0003_files_sorted = [T0003 / ("output/s03-c%02d_T0003_t01.mp4" % i) for i in range(1, 6)]
        concat_mp4(t0003_files_sorted, RUN / "output" / "S03_template_T0003_stitched.mp4", "t0003")
        # source-audio overlays of both scene stitches
        scene_audio = RUN / "scratch" / "s03_scene_src_audio.m4a"
        all_shots = ["00067", "00068", "00069", "00070", "00071", "00072", "00073", "00074"]
        lst = RUN / "scratch" / "s03_scene_audio_list.txt"
        lst.write_text("\n".join("file '%s'" % (ROOT / "clips/full" / ("shot_%s.mp4" % s))
                                 for s in all_shots), encoding="utf-8")
        lst.parent.mkdir(parents=True, exist_ok=True)
        total_s = sum(RENDER_S[c] for c in RENDER_S) + 5.875
        sh("ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i \"%s\" -vn -t %.3f \"%s\""
           % (lst, total_s, scene_audio))
        overlay("scene", RUN / "output" / "S03_vlm_T0019+T0018_stitched.mp4",
                scene_audio, RUN / "output" / "S03_vlm_srcAudio_stitched.mp4")
        overlay("scene", RUN / "output" / "S03_template_T0003_stitched.mp4",
                scene_audio, RUN / "output" / "S03_template_srcAudio_stitched.mp4")

    (RUN / "drain-report.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("chunk | status | dur (expect) | ok")
    for r in results:
        print("%s | %s | %s (%s) | %s" % (r["chunk"], r.get("status"),
                                          r.get("dur"), r.get("expected_dur"), r.get("ok")))
    print("stitch files:", [p.name for p in sorted((RUN / "output").glob("S03_*.mp4"))])


if __name__ == "__main__":
    main()
