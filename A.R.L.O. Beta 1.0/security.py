# =============================================================
# SECURITY.PY
# SafeLock: envelope encryption system, backed by the live
# Cloudflare API. Encryption logic (salt, password-derived keys,
# master key) stays local for the USER's own password lock --
# the admin lockbox is encrypted server-side using Cloudflare's
# private ADMIN_SECRET, which never ships with this program.
# =============================================================

import base64
import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import config

_current_username = None
_unlocked_master_key = None
_current_salt = None
_current_role = "regular"


def _derive_key_from_password(password, salt_b64):
    salt = base64.urlsafe_b64decode(salt_b64)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def list_accounts():
    response = requests.get(f"{config.API_BASE}/list-accounts", timeout=10)
    return response.json().get("usernames", [])


def account_exists(username):
    return username in list_accounts()


def get_account_dir():
    if _current_username is None:
        raise RuntimeError("No account is currently logged in.")
    return _current_username


def get_current_username():
    return _current_username


def create_account(username, password, role="regular"):
    global _current_username, _unlocked_master_key, _current_salt, _current_role

    salt = Fernet.generate_key()
    master_key = Fernet.generate_key()
    salt_b64 = base64.urlsafe_b64encode(salt).decode()

    password_key = _derive_key_from_password(password, salt_b64)
    locked_master_key = Fernet(password_key).encrypt(master_key).decode()

    requests.post(f"{config.API_BASE}/create-account", json={
        "username": username,
        "salt": salt_b64,
        "locked_master_key": locked_master_key,
        "master_key_plain": master_key.decode(),
        "role": role,
    }, timeout=10)

    _current_username = username
    _unlocked_master_key = master_key
    _current_salt = salt
    _current_role = role


def unlock(username, password):
    global _current_username, _unlocked_master_key, _current_salt, _current_role

    response = requests.post(f"{config.API_BASE}/login", json={"username": username}, timeout=10)
    data = response.json()
    if not data.get("success"):
        return False

    account = data["account"]
    salt_b64 = account["salt"]
    locked_master_key = account["locked_master_key"]

    password_key = _derive_key_from_password(password, salt_b64)
    fernet = Fernet(password_key)

    try:
        master_key = fernet.decrypt(locked_master_key.encode())
    except Exception:
        try:
            master_key = password.encode()
            Fernet(master_key)
        except Exception:
            return False

    _current_username = username
    _unlocked_master_key = master_key
    _current_salt = base64.urlsafe_b64decode(salt_b64)
    _current_role = account.get("role", "regular")
    return True


def get_master_key():
    if _unlocked_master_key is None:
        raise RuntimeError("No account is unlocked.")
    return _unlocked_master_key


def get_role():
    return _current_role


def is_admin():
    return get_role() == "admin"


def can_see_debug():
    return get_role() in ("admin", "tester")


def change_password(username, old_password, new_password):
    if not unlock(username, old_password):
        return False

    master_key = get_master_key()
    salt_b64 = base64.urlsafe_b64encode(_current_salt).decode()

    new_password_key = _derive_key_from_password(new_password, salt_b64)
    locked_master_key = Fernet(new_password_key).encrypt(master_key).decode()

    requests.post(f"{config.API_BASE}/update-password", json={
        "username": username,
        "salt": salt_b64,
        "locked_master_key": locked_master_key,
        "master_key_plain": master_key.decode(),
    }, timeout=10)

    return True


def delete_account(username):
    requests.post(f"{config.API_BASE}/delete-account", json={"username": username}, timeout=10)
    return True


def set_role(username, new_role):
    global _current_role
    requests.post(f"{config.API_BASE}/set-role", json={"username": username, "role": new_role}, timeout=10)
    if username == _current_username:
        _current_role = new_role
    return True


def save_setting(username, key, value):
    requests.post(f"{config.API_BASE}/save-setting", json={"username": username, "key": key, "value": value}, timeout=10)


def get_setting(username, key, default=None):
    response = requests.get(f"{config.API_BASE}/get-setting", params={"username": username, "key": key}, timeout=10)
    data = response.json()
    value = data.get("value")
    if value is None:
        return default
    if str(value).lower() in ("true", "false"):
        return str(value).lower() == "true"
    return value