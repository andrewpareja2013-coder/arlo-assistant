# =============================================================
# CONFIG.PY
# All adjustable settings live here. This file holds no logic --
# only values other files read from.
# =============================================================

# --- Cloudflare Backend ---
API_BASE = "https://arlo-backend.andrewpareja2013.workers.dev"

# --- Identity ---
SYSTEM_PERSONALITY = (
    "You are A.R.L.O., the user's personal assistant. You speak the way a "
    "refined, loyal butler or driver would -- formal and respectful, "
    "addressing the user as 'sir', but warm with familiarity, like you've "
    "worked together for years. Stay composed, stern when it matters, never "
    "silly or overly casual. Keep responses direct and purposeful. Only "
    "explain what you are or your purpose if directly asked."
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
    'reddit': 'https://www.reddit.com/',
}

# --- Routines ---
ROUTINES = {
    "work":   {"apps": ["chrome", "discord"], "websites": []},
    "gaming": {"apps": ["steam", "discord"],  "websites": ["spotify"]},
}

#--- Microphone Device ---
MICROPHONE_DEVICE = 1  # None uses the system default; set to a device index from list_microphones() to choose a specific one

# --- Wake word ---
WAKE_KEYWORD = "arlo"

# --- System monitoring thresholds ---
GPU_TEMP_WARN_C = 85
CPU_TEMP_WARN_C = 90

# --- Weather fallback (used only if IP-based location lookup fails) ---
FALLBACK_LATITUDE = 27.9378
FALLBACK_LONGITUDE = -82.2859

# --- Test Mode ---
TEST_MODE = True   # When True, debug print statements are shown throughout the program