# =============================================================
# AUTO_REGISTER.PY
# Automatically discovers and imports every tool file inside the
# tools/ folder, so each one registers itself without needing a
# manual "import tools.x" line in main.py or brain.py.
# =============================================================

import pkgutil
import importlib
import tools


def load_all_tools():
    """
    Scans the tools/ package for every module and imports it.
    Importing a tool file automatically runs its register() calls
    at the bottom of the file, adding it to the shared TOOLS registry.
    """
    for _, module_name, _ in pkgutil.iter_modules(tools.__path__):
        if module_name == "registry":
            continue
        importlib.import_module(f"tools.{module_name}")