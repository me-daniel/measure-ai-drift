"""Evaluation metrics for rescripting stability experiments.

Implements the three-level evaluation framework from the thesis:
- Level 3.1: Cognitive Stability (plan consistency via Jaccard)
- Level 3.2: Output Consistency (semantic stability via BERTScore)
- Level 3.3: Plan-Output Alignment (intervention fit via LLM judge)
"""

from __future__ import annotations

import asyncio
import logging
import re
from itertools import combinations
from typing import Any

logger = logging.getLogger(__name__)


PLAN_BLOCK_RE = re.compile(r"<plan>(.*?)</plan>", re.DOTALL | re.IGNORECASE)

def _load_valid_categories() -> set[str]:
    """Derive valid category IDs from the strategy taxonomy (single source of truth)."""
    from src.core.config_loader import load_strategy_taxonomy
    return {s["id"] for s in load_strategy_taxonomy().get("strategies", [])}


VALID_CATEGORIES = _load_valid_categories()


def extract_plan_strategies(plan_text: str) -> set[str]:
    """Extract strategy categories from a <plan>...</plan> block.

    Expects simple format: <plan>category1 / category2</plan>
    Returns only valid category IDs from the taxonomy.

    Args:
        plan_text: Raw model output containing a <plan> block.

    Returns:
        Set of valid strategy category IDs (e.g., {"agency", "safety"}).
    """
    match = PLAN_BLOCK_RE.search(plan_text or "")
    if not match:
        return set()

    block = match.group(1).strip()
    if not block:
        return set()

    # Split by " / " and normalize
    parts = [p.strip().lower() for p in block.split("/")]

    # Filter to valid categories only
    strategies = {p for p in parts if p in VALID_CATEGORIES}

    return strategies


def validate_plan_length(strategies: set[str], max_allowed: int = 2) -> bool:
    """Check if plan has valid number of strategies (1-2).
    
    Plans must have 1 or 2 strategies to be valid for thesis evaluation.
    
    Args:
        strategies: Set of extracted strategy bullets
        max_allowed: Maximum allowed strategies (default: 2)
        
    Returns:
        True if plan has valid number of strategies (1 <= n <= max_allowed)
        
    Example:
        >>> validate_plan_length({"agency", "safety"})
        True
        >>> validate_plan_length({"agency", "safety", "cognitive_reframe"})
        False
    """
    return 1 <= len(strategies) <= max_allowed


def compute_validity_rate(strategy_sets: list[set[str]], max_allowed: int = 2) -> float:
    """Compute fraction of plans that are valid (1-2 strategies).
    
    Useful for checking how well the model follows the 1-2 strategy constraint.
    
    Args:
        strategy_sets: List of strategy sets from multiple trials
        max_allowed: Maximum allowed strategies (default: 2)
        
    Returns:
        Fraction of valid plans (0.0-1.0)
        
    Example:
        >>> sets = [{"a", "b"}, {"c"}, {"d", "e", "f"}]  # 2 valid, 1 invalid
        >>> compute_validity_rate(sets)
        0.6666...
    """
    if not strategy_sets:
        return 0.0
    
    valid_count = sum(1 for s in strategy_sets if validate_plan_length(s, max_allowed))
    return valid_count / len(strategy_sets)


def compute_modal_set_agreement(strategy_sets: list[set[str]]) -> float:
    """Compute modal-set agreement: fraction of trials matching the most common strategy set.

    Complements Jaccard by measuring exact agreement rather than overlap.
    With discrete strategy picks (1-2 from 6), this is often more informative
    than mean pairwise Jaccard.

    Args:
        strategy_sets: List of strategy sets (one per trial).

    Returns:
        Fraction of trials matching the mode (0.0-1.0).

    Example:
        >>> sets = [{"a", "b"}, {"a", "b"}, {"a", "c"}]
        >>> compute_modal_set_agreement(sets)
        0.6666...
    """
    if not strategy_sets:
        return 0.0

    from collections import Counter
    # Convert sets to frozensets for hashing
    counts = Counter(frozenset(s) for s in strategy_sets)
    mode_count = counts.most_common(1)[0][1]
    return mode_count / len(strategy_sets)


def compute_pairwise_jaccard(
    sets: list[set[str]],
    only_valid: bool = False,
    max_allowed: int = 2,
) -> float:
    """Compute mean pairwise Jaccard similarity.
    
    Implements Level 3.1 (Cognitive Stability) from the thesis:
    Measures consistency of therapeutic strategies across stochastic trials.
    
    Args:
        sets: List of strategy sets (one per trial)
        only_valid: If True, exclude invalid plans (>2 strategies)
        max_allowed: Maximum strategies for validity check
        
    Returns:
        Mean Jaccard similarity across all pairs (0.0-1.0)
        
    Example:
        >>> sets = [{"agency", "safety"}, {"agency", "cognitive_reframe"}]
        >>> compute_pairwise_jaccard(sets)
        0.333...  # |{agency}| / |{agency, safety, cognitive_reframe}|
    """
    if only_valid:
        sets = [s for s in sets if validate_plan_length(s, max_allowed)]
    
    if len(sets) < 2:
        return 1.0

    scores: list[float] = []
    for a, b in combinations(sets, 2):
        if not a and not b:
            scores.append(1.0)
            continue
        union = a.union(b)
        if not union:
            scores.append(0.0)
            continue
        scores.append(len(a.intersection(b)) / len(union))

    return sum(scores) / len(scores) if scores else 0.0


_BERTSCORE_CACHE: dict[str, Any] = {}


def _get_bertscorer(model_type: str = "microsoft/deberta-xlarge-mnli") -> Any:
    """Return a cached BERTScorer instance (loads model only once per process)."""
    if model_type not in _BERTSCORE_CACHE:
        import warnings
        from bert_score import BERTScorer
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*UNEXPECTED.*")
            warnings.filterwarnings("ignore", category=FutureWarning)
            scorer = BERTScorer(model_type=model_type, lang="en")
        scorer._tokenizer.model_max_length = 512
        _BERTSCORE_CACHE[model_type] = scorer
    return _BERTSCORE_CACHE[model_type]


def compute_pairwise_bertscore(
    responses: list[str],
    model_type: str = "microsoft/deberta-xlarge-mnli",
) -> dict[str, float]:
    """Compute mean pairwise BERTScore across trial responses.

    Implements Level 3.2 (Output Consistency) from the thesis:
    Measures semantic similarity of therapist responses across trials.
    Uses DeBERTa-XLarge-MNLI (ranked #1 across 130+ models for correlation
    with human judgments). NLI fine-tuning makes it well-suited for
    comparing semantic equivalence of therapeutic responses.

    Args:
        responses: List of therapist response strings (one per trial)
        model_type: HuggingFace model for BERTScore

    Returns:
        Dict with mean precision, recall, and F1 scores

    Example:
        >>> responses = ["Let's modify the dream.", "Let's change the nightmare."]
        >>> scores = compute_pairwise_bertscore(responses)
        >>> scores["f1"]  # high similarity for semantically equivalent responses
    """
    # Filter empty responses (empty strings crash DeBERTa tokenizer)
    responses = [r for r in responses if r and r.strip()]

    if len(responses) < 2:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}

    # Build all pairs
    refs = []
    cands = []
    for a, b in combinations(responses, 2):
        refs.append(a)
        cands.append(b)

    scorer = _get_bertscorer(model_type)
    P, R, F1 = scorer.score(cands, refs)

    return {
        "precision": P.mean().item(),
        "recall": R.mean().item(),
        "f1": F1.mean().item(),
    }


# ---------------------------------------------------------------------------
# Level 3.3 — Plan-Output Alignment
# ---------------------------------------------------------------------------

# Primary: "agency: reasoning text | score: 2"
_JUDGMENT_LINE_RE = re.compile(
    r"^[\s*-]*(\w+):\s*(.+?)\s*\|\s*score:\s*([012])\s*$",
    re.IGNORECASE | re.MULTILINE,
)
# Fallback: "score: 2" on a separate line or "| 2" at end
_SCORE_NEARBY_RE = re.compile(
    r"(\w+).*?(?:\|\s*score:\s*([012])|score\s*[:=]\s*([012]))",
    re.IGNORECASE,
)


def _build_taxonomy_block(taxonomy: dict[str, Any]) -> str:
    """Format strategy definitions for the judge prompt."""
    lines = []
    for s in taxonomy.get("strategies", []):
        lines.append(f"- **{s['id']}**: {s['description']}")
    return "\n".join(lines)


def _build_strategies_block(strategies: set[str], taxonomy: dict[str, Any]) -> str:
    """Format declared strategies with their descriptions for the judge."""
    lookup = {s["id"]: s for s in taxonomy.get("strategies", [])}
    lines = []
    for sid in sorted(strategies):
        info = lookup.get(sid)
        if info:
            lines.append(f"- **{sid}**: {info['description']}")
        else:
            lines.append(f"- **{sid}**")
    return "\n".join(lines)


def _parse_judgment(raw: str, expected: set[str]) -> dict[str, dict[str, Any]]:
    """Parse judge output into per-strategy scores.

    Handles common format variations from different judge models:
    - Leading whitespace, bullets, or markdown bold
    - strategy_id literal instead of actual name (maps by position)
    - Thinking tags stripped before parsing

    Returns dict mapping strategy_id -> {"reasoning": str, "score": int}.
    Missing or unparseable strategies default to score 0.
    """
    # Strip thinking tags if present
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    # Strip markdown bold from strategy names
    cleaned = re.sub(r"\*\*(\w+)\*\*", r"\1", cleaned)

    parsed: dict[str, dict[str, Any]] = {}

    # Primary regex pass
    for match in _JUDGMENT_LINE_RE.finditer(cleaned):
        sid = match.group(1).lower()
        reasoning = match.group(2).strip()
        score = int(match.group(3))
        # Skip generic "strategy_id" literal — will handle below
        if sid != "strategy_id":
            parsed[sid] = {"reasoning": reasoning, "score": score}

    # If primary pass missed strategies, try to recover from "strategy_id:" lines
    # by matching scores to expected strategies in order
    if len(parsed) < len(expected):
        missing = expected - set(parsed.keys())
        # Look for lines with "strategy_id" literal or unmatched score patterns
        generic_scores = []
        for match in _JUDGMENT_LINE_RE.finditer(cleaned):
            sid = match.group(1).lower()
            if sid == "strategy_id" or sid not in expected:
                generic_scores.append({
                    "reasoning": match.group(2).strip(),
                    "score": int(match.group(3)),
                })

        # Assign generic scores to missing strategies in sorted order
        for sid, generic in zip(sorted(missing), generic_scores):
            parsed[sid] = generic
            logger.info("Mapped generic judge line to strategy '%s' (score=%d)", sid, generic["score"])

    # Fill any still-missing strategies with score 0
    for sid in expected:
        if sid not in parsed:
            logger.warning("Judge did not score strategy '%s' — defaulting to 0", sid)
            parsed[sid] = {"reasoning": "not scored by judge", "score": 0}

    return parsed


# Semaphore to limit concurrent judge calls (Gemini free tier: 25 RPM)
_JUDGE_SEMAPHORE: asyncio.Semaphore | None = None

def _get_judge_semaphore(max_concurrent: int = 5) -> asyncio.Semaphore:
    """Get or create the judge semaphore (lazy init for the current event loop)."""
    global _JUDGE_SEMAPHORE
    if _JUDGE_SEMAPHORE is None:
        _JUDGE_SEMAPHORE = asyncio.Semaphore(max_concurrent)
    return _JUDGE_SEMAPHORE


async def _judge_single_trial(
    judge: Any,
    system_prompt: str,
    user_msg: str,
    strategies: set[str],
    trial_index: int,
    timeout_seconds: int = 120,
    max_retries: int = 3,
) -> tuple[float, dict[str, Any], dict[str, list[int]]]:
    """Judge one trial with a timeout, semaphore, and retry on 429. Returns (score, judgment_dict, strategy_scores)."""
    sem = _get_judge_semaphore()

    for attempt in range(max_retries + 1):
        try:
            async with sem:
                raw_output, usage = await asyncio.wait_for(
                    judge.generate([
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_msg},
                    ]),
                    timeout=timeout_seconds,
                )

            parsed = _parse_judgment(raw_output, strategies)
            scores = [parsed[sid]["score"] for sid in strategies if sid in parsed]
            trial_alignment = (sum(scores) / (len(scores) * 2)) if scores else 0.0

            strat_scores: dict[str, list[int]] = {}
            for sid in strategies:
                if sid in parsed:
                    strat_scores.setdefault(sid, []).append(parsed[sid]["score"])

            judgment = {
                "trial": trial_index,
                "raw_output": raw_output,
                "parsed": {sid: parsed[sid] for sid in strategies if sid in parsed},
                "trial_alignment": trial_alignment,
                "usage": usage,
            }
            return trial_alignment, judgment, strat_scores

        except asyncio.TimeoutError:
            logger.warning("Judge call timed out for trial %d after %ds", trial_index, timeout_seconds)
            return 0.0, {"trial": trial_index, "error": f"timeout after {timeout_seconds}s"}, {}
        except Exception as e:
            err_str = str(e)
            if "429" in err_str and attempt < max_retries:
                wait = 15 * (attempt + 1)
                logger.info("Judge 429 for trial %d, retry %d/%d in %ds", trial_index, attempt + 1, max_retries, wait)
                await asyncio.sleep(wait)
                continue
            logger.warning("Judge call failed for trial %d: %s", trial_index, e)
            return 0.0, {"trial": trial_index, "error": err_str}, {}


async def compute_alignment(
    strategy_sets: list[set[str]],
    responses: list[str],
    taxonomy: dict[str, Any],
    experiment: bool = False,
) -> dict[str, Any]:
    """Evaluate plan-output alignment using an LLM judge.

    Implements Level 3.3 from the thesis: checks whether the therapist's
    response actually implements the strategies declared in its <plan>.
    Uses a ternary scale (0=absent, 1=partial, 2=implemented) normalised
    to 0.0-1.0 per trial.

    Judge calls run in parallel with a per-call timeout (120s).

    Args:
        strategy_sets: List of strategy sets (one per trial).
        responses: List of therapist response strings (one per trial).
        taxonomy: Loaded strategy_taxonomy.yaml dict.

    Returns:
        Dict with keys: mean_alignment, per_trial, per_strategy, raw_judgments,
        n_judged, n_errors, n_skipped. mean_alignment averages judged trials
        only; error/skipped trials appear as None in per_trial and are
        excluded (None if no trial could be judged).
    """
    from src.core.config_loader import load_yaml, PROMPTS_DIR
    from src.llm.provider import create_provider

    # Load judge prompt template
    prompt_data = load_yaml(PROMPTS_DIR / "evaluation" / "alignment_judge.yaml")
    system_template = prompt_data["system_prompt"]
    user_template = prompt_data["user_template"]

    # Build taxonomy block (shared across all trials)
    taxonomy_block = _build_taxonomy_block(taxonomy)
    system_prompt = system_template.replace("{taxonomy_block}", taxonomy_block)

    # Create judge provider: flash-lite for testing, pro for experiment
    judge = create_provider("judge", experiment=experiment)

    # Build tasks for all trials
    tasks = []
    skip_indices: dict[int, dict] = {}

    for i, (strategies, response) in enumerate(zip(strategy_sets, responses)):
        if not strategies or not response or not response.strip():
            skip_indices[i] = {"trial": i + 1, "skipped": True, "reason": "empty strategies or response"}
            continue

        strategies_block = _build_strategies_block(strategies, taxonomy)
        user_msg = user_template.replace("{strategies_block}", strategies_block).replace("{response}", response)
        tasks.append((i, _judge_single_trial(judge, system_prompt, user_msg, strategies, i + 1)))

    # Run all judge calls in parallel
    results_map: dict[int, tuple[float, dict, dict]] = {}
    if tasks:
        gathered = await asyncio.gather(*(t[1] for t in tasks))
        for (idx, _), result in zip(tasks, gathered):
            results_map[idx] = result

    # --- Pro fallback for suspect trials ---
    # Re-judge with Pro if: trial scores 0.0 OR any strategy was not scored by judge.
    # Keeps the original Flash judgment as a note, uses only the Pro score.
    suspect_indices = []
    for idx, (score, judgment, _) in results_map.items():
        if "error" in judgment:
            continue
        if score == 0.0:
            suspect_indices.append(idx)
            continue
        # Check for partial parse failures (strategy defaulted to 0 because judge didn't output it)
        parsed = judgment.get("parsed", {})
        if any(v.get("reasoning") == "not scored by judge" for v in parsed.values()):
            suspect_indices.append(idx)

    if suspect_indices and experiment:
        try:
            pro_judge = create_provider("judge", config_path=None, experiment=False)
            # Check if the experiment judge is already Pro (avoid double-judging with same model)
            is_already_pro = judge.config.model == pro_judge.config.model
            if is_already_pro:
                # Try loading gemini31_pro explicitly
                from src.llm.provider import load_config as _lc
                _cfg = _lc()
                _pro_def = _cfg.get("model_options", {}).get("judge", {}).get("gemini31_pro")
                if not _pro_def:
                    is_already_pro = True  # no Pro available, skip fallback
                else:
                    import os
                    _prov_cfg = _cfg["providers"][_pro_def["provider"]]
                    from src.llm.provider import LLMConfig, LLMProvider
                    pro_judge = LLMProvider(LLMConfig(
                        provider=_pro_def["provider"],
                        model=_pro_def["model"],
                        temperature=1.0,
                        max_tokens=4096,
                        api_key=os.environ.get(_prov_cfg.get("api_key_env", ""), ""),
                        base_url=_prov_cfg.get("base_url", ""),
                    ))
                    is_already_pro = False
        except Exception:
            is_already_pro = True  # can't create Pro judge, skip fallback

        if not is_already_pro and suspect_indices:
            logger.info("Re-judging %d zero-scored trials with Pro fallback", len(suspect_indices))
            for idx in suspect_indices:
                strategies = strategy_sets[idx]
                response = responses[idx]
                strategies_block = _build_strategies_block(strategies, taxonomy)
                user_msg = user_template.replace("{strategies_block}", strategies_block).replace("{response}", response)

                pro_score, pro_judgment, pro_strat_scores = await _judge_single_trial(
                    pro_judge, system_prompt, user_msg, strategies, idx + 1,
                )

                # Keep original Flash result as a note
                original_score, original_judgment, _ = results_map[idx]
                pro_judgment["pro_fallback"] = True
                pro_judgment["original_flash_score"] = original_score
                pro_judgment["original_flash_judgment"] = original_judgment

                if pro_score > 0.0:
                    logger.info("Pro fallback trial %d: %.2f (was %.2f from Flash)", idx + 1, pro_score, original_score)
                    results_map[idx] = (pro_score, pro_judgment, pro_strat_scores)
                else:
                    # Pro also scored 0 - keep it but note the double failure
                    pro_judgment["double_zero"] = True
                    logger.warning("Pro fallback also scored 0.0 for trial %d", idx + 1)
                    results_map[idx] = (pro_score, pro_judgment, pro_strat_scores)

    # Reassemble in order. Error/skipped trials carry None so they are
    # excluded from the mean: a judge timeout or an invalid plan is missing
    # data, not evidence of zero alignment (invalid plans already lower
    # validity_rate).
    per_trial: list[float | None] = []
    raw_judgments: list[dict[str, Any]] = []
    strategy_scores: dict[str, list[int]] = {}
    pro_fallback_count = 0
    n_errors = 0

    for i in range(len(strategy_sets)):
        if i in skip_indices:
            per_trial.append(None)
            raw_judgments.append(skip_indices[i])
        elif i in results_map:
            score, judgment, strat_scores = results_map[i]
            if "error" in judgment:
                n_errors += 1
                per_trial.append(None)
                raw_judgments.append(judgment)
                continue
            per_trial.append(score)
            raw_judgments.append(judgment)
            if judgment.get("pro_fallback"):
                pro_fallback_count += 1
            for sid, scores_list in strat_scores.items():
                strategy_scores.setdefault(sid, []).extend(scores_list)

    # Aggregate over judged trials only
    judged = [s for s in per_trial if s is not None]
    mean_alignment = sum(judged) / len(judged) if judged else None
    per_strategy = {
        sid: sum(scores) / (len(scores) * 2) if scores else 0.0
        for sid, scores in strategy_scores.items()
    }

    result = {
        "mean_alignment": mean_alignment,
        "per_trial": per_trial,
        "per_strategy": per_strategy,
        "raw_judgments": raw_judgments,
        "n_judged": len(judged),
        "n_errors": n_errors,
        "n_skipped": len(skip_indices),
    }
    if pro_fallback_count:
        result["pro_fallback_count"] = pro_fallback_count
        logger.info("Alignment complete: %d/%d trials used Pro fallback", pro_fallback_count, len(per_trial))

    return result
