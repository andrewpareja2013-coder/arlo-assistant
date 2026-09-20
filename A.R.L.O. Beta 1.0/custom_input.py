# =============================================================
# CUSTOM_INPUT.PY
# A replacement for input() that supports safely interrupting
# mid-typing (e.g. for alarm alerts) without losing what the
# user has typed so far.
# =============================================================

import msvcrt

current_buffer = ""


def get_input(prompt="You: "):
    """Reads input character-by-character, tracking a global buffer
    so alert_interrupt() can safely redraw it if something needs to print."""
    global current_buffer
    current_buffer = ""
    print(prompt, end="", flush=True)

    while True:
        char = msvcrt.getch()

        if char in (b"\r", b"\n"):
            print()
            result = current_buffer
            current_buffer = ""
            return result

        elif char == b"\x08":
            if current_buffer:
                current_buffer = current_buffer[:-1]
                print("\b \b", end="", flush=True)

        else:
            try:
                decoded = char.decode("utf-8")
                current_buffer += decoded
                print(decoded, end="", flush=True)
            except UnicodeDecodeError:
                continue


def alert_interrupt(message):
    """Safely prints an alert mid-typing, then redraws the current input line."""
    global current_buffer
    print(f"\n{message}")
    print("You: " + current_buffer, end="", flush=True)