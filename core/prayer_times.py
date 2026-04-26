import requests

MADHAB_MAP = {"Hanafi": 1, "Shafi": 0, "Maliki": 0, "Hanbali": 0}
METHOD_MAP = {"MWL": 3, "ISNA": 2, "Egypt": 5, "Karachi": 1}

def get_coordinates(city: str, country: str) -> tuple:
    """Get lat/lon for a city using Nominatim (OpenStreetMap)."""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": f"{city}, {country}", "format": "json", "limit": 1}
        headers = {"User-Agent": "WaqtApp/1.0"}
        r = requests.get(url, params=params, headers=headers, timeout=5)
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None, None

def get_prayer_times(city: str, country: str, madhab: str, method: str) -> dict:
    """
    Fetch prayer times using coordinates for better accuracy.
    Falls back to city/country if coordinates fail.
    """
    lat, lon = get_coordinates(city, country)

    try:
        if lat and lon:
            url = "https://api.aladhan.com/v1/timings"
            params = {
                "latitude": lat,
                "longitude": lon,
                "method": METHOD_MAP.get(method, 3),
                "school": MADHAB_MAP.get(madhab, 1)
            }
        else:
            url = "https://api.aladhan.com/v1/timingsByCity"
            params = {
                "city": city,
                "country": country,
                "method": METHOD_MAP.get(method, 3),
                "school": MADHAB_MAP.get(madhab, 1)
            }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        timings = data["data"]["timings"]

        return {
            "Fajr":    timings["Fajr"],
            "Sunrise": timings["Sunrise"],
            "Dhuhr":   timings["Dhuhr"],
            "Asr":     timings["Asr"],
            "Maghrib": timings["Maghrib"],
            "Isha":    timings["Isha"]
        }
    except Exception as e:
        raise RuntimeError(f"Failed to fetch prayer times: {e}")