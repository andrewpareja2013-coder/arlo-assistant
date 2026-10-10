# =============================================================
# AUTO_REGISTER.PY
# Automatically discovers and imports every tool file inside the
# tools/ folder, so each one registers itself without needing a
# manual "import tools.x" line in main.py or brain.py.
# A tool file that fails to import is skipped, so one broken tool
# can't stop A.R.L.O. from starting.
# =============================================================

import pkgutil
import importlib
import tools

FAILED_TOOLS = []  # (module_name, error_text) for any tool file that couldn't be loaded


def load_all_tools():
    """Scans the tools/ package and imports every module, which
    triggers each file's register() calls at import time."""
    FAILED_TOOLS.clear()
    for _, module_name, _ in pkgutil.iter_modules(tools.__path__):
        if module_name == "registry":
            continue
        try:
            importlib.import_module(f"tools.{module_name}")
        except Exception as e:
            FAILED_TOOLS.append((module_name, str(e)))
            try:
                import security
                if security.can_see_debug():
                    print(f"[TOOLS] Skipped '{module_name}': {e}")
            except Exception:
                pass