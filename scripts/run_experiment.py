"""Run the full experiment: all evaluation targets x all vignettes x temperature scale.

Temperatures run SEQUENTIALLY for each model x vignette combination.
Judge calls use a semaphore to stay within Gemini rate limits (25 RPM).
Optionally includes a therapy_temp run per model (vendor-recommended clinical temperature).

Usage:
    python scripts/run_experiment.py [--trials 20] [--slice 2]
    python scripts/run_experiment.py --temps 0.0 0.5 1.0   # custom subset
    python scripts/run_experiment.py --no-therapy-temp      # skip therapy_temp runs
    python scripts/run_experiment.py --no-judge             # skip the LLM judge (no alignment)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from src.core import Conversation
from src.evaluation import ExperimentRun
from src.llm.provider import load_config, create_provider


FROZEN_HISTORIES = Path("data/synthetic/frozen_histories")
VIGNETTES = ["anxious", "avoidant", "cooperative", "resistant", "skeptic", "trauma"]
DEFAULT_TEMPS = [0.0, 0.075, 0.15, 0.3, 0.6]  # production scale, matches src/config/experiment.yaml


def load_therapy_temps(config: dict) -> dict[str, float]:
    """Load therapy_temp values from models.yaml evaluation_targets."""
    temps = {}
    for t in config.get("evaluation_targets", []):
        if "therapy_temp" in t:
            temps[t["name"]] = t["therapy_temp"]
    return temps


def find_slice_path(vignette: str, slice_num: int) -> Path | None:
    """Find the slice file for a vignette."""
    for d in FROZEN_HISTORIES.iterdir():
        if d.is_dir() and f"frozen_{vignette}_" in d.name:
            path = d / f"slice_{slice_num}.json"
            if path.exists():
                return path
    return None


async def run_single(
    model_name: str,
    vignette: str,
    history_path: Path,
    n_trials: int,
    temperature: float,
    batch_dir: Path | None = None,
    judge: bool = True,
) -> dict:
    """Run one experiment (model x vignette x temperature) and return summary."""
    with open(history_path) as f:
        history_data = json.load(f)

    frozen_history = Conversation.from_dict(history_data)
    provider = create_provider(model_name)

    kwargs = {}
    if batch_dir:
        kwargs["base_dir"] = batch_dir

    experiment = ExperimentRun(
        frozen_history=frozen_history,
        model_name=model_name,
        vignette_name=vignette,
        **kwargs,
    ).setup()

    start = time.time()
    await experiment.run(
        n_trials=n_trials,
        temperature=temperature,
        language="en",
        mode="fused",
        therapist_provider=provider,
        judge=judge,
    )
    elapsed = time.time() - start

    # Read back metrics
    with open(experiment.path / "metrics.json") as f:
        metrics = json.load(f)

    return {
        "model": model_name,
        "vignette": vignette,
        "temperature": temperature,
        "jaccard": metrics["jaccard_all"],
        "bertscore": metrics["bertscore_f1"],
        "alignment": metrics.get("alignment_mean"),
        "path": str(experiment.path),
        "elapsed": round(elapsed, 1),
    }


def format_time(seconds: float) -> str:
    """Format seconds as h:mm:ss or m:ss."""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def print_result(r: dict) -> None:
    """Print a single run result."""
    if "error" in r:
        print(f"    T={r['temperature']}: FAILED: {r['error']}")
    else:
        align = r.get("alignment")
        align_str = f"{align:.3f}" if align is not None else "--"
        print(
            f"    T={r['temperature']}: "
            f"J={r['jaccard']:.3f} B={r['bertscore']:.3f} "
            f"A={align_str} ({r['elapsed']}s)"
        )


def print_progress(done: int, total: int, elapsed: float, failed: int) -> None:
    """Print a progress bar and ETA."""
    pct = done / total * 100 if total > 0 else 0
    bar_len = 30
    filled = int(bar_len * done / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_len - filled)

    if done > 0:
        eta = elapsed / done * (total - done)
        eta_str = format_time(eta)
    else:
        eta_str = "??:??"

    fail_str = f" ({failed} failed)" if failed > 0 else ""
    print(
        f"\n  [{bar}] {done}/{total} runs ({pct:.0f}%) "
        f"elapsed {format_time(elapsed)} ETA {eta_str}{fail_str}\n",
        flush=True,
    )


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run full experiment")
    parser.add_argument("--trials", "-n", type=int, default=20)
    parser.add_argument("--temps", type=float, nargs="+", default=DEFAULT_TEMPS,
                        help="Temperature scale (default: 0.0 0.075 0.15 0.3 0.6)")
    parser.add_argument("--slice", "-s", type=int, default=2)
    parser.add_argument("--no-therapy-temp", action="store_true",
                        help="Skip the extra therapy_temp run per model")
    parser.add_argument("--no-judge", action="store_true",
                        help="Skip the LLM judge: no alignment scores, no Google API key needed")
    parser.add_argument("--models", type=str, nargs="+", default=None,
                        help="Run only these models (by name). Default: all non-test targets")
    parser.add_argument("--add", action="store_true",
                        help="Add runs to the current latest batch instead of creating a new one")
    parser.add_argument("--batch-dir", type=Path, default=None,
                        help="Write runs into a specific batch directory")
    args = parser.parse_args()

    temps = sorted(args.temps)

    config = load_config()
    all_targets = [
        t["name"]
        for t in config.get("evaluation_targets", [])
        if not t["name"].endswith("_test")
    ]

    # Filter to specific models if requested
    if args.models:
        targets = [m for m in args.models if m in all_targets]
        missing = set(args.models) - set(all_targets)
        if missing:
            print(f"WARNING: models not found in config: {missing}")
        if not targets:
            print("No valid models to run.")
            return
    else:
        targets = all_targets

    therapy_temps = load_therapy_temps(config)

    # Determine which therapy_temps actually add a new data point
    extra_therapy = {}
    if not args.no_therapy_temp:
        for model in targets:
            tt = therapy_temps.get(model)
            if tt is not None and tt not in temps:
                extra_therapy[model] = tt

    # Count total runs
    total_runs = 0
    for model in targets:
        model_temps = list(temps)
        if model in extra_therapy:
            model_temps = sorted(set(model_temps + [extra_therapy[model]]))
        total_runs += len(VIGNETTES) * len(model_temps)

    # Batch directory: --add (append to latest), --batch-dir (explicit), or new
    from datetime import datetime
    latest_link = Path("experiments/latest")

    if args.batch_dir:
        batch_dir = args.batch_dir
        if not batch_dir.exists():
            print(f"Batch dir {batch_dir} does not exist")
            return
    elif args.add:
        if not latest_link.exists():
            print("No latest batch to add to. Run without --add first.")
            return
        batch_dir = latest_link.resolve()
        existing = len(list(batch_dir.iterdir()))
        print(f"  Adding to existing batch ({existing} runs already)")
    else:
        batch_name = datetime.now().strftime("batch_%Y%m%d_%H%M%S")
        batch_dir = Path("experiments/runs") / batch_name
        batch_dir.mkdir(parents=True, exist_ok=True)
        latest_link.unlink(missing_ok=True)
        latest_link.symlink_to(batch_dir.resolve())

    print(f"Experiment: {len(targets)} models x {len(VIGNETTES)} vignettes x {len(temps)} temps x slice_{args.slice}")
    print(f"  Batch: {batch_dir}")
    print(f"  Models: {targets}")
    print(f"  Scale temps: {temps} (sequential per model x vignette)")
    if extra_therapy:
        print(f"  Extra therapy_temp runs: {extra_therapy}")
    print(f"  Trials per run: {args.trials}")
    if args.no_judge:
        print("  Judge: disabled (alignment not scored)")
    print(f"  Total runs: {total_runs} ({total_runs * args.trials} trials)")
    print()

    results = []
    done_runs = 0
    failed_runs = 0
    experiment_start = time.time()

    for model_idx, model in enumerate(targets):
        model_temps = list(temps)
        has_extra = model in extra_therapy
        if has_extra:
            model_temps = sorted(set(model_temps + [extra_therapy[model]]))

        print(f"=== [{model_idx+1}/{len(targets)}] {model} ({len(model_temps)} temps x {len(VIGNETTES)} vignettes) ===")

        for vignette in VIGNETTES:
            history_path = find_slice_path(vignette, args.slice)
            if history_path is None:
                print(f"  SKIP {model} x {vignette}: no slice_{args.slice} found")
                for _ in model_temps:
                    done_runs += 1
                continue

            extra_label = f" +rec {extra_therapy[model]}" if has_extra else ""
            print(f"  {model} x {vignette}{extra_label}:", flush=True)

            # Run each temperature sequentially
            for temp in model_temps:
                try:
                    result = await run_single(
                        model, vignette, history_path, args.trials, temp, batch_dir,
                        judge=not args.no_judge,
                    )
                    results.append(result)
                    print_result(result)
                except Exception as e:
                    err_result = {"model": model, "vignette": vignette, "temperature": temp, "error": str(e)}
                    results.append(err_result)
                    print_result(err_result)
                    failed_runs += 1

                done_runs += 1

            # Progress update after each vignette
            if done_runs % (len(model_temps) * 2) == 0 or done_runs == total_runs:
                print_progress(done_runs, total_runs, time.time() - experiment_start, failed_runs)

    # Final summary
    total_elapsed = time.time() - experiment_start
    successful = [r for r in results if "jaccard" in r]
    print(f"\nCompleted {len(successful)}/{total_runs} runs in {format_time(total_elapsed)}")
    if failed_runs:
        print(f"  {failed_runs} runs failed")
    if successful:
        avg_j = sum(r["jaccard"] for r in successful) / len(successful)
        avg_b = sum(r["bertscore"] for r in successful) / len(successful)
        print(f"Mean Jaccard: {avg_j:.3f}, Mean BERTScore: {avg_b:.3f}")

        # Per-temperature summary
        all_temps_seen = sorted(set(r["temperature"] for r in successful))
        for temp in all_temps_seen:
            temp_runs = [r for r in successful if r["temperature"] == temp]
            t_j = sum(r["jaccard"] for r in temp_runs) / len(temp_runs)
            t_b = sum(r["bertscore"] for r in temp_runs) / len(temp_runs)
            marker = ""
            rec_models = [m for m, t in extra_therapy.items() if t == temp]
            if rec_models:
                marker = f" (rec for: {', '.join(rec_models)})"
            print(f"  T={temp}: J={t_j:.3f} B={t_b:.3f} ({len(temp_runs)} runs){marker}")

        # Per-model summary
        print("\nPer-model summary:")
        for model in targets:
            model_runs = [r for r in successful if r["model"] == model]
            if model_runs:
                m_j = sum(r["jaccard"] for r in model_runs) / len(model_runs)
                m_b = sum(r["bertscore"] for r in model_runs) / len(model_runs)
                print(f"  {model}: J={m_j:.3f} B={m_b:.3f} ({len(model_runs)} runs)")


if __name__ == "__main__":
    asyncio.run(main())
