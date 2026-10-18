# =============================================================
# CUSTOM_INPUT.PY
# A replacement for input() that supports safely interrupting
# mid-typing (e.g. for alarm alerts) without losing what the
# user has typed so far. Works on Windows, Linux, and Mac.
# Also provides masked_input() for passwords: shows * for each
# character and accepts pasted text.
# =============================================================

import os

current_buffer = ""
current_prompt = ""

if os.name == "nt":
    import msvcrt

    def _get_char():
        return msvcrt.getch()

else:
    import sys
    import tty
    import termios

    def _get_char():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            char = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return char.encode("utf-8")


def get_input(prompt="You: "):
    """Reads input character-by-character, tracking a global buffer
    so alert_interrupt() can safely redraw it if something needs to print."""
    global current_buffer, current_prompt
    current_buffer = ""
    current_prompt = prompt
    print(prompt, end="", flush=True)

    while True:
        char = _get_char()

        if char in (b"\r", b"\n"):
            print()
            result = current_buffer
            current_buffer = ""
            return result

        elif char == b"\x08" or char == b"\x7f":
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


def masked_input(prompt="Password: "):
    """Like get_input(), but shows * instead of the real characters.
    Pasting works because pasted text arrives as normal key presses.
    The real text is kept in a local variable, and the shared buffer only
    ever holds stars, so an alarm alert redraw can't reveal the password."""
    global current_buffer, current_prompt
    secret = ""
    current_buffer = ""
    current_prompt = prompt
    print(prompt, end="", flush=True)

    try:
        while True:
            char = _get_char()

            if char in (b"\r", b"\n"):
                print()
                return secret

            elif char == b"\x03":  # Ctrl+C
                print()
                raise KeyboardInterrupt

            elif char in (b"\x08", b"\x7f"):
                if secret:
                    secret = secret[:-1]
                    current_buffer = current_buffer[:-1]
                    print("\b \b", end="", flush=True)

            elif os.name == "nt" and char in (b"\x00", b"\xe0"):
                _get_char()  # arrow/function keys send two bytes; skip the second
                continue

            else:
                try:
                    decoded = char.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                if not decoded.isprintable():
                    continue
                secret += decoded
                current_buffer += "*"
                print("*", end="", flush=True)
    finally:
        current_buffer = ""


def alert_interrupt(message):
    """Safely prints an alert mid-typing, then redraws the current input line."""
    global current_buffer, current_prompt
    print(f"\n{message}")
    print(current_prompt + current_buffer, end="", flush=True)