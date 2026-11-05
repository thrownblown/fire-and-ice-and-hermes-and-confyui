"""Krea render -> goldfish VLM verdict -> ledger. The small test loop, on purpose.

Division of labour (this is the whole point):
  * the 4090 ComfyUI runs Krea2 t2i — GPU-bound, no model swaps, CPU-side VLM work would evict it;
  * the VLM lives on goldfishbowl, so judging costs the 4090 nothing and the two never contend.

Per variant: render one still from the character's canon description, then ask the 32B to CONFIRM OR
DENY that description against the image — never "who is this", never "what film" (a VLM asked for
identity invents it; asked to check a supplied description it is far more reliable and its answer is
directly comparable). Verdict + the model's stated single fix go into a JSONL ledger, one row per
variant, so a later pass can aggregate without re-querying.

Usage:
  python tools/krea_vlm_loop.py --chars JULIANA --variants 2
  python tools/krea_vlm_loop.py --chars TEAGRA,NEKRON --variants 1 --dry
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
LEDGER = ROOT / "manifests" / "krea_vlm_loop.jsonl"
OUTDIR = ROOT / "runs" / "krea_vlm_loop"
WORKFLOW = ROOT / "library" / "char" / "sheet-runs" / "JULIANA_896723655157649.json"

GF_BASE = os.environ.get("FNI_GF", "http://goldfishbowl:8888").rstrip("/")
GF_KEY = os.environ.get("GOLDFISHBOWL_API_KEY", "")
JUDGE = os.environ.get("FNI_JUDGE_MODEL", "llama-cpp/qwen3-vl-32b-heretic_ctx128k")

SYSTEM = ("You are checking a generated character still against a written description. Judge ONLY what "
          "is visible. Never name a character, actor or film. Reply with strict JSON: "
          '{"verdict": "MATCH"|"MISMATCH", "fields": {"hair": "match"|"mismatch"|"unclear", '
          '"skin": "...", "build": "...", "clothing": "..."}, "differences": [str], '
          '"single_most_important_fix": str}')


def canon(char: str) -> str:
    """The written description to test against — canon first, the sweep desc as a fallback."""
    for p in (ROOT / "refs" / "characters" / char / "traits.txt",
              ROOT / "runs" / "subhuman-krea2" / "descs" / f"{char}.txt"):
        if p.exists() and p.read_text(encoding="utf-8").strip():
            return " ".join(p.read_text(encoding="utf-8").split())
    return ""


def render(char: str, variant: int, seed: int, prompt: str, dry: bool) -> Path | None:
    """Render one character still on the 4090 from the PROVEN Krea2 t2i graph.

    `tools/krea2_stills.py` expects a different node layout (it died with KeyError: '135' on the saved
    sheet-runs graph), so this reuses the plate workflow's own constants — same Krea2 UNet, krea2 CLIP,
    Wan VAE and retro-fantasy LoRA that already renders on this box — and only swaps the positive text.
    """
    outdir = OUTDIR / char
    outdir.mkdir(parents=True, exist_ok=True)
    prefix = f"{char.lower()}_loop_v{variant:02d}"
    if dry:
        print(f"   DRY: {prefix} <- {prompt[:80]}")
        return None

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "tools"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("glp", ROOT / "tools" / "gen_location_plates.py")
    glp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(glp)
    from core.asset_reconcile import snap

    g = json.loads(Path(glp.WF).read_text(encoding="utf-8"))
    g[glp.POS_MAIN]["inputs"]["positive"] = prompt
    if glp.POS_PRE in g:
        g[glp.POS_PRE]["inputs"]["positive"] = glp.STYLE_PRE
    g[glp.SAMPLER]["inputs"]["seed"] = seed
    for node in g.values():
        if isinstance(node, dict) and "filename_prefix" in (node.get("inputs") or {}):
            node["inputs"]["filename_prefix"] = prefix
    ch = snap(g, os.environ.get("FNI_COMFY", "http://127.0.0.1:8188"), verbose=False)

    base = os.environ.get("FNI_COMFY", "http://127.0.0.1:8188").rstrip("/")
    req = urllib.request.Request(f"{base}/prompt", data=json.dumps({"prompt": g}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        pid = json.load(urllib.request.urlopen(req, timeout=120))["prompt_id"]
    except urllib.error.HTTPError as e:
        print(f"   queue FAILED {e.code}: {e.read().decode(errors='replace')[:400]}")
        return None
    deadline = time.time() + 900
    while time.time() < deadline:
        time.sleep(3)
        # Poll tolerantly: this ComfyUI answers 404 for a prompt id that is queued but not yet in
        # /history, which is NOT a failure — treat any HTTP error on the poll as "not ready" and keep
        # waiting, and only report the URL if the whole wait times out.
        try:
            h = json.load(urllib.request.urlopen(f"{base}/history/{pid}", timeout=60))
        except urllib.error.HTTPError as e:
            if e.code >= 500:
                print(f"   poll {base}/history/{pid} -> HTTP {e.code}, still waiting")
            continue
        except Exception:  # noqa: BLE001
            continue
        rec = h.get(pid)
        if not rec:
            continue
        st = (rec.get("status") or {}).get("status_str")
        if st == "error":
            print(f"   render ERROR: {json.dumps((rec.get('status') or {}).get('messages'))[:300]}")
            return None
        for out in (rec.get("outputs") or {}).values():
            for img in (out.get("images") or []):
                fn = img.get("filename")
                if not fn or not fn.lower().endswith(".png"):
                    continue
                dest = outdir / fn
                # Use the type/subfolder the history REPORTS. Hardcoding type=output 404s for any node
                # that saves to temp (the Krea2 graph's save node does), and the 404 reads like a
                # missing file rather than a wrong parameter.
                params = {"filename": fn,
                          "type": img.get("type") or "output",
                          "subfolder": img.get("subfolder") or ""}
                url = f"{base}/view?" + urllib.parse.urlencode(params)
                try:
                    with urllib.request.urlopen(url, timeout=180) as r, dest.open("wb") as fh:
                        fh.write(r.read())
                except urllib.error.HTTPError as e:
                    print(f"   download FAILED {e.code} {url}")
                    return None
                if dest.stat().st_size:
                    if ch:
                        print(f"   (reconciled {len(ch)} asset path(s))")
                    return dest
    print("   render TIMEOUT")
    return None


def judge(img: Path, description: str) -> dict:
    b64 = base64.b64encode(img.read_bytes()).decode()
    body = {"model": JUDGE, "temperature": 0.0, "max_tokens": 900,
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": [
                             {"type": "text", "text": "Written description of this character:\n" + description},
                             {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}}]}]}
    req = urllib.request.Request(f"{GF_BASE}/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          **({"Authorization": "Bearer " + GF_KEY} if GF_KEY else {})})
    with urllib.request.urlopen(req, timeout=900) as r:
        d = json.load(r)
    if d.get("model") and d["model"] != JUDGE:
        raise RuntimeError(f"served by {d['model']}, not {JUDGE} — a 200 is not proof the id exists")
    txt = d["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", txt, re.S)
    return {"raw": txt, "json": json.loads(m.group(0)) if m else None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chars", required=True)
    ap.add_argument("--variants", type=int, default=2)
    ap.add_argument("--seed-base", type=int, default=515000000)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    chars = [c.strip().upper() for c in a.chars.split(",") if c.strip()]
    if not GF_KEY:
        print("  note: GOLDFISHBOWL_API_KEY is empty — the judge call will 401")
    print(f"judge: {JUDGE} @ {GF_BASE}   renders: Krea2 on {os.environ.get('FNI_COMFY','127.0.0.1:8188')}")

    rows = []
    for char in chars:
        desc = canon(char)
        if not desc:
            print(f"[{char}] NO desc/traits on disk — skipping (a blank comparison invites invention)")
            continue
        print(f"\n[{char}] {desc[:110]}...")
        for v in range(1, a.variants + 1):
            seed = a.seed_base + sum(map(ord, char)) * 10 + v
            img = render(char, v, seed, desc, a.dry)
            if not img:
                continue
            try:
                v2 = judge(img, desc)
            except Exception as e:  # noqa: BLE001
                print(f"   judge ERROR {type(e).__name__}: {str(e)[:160]}")
                continue
            j = v2.get("json") or {}
            print(f"   v{v} seed={seed} -> {j.get('verdict','?')}  fix: {str(j.get('single_most_important_fix',''))[:90]}")
            rows.append({"char": char, "variant": v, "seed": seed, "image": str(img.relative_to(ROOT)).replace("\\", "/"),
                         "judge": JUDGE, "verdict": j.get("verdict"), "fields": j.get("fields"),
                         "differences": j.get("differences"), "fix": j.get("single_most_important_fix"),
                         "raw": v2.get("raw")})
    if rows:
        with LEDGER.open("a", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        bad = [r for r in rows if r["verdict"] == "MISMATCH"]
        print(f"\n{len(rows)} judged, {len(bad)} mismatch -> {LEDGER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
