# =============================================================
# REGISTRY.PY
# The plug-in system. Every tool file calls register() to add
# itself to the TOOLS dictionary. brain.py and boot.py read from
# this dictionary automatically.
# =============================================================

TOOLS = {}


def register(name, description, parameters, function,
             requires_confirmation=False, needs_memory=False, safe_to_test=False):
    """
    Adds a tool to the shared TOOLS dictionary.

    name                  - the tool's identifier, used by the AI to call it
    description           - tells the AI what this tool does and when to use it
    parameters            - the expected input shape, in Ollama's tool-schema format
    function              - the actual Python function that runs when called
    requires_confirmation - if True, this tool pauses and asks the user before running
    needs_memory          - if True, the Memory object gets passed in as an argument
    safe_to_test          - if True, BOOT is allowed to actually call this function
                             during startup testing (no side effects)
    """
    TOOLS[name] = {
        "description": description,
        "parameters": parameters,
        "function": function,
        "requires_confirmation": requires_confirmation,
        "needs_memory": needs_memory,
        "safe_to_test": safe_to_test,
    }