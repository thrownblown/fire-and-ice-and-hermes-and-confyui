# -*- coding: utf-8 -*-
"""Fix T0019 overlays: stretch each chunk's source audio to the EXACT render
length (renders snap up to the 17k+5 grid, so source audio is slightly short),
then re-do the per-chunk compares and the stitched-scene overlays so no video
is chopped and dialogue stays in frame.

    .venv/Scripts/python.exe runs/t0019_fixoverlays.py
"""
import sys, json, subprocess
from pathlib import Path

ROOT = Path(r"E:/FNI")
T0018 = ROOT / "runs/T0018_s03_vlm-prompt-fl2va"
T0019 = ROOT / "runs/T0019_s03_vlm-prompt-sweep"
T0003 = ROOT / "runs/T0003_s03_fl2va-srcfflf"

# chunk -> (source shots in order, render seconds, render mp4 for c01 = T0018)
CHUNKS = {
    "s03-c01": (["00067"], 5.875, T0018 / "output/s03-c01_T0018_t01_00001_.mp4"),
    "s03-c02": (["00068", "00069"], 9.416667, T0019 / "output/s03-c02_T0019_t01_00001_.mp4"),
    "s03-c03": (["00070", "00071"], 9.416667, T0019 / "output/s03-c03_T0019_t01_00001_.mp4"),
    "s03-c04": (["00072"], 5.166667, T0019 / "output/s03-c04_T0019_t01_00001_.mp4"),
    "s03-c05": (["00073", "00074"], 8.0, T0019 / "output/s03-c05_T0019_t01_00001_.mp4"),
}
SCRATCH = T0019 / "scratch"
SCRATCH.mkdir(parents=True, exist_ok=True)


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode:
        sys.stderr.write("FAILED: %s\n%s\n" % (cmd[:160], r.stderr[:400]))
    return r.returncode == 0


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def main():
    order = ["s03-c01", "s03-c02", "s03-c03", "s03-c04", "s03-c05"]
    stretched = []
    for chunk in order:
        shots, render_s, render_mp4 = CHUNKS[chunk]
        # 1. concat the source shot clips' audio
        lst = SCRATCH / ("fix_list_%s.txt" % chunk)
        lst.write_text("\n".join("file '%s'" % (ROOT / "clips/full" / ("shot_%s.mp4" % s))
                                 for s in shots), encoding="utf-8")
        raw = SCRATCH / ("fix_raw_%s.m4a" % chunk)
        sh("ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i \"%s\" -vn \"%s\"" % (lst, raw))
        d = dur(raw)
        # 2. stretch to the exact render length (0.907..1.0 range -> atempo ok)
        out = SCRATCH / ("fix_stretch_%s.m4a" % chunk)
        atempo = max(0.5, min(2.0, d / render_s))
        sh("ffmpeg -hide_banner -loglevel error -y -i \"%s\" -af atempo=%.6f -t %.3f \"%s\""
           % (raw, atempo, render_s, out))
        dd = dur(out)
        print("%s src %.3fs -> render %.3fs atempo %.4f => %.3fs" % (chunk, d, render_s, atempo, dd))
        stretched.append(out)

    # 3. concat the per-chunk stretched audio in story order -> scene audio
    scene_lst = SCRATCH / "fix_scene_list.txt"
    scene_lst.write_text("\n".join("file '%s'" % s for s in stretched), encoding="utf-8")
    scene_audio = SCRATCH / "fix_scene_audio.m4a"
    sh("ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i \"%s\" -c copy \"%s\""
       % (scene_lst, scene_audio))
    print("scene audio:", dur(scene_audio), "s (scenes are", sum(CHUNKS[c][1] for c in order), "s)")

    # 4. per-chunk compares: source audio stretched to FULL render length
    for chunk in order:
        shots, render_s, render_mp4 = CHUNKS[chunk]
        a = SCRATCH / ("fix_stretch_%s.m4a" % chunk)
        out = T0019 / "output" / ("compare_%s_vlm_srcAudio.mp4" % chunk)
        sh("ffmpeg -hide_banner -loglevel error -y -i \"%s\" -i \"%s\" -map 0:v:0 -map 1:a:0 "
           "-c:v copy -c:a aac -shortest \"%s\"" % (render_mp4, a, out))
        print("compare", chunk, "now", dur(out), "s")

    # 5. scene stitches with the full-length audio
    vlm_scene = T0019 / "output/S03_vlm_T0019+T0018_stitched.mp4"
    tpl_scene = T0019 / "output/S03_template_T0003_stitched.mp4"
    for src, tag in ((vlm_scene, "S03_vlm_srcAudio_stitched.mp4"),
                     (tpl_scene, "S03_template_srcAudio_stitched.mp4")):
        out = T0019 / "output" / tag
        sh("ffmpeg -hide_banner -loglevel error -y -i \"%s\" -i \"%s\" -map 0:v:0 -map 1:a:0 "
           "-c:v copy -c:a aac -shortest \"%s\"" % (src, scene_audio, out))
        print(tag, "now", dur(out), "s")


if __name__ == "__main__":
    main()
