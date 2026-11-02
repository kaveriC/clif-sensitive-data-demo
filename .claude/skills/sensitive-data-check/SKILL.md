---
name: sensitive-data-check
description: Run before any work near patient data in this project. Checks that the project is set up so Claude never sees real rows - deny rules on data folders, the row-dump hook, retention, auto memory off, gitignore, no data files tracked - and reports PASS/FAIL per item. Use when the user says "check the setup", "is this project safe", "sensitive data check", or at the start of a session.
---

# Sensitive-data check

Run the checker and show its table to the user verbatim:

```bash
python3 .claude/skills/sensitive-data-check/check.py
```

Then:

1. For every FAIL, say in one sentence what the risk is and offer the exact fix (a line in `.claude/settings.json`, a `.gitignore` entry, a `git rm --cached`). Make the change only when the user says yes.
2. Remind the user of the two rules this project runs on: develop on `data/demo`, run real data yourself with `python run_ase.py --config config/real.json`, and only aggregates come back into the conversation.
3. Do not read anything under `data/phi` or the real data path to "verify" the check. The deny rules will refuse it; that refusal is correct behaviour.
