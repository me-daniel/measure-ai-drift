"""Re-judge one trial per main-experiment run and report agreement with stored judgments.

Samples one judged trial from each of the 360 runs in stats/data/experiment_runs.csv,
re-runs the original judge (gemini3_flash at T=1.0) with the exact same prompt
construction as compute_alignment(), and compares the new scores against the
judgments already on disk.

Per-run results are cached under stats/data/cache/rejudge/ so the script is
resumable. Aggregate agreement statistics land in stats/data/judge_rerun_agreement.json.

Usage:
    python scripts/rejudge_subset.py --limit 5      # smoke test
    python scripts/rejudge_subset.py                # full 360
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import random
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from src.core.config_loader import load_yaml, load_strategy_taxonomy, PROMPTS_DIR
from src.evaluation.metrics import (
    _build_strategies_block,
    _build_taxonomy_block,
    _judge_single_trial,
)
from src.llm.provider import create_provider


ROOT = Path(__file__).parent.parent
RUNS_CSV = ROOT / "stats" / "data" / "experiment_runs.csv"
CACHE_DIR = ROOT / "stats" / "data" / "cache" / "rejudge"
OUT_PATH = ROOT / "stats" / "data" / "judge_rerun_agreement.json"

# Directories searched (in order) when resolving a run_id to a run directory
RUN_DIRS = [
    ROOT / "experiments" / "latest",
    ROOT / "experiments" / "runs" / "batch_20260709_mistral_medium35",
    ROOT / "experiments" / "runs" / "batch_20260728_command_a",
    ROOT / "experiments" / "runs" / "batch_20260728_gpt54_native",
]

# Sentinel written by _parse_judgment when the judge never scored a strategy
PARSE_DEFAULT_REASONING = "not scored by judge"


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------


def resolve_run_dir(run_id: str) -> Path | None:
    """Find the run directory for a run_id across the known batch dirs."""
    for base in RUN_DIRS:
        path = base / run_id
        if path.exists():
            return path
    return None


def load_runs(limit: int | None = None) -> list[dict[str, Any]]:
    """Read run_ids from the experiment CSV and resolve each to a directory."""
    with open(RUNS_CSV) as f:
        rows = list(csv.DictReader(f))

    runs = []
    for row in rows:
        run_dir = resolve_run_dir(row["run_id"])
        if run_dir is None:
            print(f"  WARNING: no run dir for {row['run_id']}")
            continue
        runs.append({
            "run_id": row["run_id"],
            "path": run_dir,
            "model": row["model"],
            "vignette": row["vignette"],
            "temperature": float(row["temperature"]),
        })

    if limit:
        runs = runs[:limit]
    return runs


def has_parse_default(parsed: dict[str, Any]) -> bool:
    """True if any strategy carries the parse-default sentinel (a fake 0)."""
    return any(v.get("reasoning") == PARSE_DEFAULT_REASONING for v in parsed.values())


def pick_trial(run: dict[str, Any], seed: int) -> dict[str, Any] | None:
    """Deterministically pick one judged trial from a run.

    Returns a dict with the sampled trial index, the original judgment's parsed
    scores and alignment, and the two quality flags. None if nothing is eligible.
    """
    judgments_path = run["path"] / "judgments.json"
    if not judgments_path.exists():
        return None

    with open(judgments_path) as f:
        judgments = json.load(f)

    eligible = [
        j for j in judgments
        if isinstance(j, dict)
        and j.get("parsed")
        and not j.get("error")
        and not j.get("skipped")
    ]
    if not eligible:
        return None

    rng = random.Random(f"{seed}:{run['run_id']}")
    judgment = rng.choice(eligible)

    parsed = judgment["parsed"]
    return {
        "trial": judgment["trial"],
        "original_parsed": {sid: v["score"] for sid, v in parsed.items()},
        "original_reasoning": {sid: v.get("reasoning", "") for sid, v in parsed.items()},
        "original_trial_alignment": judgment.get("trial_alignment"),
        "was_pro_fallback": bool(judgment.get("pro_fallback")),
        "had_parse_default": has_parse_default(parsed),
    }


# ---------------------------------------------------------------------------
# Judging
# ---------------------------------------------------------------------------


async def rejudge_run(
    run: dict[str, Any],
    sample: dict[str, Any],
    judge: Any,
    system_prompt: str,
    user_template: str,
    taxonomy: dict[str, Any],
) -> dict[str, Any]:
    """Re-judge one sampled trial and return the cache record."""
    trial_path = run["path"] / "trials" / f"trial_{sample['trial']:02d}.json"
    with open(trial_path) as f:
        trial_data = json.load(f)

    strategies = set(trial_data.get("strategies") or [])
    response = trial_data.get("response") or ""

    if not strategies or not response.strip():
        return {**run_meta(run), **sample, "rerun_error": "empty strategies or response"}

    strategies_block = _build_strategies_block(strategies, taxonomy)
    user_msg = user_template.replace("{strategies_block}", strategies_block).replace("{response}", response)

    _, judgment, _ = await _judge_single_trial(
        judge, system_prompt, user_msg, strategies, sample["trial"],
    )

    if "error" in judgment:
        return {**run_meta(run), **sample, "rerun_error": judgment["error"]}

    rerun_parsed = judgment.get("parsed", {})
    return {
        **run_meta(run),
        **sample,
        "strategies": sorted(strategies),
        "rerun_parsed": {sid: v["score"] for sid, v in rerun_parsed.items()},
        "rerun_reasoning": {sid: v.get("reasoning", "") for sid, v in rerun_parsed.items()},
        "rerun_trial_alignment": judgment.get("trial_alignment"),
        "rerun_had_parse_default": has_parse_default(rerun_parsed),
        "rerun_raw_output": judgment.get("raw_output", ""),
        "rerun_usage": judgment.get("usage", {}),
    }


def run_meta(run: dict[str, Any]) -> dict[str, Any]:
    """Metadata fields copied into every cache record."""
    return {
        "run_id": run["run_id"],
        "model": run["model"],
        "vignette": run["vignette"],
        "temperature": run["temperature"],
    }


# ---------------------------------------------------------------------------
# Agreement statistics
# ---------------------------------------------------------------------------


def confusion_matrix(pairs: list[tuple[int, int]]) -> list[list[int]]:
    """3x3 counts, rows = original score, cols = rerun score."""
    matrix = [[0, 0, 0] for _ in range(3)]
    for a, b in pairs:
        matrix[a][b] += 1
    return matrix


def strategy_stats(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Strategy-level agreement over paired original/rerun scores."""
    pairs: list[tuple[int, int]] = []
    for rec in records:
        original = rec.get("original_parsed", {})
        rerun = rec.get("rerun_parsed", {})
        for sid in sorted(set(original) & set(rerun)):
            pairs.append((original[sid], rerun[sid]))

    if not pairs:
        return {"n_pairs": 0}

    a = [p[0] for p in pairs]
    b = [p[1] for p in pairs]
    deltas = [abs(x - y) for x, y in pairs]
    n = len(pairs)

    stats = {
        "n_pairs": n,
        "exact_agreement": sum(1 for d in deltas if d == 0) / n,
        "off_by_1_rate": sum(1 for d in deltas if d == 1) / n,
        "off_by_2_rate": sum(1 for d in deltas if d == 2) / n,
        "confusion_matrix": confusion_matrix(pairs),
        "confusion_matrix_note": "rows = original score 0/1/2, cols = rerun score 0/1/2",
        "original_score_distribution": dict(sorted(Counter(a).items())),
        "rerun_score_distribution": dict(sorted(Counter(b).items())),
    }

    try:
        from sklearn.metrics import cohen_kappa_score
        if len(set(a)) > 1 or len(set(b)) > 1:
            stats["weighted_kappa_linear"] = float(
                cohen_kappa_score(a, b, weights="linear", labels=[0, 1, 2])
            )
        else:
            stats["weighted_kappa_linear"] = None
    except ImportError:
        stats["weighted_kappa_linear"] = None

    return stats


def trial_stats(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Trial-level agreement on trial_alignment."""
    deltas = []
    for rec in records:
        orig = rec.get("original_trial_alignment")
        rerun = rec.get("rerun_trial_alignment")
        if orig is None or rerun is None:
            continue
        deltas.append(rerun - orig)

    if not deltas:
        return {"n_trials": 0}

    abs_deltas = [abs(d) for d in deltas]
    return {
        "n_trials": len(deltas),
        "mean_abs_delta": statistics.mean(abs_deltas),
        "median_abs_delta": statistics.median(abs_deltas),
        "mean_signed_delta": statistics.mean(deltas),
        "n_delta_zero": sum(1 for d in deltas if d == 0),
        "pct_delta_zero": sum(1 for d in deltas if d == 0) / len(deltas),
        "max_abs_delta": max(abs_deltas),
    }


def breakdown(records: list[dict[str, Any]], key: str) -> dict[str, Any]:
    """Trial-level stats grouped by a metadata key."""
    groups: dict[Any, list[dict]] = defaultdict(list)
    for rec in records:
        groups[rec[key]].append(rec)
    return {str(k): trial_stats(v) for k, v in sorted(groups.items(), key=lambda kv: str(kv[0]))}


def compute_stats(records: list[dict[str, Any]], seed: int) -> dict[str, Any]:
    """Build the full agreement report."""
    ok = [r for r in records if "rerun_error" not in r]
    errored = [r for r in records if "rerun_error" in r]

    flagged = [r for r in ok if r["was_pro_fallback"] or r["had_parse_default"]]
    headline = [r for r in ok if not r["was_pro_fallback"] and not r["had_parse_default"]]

    rerun_parse_defaults = [r["run_id"] for r in ok if r.get("rerun_had_parse_default")]

    return {
        "seed": seed,
        "judge": "gemini3_flash @ T=1.0 (experiment judge)",
        "n_runs_sampled": len(records),
        "n_rerun_errors": len(errored),
        "rerun_errors": [{"run_id": r["run_id"], "error": r["rerun_error"]} for r in errored],
        "n_excluded_flagged": len(flagged),
        "n_headline": len(headline),
        "flag_counts": {
            "was_pro_fallback": sum(1 for r in ok if r["was_pro_fallback"]),
            "had_parse_default": sum(1 for r in ok if r["had_parse_default"]),
            "both": sum(1 for r in ok if r["was_pro_fallback"] and r["had_parse_default"]),
        },
        "rerun_parse_default_count": len(rerun_parse_defaults),
        "rerun_parse_default_runs": rerun_parse_defaults,
        "headline": {
            "strategy_level": strategy_stats(headline),
            "trial_level": trial_stats(headline),
            "by_model": breakdown(headline, "model"),
            "by_temperature": breakdown(headline, "temperature"),
        },
        "flagged_rows": {
            "strategy_level": strategy_stats(flagged),
            "trial_level": trial_stats(flagged),
        },
        "all_rows_including_flagged": {
            "strategy_level": strategy_stats(ok),
            "trial_level": trial_stats(ok),
        },
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def format_time(seconds: float) -> str:
    """Format seconds as h:mm:ss or m:ss."""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def print_report(stats: dict[str, Any]) -> None:
    """Print the headline agreement numbers."""
    print("\n=== Judge rerun agreement ===")
    print(f"  Runs sampled: {stats['n_runs_sampled']}")
    print(f"  Rerun errors: {stats['n_rerun_errors']}")
    print(f"  Excluded (flagged): {stats['n_excluded_flagged']} "
          f"(pro_fallback={stats['flag_counts']['was_pro_fallback']}, "
          f"parse_default={stats['flag_counts']['had_parse_default']})")
    print(f"  Headline n: {stats['n_headline']}")
    print(f"  Rerun parse-defaults: {stats['rerun_parse_default_count']}")

    s = stats["headline"]["strategy_level"]
    t = stats["headline"]["trial_level"]
    if s.get("n_pairs"):
        kappa = s.get("weighted_kappa_linear")
        print(f"\n  Strategy level (n={s['n_pairs']} pairs):")
        print(f"    exact agreement : {s['exact_agreement']:.1%}")
        print(f"    off by 1        : {s['off_by_1_rate']:.1%}")
        print(f"    off by 2        : {s['off_by_2_rate']:.1%}")
        print(f"    weighted kappa  : {kappa:.3f}" if kappa is not None else "    weighted kappa  : n/a")
        print("    confusion (rows=original, cols=rerun):")
        for i, row in enumerate(s["confusion_matrix"]):
            print(f"      {i}: {row}")

    if t.get("n_trials"):
        print(f"\n  Trial level (n={t['n_trials']}):")
        print(f"    mean |delta|    : {t['mean_abs_delta']:.4f}")
        print(f"    median |delta|  : {t['median_abs_delta']:.4f}")
        print(f"    mean signed     : {t['mean_signed_delta']:+.4f}")
        print(f"    delta == 0      : {t['n_delta_zero']} ({t['pct_delta_zero']:.1%})")
        print(f"    max |delta|     : {t['max_abs_delta']:.4f}")

    fs = stats["flagged_rows"]["strategy_level"]
    ft = stats["flagged_rows"]["trial_level"]
    if fs.get("n_pairs"):
        kappa = fs.get("weighted_kappa_linear")
        kstr = f"{kappa:.3f}" if kappa is not None else "n/a"
        print(f"\n  Flagged rows (n={ft['n_trials']} trials, {fs['n_pairs']} pairs):")
        print(f"    exact agreement : {fs['exact_agreement']:.1%}  kappa {kstr}")
        print(f"    mean |delta|    : {ft['mean_abs_delta']:.4f}  delta==0 {ft['pct_delta_zero']:.1%}")

    print("\n  By temperature:")
    for temp, tt in stats["headline"]["by_temperature"].items():
        if tt.get("n_trials"):
            print(f"    T={temp:<6} n={tt['n_trials']:<4} mean|d|={tt['mean_abs_delta']:.4f} "
                  f"zero={tt['pct_delta_zero']:.1%}")

    print("\n  By model:")
    for model, tt in stats["headline"]["by_model"].items():
        if tt.get("n_trials"):
            print(f"    {model:<22} n={tt['n_trials']:<4} mean|d|={tt['mean_abs_delta']:.4f} "
                  f"zero={tt['pct_delta_zero']:.1%}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    parser = argparse.ArgumentParser(description="Re-judge one trial per run and report agreement")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N runs")
    args = parser.parse_args()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    runs = load_runs(args.limit)
    print(f"Re-judging 1 trial per run: {len(runs)} runs (seed {args.seed})")

    # Prompt setup: replicate compute_alignment() exactly
    prompt_data = load_yaml(PROMPTS_DIR / "evaluation" / "alignment_judge.yaml")
    taxonomy = load_strategy_taxonomy()
    system_prompt = prompt_data["system_prompt"].replace(
        "{taxonomy_block}", _build_taxonomy_block(taxonomy)
    )
    user_template = prompt_data["user_template"]

    judge = create_provider("judge", experiment=True)
    print(f"  Judge: {judge.config.model} @ T={judge.config.temperature}")

    records: list[dict[str, Any]] = []
    pending: list[tuple[dict, dict]] = []
    n_cached = 0
    n_no_trial = 0

    for run in runs:
        cache_path = CACHE_DIR / f"{run['run_id']}.json"
        if cache_path.exists():
            with open(cache_path) as f:
                records.append(json.load(f))
            n_cached += 1
            continue

        sample = pick_trial(run, args.seed)
        if sample is None:
            print(f"  SKIP {run['run_id']}: no eligible trial")
            n_no_trial += 1
            continue
        pending.append((run, sample))

    print(f"  Cached: {n_cached}, to judge: {len(pending)}, no eligible trial: {n_no_trial}")

    if pending:
        start = time.time()
        done = 0

        async def worker(run: dict, sample: dict) -> dict:
            nonlocal done
            record = await rejudge_run(run, sample, judge, system_prompt, user_template, taxonomy)
            if "rerun_error" not in record:
                with open(CACHE_DIR / f"{run['run_id']}.json", "w") as f:
                    json.dump(record, f, indent=2)
            done += 1
            if done % 25 == 0 or done == len(pending):
                elapsed = time.time() - start
                eta = elapsed / done * (len(pending) - done)
                print(f"  {done}/{len(pending)} judged "
                      f"(elapsed {format_time(elapsed)}, ETA {format_time(eta)})", flush=True)
            return record

        results = await asyncio.gather(*(worker(r, s) for r, s in pending))
        records.extend(results)
        print(f"  Judging took {format_time(time.time() - start)}")

    stats = compute_stats(records, args.seed)
    with open(OUT_PATH, "w") as f:
        json.dump(stats, f, indent=2)

    print_report(stats)
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
