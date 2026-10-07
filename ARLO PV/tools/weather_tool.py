# =============================================================
# WEATHER_TOOL.PY
# Gets the current weather. Location is auto-detected from the
# user's public IP address, and the last successful reading is
# saved as a per-account fallback if a future lookup fails.
# =============================================================

import requests
import config
import security
from tools.registry import register


def _get_location():
    """Auto-detects lat/lon via IP and saves it, or uses the last saved reading.
    Returns (None, None) if there is neither."""
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        data = response.json()
        lat, lon = data["lat"], data["lon"]
        security.save_setting("last_known_lat", lat)
        security.save_setting("last_known_lon", lon)
        return lat, lon
    except Exception:
        lat = security.get_setting("last_known_lat", config.FALLBACK_LATITUDE)
        lon = security.get_setting("last_known_lon", config.FALLBACK_LONGITUDE)
        return lat, lon


def get_weather():
    lat, lon = _get_location()
    if lat is None or lon is None:
        return "I couldn't work out your location, sir, so I can't check the weather right now."

    unit = security.get_setting("temperature_unit", "fahrenheit")

    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,weather_code&temperature_unit={unit}"
    )
    response = requests.get(url, timeout=5)
    data = response.json()
    temp = data["current"]["temperature_2m"]
    code = data["current"]["weather_code"]

    unit_symbol = "°F" if unit == "fahrenheit" else "°C"

    if code == 0:
        condition = "clear skies"
    elif code in [1, 2, 3]:
        condition = "partly cloudy"
    elif code in [45, 48]:
        condition = "foggy"
    elif code in [51, 53, 55, 61, 63, 65]:
        condition = "rainy"
    elif code in [71, 73, 75]:
        condition = "snowy"
    elif code in [95, 96, 99]:
        condition = "stormy"
    else:
        condition = "unclear conditions"

    return f"{temp}{unit_symbol} and {condition}"


register(
    name="get_weather",
    description="Get the current weather temperature and conditions for the user's location.",
    parameters={"type": "object", "properties": {}},
    function=get_weather,
    safe_to_test=True,
)