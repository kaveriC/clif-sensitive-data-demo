#!/usr/bin/env python3
"""PreToolUse hook: keep real data out of Claude's session (slot 2 on the deck: tool results).

Registered for Read, Grep, Glob, Edit, Write, NotebookEdit and Bash. Blocks the call (exit 2;
the reason on stderr is shown to Claude) when
  1. the call names a protected location: data/phi, config/real.json, or the data_directory in
     config/real.json, checked case-insensitively and with ~ for the home folder; or
  2. it is a Bash command that would print rows: .head( .tail( .sample( .iloc[ to_string( parquet-tools pqrs.

Only exit 2 blocks, so any error inside this script also exits 2 (fail closed). settings.json adds
"onFailure": "block" for the case where python3 itself cannot start.
Checks the call as written (command and path fields). A script that opens the real path is not
caught here: deny rules, the sandbox, and running real data yourself are the other layers.
Override rule 2 for demo/synthetic data only: export CLAUDE_ALLOW_ROW_DUMPS=1.
"""
import json, os, pathlib, re, sys

def block(reason):
    print(reason, file=sys.stderr)
    sys.exit(2)

try:
    e = json.load(sys.stdin)
    tool = e.get("tool_name", "")
    inp = e.get("tool_input") or {}
    call = " ".join(str(inp.get(k, "")) for k in ("command", "file_path", "path", "pattern", "notebook_path"))

    root = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    protected = ["data/phi", "config/real.json"]
    cfg = root / "config" / "real.json"
    real = (json.load(open(cfg)).get("data_directory") or "").rstrip("/") if cfg.exists() else ""
    home = os.path.expanduser("~")
    if real:
        protected.append(real)
        if real.startswith(home + "/"):
            protected.append("~" + real[len(home):])  # Claude often writes ~ for the home folder

    hit = next((p for p in protected if p.lower() in call.lower()), None)  # case-insensitive: macOS paths are
    if hit:
        block(f"Blocked by .claude/hooks/no-row-dumps.py: this {tool} call names real data ({hit}). "
              "Claude builds and tests on data/demo; you run real data yourself in a separate terminal: "
              "uv run run_ase.py --config config/real.json")

    if tool == "Bash" and not os.environ.get("CLAUDE_ALLOW_ROW_DUMPS") and re.search(
            r"\.(head|tail|sample)\s*\(|\.iloc\s*\[|to_string\s*\(|\bparquet-tools\b|\bpqrs\b", call):
        block("Blocked by .claude/hooks/no-row-dumps.py: this would print data rows into the transcript. "
              "Use .shape, .dtypes, .columns, counts, or aggregates. For demo/synthetic data only: "
              "export CLAUDE_ALLOW_ROW_DUMPS=1.")
except SystemExit:
    raise
except Exception as err:
    block(f"no-row-dumps hook failed ({err!r}); blocking to fail closed.")
sys.exit(0)
