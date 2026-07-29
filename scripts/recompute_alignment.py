"""Recompute alignment_mean under the missing-data rule (no re-judging).

Rule (matches src/evaluation/metrics.py compute_alignment): trials whose
judgment is an error (judge timeout/failure) or skipped (empty plan or
response) are missing data, not zero alignment. alignment_mean averages
judged trials only; skipped/error entries become null in
alignment_per_trial. Adds alignment_n_judged / n_errors / n_skipped.

Idempotent: runs already in the new format are left unchanged.

Usage:
    python scripts/recompute_alignment.py [--runs-dir experiments/runs/batch_20260321_final] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def recompute_run(run_dir: Path, dry_run: bool = False) -> str | None:
    """Recompute one run's alignment fields. Returns a change note or None."""
    metrics_path = run_dir / "metrics.json"
    judgments_path = run_dir / "judgments.json"
    if not metrics_path.exists() or not judgments_path.exists():
        return None

    with open(metrics_path) as f:
        metrics = json.load(f)
    with open(judgments_path) as f:
        judgments = json.load(f)

    per_trial = metrics.get("alignment_per_trial")
    if per_trial is None or len(per_trial) != len(judgments):
        return None

    n_errors = sum(1 for j in judgments if "error" in j)
    n_skipped = sum(1 for j in judgments if j.get("skipped"))

    new_per_trial = [
        None if ("error" in j or j.get("skipped")) else s
        for s, j in zip(per_trial, judgments)
    ]
    judged = [s for s in new_per_trial if s is not None]
    new_mean = sum(judged) / len(judged) if judged else None

    # Only touch runs the rule actually affects (keeps the diff vs the
    # backup minimal); untouched runs simply have no error/skipped trials.
    old_mean = metrics.get("alignment_mean")
    if new_per_trial == per_trial and old_mean == new_mean:
        return None

    metrics["alignment_mean"] = new_mean
    metrics["alignment_per_trial"] = new_per_trial
    metrics["alignment_n_judged"] = len(judged)
    metrics["alignment_n_errors"] = n_errors
    metrics["alignment_n_skipped"] = n_skipped

    if not dry_run:
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)

    old_str = f"{old_mean:.4f}" if old_mean is not None else "None"
    new_str = f"{new_mean:.4f}" if new_mean is not None else "None"
    return (
        f"{run_dir.name}: alignment_mean {old_str} -> {new_str} "
        f"(judged {len(judged)}/{len(judgments)}, errors={n_errors}, skipped={n_skipped})"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Recompute alignment under the missing-data rule")
    parser.add_argument("--runs-dir", type=Path,
                        default=Path("experiments/runs/batch_20260321_final"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    changed = 0
    for run_dir in sorted(args.runs_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        note = recompute_run(run_dir, dry_run=args.dry_run)
        if note:
            print(("DRY RUN: " if args.dry_run else "") + note)
            changed += 1
    print(f"{changed} runs updated" + (" (dry run)" if args.dry_run else ""))


if __name__ == "__main__":
    main()
