# =============================================================
# PRIVACY_FILTER.PY
# Scans text for patterns resembling sensitive personal info (SSNs,
# phone numbers, credit card numbers, etc.) and strips them out.
# This is a hard, code-enforced safeguard -- it runs regardless of
# whether the AI followed instructions to avoid including such info.
# =============================================================

import re

PATTERNS = {
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "PHONE": re.compile(r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "CREDIT_CARD": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
}


def filter_sensitive_info(text):
    """
    Replaces anything matching a known sensitive-info pattern with
    [REDACTED], regardless of context. Returns the cleaned text.
    """
    cleaned = text
    for label, pattern in PATTERNS.items():
        cleaned = pattern.sub("[REDACTED]", cleaned)
    return cleaned