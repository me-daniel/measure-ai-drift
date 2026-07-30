"""Per-pair Jaccard vs per-pair BERTScore F1 across the main experiment.

Quantifies how sensitive BERTScore is to strategy switches. For every run in
stats/data/experiment_runs.csv the script forms all trial pairs, computes the
Jaccard similarity of the two stored strategy sets and the BERTScore F1 of the
two responses, then buckets pairs by their exact Jaccard value (0, 1/3, 1/2,
2/3, 1, other) and reports mean/SD F1 per bucket overall, per model and per
temperature.

Results are cached per run so the job can be resumed. A full pass over all 360
runs (190 pairs each) takes roughly an hour on Apple silicon.

Usage:
    python stats/scripts/pairwise_jaccard_bertscore.py                # full run
    python stats/scripts/pairwise_jaccard_bertscore.py --limit 2      # smoke test
    python stats/scripts/pairwise_jaccard_bertscore.py --force        # ignore cache
    python stats/scripts/pairwise_jaccard_bertscore.py --batch-size 64
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from itertools import combinations
from pathlib import Path

# Tokenizer forking warnings pollute the progress output.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import numpy as np
import pandas as pd

# Ensure project root is on path (same pattern as scripts/run_experiment.py)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

DEFAULT_CSV = Path("stats/data/experiment_runs.csv")
CACHE_DIR = Path("stats/data/cache/pairwise_bertscore")
OUTPUT_JSON = Path("stats/data/pairwise_jaccard_bertscore.json")

BATCH_DIRS = [
    Path("experiments/latest"),  # symlink to batch_20260321_final
    Path("experiments/runs/batch_20260709_mistral_medium35"),
    Path("experiments/runs/batch_20260728_command_a"),
    Path("experiments/runs/batch_20260728_gpt54_native"),
]

MODEL_TYPE = "microsoft/deberta-xlarge-mnli"

# Exact Jaccard values that discrete 1-2 strategy plans can produce.
BUCKET_VALUES = [
    ("0", 0.0),
    ("1/3", 1.0 / 3.0),
    ("1/2", 0.5),
    ("2/3", 2.0 / 3.0),
    ("1", 1.0),
]
BUCKET_KEYS = [k for k, _ in BUCKET_VALUES] + ["other"]
BUCKET_TOL = 1e-9

SANITY_TOL = 5e-3


def bucket_for(jaccard: float) -> str:
    """Map an exact Jaccard value to a bucket key.

    Plans with more than two strategies can yield values such as 0.25 or 0.4,
    which fall into "other".
    """
    for key, value in BUCKET_VALUES:
        if abs(jaccard - value) <= BUCKET_TOL:
            return key
    return "other"


def resolve_run_dir(run_id: str) -> Path:
    """Find the batch directory that holds a run. Raises if unresolvable."""
    for base in BATCH_DIRS:
        candidate = base / run_id
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(
        f"run_id {run_id!r} not found in any of: {[str(b) for b in BATCH_DIRS]}"
    )


def load_trials(run_dir: Path) -> tuple[list[set[str]], list[str]]:
    """Load stored strategy sets and responses, ordered by trial number."""
    trial_paths = sorted((run_dir / "trials").glob("trial_*.json"))
    if not trial_paths:
        raise FileNotFoundError(f"no trial files in {run_dir}")

    strategy_sets: list[set[str]] = []
    responses: list[str] = []
    for path in trial_paths:
        with open(path) as f:
            trial = json.load(f)
        strategy_sets.append(set(trial.get("strategies") or []))
        responses.append(trial.get("response") or "")

    return strategy_sets, responses


def jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard similarity with the semantics of metrics.compute_pairwise_jaccard."""
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def get_scorer(batch_size: int) -> tuple:
    """Build a BERTScorer mirroring src/evaluation/metrics.py, on MPS if available."""
    import warnings

    import torch
    from bert_score import BERTScorer

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*UNEXPECTED.*")
        warnings.filterwarnings("ignore", category=FutureWarning)
        scorer = BERTScorer(
            model_type=MODEL_TYPE,
            lang="en",
            device=device,
            batch_size=batch_size,
        )
    # Match the truncation behaviour of the collection pipeline.
    scorer._tokenizer.model_max_length = 512
    return scorer, device


def score_run(scorer, strategy_sets: list[set[str]], responses: list[str]) -> list[dict]:
    """Compute per-pair Jaccard and BERTScore F1 for one run.

    Pairs where either response is empty get f1=None. The collection pipeline
    dropped empty responses before pairing, so excluding those pairs from the
    aggregates reproduces its effective behaviour.
    """
    n = len(strategy_sets)
    pairs = list(combinations(range(n), 2))

    scored_idx: list[int] = []
    cands: list[str] = []
    refs: list[str] = []
    for k, (i, j) in enumerate(pairs):
        a, b = responses[i], responses[j]
        if not a or not a.strip() or not b or not b.strip():
            continue
        scored_idx.append(k)
        # metrics.compute_pairwise_bertscore uses refs=first, cands=second.
        refs.append(a)
        cands.append(b)

    f1_by_k: dict[int, float] = {}
    if cands:
        _, _, F1 = scorer.score(cands, refs)
        for k, value in zip(scored_idx, F1.tolist()):
            f1_by_k[k] = float(value)

    return [
        {
            "i": i,
            "j": j,
            "jaccard": jaccard(strategy_sets[i], strategy_sets[j]),
            "f1": f1_by_k.get(k),
        }
        for k, (i, j) in enumerate(pairs)
    ]


def stored_bertscore_f1(run_dir: Path) -> float | None:
    """Read bertscore_f1 from the run's metrics.json."""
    path = run_dir / "metrics.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f).get("bertscore_f1")


def summarise(pairs: list[dict]) -> dict[str, dict]:
    """Bucket pairs by exact Jaccard and summarise F1 within each bucket."""
    by_bucket: dict[str, list[float]] = {k: [] for k in BUCKET_KEYS}
    counts: dict[str, int] = {k: 0 for k in BUCKET_KEYS}

    for pair in pairs:
        key = bucket_for(pair["jaccard"])
        counts[key] += 1
        if pair["f1"] is not None:
            by_bucket[key].append(pair["f1"])

    out: dict[str, dict] = {}
    for key in BUCKET_KEYS:
        values = np.array(by_bucket[key], dtype=float)
        out[key] = {
            "n_pairs": counts[key],
            "n_scored": int(values.size),
            "mean_f1": float(values.mean()) if values.size else None,
            "sd_f1": float(values.std(ddof=1)) if values.size > 1 else None,
        }
    return out


def process(args: argparse.Namespace) -> None:
    df = pd.read_csv(args.csv)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    runs = []
    for row in df.itertuples(index=False):
        run_dir = resolve_run_dir(row.run_id)  # raises if unresolvable
        runs.append((row.run_id, run_dir, row.model, row.vignette, float(row.temperature)))

    pending = [
        r for r in runs
        if args.force or not (CACHE_DIR / f"{r[0]}.json").exists()
    ]
    if args.limit is not None:
        pending = pending[: args.limit]

    print(f"{len(runs)} runs resolved, {len(pending)} to compute")

    if pending:
        scorer, device = get_scorer(args.batch_size)
        print(f"BERTScorer ready: {MODEL_TYPE} on {device} (batch_size={args.batch_size})")

        for n, (run_id, run_dir, model, vignette, temperature) in enumerate(pending, 1):
            start = time.time()
            strategy_sets, responses = load_trials(run_dir)
            pairs = score_run(scorer, strategy_sets, responses)

            record = {
                "run_id": run_id,
                "model": model,
                "vignette": vignette,
                "temperature": temperature,
                "pairs": pairs,
            }
            with open(CACHE_DIR / f"{run_id}.json", "w") as f:
                json.dump(record, f)

            # MPS caching allocator grows across runs and eventually OOMs
            if device == "mps":
                import torch
                torch.mps.empty_cache()

            scored = [p["f1"] for p in pairs if p["f1"] is not None]
            mean_f1 = float(np.mean(scored)) if scored else float("nan")
            stored = stored_bertscore_f1(run_dir)
            dev = abs(mean_f1 - stored) if stored is not None and scored else float("nan")
            flag = ""
            if dev == dev and dev > SANITY_TOL:
                flag = "  WARNING: exceeds sanity tolerance"
                print(f"  WARNING {run_id}: mean pair F1 {mean_f1:.6f} vs stored {stored:.6f} (diff {dev:.2e})")

            elapsed = time.time() - start
            print(
                f"[{n}/{len(pending)}] {run_id} "
                f"pairs={len(pairs)} scored={len(scored)} "
                f"mean_f1={mean_f1:.4f} dev={dev:.2e} {elapsed:.1f}s{flag}"
            )

    aggregate(args)


def aggregate(args: argparse.Namespace) -> None:
    """Combine cached per-run pairs into the final artifact."""
    df = pd.read_csv(args.csv)

    all_pairs: list[dict] = []
    by_model: dict[str, list[dict]] = {}
    by_temp: dict[str, list[dict]] = {}
    max_dev = 0.0
    max_dev_run = None
    n_warned = 0
    n_runs = 0

    for row in df.itertuples(index=False):
        cache_path = CACHE_DIR / f"{row.run_id}.json"
        if not cache_path.exists():
            continue
        with open(cache_path) as f:
            record = json.load(f)

        n_runs += 1
        pairs = record["pairs"]
        all_pairs.extend(pairs)
        by_model.setdefault(record["model"], []).extend(pairs)
        by_temp.setdefault(f"{float(record['temperature']):g}", []).extend(pairs)

        scored = [p["f1"] for p in pairs if p["f1"] is not None]
        stored = stored_bertscore_f1(resolve_run_dir(row.run_id))
        if scored and stored is not None:
            dev = abs(float(np.mean(scored)) - stored)
            if dev > max_dev:
                max_dev, max_dev_run = dev, row.run_id
            if dev > SANITY_TOL:
                n_warned += 1

    if not n_runs:
        print("No cached runs found; nothing to aggregate.")
        return

    result = {
        "metadata": {
            "model_type": MODEL_TYPE,
            "device": "mps" if _mps_available() else "cpu",
            "batch_size": args.batch_size,
            "n_runs": n_runs,
            "n_runs_expected": len(df),
            "n_pairs_total": len(all_pairs),
            "n_pairs_scored": sum(1 for p in all_pairs if p["f1"] is not None),
            "generated": datetime.now().isoformat(timespec="seconds"),
        },
        "sanity_check": {
            "tolerance": SANITY_TOL,
            "max_abs_deviation": max_dev,
            "max_abs_deviation_run": max_dev_run,
            "n_runs_over_tolerance": n_warned,
        },
        "overall": summarise(all_pairs),
        "by_model": {m: summarise(p) for m, p in sorted(by_model.items())},
        "by_temperature": {
            t: summarise(p) for t, p in sorted(by_temp.items(), key=lambda kv: float(kv[0]))
        },
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nAggregated {n_runs}/{len(df)} runs ({len(all_pairs)} pairs) -> {OUTPUT_JSON}")
    print(f"Max sanity deviation: {max_dev:.2e} ({max_dev_run})")
    print("\nOverall bucket means:")
    for key in BUCKET_KEYS:
        stats = result["overall"][key]
        if not stats["n_pairs"]:
            continue
        mean = stats["mean_f1"]
        sd = stats["sd_f1"]
        print(
            f"  Jaccard {key:>5}: n={stats['n_pairs']:>6}  "
            f"mean F1={mean:.4f}" + (f"  SD={sd:.4f}" if sd is not None else "")
        )


def _mps_available() -> bool:
    try:
        import torch

        return bool(torch.backends.mps.is_available())
    except Exception:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Per-pair Jaccard vs per-pair BERTScore F1 over the main experiment"
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="experiment runs CSV")
    parser.add_argument("--batch-size", type=int, default=32, help="BERTScore batch size")
    parser.add_argument("--limit", type=int, default=None, help="process only the first N uncached runs")
    parser.add_argument("--force", action="store_true", help="recompute runs that already have a cache")
    args = parser.parse_args()

    process(args)


if __name__ == "__main__":
    main()
