from core.join import join_chunks, pts_to_seconds


class _Chunk:
    def __init__(self, id, sp, ep):
        self.id = id
        self.start_pts = sp
        self.end_pts = ep


def _cue(i, start, end, text="x"):
    return {"cue_index": i, "text": text, "start": start, "end": end}


def test_pts_to_seconds():
    assert pts_to_seconds(24000) == 1.0
    assert pts_to_seconds(0) == 0.0


def test_empty():
    assert join_chunks([], []) == []


def test_cue_fully_inside():
    out = join_chunks([_Chunk("c1", 0, 24000)], [_cue(0, 0.2, 0.5)])
    assert len(out[0].cues) == 1
    assert out[0].cues[0]["cue_index"] == 0


def test_cue_overlapping_boundary():
    out = join_chunks([_Chunk("c1", 0, 24000)], [_cue(0, 0.8, 1.5)])
    assert len(out[0].cues) == 1


def test_cue_outside_excluded():
    out = join_chunks([_Chunk("c1", 0, 24000)], [_cue(0, 1.5, 2.0)])
    assert out[0].cues == []


def test_unmatched_cue_excluded():
    cues = [{"cue_index": 0, "text": "x", "start": None, "end": None}]
    out = join_chunks([_Chunk("c1", 0, 24000)], cues)
    assert out[0].cues == []


def test_chunk_time_conversion():
    out = join_chunks([_Chunk("c1", 12000, 36000)], [_cue(0, 0.5, 1.0)])
    assert out[0].start_s == 0.5
    assert out[0].end_s == 1.5
    assert len(out[0].cues) == 1
