import requests


BASE_URL = "https://api.openaq.org/v2/measurements"


def fetch_pm25(lat: float, lon: float) -> float:
    params = {
        "coordinates": f"{lat},{lon}",
        "radius": 50000,
        "parameter": "pm25",
        "limit": 5,
        "order_by": "datetime",
        "sort": "desc",
    }
    try:
        res = requests.get(BASE_URL, params=params, headers={"Accept": "application/json"}, timeout=10)
        res.raise_for_status()
        results = res.json().get("results", [])
        values = []
        for row in results:
            value = row.get("value")
            if value is None:
                continue
            try:
                values.append(float(value))
            except (TypeError, ValueError):
                continue
        return sum(values) / len(values) if values else None
    except Exception as exc:
        print(f"PM2.5 fetch error: {exc}")
        return None

