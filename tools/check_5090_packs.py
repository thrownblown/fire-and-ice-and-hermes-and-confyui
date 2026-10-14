"""Check which H3-relevant ComfyUI node packs are installed on the render box.

Queries the running ComfyUI's /object_info (authoritative: node class names) and
/objections -> /extensions (frontend JS, a secondary signal) and reports, for each
pack this project references, whether its probe nodes are present.

Run: .venv/Scripts/python.exe tools/check_5090_packs.py [base_url]
Default base URL is the 5090 (env FNI_COMFY, else the Tailscale address).
"""
import json
import os
import re
import sys
import urllib.request

DEFAULT = os.environ.get("FNI_COMFY", "http://100.104.7.72:8188")

# pack label -> (github repo, regex matching its node class names)
PACKS = [
    ("Motion-Context (chain/bridge)", "NikoDemon80/ComfyUI-H3-Motion-Context",
     r"MiniMaxH3MotionContext"),
    ("obvpm timeline editor", "chanon/comfyui-obvpm-timeline",
     r"MiniMaxH3Timeline|MiniMaxH3ClipReel"),
    ("Larry Turbo (Larry v4-600 LoRA)", "Larryvrh/ComfyUI-MiniMax-H3-Turbo",
     r"MiniMaxH3Turbo(LoRA|Sampler)"),
    ("RefMod (bake .refmod)", "Luisacaotica/ComfyUI-MiniMaxH3Mod",
     r"MiniMaxH3RefMod(Create|Apply|sLoader|Extract)"),
    ("Fantastic PromptBuilder + RefMod", "Adudeguyman/ComfyUI-Fantastic-MiniMaxH3-PromptBuilder",
     r"MiniMaxH3FantasticRefModCreate|MiniMaxH3PromptBuilder"),
    ("H3 latent upscaler", "LBH-123-AI/Comfyui_Minimax_h3_latent_Upscaler",
     r"MinimaxH3LatentUpscaler"),
    ("Spectrum forecast (speed)", "xmarre/ComfyUI-Spectrum-MiniMax-H3",
     r"[Ss]pectrum"),
    ("PDD acc (motion-only speed)", "Jalen-Brunson/ComfyUI-MiniMax-H3-PDD-Acc",
     r"MiniMax.*PDD|PDD.*MiniMax"),
    ("Omnichar .char identity", "omnichar/ComfyUI-Omnichar",
     r"Omnichar"),
    ("Sol attention", None, r"MiniMaxH3MemoryEfficientSolAttentionPatch|H3SLAAttention"),
    ("Sage attention", None, r"MiniMaxH3MemoryEfficientSageAttentionPatch"),
    ("EasyCache", None, r"EasyCache"),
    ("RES4LYF samplers", None, r"ClownSampler|BongSampler|ClownGuides"),
    ("ChunkFeedForward", None, r"MiniMaxH3ChunkFeedForward"),
]


def get(base, path, timeout=30):
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return json.load(r)


def main():
    base = (sys.argv[1] if len(sys.argv) > 1 else DEFAULT).rstrip("/")
    print("probing", base)
    oi = get(base, "/object_info")
    names = list(oi)
    try:
        ext = get(base, "/extensions", timeout=15)
        extpacks = sorted({x.split("/")[2] for x in ext
                           if x.startswith("/extensions/") and len(x.split("/")) > 2})
    except Exception:  # noqa: BLE001
        extpacks = []
    print("node classes: %d   frontend-extension packs: %d" % (len(names), len(extpacks)))
    manager = any(p.lower() in ("comfyui-manager", "comfyui_manager") for p in extpacks)
    print("ComfyUI-Manager: %s" % ("present" if manager else "NOT detected"))

    missing = []
    for label, repo, pat in PACKS:
        rx = re.compile(pat)
        hits = [n for n in names if rx.search(n)]
        if hits:
            print("  OK      %-34s %s" % (label, ", ".join(hits[:3])))
        else:
            print("  MISSING %-34s %s" % (label, repo or ""))
            missing.append((label, repo))
    print()
    if missing:
        print("MISSING (%d):" % len(missing))
        for label, repo in missing:
            print("  - %s  %s" % (label, repo or "(built-in, none)"))
    else:
        print("all probed packs present")


if __name__ == "__main__":
    main()
