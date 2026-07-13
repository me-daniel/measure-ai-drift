"""Figure 5.1: Strategy distribution per model.
Figure A.1 (appendix): Plan validity rate per model.

Usage:
    python stats/scripts/fig_validity_strategy.py [--tier experiment]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from model_display import MODEL_COLORS, display_name, set_paper_style, sort_models

STRATEGY_CATEGORIES = [
    "confrontation",
    "self_empowerment",
    "safety",
    "cognitive_reframe",
    "social_support",
    "sensory_modulation",
]

STRATEGY_COLORS = {
    "confrontation": "#e63946",
    "self_empowerment": "#457b9d",
    "safety": "#2a9d8f",
    "cognitive_reframe": "#e9c46a",
    "social_support": "#f4a261",
    "sensory_modulation": "#264653",
}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--tier", choices=["test", "experiment"], default="experiment")
    args = parser.parse_args()

    if args.input is None:
        args.input = Path(f"stats/data/{args.tier}_runs.csv")
    output_dir = Path(f"thesis/figures")
    output_dir.mkdir(parents=True, exist_ok=True)

    set_paper_style()
    df = pd.read_csv(args.input)
    models = sort_models(list(df["model"].unique()))

    # --- Figure 5.1: Strategy distribution (main figure) ---
    fig1, ax = plt.subplots(figsize=(8, 5))

    strat_cols = [f"n_{cat}" for cat in STRATEGY_CATEGORIES]
    available = [c for c in strat_cols if c in df.columns]
    strat_data = df.groupby("model")[available].sum().reindex(models)

    row_totals = strat_data.sum(axis=1)
    strat_pct = strat_data.div(row_totals, axis=0) * 100

    bottom = np.zeros(len(models))
    for col in available:
        cat = col.replace("n_", "")
        values = strat_pct[col].values
        ax.bar(
            range(len(models)),
            values,
            bottom=bottom,
            label=cat,
            color=STRATEGY_COLORS.get(cat, "#888888"),
            edgecolor="white",
            linewidth=0.5,
        )
        bottom += values

    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([display_name(m) for m in models], rotation=45, ha="right", fontsize=10.5)
    ax.set_ylabel("Strategy share (%)")
    ax.set_title("Strategy distribution by model")
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=10)

    fig1.tight_layout()
    fig1.savefig(output_dir / "fig_5_1_strategy_distribution.pdf", bbox_inches="tight")
    fig1.savefig(output_dir / "fig_5_1_strategy_distribution.png", bbox_inches="tight", dpi=150)
    print(f"Saved fig_5_1 to {output_dir}/")
    plt.close(fig1)

    # --- Figure A.1: Plan validity (appendix) ---
    fig2, ax2 = plt.subplots(figsize=(8, 4))

    validity = df.groupby("model")["validity_rate"].mean().reindex(models)
    colors = [MODEL_COLORS.get(m, "#888888") for m in models]
    ax2.bar(range(len(models)), validity.values, color=colors, edgecolor="white")
    ax2.set_xticks(range(len(models)))
    ax2.set_xticklabels([display_name(m) for m in models], rotation=45, ha="right", fontsize=10.5)
    ax2.set_ylabel("Validity rate")
    ax2.set_ylim(0.95, 1.005)
    ax2.set_title("Plan validity rate by model")
    ax2.axhline(y=1.0, color="gray", linestyle="--", alpha=0.5)

    fig2.tight_layout()
    fig2.savefig(output_dir / "fig_A1_validity.pdf", bbox_inches="tight")
    fig2.savefig(output_dir / "fig_A1_validity.png", bbox_inches="tight", dpi=150)
    print(f"Saved fig_A1 to {output_dir}/")
    plt.close(fig2)


if __name__ == "__main__":
    main()
