#!/usr/bin/env python
"""Describe an image via the local LM Studio vision model (qwen3-vl-8b)."""
import argparse, base64, json, urllib.request

MODEL = "qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s"
URL = "http://127.0.0.1:1234/v1/chat/completions"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--q", default="Describe this image in detail.")
    args = ap.parse_args()

    b64 = base64.b64encode(open(args.image, "rb").read()).decode()
    payload = {
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                {"type": "text", "text": args.q},
            ],
        }],
        "temperature": 0.2,
        "max_tokens": 700,
    }
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read().decode())
    print(data["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()
