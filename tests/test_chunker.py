from core.chunker import group_shots


def _shot(sid, sp, ep):
    return {"shot_id": sid, "start_pts": sp, "end_pts": ep}


def _labels(shots, location, chars):
    return {s["shot_id"]: {"location": location, "characters": chars} for s in shots}


def test_empty():
    assert group_shots([], {}) == []


def test_three_contiguous_shots_form_one_chunk():
    shots = [_shot("shot:1", 0, 100), _shot("shot:2", 100, 200), _shot("shot:3", 200, 300)]
    labels = _labels(shots, "forest", ["Teegra"])
    chunks = group_shots(shots, labels)
    assert len(chunks) == 1
    assert chunks[0].shot_ids == ["shot:1", "shot:2", "shot:3"]


def test_four_shots_cap_at_three():
    shots = [_shot(f"shot:{i}", i * 100, (i + 1) * 100) for i in range(1, 5)]
    labels = _labels(shots, "forest", ["Teegra"])
    chunks = group_shots(shots, labels)
    assert [c.shot_ids for c in chunks] == [["shot:1", "shot:2", "shot:3"], ["shot:4"]]


def test_location_change_splits():
    shots = [_shot("shot:1", 0, 100), _shot("shot:2", 100, 200)]
    labels = {
        "shot:1": {"location": "forest", "characters": ["Teegra"]},
        "shot:2": {"location": "castle", "characters": ["Teegra"]},
    }
    assert len(group_shots(shots, labels)) == 2


def test_character_set_change_splits():
    shots = [_shot("shot:1", 0, 100), _shot("shot:2", 100, 200)]
    labels = {
        "shot:1": {"location": "forest", "characters": ["Teegra"]},
        "shot:2": {"location": "forest", "characters": ["Larn"]},
    }
    assert len(group_shots(shots, labels)) == 2


def test_empty_labels_do_not_split():
    shots = [_shot("shot:1", 0, 100), _shot("shot:2", 100, 200)]
    assert len(group_shots(shots, {})) == 1


def test_chunk_id_has_no_colon():
    shots = [_shot("shot:1", 0, 100), _shot("shot:2", 100, 200)]
    assert ":" not in group_shots(shots, {})[0].id


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
