import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "vlm_character_pass", ROOT / "tools" / "vlm_character_pass.py")
mod = importlib.util.module_from_spec(_spec)
sys.modules["vlm_character_pass"] = mod
_spec.loader.exec_module(mod)

from core.vlm_charpass import LENSES  # noqa: E402


def make_jpeg(path, color="red", size=(64, 48)):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, "JPEG")
    return path


@pytest.fixture
def fake_root(tmp_path):
    """tmp repo root with refs/characters/TUTOR/{a,b}.jpg"""
    cdir = tmp_path / "refs" / "characters" / "TUTOR"
    make_jpeg(cdir / "a.jpg", "red")
    make_jpeg(cdir / "b.jpg", "blue")
    return tmp_path


class FakeTransport:
    """Records calls; scripted responses: list of str results or exceptions."""

    def __init__(self, script=None, default='{"ok": true}'):
        self.script = list(script) if script else []
        self.default = default
        self.calls = []  # (messages, kwargs)

    def __call__(self, messages, **kw):
        self.calls.append((messages, kw))
        if self.script:
            item = self.script.pop(0)
            if isinstance(item, Exception):
                raise item
            return item
        if isinstance(self.default, Exception):
            raise self.default
        return self.default


NO_SLEEP = lambda s: None


def read_ledger(root):
    p = root / "manifests" / "vlm_charpass.jsonl"
    if not p.exists():
        return []
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def run(root, argv_extra, transport):
    return mod.run_pass(argv_extra + ["--root", str(root)], transport=transport, sleep=NO_SLEEP)


# ---- retry ladder -----------------------------------------------------------

def test_retry_ladder_recovers_on_third_attempt(fake_root):
    t = FakeTransport(script=[
        mod.VLMHttpError(500, "boom"),
        mod.VLMHttpError(429, "slow down"),
        '{"color": "red", "length": "short", "texture": "curly", "style": "bald", "notes": ""}',
    ])
    rc = run(fake_root, ["--char", "TUTOR", "--lens", "hair", "--limit", "1"], t)
    assert rc == 0
    assert len(t.calls) == 3
    # temperature 0.0 -> 0.5 and max_tokens 600 -> 900 across the ladder
    temps = [kw["temperature"] for _, kw in t.calls]
    toks = [kw["max_tokens"] for _, kw in t.calls]
    assert temps[0] == 0.0 and abs(temps[-1] - 0.5) < 1e-9
    assert toks[0] == 600 and toks[-1] == 900
    assert len(temps) == 3 and len(toks) == 3
    rows = read_ledger(fake_root)
    assert len(rows) == 1
    assert rows[0]["ok"] is True and rows[0]["attempts"] == 3


def test_retries_exhausted_fails_with_exit_2(fake_root):
    t = FakeTransport(default=mod.VLMHttpError(500, "boom"))
    rc = run(fake_root, ["--char", "TUTOR", "--lens", "hair", "--limit", "1"], t)
    assert rc == 2
    assert len(t.calls) == 3
    rows = read_ledger(fake_root)
    assert len(rows) == 1
    assert rows[0]["ok"] is False
    assert rows[0]["attempts"] == 3
    assert rows[0]["json"] is None


def test_timeout_is_retried(fake_root):
    t = FakeTransport(script=[TimeoutError(), '{"color":"black","length":"long","texture":"straight","style":"loose","notes":""}'])
    rc = run(fake_root, ["--char", "TUTOR", "--lens", "hair", "--limit", "1"], t)
    assert rc == 0
    assert len(t.calls) == 2


# ---- ledger rows -------------------------------------------------------------

def test_ledger_row_shape_and_forward_slashes(fake_root):
    t = FakeTransport(default='{"color":"black","length":"long","texture":"straight","style":"loose","notes":""}')
    rc = run(fake_root, ["--char", "TUTOR", "--lens", "hair", "--limit", "1"], t)
    assert rc == 0
    row = read_ledger(fake_root)[0]
    assert set(row) >= {"ts", "char", "lens", "image", "model", "ok", "attempts", "text", "json"}
    assert "\\" not in row["image"] and "/" in row["image"]
    assert row["char"] == "TUTOR" and row["lens"] == "hair"
    assert row["json"]["color"] == "black"


def test_normalization_failure_keeps_raw_text_json_null(fake_root):
    t = FakeTransport(default="I refuse to answer with JSON.")
    rc = run(fake_root, ["--char", "TUTOR", "--lens", "hair", "--limit", "1"], t)
    assert rc == 2  # a null-normalization answer counts as a failed item
    row = read_ledger(fake_root)[0]
    assert row["ok"] is False
    assert row["text"] == "I refuse to answer with JSON."
    assert row["json"] is None


def test_ledger_is_append_only_across_runs(fake_root):
    t = FakeTransport(default='{"color":"black","length":"long","texture":"straight","style":"loose","notes":""}')
    run(fake_root, ["--char", "TUTOR", "--lens", "hair", "--limit", "1"], t)
    t2 = FakeTransport(default='{"skin":"tan","hair":"black","eyes":"brown","garment_primary":"blue","garment_secondary":null,"metal_accent":null}')
    run(fake_root, ["--char", "TUTOR", "--lens", "colors", "--limit", "1"], t2)
    rows = read_ledger(fake_root)
    assert len(rows) == 2
    assert [r["lens"] for r in rows] == ["hair", "colors"]


# ---- cache --------------------------------------------------------------------

def test_cache_hit_makes_zero_calls_on_rerun(fake_root):
    t = FakeTransport(default='{"color":"black","length":"long","texture":"straight","style":"loose","notes":""}')
    rc1 = run(fake_root, ["--char", "TUTOR", "--lens", "hair", "--limit", "1"], t)
    assert rc1 == 0 and len(t.calls) == 1
    cache = fake_root / "library" / "char" / "vlm-cache" / "TUTOR" / "hair" / "a.jpg.json"
    assert cache.exists()
    t2 = FakeTransport()
    rc2 = run(fake_root, ["--char", "TUTOR", "--lens", "hair", "--limit", "1"], t2)
    assert rc2 == 0
    assert t2.calls == []          # cached row never re-queried
    assert len(read_ledger(fake_root)) == 1   # cache hits do not append rows


def test_cache_invalidated_on_model_change(fake_root):
    t = FakeTransport(default='{"color":"black","length":"long","texture":"straight","style":"loose","notes":""}')
    run(fake_root, ["--char", "TUTOR", "--lens", "hair", "--limit", "1", "--model", "modelA"], t)
    t2 = FakeTransport(default='{"color":"white","length":"long","texture":"straight","style":"loose","notes":""}')
    rc = run(fake_root, ["--char", "TUTOR", "--lens", "hair", "--limit", "1", "--model", "modelB"], t2)
    assert rc == 0 and len(t2.calls) == 1


def test_cache_invalidated_on_file_change(fake_root):
    t = FakeTransport(default='{"color":"black","length":"long","texture":"straight","style":"loose","notes":""}')
    run(fake_root, ["--char", "TUTOR", "--lens", "hair", "--limit", "1"], t)
    img = fake_root / "refs" / "characters" / "TUTOR" / "a.jpg"
    make_jpeg(img, "green", size=(80, 60))   # new size+mtime
    t2 = FakeTransport(default='{"color":"green","length":"long","texture":"straight","style":"loose","notes":""}')
    rc = run(fake_root, ["--char", "TUTOR", "--lens", "hair", "--limit", "1"], t2)
    assert rc == 0 and len(t2.calls) == 1


# ---- dry run / selection --------------------------------------------------------

def test_dry_run_lists_items_without_calling(fake_root, capsys):
    t = FakeTransport()
    rc = mod.run_pass(["--char", "TUTOR", "--lens", "hair", "--dry-run", "--root", str(fake_root)],
                      transport=t, sleep=NO_SLEEP)
    assert rc == 0
    assert t.calls == []
    out = capsys.readouterr().out
    assert "a.jpg" in out and "hair" in out
    assert not read_ledger(fake_root)


def test_dry_run_reports_cache_hits(fake_root):
    t = FakeTransport(default='{"color":"black","length":"long","texture":"straight","style":"loose","notes":""}')
    run(fake_root, ["--char", "TUTOR", "--lens", "hair", "--limit", "1"], t)
    t2 = FakeTransport()
    rc = mod.run_pass(["--char", "TUTOR", "--lens", "hair", "--dry-run", "--root", str(fake_root)],
                      transport=t2, sleep=NO_SLEEP)
    assert rc == 0 and t2.calls == []


def test_all_lenses_when_unspecified(fake_root):
    t = FakeTransport(default='{}')
    rc = run(fake_root, ["--char", "TUTOR", "--limit", "1"], t)
    assert rc == 0
    assert len(t.calls) == len(LENSES)


def test_limit_caps_images_per_char(fake_root):
    t = FakeTransport(default='{"color":"black","length":"long","texture":"straight","style":"loose","notes":""}')
    rc = run(fake_root, ["--char", "TUTOR", "--lens", "hair", "--limit", "1"], t)
    assert rc == 0 and len(t.calls) == 1   # a.jpg only, b.jpg skipped


def test_char_all_expands_to_corpus_dirs(fake_root):
    make_jpeg(fake_root / "refs" / "characters" / "LARN" / "x.jpg")
    t = FakeTransport(default='{"color":"black","length":"long","texture":"straight","style":"loose","notes":""}')
    rc = run(fake_root, ["--char", "all", "--lens", "hair"], t)
    assert rc == 0 and len(t.calls) == 3   # LARN/x + TUTOR/a + TUTOR/b


def test_unknown_char_exits_nonzero(fake_root):
    t = FakeTransport()
    rc = run(fake_root, ["--char", "NOBODY", "--lens", "hair"], t)
    assert rc == 2
    assert t.calls == []


def test_calls_are_serial_in_sorted_order(fake_root):
    t = FakeTransport(default='{"color":"black","length":"long","texture":"straight","style":"loose","notes":""}')
    rc = run(fake_root, ["--char", "TUTOR", "--lens", "hair"], t)
    assert rc == 0
    # each call fully completes before the next (FakeTransport is synchronous);
    # verify item order via ledger rows: a.jpg before b.jpg
    rows = read_ledger(fake_root)
    assert [os.path.basename(r["image"]) for r in rows] == ["a.jpg", "b.jpg"]


def test_messages_carry_lens_instruction_and_image(fake_root):
    t = FakeTransport(default='{"color":"black","length":"long","texture":"straight","style":"loose","notes":""}')
    run(fake_root, ["--char", "TUTOR", "--lens", "hair", "--limit", "1"], t)
    msgs, kw = t.calls[0]
    assert msgs[0]["role"] == "system"
    assert msgs[1]["content"][0]["type"] == "image_url"
    assert "data:image/jpeg;base64," in msgs[1]["content"][0]["image_url"]["url"]
    assert LENSES["hair"]["instruction"] in msgs[1]["content"][1]["text"]
    assert kw["model"] == mod.DEFAULT_MODEL


# ---- extra edge cases ---------------------------------------------------------

def test_failed_item_writes_no_cache_and_retries_on_rerun(fake_root):
    t = FakeTransport(default=mod.VLMHttpError(500, "boom"))
    rc = run(fake_root, ["--char", "TUTOR", "--lens", "hair", "--limit", "1"], t)
    assert rc == 2
    cache = fake_root / "library" / "char" / "vlm-cache" / "TUTOR" / "hair" / "a.jpg.json"
    assert not cache.exists()
    # rerun with a healthy transport: item is attempted again (not treated as cached)
    t2 = FakeTransport(default='{"color":"black","length":"long","texture":"straight","style":"loose","notes":""}')
    rc2 = run(fake_root, ["--char", "TUTOR", "--lens", "hair", "--limit", "1"], t2)
    assert rc2 == 0 and len(t2.calls) == 1
    assert cache.exists()


def test_unknown_lens_exits_2_without_calls(fake_root):
    t = FakeTransport()
    rc = run(fake_root, ["--char", "TUTOR", "--lens", "aura"], t)
    assert rc == 2
    assert t.calls == []


def test_lens_all_keyword_runs_seven_lenses(fake_root):
    t = FakeTransport(default='{}')
    rc = run(fake_root, ["--char", "TUTOR", "--lens", "all", "--limit", "1"], t)
    assert rc == 0
    assert len(t.calls) == len(LENSES)


def test_max_side_is_respected_in_encoded_image(fake_root):
    import base64 as b64mod
    import io as iomod
    make_jpeg(fake_root / "refs" / "characters" / "BIG" / "x.jpg", "gray", size=(1920, 1080))
    t = FakeTransport(default='{"color":"black","length":"long","texture":"straight","style":"loose","notes":""}')
    rc = run(fake_root, ["--char", "BIG", "--lens", "hair", "--max-side", "512"], t)
    assert rc == 0
    url = t.calls[0][0][1]["content"][0]["image_url"]["url"]
    raw = b64mod.b64decode(url.split(",", 1)[1])
    im = Image.open(iomod.BytesIO(raw))
    assert max(im.size) == 512


def test_non_image_files_in_char_dir_ignored(fake_root):
    (fake_root / "refs" / "characters" / "TUTOR" / "traits.txt").write_text("notes", encoding="utf-8")
    (fake_root / "refs" / "characters" / "TUTOR" / "ref_tiers.json").write_text("{}", encoding="utf-8")
    t = FakeTransport(default='{"color":"black","length":"long","texture":"straight","style":"loose","notes":""}')
    rc = run(fake_root, ["--char", "TUTOR", "--lens", "hair"], t)
    assert rc == 0 and len(t.calls) == 2   # only a.jpg + b.jpg


def test_corrupt_cache_file_is_requeried(fake_root):
    t = FakeTransport(default='{"color":"black","length":"long","texture":"straight","style":"loose","notes":""}')
    run(fake_root, ["--char", "TUTOR", "--lens", "hair", "--limit", "1"], t)
    cache = fake_root / "library" / "char" / "vlm-cache" / "TUTOR" / "hair" / "a.jpg.json"
    cache.write_text("{not json", encoding="utf-8")
    t2 = FakeTransport(default='{"color":"black","length":"long","texture":"straight","style":"loose","notes":""}')
    rc = run(fake_root, ["--char", "TUTOR", "--lens", "hair", "--limit", "1"], t2)
    assert rc == 0 and len(t2.calls) == 1


def test_sleep_called_between_retries(fake_root):
    slept = []
    t = FakeTransport(script=[
        mod.VLMHttpError(500, "boom"),
        mod.VLMHttpError(500, "boom"),
        '{"color":"black","length":"long","texture":"straight","style":"loose","notes":""}',
    ])
    rc = mod.run_pass(["--char", "TUTOR", "--lens", "hair", "--limit", "1", "--root", str(fake_root)],
                      transport=t, sleep=slept.append)
    assert rc == 0
    assert slept == [mod.RETRY_SLEEP, mod.RETRY_SLEEP]   # 3 attempts -> 2 sleeps
