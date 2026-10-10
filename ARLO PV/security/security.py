# =============================================================
# SECURITY.PY
# SafeLock: envelope encryption backed by the live Cloudflare API.
# Every account is identified by a random 16-character code assigned
# by the server. Usernames are display names only and can repeat.
# The password-derived lock on the master key stays local; the admin
# lockbox is encrypted server-side with a secret that never ships here.
# =============================================================

import base64
import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import config

_current_account_id = None
_current_username = None
_unlocked_master_key = None
_current_salt = None
_current_role = "regular"


# -------------------------------------------------------------
# ACCOUNT CODES
# -------------------------------------------------------------

def normalize_code(text):
    """Strips dashes/spaces and uppercases, so AC3B-3CE6-9504-6010 and ac3b3ce695046010 match."""
    return "".join(ch for ch in str(text) if ch.isalnum()).upper()


def looks_like_code(text):
    code = normalize_code(text)
    return len(code) == 16 and all(ch in "0123456789ABCDEF" for ch in code)


def format_code(account_id):
    """Shows a code in groups of four, e.g. AC3B-3CE6-9504-6010."""
    code = normalize_code(account_id)
    return "-".join(code[i:i + 4] for i in range(0, len(code), 4))


# -------------------------------------------------------------
# CURRENT SESSION
# -------------------------------------------------------------

def get_current_account_id():
    return _current_account_id


def get_current_username():
    """The display name only. Never use this to identify the account to the server."""
    return _current_username


def get_role():
    return _current_role


def is_admin():
    return get_role() == "admin"


def can_see_debug():
    return get_role() in ("admin", "tester")


def get_master_key():
    if _unlocked_master_key is None:
        raise RuntimeError("No account is unlocked.")
    return _unlocked_master_key


# -------------------------------------------------------------
# ACCOUNTS
# -------------------------------------------------------------

def _derive_key_from_password(password, salt_b64):
    salt = base64.urlsafe_b64decode(salt_b64)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def fetch_account(account_id):
    """Returns {"id", "username", "role"} for an account code, or None if it doesn't exist
    or the server can't be reached."""
    try:
        response = requests.post(f"{config.API_BASE}/login", json={"account_id": normalize_code(account_id)}, timeout=10)
        data = response.json()
    except Exception:
        return None
    if not data.get("success"):
        return None
    account = data["account"]
    return {"id": account["id"], "username": account["username"], "role": account.get("role", "regular")}


def create_account(username, password):
    """Creates an account and logs it in. Returns (account_id, None) on success or (None, error_text).
    The server generates the code and always makes the account 'regular'."""
    global _current_account_id, _current_username, _unlocked_master_key, _current_salt, _current_role

    salt = Fernet.generate_key()
    master_key = Fernet.generate_key()
    salt_b64 = base64.urlsafe_b64encode(salt).decode()

    password_key = _derive_key_from_password(password, salt_b64)
    locked_master_key = Fernet(password_key).encrypt(master_key).decode()

    try:
        response = requests.post(f"{config.API_BASE}/create-account", json={
            "username": username,
            "salt": salt_b64,
            "locked_master_key": locked_master_key,
            "master_key_plain": master_key.decode(),
        }, timeout=10)
        data = response.json()
    except Exception as e:
        return None, f"could not reach the server ({e})"

    if not data.get("success"):
        return None, data.get("error", "unknown error")
    account_id = data.get("account_id")
    if not account_id:
        return None, "the server did not return an account code (is the server up to date?)"

    _current_account_id = account_id
    _current_username = username
    _unlocked_master_key = master_key
    _current_salt = salt
    _current_role = "regular"
    return account_id, None


def unlock(account_id, password):
    """Logs into an account with its password. Returns True on success."""
    global _current_account_id, _current_username, _unlocked_master_key, _current_salt, _current_role

    try:
        response = requests.post(f"{config.API_BASE}/login", json={"account_id": normalize_code(account_id)}, timeout=10)
        data = response.json()
    except Exception:
        return False
    if not data.get("success"):
        return False

    account = data["account"]
    salt_b64 = account["salt"]
    locked_master_key = account["locked_master_key"]

    password_key = _derive_key_from_password(password, salt_b64)
    try:
        master_key = Fernet(password_key).decrypt(locked_master_key.encode())
    except Exception:
        return False

    _current_account_id = account["id"]
    _current_username = account["username"]
    _unlocked_master_key = master_key
    _current_salt = base64.urlsafe_b64decode(salt_b64)
    _current_role = account.get("role", "regular")
    return True


def change_password(account_id, old_password, new_password):
    if not unlock(account_id, old_password):
        return False

    master_key = get_master_key()
    salt_b64 = base64.urlsafe_b64encode(_current_salt).decode()

    new_password_key = _derive_key_from_password(new_password, salt_b64)
    locked_master_key = Fernet(new_password_key).encrypt(master_key).decode()

    try:
        response = requests.post(f"{config.API_BASE}/update-password", json={
            "account_id": normalize_code(account_id),
            "salt": salt_b64,
            "locked_master_key": locked_master_key,
            "master_key_plain": master_key.decode(),
        }, timeout=10)
        return bool(response.json().get("success"))
    except Exception:
        return False


def delete_account(account_id):
    """Permanently deletes an account and its data. Returns True if the server confirmed it."""
    try:
        response = requests.post(f"{config.API_BASE}/delete-account", json={"account_id": normalize_code(account_id)}, timeout=10)
        return bool(response.json().get("success"))
    except Exception:
        return False


def set_role(target, new_role, admin_code):
    """Changes an account's role. target is an account code, or a username (only accepted if exactly
    one account has that name). The server checks admin_code. Returns (True, None) or (False, error_text)."""
    global _current_role
    body = {"role": new_role, "admin_code": admin_code}
    is_code = looks_like_code(target)
    if is_code:
        body["account_id"] = normalize_code(target)
    else:
        body["username"] = target

    try:
        response = requests.post(f"{config.API_BASE}/set-role", json=body, timeout=10)
        data = response.json()
    except Exception as e:
        return False, f"could not reach the server ({e})"

    if not data.get("success"):
        return False, data.get("error", "Unknown error")

    if (is_code and body["account_id"] == _current_account_id) or (not is_code and target == _current_username):
        _current_role = new_role
    return True, None


# -------------------------------------------------------------
# PER-ACCOUNT SETTINGS (always for the logged-in account)
# -------------------------------------------------------------

def save_setting(key, value):
    try:
        requests.post(f"{config.API_BASE}/save-setting", json={"account_id": _current_account_id, "key": key, "value": value}, timeout=10)
    except Exception:
        pass


def get_setting(key, default=None):
    try:
        response = requests.get(f"{config.API_BASE}/get-setting", params={"account_id": _current_account_id, "key": key}, timeout=10)
        value = response.json().get("value")
    except Exception:
        return default
    if value is None:
        return default
    if str(value).lower() in ("true", "false"):
        return str(value).lower() == "true"
    return value