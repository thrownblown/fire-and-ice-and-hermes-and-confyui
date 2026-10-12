import base64, json, urllib.request

B = r"E:\FNI\stills\boundary"
def enc(n):
    return "data:image/jpeg;base64," + base64.b64encode(
        open(B + "\\shot_%05d_first.jpg" % n, "rb").read()).decode()

SYSTEM = ("You compare film stills to group them by camera setup. A setup = the "
          "same camera position, background, and framing. Two shots are the SAME "
          "setup even if the people in them moved or changed pose. They are "
          "DIFFERENT setups if the camera is on the opposite side (left/right "
          "swapped) or in front vs behind, or the background is a different wall "
          "or location. Reply strict JSON only.")

def group(name, shots):
    content = [{"type": "text", "text":
        "Group these %d stills (labeled 1..%d) into camera setups. Return JSON "
        "{\"groups\": [[shot labels in each setup], ...]} with every label used "
        "exactly once. Same-setup shots share camera position + background + "
        "framing (pose may differ)." % (len(shots), len(shots))}]
    for i, n in enumerate(shots, 1):
        content.append({"type": "text", "text": "[%d]" % i})
        content.append({"type": "image_url", "image_url": {"url": enc(n)}})
    payload = {"model": "qwen25vl32b", "temperature": 0.0, "max_tokens": 600,
               "messages": [{"role": "system", "content": SYSTEM},
                            {"role": "user", "content": content}]}
    req = urllib.request.Request("http://127.0.0.1:1234/v1/chat/completions",
        data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=180))
    print(name, "->", r["choices"][0]["message"]["content"])

# S06 hard subset (labels 1..7 -> shots 199,200,201,202,203,204,205)
group("S06_199-205", [199,200,201,202,203,204,205])
# S02 17/18/24/25
group("S02_17-18-24-25", [17,18,24,25])