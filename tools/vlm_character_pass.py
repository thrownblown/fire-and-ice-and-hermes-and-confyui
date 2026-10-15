#!/usr/bin/env python3
"""Multi-lens VLM character pass — runner.

Serial per-(image, lens) calls against LM Studio vision with a narrow lens
prompt (core/vlm_charpass.py), cached and ledgered:

    library/char/vlm-cache/<CHAR>/<lens>/<image>.json   per-call cache
    manifests/vlm_charpass.jsonl                        append-only ledger

Resume-safe: a cached row (same mtime/size/model) is never re-queried.
Retry ladder on HTTP 400/429/5xx/timeouts: 3 attempts, temp 0.0->0.5,
max_tokens 600->900, 3 s between.

    python tools/vlm_character_pass.py --char TUTOR --lens hair --limit 1
    python tools/vlm_character_pass.py --char all --dry-run

Exit 0 = all items ok (or cached); exit 2 = any item failed after retries
or produced an unnormalizable answer.
"""
import argparse
import base64
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.vlm_charpass import LENSES, build_messages, normalize  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "http://127.0.0.1:1234/v1/chat/completions"
DEFAULT_MODEL = "qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s"
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")
RETRY_LADDER = [(0.0, 600), (0.25, 750), (0.5, 900)]  # (temperature, max_tokens)
RETRY_SLEEP = 3.0
TIMEOUT = 300


class VLMHttpError(Exception):
    """HTTP-level failure from the transport (status may be None for network errors)."""

    def __init__(self, status, body=""):
        super().__init__(f"HTTP {status}: {body[:200]}")
        self.status = status
        self.body = body


def encode_image(path, max_side):
    """JPEG downscale to max_side long edge, base64 (pattern from tools/vlm_traits.py)."""
    im = Image.open(path)
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    if max(im.size) > max_side:
        r = max_side / max(im.size)
        im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def http_transport(messages, *, model, temperature, max_tokens, timeout=TIMEOUT, seed=None):
    """Default transport: POST to LM Studio, return content text, raise VLMHttpError."""
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }
    if seed is not None:
        payload["seed"] = seed
    req = urllib.request.Request(API, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            out = json.load(r)
    except urllib.error.HTTPError as e:
        raise VLMHttpError(e.code, e.read().decode("utf-8", "replace")) from e
    except (urllib.error.URLError, OSError) as e:
        raise VLMHttpError(None, str(e)) from e
    return out["choices"][0]["message"]["content"].strip()


def _cache_path(root, char, lens, img_name):
    return os.path.join(root, "library", "char", "vlm-cache", char, lens, img_name + ".json")


def _ledger_path(root):
    return os.path.join(root, "manifests", "vlm_charpass.jsonl")


def _cache_lookup(cache_file, st, model):
    """Return cached row dict when key (mtime, size, model) matches, else None."""
    if not os.path.exists(cache_file):
        return None
    try:
        with open(cache_file, encoding="utf-8") as f:
            c = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    if c.get("mtime") == st.st_mtime and c.get("size") == st.st_size and c.get("model") == model:
        return c
    return None


def _write_cache(cache_file, char, lens, img_name, model, st, text, js):
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump({"char": char, "lens": lens, "file": img_name, "model": model,
                   "mtime": st.st_mtime, "size": st.st_size, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "text": text, "json": js}, f, indent=1, ensure_ascii=False)


def _append_ledger(root, row, ledger_path=None):
    p = ledger_path or _ledger_path(root)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _ledger_row(char, lens, img_rel, model, ok, attempts, text, js):
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "char": char, "lens": lens, "image": img_rel, "model": model,
            "ok": ok, "attempts": attempts, "text": text, "json": js}


def _expand_chars(root, requested):
    """Resolve --char values ('all' -> sorted corpus dirs); return (chars, missing)."""
    base = os.path.join(root, "refs", "characters")
    if "all" in requested:
        if not os.path.isdir(base):
            return [], ["all"]
        chars = sorted(d for d in os.listdir(base)
                       if os.path.isdir(os.path.join(base, d))
                       and any(fn.lower().endswith(IMG_EXT) for fn in os.listdir(os.path.join(base, d))))
        return chars, []
    missing = [c for c in requested if not os.path.isdir(os.path.join(base, c))]
    return [c for c in requested if c not in missing], missing


def _images_for(root, char, limit):
    cdir = os.path.join(root, "refs", "characters", char)
    imgs = sorted(fn for fn in os.listdir(cdir) if fn.lower().endswith(IMG_EXT))
    return imgs[:limit] if limit else imgs


def _process_item(root, char, lens, img_name, args, transport, sleep, ladder):
    """Run one (image, lens) item. Returns 'cached' | 'ok' | 'fail'."""
    img_path = os.path.join(root, "refs", "characters", char, img_name)
    img_rel = os.path.join("refs", "characters", char, img_name).replace(os.sep, "/")
    st = os.stat(img_path)
    cache_file = _cache_path(root, char, lens, img_name)

    hit = None
    if not args.no_cache:
        hit = _cache_lookup(cache_file, st, args.model)
    if hit is not None:
        print(f"[cache] {char}/{lens}/{img_name}")
        return "cached"

    b64 = encode_image(img_path, args.max_side)
    msgs = build_messages(lens, b64)

    text, js, attempts, ok = None, None, 0, False
    for i, (temp, max_tok) in enumerate(ladder):
        if i:
            sleep(RETRY_SLEEP)
        attempts += 1
        try:
            t0 = time.time()
            text = transport(msgs, model=args.model, temperature=temp,
                             max_tokens=max_tok, timeout=TIMEOUT, seed=args.seed)
        except (VLMHttpError, TimeoutError, OSError) as e:
            print(f"[retry {attempts}/{len(ladder)}] {char}/{lens}/{img_name}: {e}")
            continue
        dt = time.time() - t0
        js = normalize(lens, text)
        ok = js is not None
        print(f"[vlm {dt:.0f}s] {char}/{lens}/{img_name} ok={ok} attempts={attempts}")
        break

    if ok:
        _write_cache(cache_file, char, lens, img_name, args.model, st, text, js)
    row = _ledger_row(char, lens, img_rel, args.model, ok, attempts, text, js)
    if args.seed is not None:
        row["seed"] = args.seed
    _append_ledger(root, row, ledger_path=args.ledger_out)
    return "ok" if ok else "fail"


def _build_ladder(temperature):
    """When --temperature is set, hold that temp on every rung (keep the max_tokens ramp)."""
    if temperature is None:
        return RETRY_LADDER
    return [(temperature, toks) for _, toks in RETRY_LADDER]


def run_pass(argv, transport=None, sleep=time.sleep):
    """Main entry (testable): parse argv, run the pass, return exit code."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--char", action="append", required=True,
                    help="character dir name(s) under refs/characters/, or 'all'")
    ap.add_argument("--lens", action="append", default=None,
                    help="lens name(s), default all 7")
    ap.add_argument("--limit", type=int, default=None, help="max images per character")
    ap.add_argument("--max-side", type=int, default=1024)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--seed", type=int, default=None, help="seed forwarded to the model")
    ap.add_argument("--temperature", type=float, default=None,
                    help="fixed temperature for every attempt (default: retry ladder 0.0->0.5)")
    ap.add_argument("--no-cache", action="store_true",
                    help="skip cache read AND write (forces a genuine re-query)")
    ap.add_argument("--ledger-out", default=None,
                    help="write ledger rows here instead of manifests/vlm_charpass.jsonl")
    ap.add_argument("--dry-run", action="store_true",
                    help="list (image, lens) work items + cache hits; no calls, no writes")
    ap.add_argument("--root", default=ROOT, help="repo root (default: this repo)")
    args = ap.parse_args(argv)
    root = args.root

    if transport is None:
        transport = http_transport

    if args.lens and "all" in args.lens:
        lenses = list(LENSES)
    else:
        lenses = args.lens if args.lens else list(LENSES)
    bad_lens = [l for l in lenses if l not in LENSES]
    if bad_lens:
        print(f"unknown lens: {', '.join(bad_lens)} (have: {', '.join(LENSES)})", file=sys.stderr)
        return 2

    chars, missing = _expand_chars(root, args.char)
    if missing:
        for m in missing:
            print(f"no such character dir: refs/characters/{m}", file=sys.stderr)
        return 2
    if not chars:
        print("no characters selected", file=sys.stderr)
        return 2

    ladder = _build_ladder(args.temperature)
    counts = {"ok": 0, "fail": 0, "cached": 0}
    for char in chars:
        for img_name in _images_for(root, char, args.limit):
            img_path = os.path.join(root, "refs", "characters", char, img_name)
            for lens in lenses:
                if args.dry_run:
                    st = os.stat(img_path)
                    hit = None if args.no_cache else _cache_lookup(
                        _cache_path(root, char, lens, img_name), st, args.model)
                    state = "CACHED" if hit else "todo"
                    print(f"[dry-run {state}] {char} {img_name} {lens}")
                    counts["cached" if hit else "ok"] += 1
                    continue
                counts[_process_item(root, char, lens, img_name, args, transport, sleep,
                                     ladder)] += 1

    if args.dry_run:
        print(f"dry run: {counts['ok']} todo, {counts['cached']} cached")
        return 0
    print(f"done: {counts['ok']} ok, {counts['cached']} cached, {counts['fail']} failed")
    return 2 if counts["fail"] else 0


def main():
    sys.exit(run_pass(sys.argv[1:]))


if __name__ == "__main__":
    main()
