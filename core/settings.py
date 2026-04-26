import json
import os

SETTINGS_FILE = "settings.json"

DEFAULT = {
    "city": "Bishkek",
    "country": "Kyrgyzstan",
    "madhab": "Hanafi",
    "method": "MWL",
    "theme": "dark",
    "overlay_style": "pill",
    "auto_location": True
}

def load() -> dict:
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            data = {**DEFAULT, **json.load(f)}
    else:
        data = DEFAULT.copy()
        # First run — try to auto-detect location
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