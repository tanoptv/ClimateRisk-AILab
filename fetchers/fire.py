import os

import requests


ZERO_FIRE = {"fire_count": 0, "max_frp": 0}


def fetch_fire(lat: float, lon: float, api_key: str | None = None) -> dict[str, float]:
    key = api_key or os.getenv("NASA_FIRMS_API_KEY", "")
    if not key:
        return dict(ZERO_FIRE)

    delta = 0.5
    area = f"{lon - delta},{lat - delta},{lon + delta},{lat + delta}"
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/VIIRS_SNPP_NRT/{area}/1"
    try:
        res = requests.get(url, timeout=15)
        if res.status_code != 200 or not res.text.strip():
            return dict(ZERO_FIRE)

        lines = res.text.strip().splitlines()
        if len(lines) <= 1:
            return dict(ZERO_FIRE)

        header = [h.strip().lower() for h in lines[0].split(",")]
        frp_index = header.index("frp") if "frp" in header else 13
        frp_values = []
        for line in lines[1:]:
            cols = line.split(",")
            try:
                frp_values.append(float(cols[frp_index]))
            except (IndexError, ValueError):
                continue
        return {"fire_count": len(lines) - 1, "max_frp": max(frp_values) if frp_values else 0}
    except Exception as exc:
        print(f"Fire fetch error: {exc}")
        return dict(ZERO_FIRE)

