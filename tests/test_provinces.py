import json


def test_provinces_contains_77_entries():
    with open("data/provinces.json", "r", encoding="utf-8") as f:
        provinces = json.load(f)
    assert len(provinces) == 77
    assert "เชียงใหม่" in provinces
    assert "กรุงเทพมหานคร" in provinces

