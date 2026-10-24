# -*- coding: utf-8 -*-
"""T0019 — S03 FL2VA VLM-prompt sweep (s03-c02..c05), each vs its T0003 sibling.

Same method as T0018 (VLM describes the actual first/last frames; deterministic
assembler writes the FL2VA middle with ROSTER strings + verbatim dialogue +
deferred arrival). Reuses each T0003 chunk's exact graph (same bookend stills,
same seed, same weight, same length) — the only variable is node 138.

    .venv/Scripts/python.exe runs/build_t0019.py --dry-run
    .venv/Scripts/python.exe runs/build_t0019.py --queue [--chunk s03-c02]
    .venv/Scripts/python.exe runs/build_t0019.py --collect <prompt_id>
"""
import sys, os, re, json, base64, time, shutil, subprocess, csv, argparse, urllib.request
from pathlib import Path

sys.path.insert(0, r"E:/FNI/pipeline")
sys.path.insert(0, r"E:/FNI")
import fullrun  # noqa: E402

ROOT = Path(r"E:/FNI")
T0003 = ROOT / "runs" / "T0003_s03_fl2va-srcfflf"
RUN = ROOT / "runs" / "T0019_s03_vlm-prompt-sweep"

COMFY = os.environ.get("FNI_COMFY", "http://<TOMBSTONE_TS_IP>:8188")
LM = os.environ.get("FNI_LM", "http://127.0.0.1:1234/v1/chat/completions")
VLM = os.environ.get("FNI_VLM", "qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s")

CHUNKS = ["s03-c02", "s03-c03", "s03-c04", "s03-c05"]
# source shots per chunk, from the T0003 manifest (the graphs load renamed
# copies <chunk>_first.jpg / _last.jpg, byte-identical to these source stills)
MANIFEST_SHOTS = {
    "s03-c02": ["00068", "00069"],
    "s03-c03": ["00070", "00071"],
    "s03-c04": ["00072"],
    "s03-c05": ["00073", "00074"],
}
TSV = ROOT / "script" / "dialogue-timeline.tsv"
STYLE = fullrun.style_line("Ice Peak throne hall")
CAM_MOVE = [
    "The camera drifts forward in a small, slow push as the figure speaks.",
    "The camera settles and holds, a barely-perceptible outward drift as the figure comes to rest.",
]


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def lines_by_shot(shots, tsv_rows, shots_jsonl):
    """TSV dialogue lines per source shot, by midpoint (the fullrun rule)."""
    s_idx = {s["shot_id"]: s for s in shots_jsonl}
    out = {}
    num_of = {n: n for n in shots}
    for n in shots:
        s = s_idx["shot:%s" % n]
        t0, t1 = s["start_pts"] / 24000.0, s["end_pts"] / 24000.0
        got = []
        for r in tsv_rows:
            try:
                def sec(x):
                    # HH:MM:SS,mmm
                    hh, mm, rest = x.split(":")
                    ss, mmm = rest.split(",")
                    return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(mmm) / 1000.0
                mid = (sec(r["start"]) + sec(r["end"])) / 2
            except Exception:
                continue
            if t0 < mid < t1:
                got.append(r)
        out[n] = sorted(got, key=lambda r: r["start"])
    return out


def parse_template_sections(txt):
    """From a T0003 template prompt: the instruction line + the integrated
    description split into [Shot N] sections, each carrying its <d> dialogue
    lines (speaker id, on/off flag, verbatim text). The description is one
    physical line, so regex over the string, not line matching."""
    lines = [l for l in txt.splitlines() if not l.startswith("#")]
    instr = next((l for l in lines if l.startswith("How the reference pictures")), "")
    m = re.search(r"integrated_multimodal_description:\s*(.*?)\s*overall_soundscape:", txt, re.S)
    if not m:
        return instr, []
    desc = m.group(1)
    markers = [(mm.start(), int(mm.group(1))) for mm in re.finditer(r"\[Shot (\d+)\]", desc)]
    out = []
    for i, (pos, n) in enumerate(markers):
        end = markers[i + 1][0] if i + 1 < len(markers) else len(desc)
        seg = desc[pos:end].strip()
        dl = re.findall(r"\((S\d)\)\s+(says|speaks while off-screen):\s*<d>\[(\w+)\]\s*([^<]*)</d>", seg)
        out.append({"n": n, "dialogue": dl, "raw": seg})
    return instr, out


def vlm_call(path, roster_note):
    b64 = base64.b64encode(Path(path).read_bytes()).decode()
    prompt = (
        "This is one still frame from a dramatic film set in a stone throne hall. "
        "Describe exactly what is in frame, concretely, without guessing: where each "
        "visible figure is positioned in the frame, the direction each faces, what their "
        "hands hold or rest on, head and gaze, and any prop, furniture, or background "
        "element occupied. Name visible figures only with the character descriptions "
        "below. No colors, no lighting, no mood, nothing not visible. Two short "
        "sentences.\n\nCharacters: " + roster_note
    )
    body = json.dumps({
        "model": VLM,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}},
            {"type": "text", "text": prompt}]}],
        "max_tokens": 150, "temperature": 0.15,
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


def clean(s):
    s = s.replace("\n", " ").strip()
    for junk in ("First frame:", "Frame:", "Description:", "Answer:"):
        if s.lower().startswith(junk.lower()):
            s = s[len(junk):].strip()
    return s.rstrip(".")


def mmss(t):
    mm, ss = divmod(t, 60)
    return "%02d:06.3f" % (mm, ss) if False else "%02d:%06.3f" % (mm, ss)


def assemble(chunk, g, t0003_txt, vlm1, vlm2, tsv_rows, shots_jsonl):
    first_name = g["137"]["inputs"]["image"]
    last_name = g["139"]["inputs"]["image"]
    nums = MANIFEST_SHOTS[chunk]
    instr, sections = parse_template_sections(t0003_txt)
    per = lines_by_shot(nums, tsv_rows, shots_jsonl)
    # roster strings per speaker (consistent character strings)
    cast = {}
    for sec in sections:
        for sid, onoff, lang, text in sec["dialogue"]:
            pass
    parts = []
    speaker_ids = {}
    for idx, sec in enumerate(sections, 1):
        n_shot = idx
        bits = []
        if idx == 1:
            bits.append("[Shot 1] " + STYLE + ".")
            bits.append("The opening frame matches <Picture 1>: " + clean(vlm1) + ".")
        else:
            t0 = shots_jsonl[[s["shot_id"] for s in shots_jsonl].index("shot:%s" % nums[idx - 1])]
            base = [s for s in shots_jsonl if s["shot_id"] == "shot:%s" % nums[0]][0]["start_pts"] / 24000.0
            off = t0["start_pts"] / 24000.0 - base
            bits.append("[Shot %d] At %s, the camera cuts to a new angle." % (n_shot, mmss(off)))
        bits.append(CAM_MOVE[min(idx - 1, len(CAM_MOVE) - 1)])
        # dialogue for this shot, bound to the TSV line (speaker name, on/off from template)
        shot_lines = per.get(nums[idx - 1], [])
        dl = sec["dialogue"]
        for i, (sid, onoff, lang, text) in enumerate(dl):
            # bind to TSV by order/text to recover the speaker name + canonical text
            tsv_r = shot_lines[i] if i < len(shot_lines) else None
            spk = tsv_r["speaker"] if tsv_r else None
            if spk and spk not in cast:
                cast[spk] = fullrun.ROSTER.get(spk) or ("a figure")
            desc = cast.get(spk) or "the figure"
            if spk not in speaker_ids:
                speaker_ids[spk] = "(S%d)" % (len(speaker_ids) + 1)
            use_text = (tsv_r["text"] if tsv_r else text).strip()
            if onoff.startswith("speaks"):
                bits.append("%s %s speaks while off-screen: <d>[%s] %s</d>" % (desc, speaker_ids[spk], lang, use_text))
            else:
                bits.append("%s %s says: <d>[%s] %s</d>" % (desc, speaker_ids[spk], lang, use_text))
        if idx == len(sections):
            bits.append("Only in the last seconds do these movements slow and stop, and the figure "
                        "comes to rest in the pose, spacing, framing, and position the end frame "
                        "establishes: " + clean(vlm2) + ".")
        else:
            bits.append("Through the shot the figure breathes and shifts weight, hair and clothing "
                        "settling with the movement; no figure enters or leaves the frame.")
        parts.append(" ".join(bits))
    text = "\n\n".join([
        instr,
        "integrated_multimodal_description: " + " ".join(parts),
        "overall_soundscape: " + fullrun.soundscape_line({"location": "Ice Peak throne hall",
                                                          "cast": "NEKRON", "scene_title": ""}),
        "non_diegetic_music: " + fullrun.music_line("cold sinister orchestral"),
    ])
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--queue", action="store_true")
    ap.add_argument("--chunk", default="")
    ap.add_argument("--collect", default=None)
    args = ap.parse_args()

    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "input").mkdir(exist_ok=True)
    (RUN / "output").mkdir(exist_ok=True)

    if args.collect:
        collect(args.collect)
        return

    tsv_rows = list(csv.DictReader(TSV.open(encoding="utf-8"), delimiter="\t"))
    shots_jsonl = [json.loads(l) for l in (ROOT / "shots.jsonl").open(encoding="utf-8") if l.strip()]
    cache = (RUN / "vlm_frames.json")
    vcache = jload(cache) if cache.exists() else {}

    targets = [args.chunk] if args.chunk else CHUNKS
    results = {}
    for chunk in targets:
        g = jload(T0003 / (chunk + ".json"))
        t0003_txt = (T0003 / (chunk + ".txt")).read_text(encoding="utf-8")
        first_name = g["137"]["inputs"]["image"]
        last_name = g["139"]["inputs"]["image"]
        nums = MANIFEST_SHOTS[chunk]
        # the exact files T0003 queued (byte-copies of these source stills)
        first_src = T0003 / "input" / first_name
        last_src = T0003 / "input" / last_name
        for dst_n, src in ((first_name, first_src), (last_name, last_src)):
            dst = RUN / "input" / dst_n
            if not dst.exists() or dst.stat().st_size != src.stat().st_size:
                shutil.copy(src, dst)
        roster_note = "robed court figures of the Ice Peak throne (long-haired men in dark/purple robes; a pale woman in a long gown; possibly a hooded dark-skinned envoy with yellow eyes)."
        v1 = vcache.get(chunk + "_first") or vlm_call(first_src, roster_note)
        v2 = vcache.get(chunk + "_last") or vlm_call(last_src, roster_note)
        vcache.update({chunk + "_first": v1, chunk + "_last": v2})
        cache.write_text(json.dumps(vcache, indent=2), encoding="utf-8")
        text = assemble(chunk, g, t0003_txt, v1, v2, tsv_rows, shots_jsonl)
        viol = fullrun.validate_prompt(text)
        (RUN / (chunk + "_vlm.txt")).write_text(text, encoding="utf-8")
        results[chunk] = {"violations": viol, "words": len(text.split()),
                          "seed": g["129"]["inputs"]["noise_seed"],
                          "length_s": g["132"]["inputs"]["value"],
                          "first": first_name, "last": last_name}
        print("\n===== %s (" % chunk + str(results[chunk]["words"]) + " words, seed "
              + str(results[chunk]["seed"]) + ", " + str(results[chunk]["length_s"]) + "s) =====")
        for v in viol:
            print("  VIOLATION:", v)
        print(text)
    (RUN / "sweep.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    if args.dry_run:
        print("\ndry-run: prompts written, no GPU.")
        return

    if args.queue:
        for chunk in targets:
            r = results[chunk]
            g = jload(T0003 / (chunk + ".json"))
            text = (RUN / (chunk + "_vlm.txt")).read_text(encoding="utf-8")
            g["138"]["inputs"]["value"] = text
            g["92"]["inputs"]["filename_prefix"] = "video/%s_T0019_t01" % chunk
            (RUN / (chunk + "_vlm.json")).write_text(json.dumps(g, indent=2), encoding="utf-8")
            for nm in (r["first"], r["last"]):
                name = fullrun.upload(RUN / "input" / nm)
                print("uploaded", nm, "->", name)
            fullrun.COMFY = COMFY
            out = fullrun.api("/prompt", {"prompt": g})
            pid = out.get("prompt_id")
            print("queued", chunk, "prompt_id", pid, "errors", out.get("node_errors"))
            q = (RUN / "queued.json")
            queued = jload(q) if q.exists() else {}
            queued[chunk] = {"prompt_id": pid, "queued_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                             "comfy": COMFY, "prefix": "video/%s_T0019_t01" % chunk,
                             "t0003_prefix": "video/%s_T0003_t01" % chunk}
            q.write_text(json.dumps(queued, indent=2), encoding="utf-8")


def collect(prompt_id):
    fullrun.COMFY = COMFY
    h = fullrun.api("/history/" + prompt_id)
    rec = h.get(prompt_id, {})
    print("status:", rec.get("status_str") or rec.get("status"))
    import urllib.parse
    for nid, o in rec.get("outputs", {}).items():
        for okey in ("videos", "images", "animated"):
            for v in o.get(okey, []) or []:
                if isinstance(v, dict) and "filename" in v and v["filename"].lower().endswith(".mp4"):
                    fn = v["filename"]
                    url = "%s/view?filename=%s&subfolder=%s&type=%s" % (
                        COMFY, urllib.parse.quote(fn), urllib.parse.quote(v.get("subfolder", "")),
                        v.get("type", "output"))
                    dest = RUN / "output" / Path(fn).name
                    subprocess.run(["curl", "-4", "-s", "-o", str(dest), url], check=True)
                    print("pulled ->", dest, dest.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
