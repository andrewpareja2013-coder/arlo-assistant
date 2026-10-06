# =============================================================
# REGISTRY.PY
# The plug-in system. Every tool file calls register() to add
# itself to the TOOLS dictionary. brain.py and boot.py read from
# this dictionary automatically.
# =============================================================

TOOLS = {}


def register(name, description, parameters, function,
             requires_confirmation=False, needs_memory=False, safe_to_test=False):
    """Adds a tool to the shared TOOLS dictionary."""
    TOOLS[name] = {
        "description": description,
        "parameters": parameters,
        "function": function,
        "requires_confirmation": requires_confirmation,
        "needs_memory": needs_memory,
        "safe_to_test": safe_to_test,
    }