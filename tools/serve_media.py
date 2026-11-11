# -*- coding: utf-8 -*-
"""Range-capable static file server for local media.

`python -m http.server` answers a Range request with 200 and never sends Accept-Ranges, so a browser
cannot seek a long video; on a 2 GB file most players either stall or insist on downloading the whole
thing first. This serves 206 Partial Content with Content-Range, which is what the HTML5 <video>
element needs to start fast and scrub.

    .venv/Scripts/python.exe tools/serve_media.py --root fullrun/stitched --port 8646
    .venv/Scripts/python.exe tools/serve_media.py --root . --port 8646 --verbose
"""
from __future__ import annotations

import argparse
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

CHUNK = 1 << 20          # 1 MiB write blocks
VERBOSE = False


class RangeHandler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"        # keep-alive: video players open several connections

    def _range(self, size: int) -> tuple[int, int] | None:
        h = self.headers.get("Range")
        if not h or not h.startswith("bytes="):
            return None
        spec = h[6:].split(",")[0].strip()          # only the first range is honoured
        start_s, _, end_s = spec.partition("-")
        if start_s == "":                            # "bytes=-N" = the last N bytes
            n = int(end_s or 0)
            return max(0, size - n), size - 1
        start = int(start_s)
        if start >= size:
            return None
        end = int(end_s) if end_s else size - 1
        return start, min(end, size - 1)

    def do_GET(self):                                # noqa: N802 (http.server API)
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().do_GET()                  # directory listing comes from the stdlib
        if not os.path.isfile(path):
            self.send_error(404, "not found")
            return
        size = os.path.getsize(path)
        ctype = self.guess_type(path)
        rng = self._range(size)
        try:
            f = open(path, "rb")
        except OSError as exc:
            self.send_error(404, str(exc))
            return
        with f:
            if rng:
                start, end = rng
                f.seek(start)
                self.send_response(206)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                self.send_header("Content-Length", str(end - start + 1))
            else:
                start, end = 0, size - 1
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(size))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            remaining = end - start + 1
            while remaining > 0:
                buf = f.read(min(CHUNK, remaining))
                if not buf:
                    break
                self.wfile.write(buf)
                remaining -= len(buf)

    def do_HEAD(self):                               # noqa: N802 — advertise ranges to players that probe first
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            return super().do_HEAD()
        self.send_response(200)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Length", str(os.path.getsize(path)))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()

    def log_message(self, format, *args):             # noqa: A002 (must match the stdlib signature)
        if VERBOSE:
            super().log_message(format, *args)


def main() -> int:
    global VERBOSE
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--port", type=int, default=8646)
    ap.add_argument("--bind", default="0.0.0.0")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    VERBOSE = a.verbose
    root = os.path.abspath(a.root)
    handler = lambda *args, **kw: RangeHandler(*args, directory=root, **kw)   # noqa: E731
    srv = ThreadingHTTPServer((a.bind, a.port), handler)
    print(f"serving {root} on http://{a.bind}:{a.port}/  (range requests supported)", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
