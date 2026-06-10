HAZARD_LABELS = {
    "flood": "น้ำท่วม",
    "pm25": "ฝุ่น PM2.5",
    "drought": "ภัยแล้ง",
    "storm": "พายุ",
    "earthquake": "แผ่นดินไหว",
    "fire": "ไฟป่า",
}

HAZARD_ORDER = ["flood", "pm25", "drought", "storm", "earthquake", "fire"]

SCORE_COLORS = {
    1: "#22c55e",
    2: "#a3e635",
    3: "#facc15",
    4: "#fb923c",
    5: "#ef4444",
}

SCORE_LABELS = {
    1: "ปกติ",
    2: "เฝ้าระวัง",
    3: "ระวัง",
    4: "อันตราย",
    5: "วิกฤต",
}


def _number(value: object, default: float = 0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def score_flood(weather: dict) -> tuple[int, float]:
    precip = _number(weather.get("precipitation_max", 0))
    if precip >= 50:
        return 5, precip
    if precip >= 35:
        return 4, precip
    if precip >= 20:
        return 3, precip
    if precip >= 10:
        return 2, precip
    return 1, precip


def score_pm25(pm25_value: float) -> tuple[int, float]:
    value = _number(pm25_value)
    if value >= 200:
        return 5, value
    if value >= 150:
        return 4, value
    if value >= 100:
        return 3, value
    if value >= 50:
        return 2, value
    return 1, value


def score_drought(weather: dict) -> tuple[int, float]:
    daily_precip = _number(weather.get("daily_precip_sum", 0))
    if daily_precip == 0:
        return 4, daily_precip
    if daily_precip < 1:
        return 3, daily_precip
    if daily_precip < 5:
        return 2, daily_precip
    return 1, daily_precip


def score_storm(weather: dict) -> tuple[int, float]:
    wind = _number(weather.get("wind_speed_max", 0))
    if wind >= 90:
        return 5, wind
    if wind >= 65:
        return 4, wind
    if wind >= 40:
        return 3, wind
    if wind >= 20:
        return 2, wind
    return 1, wind


def score_earthquake(eq: dict) -> tuple[int, float]:
    mag = _number(eq.get("max_magnitude", 0))
    if mag >= 7.0:
        return 5, mag
    if mag >= 6.0:
        return 4, mag
    if mag >= 5.0:
        return 3, mag
    if mag >= 4.0:
        return 2, mag
    return 1, mag


def score_fire(fire: dict) -> tuple[int, float]:
    count = _number(fire.get("fire_count", 0))
    frp = _number(fire.get("max_frp", 0))
    raw_value = max(count, frp)
    if count >= 20 or frp >= 500:
        return 5, raw_value
    if count >= 10 or frp >= 200:
        return 4, raw_value
    if count >= 5 or frp >= 50:
        return 3, raw_value
    if count >= 1:
        return 2, raw_value
    return 1, raw_value


def score_all(weather: dict, pm25: float, earthquake: dict, fire: dict) -> dict[str, tuple[int, float]]:
    return {
        "flood": score_flood(weather),
        "pm25": score_pm25(pm25),
        "drought": score_drought(weather),
        "storm": score_storm(weather),
        "earthquake": score_earthquake(earthquake),
        "fire": score_fire(fire),
    }

