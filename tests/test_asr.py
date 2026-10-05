from core.asr import segments_to_records


class _FakeSeg:
    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text


def test_segments_to_records():
    segs = [_FakeSeg(0.0, 1.5, "  hello  "), _FakeSeg(1.5, 3.0, "world")]
    recs = segments_to_records(segs)
    assert recs[0] == {"index": 0, "start": 0.0, "end": 1.5, "text": "hello"}
    assert recs[1] == {"index": 1, "start": 1.5, "end": 3.0, "text": "world"}


def test_empty_segments():
    assert segments_to_records([]) == []
