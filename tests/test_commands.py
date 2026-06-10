from bot.commands import build_command_reply, parse_command, validate_provinces


PROVINCES = {
    "เชียงใหม่": {"lat": 18.7, "lon": 98.9},
    "กรุงเทพมหานคร": {"lat": 13.7, "lon": 100.5},
}


def test_parse_follow_command():
    result = parse_command("/ติดตาม เชียงใหม่ กรุงเทพมหานคร")
    assert result.action == "follow"
    assert result.provinces == ["เชียงใหม่", "กรุงเทพมหานคร"]


def test_validate_provinces_rejects_invalid():
    valid, invalid = validate_provinces(["เชียงใหม่", "เมืองสมมติ"], PROVINCES)
    assert valid == ["เชียงใหม่"]
    assert invalid == ["เมืองสมมติ"]


def test_follow_command_does_not_save_invalid_provinces():
    saved = []

    def save_user(user_id, provinces):
        saved.append((user_id, provinces))

    reply = build_command_reply(
        "u1",
        "/ติดตาม เชียงใหม่ เมืองสมมติ",
        PROVINCES,
        lambda user_id: [],
        save_user,
    )
    assert "ไม่พบจังหวัด" in reply
    assert saved == []


def test_follow_command_saves_valid_provinces():
    saved = []
    reply = build_command_reply(
        "u1",
        "/ติดตาม เชียงใหม่ กรุงเทพมหานคร",
        PROVINCES,
        lambda user_id: [],
        lambda user_id, provinces: saved.append((user_id, provinces)),
    )
    assert "ติดตามแล้ว" in reply
    assert saved == [("u1", ["เชียงใหม่", "กรุงเทพมหานคร"])]

