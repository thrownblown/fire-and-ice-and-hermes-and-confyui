"""Inventory the pulled 5090 workflow sidecar PNGs: what each job was.

ComfyUI embeds the API graph in every saved PNG (the 'prompt' tEXt chunk), so
the pulled sidecars are a durable record of runs that never got logged while
they ran. Writes renders/5090/INVENTORY.md + .json.

Run: .venv/Scripts/python.exe tools/inventory_5090.py
"""
import json
import re
from pathlib import Path
from PIL import Image

ROOT = Path(r"E:/FNI")
DEST = ROOT / "renders" / "5090"


def graphs():
    """(png_path, api_graph, ui_meta) for every pulled sidecar."""
    for p in sorted(DEST.rglob("*.png")):
        try:
            info = dict(Image.open(p).info)
        except Exception:  # noqa: BLE001
            continue
        if "prompt" not in info:
            continue
        try:
            api = json.loads(info["prompt"])
        except Exception:  # noqa: BLE001
            continue
        yield p, api, info


def summarize(api):
    out = {"refs": [], "lora_off": [], "lora_on": [], "seeds": [], "prefix": "",
           "prompt_fields": {}, "models": [], "fps": None, "seconds": None}
    for n in api.values():
        ct = n.get("class_type", "")
        ins = n.get("inputs", {})
        if ct == "LoadImageCrop" or ct == "LoadImage":
            img = ins.get("image")
            if img:
                out["refs"].append(img)
        elif ct.startswith("Power Lora Loader"):
            for k, v in ins.items():
                if isinstance(v, dict) and "lora" in v:
                    name = v.get("lora")
                    (out["lora_on"] if v.get("on") else out["lora_off"]).append(name)
        elif ct == "easy seed" or ct == "KSampler":
            s = ins.get("seed") or ins.get("noise_seed")
            if s is not None:
                out["seeds"].append(s)
        elif ct == "VHS_VideoCombine":
            fp = ins.get("filename_prefix")
            if fp and (not out["prefix"] or "low" not in fp):
                out["prefix"] = out["prefix"] or fp
            if fp and "low" in fp:
                out["prefix"] = fp
        elif ct == "PrimitiveStringMultiline":
            v = ins.get("value") or ""
            for f in ("subject_definitions", "integrated_multimodal_description",
                      "summary", "retention_analysis", "overall_soundscape",
                      "non_diegetic_music", "detailed_description"):
                if f in v:
                    m = re.search(f + r"\s*:\s*(.{0,700})", v, re.S)
                    if m:
                        out["prompt_fields"][f] = " ".join(m.group(1).split())[:700]
        elif ct in ("UNETLoader", "CLIPLoader", "VAELoader"):
            nm = ins.get("unet_name") or ins.get("clip_name") or ins.get("vae_name")
            if nm:
                out["models"].append(nm)
        elif ct == "PrimitiveFloat":
            v = ins.get("value")
            if v == 48.0:
                out["fps"] = 48
        elif ct == "ComfyMathExpression":
            out["seconds"] = 15.0 if "a" in ins.get("expression", "") else out["seconds"]
    return out


def main():
    rows = []
    for p, api, info in graphs():
        s = summarize(api)
        row = {"sidecar": p.relative_to(ROOT).as_posix(),
               "created": info.get("CreationTime", ""), **s}
        rows.append(row)
    # group by the job's base stamp (mm_YYYYMMDD_HHMMSS)
    jobs = {}
    for r in rows:
        m = re.search(r"(?:low_)?mm_(\d{8}_\d{6})", r["sidecar"])
        key = m.group(1) if m else r["sidecar"]
        jobs.setdefault(key, {"stamp": key, "sidecars": [], "refs": set(), "lora_on": set(),
                              "lora_off": set(), "models": set(), "fields": {},
                              "seeds": set(), "fps": r["fps"]})
        j = jobs[key]
        j["sidecars"].append(r["sidecar"])
        j["refs"].update(r["refs"])
        j["lora_on"].update(r["lora_on"])
        j["lora_off"].update(r["lora_off"])
        j["models"].update(r["models"])
        j["seeds"].update(str(x) for x in r["seeds"])
        for f, v in r["prompt_fields"].items():
            j["fields"].setdefault(f, v)

    (DEST / "INVENTORY.json").write_text(
        json.dumps([{**j, "refs": sorted(j["refs"]), "lora_on": sorted(j["lora_on"]),
                     "lora_off": sorted(j["lora_off"]), "models": sorted(j["models"]),
                     "seeds": sorted(j["seeds"])} for j in jobs.values()], indent=1),
        encoding="utf-8")

    lines = ["# 5090 output inventory", "",
             "Runs recovered from the pulled workflow sidecars — these are jobs that",
             "were queued on the 5090 but never written into project memory while they ran.", ""]
    for j in sorted(jobs.values(), key=lambda x: x["stamp"]):
        lines.append("## %s" % j["stamp"])
        lines.append("- sidecars: %d" % len(j["sidecars"]))
        lines.append("- reference images: %s" % ", ".join(sorted(j["refs"])) or "-")
        lines.append("- LoRAs enabled: %s" % (", ".join(sorted(j["lora_on"])) or "none"))
        lines.append("- LoRAs available: %s" % ", ".join(sorted(j["lora_off"])[:6]))
        lines.append("- models: %s" % ", ".join(sorted(j["models"])))
        lines.append("- seeds: %s" % ", ".join(sorted(j["seeds"])))
        for f in ("subject_definitions", "summary", "integrated_multimodal_description"):
            if f in j["fields"]:
                lines.append("- %s: %s" % (f, j["fields"][f][:400]))
        lines.append("")
    (DEST / "INVENTORY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("jobs: %d" % len(jobs))
    for j in sorted(jobs.values(), key=lambda x: x["stamp"]):
        print("  %s  refs=%s  lora_on=%s" % (j["stamp"], ",".join(sorted(j["refs"]))[:60],
                                             ",".join(sorted(j["lora_on"])) or "none"))
    print("wrote", DEST / "INVENTORY.md")


if __name__ == "__main__":
    main()