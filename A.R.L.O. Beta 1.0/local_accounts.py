# =============================================================
# LOCAL_ACCOUNTS.PY
# Keeps a per-machine shortlist of usernames to show at login,
# separate from the full account list on the server. Purely a
# local convenience -- adding/removing here never touches the
# actual account or its data in the cloud.
# =============================================================

import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_LIST_FILE = os.path.join(BASE_DIR, "local_accounts.json")


def get_local_accounts():
    """Returns the list of usernames previously added on this machine."""
    if not os.path.exists(LOCAL_LIST_FILE):
        return []
    with open(LOCAL_LIST_FILE) as f:
        return json.load(f)


def add_local_account(username):
    """Adds a username to this machine's shortlist, if not already there."""
    accounts = get_local_accounts()
    if username not in accounts:
        accounts.append(username)
        with open(LOCAL_LIST_FILE, "w") as f:
            json.dump(accounts, f)


def remove_local_account(username):
    """Removes a username from this machine's shortlist only -- does not delete the actual account."""
    accounts = get_local_accounts()
    if username in accounts:
        accounts.remove(username)
        with open(LOCAL_LIST_FILE, "w") as f:
            json.dump(accounts, f)