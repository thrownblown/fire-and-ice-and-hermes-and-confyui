from core.scene_slice import cottage_shot_ids


def test_keeps_cottage_and_drops_ice():
    rows = [
        {"shot_id": "shot:1", "location_token": "cottage"},
        {"shot_id": "shot:2", "location_token": "cottage"},
        {"shot_id": "shot:3", "location_token": "ice_cave"},
    ]
    assert cottage_shot_ids(rows) == ["shot:1", "shot:2"]
