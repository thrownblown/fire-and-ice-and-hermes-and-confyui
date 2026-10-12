window.PROJECTDATA = {
 "generated": "2026-10-12T09:00:46-05:00",
 "counts": {
  "shots": 1308,
  "chunks": 494,
  "captions": 994,
  "scenes": 34,
  "shot_setup": 1308,
  "renders": 494,
  "qc_pass": 494,
  "qc_fail": 0,
  "qc_warn": 0,
  "stitched": 34,
  "film_scenes": 25,
  "gap_scenes": 9,
  "test_runs": 7,
  "test_pending": 5
 },
 "status": [
  {
   "id": "extract",
   "name": "Extraction & chop",
   "state": "done",
   "note": "Whole film cut into frame-exact per-shot clips, stills, and audio stems.",
   "detail": "1308 shots. 3924 stills (3/shot). Per-shot audio stems + one 81-min 48k stereo master bed. Master source never touched."
  },
  {
   "id": "chunk",
   "name": "Chunking",
   "state": "active",
   "note": "Shots packed into 15s-capped chunks. 10 shots are OVER the cap and need real splits.",
   "detail": "Hard 15s cap -> 494 chunks. OVER shots (need splitting before a re-render): S01 shot:00004 is a 73s montage, plus others in S11/S14/S16."
  },
  {
   "id": "render",
   "name": "Render (fullrun)",
   "state": "done",
   "note": "Every chunk rendered and downloaded from the 5090.",
   "detail": "603MB of output. 34 stitched scenes: 25 film scenes + 9 gap scenes G01-G09. Scene 10 is the one hole — see its own status item."
  },
  {
   "id": "qc",
   "name": "QC",
   "state": "done",
   "note": "Black/frozen/silent checks on all rendered chunks.",
   "detail": "Verdicts: PASS = no black >=30%, no frozen >=40%, no near-silent dialogue. Failures get a fresh-seed retake (t02)."
  },
  {
   "id": "s10",
   "name": "Scene 10 (S10)",
   "state": "blocked",
   "note": "No renders — gap in the pipeline.",
   "detail": "Separate approach: run_scene10_ledger.py + manifests/scene10_ledger.jsonl. Awaits an approach decision (see Decisions)."
  },
  {
   "id": "continuity",
   "name": "Continuity (SSIM)",
   "state": "done",
   "note": "Setup/chain clustering across shots so cross-cut scenes prompt coherently.",
   "detail": "core/continuity.py. Thresholds calibrated on S02/S03 (setup 0.42, chain 0.45). Cross-cut scenes: S06, S11 (81 shots / 41 setups), S17, G03, G04, G08."
  },
  {
   "id": "tests",
   "name": "Test runs",
   "state": "active",
   "note": "A/B experiments on the S03 pilot (and S02 continuity).",
   "detail": "T0001-T0009. Two judged, several still awaiting a look — see Decisions."
  },
  {
   "id": "stylelora",
   "name": "Style-LoRA",
   "state": "active",
   "note": "Train a style LoRA so the film reads Frazetta-painting rather than comic.",
   "detail": "Plan A = 1983 comic/cel (3924 free stills). Plan B = Frazetti oil (gated on approved styled sheets). Decision: do BOTH; three-way eval (no-LoRA vs comic vs painting) on the same chunk+seed. Toolkit: Musubi-Tuner minimax-h3 fork, Ostris v3, rank 8, ~500 steps."
  },
  {
   "id": "audio",
   "name": "Audio mix plan",
   "state": "pending",
   "note": "How voices get into the final picture.",
   "detail": "Plan A = original master audio over rendered video. Plan B = H3-cloned voices via ~4s vocal refs (RefMods). Plan C = mix of stems. Decision pending."
  },
  {
   "id": "assembly",
   "name": "Final assembly",
   "state": "pending",
   "note": "Order + audio mix that turns stitched scenes into the film.",
   "detail": "Waiting on the audio plan and continuity decisions. A/B/C mix + non-chronological reassembly for cross-cut scenes."
  }
 ],
 "decisions": [
  {
   "id": "sheet-verdicts",
   "name": "Character sheet verdicts",
   "category": "Looks",
   "state": "open",
   "owner": "Alex",
   "question": "Pick the winning sheet among the seeded variants for Juliana / Nekron / Darkwolf.",
   "context": "23 sheets in library/char/sheet-runs/output/ (Juliana 7, Nekron 7, Darkwolf 9). Darkwolf 'more Frazetta less Bakshi' test has 6 wording variants.",
   "docs": [
    {
     "path": "library/char/sheet-runs/seeds.tsv",
     "text": "JULIANA\tr01\t192149586045640\t464ef971-2d6a-4b32-8ac2-8ea23a01cf47\nJULIANA\tr02\t21503314931539\t09d2e953-02fc-477c-a54f-14a0d2454d47\nJULIANA\tr03\t271429320906394\tc267ebc1-9a8f-4bf1-8adc-b951934bb5d1\nJULIANA\tr04\t177602191217894\tdbfcab07-0b03-4a06-a443-b5cd308d63fc\nJULIANA\tr05\t8099065698678\t671ec068-b8ad-49b9-94a0-57f80d74421b\nJULIANA\tr06\t192861247604610\t5c642fde-61c2-4c2f-baf3-0417154b1457\nNEKRON\tr01\t125983969218008\t12851717-1783-4e5a-8497-9439a8c32dc7\nNEKRON\tr02\t146153319450114\ta979195a-c018-484f-8c44-6999b5efe5fd\nNEKRON\tr03\t14016473657517\t11733e26-f9f6-4df1-941f-929651080ddb\nNEKRON\tr04\t32267604974111\t94cb7a4a-7f6d-4a3c-a3a5-f89d8b29272c\nNEKRON\tr05\t133464339763468\t06e5c769-b199-46d6-b1de-e9f0d251ba97\nNEKRON\tr06\t255904812536275\t181702ec-d69b-49c7-85fc-0161a62c445e\nDARKWOLF\tp01\t218707532452351\t067ec2f9-4f84-4f0b-a1f9-7258479dac01\tfrazetta_death_dealer_front.jpeg\nDARKWOLF\tp02\t47779804761695\t993fae23-e3ca-4ebb-afca-c281d6f96d9f\tfrazetta_death_dealer_axe_raised.jpeg\nDARKWOLF\tp03\t243419032513151\tcb891d2a-44ec-4176-93da-bdfd9f934adc\tfrazetta_death_dealer_red_eyes.jpeg\nDARKWOLF\tv1_drop_ink\t218707532452351\tdfdd012e-8706-4989-a26d-4ceb23424150\nDARKWOLF\tv2_style_first\t218707532452351\t32b0671d-e13a-4557-9552-64015b36495d\nDARKWOLF\tv3_name_the_painter\t218707532452351\t378c9406-78bc-4740-950a-5a0d10468204\nDARKWOLF\tv4_two_pass_wording\t218707532452351\tef6a3031-8496-45cf-bc70-f45dba3dd4cb\nDARKWOLF\tv5_negative\t218707532452351\t466fe495-7f26-4aeb-9e3e-4ba7ca724b92\nDARKWOLF\tv6_canvas\t218707532452351\t65e18b89-b70a-4fcf-8cd6-3902ffd87b30\n"
    }
   ]
  },
  {
   "id": "teegra-traits",
   "name": "Teegra traits",
   "category": "Looks",
   "state": "open",
   "owner": "Alex",
   "question": "Lock Teegra's earring / pendant / skin / body so sheets (and renders) are consistent.",
   "context": "VLM-reported colors outrank handwritten notes — fix silently, don't flag.",
   "docs": [
    {
     "path": "docs/character_descriptions.md",
     "text": "# Fire & Ice — Character Physical Descriptions (DRAFT for curation)\n\nPhysical-appearance attributes used to map the VLM's observations back to\ncharacter identity. The VLM was not asked to name anyone: free-form naming\ninvented characters and merged distinct people. Identity comes from matching\nthese descriptions against the pass, by hand or by a later rule. A description\nthat fits nobody stays unnamed.\n\n## Leads\n\n- **Larn** — young adult man; athletic/muscular; shoulder-length blond hair;\n  brown loincloth with a gold buckle, arm bands, black boots; often\n  bare-chested; carries a sword. *(Hair confirmed blond on source stills\n  shot:00873 — not dark.)*\n- **Teegra** — young adult woman; pale skin; very long dark hair; slender;\n  light purple two-piece (sleeveless top and skirt), not a fur bikini.\n  The fur-bikini line was wrong.\n- **Darkwolf** (credited as Rescuer, scene 8) — older warrior; very large, heavily\n  muscled; dark/weathered skin; long black hair (often tied back); bare-chested\n  with a loincloth and wrist/ankle bands; carries a sword/axe.\n- **Nekron** — tall, gaunt/pale young man; sharp features; long hair that\n  reads white in the VLM pass (design notes say black); dark robes; staff.\n\n## Supporting (physical appearance TBD — derive from source frames/corpus)\n\n- **Juliana** — Nekron's mother; older woman; dark sorceress robes.\n- **King Jarol** — older king of Fire Keep; gray/white hair and beard; regal robes.\n- **Prince Taro** — Jarol's son, Teegra's brother. TBD.\n- **Roliel** — long red hair; fair skin; red/orange eyes; white flowing robe with\n  a dark belt; blue teardrop-pendant necklace, matching earrings and bracelets.\n  *(Frazetta reference — target design, not film identity.)*\n- **Otwa (Great Otwa)** — Roliel's son; gentle but immensely strong. TBD.\n- **Shaitan** — Teegra's companion at Fire Keep. TBD.\n\n## Groups\n\n- **Subhumans / Nekron's dogs** — ape-like humanoid creatures; hunched; fur-covered;\n  primitive weapons. Group taxonomy; individual tracks assigned later.\n- **Dragonhawk Riders** — Jarol's mounted forces.\n\n## Role labels (until individual identity is established)\n\n- **Envoy**, **Defender Captain** — appearance TBD.\n\n## Creatures\n\n- **Dragonhawks** — flying reptilian mounts. **Giant octopus**, **giant swamp lizard**.\n"
    }
   ]
  },
  {
   "id": "s10-approach",
   "name": "Scene 10 approach",
   "category": "Pipeline",
   "state": "open",
   "owner": "Alex",
   "question": "Decide how to generate S10, the only scene with no renders.",
   "context": "run_scene10_ledger.py + manifests/scene10_ledger.jsonl is the scaffolding; the generation path itself is undecided.",
   "docs": [
    {
     "path": "docs/plans/2026-09-21-scene10-ledger.md",
     "text": "# Scene 10 ledger implementation plan\n\n> **For implementer:** Use TDD throughout. Write failing test first. Watch it fail. Then implement.\n\n**Goal:** Turn three VLM passes on a mid-film window into a trait ledger and cluster ids for Roliel's cottage, then stop for a human name map before chunking.\n\n**Architecture:** Pure functions in `core/ledger.py` and `core/cluster.py`. The VLM runner is a script that calls existing `describe_*` functions and writes JSONL. `group_shots` is not modified. Chunk JSON is a later task that refuses to run without a name map.\n\n**Tech stack:** Python 3.11, pytest, existing `core/vlm_correlate.py`, LM Studio at `http://127.0.0.1:1234/v1`, model `qwen3-vl-8b-instruct-abliterated-v2.0@f16`.\n\n**Design:** `docs/plans/2026-09-21-scene10-ledger-design.md`\n\n---\n\n### Task 1: Trait normalizer\n\n**Files:**\n- Create: `E:/FNI/core/ledger.py`\n- Test: `E:/FNI/tests/test_ledger.py`\n\n**Step 1: Write the failing test**\n\n```python\nfrom core.ledger import normalize_location, normalize_person, is_unreliable\n\n\ndef test_location_collapses_ice_cave_synonyms():\n    assert normalize_location(\"Ice cave\") == \"ice_cave\"\n    assert normalize_location(\"icy cavern\") == \"ice_cave\"\n\n\ndef test_location_cottage_family():\n    assert normalize_location(\"wooden cabin interior\") == \"cottage\"\n    assert normalize_location(\"cottage\") == \"cottage\"\n\n\ndef test_person_tokens_are_sorted_and_stable():\n    a = normalize_person({\"sex\": \"female\", \"hair\": \"long black\", \"clothing\": \"purple top\"})\n    b = normalize_person({\"sex\": \"Female\", \"hair\": \"long, black\", \"clothing\": \"purple top\"})\n    assert a == b\n    assert \"hair:long_black\" in a\n\n\ndef test_identical_people_are_unreliable():\n    people = [\n        {\"sex\": \"male\", \"clothing\": \"black loincloth\"},\n        {\"sex\": \"male\", \"clothing\": \"black loincloth\"},\n    ]\n    assert is_unreliable(3, 0, people) is True\n\n\ndef test_distinct_people_are_reliable():\n    people = [\n        {\"sex\": \"female\", \"hair\": \"long black\"},\n        {\"sex\": \"male\", \"hair\": \"blond\"},\n    ]\n    assert is_unreliable(1, 1, people) is False\n```\n\n**Step 2: Run test — confirm it fails**\n\nCommand: `cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_ledger.py -q`\nExpected: FAIL — `ModuleNotFoundError: No module named 'core.ledger'`\n\n**Step 3: Write minimal implementation**\n\n`normalize_location` lowercases, strips punctuation, and maps a small synonym table (`ice cave`, `icy cavern` → `ice_cave`; `cabin`, `cottage`, `wooden cabin interior` → `cottage`). Unknown locations become a slug of the noun phrase, not empty, unless the input is empty.\n\n`normalize_person` emits a frozenset of `field:slug` tokens for sex, hair, clothing, build, props. Empty fields are omitted.\n\n`is_unreliable` is true when count_men + count_women >= 2 and every normalized person token-set is identical, or when the count is positive and `people` is empty.\n\n**Step 4: Run test — confirm it passes**\n\nCommand: `cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_ledger.py -q`\nExpected: PASS\n\n**Step 5: Commit**\n\nSkip if `E:/FNI` is not a git repo. Do not `git init`.\n\n---\n\n### Task 2: Cluster recurring bodies\n\n**Files:**\n- Create: `E:/FNI/core/cluster.py`\n- Test: `E:/FNI/tests/test_cluster.py`\n\n**Step 1: Write the failing test**\n\n```python\nfrom core.cluster import cluster_people\n\n\ndef test_same_signature_across_shots_is_one_cluster():\n    rows = [\n        {\"shot_id\": \"shot:1\", \"people_unreliable\": False, \"people_tokens\": [[\"hair:red\", \"sex:female\"]]},\n        {\"shot_id\": \"shot:2\", \"people_unreliable\": False, \"people_tokens\": [[\"hair:red\", \"sex:female\"]]},\n        {\"shot_id\": \"shot:3\", \"people_unreliable\": False, \"people_tokens\": [[\"hair:blond\", \"sex:male\"]]},\n    ]\n    clusters = cluster_people(rows)\n    assert len(clusters) == 2\n    red = next(c for c in clusters if \"hair:red\" in c[\"signature\"])\n    assert red[\"shot_ids\"] == [\"shot:1\", \"shot:2\"]\n\n\ndef test_unreliable_rows_do_not_vote():\n    rows = [\n        {\"shot_id\": \"shot:9\", \"people_unreliable\": True, \"people_tokens\": [[\"hair:red\", \"sex:female\"]]},\n    ]\n    assert cluster_people(rows) == []\n```\n\n**Step 2: Run test — confirm it fails**\n\nCommand: `cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_cluster.py -q`\nExpected: FAIL — no module `core.cluster`\n\n**Step 3: Write minimal implementation**\n\n`cluster_people` groups identical token-sets. A signature seen once still gets a cluster (Otwa may be rare). Unreliable rows are skipped. Cluster ids are `person_01` upward, stable sorted by signature then first shot_id.\n\n**Step 4: Run test — confirm it passes**\n\nCommand: `cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_cluster.py tests/test_ledger.py -q`\nExpected: PASS\n\n**Step 5: Commit**\n\nSkip if not a git repo.\n\n---\n\n### Task 3: Slice selection\n\n**Files:**\n- Create: `E:/FNI/core/scene_slice.py`\n- Test: `E:/FNI/tests/test_scene_slice.py`\n\n**Step 1: Write the failing test**\n\n```python\nfrom core.scene_slice import cottage_shot_ids\n\n\ndef test_keeps_cottage_and_drops_ice():\n    rows = [\n        {\"shot_id\": \"shot:1\", \"location_token\": \"cottage\"},\n        {\"shot_id\": \"shot:2\", \"location_token\": \"cottage\"},\n        {\"shot_id\": \"shot:3\", \"location_token\": \"ice_cave\"},\n    ]\n    assert cottage_shot_ids(rows) == [\"shot:1\", \"shot:2\"]\n```\n\n**Step 2: Run test — confirm it fails**\n\nCommand: `cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_scene_slice.py -q`\nExpected: FAIL — no module\n\n**Step 3: Write minimal implementation**\n\n`cottage_shot_ids` returns shot ids whose `location_token` is `cottage`, in input order. No other scene families in this task.\n\n**Step 4: Run test — confirm it passes**\n\nCommand: `cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_scene_slice.py -q`\nExpected: PASS\n\n---\n\n### Task 4: Chunk labels from cluster ids\n\n**Files:**\n- Test: `E:/FNI/tests/test_chunker.py` (append, do not rewrite)\n- Modify: none, unless a test exposes a bug in `core/chunker.py`\n\n**Step 1: Write the failing test**\n\n```python\ndef test_cluster_ids_split_on_person_change():\n    shots = [\n        {\"shot_id\": \"shot:1\", \"start_pts\": 0, \"end_pts\": 100},\n        {\"shot_id\": \"shot:2\", \"start_pts\": 100, \"end_pts\": 200},\n    ]\n    labels = {\n        \"shot:1\": {\"location\": \"cottage\", \"characters\": [\"person_01\"]},\n        \"shot:2\": {\"location\": \"cottage\", \"characters\": [\"person_02\"]},\n    }\n    chunks = group_shots(shots, labels)\n    assert len(chunks) == 2\n```\n\n**Step 2: Run test — confirm behavior**\n\nCommand: `cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_chunker.py::test_cluster_ids_split_on_person_change -q`\nExpected: PASS if current `_same_space` already treats disjoint character lists as a split. If it fails, fix `core/chunker.py` only enough to match the existing docstring.\n\n**Step 3: Full unit suite**\n\nCommand: `cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/ -q`\nExpected: all pass\n\n---\n\n### Task 5: Ledger runner script (not a unit test)\n\n**Files:**\n- Create: `E:/FNI/run_scene10_ledger.py`\n\nDo not run this until Tasks 1–4 are green.\n\nScript behavior:\n\n- Read `E:/FNI/shots.jsonl`.\n- Window: shots whose midpoint is between 35 and 55 minutes (`pts / 24000 / 60`).\n- For each shot, load up to 3 stills from `E:/FNI/stills/full/{shot_id with colon replaced by underscore}_f*.jpg`.\n- Call `describe_people`, `describe_location`, `describe_creatures` with model `qwen3-vl-8b-instruct-abliterated-v2.0@f16`.\n- Normalize. Append one JSON object per shot to `E:/FNI/manifests/scene10_ledger.jsonl`.\n- Flush after every shot so a crash keeps progress.\n- After the window, call `cluster_people` and write `E:/FNI/manifests/scene10_clusters.json`.\n- Print cluster count and stop. Do not write chunks. Do not call ComfyUI.\n\n**Verify:** script imports, and `pytest tests/ -q` still passes. A live VLM run is a separate user-approved step because it occupies the 4090 for a long time.\n\n---\n\n## Execution notes for subagents\n\n- Work only in `E:/FNI`. Python is `.venv/Scripts/python.exe`.\n- Do not start ComfyUI. Do not call `http://127.0.0.1:8188`.\n- Do not edit `config.yaml`. Do not `git init`.\n- Do not invent character names in code. Name map is a later human file.\n- Pin no extra models. VLM calls, if any, use the model string above.\n- One task per subagent. Parent reviews before the next task.\n"
    }
   ]
  },
  {
   "id": "t0003-t0005",
   "name": "T0003-T0005 verdicts",
   "category": "Test runs",
   "state": "open",
   "owner": "Alex",
   "question": "Watch the FL2VA variants (T0003 first/last stills, T0004 motion-path, T0005 action) and pick a rendering mode.",
   "context": "These three decide whether the full run's FL2VA mode is right. Watch in index.html?view=tests.",
   "docs": [
    {
     "path": "docs/test-runs-plan.md",
     "text": "# Test Runs + Final Deliverable Plan\n\n*2026-09-27. For Hermes (4090, can reach the 5090). GhstClwd can't reach the LAN from Discord, so Hermes executes.*\n\n## Final product (redefined)\nThe deliverable is **not** finished video. It's a **chunk pack**: for every chunk, a full H3 prompt plus a prepared set of input refs, Frazetta-oil-styled and blocked to the shot. Generation is then done semi-manually per chunk.\n\n## Naming convention\nEverything keys off one ID: **`sNN-cMM`** (scene from the beat sheet, chunk within the scene, zero-padded, no gaps).\n\n```\nFNI/\n  chunks/\n    s03-c01/\n      prompt.txt                  # final H3 prompt (ref2v)\n      chunk.md                    # lines, speakers, source timecodes, prev/next, shot list\n      src/  s03-c01_src_sh00064_mid.jpg ...        # original frames (read-only)\n      refs/ s03-c01_ref_JULIANA_01.png             # prepared input refs\n            s03-c01_ref_LOC_icepeak-throne.png\n            s03-c01_ref_BLOCK_sh1.png              # blocked composition per shot\n  library/                         # reusable across chunks\n    char/   JULIANA_sheet_v01.png  NEKRON_sheet_v01.png\n    loc/    LOC_icepeak-throne_v01.png\n  runs/\n    T0001_s03_ref2v-srcstills/     # one folder per test run\n      manifest.md\n      s03-c01_T0001_t01.mp4\n      s03-c02_T0001_t01.mp4\n      s03_T0001_stitched.mp4\n```\n\n**Rules**\n- Test run ID: `T####`, sequential, never reused. Folder = `T####_<scope>_<method-slug>`.\n- Render file: `<chunk>_<T####>_t<take>.mp4`. Sorting by name = story order, so the stitch is `ls | sort | concat`.\n- Library assets are versioned `_v01`, `_v02`. A chunk's refs record which library version they came from in `chunk.md`.\n- `manifest.md` per run: date, method, model/workflow, settings, chunk list, which refs, verdict (✅ / ❌ / notes). Alex fills in the verdict after watching.\n- `runs/INDEX.md`: one row per T#### (id, scope, method, verdict). This is the scoreboard.\n\n## Test matrix (S03 first, then one action scene)\n| Test | Method | Question it answers |\n|---|---|---|\n| T0001 | ref2v, **original stills** as refs | Does v3 prompt structure fix plot/speakers? (baseline) |\n| T0002 | ref2v, **Frazetta-styled character sheets** as refs | Does style transfer on refs carry into H3 motion? |\n| T0003 | ref2v, **styled sheets + styled location plate + blocking frame** | Does blocking hold composition/staging? |\n| T0004 | **V2V** low adherence from source clip + styled refs | Is V2V better for action-heavy chunks? |\n| T0005 | best of above on an **action scene** (S14 camp raid) | Does it survive fights and motion? |\n\nSame chunks, same seed where possible, one variable changed per test. Watch S03 stitched after each one.\n\n## Ref prep: where the 222-chunk job gets automated\nIt isn't 222 × hand work. It's three layers:\n\n1. **Character sheets (~10–15, manual, done once).** Edit model: source still → Frazetta oil style. Alex approves. Front/3-4/profile if possible. These go in `library/char/`.\n2. **Location plates (~15, semi-manual, done once).** One per canonical location from the beat sheet (Ice Peak throne hall, Fire Keep hall, Roliel's hut, jungle, ...). Source background frame → Frazetta oil, no characters.\n3. **Blocking frames (per shot, automated + human QA).** Edit model inputs: source mid-frame (for pose and composition) + character sheet(s) + location plate → Frazetta-styled frame matching the original staging. Batch it on the 5090 via ComfyUI and produce a contact sheet per scene. Alex rejects bad ones and only those re-run.\n\nLayers 1–2 are the only real manual effort. Layer 3 is a queue plus a thumbs-up/down review.\n\n**Automation candidates later:** auto-pick the best source mid-frame per shot (sharpness, fewest captions), auto-crop characters for sheets, a contact-sheet review where you tick rejects and it re-queues only those.\n\n## Style note\nFrazetta image gen was uncanny before because it was **text-only generation**. Style *transfer* from real frames (pose/composition locked) is a different, easier problem. T0002 tells us fast whether it works.\n\n## Don't\n- Batch-render all 222 before T0001–T0003 have verdicts\n- Change more than one variable per test\n- Overwrite a render or reuse a T#### number\n"
    }
   ]
  },
  {
   "id": "t0008-audio",
   "name": "T0008 audio (plan A baseline)",
   "category": "Audio",
   "state": "open",
   "owner": "Alex",
   "question": "Audition original audio over T0001 video — how bad is the lip-sync mismatch really?",
   "context": "Free to build, nothing rendered. Per-chunk overlays from audio/master_audio_48k_stereo.wav.",
   "docs": [
    {
     "path": "docs/audio-plan.md",
     "text": "# Audio / Voice Plan\n\n*2026-09-27. Decide by testing, not by arguing. Both paths are cheap because the SRT gives exact timecodes for every line.*\n\n## Options\n| | Approach | Pros | Cons |\n|---|---|---|---|\n| **A** | **Original audio laid over the generated video.** Mute H3 audio; use the film's audio for the chunk's source timecode. | Real performances and real score, zero voice work, and timing already matches since chunks are cut to source timecodes | Lip sync won't match the new animation (rotoscope style is forgiving); can't do new lines (cut Darkwolf ending, alt Larn) |\n| **B** | **H3 audio reference.** Feed per-character voice samples (from the film) as audio refs; H3 generates the dialogue. | Lip sync matches; works for new/cut lines; consistent per character | Voices drift; delivery is weaker than the actors; music has to be handled separately |\n| **C** | **Hybrid.** H3 generates with voice refs for lip sync, then the final mix swaps in the **original dialogue stem** where it exists, and keeps H3 voice only for new lines. | Best of both | Two passes, more mixing |\n\n**Likely winner:** C, falling back to A for dialogue-heavy scenes if H3 lip sync is weak. B only for lines that don't exist in the film.\n\n## Step 1: Stem separation (once, whole film)\nRun Demucs or UVR (MDX/Kim vocal model) on the full audio track on the 5090:\n- `audio/stems/dialogue.wav`: voices\n- `audio/stems/music_sfx.wav`: score + effects\n\nThis makes A and C clean. The score becomes its own layer (non_diegetic_music becomes real, not described).\n\n## Step 2: Voice sample library (from the SRT, automated)\nFor each character, auto-cut every HIGH-confidence line from `dialogue.wav` using the timeline timecodes (±0.15s padding):\n```\naudio/lines/L024_JULIANA.wav\naudio/lines/L025_NEKRON.wav\n...\n```\nThen Alex picks the **3–5 cleanest per character** (no music bleed, no overlap, emotional range) and puts them in:\n```\nlibrary/voice/JULIANA_ref_01.wav ... (10–30s total per character)\n```\nContact sheet: `audio/voice-review.md` lists each character's candidate clips with line text and duration, so Alex listens and ticks the ones to keep.\n\nCharacters with enough lines for a solid sample: Larn, Teegra, Nekron, Juliana, Darkwolf, Jarol, Taro, Roliel, Spirit. Minor ones (Tutor, Envoy) can use whatever exists.\n\n## Step 3: Per-chunk audio assets\nEvery chunk folder gets:\n```\nchunks/s03-c01/audio/\n  s03-c01_orig_full.wav        # original mix for the chunk's source window\n  s03-c01_orig_dialogue.wav    # dialogue stem, same window\n  s03-c01_orig_music.wav       # music/sfx stem, same window\n```\nThe prompt's voice refs point to `library/voice/<CHAR>_ref_*.wav` for the speakers in that chunk.\n\n## Tests (add to the test-runs matrix)\n| Test | Method |\n|---|---|\n| T0006 | S03, H3 with **voice refs** (B). Is lip sync and voice identity good enough? |\n| T0007 | S03, same video as T0006, **original dialogue + music stems** overlaid (C). Compare side by side. |\n| T0008 | S03, **original full mix** over T0001 video (A). Baseline. |\n\nAlex watches all three stitched. Verdict decides the default per scene type (dialogue vs action).\n\n## New lines (no source audio)\n- **Cut Darkwolf ending** (Juliana: \"You came back.\" / \"What have we done to our children?\", Darkwolf, Nekron's death scream): H3 voice refs from the samples, or a voice-cloning TTS trained on the same samples. Mix under the original score style.\n- **Alt fem Larn:** no source voice. Pick or design a voice (low, husky, calm), make 3–5 reference clips with TTS/voice design, and store them as `library/voice/LARN_F_ref_*.wav`.\n\n## Note\nCloned voices of the original actors are fine for a personal project. Think twice before publishing anything that puts new words in real actors' voices.\n"
    }
   ]
  },
  {
   "id": "t0009-continuity",
   "name": "T0009 continuity verdict",
   "category": "Test runs",
   "state": "open",
   "owner": "Alex",
   "question": "Continuity-packed (SSIM chains/setups) vs chronological packing — which reads better?",
   "context": "6/6 segments rendered + stitched, both audio overlays built (S02_continuity_audioA vs S02_chronological_audioA). Compare glacier chains 17->18 and 24->25."
  },
  {
   "id": "over-splits",
   "name": "OVER-shot splits",
   "category": "Pipeline",
   "state": "open",
   "owner": "Alex",
   "question": "Split the 10 shots flagged OVER the 15s cap into renderable pieces.",
   "context": "S01 shot:00004 (73s montage) is the worst, plus others in S11/S14/S16."
  }
 ]
};
