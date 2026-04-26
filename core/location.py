import requests

def get_location_by_ip() -> dict:
    """
    Returns city and country based on IP address.
    Falls back to Bishkek if fails.
    """
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        data = response.json()
        if data.get("status") == "success":
            return {
                "city": data.get("city", "Bishkek"),
                "country": data.get("country", "Kyrgyzstan"),
                "lat": data.get("lat"),
                "lon": data.get("lon"),
            }
    except Exception:
        pass
    return {"city": "Bishkek", "country": "Kyrgyzstan", "lat": 42.87, "lon": 74.59}