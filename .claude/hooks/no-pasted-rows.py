#!/usr/bin/env python3
"""UserPromptSubmit hook: refuse a prompt that looks like pasted data rows (slot 1 on the deck: user messages).

Blocks the prompt (exit 2; Claude Code drops it and shows this reason to you, not to the model) when the
text has a header line naming a CLIF key column (patient_id, hospitalization_id, mrn) and at least three
lines that look like records: three or more delimited fields, at least two of them numbers or dates.
Mentions of paths or filenames pass; those are checked at tool time by no-row-dumps.py.
Only exit 2 blocks, so any error inside this script also exits 2 (fail closed).
"""
import json, re, sys

KEY = re.compile(r"\b(patient_id|hospitalization_id|mrn)\b", re.I)
VALUE = re.compile(r"-?\d+(\.\d+)?|\d{4}-\d{2}-\d{2}(\s\d{2}:\d{2}(:\d{2})?)?")

def is_record(line):
    fields = [f.strip() for f in re.split(r"[,\t|]|\s{2,}", line.strip()) if f.strip()]
    return len(fields) >= 3 and sum(bool(VALUE.fullmatch(f)) for f in fields) >= 2

try:
    lines = (json.load(sys.stdin).get("prompt") or "").splitlines()
    if any(KEY.search(l) for l in lines) and sum(map(is_record, lines)) >= 3:
        print("Blocked by .claude/hooks/no-pasted-rows.py: this prompt looks like pasted data rows. "
              "Describe the data instead: columns, dtypes, counts, aggregates (cells under 11 suppressed).",
              file=sys.stderr)
        sys.exit(2)
except SystemExit:
    raise
except Exception as err:
    print(f"no-pasted-rows hook failed ({err!r}); blocking to fail closed.", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
