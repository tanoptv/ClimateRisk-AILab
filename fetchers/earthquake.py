from datetime import datetime, timedelta

import requests


BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
ZERO_EARTHQUAKE = {"max_magnitude": 0, "count": 0}


def fetch_earthquake(lat: float, lon: float) -> dict[str, float]:
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)
    params = {
        "format": "geojson",
        "latitude": lat,
        "longitude": lon,
        "maxradiuskm": 300,
        "starttime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "orderby": "magnitude",
    }
    try:
        res = requests.get(BASE_URL, params=params, timeout=10)
        res.raise_for_status()
        features = res.json().get("features", [])
        magnitudes = []
        for feature in features:
            mag = feature.get("properties", {}).get("mag")
            if mag is None:
                continue
            try:
                magnitudes.append(float(mag))
            except (TypeError, ValueError):
                continue
        return {"max_magnitude": max(magnitudes) if magnitudes else 0, "count": len(features)}
    except Exception as exc:
        print(f"Earthquake fetch error: {exc}")
        return dict(ZERO_EARTHQUAKE)

