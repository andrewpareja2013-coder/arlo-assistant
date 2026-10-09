# =============================================================
# FILE_READER_TOOL.PY
# Reads the contents of a text file so the AI can summarize or
# discuss it. Truncates long files to keep responses manageable.
# =============================================================

from tools.registry import register


def read_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if len(content) > 3000:
            content = content[:3000] + "\n\n[Content truncated -- file is longer than shown]"
        return content
    except FileNotFoundError:
        return "I couldn't find a file at that location, sir."
    except Exception as e:
        return f"I was unable to read that file: {e}"


register(
    name="read_file",
    description=(
        "Read the contents of a text file so you can summarize or discuss it. "
        "Use this whenever the user asks you to read, open, view, or summarize a specific file's contents. "
        "NEVER use run_terminal_command to read a file -- always use this dedicated tool instead. "
        "Use search_files first if you only have a filename, not the full path."
    ),
    parameters={
        "type": "object",
        "properties": {"filepath": {"type": "string", "description": "The full file path to read."}},
        "required": ["filepath"],
    },
    function=read_file,
    requires_confirmation=False,
)