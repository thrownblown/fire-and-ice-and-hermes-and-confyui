# Narrative thruline: local model job pack

**Goal:** a clear story spine before any more prompt generation. Local models on the 4090 do the bulk reading; GhstClwd (Opus) synthesizes the results into `narrative-thruline.md`.

## Run (on the 4090, from the project folder)
```
python narrative_jobs.py                                 # default model qwen3.8-27b-obliterated, all lanes
python narrative_jobs.py --model gemma-4-26b-a4b-it-heretic --lanes A   # optional second opinion
```
Stdlib only. Skips files that already exist, so it's safe to re-run. About 50 calls total.

## Lanes
| Lane | Calls | Output | What it answers |
|---|---|---|---|
| A: Scenes | 26 | `narrative/A-scenes/Sxx.md` | what happens, who wants what, stakes, the turn, hand-off to the next scene, visual beats needed, confusions |
| B: Characters | 7 | `narrative/B-characters/NAME.md` | want vs need, arc with scene ids, relationships, gaps, logline (Larn, Teegra, Nekron, Juliana, Darkwolf, Jarol, Taro) |
| C: Silent stretches | 9 | `narrative/C-gaps/before-Sxx.md` | what must happen in the no-dialogue stretches, a hypothesized beat list (checked against footage later), continuity |
| D: Cut ending | 1 | `narrative/D-cut-ending.md` | how "Darkwolf = Nekron's father" reframes the story, foreshadowing spots, a shot list for the restored ending |

Every prompt says "use only the provided text; label inferences ASSUMPTION" so the models don't fill gaps from half-remembered versions of the film.

## Then
Zip or send the `narrative/` folder back and I'll write `narrative-thruline.md`: a one-page spine, act structure, per-scene purpose, and character arcs. That feeds the beat sheet and the `# prev / # next` lines in every H3 prompt.

## Script: `narrative_jobs.py`
Save this block as `narrative_jobs.py` in the project folder (next to `script/` and `beat-sheet.md`).

```python
#!/usr/bin/env python3
"""Narrative analysis jobs for Fire and Ice, run against local LM Studio.
Usage: python narrative_jobs.py [--model MODEL] [--lanes A,B,C,D]
Writes Markdown to narrative/. Uses only the stdlib. Safe to re-run: it skips outputs that already exist.
"""
import argparse, csv, json, os, re, sys, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
API = "http://localhost:1234/v1/chat/completions"
OUT = os.path.join(BASE, "narrative")

SYSTEM = ("You are a story editor analyzing the 1983 animated film Fire and Ice. "
          "Use ONLY the dialogue and scene notes provided. Anything you infer that is not "
          "directly supported by the text must be labeled ASSUMPTION. Be concise. Output Markdown.")

def load():
    rows = list(csv.DictReader(open(os.path.join(BASE, "script/dialogue-timeline.tsv")), delimiter="\t"))
    scenes = []
    for line in open(os.path.join(BASE, "beat-sheet.md")):
        m = re.match(r"^\| (S\d\d) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|", line)
        if m:
            scenes.append(dict(id=m[1], name=m[2].strip(), time=m[3].strip(), lines=m[4].strip(),
                               cast=m[5].strip(), loc=m[6].strip(), music=m[7].strip()))
    gaps = re.findall(r"^- (\d\d:\d\d:\d\d → \d\d:\d\d:\d\d \(\d+ min, before (S\d\d)\))", open(os.path.join(BASE, "beat-sheet.md")).read(), re.M)
    return rows, scenes, gaps

def scene_text(rows, sid):
    return "\n".join(f"{r['id']} [{r['start'][:8]}] {r['speaker']}{' (?)' if r['conf']=='LOW' else ''}: {r['text']}"
                     for r in rows if r["scene"] == sid)

def header(s):
    return f"{s['id']} — {s['name']} | {s['time']} | cast: {s['cast']} | location: {s['loc']}"

def ask(model, prompt, max_tokens=1200):
    body = json.dumps({"model": model, "temperature": 0.4, "max_tokens": max_tokens,
                       "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(API, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        txt = json.load(r)["choices"][0]["message"]["content"]
    return re.sub(r"<think>.*?</think>", "", txt, flags=re.S).strip()

def job(model, path, prompt, max_tokens=1200):
    p = os.path.join(OUT, path)
    if os.path.exists(p):
        print("skip", path); return
    os.makedirs(os.path.dirname(p), exist_ok=True)
    print("run ", path, flush=True)
    try:
        res = ask(model, prompt, max_tokens)
    except Exception as e:
        res = f"ERROR: {e}"
    open(p, "w").write(f"<!-- model: {model} -->\n{res}\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen3.8-27b-obliterated")
    ap.add_argument("--lanes", default="A,B,C,D")
    a = ap.parse_args()
    rows, scenes, gaps = load()
    lanes = set(a.lanes.split(","))
    idx = {s["id"]: i for i, s in enumerate(scenes)}

    # A: per-scene breakdown with neighbors for continuity
    if "A" in lanes:
        for i, s in enumerate(scenes):
            prev = scenes[i-1] if i else None
            nxt = scenes[i+1] if i + 1 < len(scenes) else None
            prompt = f"""SCENE: {header(s)}
PREVIOUS SCENE: {header(prev) if prev else 'none'}
{scene_text(rows, prev['id']) if prev else ''}

THIS SCENE DIALOGUE:
{scene_text(rows, s['id'])}

NEXT SCENE: {header(nxt) if nxt else 'none'}
{scene_text(rows, nxt['id']) if nxt else ''}

Answer for THIS SCENE only, under these headings:
## What happens (3-5 sentences)
## Who wants what (one line per character present)
## Stakes
## The turn (what has changed by the end)
## Hand-off (how it causes or sets up the next scene)
## Visual beats needed (3-6 short bullets a storyboard artist must show for this to read clearly)
## Confusions (anything a viewer would not understand from this scene alone)"""
            job(a.model, f"A-scenes/{s['id']}.md", prompt)

    # B: character arcs
    if "B" in lanes:
        for ch in ["LARN", "TEEGRA", "NEKRON", "JULIANA", "DARKWOLF", "JAROL", "TARO"]:
            mine = [r for r in rows if r["speaker"] == ch]
            about = [r for r in rows if ch.title() in r["text"] and r["speaker"] != ch]
            prompt = f"""CHARACTER: {ch}
LINES SPOKEN BY {ch} (with scene id):
""" + "\n".join(f"{r['scene']} {r['id']}: {r['text']}" for r in mine) + f"""

LINES ABOUT {ch} BY OTHERS:
""" + "\n".join(f"{r['scene']} {r['id']} {r['speaker']}: {r['text']}" for r in about) + """

SCENE LIST:
""" + "\n".join(header(s) for s in scenes) + """

Headings:
## Want vs need
## Arc (start state → turning points with scene ids → end state)
## Key relationships
## Gaps (where the arc jumps without explanation; which scene ids)
## One-line logline for this character"""
            job(a.model, f"B-characters/{ch}.md", prompt, 1500)

    # C: silent stretches
    if "C" in lanes:
        for gap, before in gaps:
            i = idx[before]
            prev = scenes[i-1]
            s = scenes[i]
            prompt = f"""There is a long stretch with NO dialogue: {gap}.
SCENE BEFORE: {header(prev)}
{scene_text(rows, prev['id'])}

SCENE AFTER: {header(s)}
{scene_text(rows, s['id'])}

Headings:
## What MUST happen in the silent stretch for the next scene to make sense (bullets)
## Likely action sequence (numbered beats; label every beat ASSUMPTION; these will be checked against footage)
## Continuity items to track (who is where, injuries, captives, objects)"""
            job(a.model, f"C-gaps/before-{before}.md", prompt)

    # D: cut content integration
    if "D" in lanes:
        prompt = """The released film never explains why Darkwolf hates Nekron. A cut ending reveals Darkwolf is Nekron's FATHER:
- Darkwolf appears through a trap door on the glacier, calls to Nekron.
- Nekron: "She said you'd come one day." They fight. Darkwolf plants his axe in Nekron's side, then a killing blow to the head.
- Juliana holds her dying son. Juliana: "You came back." Darkwolf: "I said I would." Juliana: "What have we done to our children?" Darkwolf: "You killed mine." Their eyes meet; Nekron screams and dies.

Existing Darkwolf and Juliana lines:
""" + "\n".join(f"{r['scene']} {r['id']} {r['speaker']}: {r['text']}" for r in rows if r['speaker'] in ('DARKWOLF', 'JULIANA')) + """

SCENE LIST:
""" + "\n".join(header(s) for s in scenes) + """

Headings:
## How the reveal reframes Darkwolf, Juliana, and Nekron
## "You killed mine": whose children? (interpretations, labeled ASSUMPTION)
## Foreshadowing opportunities (scene id + a small visual or line tweak; no rewriting existing dialogue)
## Proposed shot list for the restored ending (8-15 shots)"""
        job(a.model, "D-cut-ending.md", prompt, 2000)

    print("done. Outputs in", OUT)

if __name__ == "__main__":
    main()
```
