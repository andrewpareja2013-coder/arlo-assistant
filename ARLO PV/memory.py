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

        self.summary_loaded = False  # False if the server couldn't be reached, so we never overwrite the real summary
        self.long_term_summary = self._load_summary()
        self.alarms = self._load_alarms()

    def _load_summary(self):
        try:
            response = requests.get(f"{config.API_BASE}/get-memory", params={"account_id": self.account_id}, timeout=10)
            summary = response.json().get("summary", "")
            self.summary_loaded = True
            return summary or ""
        except Exception:
            return ""

    def _load_alarms(self):
        alarms = []
        try:
            response = requests.get(f"{config.API_BASE}/get-alarms", params={"account_id": self.account_id}, timeout=10)
            rows = response.json().get("alarms", [])
        except Exception:
            return alarms
        for a in rows:
            try:
                alarms.append({
                    "id": a["id"],
                    "time": datetime.fromisoformat(a["fire_time"]),
                    "description": a["description"],
                    "fired": bool(a["fired"]),
                })
            except Exception:
                continue  # skip a damaged alarm instead of failing the whole list
        return alarms

    def _save_transcript_message(self, role, content):
        try:
            requests.post(
                f"{config.API_BASE}/save-transcript-message",
                json={"account_id": self.account_id, "role": role, "content": content},
                timeout=10,
            )
        except Exception:
            pass  # the chat keeps going; this message just isn't in the saved transcript

    def add_message(self, role, content):
        self.conversation.append({"role": role, "content": content})
        self._save_transcript_message(role, content)

    def add_action(self, action_description):
        self.actions.append(action_description)

    def save_summary(self, new_summary):
        from security.privacy_filter import filter_sensitive_info
        new_summary = filter_sensitive_info(new_summary)

        self.long_term_summary = new_summary
        if not self.summary_loaded:
            return  # the old summary never loaded, so saving now could erase it
        try:
            requests.post(f"{config.API_BASE}/save-memory", json={"account_id": self.account_id, "summary": new_summary}, timeout=10)
        except Exception:
            pass

    def save_alarms(self):
        """Refreshes the in-memory alarm list from the backend after a change.
        Individual alarms are saved/deleted directly via time_tool.py."""
        self.alarms = self._load_alarms()