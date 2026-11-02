---
name: sensitive-data-check
description: Run before any work near patient data in this project. Checks that the project is set up so Claude never sees real rows - deny rules on data folders, the row-dump hook, retention, auto memory off, gitignore, no data files tracked - and reports PASS/FAIL per item. Use when the user says "check the setup", "is this project safe", "sensitive data check", or at the start of a session.
---

# Sensitive-data check

Run the checker and paste its complete table, unchanged, in a code block before any commentary:

```bash
python3 .claude/skills/sensitive-data-check/check.py
```

Then:

1. For every FAIL, say in one sentence what the risk is and offer the exact fix the table printed. Anything site-specific (the real data path's deny rule, the sandbox block with its `denyRead` and `allowWrite` paths) belongs in `.claude/settings.local.json`, which is gitignored, never in `.claude/settings.json`. Make the change only when the user says yes.
2. Remind the user of the two rules this project runs on: develop on `data/demo`, run real data yourself with `uv run run_ase.py --config config/real.json`, and only aggregates (`output/*_summary.csv` and `.png`) come back into the conversation.
3. Do not read anything under `data/phi`, `output/logs` or the real data path to "verify" the check. The deny rules will refuse it; that refusal is correct behaviour.
