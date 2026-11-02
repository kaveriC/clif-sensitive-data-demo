#!/usr/bin/env python3
"""PreToolUse hook: keep real data out of Claude's session (hook B on the deck, slot 2: tool results).

Same contract as the clif-icu plugin's hooks/phi_guard.py
(https://github.com/Common-Longitudinal-ICU-data-Format/skills): registered on Read, Grep, Glob, Edit,
Write, NotebookEdit and Bash; exit 2 blocks and the reason on stderr is shown to Claude; path arguments
are resolved (symlinks, relative paths, ~, letter case) before comparison; site PHI folders are read from
$CLIF_PHI_PATHS_FILE, ./.clif-phi-paths and ~/.clif/phi-paths. On top of that this hook
  - always protects data/phi, config/real.json, output/logs and the data_directory in config/real.json;
  - blocks a Bash command that would print rows: .head( .tail( .sample( .iloc[ to_string( parquet-tools pqrs
    (demo or synthetic data only: export CLAUDE_ALLOW_ROW_DUMPS=1 to allow);
  - exempts an approved script: a line "<sha256>  <script>" in .claude/approved-scripts, written with
    `shasum -a 256 run_ase.py >> .claude/approved-scripts` after review, lets `uv run <script> --config <file>`
    name the real data, and only while the file still hashes the same. Edit the script and the exemption lapses;
  - fails closed: any error in this script exits 2, and settings.json adds "onFailure": "block".
Checks the call as written. A script that opens the real path is not caught here: deny rules, the sandbox,
and running real data yourself are the other layers.
"""
import hashlib, json, os, pathlib, re, sys

PATH_KEYS = ("file_path", "path", "notebook_path")
TEXT_KEYS = ("command", "pattern")

def block(reason):
    print(reason, file=sys.stderr)
    sys.exit(2)

def resolve(p):
    return os.path.realpath(os.path.expanduser(str(p)))

def is_under(target, root):
    t, r = resolve(target).casefold(), root.casefold()
    return t == r or t.startswith(r + os.sep)

try:
    e = json.load(sys.stdin)
    tool = e.get("tool_name", "")
    inp = e.get("tool_input") or {}
    root = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    cwd = e.get("cwd") or str(root)
    home = os.path.expanduser("~")

    protected = {n: resolve(root / n) for n in ("data/phi", "config/real.json", "output/logs")}  # raw -> resolved
    cfg = root / "config" / "real.json"
    if cfg.exists():
        d = (json.load(open(cfg)).get("data_directory") or "").rstrip("/")
        if d:
            protected[d] = resolve(root / d)
    for src in (os.environ.get("CLIF_PHI_PATHS_FILE"), root / ".clif-phi-paths", pathlib.Path(home) / ".clif" / "phi-paths"):
        if src and os.path.isfile(src):
            for line in open(src):
                line = line.strip()
                if line and not line.startswith("#"):
                    protected[line] = resolve(line)

    def spellings(raw, res):  # every way a command might write the location
        out = {raw, res}
        for p in (raw, res):
            if p.startswith(home + "/"):
                out.add("~" + p[len(home):])
        return {s.casefold() for s in out if s}

    hit = None
    for key in PATH_KEYS:
        v = inp.get(key)
        if isinstance(v, str) and v:
            target = v if os.path.isabs(os.path.expanduser(v)) else os.path.join(cwd, v)
            hit = next((raw for raw, res in protected.items() if is_under(target, res)), None)
            if hit:
                break
    if not hit:
        text = " ".join(str(inp.get(k, "")) for k in TEXT_KEYS).casefold()
        hit = next((raw for raw, res in protected.items() if any(s in text for s in spellings(raw, res))), None)

    def approved(cmd):
        listing = root / ".claude" / "approved-scripts"
        for line in listing.read_text().splitlines() if listing.exists() else []:
            parts = line.split()
            if len(parts) == 2:
                sha, script = parts
                p = root / script
                if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == sha and re.fullmatch(
                        rf"(uv run |python3? |\.venv/bin/python )?{re.escape(script)}( --config \S+)?", cmd.strip()):
                    return True
        return False

    if hit and not (tool == "Bash" and approved(inp.get("command", ""))):
        block(f"Blocked by .claude/hooks/no-row-dumps.py: this {tool} call names real data ({hit}). "
              "Claude builds and tests on data/demo; you run real data yourself in a separate terminal: "
              "uv run run_ase.py --config config/real.json")

    if tool == "Bash" and not os.environ.get("CLAUDE_ALLOW_ROW_DUMPS") and re.search(
            r"\.(head|tail|sample)\s*\(|\.iloc\s*\[|to_string\s*\(|\bparquet-tools\b|\bpqrs\b", str(inp.get("command", ""))):
        block("Blocked by .claude/hooks/no-row-dumps.py: this would print data rows into the transcript. "
              "Use .shape, .dtypes, .columns, counts, or aggregates. For demo/synthetic data only: "
              "export CLAUDE_ALLOW_ROW_DUMPS=1.")
except SystemExit:
    raise
except Exception as err:
    block(f"no-row-dumps hook failed ({err!r}); blocking to fail closed.")
sys.exit(0)
