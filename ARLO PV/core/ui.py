# =============================================================
# UI.PY
# Terminal display helpers: the assistant's reply prefix, loading
# animations (spinner and dots), cursor visibility control, visual
# dividers, and the screen-capture mechanism /hub uses to restore
# the exact prior screen.
# =============================================================

import sys
import io
import itertools
import threading
import time as time_module
import config


class _TeeOutput:
    """Mirrors everything written to the terminal into an in-memory buffer,
    so the exact screen contents can be restored later (used by /hub)."""
    def __init__(self, real_stdout):
        self.real_stdout = real_stdout
        self.captured = io.StringIO()

    def write(self, text):
        self.real_stdout.write(text)
        self.captured.write(text)
        return len(text)

    def flush(self):
        self.real_stdout.flush()

    def __getattr__(self, name):
        # Anything not defined here (isatty, encoding, fileno, buffer...) comes from the real stdout
        return getattr(self.real_stdout, name)


def _hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def _show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


def enable_screen_capture():
    """Replaces sys.stdout with a tee that records everything printed from
    this point on. Call once, right after login succeeds."""
    if not isinstance(sys.stdout, _TeeOutput):
        sys.stdout = _TeeOutput(sys.stdout)


def arlo_says(text):
    print(f"[{config.WAKE_KEYWORD.upper()}] {text}")


def print_divider():
    print("~" * 60)


def run_with_spinner(func, message="Loading"):
    """Runs a function while showing a spinning animation, then clears it."""
    done = threading.Event()
    _hide_cursor()

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

    try:
        return func()
    finally:
        done.set()
        spinner_thread.join()
        _show_cursor()


def run_with_dots(func, message="Saving session"):
    """Runs a function while showing a cycling dots animation (. .. ... ), then clears it."""
    done = threading.Event()
    _hide_cursor()

    def animate():
        dot_patterns = [".", "..", "..."]
        for pattern in itertools.cycle(dot_patterns):
            if done.is_set():
                break
            sys.stdout.write(f"\r{message}{pattern}   ")
            sys.stdout.flush()
            time_module.sleep(0.5)
        sys.stdout.write("\r" + " " * (len(message) + 10) + "\r")
        sys.stdout.flush()

    dots_thread = threading.Thread(target=animate, daemon=True)
    dots_thread.start()

    try:
        return func()
    finally:
        done.set()
        dots_thread.join()
        _show_cursor()