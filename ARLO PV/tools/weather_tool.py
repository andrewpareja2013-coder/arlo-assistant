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


def _describe(code):
    if code == 0:
        return "clear skies"
    if code == 1:
        return "mostly clear"
    if code == 2:
        return "partly cloudy"
    if code == 3:
        return "overcast"
    if code in (45, 48):
        return "foggy"
    if code in (51, 53, 55, 61, 63, 65, 80, 81, 82):
        return "rainy"
    if code in (56, 57, 66, 67):
        return "freezing rain"
    if code in (71, 73, 75, 77, 85, 86):
        return "snowy"
    if code in (95, 96, 99):
        return "stormy"
    return "unclear conditions"


def get_weather():
    lat, lon = _get_location()
    if lat is None or lon is None:
        return "I couldn't work out your location, sir, so I can't check the weather right now."

    unit = security.get_setting("temperature_unit", "fahrenheit")

    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,weather_code&temperature_unit={unit}"
    )
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        temp = data["current"]["temperature_2m"]
        code = data["current"]["weather_code"]
    except Exception:
        return "I couldn't get the weather right now, sir. Please check the connection and try again."

    unit_symbol = "°F" if unit == "fahrenheit" else "°C"
    return f"{temp}{unit_symbol} and {_describe(code)}"


register(
    name="get_weather",
    description="Get the current weather temperature and conditions for the user's location.",
    parameters={"type": "object", "properties": {}},
    function=get_weather,
    safe_to_test=True,
)