# -*- coding: utf-8 -*-
"""OpenAI-compatible client for goldfishbowl (Unsloth Studio at :8888, bearer auth).

One place that knows the endpoint and the token, so no script hardcodes either
(the Ollama era ended 2026-11-01: /api/generate, /api/tags, /api/ps and :11434 are
gone — see docs/canonical-setup.md section 2).

Contract
    base URL   $FNI_GF, default http://goldfishbowl:8888
    token      $GOLDFISHBOWL_API_KEY, else parsed out of ~/.hermes/.env
    API        POST {base}/v1/chat/completions   (OpenAI shape)
               GET  {base}/v1/models             (inventory + residency)

Two rules this module enforces because they cost real debugging time:
  1. A 200 is NOT proof the model exists — an unknown id is served by whatever is
     resident, so `chat()` checks that the response's `model` field equals the id
     requested (strict_model=True by default) and raises otherwise.
  2. A thinking model with a small `max_tokens` spends the whole allowance on
     reasoning and returns an HTTP 400 whose body READS LIKE PROSE ("The model used
     its whole output allowance of N tokens on reasoning..."), which looks like a
     model failure. Default max_tokens is therefore generous (4096).
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_BASE = "http://goldfishbowl:8888"
HERMES_ENV = Path.home() / "AppData" / "Local" / "hermes" / ".env"
DEFAULT_MAX_TOKENS = 4096       # see rule 2 in the module docstring
MIN_TOKENS_FOR_THINKERS = 2048  # goldfishbowl's measured floor for the abliterated arm


class GFError(RuntimeError):
    """Transport, auth or protocol failure — never returned as if it were an answer."""


def _from_file() -> str:
    try:
        for line in HERMES_ENV.read_text(encoding="utf-8").splitlines():
            if line.startswith("GOLDFISHBOWL_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def token() -> str:
    """The .env FILE wins over the process environment, deliberately.

    Hermes loads ~/.hermes/.env into its own process environment at start-up, so a
    key rotated afterwards is still the OLD value inside every subprocess the agent
    spawns. Observed 2026-11-01: the process env held the 29-char
    ADMIN_PASSWORD.txt string while the file held the real 43-char `sk-unsloth-` key,
    which produced a confusing 401 from a script that trusted the environment.
    Read the file first and say so when they disagree.
    """
    filev = _from_file()
    envv = (os.environ.get("GOLDFISHBOWL_API_KEY") or "").strip()
    if filev and envv and filev != envv:
        print(f"[gf_client] GOLDFISHBOWL_API_KEY differs: ~/.hermes/.env has {len(filev)} chars, "
              f"the process env has {len(envv)} (stale until the agent restarts) — using the file",
              file=sys.stderr)
    return filev or envv


def base_url() -> str:
    return (os.environ.get("FNI_GF") or DEFAULT_BASE).rstrip("/")


def _request(path: str, body: dict | None = None, timeout: int = 900):
    key = token()
    if not key:
        raise GFError("no GOLDFISHBOWL_API_KEY in the environment or ~/.hermes/.env")
    url = base_url() + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url, data=data,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = (e.read() or b"").decode("utf-8", "replace")[:400]
        except Exception:
            pass
        if e.code == 401 and "Not authenticated" in detail:
            raise GFError(f"401 not authenticated — no usable bearer header ({detail})") from e
        if e.code == 401:
            raise GFError(f"401 invalid token — wrong kind of artifact or revoked key ({detail})") from e
        raise GFError(f"HTTP {e.code} from {url}: {detail}") from e
    except urllib.error.URLError as e:
        raise GFError(f"unreachable {url}: {e.reason}") from e


def models() -> list[dict]:
    """Inventory + residency: id, quant, context_length, loaded, status."""
    d = _request("/v1/models", timeout=60)
    return d.get("data", d if isinstance(d, list) else [])


def _image_part(src: str) -> dict:
    """Accept a local path OR raw base64.

    A value that LOOKS like a path but does not exist is a bug in the caller, and it is a costly
    one to diagnose: the server replies HTTP 400 `{"error":{"message":"Failed to process image.",
    "type":"invalid_request_error"}}`, which reads like a broken vision model or a broken box on the
    far side. Measured 2026-11-04: a single misplaced underscore in a filename produced exactly that
    body from an otherwise healthy goldfishbowl whose 32B was loaded and answering text fine. Fail
    loudly here instead of shipping the path as base64.
    """
    looks_like_path = (os.sep in src or "/" in src) and not src.startswith("data:")
    if os.path.exists(src):
        b64 = base64.b64encode(Path(src).read_bytes()).decode("ascii")
        ext = Path(src).suffix.lstrip(".").lower() or "jpeg"
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    elif looks_like_path:
        raise GFError(f"image path does not exist: {src!r} — refusing to send it as base64 "
                      f"(the server would answer a misleading 'Failed to process image')")
    else:
        b64, mime = src, "image/jpeg"
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}


def chat(model: str, prompt: str, *, system: str | None = None,
         images: list[str] | None = None, max_tokens: int = DEFAULT_MAX_TOKENS,
         temperature: float | None = None, timeout: int = 900,
         strict_model: bool = True) -> str:
    """One non-streaming completion; returns the assistant text.

    `images` are file paths or raw base64 strings, attached to the user turn in the
    order given (that order is what <Picture N> refers to in a prompt).
    """
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    if images:
        content: list[dict] = [{"type": "text", "text": prompt}]
        content += [_image_part(i) for i in images]
        messages.append({"role": "user", "content": content})
    else:
        messages.append({"role": "user", "content": prompt})

    body = {"model": model, "messages": messages, "max_tokens": max_tokens, "stream": False}
    if temperature is not None:
        body["temperature"] = temperature

    d = _request("/v1/chat/completions", body, timeout=timeout)
    served = d.get("model")
    if strict_model and served and served != model:
        raise GFError(
            f"asked for {model!r} but the server answered as {served!r} — an unknown id is "
            f"served by whatever is RESIDENT, so this reply is NOT from the model you asked for")
    try:
        return (d["choices"][0]["message"].get("content") or "").strip()
    except (KeyError, IndexError, TypeError) as e:
        raise GFError(f"unexpected response shape: {json.dumps(d)[:300]}") from e


def smoke(model: str) -> dict:
    """One cheap call that proves auth + that THIS id answers. Use before a run."""
    out = chat(model, "Reply with exactly: PONG", max_tokens=64, timeout=300)
    return {"model": model, "ok": "PONG" in out.upper(), "reply": out[:80]}


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "models":
        ms = models()
        print(f"{base_url()} — {len(ms)} ids (key: {'set' if token() else 'MISSING'})")
        for m in ms:
            print(f"  {m.get('id'):<52} {str(m.get('quant'))[:22]:<24} "
                  f"ctx={m.get('context_length')} loaded={m.get('loaded')}")
    elif len(sys.argv) > 2 and sys.argv[1] == "smoke":
        print(smoke(sys.argv[2]))
    else:
        print(__doc__)
        print("usage: python core/gf_client.py models | smoke <model-id>")
