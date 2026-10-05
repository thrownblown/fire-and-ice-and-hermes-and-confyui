"""Transcribe master audio with faster-whisper (local GPU)."""
from __future__ import annotations

import socket
from pathlib import Path

# This machine's IPv6 routing drops connections to huggingface.co (WinError
# 10054). Force IPv4 so the model download works; do this at import time so
# every caller benefits.
_orig_getaddrinfo = socket.getaddrinfo


def _ipv4_only(host, *args, **kwargs):
    return [r for r in _orig_getaddrinfo(host, *args, **kwargs)
            if r[0] == socket.AF_INET]


socket.getaddrinfo = _ipv4_only


def segments_to_records(segments) -> list[dict]:
    """Serialize faster-whisper segments to plain dicts. Pure."""
    return [
        {"index": i, "start": round(float(s.start), 3),
         "end": round(float(s.end), 3), "text": str(s.text).strip()}
        for i, s in enumerate(segments)
    ]


def transcribe(wav_path: Path, model_size: str = "large-v3",
               device: str = "cuda", compute_type: str = "float16") -> list[dict]:
    """Transcribe a WAV and return timecoded segment records.

    First run downloads the whisper model (~3 GB) to the local cache.
    """
    from faster_whisper import WhisperModel
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, _info = model.transcribe(str(wav_path), word_timestamps=True,
                                       vad_filter=True)
    return segments_to_records(segments)
