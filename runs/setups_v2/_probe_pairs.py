import base64, json, urllib.request
from pathlib import Path

BOUND = Path(r"E:\FNI\stills\boundary")

def enc(sid):
    p = BOUND / ("shot_%05d_first.jpg" % sid)
    return "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode()

SYSTEM = ("You are judging camera setups in an animated movie. Two shots are the SAME "
          "setup if the camera is in the SAME position showing the SAME background, even "
          "if the characters are in different poses or doing different actions. They are "
          "DIFFERENT if the camera shot from the OPPOSITE side (a reverse angle / mirrored "
          "view showing a DIFFERENT background or wall). Respond with exactly one word: SAME or DIFFERENT.")

def ask(a, b):
    content = [{"type":"text","text":"[A]"},
               {"type":"image_url","image_url":{"url":enc(int(a))}},
               {"type":"text","text":"[B]"},
               {"type":"image_url","image_url":{"url":enc(int(b))}}]
    payload = {"model":"qwen25vl32b","temperature":0.0,"max_tokens":50,
               "messages":[{"role":"system","content":SYSTEM},
                           {"role":"user","content":content}]}
    req = urllib.request.Request("http://127.0.0.1:1234/v1/chat/completions",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type":"application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=300))
    return r["choices"][0]["message"]["content"].strip()

pairs = [("200","202","REVERSE angle -> want DIFFERENT"),
         ("200","204","REVERSE angle -> want DIFFERENT"),
         ("199","203","same setup -> want SAME"),
         ("202","204","same setup -> want SAME"),
         ("199","201","seated vs standing (same cam?) -> SAME"),
         ("24","25","front vs rear CU -> ?"),
         ("23","26","village outside vs inside -> DIFFERENT")]
for a,b,note in pairs:
    try:
        verdict = ask(a,b)
    except Exception as e:
        verdict = "ERROR: %s" % e
    print("%s vs %s  (%s)  ->  %s" % (a,b,note,verdict))