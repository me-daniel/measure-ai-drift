"""Figure 5.4 (appendix): Vignette difficulty by temperature (and slice depth if available).

Grid of model x vignette heatmaps, one per temperature, laid out in two
columns so the figure fits a portrait page at readable size.
If multi-slice data is available, adds a slice-depth line panel.

Usage:
    python stats/scripts/fig_vignette_slice.py [--tier test|experiment]
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from model_display import display_name, set_paper_style, sort_models


def make_heatmap(ax, df, models, vignettes, title, cbar=False, cbar_ax=None):
    """Draw a model x vignette heatmap on the given axis."""
    pivot = df.groupby(["model", "vignette"])["jaccard_all"].median().unstack(fill_value=np.nan)
    pivot = pivot.reindex(index=models, columns=vignettes)
    pivot.index = [display_name(m) for m in pivot.index]

    sns.heatmap(
        pivot,
        annot=True,
        fmt=".2f",
        annot_kws={"fontsize": 9.5},
        cmap="RdYlGn",
        vmin=0,
        vmax=1,
        ax=ax,
        cbar=cbar,
        cbar_ax=cbar_ax,
        cbar_kws={"label": "Median Jaccard"} if cbar else None,
    )
    ax.set_title(title)
    ax.set_ylabel("")
    ax.set_xlabel("")


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
    vignettes = sorted(df["vignette"].unique())
    temps = sorted(df["temperature"].unique())
    # Slice panel only makes sense with more than one slice depth
    has_slices = "slice" in df.columns and df["slice"].dropna().nunique() > 1

    # Two-column grid, one heatmap per temperature (+ optional slice panel)
    n_panels = len(temps) + (1 if has_slices else 0)
    n_cols = 2
    n_rows = math.ceil(n_panels / n_cols)
    fig, axes = plt.subplots(
        n_rows, n_cols,
        figsize=(6.4 * n_cols, max(4, len(models) * 0.42 + 1.2) * n_rows),
    )
    axes = np.atleast_1d(axes).flatten()

    # One heatmap per temperature; only leftmost column keeps model names
    for i, temp in enumerate(temps):
        temp_df = df[df["temperature"] == temp]
        make_heatmap(axes[i], temp_df, models, vignettes, f"T = {temp}")
        if i % n_cols != 0:
            axes[i].set_yticklabels([])

    # Slice depth panel (if available)
    if has_slices:
        ax_slice = axes[len(temps)]
        for model in models:
            model_data = df[df["model"] == model]
            slice_medians = model_data.groupby("slice")["jaccard_all"].median()
            ax_slice.plot(slice_medians.index, slice_medians.values, marker="o", label=model)

        ax_slice.set_xlabel("Slice depth")
        ax_slice.set_ylabel("Median Jaccard")
        ax_slice.set_title("Stability by conversation depth")
        ax_slice.legend(fontsize=9)
        ax_slice.set_ylim(0, 1.1)

    # Hide unused grid cells
    for ax in axes[n_panels:]:
        ax.set_visible(False)

    fig.tight_layout()
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "fig_5_4_vignette_slice.pdf", bbox_inches="tight")
    fig.savefig(output_dir / "fig_5_4_vignette_slice.png", bbox_inches="tight", dpi=150)
    print(f"Saved fig_5_4 to {output_dir}/")
    plt.close(fig)


if __name__ == "__main__":
    main()
