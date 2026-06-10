import requests


BASE_URL = "https://api.open-meteo.com/v1/forecast"
ZERO_WEATHER = {
    "precipitation_max": 0,
    "precipitation_sum": 0,
    "wind_speed_max": 0,
    "daily_precip_sum": 0,
}


def _clean_values(values: object) -> list[float]:
    if not isinstance(values, list):
        return []
    cleaned = []
    for value in values:
        if value is None:
            continue
        try:
            cleaned.append(float(value))
        except (TypeError, ValueError):
            continue
    return cleaned


def fetch_weather(lat: float, lon: float) -> dict[str, float]:
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "precipitation,wind_speed_10m",
        "daily": "precipitation_sum,wind_speed_10m_max",
        "forecast_days": 1,
        "timezone": "Asia/Bangkok",
    }
    try:
        res = requests.get(BASE_URL, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        hourly = data.get("hourly", {})
        daily = data.get("daily", {})
        precip_values = _clean_values(hourly.get("precipitation", []))
        wind_values = _clean_values(hourly.get("wind_speed_10m", []))
        daily_precip = _clean_values(daily.get("precipitation_sum", []))
        return {
            "precipitation_max": max(precip_values) if precip_values else 0,
            "precipitation_sum": sum(precip_values) if precip_values else 0,
            "wind_speed_max": max(wind_values) if wind_values else 0,
            "daily_precip_sum": daily_precip[0] if daily_precip else 0,
        }
    except Exception as exc:
        print(f"Weather fetch error: {exc}")
        return dict(ZERO_WEATHER)

