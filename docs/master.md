# Measure-AI-Drift - Project Master Document

> Single source of truth for thesis scope, architecture, design decisions, and model selection.
> For chapter structure, see [thesis_extended_structure.md](thesis_extended_structure.md).
> For Claude Code working instructions, see [../CLAUDE.md](../CLAUDE.md).

---

## 1 Thesis Scope

**Title:** Measuring Drift in Therapeutic AI: A Stability-Based Evaluation of Sovereign LLMs in Nightmare Therapy

**Research question:** How consistent is LLM clinical reasoning across stochastic runs in a structured therapeutic protocol?

**Core idea:** LLMs used in therapy must produce stable, protocol-adherent responses, not just plausible ones. This thesis builds a three-level evaluation framework to measure that stability and applies it to compare an EU-sovereign therapy model against proprietary and open-weight baselines.

**Scope boundaries:**
- Isolated to the **rescripting phase** of Imagery Rehearsal Therapy (the cognitive core)
- Synthetic patients (BDI-profiled vignettes), not real clinical interactions
- **Fused mode** only (plan + response in a single CoT call). Chained mode was explored early on but fused is the production approach
- Stability measurement, not therapeutic efficacy

**What this thesis is NOT:**
- Not a clinical trial (no real patients)
- Not a benchmark paper (the framework is the contribution, not a leaderboard)
- Not about sovereignty per se: sovereignty motivates the choice of primary subject, but the evaluation framework applies to any LLM

---

## 2 Architecture

### 2.1 Two-Stack Design

The system separates dialogue creation from stability measurement:

**Generation Stack** (`src/stacks/generation_stack.py`):
Three-agent loop that produces synthetic therapy sessions.
- **Patient Agent**: simulates responses based on a BDI-profiled vignette
- **Router Agent**: classifies current IRT stage from conversation history
- **Therapist Agent**: generates stage-appropriate therapeutic responses
- Traverses the 5-stage IRT protocol: recording → rewriting → summary → rehearsal → final
- `save_frozen_history()` exports the full dialogue plus slices at rewriting-turn boundaries

**Evaluation Stack** (`src/stacks/evaluation_stack.py`):
Runs stability tests on frozen conversation histories.
- Bypasses the router → the rescripting prompt is injected directly (stage is known a priori)
- Fused CoT generation: `<plan>` block declares 1–2 strategies, then the therapeutic response follows
- Runs N independent trials per condition (default: 20)
- Computes three evaluation metrics per experiment run

### 2.2 Data Flow

```
Vignettes (6 JSON files)
    ↓
Generation Stack (Patient ↔ Router ↔ Therapist)
    ↓
Frozen Histories: frozen_{vignette}_{hash}/
    full.json, slice_1.json, slice_2.json, slice_3.json
    ↓
Evaluation Stack (rescripting prompt → Therapist LLM × 20 trials × 5 temperatures)
    ↓
Experiment Runs: {timestamp}_{model}_{vignette}/
    config.yaml, frozen_history.json, trials/, metrics.json, judgments.json
    ↓
Aggregation Pipeline
    ↓
Results: stability, semantic consistency, alignment scores
```

### 2.3 Frozen History Design

Frozen histories are deterministic evaluation entry points: every trial receives identical context.

Each vignette produces one folder with four files:
- `full.json`: complete dialogue (all stages)
- `slice_1.json`: prefix up to and including the 1st rewriting exchange
- `slice_2.json`: prefix up to and including the 2nd rewriting exchange
- `slice_3.json`: prefix up to and including the 3rd rewriting exchange

Slicing uses `slice_at_rewriting_turn(n)`, which cuts after the Nth therapist rewriting message. Patient messages have `stage=None` (only therapist messages carry stage tags), so this method correctly excludes post-slice patient responses.

> **Known bug:** `slice_at_stage(REWRITING)` leaks post-rewriting patient messages. Not used in production.

### 2.4 Key Components

| Component | Path | Purpose |
|-----------|------|---------|
| Agents | `src/agents/` | Patient, Therapist, Router implementations |
| Core models | `src/core/` | Conversation, Message, Stage/Language enums, config loading |
| LLM provider | `src/llm/provider.py` | Multi-provider abstraction (Groq, OpenAI, Scaleway, Gemini, Mistral, OpenRouter) |
| Experiment runner | `src/evaluation/experiment.py` | Orchestrates a single experiment run |
| Sampler | `src/evaluation/sampler.py` | Multi-trial generation (serial/parallel) |
| Metrics | `src/evaluation/metrics.py` | Jaccard, BERTScore, validity rate, alignment |
| CLI | `src/cli.py` | All commands: generate, evaluate, aggregate, etc. |

### 2.5 Design Patterns

- **Async-first**: all LLM calls use `asyncio`
- **Config-driven**: models and prompts loaded from YAML, swap without code changes
- **Pydantic models**: type-safe data flow. `extra="ignore"` silently drops unknown JSON fields
- **Provider abstraction**: single `LLMProvider` class for all backends via OpenAI-compatible API
- **Frozen histories**: serialised conversation snapshots for deterministic evaluation

> For the full file tree, see [architecture_plan.md](architecture_plan.md).

---

## 3 Evaluation Framework

Three levels, each measuring a distinct property:

### 3.1 Method 1 - Plan Consistency

**Question:** Do stochastic runs produce the same therapeutic decisions?

**Metric:** Mean pairwise Jaccard similarity over strategy sets across C(20,2) = 190 trial pairs.

**Input:** Strategy sets extracted from `<plan>` blocks via `extract_plan_strategies()`.

**Quality gate:** Plan validity rate, i.e. percentage of trials where the `<plan>` block parses correctly.

### 3.2 Method 2 - Response Similarity

**Question:** Do stochastic runs produce therapeutically equivalent responses?

**Metric:** Mean pairwise BERTScore F1 across 190 trial pairs.

**Embedding model:** DeBERTa-XLarge-MNLI (He et al., 2021), ranked #1 of 130+ models on WMT16 human correlation (r = 0.778). NLI fine-tuning aligns with the semantic comparison task.

**Input:** Response texts only (plan blocks excluded).

> For model selection rationale, see [bertscore_model_selection.md](bertscore_model_selection.md).

### 3.3 Method 3 - Plan-Response Alignment (Validation Check)

**Question:** Does the model's response implement its declared therapeutic plan?

**Metric:** LLM judge (Gemini 3 Flash, T=1.0; suspect trials re-judged by Gemini 3.1 Pro) scores each declared strategy on a ternary scale:
- 0 = absent, 1 = partial, 2 = implemented

**Inputs:** Both the extracted strategies AND the response text, scored against the strategy taxonomy definitions.

**Mitigations:** Cross-model judging, CoT justification, deterministic decoding, transparent rubric.

**Role in analysis:** Alignment serves as a validation check: if models consistently score near 1.0, it confirms they implement what they declare, which validates Jaccard as measuring genuine decision stability (not just label noise). If variance appears, alignment becomes a comparative metric in its own right.

> For the full rationale (including why NLI cross-encoders were rejected), see [alignment_approach_analysis.md](alignment_approach_analysis.md).

### Data Flow Between Methods

```
Trial output (plan + response)
    ├─→ extract_plan_strategies() ─→ strategy sets ─→ Method 1 (Jaccard)
    ├─→ response texts ─────────────────────────────→ Method 2 (BERTScore)
    └─→ strategies + response + taxonomy ───────────→ Method 3 (LLM judge)
```

---

## 4 The Plan Mechanism

The `<plan>` block is a **declared intent mechanism**, not an explanation of internal reasoning.

In fused mode, the model produces `<plan>strategy_1 / strategy_2</plan>` followed by its therapeutic response in a single call. The plan tokens condition the response tokens (CoT-style).

**What the plan enables:**
- Structured measurement of strategy-level consistency (Method 1)
- Alignment verification between intent and execution (Method 3)
- Clinical oversight (reviewable summary of intended approach)
- Taxonomic constraint (keeps responses within the IRT framework)

**What the plan does NOT claim:** faithfulness to internal reasoning. The CoT faithfulness debate (Turpin et al., 2023; Lanham et al., 2023) is acknowledged but sidestepped: the measurement framework works regardless of whether the plan reflects genuine reasoning.

> For the full analysis including fused vs. chained comparison, see [plan_mechanism_analysis.md](plan_mechanism_analysis.md). Note: that document was written during early exploration when chained mode showed higher empirical stability. The thesis uses fused mode because the plan conditioning the response tokens is the more natural CoT framing, and the chained comparison data predates the current 6-category taxonomy.

---

## 5 Strategy Taxonomy

6 categories describing concrete therapeutic **mechanisms** (not goals):

| Category | Mechanism |
|----------|-----------|
| confrontation | External action toward the threat (fight, challenge, resist) |
| self_empowerment | Internal transformation (grow stronger, gain abilities) |
| safety | Environment modification (safe spaces, protective elements) |
| cognitive_reframe | Meaning change (reinterpret threatening elements) |
| social_support | Adding allies (introduce helpful figures) |
| sensory_modulation | Sensory and calming details (modify light, sound, texture, introduce comforting elements) |

The taxonomy evolved through four iterations (8 → 6 → 7 → 6) to resolve a severe distribution skew where empowerment/mastery consumed 87.7% of all picks.

> For the full evolution history, see [strategy_taxonomy_evolution.md](strategy_taxonomy_evolution.md).

---

## 6 Model Selection

### 6.1 Sovereignty Scope

Sovereignty is relevant **only for the primary therapy model**: Mistral Large 3 (currently via OpenRouter, Mistral API as fallback). It is the EU-sovereign, Apache 2.0 flagship being evaluated against baselines.

All other roles (patient, router, judge) and all other evaluation targets have **no sovereignty requirement**. The thesis question is "does the EU flagship match proprietary frontier?", not "are all models sovereign?"

### 6.2 Evaluation Targets (Therapist Role)

These are the 12 models being compared on the three evaluation metrics, all running in non-thinking mode.

**Primary subject:**

| Model | Size | Provider | Notes |
|-------|------|----------|-------|
| **Mistral Large 3** | 675B MoE (41B active) | OpenRouter | EU-sovereign, Apache 2.0. The EU flagship this thesis evaluates |

**EU-sovereign (Mistral family):**

| Model | Size | Provider | Why this model |
|-------|------|----------|----------------|
| **Mistral Small 3.2** | 24B dense | OpenRouter | Smallest Mistral, baseline within the family |
| **Mistral Small 4** | 119B MoE (6.5B active) | OpenRouter | Newest Mistral, fewest active parameters of any MoE in the set |
| **Mistral Medium 3.5** | 128B dense | OpenRouter | Post-hoc addition (July 2026, run on identical frozen histories) validating pipeline extensibility. Open weights, modified MIT license (not Apache 2.0 like its siblings). Released 2026-04-30 |

**Open-weight comparators (by size class):**

| Class | Model | Size | Provider | Why this model |
|-------|-------|------|----------|----------------|
| Small | **Qwen 3.5 27B** | 27B dense | OpenRouter | Benchmark leader at this size class. Hybrid-thinking, reasoning disabled for fair comparison |
| Small | **OLMo 3.1 32B** | 32B dense | OpenRouter | Fully open (weights + training data + code). Best provenance story for a thesis |
| Mid | **Llama 3.3 70B** | 70B dense | OpenRouter | Original model from the efficacy study. Provides continuity with prior work |
| Large | **Qwen 3.5 122B** | 122B MoE (10B active) | OpenRouter | Mid-size MoE comparator |
| Large | **Qwen 3.5 397B** | 397B MoE (17B active) | OpenRouter | Large MoE comparator, replaced DeepSeek V3.2 |
| Large | **Command A** | 111B dense | OpenRouter (pinned to Cohere) | Dense control for the dense-architecture expectation behind Medium 3.5. CC-BY-NC, added 2026-07-28 |

**Proprietary ceiling:**

| Model | Provider | Why this model |
|-------|----------|----------------|
| **GPT-5.4** | OpenAI API (native, gateway dropped temperature) | Strongest proprietary model without thinking overhead |
| **Claude Sonnet 4.6** | OpenRouter ($3/$15) | Character-trained for safety-aware interaction. Near-Opus capability at Sonnet pricing |

**Selection rationale:**
- Size-class ladder: 24-32B (small dense) -> 70B (mid dense) -> 119-675B MoE (large) -> frontier (proprietary ceiling)
- Four Mistral models test sovereignty across the family (Medium 3.5 added post-hoc as extensibility check)
- Qwen 3.5 at three scales (27B, 122B, 397B) tests scaling within one family
- OLMo 3.1: full data provenance
- Llama 3.3 70B: continuity with the original efficacy study
- Command A: second 111-128B dense model, controls whether stability tracks the dense architecture class or the specific model
- Two proprietary ceilings: GPT-5.4 + Sonnet 4.6

**Dropped (kept as commented options in models.yaml):**
- DeepSeek V3.2 (internal temperature scaling makes cross-model comparison unreliable)
- Mistral Medium 3.1 (closed weights, weak thesis story — superseded by the open-weight Medium 3.5, added July 2026)
- GLM-5 (third MoE adds little)

> All 12 evaluation targets are configured in `models.yaml`. See [thesis_models.md](thesis_models.md) for the full assignment table and [SOTA_LLMs.md](SOTA_LLMs.md) for current availability and pricing.

### 6.3 Supporting Roles

These models are NOT being evaluated. They serve infrastructure roles:

| Role | Current model | Purpose |
|------|--------------|---------|
| **Patient** | Dolphin Mistral Venice 24B (OpenRouter, free) | Uncensored Mistral fine-tune for nightmare/trauma roleplay |
| **Router** | Llama 3.3 70B (OpenRouter) | Classifies IRT stage during generation |
| **Judge** | Gemini 3 Flash (Google AI Studio, T=1.0); Gemini 3.1 Pro re-judges suspect trials | Scores plan-output alignment (Method 3). Thinking enabled. No family overlap with eval targets |

### 6.4 Providers

| Provider | Base URL | Used for |
|----------|----------|----------|
| OpenRouter | `openrouter.ai/api/v1` | All evaluation targets except GPT-5.4, Patient (Venice), Router |
| OpenAI | `api.openai.com/v1` | GPT-5.4 (native re-collection, gateway dropped temperature) |
| Google AI Studio | `generativelanguage.googleapis.com/v1beta/openai/` | Judge (Gemini 3 Flash + 3.1 Pro fallback) |

Per-collection serving conditions (routing mode, pinning, quantisation snapshots): [LLM_run_recordings.md](LLM_run_recordings.md).

### 6.5 OpenRouter Constraints

- Per model: 6 vignettes x 1 slice x 20 trials x 5 temperatures = 600 calls

---

## 7 Experimental Design

### 7.1 Conditions

| Dimension | Values |
|-----------|--------|
| Vignettes | anxious, avoidant, cooperative, resistant, skeptic, trauma |
| Slice | slice_2 (second rewriting-turn boundary) |
| Trials per condition | 20 |
| Temperatures | T=0.0, T=0.075, T=0.15, T=0.3, T=0.6 |
| Models | 12 evaluation targets (see §6.2) |

Total per model: 6 x 1 x 20 x 5 = **600 trials**
Total across all models: 600 x 12 = **7,200 trials**

> Collection dates: 10 models on 2026-03-21 to 2026-03-24; Mistral Medium 3.5 added 2026-07-09 on the identical frozen histories (`run_date` column in the aggregated CSV).

### 7.2 Output Structure

Each experiment run produces:
```
experiments/runs/{timestamp}_{model}_{vignette}/
    config.yaml           # run parameters
    frozen_history.json    # input conversation
    trials/
        trial_01.json ... trial_20.json  # plan + response + usage + strategies
    metrics.json           # Jaccard, BERTScore, validity, alignment
    judgments.json          # raw LLM judge outputs with reasoning
```

### 7.3 Configuration Files

- `src/config/models.yaml`: provider endpoints, model options, active role assignments, evaluation targets
- `src/config/experiment.yaml`: trial count, temperatures, tag formats, metric selection, output paths

---

## 8 Document Index

| Document | Content |
|----------|---------|
| [thesis_extended_structure.md](thesis_extended_structure.md) | Canonical thesis outline with visualization markers |
| [thesis_models.md](thesis_models.md) | Current LLM role assignments and evaluation targets |
| [SOTA_LLMs.md](SOTA_LLMs.md) | Living reference for current model landscape (overrides LLM training data) |
| [TODO.md](TODO.md) | Current action items and blockers |
| [architecture_plan.md](architecture_plan.md) | Full project file tree |
| [strategy_taxonomy_evolution.md](strategy_taxonomy_evolution.md) | Taxonomy journey: 8 → 6 → 7 → 6 categories |
| [plan_mechanism_analysis.md](plan_mechanism_analysis.md) | Plan as declared intent, fused vs. chained comparison |
| [alignment_approach_analysis.md](alignment_approach_analysis.md) | LLM judge vs. NLI rationale, ternary scoring design |
| [bertscore_model_selection.md](bertscore_model_selection.md) | DeBERTa-XLarge-MNLI selection rationale |
| [citations.md](citations.md) | Literature grounding: where each source fits, Zotero keys, integration notes |
| [STYLE.md](STYLE.md) | Writing style rules for all markdown files |
