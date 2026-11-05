#!/usr/bin/env python
"""Build docs/reddit-threads.jsonl — the machine catalog of Reddit threads this project has used.

Why: docs/h3_reddit_threads.md is prose, hand-maintained, and misses threads that were pulled
into digests without being added to the index. This scans every docs/*.md for Reddit thread ids,
enriches them from the arctic-shift archive (title/sub/subreddit/score/date/num_comments), merges
a small curated overlay (status + which digest doc to read), and emits one JSON row per thread.

Rows are the ledger; the markdown index points at them. Re-run after any research pull:

    .venv/Scripts/python.exe tools/build_reddit_catalog.py            # writes docs/reddit-threads.jsonl
    .venv/Scripts/python.exe tools/build_reddit_catalog.py --check    # report only, no write

Needs no key: arctic-shift is public. curl -4 is used deliberately (this host's IPv6 is broken).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"
OUT = DOCS / "reddit-threads.jsonl"
INDEX = "docs/h3_reddit_threads.md"   # the prose map; entries here alone are not a digest

API = "https://arctic-shift.photon-reddit.com/api/posts/ids?ids="

# status: read = digested in a doc; todo = named/known but not pulled; blocked = pull walled
# (login-gated share link or the like); lead = mentioned as a source, not a thread we pulled.
OVERLAY = {
    "1xif258": dict(status="read", digest="docs/h3_reddit_research_2026-10-31.md",
                    takeaway="No dedicated H3 'prompt visualizer' exists; everyone runs an abliterated LLM with the official guide as system prompt — the shape of our prompt_fix stage."),
    "1xirbr2": dict(status="read", digest="docs/h3_reddit_research_2026-10-31.md",
                    takeaway="agentY (in-ComfyUI agent) + #OpenSourceHiggsfield context; flagged 'MALICIOUS' by a commenter, author attributes it to code execution — do not install unread."),
    "1xlaj6u": dict(status="read", digest="docs/h3_reddit_research_2026-11-04.md",
                    takeaway="Framing tokens are not instructions: captions are VLM scene graphs, so cover the frame with described content/action ('you can see X' does nothing). Camera motion has a fixed 20-phrase vocabulary (§4.3 of the guide we vendor)."),
    "1xl8hgc": dict(status="read", digest="docs/h3_reddit_research_2026-11-04.md",
                    takeaway="Character-swap route to identity: akatz-ai/MiniMax-H3-Character-Swap-LoRA (ref2va) + D3voz/openjutsu (H3 + SAM 3.1 tracking + Qwen3-VL 8B describer). OP's verdict: OPENjutsu is 'the actual answer'."),
    "1x8scrg": dict(status="read", digest="docs/h3_reddit_threads.md",
                    takeaway="Six-section REF2VA structure = our grammar; image order close-up face → body front → side; never name <Video N>/<Audio N>/<Subject N> in detailed_description."),
    "1x34suo": dict(status="read", digest="docs/h3_veterans_thread.md",
                    takeaway="Seed instability → restart ComfyUI; no 4-step turbo LoRA at 1.0 for ref2video; ref_image_size=max for identity."),
    "1wclxbj": dict(status="read", digest="docs/h3-refmods-thread.md",
                    takeaway="Always <Subject N>, subjects in loader order; background bleed is the failure mode; voice-in-refmod not proven."),
    "1wtc1jo": dict(status="read", digest="docs/h3_clown_anchoring_overlap.md",
                    takeaway="Audio-side counterpart of Clown Anchoring; 17n+5 overlap formula, audio and video overlaps independent."),
    "1wz3s0q": dict(status="read", digest="docs/h3_shared_threads_2026-10-12.md",
                    takeaway="SelfLift dual sampling for seamless long video, no colour shift."),
    # named in digests but never pulled (the index's unread-leads list)
    "1w43syg": dict(status="todo", digest=None, takeaway="H3 latent upscale / second pass (altoiddealer workflow ships a latent upscale pass)."),
    "1vj8nyp": dict(status="todo", digest=None, takeaway="H3 multi-speaker dialogue quality."),
    "1vkh2mi": dict(status="todo", digest=None, takeaway="H3 any-language audio."),
    "1vnis23": dict(status="todo", digest=None, takeaway="H3 prompt-structure cheat sheet."),
    "1vfnby5": dict(status="todo", digest=None, takeaway="Edited camera/sound prompt guide."),
    "1vxpbo1": dict(status="todo", digest=None, takeaway="Gibberish-audio fix."),
    "1viui81": dict(status="todo", digest=None, takeaway="Gibberish-audio fix (second thread)."),
    "1w4m8r4": dict(status="todo", takeaway="Minimax H3 news round-up, 1st Sept 2026 (77 up) — dated digest of H3 developments."),
    "1w2wcnh": dict(status="todo", takeaway="Collection of Minimax H3 workflows (149 up) — workflow corpus to mine."),
    "1w5e6pl": dict(status="todo", takeaway="Endless MiniMax H3 (with Endless LipSync) v1.0 (r/comfyui) — long-video + lipsync node chain."),
    "1wkmopn": dict(status="todo", takeaway="H3 Ultra-Flexible Director's Console / SelfLift second pass (r/comfyui) — extend the SelfLift lead we already use."),
    "1vojrzv": dict(status="todo", takeaway="qwen 3.8 writes better MiniMax prompts than 3.6 on the same system prompt (289 up, 68 comments) — direct A/B evidence for the prompt_fix rewriter arm."),
    "1x22omv": dict(status="read", digest="docs/h3_shared_threads_2026-10-12.md",
                    takeaway="NimbleCloud13 H3 field guide (settings/file reference; plain-English). Local HTML in explore/h3-field-guide/."),
    "1x1umis": dict(status="read", digest="docs/h3_shared_threads_2026-10-12.md",
                    takeaway="Delivery-reference technique: video ref for acting, pictures for appearance."),
    "1x1g4mu": dict(status="read", digest="docs/h3_shared_threads_2026-10-12.md",
                    takeaway="Turbo-LoRA roundup; Larry V4 600-step @ 8 steps is the audio-safe one."),
}

SKIP_IDS = {"1939453", "2072238435"}  # civitai model id / not a reddit thread

ID_RE = re.compile(r"reddit\.com/r/([A-Za-z0-9_]+)/comments/([a-z0-9]{6,7})")
BARE_RE = re.compile(r"(?<![A-Za-z0-9/T_])(1[a-z0-9]{5,6})(?![A-Za-z0-9])")


def scan() -> dict[str, dict]:
    """Every reddit thread id mentioned in docs/*.md, with the docs that mention it."""
    found: dict[str, dict] = {}
    for md in sorted(DOCS.glob("*.md")):
        text = md.read_text(encoding="utf-8", errors="replace")
        rel = f"docs/{md.name}"
        for sub, pid in ID_RE.findall(text):
            e = found.setdefault(pid, {"id": pid, "subreddit": sub, "mentioned_in": []})
            if sub and not e.get("subreddit"):
                e["subreddit"] = sub
            if rel not in e["mentioned_in"]:
                e["mentioned_in"].append(rel)
        for pid in BARE_RE.findall(text):
            if pid in SKIP_IDS or pid in found and found[pid]["mentioned_in"] and rel in found[pid]["mentioned_in"]:
                continue
            e = found.setdefault(pid, {"id": pid, "subreddit": None, "mentioned_in": []})
            if rel not in e["mentioned_in"]:
                e["mentioned_in"].append(rel)
    for pid in SKIP_IDS:
        found.pop(pid, None)
    return found


def fetch(ids: list[str]) -> dict[str, dict]:
    """Post metadata from arctic-shift, in chunks (it throttles bursts)."""
    out: dict[str, dict] = {}
    for i in range(0, len(ids), 20):
        chunk = ids[i:i + 20]
        url = API + ",".join(chunk)
        for attempt in range(4):
            p = subprocess.run(["curl", "-4", "-s", "--max-time", "45", url],
                               capture_output=True, text=True)
            try:
                data = json.loads(p.stdout)
            except Exception:
                data = None
            if isinstance(data, dict) and data.get("data"):
                for post in data["data"]:
                    out[post.get("id")] = post
                break
            if isinstance(data, dict) and data.get("error") is None:
                break  # genuinely unknown ids (deleted/private) — fine
            time.sleep(3 + 3 * attempt)
        else:
            print(f"  ! chunk {i//20} failed: {chunk[:3]}…", file=sys.stderr)
        time.sleep(1.5)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only, do not write")
    args = ap.parse_args()

    found = scan()
    ids = sorted(found)
    print(f"scanned {len(list(DOCS.glob('*.md')))} docs -> {len(ids)} distinct reddit thread ids")
    meta = fetch(ids)
    print(f"archive returned metadata for {len(meta)}/{len(ids)}")

    rows = []
    for pid in ids:
        e = found[pid]
        m = meta.get(pid) or {}
        ov = OVERLAY.get(pid, {})
        # Status is DERIVED from where the id shows up, not hand-listed:
        #   read    = some doc other than the index pulled it into a digest
        #   indexed = it appears only in docs/h3_reddit_threads.md (map entry with a takeaway)
        #   todo    = named as a known-useful lead that was never pulled
        digests = [d for d in e["mentioned_in"] if d != INDEX]
        if ov.get("status") == "todo":
            status = "todo"
        elif digests:
            status = "read"
        elif not m:
            status = "unknown"
        else:
            status = "indexed"
        row = {
            "id": pid,
            "subreddit": m.get("subreddit") or e.get("subreddit"),
            "title": m.get("title"),
            "url": f"https://www.reddit.com/r/{m.get('subreddit') or e.get('subreddit') or '_'}/comments/{pid}/",
            "author": m.get("author"),
            "score": m.get("score"),
            "num_comments": m.get("num_comments"),
            "created_utc": m.get("created_utc"),
            "status": status,
            "digests": digests,
            "takeaway": ov.get("takeaway"),
            "mentioned_in": e["mentioned_in"],
            "in_archive": bool(m),
        }
        rows.append(row)

    rows.sort(key=lambda r: (r["created_utc"] or 0), reverse=True)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print("status counts:", json.dumps(counts, sort_keys=True))

    if args.check:
        for r in rows:
            print(f"{r['id']} {r['status']:9s} {(r['title'] or '(no metadata)')[:80]}")
        return 0

    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        # A file-level marker the repo's pre-commit hook looks for: thread titles are quoted verbatim
        # from the sources, so the catalog legitimately carries adult-topic vocabulary. Emitting it
        # here means a regeneration never loses the marker (and never blocks a commit).
        fh.write(json.dumps({"_note": "spicy-ok: thread titles are quoted verbatim from the source "
                                      "threads", "_generator": "tools/build_reddit_catalog.py"},
                            ensure_ascii=False) + "\n")
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {OUT} — {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
