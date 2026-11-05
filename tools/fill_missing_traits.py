#!/usr/bin/env python
"""Fill a missing character canon (`traits.txt`) from SOURCE FILM STILLS, end to end.

For each character with no non-empty `refs/characters/<NAME>/traits.txt`:

  1. tier its reference dir (`ref_tiers.json`): film frames are `canonical`, our own generations
     (ComfyUI_*, fni_*, MiniMax_H3_*, qwedit_*, the SHEET) are `inspiration` and are excluded from
     the consensus — deriving canon from our own renders is circular.
  2. if it has fewer than `--min-frames` canonical film frames, source more from `stills/full/`
     using the shots the character actually appears in (`fullrun/chunks.jsonl` speakers +
     stamped_names → shot_nums).
  3. run `tools/vlm_traits.py --char <NAME>` (per-image literal reads + a consensus synthesis,
     cached, local qwen3-vl-8b via LM Studio).
  4. draft ONE dense house-style trait line from that synthesis (one extra VLM call) and write
     `traits.txt` with a provenance trail. **A non-empty traits.txt is never overwritten** —
     the four characters that already have canon stay untouched unless `--force`.

    .venv/Scripts/python.exe tools/fill_missing_traits.py                     # all 9 missing, report+write
    .venv/Scripts/python.exe tools/fill_missing_traits.py --chars TARO --dry-run
    .venv/Scripts/python.exe tools/fill_missing_traits.py --chars NEKRON --force

Ledger: `manifests/traits_fill.jsonl` (one row per character: frames used, tiers, model, wrote/skip).
Drafts are NOT canon — every written file says so on its provenance line, because the film is the
source of *appearance*, not of the remake's design decisions.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHARS = ROOT / "refs" / "characters"
STILLS = ROOT / "stills" / "full"
CHUNKS = ROOT / "fullrun" / "chunks.jsonl"
LEDGER = ROOT / "manifests" / "traits_fill.jsonl"
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
API = "http://127.0.0.1:1234/v1/chat/completions"
MODEL = "qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s"

# the 9 characters the audio-led batch used that have no canon file
MISSING = ["NEKRON", "JAROL", "TARO", "ROLIEL", "JULIANA", "ENVOY", "SUBHUMAN CAPTAIN", "SUBHUMAN", "LARN"]

IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")
INSP_PREFIX = ("comfyui", "fni_", "minimax_h3", "qwedit")
INSP_TOKEN = ("_temp", "_sheet_", "_r0", "_r1")

DRAFT_PROMPT = (
    "Below is a consensus trait sheet derived from reference stills of ONE character in a 1983 "
    "animated film, plus the per-image notes it was built from.\n\n"
    "Write the character's traits as ONE dense paragraph in this house style: physical appearance "
    "first (sex/age impression, build, skin, hair, eyes, face), then costume (each garment with its "
    "COLOUR and material), then ornaments and distinguishing marks. Colours must be the ones the "
    "images actually show — never invent one, and if the images disagree on something, say the "
    "majority reading and name the exception briefly.\n"
    "No name, no personality, no story, no speculation. Under 90 words. Output ONLY the paragraph.\n\n"
    "== CONSENSUS ==\n{consensus}"
)


def classify(name: str, fn: str) -> str:
    low = fn.lower()
    # film frames: shots extracted from the source, curated identity stills, contact sheets, and the
    # film_* frames this script sources itself
    if low.startswith(("shot_", "id_", "film_")) or "film_frames" in low:
        return "canonical"
    # everything else is ours (ComfyUI_*, fni_*, MiniMax_H3_*, qwedit_*, <NAME>_sheet_*, <NAME>_r0*,
    # *.webp of unknown origin) — never canonical, because deriving canon from our own generations is
    # circular (the sheet would vote for its own costume — exactly the drift being audited)
    return "inspiration"


def write_tiers(cdir: Path, name: str) -> tuple[int, int]:
    imgs = sorted(p.name for p in cdir.iterdir() if p.name.lower().endswith(IMG_EXT))
    canon = [f for f in imgs if classify(name, f) == "canonical"]
    insp = [f for f in imgs if f not in canon]
    tiers = {"lineage": (f"tiered by tools/fill_missing_traits.py: canonical = frames of the 1983 source "
                         f"film ({len(canon)}), inspiration = our own generations, excluded from the "
                         f"consensus (circular otherwise)."),
             "refs": {}}
    for f in canon:
        tiers["refs"][f] = {"tier": "canonical"}
    for f in insp:
        tiers["refs"][f] = {"tier": "inspiration"}
    (cdir / "ref_tiers.json").write_text(json.dumps(tiers, indent=1, ensure_ascii=False), encoding="utf-8")
    return len(canon), len(insp)


def shots_for(name: str) -> list[str]:
    """Shots this character appears in, per the render ledger (speakers + stamped_names)."""
    want = name.upper()
    shots: list[str] = []
    if not CHUNKS.exists():
        return shots
    for line in CHUNKS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        names = [str(n).upper() for n in (r.get("speakers") or []) + (r.get("stamped_names") or [])]
        if any(n == want or n.startswith(want + " ") or n.startswith(want + "S") for n in names):
            shots += [str(s) for s in (r.get("shot_nums") or [])]
    return sorted(set(shots), key=lambda s: int(s) if s.isdigit() else 0)


def source_film_frames(cdir: Path, name: str, need: int) -> int:
    """Copy up to `need` frames of this character's own shots out of stills/full/.

    Sampled EVENLY across the shot list, not from the start: the first shots of a character are
    usually one scene and one lighting/moment, which would give a lopsided consensus.
    """
    shots = [s for s in shots_for(name) if list(STILLS.glob(f"shot_{s}_f*.jpg"))]
    if not shots:
        return 0
    if len(shots) > need:
        step = len(shots) / need
        shots = [shots[int(i * step)] for i in range(need)]
    got = 0
    for shot in shots:
        cands = sorted(STILLS.glob(f"shot_{shot}_f*.jpg"))
        pick = cands[len(cands) // 2]           # the median frame of the shot
        dst = cdir / f"film_shot_{shot}_{pick.name.split('_f')[-1]}"
        if not dst.exists():
            shutil.copy2(pick, dst)
        got += 1
        if got >= need:
            break
    return got


def vlm(prompt: str, max_tokens: int = 400, timeout: int = 300) -> str:
    import urllib.request
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                       "max_tokens": max_tokens, "temperature": 0.2, "stream": False}).encode()
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()


def read_cache(cdir: Path, fn: str) -> str:
    p = cdir / "vlm" / (fn + ".json")
    if not p.exists():
        return ""
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("text", "")
    except Exception:
        return ""


SEX_RE = (("female", re.compile(r"\b(female|woman|girl|she|her|mother|queen)\b", re.I)),
          ("male", re.compile(r"\b(male|man|boy|he|his|father|king|elderly male)\b", re.I)))
COLOURS = ("black", "white", "blond", "blonde", "red", "crimson", "dark", "brown", "gray",
           "grey", "silver", "golden", "auburn", "purple", "blue")


def signals(text: str) -> dict:
    """Cheap, transparent signals from one cached read: sex + hair colour + skin tone."""
    out: dict[str, str | None] = {"sex": None, "hair": None, "skin": None}
    for label, rx in SEX_RE:
        if rx.search(text):
            out["sex"] = label
            break
    hm = re.search(r"hair[^.]{0,60}", text, re.I) or re.search(r"[^.]{0,60}hair", text, re.I)
    if hm:
        for c in COLOURS:
            if re.search(rf"\b{c}", hm.group(0), re.I):
                out["hair"] = "blond" if c in ("blonde",) else c
                break
    sm = re.search(r"skin\s+(?:is\s+|tone\s+|appears\s+)?([a-z]+)", text, re.I)
    if sm:
        out["skin"] = sm.group(1).lower()
    return out


def coherence_filter(cdir: Path, name: str) -> tuple[list[str], list[tuple[str, dict, str]]]:
    """Demote canonical frames whose read disagrees with the character's `id_*` anchor.

    The frames are sourced via `fullrun/chunks.jsonl` stamped_names/speakers, and that ledger is
    known to over-attribute (a stamp can name a character who is not in the shot). Measured
    2026-11-04: NEKRON's sourced set mixed pale white-haired figures with a dark-haired woman, and
    TARO's included Larn — which put a wrong "female"/"blonde" signal into the consensus. So every
    canonical frame's cached read is checked against the ONE curated identity still (`id_<NAME>.*`)
    on sex and hair colour; disagreers are demoted to `inspiration` (excluded) and reported, never
    silently dropped.

    Returns (kept_frames, [(frame, signals, reason), ...]).
    """
    tiers_p = cdir / "ref_tiers.json"
    tiers = json.loads(tiers_p.read_text(encoding="utf-8")) if tiers_p.exists() else {"refs": {}}
    refs = tiers.get("refs", {})
    anchor_fn = next((f for f in refs if f.lower().startswith("id_")), None)
    anchor = signals(read_cache(cdir, anchor_fn)) if anchor_fn else {}
    if not anchor_fn or not any(v for v in anchor.values()):
        print(f"  {name}: no usable id_* anchor read — coherence filter skipped", flush=True)
        return [], []

    kept, dropped = [], []
    for fn in list(refs):
        if refs[fn].get("tier") != "canonical" or fn == anchor_fn:
            continue
        s = signals(read_cache(cdir, fn))
        why = []
        if anchor["sex"] and s["sex"] and s["sex"] != anchor["sex"]:
            why.append(f"sex {s['sex']} vs anchor {anchor['sex']}")
        if anchor["hair"] and s["hair"] and s["hair"] != anchor["hair"]:
            why.append(f"hair {s['hair']} vs anchor {anchor['hair']}")
        if why:
            refs[fn]["tier"] = "inspiration"
            refs[fn]["demoted_by"] = "coherence_filter vs " + anchor_fn + ": " + "; ".join(why)
            dropped.append((fn, s, "; ".join(why)))
        else:
            kept.append(fn)
    if dropped:
        tiers["lineage"] = (str(tiers.get("lineage") or "") +
                            f" | coherence-filtered against {anchor_fn}: {len(dropped)} frame(s) demoted")
        tiers_p.write_text(json.dumps(tiers, indent=1, ensure_ascii=False), encoding="utf-8")
    return kept, dropped


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chars", default=",".join(MISSING))
    ap.add_argument("--min-frames", type=int, default=6, help="top up canonical film frames to this many")
    ap.add_argument("--max-source", type=int, default=8, help="max frames to copy from stills/full/")
    ap.add_argument("--force", action="store_true", help="overwrite a NON-EMPTY traits.txt")
    ap.add_argument("--no-filter", action="store_true",
                    help="skip the id_*-anchored coherence filter (NOT recommended: the sourced "
                         "frames come from an over-attributing ledger)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = []
    for name in [c.strip() for c in args.chars.split(",") if c.strip()]:
        cdir = CHARS / name
        row: dict = {"char": name, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
        if not cdir.is_dir():
            print(f"{name}: no such dir, skipped")
            continue
        tpath = cdir / "traits.txt"
        existing = tpath.read_text(encoding="utf-8").strip() if tpath.exists() else ""
        if existing and not args.force:
            print(f"{name}: traits.txt already has canon ({len(existing)} chars) — SKIP (use --force)")
            row.update(action="skip-existing")
            rows.append(row)
            continue

        n_canon, n_insp = write_tiers(cdir, name)
        row.update(canonical_frames=n_canon, inspiration_refs=n_insp)
        sourced = 0
        if n_canon < args.min_frames:
            sourced = 0 if args.dry_run else source_film_frames(cdir, name, min(args.max_source,
                                                                             args.min_frames - n_canon))
            if sourced:
                n_canon, n_insp = write_tiers(cdir, name)     # re-tier with the new frames
                row.update(canonical_frames=n_canon, sourced_from_stills=sourced)
        print(f"{name}: canonical film frames {n_canon} (+{sourced} sourced), inspiration {n_insp}")
        if args.dry_run:
            row.update(action="dry-run")
            rows.append(row)
            continue
        if n_canon == 0:
            print(f"  no film frames available — cannot derive canon, skipped")
            row.update(action="skip-no-frames")
            rows.append(row)
            continue

        # 1) per-image reads + consensus (existing, tested tool)
        p = subprocess.run([PY, "tools/vlm_traits.py", "--char", name], cwd=str(ROOT),
                           capture_output=True, text=True, timeout=3600)
        if p.returncode != 0:
            print(f"  vlm_traits failed rc={p.returncode}: {p.stderr[-200:]}")
            row.update(action="error-vlm-traits")
            rows.append(row)
            continue

        # 1b) coherence filter: the frames came from the stamped-names ledger, which over-attributes.
        # Drop frames whose read contradicts the character's curated id_* still, then re-synthesize
        # from the survivors only (cache-only, no new per-image calls).
        if not args.no_filter:
            kept, dropped = coherence_filter(cdir, name)
            if dropped:
                print(f"  coherence filter: {len(kept)} kept, {len(dropped)} demoted "
                      f"(wrong-character frames):")
                for fn, s, why in dropped:
                    print(f"    - {fn}: {why}")
                row.update(coherence_demoted=[f for f, _, _ in dropped])
                subprocess.run([PY, "tools/vlm_traits.py", "--char", name, "--synth-only"],
                               cwd=str(ROOT), capture_output=True, text=True, timeout=1800)

        md = cdir / "vlm" / "traits-vlm.md"
        if not md.exists():
            row.update(action="error-no-synthesis")
            rows.append(row)
            continue
        consensus = " ".join(md.read_text(encoding="utf-8").split())
        consensus = consensus[consensus.find("## VLM synthesis"):][:4000] or consensus[:4000]

        # 2) one dense house-style line
        try:
            line = " ".join(vlm(DRAFT_PROMPT.format(consensus=consensus), max_tokens=500).split())
        except Exception as e:  # noqa: BLE001
            print(f"  draft call failed: {e}")
            row.update(action="error-draft")
            rows.append(row)
            continue
        line = re.sub(r"^(traits|paragraph)\s*:\s*", "", line, flags=re.I)
        if len(line) < 40:
            row.update(action="error-draft-too-short", draft=line)
            rows.append(row)
            continue

        tpath.write_text(
            f"{line}\n"
            f"(provenance: derived from {n_canon} source-film frames in refs/characters/{name}/ "
            f"(film_* / shot_* / id_*) by {MODEL} via LM Studio on {time.strftime('%Y-%m-%d')}; "
            f"per-frame reads + disagreements in refs/characters/{name}/vlm/traits-vlm.md; our own "
            f"generations and the character sheet were tiered 'inspiration' and excluded (circular). "
            f"FILM-DERIVED DRAFT — not yet ruled by Alex.)\n", encoding="utf-8")
        print(f"  wrote traits.txt ({len(line)} chars): {line[:150]}")
        row.update(action="wrote", draft=line, frames_used=n_canon)
        rows.append(row)

    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("ledger:", LEDGER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
