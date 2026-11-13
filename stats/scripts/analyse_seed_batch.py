"""Analyse seed batch: compare seeded vs unseeded Mistral Large 3 runs.

Loads seed_batch (seed=42, fixed) and matching runs from experiments/latest/,
then compares Jaccard, BERTScore, Alignment side by side.

Outputs:
  - Console summary table
  - stats/data/seed_comparison_summary.csv (mean and SD per metric, temperature, source)
  - Figure: paired bar chart (seeded vs unseeded) per temperature

If the raw run folders are not on this machine, the figure is redrawn from the
summary CSV alone.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

from model_display import MODEL_COLORS, set_paper_style

SEED_DIR = Path("experiments/runs/seed_batch")
MAIN_DIR = Path("experiments/latest")
OUTPUT_DIR = Path("thesis/figures")
SUMMARY_PATH = Path("stats/data/seed_comparison_summary.csv")
METRICS = ["jaccard", "bertscore_f1", "alignment"]


def load_runs(batch_dir: Path, model_filter: str = "mistral_large") -> pd.DataFrame:
    rows = []
    for run_dir in sorted(batch_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        config_path = run_dir / "config.yaml"
        metrics_path = run_dir / "metrics.json"
        if not config_path.exists() or not metrics_path.exists():
            continue

        with open(config_path) as f:
            cfg = yaml.safe_load(f)

        if cfg["model"] != model_filter:
            continue

        with open(metrics_path) as f:
            metrics = json.load(f)

        rows.append({
            "vignette": cfg["vignette"],
            "temperature": cfg["temperature"],
            "jaccard": metrics.get("jaccard_all"),
            "bertscore_f1": metrics.get("bertscore_f1"),
            "alignment": metrics.get("alignment_mean"),
            "modal_agreement": metrics.get("modal_set_agreement"),
            "n_trials": metrics.get("n_trials"),
        })

    return pd.DataFrame(rows)


def summarise(seed_df: pd.DataFrame, main_df: pd.DataFrame) -> pd.DataFrame:
    """Mean and SD across vignettes per metric, temperature and source."""
    rows = []
    for metric in METRICS:
        for source, df in [("seeded", seed_df), ("unseeded", main_df)]:
            for temp in sorted(seed_df["temperature"].unique()):
                vals = df[df["temperature"] == temp][metric]
                rows.append({"metric": metric, "temperature": temp, "source": source,
                             "mean": round(vals.mean(), 4), "sd": round(vals.std(), 4)})
    return pd.DataFrame(rows)


def plot_comparison(summary: pd.DataFrame) -> None:
    """Paired bars in the Mistral Large 3 colour: unseeded solid, seeded hatched."""
    set_paper_style()
    color = MODEL_COLORS["mistral_large"]
    temps = sorted(summary["temperature"].unique())
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

    bar_width = 0.3
    x = np.arange(len(temps))

    for ax, metric, label in zip(axes, METRICS,
                                  ["Jaccard", "BERTScore F1", "Alignment"]):
        sub = summary[summary["metric"] == metric].set_index(["source", "temperature"])
        seeded = sub.loc["seeded"].loc[temps]
        unseeded = sub.loc["unseeded"].loc[temps]

        ax.bar(x - bar_width / 2, seeded["mean"], bar_width, yerr=seeded["sd"],
               label="Seeded (seed=42)", facecolor="white", edgecolor=color,
               hatch="/////", linewidth=1.2, capsize=3)
        ax.bar(x + bar_width / 2, unseeded["mean"], bar_width, yerr=unseeded["sd"],
               label="Unseeded (main)", facecolor=color, edgecolor=color,
               linewidth=1.2, capsize=3)

        ax.set_xticks(x)
        ax.set_xticklabels([f"T={t}" for t in temps])
        ax.set_title(label)
        ax.set_ylim(0.5, 1.05)

    axes[0].set_ylabel("Score")
    fig.suptitle("Mistral Large 3: Seeded vs Unseeded (20 trials, seed=42)", y=1.02)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False,
               handlelength=2.6, handleheight=1.3,
               bbox_to_anchor=(0.5, -0.08))
    fig.tight_layout()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_DIR / "fig_seed_comparison.pdf", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / "fig_seed_comparison.png", bbox_inches="tight", dpi=150)
    print(f"\nSaved fig_seed_comparison to {OUTPUT_DIR}/")
    plt.close(fig)


def main():
    if not SEED_DIR.exists() and SUMMARY_PATH.exists():
        print(f"No raw runs at {SEED_DIR}, redrawing from {SUMMARY_PATH}")
        plot_comparison(pd.read_csv(SUMMARY_PATH))
        return

    seed_df = load_runs(SEED_DIR)
    main_df = load_runs(MAIN_DIR)

    if seed_df.empty:
        print("No seed_batch runs found!")
        return

    # Filter main to matching temperatures
    seed_temps = set(seed_df["temperature"].unique())
    main_df = main_df[main_df["temperature"].isin(seed_temps)]

    seed_df["source"] = "seeded (seed=42)"
    main_df["source"] = "unseeded (main)"

    print("=" * 70)
    print("SEED BATCH ANALYSIS: Mistral Large 3")
    print(f"Seeded runs: {len(seed_df)} | Main runs: {len(main_df)}")
    print("=" * 70)

    # Per-temperature comparison
    metrics = METRICS
    for temp in sorted(seed_temps):
        print(f"\n--- T = {temp} ---")
        s = seed_df[seed_df["temperature"] == temp]
        m = main_df[main_df["temperature"] == temp]
        print(f"{'':>15s}  {'Seeded':>10s} {'Unseeded':>10s}  {'Delta':>8s}")
        for metric in metrics:
            sv = s[metric].mean()
            mv = m[metric].mean()
            delta = sv - mv
            print(f"  {metric:>13s}  {sv:10.3f} {mv:10.3f}  {delta:+8.3f}")
        # Modal agreement
        sv = s["modal_agreement"].mean()
        mv = m["modal_agreement"].mean()
        print(f"  {'modal_agree':>13s}  {sv:10.3f} {mv:10.3f}  {sv - mv:+8.3f}")

    # Per-vignette detail at each temp
    print("\n--- Per-vignette Jaccard ---")
    print(f"{'Vignette':>14s} {'Temp':>6s} {'Seeded':>8s} {'Unseeded':>8s} {'Delta':>8s}")
    for temp in sorted(seed_temps):
        for vig in sorted(seed_df["vignette"].unique()):
            sj = seed_df[(seed_df["temperature"] == temp) & (seed_df["vignette"] == vig)]["jaccard"]
            mj = main_df[(main_df["temperature"] == temp) & (main_df["vignette"] == vig)]["jaccard"]
            if sj.empty or mj.empty:
                continue
            sv = sj.values[0]
            mv = mj.values[0]
            print(f"  {vig:>12s} {temp:6.3f} {sv:8.3f} {mv:8.3f} {sv - mv:+8.3f}")

    summary = summarise(seed_df, main_df)
    summary.to_csv(SUMMARY_PATH, index=False)
    plot_comparison(summary)


if __name__ == "__main__":
    main()
