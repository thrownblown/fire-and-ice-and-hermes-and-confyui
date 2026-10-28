# -*- coding: utf-8 -*-
"""Shared guardrails for machine-authored text that feeds renders.

Burned 2026-10-27: vlm_blocking.py wrote 487 transport-error strings
("ERR <urlopen error WinError 10061>") into manifests/blocking.json and the
render driver injected them into ~30 queued prompts. Same class as the
review-ledger rule (a transport error is not a verdict) — now generalized:
AN ERROR STRING IS NOT CONTENT, in any ledger, prompt, or manifest.

Use:
  from core.prompt_guards import looks_like_error, usable_blocking, lint_prompt
"""
from __future__ import annotations

import re

# signatures of transport/tooling failures that must never reach a ledger or prompt
_ERROR_PATTERNS = [
    r"^\s*ERR\b",
    r"urlopen error",
    r"WinError\s*\d+",
    r"Errno\s*\d+",
    r"Connection (refused|reset|aborted)",
    r"HTTPError",
    r"ReadTimeout",
    r"TimeoutExpired",
    r"Traceback \(most recent call last\)",
    r"RemoteDisconnected",
    r"NameResolutionError",
    r"Failed to establish a new connection",
    r"VLM ERROR",
]
_ERROR_RE = re.compile("|".join(_ERROR_PATTERNS), re.I)


def looks_like_error(text: str | None) -> bool:
    """True if the string is a transport/tooling failure, not real content."""
    if not text or not text.strip():
        return True  # empty is not usable content either
    return bool(_ERROR_RE.search(text))


def usable_blocking(text: str | None) -> bool:
    """A blocking entry is usable iff it is real prose: not an error string and
    long enough to actually say something (a one-word entry is a failed draft)."""
    if looks_like_error(text):
        return False
    return len(text.split()) >= 8


def lint_prompt(text: str, mode: str = "audio_only") -> list[str]:
    """Lint a finished render prompt before it is queued. Returns a list of
    problems (empty = pass). mode 'audio_only' forbids video-reference lines."""
    problems = []
    if looks_like_error(text):
        problems.append("prompt contains an error/transport string")
    if len(text) < 400:
        problems.append(f"prompt suspiciously short ({len(text)} chars)")
    if mode == "audio_only" and "<Video" in text:
        problems.append("audio-only prompt must not reference <Video N> (dead reference)")
    if mode == "ref2va" and "<Video 1>" not in text:
        problems.append("ref2va prompt is missing its <Video 1> retention lines")
    return problems
