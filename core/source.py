# -*- coding: utf-8 -*-
"""Where the source master is, and what this repo is allowed to say about it.

The master is the user's own rip of a commercial film, and this repository is public. Naming a
specific release, or publishing its digest, ties the project to that particular copy — not the
project's business and not something to publish. So:

  * tracked artifacts record a NEUTRAL name (`<source-master>`), never the real filename;
  * the real filename and sha256 live in `docs/source-master.local.json`, which is gitignored;
  * scripts resolve the master from `$FNI_MASTER`, else from that local record, and fail loudly
    if neither exists.

The loud failure is the point. Four scripts used to hardcode one release's filename as the master
path, which is how a pirated release name ended up in a public repo's README, manifests, master.json
and archived logs — and would have come straight back on the next `cut_detect.py` run.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / "docs" / "source-master.local.json"
NEUTRAL = "<source-master>"
SLUG = "fire_and_ice_1983"          # stable, non-identifying id used in master.json


def _local() -> dict:
    if LOCAL.exists():
        try:
            return json.loads(LOCAL.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"source: {LOCAL} is not valid JSON ({exc})") from exc
    return {}


def master_path() -> Path:
    """The source master: $FNI_MASTER wins, else the local record, else a clear failure."""
    env = os.environ.get("FNI_MASTER")
    if env:
        p = Path(env)
    else:
        name = _local().get("file")
        if not name:
            raise SystemExit(
                "source: no master configured. Set $FNI_MASTER, or write "
                '{"file": "<your rip>.mp4"} to docs/source-master.local.json (gitignored) — '
                "this repo deliberately does not hardcode a source filename.")
        p = Path(name)
        if not p.is_absolute():
            p = ROOT / p
    if not p.exists():
        raise SystemExit(f"source: master not found at {p}")
    return p


def record(path: Path, digest: str = "", **extra) -> str:
    """Record the real name/digest in the gitignored local file; return the neutral token."""
    rec = _local()
    rec["file"] = Path(path).name
    if digest:
        rec["sha256"] = digest
    rec.update(extra)
    LOCAL.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    return NEUTRAL
