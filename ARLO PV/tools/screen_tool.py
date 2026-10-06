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


def see_screen(question):
    screenshot = ImageGrab.grab()
    buffer = BytesIO()
    screenshot.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    response = requests.post(f"{config.API_BASE}/vision-chat", json={
        "image": image_b64,
        "prompt": question,
    }, timeout=30)
    data = response.json()

    if not data.get("success"):
        return f"I was unable to analyze the screen: {data.get('error', 'unknown error')}"

    return data["response"].get("response", "I couldn't determine what's on screen.")


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