# Scene 10 ledger implementation plan

> **For implementer:** Use TDD throughout. Write failing test first. Watch it fail. Then implement.

**Goal:** Turn three VLM passes on a mid-film window into a trait ledger and cluster ids for Roliel's cottage, then stop for a human name map before chunking.

**Architecture:** Pure functions in `core/ledger.py` and `core/cluster.py`. The VLM runner is a script that calls existing `describe_*` functions and writes JSONL. `group_shots` is not modified. Chunk JSON is a later task that refuses to run without a name map.

**Tech stack:** Python 3.11, pytest, existing `core/vlm_correlate.py`, LM Studio at `http://127.0.0.1:1234/v1`, model `qwen3-vl-8b-instruct-abliterated-v2.0@f16`.

**Design:** `docs/plans/2026-09-21-scene10-ledger-design.md`

---

### Task 1: Trait normalizer

**Files:**
- Create: `E:/FNI/core/ledger.py`
- Test: `E:/FNI/tests/test_ledger.py`

**Step 1: Write the failing test**

```python
from core.ledger import normalize_location, normalize_person, is_unreliable


def test_location_collapses_ice_cave_synonyms():
    assert normalize_location("Ice cave") == "ice_cave"
    assert normalize_location("icy cavern") == "ice_cave"


def test_location_cottage_family():
    assert normalize_location("wooden cabin interior") == "cottage"
    assert normalize_location("cottage") == "cottage"


def test_person_tokens_are_sorted_and_stable():
    a = normalize_person({"sex": "female", "hair": "long black", "clothing": "purple top"})
    b = normalize_person({"sex": "Female", "hair": "long, black", "clothing": "purple top"})
    assert a == b
    assert "hair:long_black" in a


def test_identical_people_are_unreliable():
    people = [
        {"sex": "male", "clothing": "black loincloth"},
        {"sex": "male", "clothing": "black loincloth"},
    ]
    assert is_unreliable(3, 0, people) is True


def test_distinct_people_are_reliable():
    people = [
        {"sex": "female", "hair": "long black"},
        {"sex": "male", "hair": "blond"},
    ]
    assert is_unreliable(1, 1, people) is False
```

**Step 2: Run test — confirm it fails**

Command: `cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_ledger.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.ledger'`

**Step 3: Write minimal implementation**

`normalize_location` lowercases, strips punctuation, and maps a small synonym table (`ice cave`, `icy cavern` → `ice_cave`; `cabin`, `cottage`, `wooden cabin interior` → `cottage`). Unknown locations become a slug of the noun phrase, not empty, unless the input is empty.

`normalize_person` emits a frozenset of `field:slug` tokens for sex, hair, clothing, build, props. Empty fields are omitted.

`is_unreliable` is true when count_men + count_women >= 2 and every normalized person token-set is identical, or when the count is positive and `people` is empty.

**Step 4: Run test — confirm it passes**

Command: `cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_ledger.py -q`
Expected: PASS

**Step 5: Commit**

Skip if `E:/FNI` is not a git repo. Do not `git init`.

---

### Task 2: Cluster recurring bodies

**Files:**
- Create: `E:/FNI/core/cluster.py`
- Test: `E:/FNI/tests/test_cluster.py`

**Step 1: Write the failing test**

```python
from core.cluster import cluster_people


def test_same_signature_across_shots_is_one_cluster():
    rows = [
        {"shot_id": "shot:1", "people_unreliable": False, "people_tokens": [["hair:red", "sex:female"]]},
        {"shot_id": "shot:2", "people_unreliable": False, "people_tokens": [["hair:red", "sex:female"]]},
        {"shot_id": "shot:3", "people_unreliable": False, "people_tokens": [["hair:blond", "sex:male"]]},
    ]
    clusters = cluster_people(rows)
    assert len(clusters) == 2
    red = next(c for c in clusters if "hair:red" in c["signature"])
    assert red["shot_ids"] == ["shot:1", "shot:2"]


def test_unreliable_rows_do_not_vote():
    rows = [
        {"shot_id": "shot:9", "people_unreliable": True, "people_tokens": [["hair:red", "sex:female"]]},
    ]
    assert cluster_people(rows) == []
```

**Step 2: Run test — confirm it fails**

Command: `cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_cluster.py -q`
Expected: FAIL — no module `core.cluster`

**Step 3: Write minimal implementation**

`cluster_people` groups identical token-sets. A signature seen once still gets a cluster (Otwa may be rare). Unreliable rows are skipped. Cluster ids are `person_01` upward, stable sorted by signature then first shot_id.

**Step 4: Run test — confirm it passes**

Command: `cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_cluster.py tests/test_ledger.py -q`
Expected: PASS

**Step 5: Commit**

Skip if not a git repo.

---

### Task 3: Slice selection

**Files:**
- Create: `E:/FNI/core/scene_slice.py`
- Test: `E:/FNI/tests/test_scene_slice.py`

**Step 1: Write the failing test**

```python
from core.scene_slice import cottage_shot_ids


def test_keeps_cottage_and_drops_ice():
    rows = [
        {"shot_id": "shot:1", "location_token": "cottage"},
        {"shot_id": "shot:2", "location_token": "cottage"},
        {"shot_id": "shot:3", "location_token": "ice_cave"},
    ]
    assert cottage_shot_ids(rows) == ["shot:1", "shot:2"]
```

**Step 2: Run test — confirm it fails**

Command: `cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_scene_slice.py -q`
Expected: FAIL — no module

**Step 3: Write minimal implementation**

`cottage_shot_ids` returns shot ids whose `location_token` is `cottage`, in input order. No other scene families in this task.

**Step 4: Run test — confirm it passes**

Command: `cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_scene_slice.py -q`
Expected: PASS

---

### Task 4: Chunk labels from cluster ids

**Files:**
- Test: `E:/FNI/tests/test_chunker.py` (append, do not rewrite)
- Modify: none, unless a test exposes a bug in `core/chunker.py`

**Step 1: Write the failing test**

```python
def test_cluster_ids_split_on_person_change():
    shots = [
        {"shot_id": "shot:1", "start_pts": 0, "end_pts": 100},
        {"shot_id": "shot:2", "start_pts": 100, "end_pts": 200},
    ]
    labels = {
        "shot:1": {"location": "cottage", "characters": ["person_01"]},
        "shot:2": {"location": "cottage", "characters": ["person_02"]},
    }
    chunks = group_shots(shots, labels)
    assert len(chunks) == 2
```

**Step 2: Run test — confirm behavior**

Command: `cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_chunker.py::test_cluster_ids_split_on_person_change -q`
Expected: PASS if current `_same_space` already treats disjoint character lists as a split. If it fails, fix `core/chunker.py` only enough to match the existing docstring.

**Step 3: Full unit suite**

Command: `cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/ -q`
Expected: all pass

---

### Task 5: Ledger runner script (not a unit test)

**Files:**
- Create: `E:/FNI/run_scene10_ledger.py`

Do not run this until Tasks 1–4 are green.

Script behavior:

- Read `E:/FNI/shots.jsonl`.
- Window: shots whose midpoint is between 35 and 55 minutes (`pts / 24000 / 60`).
- For each shot, load up to 3 stills from `E:/FNI/stills/full/{shot_id with colon replaced by underscore}_f*.jpg`.
- Call `describe_people`, `describe_location`, `describe_creatures` with model `qwen3-vl-8b-instruct-abliterated-v2.0@f16`.
- Normalize. Append one JSON object per shot to `E:/FNI/manifests/scene10_ledger.jsonl`.
- Flush after every shot so a crash keeps progress.
- After the window, call `cluster_people` and write `E:/FNI/manifests/scene10_clusters.json`.
- Print cluster count and stop. Do not write chunks. Do not call ComfyUI.

**Verify:** script imports, and `pytest tests/ -q` still passes. A live VLM run is a separate user-approved step because it occupies the 4090 for a long time.

---

## Execution notes for subagents

- Work only in `E:/FNI`. Python is `.venv/Scripts/python.exe`.
- Do not start ComfyUI. Do not call `http://127.0.0.1:8188`.
- Do not edit `config.yaml`. Do not `git init`.
- Do not invent character names in code. Name map is a later human file.
- Pin no extra models. VLM calls, if any, use the model string above.
- One task per subagent. Parent reviews before the next task.
