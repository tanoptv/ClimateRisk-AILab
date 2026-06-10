import requests


BASE_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def fetch_pm25(lat: float, lon: float) -> float | None:
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "pm2_5",
        "forecast_days": 1,
        "timezone": "Asia/Bangkok",
    }
    try:
        res = requests.get(BASE_URL, params=params, timeout=10)
        res.raise_for_status()
        values = [v for v in res.json().get("hourly", {}).get("pm2_5", []) if v is not None]
        recent = values[-4:] if len(values) >= 4 else values
        return sum(recent) / len(recent) if recent else None
    except Exception as exc:
        print(f"PM2.5 fetch error: {exc}")
        return None
