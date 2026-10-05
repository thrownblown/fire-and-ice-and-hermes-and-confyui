from core.align import align, similarity
from core.script import Cue


def _cues(texts):
    return [Cue(index=i, page=1, text=t) for i, t in enumerate(texts)]


def _seg(items):
    return [{"index": i, "start": float(i * 10), "end": float(i * 10 + 5), "text": t}
            for i, t in enumerate(items)]


def test_similarity_identical():
    assert similarity("hello world", "hello world") == 1.0


def test_similarity_disjoint_low():
    assert similarity("hello world", "goodbye cruel") < 0.2


def test_similarity_empty():
    assert similarity("", "x") == 0.0
    assert similarity("x", "") == 0.0


def test_align_exact_match():
    cues = _cues(["the first line", "the second line"])
    segs = _seg(["the first line", "the second line"])
    out = align(cues, segs)
    assert out[0].start == 0.0 and out[0].end == 5.0 and out[0].score == 1.0
    assert out[1].start == 10.0 and out[1].end == 15.0


def test_align_skips_unmatched_without_reordering():
    cues = _cues(["alpha", "beta", "gamma"])
    segs = _seg(["alpha", "zzz noise", "gamma"])
    out = align(cues, segs)
    assert out[0].start == 0.0
    assert out[1].start is None
    assert out[2].start == 20.0


def test_align_times_monotonic():
    cues = _cues(["one", "two", "three", "four"])
    segs = _seg(["one", "two", "three", "four"])
    out = align(cues, segs)
    starts = [c.start for c in out]
    assert starts == sorted(starts)
    assert starts == [0.0, 10.0, 20.0, 30.0]


def test_align_empty():
    assert align([], []) == []


def test_align_no_segments():
    out = align(_cues(["x"]), [])
    assert len(out) == 1
    assert out[0].start is None
