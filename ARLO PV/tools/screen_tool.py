# =============================================================
# SCREEN_TOOL.PY
# Takes a screenshot and asks a vision AI model (via Cloudflare
# Workers AI) to describe or analyze what's on screen.
# =============================================================

import base64
from io import BytesIO
from PIL import ImageGrab
import requests
import config
from tools.registry import register

MAX_WIDTH = 1600


def see_screen(question):
    try:
        screenshot = ImageGrab.grab()
    except Exception:
        return "I couldn't capture the screen, sir. This computer may not support screenshots."

    if screenshot.width > MAX_WIDTH:
        new_height = round(screenshot.height * MAX_WIDTH / screenshot.width)
        screenshot = screenshot.resize((MAX_WIDTH, new_height))

    buffer = BytesIO()
    screenshot.save(buffer, format="PNG")
    image_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    try:
        response = requests.post(f"{config.API_BASE}/vision-chat", json={
            "image": image_b64,
            "prompt": question,
        }, timeout=30)
        data = response.json()
    except Exception:
        return "I couldn't reach the vision service, sir. Please check the connection and try again."

    if not data.get("success"):
        return f"I was unable to analyze the screen: {data.get('error', 'unknown error')}"

    result = data.get("response")
    if isinstance(result, dict):
        return result.get("response", "I couldn't determine what's on screen.")
    if isinstance(result, str) and result:
        return result
    return "I couldn't determine what's on screen."


register(
    name="see_screen",
    description="Take a screenshot of the user's screen and answer a question about what's currently displayed.",
    parameters={
        "type": "object",
        "properties": {"question": {"type": "string", "description": "What to look for or answer about the screen."}},
        "required": ["question"],
    },
    function=see_screen,
)