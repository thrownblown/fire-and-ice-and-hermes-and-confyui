"""Multi-lens VLM character pass — pure library (no network).

Lenses, message construction, answer normalization, and deterministic
majority-vote consensus for the per-character trait pipeline.

Design: docs/plans/2026-10-13-vlm-character-pass-design.md
Runner: tools/vlm_character_pass.py   Aggregation: tools/vlm_profile_synth.py

Schema value kinds:
    "str"      a string field
    "list"     a list of strings
    "objlist"  a list of dicts (each dict free-form per the lens instruction)
"""
import json
import re

# --------------------------------------------------------------------------
# Lenses — ordered; each has a strict-JSON schema + narrow instruction text.
# --------------------------------------------------------------------------
LENSES = {
    "physique": {
        "schema": {
            "sex": "str",
            "age_range": "str",
            "build": "str",
            "height_impression": "str",
            "skin_neutral_light": "str",
        },
        "instruction": (
            "Look at the single most prominent human figure in this frame. "
            "Report their physique only: apparent sex, age range (child/teen/"
            "young adult/middle-aged/elderly/indeterminate), build (slim/"
            "lean/muscular/stocky/heavy), the height impression they give "
            "(tall/average/short/imposing), and their skin tone as it would "
            "appear under neutral white light, ignoring colored scene lighting. "
            "Return JSON with exactly these keys: "
            "sex, age_range, build, height_impression, skin_neutral_light."
        ),
    },
    "face": {
        "schema": {
            "face_shape": "str",
            "eyes": "str",
            "brows": "str",
            "nose": "str",
            "lips": "str",
            "distinguishing_features": "list",
        },
        "instruction": (
            "Look at the single most prominent human figure's FACE in this "
            "frame. Report face shape, eyes (shape/color impression/expression "
            "if visible), brows, nose, lips, and any distinguishing features "
            "(scars, marks, wrinkles, unusual proportions) as a list of short "
            "strings. Describe only what is visible; if a feature is not "
            "visible, use null for it. Return JSON with exactly these keys: "
            "face_shape, eyes, brows, nose, lips, distinguishing_features."
        ),
    },
    "hair": {
        "schema": {
            "color": "str",
            "length": "str",
            "texture": "str",
            "style": "str",
            "notes": "str",
        },
        "instruction": (
            "Look at the single most prominent human figure's HAIR in this "
            "frame. Report color (as it would appear under neutral light), "
            "length (shaved/very short/short/shoulder-length/long/very long), "
            "texture (straight/wavy/curly/coarse/fine), style (loose/tied "
            "back/braided/ponytail/messy/covered), and notes for anything else "
            "(bangs, hair accessories, wet/matted hair). Return JSON with "
            "exactly these keys: color, length, texture, style, notes."
        ),
    },
    "wardrobe": {
        "schema": {
            "garments": "objlist",
            "state_of_dress": "str",
        },
        "instruction": (
            "Look at the single most prominent human figure's CLOTHING in this "
            "frame. List each visible garment as an object with keys: item "
            "(e.g. tunic, loincloth, cloak, boots), color, material "
            "(leather/fur/cloth/metal/unknown), cut (how it fits/hangs). Also "
            "report state_of_dress (e.g. fully dressed, armored, ragged, "
            "partially clad, barefoot). Return JSON with exactly these keys: "
            "garments (list of objects), state_of_dress."
        ),
    },
    "props": {
        "schema": {
            "items": "objlist",
            "weapons": "list",
        },
        "instruction": (
            "Look at what the single most prominent human figure CARRIES or "
            "WEARS as objects in this frame (excluding ordinary clothing). "
            "List each prop as an object with keys: item, color, "
            "worn_or_carried (worn/carried/held), body_location (e.g. belt, "
            "back, left hand, neck). List any weapons separately as short "
            "strings. If none, use empty lists. Return JSON with exactly "
            "these keys: items (list of objects), weapons (list of strings)."
        ),
    },
    "colors": {
        "schema": {
            "skin": "str",
            "hair": "str",
            "eyes": "str",
            "garment_primary": "str",
            "garment_secondary": "str",
            "metal_accent": "str",
        },
        "instruction": (
            "Report the COLORS of the single most prominent human figure in "
            "this frame, as they would appear under neutral white light "
            "(ignore colored scene lighting): skin, hair, eyes, the primary "
            "garment color, a secondary garment color, and any metal accent "
            "color (jewelry, armor trim, weapon metal). Use null when a region "
            "is not visible. Return JSON with exactly these keys: skin, hair, "
            "eyes, garment_primary, garment_secondary, metal_accent."
        ),
    },
    "signature": {
        "schema": {
            "memorable_traits": "list",
            "unmistakable_because": "str",
        },
        "instruction": (
            "Look at the single most prominent human figure in this frame. "
            "List the most MEMORABLE visual traits — the handful of features "
            "that would let someone recognize this figure in another frame "
            "(e.g. 'long white hair', 'fur cloak', 'skull headdress'). Then "
            "state in one sentence what makes this figure unmistakable. "
            "Physical traits only. Return JSON with exactly these keys: "
            "memorable_traits (list of strings), unmistakable_because."
        ),
    },
}

SYSTEM_INVARIANTS = (
    "You are a precise visual observer labeling ONE frame from a 1983 "
    "rotoscoped fantasy animation. Rules:\n"
    "- Describe only what is visually present in the frame. Never invent.\n"
    "- Never name characters, actors, or voice performers — physical "
    "attributes only.\n"
    "- Report skin and colors as they would appear under neutral light; "
    "ignore colored scene lighting.\n"
    "- Respond with strict JSON only: no prose, no markdown fences, no "
    "explanations before or after the JSON object.\n"
    "- One frame per call; describe the single most prominent human figure."
)


def build_messages(lens, image_b64):
    """Chat messages for one (image, lens) call. OpenAI vision format."""
    if lens not in LENSES:
        raise KeyError(f"unknown lens: {lens}")
    spec = LENSES[lens]
    system = (
        SYSTEM_INVARIANTS
        + "\n\nRequired JSON schema (keys and value kinds):\n"
        + json.dumps(spec["schema"], indent=1)
        + "\n\n" + spec["instruction"]
    )
    user_text = spec["instruction"] + "\nReturn strict JSON only."
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": [
            {"type": "image_url",
             "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
            {"type": "text", "text": user_text},
        ]},
    ]


# --------------------------------------------------------------------------
# normalize — salvage the JSON answer out of whatever text came back.
# --------------------------------------------------------------------------
_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _first_json_object(text):
    """Return the first balanced {...} dict found in text, else None."""
    candidates = []
    m = _FENCE_RE.search(text)
    if m:
        candidates.append(m.group(1))
    start = text.find("{")
    while start != -1:
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(text[start:i + 1])
                    break
        start = text.find("{", start + 1)
    for cand in candidates:
        try:
            obj = json.loads(cand)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(obj, dict):
            return obj
    return None


_NULLISH = {"null", "none", "n/a", "na", "nil", ""}


def is_nullish(val):
    """True for None and placeholder strings the model emits instead of JSON null."""
    return val is None or (isinstance(val, str) and val.strip().lower() in _NULLISH)


def _nullify(val):
    """Map placeholder strings the model emits instead of JSON null to None."""
    return None if is_nullish(val) else val


def normalize(lens, text):
    """Normalize raw VLM text into the lens schema, or None on junk.

    - strips fences/prose around the JSON object
    - fills missing schema keys with None
    - coerces list/objlist fields given as a single value into a 1-element list
    - maps nullish placeholder strings ("null", "None", "N/A") to None
    - keeps unknown keys under "_extra" (never thrown away)
    """
    if lens not in LENSES:
        raise KeyError(f"unknown lens: {lens}")
    if not text or not isinstance(text, str):
        return None
    obj = _first_json_object(text)
    if obj is None:
        return None
    schema = LENSES[lens]["schema"]
    out = {}
    for key, kind in schema.items():
        raw = obj.get(key)
        val = _nullify(raw)
        if kind == "list":
            if isinstance(raw, str):
                val = [] if val is None else [val]
            elif isinstance(val, list):
                val = [v for v in val if _nullify(v) is not None]
        elif kind == "objlist":
            if isinstance(val, dict):
                val = [val]
            elif not isinstance(val, list):
                val = None
        elif kind == "str" and val is not None and not isinstance(val, str):
            val = str(val)
        out[key] = val
    extra = {k: v for k, v in obj.items() if k not in schema}
    if extra:
        out["_extra"] = extra
    return out


# --------------------------------------------------------------------------
# consensus — deterministic majority vote with substring merging.
# --------------------------------------------------------------------------
def _canon_key(s):
    """Collapse a value string for voting: lowercase, squeeze punctuation."""
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


def consensus(values):
    """Majority vote over string answers.

    Returns {"value", "share", "n", "outliers"} where value is the winning
    canonical form (shortest merged surface string, lowercased; ties
    alphabetical), share = winner votes / n, and outliers = original-cased
    non-winner values.

    Merging: two answers vote together when one's collapsed token set is a
    subset of the other's ("long black" merges into "long, straight, black
    hair" — substring-contiguous merge fails on interleaved adjectives).
    Greedy over input order, so the result is deterministic.
    """
    vals = []
    for v in values:
        if isinstance(v, str) and v.strip() and _canon_key(v):
            vals.append((v, set(_canon_key(v).split())))
    n = len(vals)
    if n == 0:
        return {"value": None, "share": 0.0, "n": 0, "outliers": []}

    clusters = []  # {"tokens": set, "surface": list[str], "votes": int, "members": [...]}
    for orig, toks in vals:
        placed = False
        for cl in clusters:
            if toks <= cl["tokens"] or cl["tokens"] <= toks:
                cl["tokens"] |= toks
                cl["surface"].append(orig.strip())
                cl["votes"] += 1
                cl["members"].append(orig)
                placed = True
                break
        if not placed:
            clusters.append({"tokens": set(toks), "surface": [orig.strip()],
                             "votes": 1, "members": [orig]})

    def canon(cl):
        # shortest surface form wins; ties alphabetical (case-insensitive)
        return sorted(cl["surface"], key=lambda s: (len(s), s.lower()))[0].lower()

    winner = min(clusters, key=lambda cl: (-cl["votes"], canon(cl)))
    outliers = [m for cl in clusters if cl is not winner for m in cl["members"]]
    return {
        "value": canon(winner),
        "share": winner["votes"] / n,
        "n": n,
        "outliers": outliers,
    }
