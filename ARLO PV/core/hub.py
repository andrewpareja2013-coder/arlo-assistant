# =============================================================
# HUB.PY
# Admin-only overview shown as a temporary overlay that restores the
# exact prior screen on exit. With the admin secret it lists every
# account (name + code) and their activity; without it, only your own.
# =============================================================

import sys
import os
import io
from getpass import getpass
import requests
import config
import security
from ui import arlo_says


def _clear():
    os.system("cls" if os.name == "nt" else "clear")


def _load_accounts(admin_secret):
    """Returns (accounts, note). Without a valid admin secret, only the current account is returned."""
    own = [{
        "id": security.get_current_account_id(),
        "username": security.get_current_username(),
        "role": security.get_role(),
    }]
    if not admin_secret:
        return own, "Showing your own account only. Enter the admin secret to see every account."
    try:
        response = requests.get(
            f"{config.API_BASE}/admin-list-accounts",
            headers={"X-Admin-Secret": admin_secret},
            timeout=10,
        )
        data = response.json()
    except Exception:
        return own, "Couldn't reach the server. Showing your own account only."
    if not data.get("success"):
        return own, "Incorrect admin secret. Showing your own account only."
    return data["accounts"], None


def show_hub(memory):
    """Admin-only: shows activity for the accounts the admin secret unlocks."""
    if not security.is_admin():
        arlo_says("The HUB is restricted to admin accounts only, sir.")
        return

    capture_on = hasattr(sys.stdout, "captured")
    pre_hub_snapshot = sys.stdout.captured.getvalue() if capture_on else ""

    _clear()

    width = 40
    title = f"{config.WAKE_KEYWORD.upper()} HUB (Admin)"
    print("\n╔" + "═" * width + "╗")
    print("║" + title.center(width) + "║")
    print("╚" + "═" * width + "╝\n")

    admin_secret = getpass("Admin secret (Enter to skip and see only your own account): ").strip()
    accounts, note = _load_accounts(admin_secret)

    print(f"\n── Accounts ({len(accounts)}) ──")
    if note:
        print(f"  {note}")
    for acct in accounts:
        print(f"  {acct['username']}  [{security.format_code(acct['id'])}]  ({acct.get('role', '?')})")
    print()

    print("── Activity by Account ──")
    for acct in accounts:
        try:
            transcript = requests.get(
                f"{config.API_BASE}/get-transcript", params={"account_id": acct["id"]}, timeout=10
            ).json().get("transcript", [])
            summary = requests.get(
                f"{config.API_BASE}/get-memory", params={"account_id": acct["id"]}, timeout=10
            ).json().get("summary", "")
        except Exception:
            print(f"\n  {acct['username']} -- couldn't load activity")
            continue

        print(f"\n  {acct['username']} -- {len(transcript)} total messages")
        for msg in transcript[-3:]:
            print(f"    [{msg.get('role', '?')}] {str(msg.get('content', ''))[:60]}")
        if summary:
            print(f"    Memory summary: {str(summary)[:150]}")
    print()

    input("\nPress Enter to return...")
    _clear()
    if capture_on:
        sys.stdout.real_stdout.write(pre_hub_snapshot)
        sys.stdout.real_stdout.flush()
        sys.stdout.captured = io.StringIO(pre_hub_snapshot)
        sys.stdout.captured.seek(0, io.SEEK_END)