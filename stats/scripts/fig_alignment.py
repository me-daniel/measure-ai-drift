"""Figure 5.6: Alignment by model and temperature.

Left: Line plot of mean alignment by temperature per model.
Right: Bar chart of mean alignment per model (collapsed across temps).

Usage:
    python stats/scripts/fig_alignment.py [--tier experiment]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from model_display import MODEL_COLORS, display_name, set_paper_style, sort_models


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--tier", choices=["test", "experiment"], default="experiment")
    args = parser.parse_args()

    if args.input is None:
        args.input = Path(f"stats/data/{args.tier}_runs.csv")
    output_dir = Path(f"thesis/figures")

    set_paper_style()
    df = pd.read_csv(args.input)
    models = sort_models(list(df["model"].unique()))
    temps = sorted(df["temperature"].unique())

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.8))

    # Left: line plot by temperature
    for model in models:
        mdf = df[df["model"] == model]
        means = []
        sds = []
        valid_temps = []

        for temp in temps:
            vals = mdf[mdf["temperature"] == temp]["alignment_mean"].dropna()
            if vals.empty:
                continue
            valid_temps.append(temp)
            means.append(vals.mean())
            sds.append(vals.std() if len(vals) > 1 else 0)

        if not valid_temps:
            continue

        color = MODEL_COLORS.get(model, "#888888")
        means_arr = np.array(means)
        sds_arr = np.array(sds)
        ax1.plot(valid_temps, means, marker="o", label=display_name(model),
                 color=color, linewidth=2)
        lower = np.clip(means_arr - sds_arr, 0, 1)
        upper = np.clip(means_arr + sds_arr, 0, 1)
        ax1.fill_between(valid_temps, lower, upper, alpha=0.07, color=color)

    ax1.set_xlabel("Temperature")
    ax1.set_ylabel("Mean Alignment (SD)")
    ax1.set_ylim(0.5, 1.05)
    ax1.set_title("Plan-response alignment by temperature")

    # Right: bar chart per model (collapsed)
    model_means = df.groupby("model")["alignment_mean"].mean().reindex(models)
    model_sds = df.groupby("model")["alignment_mean"].std().reindex(models)
    colors = [MODEL_COLORS.get(m, "#888888") for m in models]
    x = range(len(models))

    # Clip error bars so they don't exceed [0, 1]
    err_lower = np.clip(model_sds.values, 0, model_means.values)
    err_upper = np.clip(model_sds.values, 0, 1.0 - model_means.values)

    ax2.bar(x, model_means.values, yerr=[err_lower, err_upper], capsize=3,
            color=colors, edgecolor="white", linewidth=0.5)
    ax2.set_xticks(list(x))
    ax2.set_xticklabels([display_name(m) for m in models], rotation=45,
                         ha="right", fontsize=10.5)
    ax2.set_ylabel("Mean Alignment")
    ax2.set_ylim(0.5, 1.05)
    ax2.set_title("Overall alignment by model")

    fig.tight_layout()
    # Shared legend below both panels: inside ax1 it covers the lower curves
    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.02),
               ncol=4, fontsize=9.5, frameon=False)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "fig_5_6_alignment.pdf", bbox_inches="tight")
    fig.savefig(output_dir / "fig_5_6_alignment.png", bbox_inches="tight", dpi=150)
    print(f"Saved fig_5_6_alignment to {output_dir}/")
    plt.close(fig)


if __name__ == "__main__":
    main()
