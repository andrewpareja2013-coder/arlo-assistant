# =============================================================
# PASSWORD_BANK_TOOL.PY
# Stores and retrieves saved credentials, encrypted using the
# account's own master key before ever being sent to the server.
# The server only ever sees ciphertext, never real passwords.
# =============================================================

import json
import requests
from cryptography.fernet import Fernet
import config
import security
from tools.registry import register


def add_password(service, username_for_service, password_value):
    """Encrypts and saves a credential for a service, tied to the current account."""
    fernet = Fernet(security.get_master_key())
    data = json.dumps({"username": username_for_service, "password": password_value})
    encrypted = fernet.encrypt(data.encode()).decode()

    current_user = security.get_current_username()
    requests.post(f"{config.API_BASE}/save-password", json={
        "username": current_user,
        "service": service,
        "encrypted_data": encrypted,
    }, timeout=10)

    return f"Saved credentials for {service}, sir."


def get_password(service):
    """Retrieves and decrypts all saved credentials matching a service name."""
    current_user = security.get_current_username()
    response = requests.get(f"{config.API_BASE}/get-passwords", params={"username": current_user}, timeout=10)
    passwords = response.json().get("passwords", [])

    fernet = Fernet(security.get_master_key())
    matches = []
    for entry in passwords:
        if entry["service"].lower() == service.lower():
            decrypted = fernet.decrypt(entry["encrypted_data"].encode()).decode()
            data = json.loads(decrypted)
            matches.append(f"Username: {data['username']}, Password: {data['password']}")

    if not matches:
        return f"I don't have any credentials saved for {service}, sir."
    if len(matches) == 1:
        return matches[0]
    return f"I found {len(matches)} entries for {service}, sir:\n" + "\n".join(matches)


def list_password_services():
    """Lists saved credentials (service + username, not passwords) in the password bank."""
    current_user = security.get_current_username()
    response = requests.get(f"{config.API_BASE}/get-passwords", params={"username": current_user}, timeout=10)
    passwords = response.json().get("passwords", [])

    if not passwords:
        return "You have no saved credentials, sir."

    fernet = Fernet(security.get_master_key())
    lines = []
    for entry in passwords:
        decrypted = fernet.decrypt(entry["encrypted_data"].encode()).decode()
        data = json.loads(decrypted)
        lines.append(f"{entry['service']} -- {data['username']}")

    return "Saved credentials:\n" + "\n".join(lines)


def delete_password(service):
    """Deletes a saved credential by service name."""
    current_user = security.get_current_username()
    response = requests.get(f"{config.API_BASE}/get-passwords", params={"username": current_user}, timeout=10)
    passwords = response.json().get("passwords", [])

    matches = [p for p in passwords if p["service"].lower() == service.lower()]

    if not matches:
        return f"I don't have any credentials saved for {service}, sir."

    for entry in matches:
        requests.post(f"{config.API_BASE}/delete-password", json={"id": entry["id"]}, timeout=10)

    return f"Deleted {len(matches)} credential(s) for {service}, sir."


register(
    name="delete_password",
    description="Delete saved credential(s) from the password bank by service name. Use this when the user asks to remove or delete a saved password.",
    parameters={
        "type": "object",
        "properties": {
            "service": {"type": "string", "description": "Name of the service to delete credentials for."}
        },
        "required": ["service"],
    },
    function=delete_password,
    requires_confirmation=True,
)

register(
    name="add_password",
    description="Save a username/password credential to the encrypted password bank. Use this when the user asks to save or store a password for a service. If the user might have multiple accounts for the same service (e.g. two Gmail accounts), ask them to give each a distinguishing name, like 'gmail-personal' and 'gmail-work', rather than saving both under the same generic service name.",
    parameters={
        "type": "object",
        "properties": {
            "service": {"type": "string", "description": "Name of the service, e.g. 'gmail' or 'gmail-work' if there are multiple accounts for the same service."},
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
    description="Retrieve a saved credential from the encrypted password bank. Use this when the user asks you to recall a saved password.",
    parameters={
        "type": "object",
        "properties": {
            "service": {"type": "string", "description": "Name of the service to retrieve credentials for."}
        },
        "required": ["service"],
    },
    function=get_password,
    requires_confirmation=True,
)

register(
    name="list_password_services",
    description=(
        "List saved credentials (service and username, not passwords) in the password bank. "
        "Use this whenever the user asks what accounts/passwords/logins they have saved, including "
        "casual phrasing like 'list my gmails' or 'what accounts do I have' -- this almost always means "
        "the password bank, NOT the user's actual email inbox, which you cannot access."
    ),
    parameters={"type": "object", "properties": {}},
    function=list_password_services,
)