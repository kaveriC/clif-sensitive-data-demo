#!/usr/bin/env python3
"""Checklist for a project that handles sensitive data with Claude Code. Prints PASS/FAIL only; reads no data."""
import json, os, pathlib, subprocess, sys

root = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
results = []

def check(name, ok, fix):
    results.append((name, bool(ok), fix))

def load(p):
    try:
        return json.load(open(p))
    except Exception:
        return {}

proj = load(root / ".claude" / "settings.json")
local = load(root / ".claude" / "settings.local.json")
user = load(pathlib.Path.home() / ".claude" / "settings.json")
deny = sum((s.get("permissions", {}).get("deny", []) for s in (proj, local, user)), [])
hooks = json.dumps(proj.get("hooks", {})) + json.dumps(user.get("hooks", {}))

check("Read deny rule covers a data folder", any(r.startswith("Read(") for r in deny),
      'add "Read(./data/phi/**)" and the real data path to permissions.deny')
check("Edit deny rule covers a data folder", any(r.startswith("Edit(") for r in deny),
      'add "Edit(./data/phi/**)" to permissions.deny')
check("Row-dump hook registered (PreToolUse on Bash)", "no-row-dumps" in hooks,
      "register .claude/hooks/no-row-dumps.py under hooks.PreToolUse with matcher Bash")
check('Hook fails closed ("onFailure": "block")', '"onFailure": "block"' in hooks,
      'add "onFailure": "block" to the hook entry (Claude Code 2.1.295+); otherwise a crashed hook lets the command run')
check("Auto memory off for this project", proj.get("autoMemoryEnabled") is False or user.get("autoMemoryEnabled") is False,
      'set "autoMemoryEnabled": false')
cp = proj.get("cleanupPeriodDays", user.get("cleanupPeriodDays", 30))
check(f"Transcript retention set ({cp} days)", cp <= 14, 'set "cleanupPeriodDays": 7')
sandbox_on = any(isinstance(s.get("sandbox"), dict) and s["sandbox"].get("enabled") is True for s in (proj, local, user))
results.append(("Sandbox enabled (strongest layer; optional here)", sandbox_on if sandbox_on else None,
                '"sandbox": {"enabled": true, "filesystem": {"denyRead": ["<real data path>"]}}'))

gi = (root / ".gitignore").read_text() if (root / ".gitignore").exists() else ""
check(".gitignore excludes output/ and data/phi/", "output/" in gi and "data/phi" in gi,
      "add output/ and data/phi/* to .gitignore")
tracked = ""
if (root / ".git").exists():
    tracked = subprocess.run(["git", "-C", str(root), "ls-files"], capture_output=True, text=True).stdout
    bad = [f for f in tracked.split("\n") if f.endswith((".parquet", ".csv")) and not f.startswith("data/demo/")]
    check("No data files tracked in git outside data/demo", not bad, "git rm --cached <file>; add to .gitignore")
    leaked = subprocess.run(["git", "-C", str(root), "ls-files", "-ci", "--exclude-standard"], capture_output=True, text=True).stdout.split()
    check("No gitignored file is still tracked", not leaked, "git rm --cached " + " ".join(leaked) + "; then commit")
else:
    check("Project is a git repo (so tracked files can be audited)", False, "git init")
real_dir = load(root / "config" / "real.json").get("data_directory", "")
if real_dir:
    check("Real data path from config/real.json is Read-denied",
          any(r.startswith("Read(") and real_dir.rstrip("/").lstrip("/") in r for r in deny),
          f'add "Read(/{real_dir.rstrip("/")}/**)" to .claude/settings.local.json permissions.deny')
check("Real data lives outside the project folder",
      not any(p.suffix == ".parquet" for p in (root / "data" / "phi").glob("*")) if (root / "data" / "phi").exists() else True,
      "move real data out of the project; point config/real.json at it")
check("CLAUDE.md states the no-rows rule", (root / "CLAUDE.md").exists() and "Never print rows" in (root / "CLAUDE.md").read_text(),
      "add the no-rows rule to CLAUDE.md")

width = max(len(n) for n, _, _ in results) + 2
print(f"{'check':{width}} result")
print("-" * (width + 8))
fails = 0
for n, ok, fix in results:
    status = "PASS" if ok else ("OPTIONAL" if ok is None else "FAIL")
    print(f"{n:{width}} {status}")
    if ok is False:
        fails += 1
        print(f"{'':{width}}   fix: {fix}")
    elif ok is None:
        print(f"{'':{width}}   to enable: {fix}")
print("-" * (width + 8))
print(f"{sum(1 for _, ok, _ in results if ok)} passed, {fails} failed. Nothing under data/ was read.")
sys.exit(0)
