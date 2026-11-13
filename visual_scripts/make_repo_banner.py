"""Repository banner (GitHub social preview, 1280x640) in the reDreamAI palette.

Left: title, procedure and design numbers. Right: mean Jaccard per model at the
lowest and highest sweep temperature, read from stats/data/experiment_runs.csv.

Usage:
    uv run python visual_scripts/make_repo_banner.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch

sys.path.insert(0, str(Path(__file__).parent.parent / "stats" / "scripts"))
from model_display import display_name  # noqa: E402

DATA = Path("stats/data/experiment_runs.csv")
OUTPUT = Path("visualizations/repo_banner.png")

# reDreamAI dark theme (website style.css)
BG = "#0c0a1a"
CARD = "#15132b"
BORDER = "#2b2850"
TURQUOISE = "#18d9ea"
VIOLET = "#6366f1"
VIOLET_DEEP = "#7c3aed"
VIOLET_LIGHT = "#b39dff"
INK = "#ffffff"
INK_SOFT = "#d1d5db"
INK_MUTED = "#9ca3af"
BRAND = LinearSegmentedColormap.from_list("brand", [TURQUOISE, VIOLET, VIOLET_DEEP])

W, H = 12.8, 6.4  # inches, 1280x640 at dpi 100


def gradient_bar(fig, x, y, w, h):
    ax = fig.add_axes([x / W, y / H, w / W, h / H])
    ax.imshow(np.linspace(0, 1, 256).reshape(1, -1), aspect="auto", cmap=BRAND)
    ax.axis("off")


def chip(ax, x, y, w, h, title, sub):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.09",
                                facecolor=CARD, edgecolor=BORDER, linewidth=1))
    ax.text(x + w / 2, y + h * 0.63, title, color=INK, fontsize=10.5, fontweight="bold",
            ha="center", va="center")
    ax.text(x + w / 2, y + h * 0.28, sub, color=INK_MUTED, fontsize=8.5,
            ha="center", va="center")


def main():
    plt.rcParams["font.family"] = ["Arial", "Helvetica", "DejaVu Sans"]
    df = pd.read_csv(DATA)
    temps = sorted(df["temperature"].unique())
    t_lo, t_hi = temps[0], temps[-1]
    means = df.groupby(["model", "temperature"])["jaccard_all"].mean().unstack()
    order = means.mean(axis=1).sort_values().index  # least stable at the bottom
    n_trials = int(df["n_trials"].sum())

    fig = plt.figure(figsize=(W, H), facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")

    # --- Left: title, procedure, design numbers ---
    x0 = 0.7
    ax.text(x0, 5.55, "MEASURE-AI-DRIFT", color=TURQUOISE, fontsize=10.5, fontweight="bold")
    ax.text(x0, 4.82, "Measuring Drift in", color=INK, fontsize=31, fontweight="bold")
    ax.text(x0, 4.22, "Therapeutic AI", color=INK, fontsize=31, fontweight="bold")
    gradient_bar(fig, x0, 3.98, 2.3, 0.055)
    ax.text(x0, 3.52, "Does an LLM therapist make the same decision twice?",
            color=INK_SOFT, fontsize=13)

    chips = [("Frozen history", "same input"), ("20 trials", "per condition"),
             ("Plan + response", "one call"), ("3 metrics", "per layer")]
    cw, ch, gap = 1.26, 0.72, 0.2
    for i, (title, sub) in enumerate(chips):
        cx = x0 + i * (cw + gap)
        chip(ax, cx, 2.3, cw, ch, title, sub)
        if i:
            ax.annotate("", xy=(cx - 0.03, 2.3 + ch / 2), xytext=(cx - gap + 0.03, 2.3 + ch / 2),
                        arrowprops=dict(arrowstyle="-|>", color=INK_MUTED, lw=1))

    stats = [(df["model"].nunique(), "models"), (df["vignette"].nunique(), "patient vignettes"),
             (len(temps), "temperatures"), (f"{n_trials:,}", "trials")]
    for i, (value, label) in enumerate(stats):
        sx = x0 + i * (cw + gap)
        ax.text(sx, 1.25, str(value), color=INK, fontsize=22, fontweight="bold")
        ax.text(sx, 0.95, label, color=INK_MUTED, fontsize=9.5)

    # --- Right: decision consistency per model at the two ends of the sweep ---
    px, pw = 7.0, 5.1
    ax.add_patch(FancyBboxPatch((px, 0.6), pw, 5.2, boxstyle="round,pad=0,rounding_size=0.14",
                                facecolor=CARD, edgecolor=BORDER, linewidth=1))
    ax.text(px + 0.3, 5.37, "Decision consistency by model", color=INK, fontsize=12.5,
            fontweight="bold")
    ax.text(px + 0.3, 5.08, "Mean pairwise Jaccard of declared strategy sets",
            color=INK_MUTED, fontsize=9)

    lo, hi = 0.5, 1.0
    tx0, tx1 = px + 1.95, px + pw - 0.35
    to_x = lambda v: tx0 + (v - lo) / (hi - lo) * (tx1 - tx0)
    y_top, y_bot = 4.55, 1.25
    ys = np.linspace(y_bot, y_top, len(order))

    for tick in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        ax.plot([to_x(tick)] * 2, [y_bot - 0.18, y_top + 0.18], color=BORDER, lw=0.8, zorder=1)
        ax.text(to_x(tick), y_bot - 0.36, f"{tick:.1f}", color=INK_MUTED, fontsize=8.5, ha="center")

    for y, model in zip(ys, order):
        a, b = means.loc[model, t_lo], means.loc[model, t_hi]
        ax.text(tx0 - 0.15, y, display_name(model), color=INK_SOFT, fontsize=9.5,
                ha="right", va="center")
        ax.plot([to_x(a), to_x(b)], [y, y], color="#4b4a78", lw=2, zorder=2, solid_capstyle="round")
        ax.scatter(to_x(b), y, s=62, color=VIOLET_LIGHT, edgecolors=CARD, linewidths=1.2, zorder=3)
        ax.scatter(to_x(a), y, s=62, color=TURQUOISE, edgecolors=CARD, linewidths=1.2, zorder=4)

    lx = px + pw - 1.85
    for dx, color, label in [(0, TURQUOISE, f"T = {t_lo:g}"), (0.82, VIOLET_LIGHT, f"T = {t_hi:g}")]:
        ax.scatter(lx + dx, 5.42, s=55, color=color, edgecolors=CARD, linewidths=1.2)
        ax.text(lx + dx + 0.14, 5.42, label, color=INK_SOFT, fontsize=9.5, va="center")

    ax.text(x0, 0.32, "Imagery Rehearsal Therapy  ·  EU-sovereign, open-weight and proprietary models",
            color=INK_MUTED, fontsize=9)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=200, facecolor=BG)
    print(f"Saved {OUTPUT}")
    plt.close(fig)


if __name__ == "__main__":
    main()
