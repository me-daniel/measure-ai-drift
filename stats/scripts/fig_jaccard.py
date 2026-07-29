"""Figure 5.2: Jaccard and modal-set stability by temperature (headline figure).

Left subplot: line plot of median Jaccard per model across temperature scale,
with IQR shading. Reference lines for perfect (1.0) and random baseline (~0.2).
Right subplot: same layout for modal-set agreement rate.

Usage:
    python stats/scripts/fig_jaccard.py [--tier test|experiment]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RANDOM_BASELINE = 0.2  # Expected Jaccard for random 2-of-6 picks

from model_display import MODEL_COLORS, MODEL_GROUPS, display_name, set_paper_style, sort_models


def plot_metric(ax, df, metric, title, ylabel, model_filter=None):
    """Plot lines for a metric by model across temperatures."""
    models = sort_models(list(df["model"].unique()))
    if model_filter is not None:
        models = [m for m in models if m in model_filter]
    temps = sorted(df["temperature"].unique())

    for model in models:
        mdf = df[df["model"] == model]
        medians = []
        q1s = []
        q3s = []
        valid_temps = []

        for temp in temps:
            vals = mdf[mdf["temperature"] == temp][metric].dropna()
            if vals.empty:
                continue
            valid_temps.append(temp)
            medians.append(vals.median())
            q1s.append(vals.quantile(0.25))
            q3s.append(vals.quantile(0.75))

        if not valid_temps:
            continue

        color = MODEL_COLORS.get(model, "#888888")
        ax.plot(valid_temps, medians, marker="o", label=display_name(model), color=color, linewidth=2)
        ax.fill_between(valid_temps, q1s, q3s, alpha=0.07, color=color)

    ax.axhline(y=1.0, color="green", linestyle="--", alpha=0.4, label="Perfect")
    ax.axhline(y=RANDOM_BASELINE, color="red", linestyle=":", alpha=0.4, label=f"Random (~{RANDOM_BASELINE})")
    ax.set_xlabel("Temperature")
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, 1.1)
    ax.set_title(title)
    ax.legend(fontsize=9.5, loc="lower left")


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

    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Figure 5.2: Jaccard split into 3 family panels ---
    # 11in wide prints at ~66% scale (vs ~55% at 13.5in), so fonts render larger
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8), sharey=True)
    for ax, (group_name, group_models) in zip(axes, MODEL_GROUPS.items()):
        plot_metric(ax, df, "jaccard_all", group_name, "Median Jaccard (IQR)",
                    model_filter=set(group_models))
    # Only leftmost axis needs the y-label
    axes[1].set_ylabel("")
    axes[2].set_ylabel("")
    fig.suptitle("Jaccard similarity by model and temperature", y=1.02)
    fig.tight_layout()
    fig.savefig(output_dir / "fig_5_2_jaccard.pdf", bbox_inches="tight")
    fig.savefig(output_dir / "fig_5_2_jaccard.png", bbox_inches="tight", dpi=150)
    print(f"Saved fig_5_2 to {output_dir}/")
    plt.close(fig)

    # --- Figure 5.2b: Modal-set agreement (all models, single panel) ---
    has_modal = df["modal_set_agreement"].notna().any() if "modal_set_agreement" in df.columns else False
    if has_modal:
        fig2, ax2 = plt.subplots(1, 1, figsize=(7.5, 5))
        plot_metric(ax2, df, "modal_set_agreement", "Most common plan combination", "Agreement rate")
        # 13 entries cover the data if drawn inside the axes: park the legend outside
        ax2.legend(fontsize=9.5, loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
        fig2.tight_layout()
        fig2.savefig(output_dir / "fig_5_2b_modal_agreement.pdf", bbox_inches="tight")
        fig2.savefig(output_dir / "fig_5_2b_modal_agreement.png", bbox_inches="tight", dpi=150)
        print(f"Saved fig_5_2b to {output_dir}/")
        plt.close(fig2)


if __name__ == "__main__":
    main()
