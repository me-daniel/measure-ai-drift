"""Exploratory comparison: Nemotron 3 Mamba-Transformer hybrids vs the 13-model set.

Branch 24_Nemotron only, not part of the paper. Reads the canonical runs, the
pinned bridge runs and stats/data/nemotron_runs.csv, and prints markdown tables
for docs/nemotron_test.md.

Usage: uv run python stats/scripts/nemotron_compare.py [nemotron_runs.csv]
"""
import sys
from pathlib import Path

import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr

DATA = Path("stats/data")
CATS = ["sensory_modulation", "cognitive_reframe", "self_empowerment", "safety", "social_support", "confrontation"]
SWEEP = [0.0, 0.075, 0.15, 0.3, 0.6]
NEMO = ["nemotron3_nano", "nemotron3_super", "nemotron3_ultra"]
# Size-matched transformer peers (total parameters). "bridge:" = pinned re-collection.
PEERS = {
    "nemotron3_nano": ["qwen35_27b", "olmo3_32b", "mistral_small32", "bridge:qwen35_27b"],
    "nemotron3_super": ["mistral_small4", "qwen35_122b", "bridge:mistral_small4", "bridge:qwen35_122b"],
    "nemotron3_ultra": ["qwen35_397b", "mistral_large", "mistral_large4", "bridge:mistral_large"],
}

main = pd.read_csv(DATA / "experiment_runs.csv")
bridge = pd.read_csv(DATA / "bridge_runs.csv").assign(model=lambda d: "bridge:" + d.model)
nemo = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else DATA / "nemotron_runs.csv")
sweep = pd.concat([main, nemo[nemo.temperature.isin(SWEEP)]], ignore_index=True)
everything = pd.concat([sweep, bridge], ignore_index=True)


def profile(df: pd.DataFrame) -> pd.Series:
    counts = sorted((df[f"n_{c}"].sum() for c in CATS), reverse=True) if "n_safety" in df else None
    by_t = df.groupby("temperature").jaccard_all.mean()
    rho, p = spearmanr(df.temperature, df.jaccard_all) if df.jaccard_all.nunique() > 1 and df.temperature.nunique() > 1 else (float("nan"), float("nan"))
    t0 = df[df.temperature == 0.0]
    return pd.Series({
        "runs": len(df),
        "median_J": df.jaccard_all.median(),
        "mean_J": df.jaccard_all.mean(),
        "modal": df.modal_set_agreement.mean(),
        "single_set": (df.modal_set_agreement == 1.0).mean(),
        "single_set_T0": (t0.modal_set_agreement == 1.0).mean(),
        "bert": df.bertscore_f1.mean(),
        "bert_T0": t0.bertscore_f1.mean(),
        "bert_drop": t0.bertscore_f1.mean() - df[df.temperature == 0.6].bertscore_f1.mean(),
        "align": df.alignment_mean.mean(),
        "validity": df.validity_rate.mean(),
        "top2": (counts[0] + counts[1]) / sum(counts) if counts and sum(counts) else float("nan"),
        "rho_J_T": rho,
        "p_rho": p,
        "best_T": by_t.idxmax(),
    })


def fmt(df: pd.DataFrame) -> str:
    """Markdown table without the optional tabulate dependency."""
    df = df.reset_index()
    cell = lambda v: f"{v:.3f}" if isinstance(v, float) else str(v)
    lines = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(cell(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


prof = everything.groupby("model")[everything.columns.drop("model")].apply(profile).sort_values("modal", ascending=False)
prof["runs"] = prof.runs.astype(int)
prof["rank_modal"] = range(1, len(prof) + 1)
print("## Profile on the shared 5-point sweep (all models, bridge rows prefixed)\n")
print(fmt(prof))

print("\n## Nemotron vs size-matched peers (run-level Jaccard and BERTScore, Mann-Whitney, Holm over all comparisons)\n")
rows = []
for m, peers in PEERS.items():
    a = everything[everything.model == m]
    for peer in peers:
        b = everything[everything.model == peer]
        for col in ["jaccard_all", "bertscore_f1"]:
            p = mannwhitneyu(a[col], b[col], alternative="two-sided").pvalue
            rows.append({"nemotron": m, "peer": peer, "metric": col,
                         "nemotron_mean": a[col].mean(), "peer_mean": b[col].mean(), "p": p})
comp = pd.DataFrame(rows).sort_values("p").reset_index(drop=True)
k = len(comp)
comp["p_holm"] = [min(1.0, max((k - i) * p for i, p in enumerate(comp.p[: j + 1]))) for j in range(k)]
print(fmt(comp.sort_values(["nemotron", "metric", "peer"]).set_index(["nemotron", "metric", "peer"])))

print("\n## Mean Jaccard / BERTScore by temperature, Nemotron incl. vendor default T=1.0\n")
for col in ["jaccard_all", "bertscore_f1", "modal_set_agreement"]:
    print(f"\n{col}\n")
    print(fmt(nemo.pivot_table(index="model", columns="temperature", values=col, aggfunc="mean")))

print("\n## Nemotron by vignette (median Jaccard, sweep only)\n")
print(fmt(sweep[sweep.model.isin(NEMO)].pivot_table(index="model", columns="vignette", values="jaccard_all", aggfunc="median")))

print("\n## Strategy shares, Nemotron (all temperatures)\n")
shares = nemo.groupby("model")[[f"n_{c}" for c in CATS]].sum()
print(fmt(shares.div(shares.sum(axis=1), axis=0)))

print("\n## Judge accounting, Nemotron\n")
print(fmt(nemo.groupby("model")[["n_trials", "alignment_n_judged", "alignment_n_errors", "alignment_n_skipped", "alignment_pro_fallback"]].sum()))
