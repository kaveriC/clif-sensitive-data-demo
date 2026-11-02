#!/usr/bin/env python3
"""PreToolUse hook (Bash): keep real data out of Claude's session.

Refuses a Bash command when it
  1. names a protected location: data/phi, config/real.json, or the data_directory
     listed in config/real.json (so Claude cannot run code on real data; you do that), or
  2. would print rows into the transcript: .head( .tail( .sample( .iloc[ to_string( parquet-tools pqrs.

This matches command text only. A script file that reads real data is not caught here,
which is why the deny rules, CLAUDE.md, and running real data yourself are separate layers.
Override rule 2 for demo/synthetic data only: export CLAUDE_ALLOW_ROW_DUMPS=1.
"""
import json, os, pathlib, re, sys

def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
        "permissionDecision": "deny", "permissionDecisionReason": reason}}))
    sys.exit(0)

try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)  # fail open on malformed input; deny rules still apply
if d.get("tool_name") != "Bash":
    sys.exit(0)
cmd = d.get("tool_input", {}).get("command", "")

root = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
protected = ["data/phi", "config/real.json"]
try:
    real = json.load(open(root / "config" / "real.json")).get("data_directory", "").rstrip("/")
    if real:
        protected.append(real)
    home = os.path.expanduser("~")
    if real.startswith(home + "/"):
        protected.append("~" + real[len(home):])  # Claude often writes ~ for the home folder
except Exception:
    pass
hit = next((p for p in protected if p and p.lower() in cmd.lower()), None)  # case-insensitive: macOS paths are
if hit:
    deny(f"Blocked: this command touches real data ({hit}). Claude builds and tests on data/demo; "
         "you run real data yourself in a separate terminal: python run_ase.py --config config/real.json")

if not os.environ.get("CLAUDE_ALLOW_ROW_DUMPS") and re.search(
        r"\.(head|tail|sample)\s*\(|\.iloc\s*\[|to_string\s*\(|\bparquet-tools\b|\bpqrs\b", cmd):
    deny("Blocked: this would print data rows into the transcript. Use .shape, .dtypes, .columns, "
         "counts, or aggregates. For demo/synthetic data only: export CLAUDE_ALLOW_ROW_DUMPS=1.")
