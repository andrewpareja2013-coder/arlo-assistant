# =============================================================
# FILE_SEARCH_TOOL.PY
# Searches the user's PC for files or folders by name, matching
# any/all words in the search term regardless of order.
# =============================================================

import os
from tools.registry import register


def search_files(filename):
    search_path = "C:\\Users\\apareja"
    search_words = filename.lower().split()
    matches = []

    for root, dirs, files in os.walk(search_path):
        dirs[:] = [d for d in dirs if d.lower() != "appdata"]

        for name in dirs + files:
            name_lower = name.lower()
            if all(word in name_lower for word in search_words):
                matches.append(os.path.join(root, name))
        if len(matches) >= 10:
            break

    if matches:
        return "\n".join(matches[:10])
    else:
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