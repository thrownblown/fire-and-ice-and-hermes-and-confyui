"""Diagnose the 400 on refrun's /prompt queue. Replicates cmd_render for S06-c01
but reads the full HTTP error body instead of the bare status."""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(r"E:/FNI")))

import fullrun as F
import refrun as R

rows = [json.loads(l) for l in F.CHUNK_LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
row = next(r for r in rows if r["chunk_id"] == "S06-c01")

assert R.build_ref_video(row), "no ref video"
people, dialogue = R.load_context()
caps = F.load_captions()
text = R.build_ref_prompt(row, caps, people, dialogue)

print("=== upload ref video ===")
try:
    vname = F.upload(R.REFS / R.ref_video_name(row["chunk_id"]))
    print("video upload returned name:", repr(vname))
except Exception as e:  # noqa: BLE001
    print("video upload EXC:", e); vname = None

print("=== upload stills ===")
still_names = []
for snum in row["shot_nums"]:
    s = F.stills_for(snum)
    if s:
        try:
            n = F.upload(s[0]); still_names.append(n); print("still:", snum, "->", repr(n))
        except Exception as e:  # noqa: BLE001
            print("still upload EXC:", e)

g = R.build_ref_graph(row, still_names)
g["138"]["inputs"]["value"] = text
body = json.dumps({"prompt": g}).encode()
req = urllib.request.Request(F.COMFY + "/prompt", data=body,
                             headers={"Content-Type": "application/json"})
try:
    r = urllib.request.urlopen(req, timeout=90)
    print("=== OK ===\n", r.read().decode()[:600])
except urllib.error.HTTPError as e:
    print("=== HTTP %d ===\n%s" % (e.code, e.read().decode()[:4000]))