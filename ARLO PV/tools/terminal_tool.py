# =============================================================
# TERMINAL_TOOL.PY
# Runs terminal/command-line commands. Safe read-only commands
# execute immediately; anything that modifies or deletes something
# requires explicit user confirmation first.
# =============================================================

import re
import subprocess
from tools.registry import register

MAX_CHARS = 3000

# Words that mean a command changes something. The safe tool refuses these
# and sends the AI to run_risky_command, which asks the user first.
RISKY_PATTERN = re.compile(
    r"(?<![\w-])("
    r"del|erase|rm|rmdir|rd|remove-item|move|mv|ren|rename|format|diskpart|"
    r"taskkill|kill|pkill|stop-process|shutdown|restart-computer|stop-computer|"
    r"reg\s+(add|delete)|sc\s+(stop|delete)|net\s+user|chmod|chown|sudo|set-executionpolicy"
    r")(?![\w-])",
    re.IGNORECASE,
)


def run_command(command):
    if not command or not str(command).strip():
        return "I need a command to run, sir."

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=15
        )
        output = (result.stdout or "").strip()
        error = (result.stderr or "").strip()

        if error and not output:
            return f"Command produced an error: {error[:MAX_CHARS]}"
        if not output:
            return "Command ran successfully with no output."
        if len(output) > MAX_CHARS:
            output = output[:MAX_CHARS] + "\n\n[Output truncated -- it was longer than shown]"
        return output
    except subprocess.TimeoutExpired:
        return "Command timed out after 15 seconds."
    except Exception as e:
        return f"Failed to run command: {e}"


def run_safe_command(command):
    if command and RISKY_PATTERN.search(str(command)):
        return (
            "That command changes or removes something, so it can't run here. "
            "Use run_risky_command instead, which asks the user to confirm first."
        )
    return run_command(command)


register(
    name="run_terminal_command",
    description=(
        "Run a terminal/command-line command and return its output. For disk space specifically, use: "
        "'powershell \"Get-PSDrive C | Select-Object Name, @{Name=\\'Used(GB)\\';Expression={[math]::Round(($_.Used/1GB),2)}}, "
        "@{Name=\\'Free(GB)\\';Expression={[math]::Round(($_.Free/1GB),2)}}\"'. For IP address, use 'ipconfig'. "
        "Avoid 'wmic' -- it's deprecated and unavailable on many modern Windows systems. "
        "Read-only commands only: anything that deletes, moves, or kills must use run_risky_command."
    ),
    parameters={
        "type": "object",
        "properties": {"command": {"type": "string", "description": "The exact command to run."}},
        "required": ["command"],
    },
    function=run_safe_command,
)

register(
    name="run_risky_command",
    description="Run a command that modifies, deletes, or moves files, or stops/kills processes.",
    parameters={
        "type": "object",
        "properties": {"command": {"type": "string", "description": "The exact command to run."}},
        "required": ["command"],
    },
    function=run_command,
    requires_confirmation=True,
)