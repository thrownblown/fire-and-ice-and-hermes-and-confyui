def cottage_shot_ids(rows):
    return [row["shot_id"] for row in rows if row.get("location_token") == "cottage"]
