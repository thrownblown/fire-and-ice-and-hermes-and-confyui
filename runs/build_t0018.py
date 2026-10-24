# -*- coding: utf-8 -*-
"""T0018 — VLM-authored FL2VA prompt vs T0003 template (single chunk S03-c01).

One variable: node 138's prompt text. Reuses T0003's exact graph (same two
bookend stills, same seed, same FL2VA weight, same steps/length), so the
rendered take lands side by side with T0003's s03-c01.

The VLM (4090, LM Studio qwen3-vl-8b@q4) describes the actual first and last
frames. A deterministic assembler writes the FL2VA middle: ROSTER identity
string + VLM start-frame anchor + dialogue verbatim + VLM end-frame anchor +
deferred arrival. Same 3-field FL2VA grammar -> validate_prompt() still applies.

    .venv/Scripts/python.exe runs/build_t0018.py --dry-run     # VLM + assemble, no GPU
    .venv/Scripts/python.exe runs/build_t0018.py --queue       # upload + POST to 5090
    .venv/Scripts/python.exe runs/build_t0018.py --collect <prompt_id>
"""
import sys, os, json, base64, time, shutil, subprocess, argparse, urllib.request
from pathlib import Path

sys.path.insert(0, r"E:/FNI/pipeline")
sys.path.insert(0, r"E:/FNI")

import fullrun  # noqa: E402

ROOT = Path(r"E:/FNI")
RUN = ROOT / "runs" / "T0018_s03_vlm-prompt-fl2va"
SRC_GRAPH = ROOT / "runs" / "T0003_s03_fl2va-srcfflf" / "s03-c01.json"
SRC_TXT = ROOT / "runs" / "T0003_s03_fl2va-srcfflf" / "s03-c01.txt"

COMFY_5090 = os.environ.get("FNI_COMFY", "http://<TOMBSTONE_TS_IP>:8188")
LM = os.environ.get("FNI_LM", "http://127.0.0.1:1234/v1/chat/completions")
VLM = os.environ.get("FNI_VLM", "qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s")

FIRST_STILL = ROOT / "stills/full" / "shot_00067_f00000.jpg"
LAST_STILL = ROOT / "stills/full" / "shot_00067_f00127.jpg"

# Consistent character strings (ROSTER) — the same stable descriptors used for
# every prompt, so identity does not drift when the VLM re-describes the frame.
CHAR = "an older woman with long straight black hair and crimson lips, in a deep purple " \
       "long-sleeved gown with long silver dagger-shaped earrings"
SPEAKER_DESC = "a pale, regal older queen, long straight black hair, crimson lips, deep " \
               "purple long-sleeved gown, long silver dagger-shaped earrings"
SPEAKER_ID = "(S1)"

DIALOGUE = [
    "You have done well, my son.",
    "The North Village has fallen. We have won.",
]

VLM_PROMPT = (
    "This is one still frame from a dramatic film, in a stone throne hall. "
    "Describe exactly what is in frame, concretely and without guessing: "
    "where the main figure is positioned in the frame, the direction she faces and "
    "the height she sits or stands at, what her hands hold or rest on, her head and "
    "gaze, and any visible prop, furniture, or background element she occupies. "
    "Use only the character description given below when naming the figure. "
    "Do not mention colors, lighting, mood, or anything not visible. "
    "Two short sentences only.\n\n"
    "Character: %s"
) % SPEAKER_DESC


def vlm(path):
    b64 = base64.b64encode(Path(path).read_bytes()).decode()
    body = json.dumps({
        "model": VLM,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}},
            {"type": "text", "text": VLM_PROMPT}]}],
        "max_tokens": 130, "temperature": 0.15,
    }).encode()
    req = urllib.request.Request(LM, data=body, headers={"Content-Type": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                return json.load(r)["choices"][0]["message"]["content"].strip()
        except Exception as e:  # noqa: BLE001
            if attempt == 3:
                return "ERROR: %s" % e
            time.sleep(3 * (attempt + 1))
    return "ERROR"


def get_vlm_cache():
    f = RUN / "vlm_frames.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return {}


def cache_vlm():
    cache = get_vlm_cache()
    changed = False
    for key, still in (("first", FIRST_STILL), ("last", LAST_STILL)):
        if key not in cache:
            print("  VLM %s frame ->" % key, still.name)
            out = vlm(still)
            print("   ", out)
            cache[key] = out
            changed = True
    (RUN / "vlm_frames.json").write_text(json.dumps(cache, indent=2), encoding="utf-8")
    return cache


def clean_desc(s):
    # strip a leading label the VLM sometimes adds; keep it to one block of prose
    s = s.replace("\n", " ").strip()
    for junk in ("First frame:", "Frame:", "Description:", "Answer:"):
        if s.lower().startswith(junk.lower()):
            s = s[len(junk):].strip()
    s = s.rstrip(".")
    return s


def assemble(cache):
    style = fullrun.style_line("Ice Peak throne hall")
    instr = (
        "How the reference pictures align with the target video — Picture 1 (from Shot 1) "
        "aligns with the 0.00-second mark of the target video; Picture 2 (from Shot 1) "
        "aligns with the 5.88-second mark of the target video."
    )
    shot = []
    shot.append("[Shot 1] " + style + ".")
    shot.append("The opening frame matches <Picture 1>: " + clean_desc(cache["first"]) + ".")
    shot.append(SPEAKER_DESC + " " + SPEAKER_ID + " is on screen and speaks: "
                + " ".join("<d>[English] %s</d>" % t for t in DIALOGUE) + ".")
    shot.append(
        "The camera holds the medium three-quarter framing. Only in the last seconds do "
        "these small movements — a shifted gaze, a tilt of the head, the settle of the "
        "gown — slow and stop, and the figure comes to rest in the pose, spacing, "
        "framing, and position the end frame establishes: " + clean_desc(cache["last"]) + "."
    )
    parts = " ".join(shot)
    text = "\n\n".join([
        instr,
        "integrated_multimodal_description: " + parts,
        "overall_soundscape: " + fullrun.soundscape_line({"location": "Ice Peak throne hall",
                                                          "cast": "JULIANA", "scene_title": ""}),
        "non_diegetic_music: " + fullrun.music_line("cold sinister orchestral"),
    ])
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--queue", action="store_true")
    ap.add_argument("--collect", default=None)
    args = ap.parse_args()

    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "input").mkdir(exist_ok=True)
    (RUN / "output").mkdir(exist_ok=True)
    (RUN / "vlm-cache").mkdir(exist_ok=True)

    if args.collect:
        collect(args.collect)
        return

    # 1. copy the two bookend stills (exact same files T0003 queued)
    first_dst = RUN / "input" / "s03-c01_first.jpg"
    last_dst = RUN / "input" / "s03-c01_last.jpg"
    for src, dst in ((FIRST_STILL, first_dst), (LAST_STILL, last_dst)):
        if not dst.exists() or dst.stat().st_size != src.stat().st_size:
            shutil.copy(src, dst)
            print("copied", src.name, "->", dst.name)

    # 2. VLM describe the actual bookend frames (cached -> rebuild is free)
    cache = cache_vlm()

    # 3. assemble the 3-field FL2VA prompt
    text = assemble(cache)
    for v in fullrun.validate_prompt(text):
        print("  PROMPT VIOLATION:", v)
    (RUN / "s03-c01_vlm.txt").write_text(text, encoding="utf-8")
    print("\n===== T0018 VLM-ASSEMBLED PROMPT =====")
    print(text)
    print("====== end (" + str(len(text.split())) + " words) ======\n")

    if args.dry_run:
        print("dry-run: prompt written, no GPU. Re-run with --queue to upload+POST.")
        return

    if args.queue:
        # 4. reuse T0003's exact graph; swap node 138 + output prefix
        g = json.loads(SRC_GRAPH.read_text(encoding="utf-8"))
        g["138"]["inputs"]["value"] = text
        g["92"]["inputs"]["filename_prefix"] = "video/s03-c01_T0018_t01"
        # keep T0003's seed/length/steps/weight verbatim (the single variable is 138)
        (RUN / "s03-c01_vlm.json").write_text(json.dumps(g, indent=2), encoding="utf-8")
        # side-by-side reference: copy T0003's own prompt+graph into this run for eyeball diff
        shutil.copy(SRC_TXT, RUN / "ref_T0003_s03-c01.txt")
        shutil.copy(SRC_GRAPH, RUN / "ref_T0003_s03-c01.json")

        # 5. upload the two stills to the 5090 (must exist in that box's input/)
        for dst in (first_dst, last_dst):
            fullrun.COMFY = COMFY_5090
            name = fullrun.upload(dst)
            print("uploaded ->", name)

        # 6. POST to 5090
        fullrun.COMFY = COMFY_5090
        out = fullrun.api("/prompt", {"prompt": g})
        pid = out.get("prompt_id")
        print("queued prompt_id:", pid, "errors:", out.get("node_errors"))
        (RUN / "queued.json").write_text(json.dumps(
            {"prompt_id": pid, "queued_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
             "comfy": COMFY_5090, "weight": g["127"]["inputs"]["unet_name"],
             "seed": g["129"]["inputs"]["noise_seed"],
             "still_first": "s03-c01_first.jpg", "still_last": "s03-c01_last.jpg",
             "reference_t0003_prefix": "video/s03-c01_T0003_t01",
             "t0018_prefix": "video/s03-c01_T0018_t01"}, indent=2), encoding="utf-8")
        return


def collect(prompt_id):
    fullrun.COMFY = COMFY_5090
    h = fullrun.api("/history/" + prompt_id)
    rec = h.get(prompt_id, {})
    print("status:", rec.get("status_str") or rec.get("status"))
    outs = rec.get("outputs", {})
    for nid, o in outs.items():
        for v in o.get("videos", []):
            fn = v.get("filename")
            sub = v.get("subfolder", "")
            print("output video:", fn, "subfolder:", sub)
            import urllib.parse
            url = "%s/view?filename=%s&subfolder=%s&type=output" % (
                COMFY_5090, urllib.parse.quote(fn), urllib.parse.quote(sub))
            dest = RUN / "output" / Path(fn).name
            os.makedirs(dest.parent, exist_ok=True)
            subprocess.run(["curl", "-4", "-s", "-o", str(dest), url], check=True)
            print("pulled ->", dest, dest.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
