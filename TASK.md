# Task: write `run_ase.py`

Build `run_ase.py`, a command-line script that computes CDC Adult Sepsis Events (ASE) on a CLIF
dataset and reports aggregates only. Develop and test it on the demo data. The researcher runs the
same script on real data in their own terminal; Claude never does.

## Interface

- `uv run run_ase.py --config config/demo.json`
- The config holds `data_directory`, `filetype`, `timezone`, `output_directory`, `label`.
- The researcher's command is identical with `config/real.json`. Do not open that file or its data path.

## Compute

- `from clifpy.utils.ase import compute_ase`
- `compute_ase(data_directory=..., filetype=..., timezone=..., verbose=False)` loads the CLIF tables
  itself and returns one row per blood-culture episode. Columns you need: `hospitalization_id`,
  `sepsis` (1 = ASE event), `type` (`community` or `hospital` onset),
  `ase_first_criteria_wo_lactate` (the first organ-dysfunction criterion met).

## Report, the only output

Metrics, in this order:

1. `hospitalizations_evaluated`: distinct `hospitalization_id`
2. `blood_culture_episodes`: rows returned
3. `ase_events`: rows with `sepsis == 1`
4. `hospitalizations_with_ase`: distinct `hospitalization_id` among those
5. `onset_<type>`: ASE events by onset type
6. `first_criterion_<value>`: ASE events by first criterion

Small-cell suppression: any count from 1 to 10 is reported as `<11`. Zero stays `0`.

Write `output/ase_summary_<label>.csv` with columns `metric, count_reported`, and
`output/ase_summary_<label>.png`, a horizontal bar chart of the same table where suppressed cells are
drawn at length 11, hatched, and labelled `<11`. Print the same table to stdout, nothing else.

## Rules, repeated from CLAUDE.md

- Never print rows or a DataFrame, never `.head()`. Schema, dtypes and counts only. The project hook
  blocks row printers in shell commands and blocks any call that names the real data.
- Keep stdout clean. clifpy logs every table load to stdout and its ASE code raises pandas
  FutureWarnings; silence both so stdout holds only the summary (`logging.disable(logging.INFO)` and
  a `FutureWarning` filter scoped to the `clifpy` module work).
- matplotlib is installed; use the `Agg` backend.

## Acceptance on the demo data (open CLIF-MIMIC demo, 100 patients)

| metric | count_reported |
|---|---|
| hospitalizations_evaluated | 310 |
| blood_culture_episodes | 525 |
| ase_events | 53 |
| hospitalizations_with_ase | 27 |
| onset_community | 44 |
| onset_hospital | <11 |
| first_criterion_first_qad | 30 |
| every other first_criterion_* | <11 |

Exit code 0, nothing on stderr, about one second of runtime.
