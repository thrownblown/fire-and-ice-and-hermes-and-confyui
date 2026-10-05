"""VLM correlation: stills + script -> structured shot labels via Qwen3-VL.

Runs against LM Studio's OpenAI-compatible endpoint. The model returns JSON;
we validate it against a Pydantic schema before it is trusted downstream.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

from pydantic import BaseModel, Field


class ShotLabel(BaseModel):
    shot_id: str
    characters: list[str] = Field(default_factory=list)
    action: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)


class CorrelationOutput(BaseModel):
    scene_id: str
    location: str
    shots: list[ShotLabel]
    dialogue_assignments: list[dict] = Field(default_factory=list)


def validate_output(raw: dict) -> CorrelationOutput:
    """Validate VLM JSON against the correlation schema. Raises on bad input."""
    return CorrelationOutput.model_validate(raw)


def encode_image(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def build_prompt(script_span: str, shot_ids: list[str]) -> str:
    shots = "\n".join(shot_ids)
    return (
        "You are a film analyst. Given the stills of the shots listed below, in "
        "order, plus the script excerpt, produce JSON with:\n"
        "- scene_id and location (the environment shown)\n"
        "- per-shot: shot_id, characters present (named from the script), coarse "
        "action, confidence 0.0-1.0\n"
        "- dialogue_assignments: which script lines fall in which shot\n\n"
        f"Shots (in order):\n{shots}\n\n"
        f"Script excerpt:\n{script_span}\n\n"
        "Respond with ONLY the JSON, no prose."
    )


def call_vlm(model: str, prompt: str, image_paths: list[Path],
             system: str | None = None,
             base_url: str = "http://127.0.0.1:1234/v1") -> dict:
    """Send one multimodal request to LM Studio and return the parsed JSON."""
    import time

    import requests
    content = [{"type": "text", "text": prompt}]
    for p in image_paths:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{encode_image(p)}"},
        })
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": content})
    payload = {"model": model, "messages": messages, "temperature": 0.2}
    for attempt in range(3):
        try:
            resp = requests.post(f"{base_url}/chat/completions", json=payload, timeout=600)
            resp.raise_for_status()
            break
        except requests.HTTPError:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    text = resp.json()["choices"][0]["message"]["content"]
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


SYSTEM_PROMPT = (
    "You are a film-analysis assistant working frame-by-frame on Ralph Bakshi's "
    "Fire and Ice (1983). Describe only what is visually present in the frames. "
    "Never name characters, actors, or voice performers — report physical "
    "observations only: count, sex, build, hair, skin, clothing, props, pose. "
    "Report skin tone as it would appear in neutral light; ignore colored-lighting "
    "tints. Respond with strict JSON only, no prose, no markdown fences."
)


def describe_people(model: str, image_paths: list[Path],
                    base_url: str = "http://127.0.0.1:1234/v1") -> dict:
    """Physical description of people in the frames — deliberately no names."""
    prompt = (
        "Count the people visible in these frames: how many men, how many women. "
        "For each person, give physical attributes only (sex, build, hair, skin, "
        "clothing) and their action. Describe each person individually: if they "
        "differ, state the differences, and do not repeat an identical description "
        "for different people. Do NOT name anyone. Respond with JSON: "
        '{"count_men": 0, "count_women": 0, "people": [{"sex": "", "build": "", '
        '"hair": "", "skin": "", "clothing": "", "action": ""}]}'
    )
    result = call_vlm(model, prompt, image_paths, system=SYSTEM_PROMPT, base_url=base_url)
    if not result.get("count_men") and not result.get("count_women"):
        result["people"] = []
    return result


def describe_location(model: str, image_paths: list[Path],
                      base_url: str = "http://127.0.0.1:1234/v1") -> dict:
    """Background/location description of the frames."""
    prompt = (
        "Describe the background/location/environment in these frames. Name the "
        "setting with a specific noun phrase (e.g., forest, open plains, ice cave, "
        "stone fortress interior, village, shoreline). Do not leave location empty "
        "when any setting is visible. Also give indoors/outdoors, time of day, and "
        "notable elements. Respond with JSON: "
        '{"location": "", "indoors_outdoors": "", "time_of_day": "", '
        '"notable_elements": []}'
    )
    return call_vlm(model, prompt, image_paths, system=SYSTEM_PROMPT, base_url=base_url)


def describe_creatures(model: str, image_paths: list[Path],
                       base_url: str = "http://127.0.0.1:1234/v1") -> dict:
    """Creatures/animals in the frames (mounts, reptiles, birds, monsters)."""
    prompt = (
        "Are there any animals or creatures visible in these frames (mounts, "
        "reptiles, birds, monsters)? For each, give a type, physical description, "
        "and what it is doing. Do NOT name specific characters. Respond with JSON: "
        '{"creatures": [{"type": "", "description": "", "action": ""}]}'
    )
    result = call_vlm(model, prompt, image_paths, system=SYSTEM_PROMPT, base_url=base_url)
    result["creatures"] = [
        c for c in result.get("creatures", [])
        if (c.get("type") or c.get("description"))
    ]
    return result
