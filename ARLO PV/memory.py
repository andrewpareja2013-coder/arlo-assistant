# =============================================================
# MEMORY.PY
# Holds everything A.R.L.O. remembers during a session. Long-term
# summary, alarms, and transcript live on the backend under the
# account code of whoever was logged in when the session started,
# so a later logout can never mix up whose data is whose.
# =============================================================

import requests
import security
import config
from datetime import datetime


class Memory:
    def __init__(self):
        self.account_id = security.get_current_account_id()
        self.conversation = []
        self.actions = []
        self.pending_action = None

        self.long_term_summary = self._load_summary()
        self.alarms = self._load_alarms()

    def _load_summary(self):
        response = requests.get(f"{config.API_BASE}/get-memory", params={"account_id": self.account_id}, timeout=10)
        return response.json().get("summary", "")

    def _load_alarms(self):
        response = requests.get(f"{config.API_BASE}/get-alarms", params={"account_id": self.account_id}, timeout=10)
        alarms = []
        for a in response.json().get("alarms", []):
            alarms.append({
                "id": a["id"],
                "time": datetime.fromisoformat(a["fire_time"]),
                "description": a["description"],
                "fired": bool(a["fired"]),
            })
        return alarms

    def _save_transcript_message(self, role, content):
        requests.post(
            f"{config.API_BASE}/save-transcript-message",
            json={"account_id": self.account_id, "role": role, "content": content},
            timeout=10,
        )

    def add_message(self, role, content):
        self.conversation.append({"role": role, "content": content})
        self._save_transcript_message(role, content)

    def add_action(self, action_description):
        self.actions.append(action_description)

    def save_summary(self, new_summary):
        from security.privacy_filter import filter_sensitive_info
        new_summary = filter_sensitive_info(new_summary)

        self.long_term_summary = new_summary
        requests.post(f"{config.API_BASE}/save-memory", json={"account_id": self.account_id, "summary": new_summary}, timeout=10)

    def save_alarms(self):
        """Refreshes the in-memory alarm list from the backend after a change.
        Individual alarms are saved/deleted directly via time_tool.py."""
        self.alarms = self._load_alarms()