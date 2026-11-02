# CLIF sensitive-data demo

A small project that shows the working principle: **code goes to the data; data never goes to the model.**

Claude builds and tests an analysis on open demo data it may read. The same code is
run on real data by the researcher, outside Claude. Only aggregates come back.

## What is in here

The repo is the guardrail kit plus a task.

| Path | Purpose |
|---|---|
| `CLAUDE.md` | The project rules Claude loads every turn. Context the model may follow, not enforcement. |
| `.claude/settings.json` | Deny rules on `data/phi` and on `output/logs` (clifpy's own logs may quote values after a real run), both hooks (fail closed), bypass-permissions mode off, auto memory off, 7-day retention. Put the deny rule for your real data path in `.claude/settings.local.json` (gitignored). |
| `.claude/hooks/no-pasted-rows.py` | UserPromptSubmit hook, for what you type. Drops a prompt that looks like pasted data rows (an id-column header plus three or more record-like lines) before it reaches the model. |
| `.claude/hooks/no-row-dumps.py` | PreToolUse hook, for what tools return. Same contract as the clif-icu plugin's `phi_guard.py`: registered on Read, Grep, Glob, Edit, Write and Bash, resolves paths (symlinks, relative paths, `~`, letter case), reads site PHI folders from `.clif-phi-paths` and `~/.clif/phi-paths`, exits 2 to block. Also protects `data/phi`, `config/real.json`, `output/logs` and the real `data_directory`, and blocks Bash commands that print rows (`.head(`, `.tail(`, `.sample(`, `.iloc[`, `to_string(`). Checks the call as written; an error in the hook also blocks. |
| `.claude/hooks/phi-scan.py` | PostToolUse hook, advisory, port of the plugin's `phi_scan.py`. Flags MRN-, SSN- and birth-date-shaped patterns in Read and Bash output and tells Claude to stop. It runs after the output is in the context, so it can warn but not prevent. |
| `.claude/skills/sensitive-data-check/` | `/sensitive-data-check`: PASS/FAIL table for the setup. Reads no data. |
| `config/demo.json`, `config/real.example.json` | Same pipeline, two data paths. Copy the example to `config/real.json` (gitignored) and set your real path. |
| `data/demo/` | CLIF-MIMIC demo (100 patients, open ODbL licence). Claude may read it. |
| `data/phi/` | Stand-in for real data. Empty on purpose; Read/Edit denied. |
| `pyproject.toml`, `uv.lock` | Pinned environment. `uv sync` recreates it. |
| `TASK.md` | The spec Claude builds from: CDC Adult Sepsis Event via `clifpy`, aggregates only, cells under 11 suppressed, CSV and PNG out, acceptance numbers for the demo data. |
| `run_ase.py` | Not in the kit, and gitignored on `main`. Claude writes it from `TASK.md`. A finished copy is on the `solution` branch: `git show solution:run_ase.py > run_ase.py`. |

## Try it

```
git clone https://github.com/kaveriC/clif-sensitive-data-demo.git
cd clif-sensitive-data-demo
uv sync
cp config/real.example.json config/real.json      # then set data_directory to your real data
```

Create `.claude/settings.local.json` with the deny rule for that path:

```json
{"permissions": {"deny": ["Read(//absolute/path/to/real/data/**)", "Edit(//absolute/path/to/real/data/**)"]}}
```

Open the folder in Claude Code, then:

1. `/sensitive-data-check` should pass every row.
2. Ask: *Read TASK.md and write run_ase.py. Test it on config/demo.json and show me the summary. Aggregates only.*
3. In your own terminal, not in Claude: `uv run run_ase.py --config config/real.json`.
4. Ask Claude to read `output/ase_summary_real.csv` and compare it with the demo run. Only counts cross the line.

## Data and licence

Code is MIT. `data/demo/` is the CLIF-formatted **MIMIC-IV Clinical Database Demo** (Johnson, A., Pollard, T., & Mark, R., v2.2, PhysioNet, 2023; https://physionet.org/content/mimic-iv-demo/2.2/), released under the Open Data Commons Open Database License v1.0 (ODbL). It contains no real identifiers and no data use agreement is required. Nothing from the full, credentialed MIMIC-IV or from any health system is in this repository.

## Same guard as the clif-icu plugin

The hooks follow the [clif-icu plugin's](https://github.com/Common-Longitudinal-ICU-data-Format/skills) `hooks/phi_guard.py` and `hooks/phi_scan.py`, and its [PHI-safe development reference](https://github.com/Common-Longitudinal-ICU-data-Format/skills/blob/main/skills/clif-icu/reference/phi-safe-development.md): the agent writes the code on non-PHI data, the human runs it on real data, only sanitized aggregates come back. If your site already lists real-data folders in `~/.clif/phi-paths`, this hook reads them too. Two things are stricter here: the hook fails closed, and it is active without any config.

To let Claude run one reviewed script on real data (only on a BAA-covered channel, see the reference's Phase B), approve it by hash: `shasum -a 256 run_ase.py >> .claude/approved-scripts`. The hook then allows `uv run run_ase.py --config config/real.json` and nothing else, and the exemption lapses the moment the file changes.

## What this does not stop

Layers, not a wall. The hooks check each prompt and tool call as written, so a script file Claude writes that opens the real path is not caught by them; the Read deny rule does not govern Bash at all. Strongest extra layer: turn on the sandbox with `"sandbox": {"enabled": true, "filesystem": {"denyRead": ["<real data path>"]}}` in `.claude/settings.local.json`, and keep running real data yourself.

## Use this for your own project

Copy `.claude/`, `CLAUDE.md` and `.gitignore` into your project, write your own `TASK.md` in the same shape (aggregates only, cells under 11 suppressed, acceptance numbers on open or synthetic data), point `config/real.json` at your data, add that path to `.claude/settings.local.json`, and run `/sensitive-data-check`.
