import json
import os

SETTINGS_FILE = "settings.json"

DEFAULT = {
    "city": "Bishkek",
    "country": "Kyrgyzstan",
    "madhab": "Hanafi",
    "method": "MWL",
    "theme_name": "Dark Green",
    "overlay_style": "pill",
    "display_mode": "overlay",
    "notifications": True,
    "language": "en",
    "auto_location": True,
    "cached_times": None,
    "cached_date": None,
}

def load() -> dict:
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            data = {**DEFAULT, **json.load(f)}
    else:
        data = DEFAULT.copy()
        try:
            from core.location import get_location_by_ip
            loc = get_location_by_ip()
            data["city"] = loc["city"]
            data["country"] = loc["country"]
            save(data)
        except Exception:
            pass
    return data

def save(data: dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def save_cached_times(data: dict, times: dict):
    """Save prayer times to local cache for offline use."""
    from datetime import date
    data["cached_times"] = times
    data["cached_date"]  = date.today().isoformat()
    save(data)

def get_cached_times(data: dict) -> dict | None:
    """Return cached times if they exist and are from today."""
    from datetime import date
    cached = data.get("cached_times")
    cached_date = data.get("cached_date")
    if cached and cached_date == date.today().isoformat():
        return cached
    return None