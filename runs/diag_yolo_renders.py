# -*- coding: utf-8 -*-
"""YOLO render diagnostic (Alex: "blocking and character refs are way off — see
what done did"). For each completed audioOnly render: show goldfishbowl 32B the
intended subject sheet(s) + 3 extracted frames, ask who is present, MATCH/
MISMATCH per subject, the blocking, and everything wrong. Streams verdicts to
runs/yolo_diag/diag_results.jsonl (resumable).
"""
import base64
import json
import re
import sys
import urllib.request
from pathlib import Path

GF = "http://<GOLDFISHBOWL_TS_IP>:11434/api/generate"
ROOT = Path(r"E:/FNI")
DIAG = ROOT / "runs" / "yolo_diag"
RUN_DIR = ROOT / "runs" / "T0016_s05_technicolor-audio-only-ref2va"
OUT = DIAG / "diag_results.jsonl"


def b64(p):
    return base64.b64encode(Path(p).read_bytes()).decode()


def sheet_for(name):
    d = ROOT / "refs" / "characters" / name
    hits = sorted(d.glob(f"{name}_sheet_t*.png"))
    return hits[0] if hits else None


def vlm(prompt, images, timeout=600):
    body = json.dumps({"model": "qwen3-vl-32b-heretic:ctx128k", "prompt": prompt,
                       "images": images, "stream": False}).encode()
    req = urllib.request.Request(GF, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())["response"]


def main():
    frames = json.load(open(DIAG / "frames.json"))
    done = {json.loads(l)["chunk"] for l in OUT.read_text().splitlines() if l.strip()} if OUT.exists() else set()
    for cid, fs in frames.items():
        if cid in done:
            continue
        ptxt_path = RUN_DIR / "prompts" / f"{cid}.txt"
        ptxt = ptxt_path.read_text(encoding="utf-8") if ptxt_path.exists() else ""
        m = re.search(r"subject_definitions:\n(.*?)\n\n", ptxt, re.S)
        subj_block = m.group(1).strip() if m else "(none found)"
        subjects = re.findall(r"<Subject \d+> is ([A-Z ]+?),", subj_block)
        imgs, labels = [], []
        for n in subjects:
            sp = sheet_for(n.strip())
            if sp:
                imgs.append(b64(sp))
                labels.append(f"REF SHEET for {n.strip()}")
        for f in fs:
            imgs.append(b64(f))
            labels.append("GENERATED frame")
        prompt = (
            "You are auditing an AI video generation for a film remake.\n"
            f"The images are: {', '.join(labels)} (in that order).\n"
            f"INTENDED SUBJECTS: {subj_block}\n"
            "The last 3 images are frames from the generated video.\n"
            "Answer plainly and specifically:\n"
            "1. How many people appear in the generated frames? Describe each (build, hair, costume).\n"
            "2. Does each person MATCH their reference sheet (face, hair, costume)? Say MATCH or MISMATCH per subject and why.\n"
            "3. What are the people DOING (blocking)? What is the setting?\n"
            "4. List everything wrong vs the intent: extra people, wrong characters, wrong costume, wrong register (cartoon vs live-action), garbled anatomy."
        )
        try:
            resp = vlm(prompt, imgs)
        except Exception as e:
            resp = f"VLM ERROR: {e}"
        with OUT.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"chunk": cid, "subjects": subjects, "verdict": resp}) + "\n")
        print(f"== {cid} done ({len(resp)} chars)", flush=True)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
