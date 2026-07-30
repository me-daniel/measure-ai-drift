"""Figure 3.1: End-to-end pipeline diagram.

Shows the two-stack architecture: generation → frozen histories → evaluation → metrics.
Stacks stacked vertically, frozen history feeds down into evaluation stack.

Output: thesis/figures/fig_3_1_pipeline.pdf
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
C_GEN = "#d4e6f1"
C_EVAL = "#fadbd8"
C_BOX = "#fdfefe"
C_ARROW = "#566573"
C_BORDER = "#2c3e50"
C_ACCENT = "#e74c3c"


def draw_box(ax, x, y, text, subtext=None, color=C_BOX, w=2.2, h=1.0):
    box = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.1", facecolor=color,
        edgecolor=C_BORDER, linewidth=1.3, zorder=3,
    )
    ax.add_patch(box)
    if subtext:
        ax.text(x, y + 0.15, text, ha="center", va="center",
                fontsize=11, fontweight="bold", zorder=4)
        ax.text(x, y - 0.18, subtext, ha="center", va="center",
                fontsize=8.5, color="#555", zorder=4, style="italic")
    else:
        ax.text(x, y, text, ha="center", va="center",
                fontsize=11, fontweight="bold", zorder=4)


def arrow(ax, x1, y1, x2, y2, color=C_ARROW, lw=1.5):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", color=color, lw=lw), zorder=2,
    )


def main():
    fig, ax = plt.subplots(figsize=(15, 8))
    ax.set_xlim(-0.8, 15.5)
    ax.set_ylim(-1.0, 8.5)
    ax.set_aspect("equal")
    ax.axis("off")

    # ── Generation Stack background (top) ───────────────────────────────
    cx = 6.7  # center x for both stacks
    gen_bg = FancyBboxPatch(
        (cx - 7.2, 4.8), 14.4, 2.0,
        boxstyle="round,pad=0.2", facecolor=C_GEN,
        edgecolor="#2471a3", linewidth=1.2, linestyle="--", alpha=0.4, zorder=1,
    )
    ax.add_patch(gen_bg)
    ax.text(cx, 7.13, "Generation Stack", fontsize=12, fontweight="bold",
            color="#2471a3", ha="center", zorder=4)
    ax.text(cx, 6.77, "Run once per vignette", fontsize=9,
            color="#2471a3", style="italic", ha="center", zorder=4)

    # ── Evaluation Stack background (bottom) ────────────────────────────
    eval_bg = FancyBboxPatch(
        (cx - 7.2, 0.3), 14.4, 2.0,
        boxstyle="round,pad=0.2", facecolor=C_EVAL,
        edgecolor="#c0392b", linewidth=1.2, linestyle="--", alpha=0.4, zorder=1,
    )
    ax.add_patch(eval_bg)
    ax.text(cx, 2.62, "Evaluation Stack", fontsize=12, fontweight="bold",
            color="#c0392b", ha="center", zorder=4)
    ax.text(cx, 2.27, "Run 20 trials per vignette \u00d7 model \u00d7 temperature",
            fontsize=9, color="#c0392b", style="italic", ha="center", zorder=4)

    # ── Generation row (y=5.8) ──────────────────────────────────────────
    # 5 boxes, evenly spaced across center (total span ~12.4, centered on 6.7)
    gy = 5.8
    bw = 2.0  # box width
    gap = 1.1  # gap between boxes
    stride = bw + gap
    gx0 = 6.7 - 2 * stride  # leftmost box center

    gx = [gx0 + i * stride for i in range(5)]
    draw_box(ax, gx[0], gy, "6 Patients", "Character Vignettes", w=bw)
    draw_box(ax, gx[1], gy, "3-Agents", "Dialogue Loop", w=bw)
    draw_box(ax, gx[2], gy, "Therapy", "Sessions", w=bw)
    draw_box(ax, gx[3], gy, "Histories", "frozen dialogues", w=bw)
    draw_box(ax, gx[4], gy, "Slices", "cut at rescripting turns", color="#fff9c4", w=bw)

    ax.text(gx[1], 4.95, "Patient + Router + Therapist",
            ha="center", va="top", fontsize=8, color="#555", zorder=4)

    # Generation arrows
    for i in range(4):
        arrow(ax, gx[i] + bw / 2, gy, gx[i + 1] - bw / 2, gy)

    # ── Evaluation row (y=1.3) ──────────────────────────────────────────
    # 4 boxes, centered on 6.7
    ey = 1.3
    ew = [2.2, 2.4, 3.0, 2.6]  # widths
    egap = 0.9
    # Compute positions: total width = sum(ew) + 3*egap
    total_ew = sum(ew) + 3 * egap
    ex0 = 6.7 - total_ew / 2 + ew[0] / 2  # leftmost center
    ex = [ex0]
    for i in range(1, 4):
        ex.append(ex[i - 1] + ew[i - 1] / 2 + egap + ew[i] / 2)

    draw_box(ax, ex[0], ey, "Model", "12 LLMs tested", w=ew[0])
    draw_box(ax, ex[1], ey, "20 Trials", "Plan + Response\nunder same conditions", w=ew[1])
    draw_box(ax, ex[2], ey, "3 Metrics", "Jaccard / BERTScore / Alignment", w=ew[2])
    draw_box(ax, ex[3], ey, "Analysis", "Cross-Model Comparisons", w=ew[3])

    # Eval arrows
    for i in range(3):
        arrow(ax, ex[i] + ew[i] / 2, ey, ex[i + 1] - ew[i + 1] / 2, ey)

    # ── Orange arrow: Frozen Histories → Model Under Test ───────────────
    frozen_x, frozen_bottom = gx[4], gy - 0.5
    model_x, model_top = ex[0], ey + 0.5
    mid_y = 3.55  # midpoint between the two rows

    # Vertical down from frozen
    ax.plot([frozen_x, frozen_x], [frozen_bottom, mid_y],
            color=C_ACCENT, lw=2.5, zorder=2)
    # Horizontal left to model
    ax.plot([frozen_x, model_x], [mid_y, mid_y],
            color=C_ACCENT, lw=2.5, zorder=2)
    # Vertical down into model (with arrowhead)
    arrow(ax, model_x, mid_y, model_x, model_top, color=C_ACCENT, lw=2.5)

    # Label on the orange path
    ax.text(cx, 3.9, "Identical input per trial",
            ha="center", va="bottom", fontsize=10, color="#b7950b",
            fontweight="bold", zorder=4,
            bbox=dict(facecolor="#fff9c4", edgecolor="#b7950b",
                      boxstyle="round,pad=0.3", linewidth=1.2))

    fig.tight_layout()
    fig.savefig("thesis/figures/fig_3_1_pipeline.pdf", bbox_inches="tight")
    fig.savefig("thesis/figures/fig_3_1_pipeline.png", bbox_inches="tight", dpi=150)
    print("Saved thesis/figures/fig_3_1_pipeline")
    plt.close(fig)


if __name__ == "__main__":
    main()
