# =============================================================
# HUB.PY
# Admin-only overview: cross-account activity and memory, shown
# as a temporary overlay that restores the exact prior screen.
# =============================================================

import sys
import os
import io
import json
import base64
import requests
import config
import security
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from ui import arlo_says


def _derive_admin_key(admin_secret):
    salt = b"arlo-admin-salt-fixed"
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    return kdf.derive(admin_secret.encode())


def _decrypt_admin_master_key(admin_locked_b64, admin_secret):
    key = _derive_admin_key(admin_secret)
    raw = base64.b64decode(admin_locked_b64)
    iv, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(iv, ciphertext, None).decode()


def show_hub(memory):
    """Admin-only: displays activity and memory across ALL accounts."""
    if not security.is_admin():
        arlo_says("The HUB is restricted to admin accounts only, sir.")
        return

    pre_hub_snapshot = sys.stdout.buffer.getvalue()

    os.system("cls" if os.name == "nt" else "clear")

    width = 40
    title = f"{config.WAKE_KEYWORD.upper()} HUB (Admin)"
    print("\n╔" + "═" * width + "╗")
    print("║" + title.center(width) + "║")
    print("╚" + "═" * width + "╝\n")

    admin_secret = input("Admin secret (to view decrypted memory, or Enter to skip): ").strip()

    accounts = security.list_accounts()
    print(f"\n── All Accounts ({len(accounts)}) ──")
    for acct in accounts:
        print(f"  {acct}")
    print()

    print("── Activity by Account ──")
    for acct in accounts:
        response = requests.get(f"{config.API_BASE}/get-transcript", params={"username": acct}, timeout=10)
        transcript = response.json().get("transcript", [])
        print(f"\n  {acct} -- {len(transcript)} total messages")
        for msg in transcript[-3:]:
            print(f"    [{msg['role']}] {msg['content'][:60]}")

        if admin_secret:
            admin_response = requests.get(
                f"{config.API_BASE}/admin-get-account",
                params={"username": acct},
                headers={"X-Admin-Secret": admin_secret},
                timeout=10,
            )
            admin_data = admin_response.json()
            if admin_data.get("success"):
                summary_response = requests.get(f"{config.API_BASE}/get-memory", params={"username": acct}, timeout=10)
                summary = summary_response.json().get("summary", "")
                if summary:
                    print(f"    Memory summary: {summary[:150]}")
    print()

    input("\nPress Enter to return...")
    os.system("cls" if os.name == "nt" else "clear")
    sys.stdout.real_stdout.write(pre_hub_snapshot)
    sys.stdout.real_stdout.flush()
    sys.stdout.buffer = io.StringIO(pre_hub_snapshot)
    sys.stdout.buffer.seek(0, io.SEEK_END)