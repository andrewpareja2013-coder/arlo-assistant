# =============================================================
# MEMORY.PY
# Holds everything A.R.L.O. remembers during a session. Long-term
# summary, alarms, and transcript are backed by the live
# Cloudflare API instead of local encrypted files.
# =============================================================

import requests
import security
import config
from datetime import datetime


class Memory:
    def __init__(self):
        self.conversation = []
        self.actions = []
        self.pending_action = None

        self.long_term_summary = self._load_summary()
        self.alarms = self._load_alarms()

    def add_message(self, role, content):
        self.conversation.append({"role": role, "content": content})
        self._save_transcript_message(role, content)

    def add_action(self, action_description):
        self.actions.append(action_description)

    def _load_summary(self):
        username = security.get_current_username()
        response = requests.get(f"{config.API_BASE}/get-memory", params={"username": username}, timeout=10)
        return response.json().get("summary", "")

    def save_summary(self, new_summary):
        from privacy_filter import filter_sensitive_info
        new_summary = filter_sensitive_info(new_summary)

        self.long_term_summary = new_summary
        username = security.get_current_username()
        requests.post(f"{config.API_BASE}/save-memory", json={"username": username, "summary": new_summary}, timeout=10)

    def _load_alarms(self):
        username = security.get_current_username()
        response = requests.get(f"{config.API_BASE}/get-alarms", params={"username": username}, timeout=10)
        data = response.json()
        alarms = []
        for a in data.get("alarms", []):
            alarms.append({
                "id": a["id"],
                "time": datetime.fromisoformat(a["fire_time"]),
                "description": a["description"],
                "fired": bool(a["fired"]),
            })
        return alarms

    def save_alarms(self):
        """Refreshes the in-memory alarm list from the backend after a change.
        Individual alarms are saved/deleted directly via time_tool.py."""
        self.alarms = self._load_alarms()

    def _save_transcript_message(self, role, content):
        username = security.get_current_username()
        requests.post(f"{config.API_BASE}/save-transcript-message", json={"username": username, "role": role, "content": content}, timeout=10)