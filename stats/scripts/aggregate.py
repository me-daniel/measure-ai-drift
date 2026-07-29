"""Step 0: Aggregate experiment runs into a single CSV.

Reads evaluation targets from models.yaml to determine which runs are valid.
Filters by tier: "test" (_test suffix models), "experiment" (no suffix), or "all".

Usage:
    python stats/scripts/aggregate.py --tier test       # smoke test runs only
    python stats/scripts/aggregate.py --tier experiment  # full experiment runs only
    python stats/scripts/aggregate.py --tier all         # both (separate columns)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml

MODELS_YAML = Path("src/config/models.yaml")
TAXONOMY_YAML = Path("data/prompts/evaluation/strategy_taxonomy.yaml")


def load_strategy_categories(taxonomy_path: Path = TAXONOMY_YAML) -> list[str]:
    """Category IDs from the strategy taxonomy (single source of truth)."""
    with open(taxonomy_path) as f:
        taxonomy = yaml.safe_load(f)
    return [s["id"] for s in taxonomy.get("strategies", [])]


STRATEGY_CATEGORIES = load_strategy_categories()


def load_evaluation_targets(config_path: Path = MODELS_YAML) -> dict[str, set[str]]:
    """Read models.yaml and return test/experiment target name sets."""
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    test_models = set()
    experiment_models = set()

    for target in cfg.get("evaluation_targets", []):
        name = target["name"]
        if name.endswith("_test"):
            test_models.add(name)
        else:
            experiment_models.add(name)

    return {"test": test_models, "experiment": experiment_models}


def load_run(run_dir: Path) -> dict | None:
    """Load a single experiment run into a flat dict. Returns None on failure."""
    config_path = run_dir / "config.yaml"
    metrics_path = run_dir / "metrics.json"

    if not config_path.exists() or not metrics_path.exists():
        return None

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        with open(metrics_path) as f:
            metrics = json.load(f)
    except Exception:
        return None

    row = {
        "run_id": run_dir.name,
        "run_date": run_dir.name[:8],  # runs are named {YYYYMMDD}_{HHMMSS}_{model}_{vignette}
        "model": config.get("model", "unknown"),
        "vignette": config.get("vignette", "unknown"),
        "temperature": config.get("temperature", metrics.get("temperature", 0.0)),
        "slice": config.get("slice"),
        "n_trials": metrics.get("n_trials", 0),
        "mode": config.get("mode", "fused"),
        # Stability metrics
        "validity_rate": metrics.get("validity_rate"),
        "jaccard_all": metrics.get("jaccard_all"),
        "jaccard_valid": metrics.get("jaccard_valid_only"),
        "modal_set_agreement": metrics.get("modal_set_agreement"),
        "bertscore_f1": metrics.get("bertscore_f1"),
        "bertscore_precision": metrics.get("bertscore_precision"),
        "bertscore_recall": metrics.get("bertscore_recall"),
        "alignment_mean": metrics.get("alignment_mean"),
        # Judge accounting (absent in runs predating the missing-data rule)
        "alignment_n_judged": metrics.get("alignment_n_judged"),
        "alignment_n_errors": metrics.get("alignment_n_errors"),
        "alignment_n_skipped": metrics.get("alignment_n_skipped"),
        "alignment_pro_fallback": metrics.get("alignment_pro_fallback"),
    }

    # Expand strategy counts into separate columns
    counts = metrics.get("strategy_counts", {})
    for cat in STRATEGY_CATEGORIES:
        row[f"n_{cat}"] = counts.get(cat, 0)

    # Expand per-strategy alignment
    alignment_per = metrics.get("alignment_per_strategy", {})
    for cat in STRATEGY_CATEGORIES:
        row[f"align_{cat}"] = alignment_per.get(cat)

    return row


def aggregate(runs_dirs: Path | list[Path], tier: str = "experiment") -> pd.DataFrame:
    """Scan run directories and return a DataFrame filtered by tier.

    Args:
        runs_dirs: One or more directories containing experiment run folders
            (multiple batches are merged into one DataFrame).
        tier: "test", "experiment", or "all".
    """
    if isinstance(runs_dirs, Path):
        runs_dirs = [runs_dirs]

    targets = load_evaluation_targets()
    if tier == "test":
        allowed = targets["test"]
    elif tier == "experiment":
        allowed = targets["experiment"]
    else:
        allowed = targets["test"] | targets["experiment"]

    rows = []
    skipped = []
    for runs_dir in runs_dirs:
        for run_path in sorted(runs_dir.iterdir()):
            if not run_path.is_dir():
                continue
            row = load_run(run_path)
            if row is None:
                continue
            if row["model"] in allowed:
                row["tier"] = "test" if row["model"] in targets["test"] else "experiment"
                rows.append(row)
            else:
                skipped.append(row["model"])

    if skipped:
        skipped_unique = sorted(set(skipped))
        print(f"Skipped {len(skipped)} runs from non-target models: {skipped_unique}")

    if not rows:
        print(f"No valid {tier} runs found in {[str(d) for d in runs_dirs]}")
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.sort_values(["model", "vignette", "temperature"]).reset_index(drop=True)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate experiment runs into CSV")
    parser.add_argument(
        "--runs-dir",
        type=Path,
        nargs="+",
        default=[Path("experiments/latest")],
        help="One or more batch directories to aggregate (merged into one CSV)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--tier",
        choices=["test", "experiment", "all"],
        default="experiment",
        help="Which runs to include: test (_test models), experiment, or all",
    )
    args = parser.parse_args()

    if args.output is None:
        args.output = Path(f"stats/data/{args.tier}_runs.csv")

    df = aggregate(args.runs_dir, tier=args.tier)
    if df.empty:
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)

    print(f"Aggregated {len(df)} {args.tier} runs -> {args.output}")
    print(f"Models: {sorted(df['model'].unique())}")
    print(f"Vignettes: {sorted(df['vignette'].unique())}")
    print(f"Temperatures: {sorted(df['temperature'].unique())}")
    if df["slice"].notna().any():
        print(f"Slices: {sorted(df['slice'].dropna().unique())}")


if __name__ == "__main__":
    main()
