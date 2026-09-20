# =============================================================
# MAIN.PY
# The entry point. Runs the conversation loop, handles special
# commands, and ties memory, brain, and tools together.
# =============================================================

import os
import sys
import itertools
import textwrap
import threading
import requests
import time as time_module
from datetime import datetime
from memory import Memory
from brain import get_reply, update_long_term_memory
from tools.registry import TOOLS
from tools.time_tool import get_time
from boot import run_boot_check
from custom_input import get_input, alert_interrupt
from hardware_limits import detect_and_save_thresholds
from librehardwaremonitor_launcher import ensure_lhm_running
from voice_input import listen_for_wake_word, speak
import security
import config

COMMANDS = {
    "/help": "List all available commands.",
    "/changepassword": "Change your account password.",
    "/setrole": "(Admin only) Change an account's role.",
}


def arlo_says(text):
    print("ARLO :", text)


def run_with_spinner(func, message="Loading"):
    """Runs a function while showing a spinning animation, then clears it."""
    done = threading.Event()

    def spin():
        for char in itertools.cycle("-\\|/"):
            if done.is_set():
                break
            sys.stdout.write(f"\r{message}... {char}")
            sys.stdout.flush()
            time_module.sleep(0.1)
        sys.stdout.write("\r" + " " * (len(message) + 10) + "\r")
        sys.stdout.flush()

    spinner_thread = threading.Thread(target=spin, daemon=True)
    spinner_thread.start()

    result = func()

    done.set()
    spinner_thread.join()
    return result


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
    import local_accounts

    while True:
        os.system("cls")
        accounts = local_accounts.get_local_accounts()

        width = 40
        title = "A . R . L . O ."
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
            os.system("cls")
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
            os.system("cls")
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
            role = input("  Role (admin/tester/regular) [regular]: ").strip().lower()
            if role not in ("admin", "tester", "regular"):
                role = "regular"
            security.create_account(username, password, role)
            local_accounts.add_local_account(username)
            run_setup_questions(username)
            print(f"\n  Account '{username}' created successfully.")
            input("  Press Enter to continue...")
            os.system("cls")
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
                os.system("cls")
                return
            print("\n  Incorrect password.")
            input("  Press Enter to continue...")

        else:
            print("\n  Invalid selection.")
            input("  Press Enter to continue...")


def check_alarms():
    while True:
        now = datetime.now()
        for alarm in memory.alarms:
            if not alarm["fired"] and now >= alarm["time"]:
                alarm["fired"] = True
                requests.post(f"{config.API_BASE}/mark-alarm-fired", json={"id": alarm["id"]}, timeout=10)
                alert_interrupt(f"🔔 ALARM: {alarm['description']}")
        time_module.sleep(2)


def handle_voice_command(command_text):
    """Called when the wake word is detected and a command is transcribed."""
    print(f"\nYou (voice): {command_text}")
    reply = get_reply(command_text, memory)
    wrapped_reply = textwrap.fill(reply, width=80)
    arlo_says(wrapped_reply)
    speak(reply)


# -------------------------------------------------------------
# STARTUP
# -------------------------------------------------------------

login()

memory = Memory()
boot_summary = run_with_spinner(lambda: run_boot_check(memory), message="Starting A.R.L.O.")
run_with_spinner(detect_and_save_thresholds, message="Checking hardware")
run_with_spinner(ensure_lhm_running, message="Preparing system monitor")

if config.TEST_MODE and security.can_see_debug():
    print(boot_summary)

current_time = get_time()
arlo_says(f"Hello Sir, it is currently {current_time}.")

now = datetime.now()
missed_any = False
for alarm in memory.alarms:
    if not alarm["fired"] and now >= alarm["time"]:
        alarm["fired"] = True
        missed_any = True
        arlo_says(f"While you were away, this alarm went off: {alarm['description']} (was set for {alarm['time'].strftime('%I:%M %p')})")
if missed_any:
    memory.save_alarms()

alarm_thread = threading.Thread(target=check_alarms, daemon=True)
alarm_thread.start()

voice_thread = threading.Thread(target=listen_for_wake_word, args=(handle_voice_command,), daemon=True)
voice_thread.start()


# -------------------------------------------------------------
# MAIN LOOP
# -------------------------------------------------------------

while True:
    user_input = get_input("You: ")

    if user_input.strip() == "":
        update_long_term_memory(memory)
        os.system("cls")
        break

    if memory.pending_action:
        tool_name = memory.pending_action["tool_name"]
        if tool_name == "add_and_open_app":
            app_name = memory.pending_action["tool_input"]["app_name"]
            memory.pending_action = None
            result = TOOLS["add_and_open_app"]["function"](app_name, user_input.strip())
            arlo_says(result)
        elif tool_name == "add_and_open_website":
            site_name = memory.pending_action["tool_input"]["site_name"]
            memory.pending_action = None
            result = TOOLS["add_and_open_website"]["function"](site_name, user_input.strip())
            arlo_says(result)
        elif user_input.lower() in ["yes", "y", "confirm"]:
            tool_input = memory.pending_action["tool_input"]
            function = TOOLS[tool_name]["function"]
            result = function(**tool_input) if tool_input else function()
            memory.add_action(f"{tool_name}: {tool_input} (confirmed)")
            memory.pending_action = None
            arlo_says(result)
        else:
            memory.pending_action = None
            arlo_says("Understood, action cancelled, sir.")
        continue

    if user_input == "/help":
        arlo_says("Here are the commands I understand:")
        for cmd, desc in COMMANDS.items():
            print(f"  {cmd} -- {desc}")
        continue

    if user_input == "/changepassword":
        old = input("Current password: ")
        new = input("New password: ")
        confirm = input("Confirm new password: ")
        if new != confirm:
            arlo_says("New passwords didn't match, sir.")
        elif security.change_password(security.get_current_username(), old, new):
            arlo_says("Password changed successfully, sir.")
        else:
            arlo_says("That current password was incorrect, sir.")
        continue

    if user_input == "/setrole":
        if not security.is_admin():
            arlo_says("Only admins can change account roles, sir.")
            continue
        target = input("Username to change: ").strip()
        new_role = input("New role (admin/tester/regular): ").strip().lower()
        if security.set_role(target, new_role):
            arlo_says(f"'{target}' is now set to '{new_role}', sir.")
        else:
            arlo_says("That username or role was invalid, sir.")
        continue

    reply = get_reply(user_input, memory)
    wrapped_reply = textwrap.fill(reply, width=80)
    arlo_says(wrapped_reply)