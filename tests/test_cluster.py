from core.cluster import cluster_people


def test_same_signature_across_shots_is_on_one_cluster():
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
