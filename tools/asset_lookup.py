#!/usr/bin/env python
"""CLI for the asset-library resolver.

Usage:
    python tools/asset_lookup.py --root assets --character aria --wardrobe coat_02 --prop lantern_01
    python tools/asset_lookup.py --root assets --shot shot:00023

Prints a single JSON pack to stdout (schema fni.asset/pack/v1). On any missing or
non-approved asset it prints a JSON error to stderr and exits non-zero.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from asset_library import AssetLookupError, build_pack


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default="assets",
                   help="path to the assets library (default: ./assets)")
    p.add_argument("--character", action="append", default=[],
                   help="character_id (repeatable)")
    p.add_argument("--wardrobe", action="append", default=[],
                   help="garment id or bare slug (repeatable)")
    p.add_argument("--prop", action="append", default=[],
                   help="prop id or bare slug (repeatable)")
    p.add_argument("--shot", default=None,
                   help="shot id (e.g. shot:00023); resolves all characters/wardrobe/props")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if not args.shot and not args.character and not args.wardrobe and not args.prop:
        _parser().error("nothing to look up: pass --shot or --character/--wardrobe/--prop")

    try:
        pack = build_pack(
            root=args.root,
            character_ids=args.character,
            wardrobe=args.wardrobe,
            props=args.prop,
            shot_id=args.shot,
        )
    except AssetLookupError as exc:
        err = {
            "schema": "fni.asset/pack/v1",
            "reference_images": [],
            "description_block": "",
            "validation": {"ok": False, "errors": exc.errors},
        }
        json.dump(err, sys.stderr, indent=2)
        return 1

    json.dump(pack, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())