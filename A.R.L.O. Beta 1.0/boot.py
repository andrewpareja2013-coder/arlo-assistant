# =============================================================
# BOOT.PY
# Background Operations & Optimization Test.
# Runs at startup: verifies every registered tool is structurally
# valid, and functionally tests any tool marked safe_to_test.
# =============================================================

from tools.registry import TOOLS
from error_codes import report_error


def run_boot_check(memory):
    """Runs all BOOT checks and returns a summary string (only meaningful in Test Mode)."""
    passed = 0
    failed = 0
    failures = []

    for name, info in TOOLS.items():
        if not info.get("description") or not info.get("parameters") or not info.get("function"):
            report_error("E003", name)
            failed += 1
            failures.append(f"{name}: missing required registration fields")
            continue

        if info.get("safe_to_test"):
            try:
                if info["needs_memory"]:
                    info["function"](memory)
                else:
                    info["function"]()
            except Exception as e:
                failed += 1
                failures.append(f"{name}: {e}")
                continue

        passed += 1

    summary_lines = [f"[BOOT] {passed} tools passed, {failed} tools failed."]
    for f in failures:
        summary_lines.append(f"[BOOT] FAILED -- {f}")
    return "\n".join(summary_lines)