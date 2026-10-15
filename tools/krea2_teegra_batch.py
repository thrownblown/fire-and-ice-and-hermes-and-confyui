#!/usr/bin/env python
"""Teegra Krea2 still batch — isolate LoRA strength, fixed seed.

Configs (all same seed 82036621553915, same prompt except the person_27 trigger word
dropped when person_27 is off):
  1. person_27 ON @1.0  + retro-fantasy @1.0   (baseline, as the saved workflow shipped)
  2. person_27 OFF      + retro-fantasy @1.0   (text-only Teegra — the prior "char LoRA off" fix)
  3. person_27 OFF      + retro-fantasy @0.8   (gentler style)
  4. person_27 @0.4     + retro-fantasy @1.0   (weak identity anchor)
"""
import sys, os, time
sys.path.insert(0, r"E:/FNI")
sys.path.insert(0, r"E:/FNI/tools")
import krea2_stills as k

WF = r"C:/Users/gsfny/Downloads/ComfyUI_00108_.json"
OUT = r"E:/FNI/renders/5090/teegra-stills"
SEED = 82036621553915

PRE_WITH_PERSON27 = "retr0fantasy, 60s Soviet fantasy-film, subtle film grain, aged theatrical print quality, caucasian, person_27,"
PRE_NO_PERSON27 = "retr0fantasy, 60s Soviet fantasy-film, subtle film grain, aged theatrical print quality, caucasian,"

CONFIGS = [
    ("c1_person_271_retro1", 1.0, 1.0, PRE_WITH_PERSON27),
    ("c2_person_27OFF_retro1", 0.0, 1.0, PRE_NO_PERSON27),
    ("c3_person_27OFF_retro08", 0.0, 0.8, PRE_NO_PERSON27),
    ("c4_person_2704_retro1", 0.4, 1.0, PRE_WITH_PERSON27),
]

for tag, person_27_s, retro_s, pre in CONFIGS:
    g = k.load_workflow(WF)
    k.set_prompt(g, pre=pre)
    k.set_lora(g, "lora_1", on=(person_27_s > 0), strength=person_27_s)
    k.set_lora(g, "lora_7", on=(retro_s > 0), strength=retro_s)
    k.set_seed(g, SEED)
    k.set_prefix(g, f"teegra_{tag}")
    cid = f"fni-teegra-{tag}-{int(time.time())}"
    pid = k.queue_graph(g, cid)
    print(f"[{tag}] queued prompt_id={pid}", flush=True)
    files = k.wait_and_download(g, pid, OUT)
    print(f"[{tag}] -> {files}", flush=True)

print("BATCH DONE", flush=True)