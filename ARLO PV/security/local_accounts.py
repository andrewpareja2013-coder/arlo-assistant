# =============================================================
# LOCAL_ACCOUNTS.PY
# Keeps a per-machine shortlist of accounts (code + display name) to
# show at login, separate from the accounts on the server. Purely a
# local convenience -- adding or removing here never touches the
# real account or its data.
# An old list that only holds usernames is converted once, by asking
# the server which account has each name (temporary, removed in 1.2.4).
# =============================================================

import os
import json
import requests
import config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_LIST_FILE = os.path.join(BASE_DIR, "local_accounts.json")


def _read_file():
    if not os.path.exists(LOCAL_LIST_FILE):
        return []
    try:
        with open(LOCAL_LIST_FILE) as f:
            data = json.load(f)
    except Exception:
        return []
    return data if isinstance(data, list) else []


def _write_file(accounts):
    with open(LOCAL_LIST_FILE, "w") as f:
        json.dump(accounts, f, indent=2)


def _lookup_code_by_name(name):
    """Returns (account_id or None, server_reachable). Used only to convert old names-only lists."""
    try:
        response = requests.post(f"{config.API_BASE}/login", json={"username": name}, timeout=10)
        data = response.json()
    except Exception:
        return None, False
    if data.get("success"):
        return data["account"]["id"], True
    return None, True


def get_local_accounts():
    """Returns [{"id": account code, "name": display name}, ...]."""
    accounts = []
    converted = False
    server_unreachable = False

    for entry in _read_file():
        if isinstance(entry, dict) and "id" in entry and "name" in entry:
            accounts.append(entry)
        elif isinstance(entry, str):
            converted = True
            account_id, reachable = _lookup_code_by_name(entry)
            if not reachable:
                server_unreachable = True
            elif account_id:
                accounts.append({"id": account_id, "name": entry})

    # Only save the converted list if the server answered for every name
    if converted and not server_unreachable:
        _write_file(accounts)
    return accounts


def add_local_account(account_id, name):
    """Adds an account to this machine's shortlist, if it isn't already there."""
    accounts = get_local_accounts()
    if not any(a["id"] == account_id for a in accounts):
        accounts.append({"id": account_id, "name": name})
        _write_file(accounts)


def remove_local_account(account_id):
    """Removes an account from this machine's shortlist only -- the real account is untouched."""
    accounts = [a for a in get_local_accounts() if a["id"] != account_id]
    _write_file(accounts)