# =============================================================
# TERMINAL_TOOL.PY
# Runs terminal/command-line commands. Safe read-only commands
# execute immediately; anything that modifies or deletes something
# requires explicit user confirmation first.
# =============================================================

import subprocess
from tools.registry import register


def run_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15
        )
        output = result.stdout.strip()
        error = result.stderr.strip()

        if error and not output:
            return f"Command produced an error: {error}"
        return output if output else "Command ran successfully with no output."
    except subprocess.TimeoutExpired:
        return "Command timed out after 15 seconds."
    except Exception as e:
        return f"Failed to run command: {e}"


register(
    name="run_terminal_command",
    description=(
        "Run a terminal/command-line command and return its output. For disk space specifically, use: "
        "'powershell \"Get-PSDrive C | Select-Object Name, @{Name=\\'Used(GB)\\';Expression={[math]::Round(($_.Used/1GB),2)}}, "
        "@{Name=\\'Free(GB)\\';Expression={[math]::Round(($_.Free/1GB),2)}}\"'. For IP address, use 'ipconfig'. "
        "Avoid 'wmic' -- it's deprecated and unavailable on many modern Windows systems."
    ),
    parameters={
        "type": "object",
        "properties": {"command": {"type": "string", "description": "The exact command to run."}},
        "required": ["command"],
    },
    function=run_command,
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