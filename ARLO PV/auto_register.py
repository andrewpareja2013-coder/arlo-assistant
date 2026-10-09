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
    """Scans the tools/ package and imports every module, which
    triggers each file's register() calls at import time."""
    for _, module_name, _ in pkgutil.iter_modules(tools.__path__):
        if module_name == "registry":
            continue
        importlib.import_module(f"tools.{module_name}")