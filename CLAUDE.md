# CLIF sensitive-data demo

Rules for this project:
- Develop and test only against `data/demo` (open CLIF-MIMIC demo, 100 patients). Never read `data/phi` or the real CLIF-MIMIC path; both are denied and that is intentional.
- Never print rows. Report schema, dtypes, counts, and aggregates; counts under 11 are shown as "<11".
- Real-data runs are done by the researcher in a separate terminal with `python run_ase.py --config config/real.json`. You may read `output/*_summary.csv` (aggregates only) and interpret them.
- Keep intermediates under `output/` (gitignored), never in the scratchpad or /tmp.
- Run `/sensitive-data-check` before any real-data work.
