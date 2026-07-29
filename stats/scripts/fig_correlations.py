"""Figure 5.5: Metric correlation -- median Jaccard vs mean BERTScore per model.

Scatter with one point per model, colored by model. Labels use display names
with smart placement to avoid overlaps. No redundant legend.

Usage:
    python stats/scripts/fig_correlations.py [--tier test|experiment]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats as sp

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
    df = pd.read_csv(args.input).dropna(subset=["jaccard_all", "bertscore_f1"])

    model_stats = df.groupby("model").agg(
        jaccard=("jaccard_all", "median"),
        bertscore=("bertscore_f1", "mean"),
    )

    fig, ax = plt.subplots(figsize=(8, 6))

    # Plot points in canonical order
    ordered = sort_models(list(model_stats.index))
    for model in ordered:
        row = model_stats.loc[model]
        color = MODEL_COLORS.get(model, "#888888")
        ax.scatter(
            row["jaccard"],
            row["bertscore"],
            color=color,
            s=170,
            zorder=3,
            edgecolors="white",
            linewidth=1.5,
        )

    # Hand-tuned label placement per model: (dx, dy, ha), offsets in points.
    # Tuned for the 11-model dataset: four models share Jaccard = 1.0 on the
    # right edge (labels staggered right), OLMo and Qwen 122B dots coincide.
    LABEL_OFFSETS = {
        # left cluster
        "qwen35_397b": (-10, -3, "right"),
        "llama70b": (0, -16, "center"),
        "qwen35_27b": (0, 10, "center"),
        "mistral_large": (10, -3, "left"),
        "mistral_large2": (2, -30, "center"),
        "mistral_small4": (10, -3, "left"),
        "command_a": (10, -3, "left"),
        # right cluster
        "sonnet46": (-10, -3, "right"),
        "gpt54": (0, -16, "center"),
        "mistral_small32": (10, -3, "left"),
        "olmo3_32b": (10, -12, "left"),
        "qwen35_122b": (10, 5, "left"),
        "mistral_medium35": (10, -3, "left"),
    }

    for model, row in model_stats.iterrows():
        x, y = row["jaccard"], row["bertscore"]
        name = display_name(model)
        color = MODEL_COLORS.get(model, "#888888")

        if model in LABEL_OFFSETS:
            dx, dy, ha = LABEL_OFFSETS[model]
        else:
            dx, dy, ha = 10, -3, "left"
            print(f"WARNING: no label offset tuned for '{model}', using default -- check for overlaps")

        ax.annotate(
            name,
            (x, y),
            textcoords="offset points",
            xytext=(dx, dy),
            fontsize=10.5,
            ha=ha,
            color=color,
            fontweight="bold",
        )

    # Spearman on model-level aggregates
    n = len(model_stats)
    if n >= 3:
        rho, p = sp.spearmanr(model_stats["jaccard"], model_stats["bertscore"])
        label = f"Spearman rho = {rho:.3f}"
        if p < 0.001:
            label += ", p < 0.001"
        else:
            label += f", p = {p:.3f}"
        label += f" (N = {n} models)"

        ax.annotate(
            label,
            xy=(0.05, 0.95),
            xycoords="axes fraction",
            fontsize=10.5,
            va="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
        )

    ax.set_xlabel("Median Jaccard similarity (strategy consistency)")
    ax.set_ylabel("Mean BERTScore F1 (semantic consistency)")
    ax.set_title("Strategy consistency vs semantic consistency")

    ax.set_xlim(0.6, 1.06)
    ax.set_ylim(0.66, 0.88)

    fig.tight_layout()
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "fig_5_5_correlations.pdf", bbox_inches="tight")
    fig.savefig(output_dir / "fig_5_5_correlations.png", bbox_inches="tight", dpi=150)
    print(f"Saved fig_5_5 to {output_dir}/")
    plt.close(fig)


if __name__ == "__main__":
    main()
