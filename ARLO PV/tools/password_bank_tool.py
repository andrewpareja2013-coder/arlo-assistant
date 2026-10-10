# =============================================================
# PASSWORD_BANK_TOOL.PY
# Stores and retrieves saved credentials, encrypted with the
# account's own master key before ever being sent to the server.
# The server only ever sees ciphertext, never real passwords.
# =============================================================

import json
import requests
from cryptography.fernet import Fernet
import config
import security
from tools.registry import register

CONNECTION_ERROR = "I couldn't reach the password bank, sir. Please check the connection and try again."
LOCKED_ERROR = "I couldn't unlock the password bank, sir."


def _get_fernet():
    """Returns a Fernet for the account's master key, or None if it isn't available."""
    try:
        key = security.get_master_key()
        return Fernet(key) if key else None
    except Exception:
        return None


def _decrypt(fernet, entry):
    """Returns the decrypted entry as a dict, or None if it can't be read."""
    try:
        return json.loads(fernet.decrypt(entry["encrypted_data"].encode()).decode())
    except Exception:
        return None


def _fetch_entries():
    """Returns the list of saved entries, or None if the server couldn't be reached."""
    try:
        response = requests.get(
            f"{config.API_BASE}/get-passwords",
            params={"account_id": security.get_current_account_id()},
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("passwords", [])
    except Exception:
        return None


def _post(path, payload):
    """Sends a request to the server. Returns True only if the server accepted it."""
    try:
        response = requests.post(f"{config.API_BASE}{path}", json=payload, timeout=10)
        response.raise_for_status()
        try:
            return bool(response.json().get("success", True))
        except ValueError:
            return True
    except Exception:
        return False


def add_password(service, username_for_service, password_value):
    fernet = _get_fernet()
    if fernet is None:
        return LOCKED_ERROR

    data = json.dumps({"username": username_for_service, "password": password_value})
    encrypted = fernet.encrypt(data.encode()).decode()

    saved = _post("/save-password", {
        "account_id": security.get_current_account_id(),
        "service": service,
        "encrypted_data": encrypted,
    })
    if not saved:
        return f"I couldn't save the credentials for {service}, sir. Please try again."

    return f"Saved credentials for {service}, sir."


def get_password(service):
    fernet = _get_fernet()
    if fernet is None:
        return LOCKED_ERROR

    entries = _fetch_entries()
    if entries is None:
        return CONNECTION_ERROR

    matches = []
    unreadable = 0
    for entry in entries:
        if entry["service"].lower() == service.lower():
            data = _decrypt(fernet, entry)
            if data is None:
                unreadable += 1
            else:
                matches.append(f"Username: {data['username']}, Password: {data['password']}")

    if not matches:
        if unreadable:
            return f"I found {unreadable} entry for {service}, sir, but couldn't decrypt it."
        return f"I don't have any credentials saved for {service}, sir."

    result = matches[0] if len(matches) == 1 else f"I found {len(matches)} entries for {service}, sir:\n" + "\n".join(matches)
    if unreadable:
        result += f"\n({unreadable} other entry couldn't be decrypted.)"
    return result


def delete_password(service):
    entries = _fetch_entries()
    if entries is None:
        return CONNECTION_ERROR

    matches = [p for p in entries if p["service"].lower() == service.lower()]
    if not matches:
        return f"I don't have any credentials saved for {service}, sir."

    deleted = sum(1 for entry in matches if _post("/delete-password", {"id": entry["id"]}))

    if deleted == 0:
        return f"I couldn't delete the credentials for {service}, sir. Please try again."
    if deleted < len(matches):
        return f"Deleted {deleted} of {len(matches)} credential(s) for {service}, sir. Please try again for the rest."
    return f"Deleted {deleted} credential(s) for {service}, sir."


def list_password_services():
    fernet = _get_fernet()
    if fernet is None:
        return LOCKED_ERROR

    entries = _fetch_entries()
    if entries is None:
        return CONNECTION_ERROR
    if not entries:
        return "You have no saved credentials, sir."

    lines = []
    for entry in entries:
        data = _decrypt(fernet, entry)
        if data is None:
            lines.append(f"{entry['service']} -- (couldn't be decrypted)")
        else:
            lines.append(f"{entry['service']} -- {data['username']}")

    return "Saved credentials:\n" + "\n".join(lines)


register(
    name="add_password",
    description=(
        "Save a username/password credential to the encrypted password bank. If the user might have "
        "multiple accounts for the same service, ask them to give each a distinguishing name, like "
        "'gmail-personal' and 'gmail-work', rather than saving both under the same generic service name."
    ),
    parameters={
        "type": "object",
        "properties": {
            "service": {"type": "string", "description": "Name of the service, e.g. 'gmail'."},
            "username_for_service": {"type": "string", "description": "The username or email for this account."},
            "password_value": {"type": "string", "description": "The password to save."},
        },
        "required": ["service", "username_for_service", "password_value"],
    },
    function=add_password,
    requires_confirmation=True,
)

register(
    name="get_password",
    description="Retrieve a saved credential from the encrypted password bank.",
    parameters={
        "type": "object",
        "properties": {"service": {"type": "string", "description": "Service to retrieve credentials for."}},
        "required": ["service"],
    },
    function=get_password,
    requires_confirmation=True,
)

register(
    name="delete_password",
    description="Delete saved credential(s) from the password bank by service name.",
    parameters={
        "type": "object",
        "properties": {"service": {"type": "string", "description": "Service to delete credentials for."}},
        "required": ["service"],
    },
    function=delete_password,
    requires_confirmation=True,
)

register(
    name="list_password_services",
    description=(
        "List saved credentials (service and username, not passwords) in the password bank. "
        "Use this whenever the user asks what accounts/passwords/logins they have saved, including "
        "casual phrasing like 'list my gmails' -- this means the password bank, NOT the user's actual "
        "email inbox, which you cannot access."
    ),
    parameters={"type": "object", "properties": {}},
    function=list_password_services,
)