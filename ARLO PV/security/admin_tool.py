# =============================================================
# ADMIN_TOOL.PY
# FOR YOUR EYES ONLY. Never ship this to testers. Lists every account
# and decrypts any account's master key using the admin secret only you know.
# Run:  python security\admin_tool.py
# If pasting the secret doesn't work, run:  python security\admin_tool.py --visible
# =============================================================

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import base64
import getpass
import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import config


def _normalize_code(text):
    return "".join(ch for ch in str(text) if ch.isalnum()).upper()


def _looks_like_code(text):
    code = _normalize_code(text)
    return len(code) == 16 and all(ch in "0123456789ABCDEF" for ch in code)


def _format_code(code):
    code = _normalize_code(code)
    return "-".join(code[i:i + 4] for i in range(0, len(code), 4))


def _derive_admin_key(admin_secret):
    """Mirrors the server's PBKDF2 derivation exactly, so we get the same key."""
    salt = b"arlo-admin-salt-fixed"
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    return kdf.derive(admin_secret.encode())


def decrypt_admin_master_key(admin_locked_b64, admin_secret):
    """Decrypts an admin-locked master key using AES-GCM, matching the server's encryption."""
    key = _derive_admin_key(admin_secret)
    raw = base64.b64decode(admin_locked_b64)
    iv, ciphertext = raw[:12], raw[12:]
    return AESGCM(key).decrypt(iv, ciphertext, None).decode()


def list_accounts(admin_secret):
    response = requests.get(
        f"{config.API_BASE}/admin-list-accounts",
        headers={"X-Admin-Secret": admin_secret},
        timeout=10,
    )
    data = response.json()
    if not data.get("success"):
        print(f"Error: {data.get('error')}")
        return False
    for acct in data["accounts"]:
        print(f"  {acct['username']}  [{_format_code(acct['id'])}]  ({acct['role']})")
    return True


def view_account(identifier, admin_secret):
    params = {"account_id": _normalize_code(identifier)} if _looks_like_code(identifier) else {"username": identifier}
    response = requests.get(
        f"{config.API_BASE}/admin-get-account",
        params=params,
        headers={"X-Admin-Secret": admin_secret},
        timeout=10,
    )
    data = response.json()
    if not data.get("success"):
        print(f"Error: {data.get('error')}")
        return

    account = data["account"]
    try:
        master_key_b64 = decrypt_admin_master_key(account["admin_locked_master_key"], admin_secret)
    except Exception:
        print("Couldn't decrypt this account's lockbox. It may still be locked with an older secret.")
        print("Log in as that account and run /changepassword to re-lock it with the current secret.")
        return
    print(f"\nUsername: {account['username']}")
    print(f"Code: {_format_code(account['id'])}")
    print(f"Role: {account['role']}")
    print(f"Decrypted master key: {master_key_b64}")


def _ask_secret():
    if "--visible" in sys.argv:
        return input("Enter your admin secret (visible on screen): ").strip()
    return getpass.getpass("Enter your admin secret (typing is hidden): ").strip()


if __name__ == "__main__":
    secret = _ask_secret()
    print("\nAccounts:")
    if list_accounts(secret):
        chosen = input("\nAccount code or username to view (Enter to quit): ").strip()
        if chosen:
            view_account(chosen, secret)