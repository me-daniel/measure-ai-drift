"""Exploratory figures: Nemotron 3 hybrids vs size-matched Qwen and Mistral models.

Branch 24_Nemotron only, not part of the paper. Writes two figures to docs/figures/:
  fig_nemotron_temperature: mean Jaccard (top) and mean BERTScore (bottom) by
      temperature, one panel per size class. Nemotron also has T=1.0 (NVIDIA default).
  fig_nemotron_ranking: modal-set agreement of all 16 models on the shared sweep.

Colours are figure-specific, one per family (Nemotron aqua, Qwen blue, Mistral
orange), validated all-pairs with the dataviz palette validator. The paper's
per-model colours fail that check when Qwen and Mistral share a panel.

Usage: uv run python stats/scripts/fig_nemotron.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from model_display import display_name, set_paper_style

DATA = Path("stats/data")
OUT = Path("docs/figures")
SWEEP = [0.0, 0.075, 0.15, 0.3, 0.6]

FAMILY_COLORS = {"Nemotron": "#1baf7a", "Qwen": "#2a78d6", "Mistral": "#eb6834"}
OTHER_COLOR = "#767570"
MARKERS = {"Nemotron": "o", "Qwen": "s", "Mistral": "^", "Other": "o"}
INK, INK_MUTED = "#0b0b0b", "#52514e"

NEMO_NAMES = {"nemotron3_nano": "Nemotron 3 Nano", "nemotron3_super": "Nemotron 3 Super",
              "nemotron3_ultra": "Nemotron 3 Ultra"}

# One panel per size class: (title, nemotron, [(peer, linestyle), ...])
PANELS = [
    ("~30B: Nano (30B-A3B)", "nemotron3_nano", [("qwen35_27b", "-"), ("mistral_small32", "-")]),
    ("~120B: Super (120B-A12B)", "nemotron3_super", [("qwen35_122b", "-"), ("mistral_small4", "-")]),
    ("550B+: Ultra (550B-A55B)", "nemotron3_ultra", [("qwen35_397b", "-"), ("mistral_large", "-"), ("mistral_large4", "--")]),
]
ROWS = [("jaccard_all", "Mean Jaccard\n(decision consistency)", (0.3, 1.04)),
        ("bertscore_f1", "Mean BERTScore F1\n(response similarity)", (0.6, 0.92))]


def name(m: str) -> str:
    return NEMO_NAMES.get(m, display_name(m))


def short(m: str) -> str:
    """Compact direct label: family prefix dropped, the panel legend carries it."""
    return name(m).replace("Nemotron 3 ", "").replace("Mistral ", "").replace("Qwen 3.5 ", "Qwen ")


def family(m: str) -> str:
    if m.startswith("nemotron"):
        return "Nemotron"
    if m.startswith("qwen"):
        return "Qwen"
    if m.startswith("mistral"):
        return "Mistral"
    return "Other"


def color(m: str) -> str:
    return FAMILY_COLORS.get(family(m), OTHER_COLOR)


def dodge(items: list[tuple[float, str, str]], gap: float) -> list[tuple[float, str, str]]:
    """Spread end labels vertically so none sit closer than `gap`."""
    items = sorted(items)
    for i in range(1, len(items)):
        if items[i][0] - items[i - 1][0] < gap:
            items[i] = (items[i - 1][0] + gap, *items[i][1:])
    return items


def temperature_figure(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(15, 8.6), sharey="row", sharex=True)
    means = df.groupby(["model", "temperature"])[["jaccard_all", "bertscore_f1"]].mean()

    for col, (title, nemo, peers) in enumerate(PANELS):
        for row, (metric, ylabel, ylim) in enumerate(ROWS):
            ax = axes[row, col]
            ax.axvspan(0.75, 1.06, color="#f1f0ec", zorder=0, lw=0)
            span = ylim[1] - ylim[0]
            ends = {"nemo": [], "peer": []}
            for m, ls in [(nemo, "-")] + peers:
                s = means.loc[m, metric]
                is_nemo = m == nemo
                ax.plot(s.index, s.values, ls, color=color(m), lw=2.6 if is_nemo else 1.8,
                        marker=MARKERS[family(m)], ms=7 if is_nemo else 6,
                        markeredgecolor="white", markeredgewidth=1.0, zorder=3 if is_nemo else 2,
                        label=name(m))
                ends["nemo" if is_nemo else "peer"].append((s.values[-1], short(m), s.index[-1]))
                if is_nemo:  # mark the vendor-default point
                    ax.plot([1.0], [s.loc[1.0]], "o", ms=12, mfc="none", mec=color(m), mew=1.6, zorder=4)
            # direct labels in ink right of each line end, dodged per column, with a
            # leader line when a label had to move away from its line end
            for group in ends.values():
                for y_lab, label, x_end in dodge([(y, lbl, x) for y, lbl, x in group], gap=0.06 * span):
                    y_true = next(y for y, lbl, _ in group if lbl == label)
                    x_lab = x_end + 0.045
                    if abs(y_lab - y_true) > 0.015 * span:
                        ax.plot([x_end + 0.012, x_lab - 0.006], [y_true, y_lab], color="#b5b4ae", lw=0.8, zorder=4)
                    ax.text(x_lab, y_lab, label, va="center", fontsize=10, color=INK, zorder=6,
                            bbox=dict(boxstyle="square,pad=0.12", fc="white", ec="none"), clip_on=False)
            ax.set_ylim(*ylim)
            ax.set_xlim(-0.03, 1.06)
            ax.set_xticks([0, 0.15, 0.3, 0.6, 1.0])
            ax.grid(axis="y", color="#e4e3df", lw=0.8)
            ax.set_axisbelow(True)
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
            for side in ("left", "bottom"):
                ax.spines[side].set_color("#b5b4ae")
            ax.tick_params(colors=INK_MUTED)
            if row == 0:
                ax.set_title(title, color=INK, loc="left")
                ax.legend(loc="lower left", fontsize=9.5, frameon=False, labelspacing=0.25, handlelength=2.2)
            if row == 1:
                ax.set_xlabel("Temperature")
            if col == 0:
                ax.set_ylabel(ylabel, color=INK)
    axes[0, 0].text(0.905, 1.025, "T=1.0\n(Nemotron only)", ha="center", va="top",
                    fontsize=9.5, color=INK_MUTED)
    fig.suptitle("Nemotron 3 hybrids vs size-matched Qwen and Mistral models", x=0.06, ha="left", color=INK)
    fig.text(0.06, 0.005, "Means over 6 vignettes per point (20 trials each). Qwen and Mistral: canonical runs (mostly default routing). "
             "Nemotron: pinned single provider.\nRinged point: T=1.0, NVIDIA's default for Super and Ultra (Nano: greedy for reasoning off).", fontsize=9.5, color=INK_MUTED)
    fig.tight_layout(rect=(0, 0.04, 0.97, 0.97), w_pad=4.5)
    save(fig, "fig_nemotron_temperature")


def ranking_figure(df: pd.DataFrame) -> None:
    sweep = df[df.temperature.isin(SWEEP)]
    modal = sweep.groupby("model").modal_set_agreement.mean().sort_values()
    fig, ax = plt.subplots(figsize=(8.5, 7.2))
    y = range(len(modal))
    for i, (m, v) in enumerate(modal.items()):
        is_nemo = m.startswith("nemotron")
        ax.plot([0.55, v], [i, i], color="#e4e3df", lw=1.2, zorder=1)
        ax.plot([v], [i], "o", color=color(m), ms=11 if is_nemo else 8.5,
                markeredgecolor="white", markeredgewidth=1.5, zorder=3)
        if is_nemo:
            ax.text(v + 0.012, i, f"{v:.3f}", va="center", fontsize=10.5, color=INK)
    ax.set_yticks(list(y))
    ax.set_yticklabels([name(m) for m in modal.index])
    for lbl, m in zip(ax.get_yticklabels(), modal.index):
        lbl.set_color(INK if m.startswith("nemotron") else INK_MUTED)
        lbl.set_fontweight("bold" if m.startswith("nemotron") else "normal")
    ax.set_xlim(0.55, 1.03)
    ax.set_xlabel("Modal-set agreement (shared sweep T = 0 to 0.6)")
    ax.grid(axis="x", color="#e4e3df", lw=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#b5b4ae")
    ax.tick_params(axis="y", length=0)
    ax.tick_params(colors=INK_MUTED)
    handles = [plt.Line2D([], [], marker="o", ls="", color=c, ms=8.5, label=f)
               for f, c in [*FAMILY_COLORS.items(), ("Other", OTHER_COLOR)]]
    ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=10.5)
    ax.set_title("Decision consistency of all 16 models", loc="left", color=INK)
    fig.text(0.02, 0.005, "Pinned single provider: Nemotron, Mistral Large 4, Command A, GPT-5.4 (native API). "
             "Others: default routing.", fontsize=9, color=INK_MUTED)
    fig.tight_layout(rect=(0, 0.025, 1, 1))
    save(fig, "fig_nemotron_ranking")


def save(fig, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{stem}.{ext}", dpi=200 if ext == "png" else None, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / stem}.png/.pdf")


def main() -> None:
    set_paper_style()
    df = pd.concat([pd.read_csv(DATA / "experiment_runs.csv"), pd.read_csv(DATA / "nemotron_runs.csv")],
                   ignore_index=True)
    temperature_figure(df)
    ranking_figure(df)


if __name__ == "__main__":
    main()
