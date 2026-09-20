# =============================================================
# ERROR_CODES.PY
# A central registry of standardized error codes. Every kind of
# failure in A.R.L.O. gets a unique code and description, so users
# have something concrete to report or look up when something breaks.
# =============================================================

ERROR_CODES = {
    "E001": "Failed to reach the AI model (Ollama connection issue).",
    "E002": "A tool failed to execute correctly.",
    "E003": "A tool is missing required registration fields.",
    "E004": "Failed to load or save encrypted data.",
    "E005": "Login or account operation failed.",
}


def report_error(code, detail=""):
    """
    Prints a standardized error message to the user, and returns
    the same message so it can also be spoken/displayed as A.R.L.O.'s
    reply if relevant. Future: this also sends the error to HUB.
    """
    description = ERROR_CODES.get(code, "Unknown error.")
    message = f"[ARLO-{code}] {description}"
    if detail:
        message += f" ({detail})"
    print(message)
    return message