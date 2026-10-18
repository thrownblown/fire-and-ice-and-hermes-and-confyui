"""Asset-library resolver: look up a shot or (character + wardrobe + props) by id and
return the exact reference images and metadata the edit stage needs.

Schema: docs/asset-schema.md (see also the copied copy beside the README).
Directory-per-asset, one ``manifest.yml`` per folder, no database.

This module is importable AND drives the ``asset_lookup.py`` CLI. It contains no
hard-coded absolute paths: every path is computed from a ``root`` argument that the
caller supplies (defaults to ``assets/`` relative to the current directory).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

import yaml

PACK_SCHEMA = "fni.asset/pack/v1"

# Canonical angle ordering for garment/prop refs. Anything not in this list (detail.*)
# sorts after the fixed set, alphabetically.
ANGLE_ORDER = ["front", "back", "side", "profile", "top"]

# Canonical group order for a character's nested canonical_refs {face, body}.
CHAR_GROUP_ORDER = ("face", "body")


class AssetLookupError(Exception):
    """Raised when the request cannot be satisfied. Carries every problem found."""

    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


@dataclass
class ResolvedRef:
    role: str          # "character" | "wardrobe" | "prop"
    asset_id: str
    angle: str
    rel: str           # path relative to the assets root
    path: str          # absolute path (computed at runtime, not hard-coded)


@dataclass
class ResolvedAsset:
    role: str
    asset_id: str
    manifest: dict = field(default_factory=dict)
    refs: list[ResolvedRef] = field(default_factory=list)


def _load_manifest(path: str, errors: list) -> Optional[dict]:
    if not os.path.isfile(path):
        errors.append(f"missing manifest: {path.replace(os.sep, '/')}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        errors.append(f"bad YAML in {path}: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"manifest is not a mapping: {path}")
        return None
    return data


def _check_approved(role: str, asset_id: str, manifest: dict, errors: list) -> None:
    status = manifest.get("status")
    if status != "approved":
        errors.append(
            f"{role} '{asset_id}' is not approved (status={status!r}); "
            "only approved assets may be referenced"
        )


def _rel(root: str, abs_path: str) -> str:
    return os.path.relpath(abs_path, root).replace(os.sep, "/")


def _resolve_ref_file(abs_path: str, root: str, role: str, asset_id: str, errors: list):
    if not os.path.isfile(abs_path):
        errors.append(f"{role} '{asset_id}' references missing file: {_rel(root, abs_path)}")
        return None
    return abs_path


# --- character ----------------------------------------------------------------

def _character_refs(manifest: dict) -> list[tuple[str, str]]:
    """Expand canonical_refs into an ordered (angle, relpath) list."""
    out: list[tuple[str, str]] = []
    cr = manifest.get("canonical_refs") or {}
    for group in CHAR_GROUP_ORDER:
        g = cr.get(group)
        if not isinstance(g, dict):
            continue
        for angle, rel in g.items():
            out.append((f"{group}.{angle}", rel))
    # any group outside the canonical set, appended in declaration order
    for group, g in cr.items():
        if group in CHAR_GROUP_ORDER or not isinstance(g, dict):
            continue
        for angle, rel in g.items():
            out.append((f"{group}.{angle}", rel))
    return out


def resolve_character(root: str, character_id: str, errors: list) -> Optional[ResolvedAsset]:
    char_dir = os.path.join(root, "characters", character_id)
    man = _load_manifest(os.path.join(char_dir, "manifest.yml"), errors)
    if man is None:
        return None
    _check_approved("character", character_id, man, errors)

    asset = ResolvedAsset("character", character_id, manifest=man)
    for angle, rel in _character_refs(man):
        abs_path = os.path.abspath(os.path.join(char_dir, rel))
        if _resolve_ref_file(abs_path, root, "character", character_id, errors):
            asset.refs.append(ResolvedRef(
                "character", character_id, angle, _rel(root, abs_path), abs_path,
            ))
    return asset


# --- wardrobe ----------------------------------------------------------------

def _ordered_angles(refs: dict) -> list[str]:
    keys = [k for k in refs if isinstance(k, str)]
    fixed = sorted([k for k in keys if k in ANGLE_ORDER], key=ANGLE_ORDER.index)
    details = sorted(k for k in keys if k.startswith("detail."))
    return fixed + details


def _resolve_garment_id(root: str, ref: str, character_ids: list, errors: list) -> Optional[str]:
    """Resolve a wardrobe reference (bare slug or full ``<char>.<slot>.<slug>``)."""
    if "." in ref:
        parts = ref.split(".")
        if len(parts) >= 3:
            return ref  # full garment id; validated against disk below
    # bare slug -> resolve within the given characters' wardrobe_ids
    if not character_ids:
        errors.append(f"wardrobe '{ref}': bare slug needs --character to resolve")
        return None
    matches = []
    for cid in character_ids:
        cman = _load_manifest(os.path.join(root, "characters", cid, "manifest.yml"), errors)
        if not cman:
            continue
        for garment_id in cman.get("wardrobe_ids", []):
            if garment_id.split(".")[-1] == ref:
                matches.append(garment_id)
    unique = list(dict.fromkeys(matches))
    if len(unique) == 1:
        return unique[0]
    if not unique:
        errors.append(f"wardrobe '{ref}': no garment with that slug on "
                      f"{', '.join(character_ids) or '(none)'}")
        return None
    errors.append(f"wardrobe '{ref}': ambiguous, matches {unique}")
    return None


def resolve_garment(root: str, garment_id: str, errors: list) -> Optional[ResolvedAsset]:
    character_id = garment_id.split(".")[0]
    gar_dir = os.path.join(root, "characters", character_id, "wardrobe", garment_id)
    man = _load_manifest(os.path.join(gar_dir, "manifest.yml"), errors)
    if man is None:
        return None
    _check_approved("wardrobe", garment_id, man, errors)

    asset = ResolvedAsset("wardrobe", garment_id, manifest=man)
    for angle in _ordered_angles(man.get("refs") or {}):
        rel = man["refs"][angle]
        abs_path = os.path.abspath(os.path.join(gar_dir, rel))
        if _resolve_ref_file(abs_path, root, "wardrobe", garment_id, errors):
            asset.refs.append(ResolvedRef(
                "wardrobe", garment_id, angle, _rel(root, abs_path), abs_path,
            ))
    return asset


# --- prop ----------------------------------------------------------------------

def _resolve_prop_id(root: str, ref: str, errors: list) -> Optional[str]:
    if "." in ref:
        return ref  # full <category>.<slug>
    # bare slug -> search all props for a unique slug match
    props_dir = os.path.join(root, "props")
    matches = []
    if os.path.isdir(props_dir):
        for name in sorted(os.listdir(props_dir)):
            man = _load_manifest(os.path.join(props_dir, name, "manifest.yml"), errors)
            if man and man.get("prop_id", name).split(".")[-1] == ref:
                matches.append(man.get("prop_id", name))
    unique = list(dict.fromkeys(matches))
    if len(unique) == 1:
        return unique[0]
    if not unique:
        errors.append(f"prop '{ref}': no prop with that slug")
        return None
    errors.append(f"prop '{ref}': ambiguous, matches {unique}")
    return None


def resolve_prop(root: str, prop_id: str, errors: list) -> Optional[ResolvedAsset]:
    prop_dir = os.path.join(root, "props", prop_id)
    man = _load_manifest(os.path.join(prop_dir, "manifest.yml"), errors)
    if man is None:
        return None
    _check_approved("prop", prop_id, man, errors)

    asset = ResolvedAsset("prop", prop_id, manifest=man)
    for angle in _ordered_angles(man.get("refs") or {}):
        rel = man["refs"][angle]
        abs_path = os.path.abspath(os.path.join(prop_dir, rel))
        if _resolve_ref_file(abs_path, root, "prop", prop_id, errors):
            asset.refs.append(ResolvedRef(
                "prop", prop_id, angle, _rel(root, abs_path), abs_path,
            ))
    return asset


# --- shots ----------------------------------------------------------------------

def _shot_manifest_path(root: str, shot_id: str) -> str:
    # Windows filenames cannot contain ':' -> store shot records with '-' for ':'.
    stem = shot_id.replace(":", "-")
    return os.path.join(root, "shots", f"{stem}.yml")


def resolve_shot(root: str, shot_id: str, errors: list) -> Optional[dict]:
    path = _shot_manifest_path(root, shot_id)
    return _load_manifest(path, errors)


# --- description block -----------------------------------------------------------

def _build_description(assets: list[ResolvedAsset], root: str) -> str:
    lines: list[str] = []
    for a in assets:
        m = a.manifest
        if a.role == "character":
            lines.append(f"Character: {m.get('name', a.asset_id)} ({a.asset_id})")
            traits = m.get("distinguishing_traits") or []
            if traits:
                lines.append("  distinguishing traits:")
                for t in traits:
                    lines.append(f"    - {t}")
            notes = _read_traits_md(root, a.asset_id)
            if notes:
                lines.append("  curator notes:")
                for n in notes:
                    lines.append(f"    {n}")
        elif a.role == "wardrobe":
            lines.append(f"Wardrobe: {m.get('name', a.asset_id)} [{a.asset_id}] "
                         f"slot={m.get('slot', '?')}")
            mat = m.get("materials") or {}
            color = mat.get("color") or {}
            rgb = color.get("primary")
            name = color.get("primary_name")
            color_txt = f"{name}" if name else ""
            if rgb:
                color_txt += f" (RGB {', '.join(str(c) for c in rgb)})"
            if color_txt.strip():
                lines.append(f"  color: {color_txt.strip()}")
            if mat.get("material"):
                lines.append(f"  material: {mat['material']}")
            if m.get("notes"):
                lines.append(f"  notes: {' '.join(m['notes'].strip().split())}")
        elif a.role == "prop":
            lines.append(f"Prop: {m.get('name', a.asset_id)} [{a.asset_id}] "
                         f"category={m.get('category', '?')}")
            scale = m.get("scale") or {}
            scale_parts = []
            if scale.get("relative_to"):
                scale_parts.append(scale["relative_to"])
            if scale.get("approx_length_cm"):
                scale_parts.append(f"~{scale['approx_length_cm']} cm")
            if scale_parts:
                lines.append(f"  scale: {'; '.join(scale_parts)}")
            if m.get("notes"):
                lines.append(f"  notes: {' '.join(m['notes'].strip().split())}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _read_traits_md(root: str, character_id: str) -> list[str]:
    path = os.path.join(root, "characters", character_id, "traits.md")
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    # skip heading + blank lines; keep substantive bullets/paragraphs
    notes = []
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("---"):
            continue
        notes.append(s.lstrip("- ").strip())
    return notes


# --- top-level pack --------------------------------------------------------------

def build_pack(
    root: str,
    character_ids: Optional[list] = None,
    wardrobe: Optional[list] = None,
    props: Optional[list] = None,
    shot_id: Optional[str] = None,
) -> dict:
    """Resolve the request and return the machine-readable pack. Raises
    AssetLookupError on any missing or non-approved asset."""
    character_ids = list(character_ids or [])
    wardrobe = list(wardrobe or [])
    props = list(props or [])
    errors: list[str] = []
    assets: list[ResolvedAsset] = []
    seen_char: dict[str, None] = {}

    # --shot mode expands into the same character/wardrobe/prop streams.
    if shot_id:
        shot = resolve_shot(root, shot_id, errors)
        if shot:
            if shot.get("status", "approved") != "approved":
                errors.append(f"shot '{shot_id}' status is {shot.get('status')!r}")
            for entry in shot.get("characters", []):
                cid = entry.get("character_id")
                if cid and cid not in character_ids:
                    character_ids.append(cid)
                for gid in entry.get("wardrobe_ids", []):
                    if gid not in wardrobe:
                        wardrobe.append(gid)
                for pid in entry.get("prop_ids", []):
                    if pid not in props:
                        props.append(pid)

    for cid in character_ids:
        if cid in seen_char:
            continue
        seen_char[cid] = None
        res = resolve_character(root, cid, errors)
        if res:
            assets.append(res)

    for wref in wardrobe:
        garment_id = _resolve_garment_id(root, wref, character_ids, errors)
        if garment_id:
            res = resolve_garment(root, garment_id, errors)
            if res:
                assets.append(res)

    for pref in props:
        prop_id = _resolve_prop_id(root, pref, errors)
        if prop_id:
            res = resolve_prop(root, prop_id, errors)
            if res:
                assets.append(res)

    if errors:
        raise AssetLookupError(errors)

    refs: list[dict] = []
    for a in assets:
        for r in a.refs:
            refs.append({
                "role": r.role,
                "asset_id": r.asset_id,
                "angle": r.angle,
                "rel": r.rel,
                "path": r.path,
                "status": "approved",
            })

    return {
        "schema": PACK_SCHEMA,
        "request": {
            "character_ids": character_ids,
            "wardrobe": wardrobe,
            "props": props,
            "shot_id": shot_id,
        },
        "reference_images": refs,
        "description_block": _build_description(assets, root),
        "validation": {"ok": True, "errors": []},
    }