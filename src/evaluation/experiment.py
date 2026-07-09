"""Experiment runner with structured output for reproducibility.

Creates experiment runs in the format:
    experiments/runs/{batch}/{timestamp}_{model}_{vignette}/
        config.yaml
        frozen_history.json
        trials/
            trial_01.json
            trial_02.json
            ...
        metrics.json
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from src.core import Conversation
from src.evaluation.sampler import Sampler, TrialResult
from src.evaluation.metrics import (
    extract_plan_strategies,
    compute_validity_rate,
    compute_pairwise_jaccard,
    compute_modal_set_agreement,
    compute_pairwise_bertscore,
    compute_alignment,
)


class ExperimentRun:
    """Manages a single experiment run with structured output."""

    def __init__(
        self,
        frozen_history: Conversation,
        model_name: str,
        vignette_name: str,
        base_dir: str | Path = "experiments/latest",
    ) -> None:
        self.frozen_history = frozen_history
        self.model_name = model_name
        self.vignette_name = vignette_name
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create run directory
        dir_name = f"{self.timestamp}_{model_name}_{vignette_name}"
        self.run_dir = Path(base_dir) / dir_name
        self.trials_dir = self.run_dir / "trials"

        self._results: list[TrialResult] = []
        self._config: dict[str, Any] = {}

    def setup(self) -> "ExperimentRun":
        """Create directory structure and save frozen history."""
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.trials_dir.mkdir(exist_ok=True)

        # Save frozen history
        history_path = self.run_dir / "frozen_history.json"
        with open(history_path, "w") as f:
            json.dump(self.frozen_history.to_dict(), f, indent=2, ensure_ascii=False, default=str)

        return self

    async def run(
        self,
        n_trials: int,
        temperature: float,
        language: str = "en",
        parallel: bool = False,
        mode: str = "split",
        therapist_provider: Any = None,
    ) -> list[TrialResult]:
        """Run the experiment and save results."""
        # Detect slice from frozen history filename (e.g., "slice_2.json" -> 2)
        slice_number = self._detect_slice(self.frozen_history)

        # Store config
        self._config = {
            "model": self.model_name,
            "vignette": self.vignette_name,
            "n_trials": n_trials,
            "temperature": temperature,
            "slice": slice_number,
            "language": language,
            "parallel": parallel,
            "mode": mode,
            "timestamp": self.timestamp,
        }

        # Save config
        config_path = self.run_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(self._config, f, default_flow_style=False)

        # Run trials
        from src.stacks.evaluation_stack import EvaluationStack
        stack = EvaluationStack(language=language, therapist_provider=therapist_provider, mode=mode)
        sampler = Sampler(language=language, stack=stack, mode=mode)
        self._results = await sampler.run(
            self.frozen_history,
            n_trials=n_trials,
            temperature=temperature,
            parallel=parallel,
        )

        # Save individual trials
        for i, result in enumerate(self._results, 1):
            trial_path = self.trials_dir / f"trial_{i:02d}.json"
            trial_data = {
                "temperature": result.temperature,
                "plan": result.plan,
                "response": result.response,
                "plan_usage": result.plan_usage,
                "response_usage": result.response_usage,
                "strategies": list(extract_plan_strategies(result.plan)),
            }
            with open(trial_path, "w") as f:
                json.dump(trial_data, f, indent=2, ensure_ascii=False)

        # Compute and save metrics
        await self._save_metrics()

        return self._results

    async def _save_metrics(self) -> None:
        """Compute and save metrics to metrics.json (and judgments.json)."""
        from src.core.config_loader import load_strategy_taxonomy

        strategy_sets = [extract_plan_strategies(r.plan) for r in self._results]

        # Compute BERTScore on responses
        responses = [r.response for r in self._results]
        bertscore = compute_pairwise_bertscore(responses)

        # Compute alignment (Level 3.3) — LLM judge call
        # Auto-detect experiment tier: experiment models use gemini31_pro judge
        from src.llm.provider import load_config
        _cfg = load_config()
        _experiment_names = {
            t["name"] for t in _cfg.get("evaluation_targets", [])
            if not t.get("name", "").endswith("_test")
        }
        is_experiment = self.model_name in _experiment_names

        taxonomy = load_strategy_taxonomy()
        alignment = await compute_alignment(
            strategy_sets, responses, taxonomy, experiment=is_experiment,
        )

        metrics = {
            "n_trials": len(self._results),
            "temperature": self._config.get("temperature", 0.0),
            "slice": self._config.get("slice"),
            "validity_rate": compute_validity_rate(strategy_sets),
            "jaccard_all": compute_pairwise_jaccard(strategy_sets, only_valid=False),
            "jaccard_valid_only": compute_pairwise_jaccard(strategy_sets, only_valid=True),
            "modal_set_agreement": compute_modal_set_agreement(strategy_sets),
            "bertscore_f1": bertscore["f1"],
            "bertscore_precision": bertscore["precision"],
            "bertscore_recall": bertscore["recall"],
            "alignment_mean": alignment["mean_alignment"],
            "alignment_per_trial": alignment["per_trial"],
            "alignment_per_strategy": alignment["per_strategy"],
            "alignment_n_judged": alignment["n_judged"],
            "alignment_n_errors": alignment["n_errors"],
            "alignment_n_skipped": alignment["n_skipped"],
            "alignment_pro_fallback": alignment.get("pro_fallback_count", 0),
            "strategy_counts": self._compute_strategy_counts(strategy_sets),
        }

        metrics_path = self.run_dir / "metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)

        # Save raw judge outputs for transparency/debugging
        judgments_path = self.run_dir / "judgments.json"
        with open(judgments_path, "w") as f:
            json.dump(alignment["raw_judgments"], f, indent=2, ensure_ascii=False)

    def _compute_strategy_counts(self, strategy_sets: list[set[str]]) -> dict[str, int]:
        """Count frequency of each strategy across trials."""
        counts: dict[str, int] = {}
        for strategies in strategy_sets:
            for s in strategies:
                counts[s] = counts.get(s, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: -x[1]))

    @staticmethod
    def _detect_slice(conversation: Conversation) -> int | None:
        """Detect slice number from frozen history metadata or source path."""
        # Check if metadata carries slice info
        meta = getattr(conversation, "metadata", {}) or {}
        if "slice" in meta:
            return int(meta["slice"])

        # Check source_path for slice_N pattern
        source = meta.get("source_path", "")
        if source:
            import re
            m = re.search(r"slice_(\d+)", str(source))
            if m:
                return int(m.group(1))

        return None

    @property
    def results(self) -> list[TrialResult]:
        return self._results

    @property
    def path(self) -> Path:
        return self.run_dir


def load_experiment(run_dir: str | Path) -> dict[str, Any]:
    """Load a completed experiment run."""
    run_dir = Path(run_dir)

    # Load config
    with open(run_dir / "config.yaml") as f:
        config = yaml.safe_load(f)

    # Load metrics
    with open(run_dir / "metrics.json") as f:
        metrics = json.load(f)

    # Load trials
    trials = []
    trials_dir = run_dir / "trials"
    for trial_path in sorted(trials_dir.glob("trial_*.json")):
        with open(trial_path) as f:
            trials.append(json.load(f))

    return {
        "config": config,
        "metrics": metrics,
        "trials": trials,
        "path": str(run_dir),
    }
