"""Stage 7: one API-format graph per H3 prompt.

No ComfyUI. Copies graphs/video_minimax_h3_r2v.json and fills:
  node 132  duration (seconds) from the prompt header
  node 138  prompt body
  node 92   filename prefix
  LoadImage nodes 137, 139, 147-150  one per reference, in subject order

MiniMaxH3ReferenceToVideo accepts up to 9 refs as ref_images.ref_image_N.
The sample graph only wired two. Empty slots are omitted, not left blank.

Output: reports/h3-graphs/chunk_NNNN.json
"""
import json
import re
from pathlib import Path

ROOT = Path(r"E:/FNI")
TEMPLATE = ROOT / "graphs" / "video_minimax_h3_r2v.json"
PROMPTS = ROOT / "reports" / "h3-prompts"
OUT = ROOT / "reports" / "h3-graphs"

# LoadImage node ids reserved for ref slots 0..5. 137 and 139 match the sample graph.
REF_NODES = ["137", "139", "147", "148", "149", "150"]
MAX_REFS = len(REF_NODES)

# Files that exist in corpus/. The Linux box must have the same names in input/.
REFS = {
    "Teegra": "teegra_shot_00067.jpg",
    "Larn": "Larn.webp",
    "Nekron": "nekron_shot_00784.jpg",
}
SUBJECT = re.compile(r"^<Subject \d+>: (.+?)\.")
LENGTH = re.compile(r"^# graph_length_seconds:\s*([0-9.]+)")


def lead_names(body):
    traits = {
        "long black hair": "Teegra",
        "blond man": "Larn",
        "long white hair": "Nekron",
    }
    names = []
    for line in body.splitlines():
        m = SUBJECT.match(line)
        if not m:
            continue
        desc = m.group(1)
        for needle, name in traits.items():
            if needle in desc and name not in names:
                names.append(name)
    return names


def wire_refs(graph, images):
    """One LoadImage per picture, wired as ref_images.ref_image_N from 0.

    Slots past the images we have are removed so an empty LoadImage is not queued.
    """
    images = images[:MAX_REFS]
    node = graph["136"]["inputs"]
    for key in [k for k in node if k.startswith("ref_images.ref_image_")]:
        node.pop(key)
    for i, image in enumerate(images):
        nid = REF_NODES[i]
        graph[nid] = {
            "inputs": {"image": image},
            "class_type": "LoadImage",
            "_meta": {"title": f"Load Image {i}"},
        }
        node[f"ref_images.ref_image_{i}"] = [nid, 0]
    for nid in REF_NODES[len(images):]:
        graph.pop(nid, None)


def fill(template, prompt_text, stem):
    graph = json.loads(json.dumps(template))
    header, _, body = prompt_text.partition("\n\n")
    m = LENGTH.search(header)
    if not m:
        raise ValueError(f"{stem}: no graph_length_seconds")
    seconds = float(m.group(1))
    names = lead_names(body or prompt_text)
    images = [REFS[n] for n in names if n in REFS]
    if not images:
        images = [REFS["Larn"]]
    graph["132"]["inputs"]["value"] = seconds
    graph["138"]["inputs"]["value"] = (body or prompt_text).strip() + "\n"
    graph["92"]["inputs"]["filename_prefix"] = f"video/FNI_{stem}"
    wire_refs(graph, images)
    return graph


def main():
    template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("chunk_*.json"):
        old.unlink()
    written = 0
    for path in sorted(PROMPTS.glob("chunk_*.txt")):
        text = path.read_text(encoding="utf-8")
        graph = fill(template, text, path.stem)
        dest = OUT / (path.stem + ".json")
        dest.write_text(json.dumps(graph, indent=2), encoding="utf-8")
        written += 1
    print(f"wrote {written} graphs to {OUT}")


if __name__ == "__main__":
    main()
