"""Figure 5.3: BERTScore F1 by model and temperature.

Line plot: x-axis = temperature, one line per model, y-axis = mean BERTScore F1
(shaded SD band).

Usage:
    python stats/scripts/fig_bertscore.py [--tier test|experiment]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from model_display import MODEL_COLORS, MODEL_GROUPS, display_name, sort_models


def plot_bertscore(ax, df, title, model_filter=None):
    """Plot BERTScore F1 lines for selected models across temperatures."""
    models = sort_models(list(df["model"].unique()))
    if model_filter is not None:
        models = [m for m in models if m in model_filter]
    temps = sorted(df["temperature"].unique())

    for model in models:
        mdf = df[df["model"] == model]
        means = []
        sds = []
        valid_temps = []

        for temp in temps:
            vals = mdf[mdf["temperature"] == temp]["bertscore_f1"].dropna()
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
        ax.plot(valid_temps, means, marker="o", label=display_name(model), color=color, linewidth=2)
        ax.fill_between(valid_temps, means_arr - sds_arr, means_arr + sds_arr, alpha=0.07, color=color)

    ax.set_xlabel("Temperature")
    ax.set_ylabel("Mean BERTScore F1 (SD)")
    ax.set_ylim(0.5, 1.0)
    ax.set_title(title)
    ax.legend(fontsize=8)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--tier", choices=["test", "experiment"], default="experiment")
    args = parser.parse_args()

    if args.input is None:
        args.input = Path(f"stats/data/{args.tier}_runs.csv")
    output_dir = Path(f"thesis/figures")
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5), sharey=True)
    for ax, (group_name, group_models) in zip(axes, MODEL_GROUPS.items()):
        plot_bertscore(ax, df, group_name, model_filter=set(group_models))
    axes[1].set_ylabel("")
    axes[2].set_ylabel("")
    fig.suptitle("BERTScore F1 by model and temperature", fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(output_dir / "fig_5_3_bertscore.pdf", bbox_inches="tight")
    fig.savefig(output_dir / "fig_5_3_bertscore.png", bbox_inches="tight", dpi=150)
    print(f"Saved fig_5_3 to {output_dir}/")
    plt.close(fig)


if __name__ == "__main__":
    main()
