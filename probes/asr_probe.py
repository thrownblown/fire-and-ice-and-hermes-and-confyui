"""ASR qualification probe: transcribe chunk_00001.wav.

This machine's IPv6 routing drops connections to huggingface.co (WinError
10054). Forcing AF_INET resolution fixes the faster-whisper model download.
"""
import socket

_orig_getaddrinfo = socket.getaddrinfo


def _ipv4_only(host, *args, **kwargs):
    return [r for r in _orig_getaddrinfo(host, *args, **kwargs)
            if r[0] == socket.AF_INET]


socket.getaddrinfo = _ipv4_only

from pathlib import Path

from core.asr import transcribe

recs = transcribe(Path("audio/chunks/chunk_00001.wav"))
for r in recs[:20]:
    print(f"{r['start']:>7.2f}-{r['end']:>7.2f}: {r['text']}")
print(f"--- {len(recs)} segments total ---")
