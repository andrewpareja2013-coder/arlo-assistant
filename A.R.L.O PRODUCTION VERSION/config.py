# =============================================================
# CONFIG.PY
# All adjustable settings live here. This file holds no logic --
# only values other files read from.
# =============================================================

# --- Cloudflare Backend ---
API_BASE = "https://arlo-backend.andrewpareja2013.workers.dev"

# --- Voice ---
VOICE_ENABLED = False  # Set to True to enable wake-word voice commands

# --- Wake word / Name ---
# Changing this changes the assistant's name everywhere: voice wake-word
# detection, the login screen, HUB, chat replies, and its own self-identity.
WAKE_KEYWORD = "arlo"

# --- Identity ---
SYSTEM_PERSONALITY = (
    f"You are {WAKE_KEYWORD.upper()}, the user's personal assistant. You speak the way a "
    "refined, loyal butler or driver would -- formal and respectful, "
    "addressing the user as 'sir', but warm with familiarity, like you've "
    "worked together for years. Stay composed, stern when it matters, never "
    "silly or overly casual. Keep responses direct and purposeful. Only "
    "explain what you are or your purpose if directly asked."
    f" Users may address you by name, '{WAKE_KEYWORD.capitalize()}' -- recognize this as referring to you, whether typed or spoken."
)

# --- Known Applications ---
KNOWN_APPS = {
    "notepad":       {"open": "notepad.exe",        "close": "notepad.exe"},
    "chrome":        {"open": r"C:\Program Files\Google\Chrome\Application\chrome.exe",          "close": "chrome.exe"},
    "calculator":    {"open": "calc.exe",            "close": "CalculatorApp.exe"},
    "discord":       {"open": r"C:\Users\apareja\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Discord.lnk", "close": "Discord.exe"},
    "steam":         {"open": r"C:\Program Files (x86)\Steam\steam.exe", "close": "steam.exe"},
    "task manager":  {"open": "taskmgr.exe",         "close": "Taskmgr.exe"},
    "file explorer": {"open": "explorer.exe",        "close": "explorer.exe"},
    "paint":         {"open": "mspaint.exe",         "close": "mspaint.exe"},
    "roblox":        {"open": r"C:\Users\apareja\Desktop\Roblox Player.lnk", "close": "Roblox Player.lnk"},
}

APP_ALIASES = {
    "google": "chrome",
}

# --- Known Websites ---
KNOWN_WEBSITES = {
    "spotify": "https://open.spotify.com",
}

# --- Routines ---
ROUTINES = {
    "work":   {"apps": ["chrome", "discord"], "websites": []},
    "gaming": {"apps": ["steam", "discord"],  "websites": ["spotify"]},
}

# --- Weather fallback (used only if IP-based location lookup fails) ---
FALLBACK_LATITUDE = 27.9378
FALLBACK_LONGITUDE = -82.2859

# --- Test Mode ---
TEST_MODE = False   # When True, debug print statements are shown throughout the program