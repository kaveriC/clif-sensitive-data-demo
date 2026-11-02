#!/usr/bin/env python3
"""Compute CDC Adult Sepsis Events with clifpy and print aggregates only.

Usage: python run_ase.py --config config/demo.json
       python run_ase.py --config config/real.json   # run by the researcher, not by Claude
Output: output/ase_summary_<label>.csv and .png (aggregate counts; cells under 11 suppressed)
"""
import argparse, json, logging, pathlib, re, sys, warnings
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # file output only, no display
import matplotlib.pyplot as plt
from clifpy.utils.ase import compute_ase

logging.disable(logging.INFO)  # clifpy logs every table load to stdout; its file logs under output/logs keep WARNING and above
warnings.filterwarnings("ignore", category=FutureWarning, module=r"clifpy\.")  # pandas deprecations raised inside clifpy.utils.ase

SMALL = 11

def suppress(n: int) -> str:
    return f"<{SMALL}" if 0 < n < SMALL else str(n)

def plot(summary, path, label):
    """Horizontal bars of the summary. Suppressed cells are drawn at the threshold, hatched, labelled "<11"."""
    def pretty(m):
        m = m.replace("onset_", "onset: ").replace("first_criterion_", "first criterion: ").replace("_", " ").capitalize()
        return re.sub(r"\b(ase|qad|imv|aki)\b", lambda x: x.group().upper(), m, flags=re.I)
    hidden = summary["count_reported"].str.startswith("<")
    length = summary["count"].where(~hidden, SMALL)  # every suppressed bar has the same length
    group = summary["metric"].str.extract(r"^(onset|first_criterion)")[0].fillna("totals")
    y = pd.Series(range(len(summary))) + (group != group.shift()).cumsum() * 0.6  # air between groups
    fig, ax = plt.subplots(figsize=(8, 0.42 * len(summary) + 1.6), dpi=200, facecolor="#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    ax.barh(y[~hidden], length[~hidden], height=0.55, color="#2a78d6")
    ax.barh(y[hidden], length[hidden], height=0.55, facecolor="none", edgecolor="#898781", hatch="////", linewidth=1)
    for yi, l, txt in zip(y, length, summary["count_reported"]):
        ax.text(l + length.max() * 0.012, yi, txt, va="center", fontsize=9, color="#0b0b0b")
    ax.set_yticks(y); ax.set_yticklabels(summary["metric"].map(pretty), fontsize=9, color="#52514e")
    ax.invert_yaxis(); ax.set_xticks([]); ax.set_xlim(0, length.max() * 1.12)
    for side in ("top", "right", "bottom"): ax.spines[side].set_visible(False)
    ax.spines["left"].set_color("#c3c2b7"); ax.tick_params(axis="y", length=0)
    ax.set_title(f"CDC Adult Sepsis Events, {label} data", loc="left", fontsize=12, color="#0b0b0b", pad=24)
    ax.text(0, 1.02, f"Counts. Hatched = fewer than {SMALL}, exact count suppressed.", transform=ax.transAxes, fontsize=9, color="#52514e")
    fig.tight_layout(); fig.savefig(path); plt.close(fig)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--config", required=True)
    cfg = json.load(open(ap.parse_args().config))
    out = pathlib.Path(cfg.get("output_directory", "output")); out.mkdir(exist_ok=True)
    df = compute_ase(data_directory=cfg["data_directory"], filetype=cfg["filetype"],
                     timezone=cfg["timezone"], verbose=False)
    ase_col = next(c for c in df.columns if c.lower() in ("sepsis", "ase", "ase_flag", "has_ase"))
    flag = df[ase_col].fillna(0).astype(int).astype(bool)
    rows = [("hospitalizations_evaluated", int(df["hospitalization_id"].nunique())),
            ("blood_culture_episodes", len(df)),
            ("ase_events", int(flag.sum())),
            ("hospitalizations_with_ase", int(df.loc[flag, "hospitalization_id"].nunique()))]
    if "type" in df.columns:  # hospital-onset vs community-onset
        for k, v in df.loc[flag, "type"].value_counts(dropna=False).items():
            rows.append((f"onset_{k}", int(v)))
    if "ase_first_criteria_wo_lactate" in df.columns:
        for k, v in df.loc[flag, "ase_first_criteria_wo_lactate"].value_counts(dropna=True).items():
            rows.append((f"first_criterion_{k}", int(v)))
    summary = pd.DataFrame(rows, columns=["metric", "count"])
    summary["count_reported"] = summary["count"].map(suppress)
    label = cfg.get("label", "run"); stem = out / f"ase_summary_{label}"
    summary[["metric", "count_reported"]].to_csv(f"{stem}.csv", index=False)
    plot(summary, f"{stem}.png", label)
    print(f"data: {cfg['data_directory']}")
    print(f"columns in ASE output: {len(df.columns)}; schema: {list(df.columns)[:8]}...")
    for m, c in summary[["metric", "count_reported"]].itertuples(index=False):
        print(f"  {m:28s} {c}")
    print(f"wrote {stem}.csv and {stem}.png (aggregates only)")

if __name__ == "__main__":
    sys.exit(main())
