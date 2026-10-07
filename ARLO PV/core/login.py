# =============================================================
# LOGIN.PY
# The account selection screen: create a new account, add an existing
# one with its code, remove one from this device's list, delete one
# permanently, or log in.
# =============================================================

import os
import config
import security
from security import local_accounts


def _clear():
    os.system("cls" if os.name == "nt" else "clear")


def _pause():
    input("  Press Enter to continue...")


def _labels(accounts):
    """Names for the login list. Accounts sharing a name also show the end of their code."""
    counts = {}
    for acct in accounts:
        counts[acct["name"]] = counts.get(acct["name"], 0) + 1
    labels = []
    for acct in accounts:
        if counts[acct["name"]] > 1:
            labels.append(f"{acct['name']}  (code ends {acct['id'][-4:]})")
        else:
            labels.append(acct["name"])
    return labels, [name for name, count in counts.items() if count > 1]


def run_setup_questions():
    print("\nLet's set a few preferences.")
    temp_unit = input("Fahrenheit or celsius? (F/C) [fahrenheit]: ").strip().lower()
    if temp_unit in ("c", "celsius"):
        temp_unit = "celsius"
    else:
        temp_unit = "fahrenheit"
    security.save_setting("temperature_unit", temp_unit)

    military = input("Use 24-hour military time? (yes/no) [no]: ").strip().lower()
    security.save_setting("military_time", military == "yes")
    print("Preferences saved.\n")


def _warn_same_name(accounts, name):
    """Warns when an account with this name is already on the device. Returns True to go ahead."""
    same = [a for a in accounts if a["name"].lower() == name.lower()]
    if not same:
        return True
    print(f"\n  Warning: this device already has an account named '{same[0]['name']}'.")
    print("  Two accounts can share a name, but they are different accounts with separate data.")
    print("  The login list will show the end of each account's code so you can tell them apart.")
    return input("  Continue? (yes/no): ").strip().lower() in ("yes", "y")


def _create_account_flow(accounts):
    """Returns True if an account was created (the user is then logged in)."""
    print()
    username = input("  Choose a username: ").strip()
    if username == "":
        print("\n  A username is required.")
        _pause()
        return False
    if not _warn_same_name(accounts, username):
        return False

    password = input("  Create a password: ")
    confirm = input("  Confirm password: ")
    if password != confirm or password.strip() == "":
        print("\n  Passwords didn't match or were empty. Try again.")
        _pause()
        return False

    account_id, error = security.create_account(username, password)
    if account_id is None:
        print(f"\n  Couldn't create the account: {error}")
        _pause()
        return False

    local_accounts.add_local_account(account_id, username)
    run_setup_questions()
    print(f"  Account '{username}' created.")
    print(f"  Your account code: {security.format_code(account_id)}")
    print("  Keep it private. You need it to add this account on another device.")
    print("  You can see it again any time by typing /mycode.")
    input("\n  Press Enter to continue...")
    return True


def _add_account_flow(accounts):
    print()
    raw = input("  Account code to add: ").strip()
    if not security.looks_like_code(raw):
        print("\n  That doesn't look like an account code. It has 16 letters and numbers,")
        print("  like AC3B-3CE6-9504-6010.")
        _pause()
        return

    account_id = security.normalize_code(raw)
    if any(a["id"] == account_id for a in accounts):
        print("\n  That account is already on this device.")
        _pause()
        return

    account = security.fetch_account(account_id)
    if account is None:
        print("\n  No account with that code was found (or the server couldn't be reached).")
        _pause()
        return

    if not _warn_same_name(accounts, account["username"]):
        return

    local_accounts.add_local_account(account_id, account["username"])
    print(f"\n  '{account['username']}' added to this device's login list.")
    _pause()


def _remove_flow(accounts):
    print()
    raw = input("  Number of the account to remove from this list: ").strip()
    if raw.isdigit() and 1 <= int(raw) <= len(accounts):
        entry = accounts[int(raw) - 1]
        local_accounts.remove_local_account(entry["id"])
        print(f"\n  '{entry['name']}' removed from this device's list. The account itself is untouched.")
    else:
        print("\n  That isn't a number on the list.")
    _pause()


def _delete_flow(accounts):
    print()
    raw = input("  Number from the list, or a full account code, to delete permanently: ").strip()
    if raw.isdigit() and 1 <= int(raw) <= len(accounts):
        entry = accounts[int(raw) - 1]
        target_id, name = entry["id"], entry["name"]
    elif security.looks_like_code(raw):
        target_id = security.normalize_code(raw)
        account = security.fetch_account(target_id)
        if account is None:
            print("\n  No account with that code was found.")
            _pause()
            return
        name = account["username"]
    else:
        print("\n  That isn't a number on the list or an account code.")
        _pause()
        return

    confirm = input(f"  Type 'yes' to permanently delete '{name}' ({security.format_code(target_id)}) and all its data: ")
    if confirm.strip().lower() == "yes":
        if security.delete_account(target_id):
            local_accounts.remove_local_account(target_id)
            print(f"\n  Account '{name}' deleted.")
        else:
            print("\n  The server couldn't delete that account.")
    _pause()


def login():
    """Runs the account screen until someone is logged in."""
    while True:
        _clear()
        accounts = local_accounts.get_local_accounts()

        width = 40
        title = " . ".join(config.WAKE_KEYWORD.upper()) + " ."
        subtitle = "Automated Resource & Logic Operator"
        print()
        print("╔" + "═" * width + "╗")
        print("║" + title.center(width) + "║")
        print("║" + subtitle.center(width) + "║")
        print("╚" + "═" * width + "╝")
        print()

        print("  ── Accounts on this device ──")
        if accounts:
            labels, shared_names = _labels(accounts)
            for i, label in enumerate(labels, start=1):
                print(f"    [{i}]  {label}")
            if shared_names:
                names = ", ".join(repr(n) for n in shared_names)
                print(f"\n  Note: more than one account here is named {names}.")
                print("  They are different accounts. The code ending next to each tells them apart.")
        else:
            print("    (none yet)")
        print()
        print("  ── Options ──")
        print("    [N]  Create new account")
        print("    [A]  Add an existing account using its code")
        print("    [R]  Remove an account from this list")
        print("    [D]  Delete an account permanently")
        print("    [↵]  Exit")
        print()
        choice = input("  Select: ").strip()

        if choice == "":
            _clear()
            exit()

        elif choice.lower() == "n":
            if _create_account_flow(accounts):
                _clear()
                return

        elif choice.lower() == "a":
            _add_account_flow(accounts)

        elif choice.lower() == "r":
            _remove_flow(accounts)

        elif choice.lower() == "d":
            _delete_flow(accounts)

        elif choice.isdigit() and 1 <= int(choice) <= len(accounts):
            entry = accounts[int(choice) - 1]
            password = input(f"  Password for {entry['name']}: ")
            if security.unlock(entry["id"], password):
                print(f"\n  Welcome back, {entry['name']}.")
                _pause()
                _clear()
                return
            print("\n  Incorrect password, or this account no longer exists on the server.")
            _pause()

        else:
            print("\n  Invalid selection.")
            _pause()