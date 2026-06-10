from scorer.risk_scorer import score_all, score_drought, score_fire, score_flood, score_pm25


def test_flood_score_5_at_threshold():
    assert score_flood({"precipitation_max": 50}) == (5, 50)


def test_flood_score_4_just_below_threshold():
    assert score_flood({"precipitation_max": 49}) == (4, 49)


def test_pm25_boundaries():
    assert score_pm25(49) == (1, 49)
    assert score_pm25(50) == (2, 50)
    assert score_pm25(200) == (5, 200)


def test_drought_has_no_score_5():
    assert score_drought({"daily_precip_sum": 0}) == (4, 0)
    assert score_drought({"daily_precip_sum": 0.5}) == (3, 0.5)
    assert score_drought({"daily_precip_sum": 6}) == (1, 6)


def test_fire_uses_count_or_frp():
    assert score_fire({"fire_count": 20, "max_frp": 10}) == (5, 20)
    assert score_fire({"fire_count": 1, "max_frp": 0}) == (2, 1)
    assert score_fire({"fire_count": 0, "max_frp": 50}) == (3, 50)


def test_score_all_returns_all_hazards():
    result = score_all(
        {"precipitation_max": 25, "daily_precip_sum": 0.5, "wind_speed_max": 91},
        120,
        {"max_magnitude": 4.2, "count": 1},
        {"fire_count": 0, "max_frp": 0},
    )
    assert set(result) == {"flood", "pm25", "drought", "storm", "earthquake", "fire"}
    assert result["storm"] == (5, 91)

