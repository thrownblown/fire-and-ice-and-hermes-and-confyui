import base64

import pytest
from pydantic import ValidationError

from core.vlm_correlate import build_prompt, encode_image, validate_output


def test_valid_output_passes():
    raw = {"scene_id": "s1", "location": "forest", "shots": [
        {"shot_id": "shot:1", "characters": ["Teegra"], "action": "talking", "confidence": 0.9}
    ]}
    out = validate_output(raw)
    assert out.location == "forest"
    assert out.shots[0].characters == ["Teegra"]


def test_invalid_confidence_rejected():
    raw = {"scene_id": "s1", "location": "forest", "shots": [
        {"shot_id": "shot:1", "confidence": 2.0}
    ]}
    with pytest.raises(ValidationError):
        validate_output(raw)


def test_missing_shot_id_rejected():
    raw = {"scene_id": "s1", "location": "forest", "shots": [{"characters": []}]}
    with pytest.raises(ValidationError):
        validate_output(raw)


def test_prompt_contains_shots_and_script():
    p = build_prompt("SCRIPT TEXT", ["shot:1", "shot:2"])
    assert "shot:1" in p and "shot:2" in p and "SCRIPT TEXT" in p


def test_encode_image_roundtrip(tmp_path):
    img = tmp_path / "a.jpg"
    img.write_bytes(b"\xff\xd8\xff\xd9")
    assert base64.b64decode(encode_image(img)) == b"\xff\xd8\xff\xd9"
