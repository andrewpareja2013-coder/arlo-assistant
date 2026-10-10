# =============================================================
# FILE_SEARCH_TOOL.PY
# Searches the user's PC for files or folders by name, matching
# any/all words in the search term regardless of order.
# Searches the current user's home folder.
# =============================================================

import os
import time
from tools.registry import register

MAX_RESULTS = 10
MAX_SECONDS = 20
SKIP_FOLDERS = {"appdata", "node_modules", "__pycache__", "site-packages", "$recycle.bin"}


def search_files(filename):
    search_words = str(filename).lower().split()
    if not search_words:
        return "What should I search for, sir?"

    search_path = os.path.expanduser("~")
    matches = []
    started = time.time()
    timed_out = False

    for root, dirs, files in os.walk(search_path):
        dirs[:] = [d for d in dirs if d.lower() not in SKIP_FOLDERS and not d.startswith(".")]

        for name in dirs + files:
            name_lower = name.lower()
            if all(word in name_lower for word in search_words):
                matches.append(os.path.join(root, name))

        if len(matches) >= MAX_RESULTS:
            break
        if time.time() - started > MAX_SECONDS:
            timed_out = True
            break

    if matches:
        result = "\n".join(matches[:MAX_RESULTS])
        if timed_out:
            result += "\n\n(Search stopped early after 20 seconds, so there may be more.)"
        return result

    if timed_out:
        return f"I searched for 20 seconds and found nothing matching '{filename}', sir. The search didn't cover everything."
    return f"No files or folders found matching '{filename}', sir."


register(
    name="search_files",
    description=(
        "Search for a file or folder by name or partial name on the user's PC. "
        "Use this whenever the user says 'find', 'locate', or 'search for' a file or folder. "
        "This is NOT the same as a terminal 'find' command -- always use this dedicated tool "
        "for file searches, never run_terminal_command. Report ONLY the file paths returned -- "
        "do not speculate, analyze, or add commentary about what the files might be for."
    ),
    parameters={
        "type": "object",
        "properties": {"filename": {"type": "string", "description": "The file or folder name to search for."}},
        "required": ["filename"],
    },
    function=search_files,
)