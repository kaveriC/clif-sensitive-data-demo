# CLIF sensitive-data demo

A small project that shows the working principle: **code goes to the data; data never goes to the model.**

Claude builds and tests an analysis on open demo data it may read. The same code is
run on real data by the researcher, outside Claude. Only aggregates come back.

## What is in here

| Path | Purpose |
|---|---|
| `data/demo/` | CLIF-MIMIC demo (100 patients, open ODbL licence). Claude may read it. |
| `data/phi/` | Stand-in for real data. Empty on purpose; Read/Edit denied. |
| `config/demo.json`, `config/real.example.json` | Same pipeline, two data paths. Copy the example to `config/real.json` (gitignored) and set your real path. |
| `pyproject.toml`, `uv.lock` | Pinned environment. `uv sync` recreates it; `uv run run_ase.py ...` uses it. |
| `run_ase.py` | CDC Adult Sepsis Event via `clifpy.utils.ase.compute_ase`; prints aggregates only, cells under 11 suppressed; writes `output/ase_summary_<label>.csv` and a bar-chart `.png` of the same table. |
| `.claude/settings.json` | Deny rules on `data/phi`, the hook, auto memory off, 7-day retention. Put the deny rule for your real data path in `.claude/settings.local.json` (gitignored). |
| `.claude/hooks/no-row-dumps.py` | PreToolUse hook: refuses Bash commands that name the real data (`data/phi`, `config/real.json`, or its path) or print rows (`.head(`, `.tail(`, `.sample(`, `.iloc[`, `to_string(`). Matches command text only. |
| `.claude/skills/sensitive-data-check/` | `/sensitive-data-check`: PASS/FAIL table for the setup. Reads no data. |
| `CLAUDE.md` | The project rules Claude loads every turn. |

Setup once:

```
uv sync                                            # creates .venv from pyproject.toml / uv.lock
cp config/real.example.json config/real.json      # then set data_directory to your real data
```

and create `.claude/settings.local.json`:

```json
{"permissions": {"deny": ["Read(//absolute/path/to/real/data/**)", "Edit(//absolute/path/to/real/data/**)"]}}
```

## Data and licence

Code is MIT. `data/demo/` is the CLIF-formatted **MIMIC-IV Clinical Database Demo** (Johnson, A., Pollard, T., & Mark, R., v2.2, PhysioNet, 2023; https://physionet.org/content/mimic-iv-demo/2.2/), released under the Open Data Commons Open Database License v1.0 (ODbL). It contains no real identifiers and no data use agreement is required. Nothing from the full, credentialed MIMIC-IV or from any health system is in this repository.

## What this does not stop

Layers, not a wall. The hook reads command text, so a script file Claude writes that opens the real path is not caught by it; the Read deny rule does not govern Bash at all. Strongest extra layer: turn on the sandbox with `"sandbox": {"enabled": true, "filesystem": {"denyRead": ["<real data path>"]}}` in `.claude/settings.local.json`, and keep running real data yourself.

## Use this for your own project

Copy `.claude/`, `CLAUDE.md`, `.gitignore`, and `run_ase.py`'s pattern (aggregates only, cells under 11 suppressed) into your project, point `config/real.json` at your data, and run `/sensitive-data-check`. The deny rules in `.claude/settings.json` need your real data path added.
