# =============================================================
# LOGIN.PY
# The account selection screen: create new, add existing, remove
# from this device's list, delete permanently, or log in.
# =============================================================

import os
import security
import config
from security import local_accounts


def run_setup_questions(username):
    print("\nLet's set a few preferences.")
    temp_unit = input("Fahrenheit or celsius? (F/C) [fahrenheit]: ").strip().lower()
    if temp_unit in ("c", "celsius"):
        temp_unit = "celsius"
    else:
        temp_unit = "fahrenheit"
    security.save_setting(username, "temperature_unit", temp_unit)

    military = input("Use 24-hour military time? (yes/no) [no]: ").strip().lower()
    security.save_setting(username, "military_time", military == "yes")
    print("Preferences saved.\n")


def login():
    """Handles account selection: create new, add existing, remove from list, log in, or delete one."""
    while True:
        os.system("cls" if os.name == "nt" else "clear")
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

        if not accounts:
            print("  No accounts exist yet. Let's create one.\n")
            username = input("  Choose a username: ").strip()
            password = input("  Create a password: ")
            confirm = input("  Confirm password: ")
            if password != confirm or password.strip() == "":
                print("\n  Passwords didn't match or were empty. Try again.")
                input("  Press Enter to continue...")
                continue
            security.create_account(username, password, "admin")
            local_accounts.add_local_account(username)
            run_setup_questions(username)
            print(f"\n  Account '{username}' created successfully.")
            input("  Press Enter to continue...")
            os.system("cls" if os.name == "nt" else "clear")
            return

        print("  ── Accounts on this device ──")
        for i, name in enumerate(accounts, start=1):
            print(f"    [{i}]  {name}")
        print()
        print("  ── Options ──")
        print("    [N]  Create new account")
        print("    [A]  Add an existing account to this device")
        print("    [R]  Remove an account from this list")
        print("    [D]  Delete an account permanently")
        print("    [↵]  Exit")
        print()
        choice = input("  Select: ").strip()

        if choice == "":
            os.system("cls" if os.name == "nt" else "clear")
            exit()

        elif choice.lower() == "n":
            print()
            username = input("  Choose a username: ").strip()
            if security.account_exists(username):
                print("\n  That username is already taken.")
                input("  Press Enter to continue...")
                continue
            password = input("  Create a password: ")
            confirm = input("  Confirm password: ")
            if password != confirm or password.strip() == "":
                print("\n  Passwords didn't match or were empty. Try again.")
                input("  Press Enter to continue...")
                continue
            security.create_account(username, password, "regular")
            local_accounts.add_local_account(username)
            run_setup_questions(username)
            print(f"\n  Account '{username}' created successfully.")
            input("  Press Enter to continue...")
            os.system("cls" if os.name == "nt" else "clear")
            return

        elif choice.lower() == "a":
            print()
            username = input("  Username to add: ").strip()
            if not security.account_exists(username):
                print("\n  No account with that username exists.")
                input("  Press Enter to continue...")
                continue
            local_accounts.add_local_account(username)
            print(f"\n  '{username}' added to this device's login list.")
            input("  Press Enter to continue...")
            continue

        elif choice.lower() == "r":
            print()
            username = input("  Which username to remove from this list? ").strip()
            local_accounts.remove_local_account(username)
            print(f"\n  '{username}' removed from this device's list. The account itself is untouched.")
            input("  Press Enter to continue...")
            continue

        elif choice.lower() == "d":
            print()
            username = input("  Which username do you want to permanently delete? ").strip()
            if not security.account_exists(username):
                print("\n  That account doesn't exist.")
                input("  Press Enter to continue...")
                continue
            confirm = input(f"  Type 'yes' to permanently delete '{username}' and all its data: ")
            if confirm.lower() == "yes":
                security.delete_account(username)
                local_accounts.remove_local_account(username)
                print(f"\n  Account '{username}' deleted.")
            input("  Press Enter to continue...")
            continue

        elif choice.isdigit() and 1 <= int(choice) <= len(accounts):
            username = accounts[int(choice) - 1]
            password = input(f"  Password for {username}: ")
            if security.unlock(username, password):
                print(f"\n  Welcome back, {username}.")
                input("  Press Enter to continue...")
                os.system("cls" if os.name == "nt" else "clear")
                return
            print("\n  Incorrect password.")
            input("  Press Enter to continue...")

        else:
            print("\n  Invalid selection.")
            input("  Press Enter to continue...")