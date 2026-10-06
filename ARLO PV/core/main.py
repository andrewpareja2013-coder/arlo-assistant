# =============================================================
# MAIN.PY
# The entry point. Runs the conversation loop, handles special
# commands, and ties memory, brain, and tools together.
# =============================================================

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import updater
import textwrap
import threading
import requests
from datetime import datetime
from memory import Memory
from brain import get_reply, update_long_term_memory
from tools.registry import TOOLS
from tools.time_tool import get_time
from boot import run_boot_check
from custom_input import get_input, alert_interrupt
from hardware import detect_and_save_thresholds, ensure_lhm_running
import security
import config

from login import login
from ui import arlo_says, run_with_spinner, run_with_dots, enable_screen_capture, print_divider
from hub import show_hub

COMMANDS = {
    "/help": "List all available commands.",
    "/hub": "(Admin only) View activity across all accounts.",
    "/changepassword": "Change your account password.",
    "/setrole": "(Admin only) Change an account's role.",
    "/update": "Manually check for and install updates.",
    "/logout": "Log out and return to the account selection screen.",
}


def check_alarms(memory, stop_event):
    """Fires alarms for one session. Stops when that session ends."""
    while not stop_event.is_set():
        now = datetime.now()
        for alarm in memory.alarms:
            if stop_event.is_set():
                return
            if not alarm["fired"] and now >= alarm["time"]:
                alarm["fired"] = True
                requests.post(f"{config.API_BASE}/mark-alarm-fired", json={"id": alarm["id"]}, timeout=10)
                alert_interrupt(f"🔔 ALARM: {alarm['description']}")
        stop_event.wait(2)


def _load_voice():
    """Loads the voice code only when voice is turned on.
    Returns (listen_for_wake_word, speak, error_text). On failure the first two are None."""
    try:
        from voice_input import listen_for_wake_word, speak
        return listen_for_wake_word, speak, None
    except (ImportError, OSError) as e:
        return None, None, str(e)


def handle_voice_command(command_text, memory, speak):
    """Called when the wake word is detected and a command is transcribed."""
    print(f"\nYou (voice): {command_text}")
    reply = get_reply(command_text, memory)
    wrapped_reply = textwrap.fill(reply, width=80)
    arlo_says(wrapped_reply)
    speak(reply)


def run_session():
    """Runs one full login -> chat session. Returns 'exit' or 'logout'."""
    login()
    update_message = updater.check_for_update()
    enable_screen_capture()

    stop_event = threading.Event()  # tells this session's background threads to stop when it ends

    memory = Memory()
    boot_summary = run_with_spinner(lambda: run_boot_check(memory), message="Starting A.R.L.O.")
    run_with_spinner(detect_and_save_thresholds, message="Checking hardware")
    run_with_spinner(ensure_lhm_running, message="Preparing system monitor")

    if config.TEST_MODE and security.can_see_debug():
        print(boot_summary)

    current_time = get_time()
    arlo_says(f"Hello Sir, it is currently {current_time}.")
    print_divider()

    if update_message:
        arlo_says(update_message)
        print_divider()

    now = datetime.now()
    missed_any = False
    for alarm in memory.alarms:
        if not alarm["fired"] and now >= alarm["time"]:
            alarm["fired"] = True
            missed_any = True
            arlo_says(f"While you were away, this alarm went off: {alarm['description']} (was set for {alarm['time'].strftime('%I:%M %p')})")
    if missed_any:
        memory.save_alarms()
        print_divider()

    alarm_thread = threading.Thread(target=check_alarms, args=(memory, stop_event), daemon=True)
    alarm_thread.start()

    if config.VOICE_ENABLED:
        listen_for_wake_word, speak, voice_error = _load_voice()
        if listen_for_wake_word is None:
            arlo_says(f"Voice is turned on, but it couldn't start: {voice_error}")
            print_divider()
        else:
            voice_thread = threading.Thread(
                target=listen_for_wake_word,
                args=(lambda text: handle_voice_command(text, memory, speak),),
                kwargs={"stop_event": stop_event},
                daemon=True,
            )
            voice_thread.start()

    while True:
        username_display = security.get_current_username()
        user_input = get_input(f"[{username_display}] ")
        print_divider()

        if user_input.strip() == "":
            confirm_exit = input("Are you sure you want to exit A.R.L.O.? (yes/no): ").strip().lower()
            if confirm_exit not in ("yes", "y", ""):
                continue
            stop_event.set()
            run_with_dots(lambda: update_long_term_memory(memory), message="Saving session")
            os.system("cls" if os.name == "nt" else "clear")
            return "exit"

        if user_input == "/logout":
            stop_event.set()
            run_with_dots(lambda: update_long_term_memory(memory), message="Saving session")
            os.system("cls" if os.name == "nt" else "clear")
            return "logout"

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
            print_divider()
            continue

        if user_input == "/help":
            arlo_says("Here are the commands I understand:")
            for cmd, desc in COMMANDS.items():
                print(f"  {cmd} -- {desc}")
            print_divider()
            continue

        if user_input == "/hub":
            show_hub(memory)
            continue

        if user_input == "/update":
            arlo_says("Installing update...")
            result = updater.apply_update()
            if result:
                arlo_says("Update installed. Please restart A.R.L.O., sir.")
            else:
                arlo_says("Unable to install the update, sir.")
            print_divider()
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
            print_divider()
            continue

        if user_input == "/setrole":
            target = input("Username to change: ").strip()
            new_role = input("New role (admin/tester/regular): ").strip().lower()
            admin_code = input("Admin code: ").strip()
            success, error = security.set_role(target, new_role, admin_code)
            if success:
                arlo_says(f"'{target}' is now set to '{new_role}', sir.")
            else:
                arlo_says(f"Unable to change role: {error}")
            print_divider()
            continue

        reply = get_reply(user_input, memory)
        wrapped_reply = textwrap.fill(reply, width=80)
        arlo_says(wrapped_reply)
        print_divider()


# -------------------------------------------------------------
# PROGRAM LOOP (allows logging out and back in without restarting)
# -------------------------------------------------------------

while True:
    action = run_session()
    if action == "exit":
        break