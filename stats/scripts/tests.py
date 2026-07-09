"""Statistical tests (exploratory, bachelor's thesis scope).

Tests:
- Temperature effect: Spearman correlation + Kruskal-Wallis (pooled and per-model)
- Model differences: Kruskal-Wallis H (across models)
- Vignette effect: Kruskal-Wallis H (across vignettes)
- Correlation: Spearman between Jaccard, BERTScore, and Alignment
- Alignment: Kruskal-Wallis across models

Usage:
    python stats/scripts/tests.py [--tier experiment]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sp


def temperature_effect(df: pd.DataFrame, metric: str = "jaccard_all") -> dict:
    """Temperature effect: Spearman correlation + Kruskal-Wallis.

    Scale: [0.0, 0.075, 0.15, 0.3, 0.6]. Tests whether stability degrades
    monotonically with temperature.
    """
    valid = df[["temperature", metric]].dropna()
    temps = sorted(valid["temperature"].unique())

    result: dict = {
        "test": "temperature_effect",
        "metric": metric,
        "n_temperatures": len(temps),
        "temperatures": [float(t) for t in temps],
    }

    # Spearman: monotonic trend of metric with temperature
    if len(valid) >= 5:
        rho, p = sp.spearmanr(valid["temperature"], valid[metric])
        result["spearman_rho"] = float(rho)
        result["spearman_p"] = float(p)
        result["p_value"] = float(p)  # for summary printer
        result["statistic"] = f"rho={rho:.3f}"

    # Kruskal-Wallis: differences across temperature groups
    groups = [g[metric].values for _, g in valid.groupby("temperature")]
    groups = [g for g in groups if len(g) > 0]
    if len(groups) >= 3:
        stat, p = sp.kruskal(*groups)
        n_total = sum(len(g) for g in groups)
        result["kruskal_H"] = float(stat)
        result["kruskal_p"] = float(p)
        result["kruskal_eta_sq"] = float(stat) / (n_total - 1)

    # Per-temperature medians
    result["medians_by_temp"] = {
        str(t): float(valid[valid["temperature"] == t][metric].median())
        for t in temps
    }

    return result


def temperature_effect_per_model(df: pd.DataFrame, metric: str = "jaccard_all") -> dict:
    """Per-model Spearman correlation of metric vs temperature."""
    models = sorted(df["model"].unique())
    per_model = {}

    for model in models:
        mdf = df[df["model"] == model][["temperature", metric]].dropna()
        if len(mdf) >= 4:
            rho, p = sp.spearmanr(mdf["temperature"], mdf[metric])
            per_model[model] = {
                "rho": float(rho),
                "p_value": float(p),
                "n": len(mdf),
                "significant": bool(p < 0.05),
            }

    return {
        "test": "temperature_effect_per_model",
        "metric": metric,
        "per_model": per_model,
    }


def model_differences(df: pd.DataFrame, metric: str = "jaccard_all") -> dict:
    """Kruskal-Wallis H test across models."""
    groups = [group[metric].dropna().values for _, group in df.groupby("model")]
    groups = [g for g in groups if len(g) > 0]

    if len(groups) < 3:
        return {"test": "kruskal_wallis", "metric": metric, "note": "fewer than 3 groups"}

    stat, p = sp.kruskal(*groups)
    n_total = sum(len(g) for g in groups)
    eta_sq = float(stat) / (n_total - 1)

    result = {
        "test": "kruskal_wallis",
        "metric": metric,
        "n_groups": len(groups),
        "n_total": n_total,
        "H_statistic": float(stat),
        "p_value": float(p),
        "eta_squared": eta_sq,
    }

    # Pairwise Mann-Whitney U with Bonferroni if significant
    if p < 0.05:
        models = sorted(df["model"].unique())
        pairwise = []
        n_comparisons = len(models) * (len(models) - 1) // 2
        for i, m1 in enumerate(models):
            for m2 in models[i + 1:]:
                g1 = df[df["model"] == m1][metric].dropna().values
                g2 = df[df["model"] == m2][metric].dropna().values
                if len(g1) > 0 and len(g2) > 0:
                    u_stat, u_p = sp.mannwhitneyu(g1, g2, alternative="two-sided")
                    pairwise.append({
                        "pair": f"{m1} vs {m2}",
                        "U_statistic": float(u_stat),
                        "p_value": float(u_p),
                        "p_bonferroni": float(min(u_p * n_comparisons, 1.0)),
                    })
        result["pairwise"] = pairwise

    return result


def vignette_effect(df: pd.DataFrame, metric: str = "jaccard_all") -> dict:
    """Kruskal-Wallis H test across vignettes."""
    groups = [group[metric].dropna().values for _, group in df.groupby("vignette")]
    groups = [g for g in groups if len(g) > 0]

    if len(groups) < 3:
        return {"test": "kruskal_wallis", "metric": metric, "grouping": "vignette", "note": "fewer than 3 groups"}

    stat, p = sp.kruskal(*groups)
    n_total = sum(len(g) for g in groups)
    eta_sq = float(stat) / (n_total - 1)

    return {
        "test": "kruskal_wallis",
        "metric": metric,
        "grouping": "vignette",
        "n_groups": len(groups),
        "n_total": n_total,
        "H_statistic": float(stat),
        "p_value": float(p),
        "eta_squared": eta_sq,
    }


def metric_correlation(df: pd.DataFrame) -> dict:
    """Spearman correlations between all metric pairs."""
    metrics = ["jaccard_all", "bertscore_f1", "alignment_mean"]
    available = [m for m in metrics if m in df.columns]

    correlations = {}
    for i, m1 in enumerate(available):
        for m2 in available[i + 1:]:
            valid = df[[m1, m2]].dropna()
            if len(valid) >= 5:
                rho, p = sp.spearmanr(valid[m1], valid[m2])
                correlations[f"{m1}_vs_{m2}"] = {
                    "rho": float(rho),
                    "p_value": float(p),
                    "n": len(valid),
                }

    return {
        "test": "spearman_correlations",
        "pairs": correlations,
    }


def run_all_tests(df: pd.DataFrame) -> dict:
    """Run all statistical tests and return results."""
    results = {
        "temperature_effect_jaccard": temperature_effect(df, "jaccard_all"),
        "temperature_effect_bertscore": temperature_effect(df, "bertscore_f1"),
        "temperature_per_model_jaccard": temperature_effect_per_model(df, "jaccard_all"),
        "model_differences_jaccard": model_differences(df, "jaccard_all"),
        "model_differences_bertscore": model_differences(df, "bertscore_f1"),
        "vignette_effect_jaccard": vignette_effect(df, "jaccard_all"),
        "vignette_effect_bertscore": vignette_effect(df, "bertscore_f1"),
        "correlations": metric_correlation(df),
        "note": "All tests are exploratory given sample sizes. Effect sizes reported alongside p-values.",
    }

    # Alignment tests if available
    if "alignment_mean" in df.columns:
        results["model_differences_alignment"] = model_differences(df, "alignment_mean")
        results["temperature_effect_alignment"] = temperature_effect(df, "alignment_mean")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run statistical tests")
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--tier", choices=["test", "experiment"], default="experiment")
    args = parser.parse_args()

    if args.input is None:
        args.input = Path(f"stats/data/{args.tier}_runs.csv")
    if args.output is None:
        args.output = Path(f"stats/data/{args.tier}_test_results.json")

    df = pd.read_csv(args.input)
    results = run_all_tests(df)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print(f"Test results -> {args.output}")
    for key, val in results.items():
        if key == "note":
            continue

        # Standard test with p_value
        p = val.get("p_value")
        if p is not None:
            sig = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else ""))
            extra = f" {val['statistic']}" if "statistic" in val else ""
            print(f"  {key:45s} p={p:.6f}{sig}{extra}")
            continue

        # Per-model temperature trends
        if "per_model" in val:
            print(f"  {key}:")
            for model, data in sorted(val["per_model"].items()):
                sig = "*" if data["significant"] else ""
                print(f"    {model:20s} rho={data['rho']:+.3f} p={data['p_value']:.4f}{sig}")
            continue

        # Correlations
        if "pairs" in val:
            print(f"  {key}:")
            for pair, data in val["pairs"].items():
                sig = "***" if data["p_value"] < 0.001 else ""
                print(f"    {pair:40s} rho={data['rho']:.3f} p={data['p_value']:.6f}{sig}")
            continue

        print(f"  {key:45s} {val.get('note', 'n/a')}")


if __name__ == "__main__":
    main()
