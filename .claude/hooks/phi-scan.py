#!/usr/bin/env python3
"""PostToolUse hook, advisory (hook C on the deck): flags PHI-shaped patterns in Read and Bash output.

Port of the clif-icu plugin's hooks/phi_scan.py (https://github.com/Common-Longitudinal-ICU-data-Format/skills).
By the time this runs the output is already in the context, so it cannot block; it tells Claude to stop
and sanitize. Synthetic data trips it by design. Exit 0 always. CLIF_PHI_SCAN=off disables.
"""
import json, os, re, sys

PATTERNS = [
    ("MRN-like identifier", re.compile(r"\bMRN\W{0,3}\d{5,}", re.I)),
    ("SSN-like number", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("DOB-like field", re.compile(r"\bDOB\W{0,3}(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})", re.I)),
    ("birth-date-like value", re.compile(
        r"(?:birth\w*|\bdob\b).{0,24}\b(?:19[0-9]{2}|20[0-4][0-9])-\d{2}-\d{2}\b"
        r"|\b(?:19[0-9]{2}|20[0-4][0-9])-\d{2}-\d{2}\b.{0,24}(?:birth\w*|\bdob\b)", re.I)),
]

def text_of(x, depth=0):
    if depth > 8:
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, (int, float)):
        return str(x)
    if isinstance(x, dict):
        return " ".join(text_of(v, depth + 1) for v in x.values())
    if isinstance(x, list):
        return " ".join(text_of(v, depth + 1) for v in x)
    return ""

try:
    if os.environ.get("CLIF_PHI_SCAN", "").lower() != "off":
        text = text_of(json.load(sys.stdin).get("tool_response"))[:200_000]
        hits = sorted({label for label, rx in PATTERNS if rx.search(text)})
        if hits:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext":
                "PHI scan: tool output contains PHI-shaped patterns (" + ", ".join(hits) + "). STOP: do not "
                "repeat, summarize or reason over these values. If this is real data the workflow was violated; "
                "tell the user to open a new session on data/demo. If it is demo or synthetic data, say so and "
                "continue."}}))
except Exception:
    pass  # advisory: never break the session
sys.exit(0)
