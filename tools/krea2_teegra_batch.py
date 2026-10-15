#!/usr/bin/env python
"""Teegra Krea2 still batch — isolate LoRA strength, fixed seed.

Configs (all same seed 82036621553915, same prompt except the jada trigger word
dropped when jada is off):
  1. jada ON @1.0  + retro-fantasy @1.0   (baseline, as the saved workflow shipped)
  2. jada OFF      + retro-fantasy @1.0   (text-only Teegra — the prior "char LoRA off" fix)
  3. jada OFF      + retro-fantasy @0.8   (gentler style)
  4. jada @0.4     + retro-fantasy @1.0   (weak identity anchor)
"""
import sys, os, time
sys.path.insert(0, r"E:/FNI")
sys.path.insert(0, r"E:/FNI/tools")
import krea2_stills as k

WF = r"C:/Users/gsfny/Downloads/ComfyUI_00108_.json"
OUT = r"E:/FNI/renders/5090/teegra-stills"
SEED = 82036621553915

PRE_WITH_JADA = "retr0fantasy, 60s Soviet fantasy-film, subtle film grain, aged theatrical print quality, caucasian, rlyjada,"
PRE_NO_JADA = "retr0fantasy, 60s Soviet fantasy-film, subtle film grain, aged theatrical print quality, caucasian,"

CONFIGS = [
    ("c1_jada1_retro1", 1.0, 1.0, PRE_WITH_JADA),
    ("c2_jadaOFF_retro1", 0.0, 1.0, PRE_NO_JADA),
    ("c3_jadaOFF_retro08", 0.0, 0.8, PRE_NO_JADA),
    ("c4_jada04_retro1", 0.4, 1.0, PRE_WITH_JADA),
]

for tag, jada_s, retro_s, pre in CONFIGS:
    g = k.load_workflow(WF)
    k.set_prompt(g, pre=pre)
    k.set_lora(g, "lora_1", on=(jada_s > 0), strength=jada_s)
    k.set_lora(g, "lora_7", on=(retro_s > 0), strength=retro_s)
    k.set_seed(g, SEED)
    k.set_prefix(g, f"teegra_{tag}")
    cid = f"fni-teegra-{tag}-{int(time.time())}"
    pid = k.queue_graph(g, cid)
    print(f"[{tag}] queued prompt_id={pid}", flush=True)
    files = k.wait_and_download(g, pid, OUT)
    print(f"[{tag}] -> {files}", flush=True)

print("BATCH DONE", flush=True)