# Experiment Analysis

> Key findings from 360 runs (12 models x 6 vignettes x 5 temperatures x 20 trials = 7,200 trials).
> Data: `experiments/latest/` plus `batch_20260709_mistral_medium35`, `batch_20260728_command_a`, and `batch_20260728_gpt54_native`, aggregated in `stats/data/experiment_runs.csv`.
> Generated 2026-03-24, revised 2026-07-28 (12-model set, GPT-5.4 native re-collection).
> The superseded GPT-5.4 runs are excluded from all analyses and preserved in `experiments/runs/batch_20260321_gpt54_openrouter_default_sampling/` (see finding 10).

## Models tested

| Group | Model | Size | Active params |
|---|---|---|---|
| EU-sovereign | Mistral Small 3.2 | 24B dense | 24B |
| EU-sovereign | Mistral Small 4 | 119B MoE | 6.5B |
| EU-sovereign | Mistral Medium 3.5 | 128B dense | 128B |
| EU-sovereign | Mistral Large 3 | 675B MoE | 41B |
| Open-weight | Qwen 3.5 27B | 27B dense | 27B |
| Open-weight | Qwen 3.5 122B | 122B MoE | 10B |
| Open-weight | Qwen 3.5 397B | 397B MoE | 17B |
| Open-weight | OLMo 3.1 32B | 32B dense | 32B |
| Open-weight | Llama 3.3 70B | 70B dense | 70B |
| Open-weight | Command A | 111B dense | 111B |
| Proprietary | GPT-5.4 | closed | closed |
| Proprietary | Claude Sonnet 4.6 | closed | closed |

All models via OpenRouter except GPT-5.4 (native OpenAI API, finding 10). Per-run collection dates live in the `run_date` column of the CSV. Newer collections pin one serving provider per model (`require_parameters: true`, provider logged per trial), the original ones used OpenRouter default routing.

## Temperature scale

[0.0, 0.075, 0.15, 0.3, 0.6]. All models tested at all 5 points. T=0.075 added after initial 4-point run revealed Mistral peaks between 0.0 and 0.15.

## Jaccard (strategy consistency, median) by model and temperature

| Model | T=0.0 | T=0.075 | T=0.15 | T=0.3 | T=0.6 |
|---|---|---|---|---|---|
| Mistral Small 3.2 (24B) | 0.967 | 1.000 | 0.967 | 0.967 | 0.872 |
| Mistral Small 4 (119B MoE) | 0.746 | 0.874 | 0.935 | 0.646 | 0.625 |
| Mistral Medium 3.5 (128B) | 1.000 | 1.000 | 1.000 | 1.000 | 0.967 |
| Mistral Large 3 (675B MoE) | 0.772 | 0.709 | 0.877 | 0.775 | 0.712 |
| Qwen 3.5 27B | 0.760 | 0.754 | 0.768 | 0.595 | 0.518 |
| Qwen 3.5 122B | 1.000 | 1.000 | 0.967 | 0.853 | 0.730 |
| Qwen 3.5 397B | 0.799 | 0.737 | 0.775 | 0.642 | 0.626 |
| OLMo 3.1 32B | 1.000 | 1.000 | 0.911 | 0.911 | 0.746 |
| Llama 3.3 70B | 0.705 | 0.730 | 0.732 | 0.668 | 0.597 |
| Command A (111B) | 0.911 | 0.793 | 0.950 | 0.714 | 0.724 |
| GPT-5.4 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Claude Sonnet 4.6 | 0.868 | 0.779 | 1.000 | 0.854 | 0.933 |

## Statistical tests

All tests exploratory. Effect sizes reported alongside p-values. Pairwise contrasts use Mann-Whitney U with Bonferroni over C(12,2) = 66 pairs.

### Temperature effect (pooled)

- Jaccard vs temperature: rho=-0.215, p<0.001. Higher temperature reduces strategy consistency.
- BERTScore vs temperature: rho=-0.489, p<0.001. Stronger effect on semantic wording than strategy choice.
- Alignment vs temperature: rho=-0.069, p=0.193. **Not significant.** Models implement chosen strategies equally well regardless of temperature.

### Temperature effect (per-model Spearman, Jaccard)

| Model | rho | p | Significant? |
|---|---|---|---|
| Mistral Small 3.2 | -0.232 | 0.217 | No |
| Mistral Small 4 | -0.216 | 0.251 | No |
| Mistral Medium 3.5 | -0.306 | 0.100 | No |
| Mistral Large 3 | -0.081 | 0.672 | No |
| Qwen 3.5 27B | -0.485 | 0.007 | Yes |
| Qwen 3.5 122B | -0.560 | 0.001 | Yes |
| Qwen 3.5 397B | -0.150 | 0.427 | No |
| OLMo 3.1 32B | -0.650 | <0.001 | Yes |
| Llama 3.3 70B | -0.161 | 0.394 | No |
| Command A | -0.251 | 0.180 | No |
| GPT-5.4 | +0.085 | 0.655 | No |
| Claude Sonnet 4.6 | +0.028 | 0.882 | No |

Temperature-sensitive: OLMo, Qwen 27B, Qwen 122B.
Temperature-robust: all Mistrals, Llama, Qwen 397B, Command A, GPT-5.4, Sonnet.

### Model differences (Kruskal-Wallis)

- Jaccard: H(11)=104.5, p<0.001, eta2=0.291. 20 of 66 pairs significant.
- BERTScore: H(11)=92.0, p<0.001, eta2=0.256. 19 of 66 pairs significant.
- Alignment: H(11)=155.8, p<0.001, eta2=0.434. 34 of 66 pairs significant.

### Vignette effect

- Jaccard: H(5)=6.3, p=0.280, eta2=0.018. **Not significant.**
- BERTScore: H(5)=11.0, p=0.052, eta2=0.031. **Not significant** (boundary).

The earlier 10-model analysis had shown a significant vignette effect (p=0.007). With the corrected GPT-5.4 data and two added models it disappears: stability is a model property, not a patient-difficulty property.

### Metric correlations

- Jaccard vs BERTScore: rho=0.552, p<0.001. Moderate. Related but distinct dimensions.
- Jaccard vs Alignment: rho=0.293, p<0.001. Weak.
- BERTScore vs Alignment: rho=0.403, p<0.001. Weak-moderate.

## Key findings

### 1. Four stability tiers

1. **Decision-deterministic ceiling:** GPT-5.4, Mistral Medium 3.5. Median J=1.000 at essentially every temperature. GPT-5.4 produces a single strategy set across all 20 trials in 28 of its 30 conditions (modal-set agreement 0.993). Medium 3.5 matches it at the median with a broader repertoire.
2. **Temperature-robust:** Sonnet 4.6, Mistral family, Llama, Qwen 397B, Command A. No statistically significant degradation. Sonnet varies stochastically (2-3 distinct strategy sets in about half its conditions, including at T=0.0) but without temperature dependence.
3. **Temperature-sensitive:** OLMo, Qwen 122B. High peak at T=0.0, significant degradation as temperature increases.
4. **Consistently variable:** Qwen 27B. Lower baseline, significant degradation. Smallest model in the set.

### 2. T=0.0 is not optimal for all models

Ten of twelve models reach their best mean Jaccard at a non-zero temperature. Mistral Small 4 rises from 0.777 at T=0.0 to 0.881 at T=0.15, Mistral Large from 0.796 to 0.848 at T=0.15, Llama from 0.719 to 0.775 at T=0.075, Command A from 0.832 to 0.861 at T=0.15. A tiny amount of sampling variance produces more consistent strategy selection than pure greedy decoding.

### 3. The optimum sits at 0.075-0.15, not at one universal point

Five models peak at T=0.075 (GPT-5.4, Medium 3.5, Small 3.2, Qwen 122B, Llama) and five at T=0.15 (Command A, Mistral Large, Small 4, Qwen 397B, Sonnet). Only OLMo and Qwen 27B peak at T=0.0. The Mistral family peaks exactly in the region of its vendor default (0.15).

### 4. Alignment is temperature-independent

Models do not get worse at implementing strategies as temperature rises. They pick *different* strategies more often (lower Jaccard) but implement whichever strategies they pick equally well (stable alignment). The instability is in *decision-making*, not *execution*.

### 5. Vignette difficulty does not matter (revised)

The vignette effect is not significant in the 12-model set (Jaccard p=0.280, BERTScore p=0.052). The significant effect in the earlier 10-model analysis (p=0.007) did not survive the corrected GPT-5.4 data and the two additions. Median Jaccard spans a narrow 0.818 (cooperative) to 1.000 (anxious, skeptic). Per-vignette heatmaps stay useful for spotting where a specific model breaks down.

### 6. BERTScore is insensitive to plan-level instability

BERTScore correlates with Jaccard (rho=0.552) but measures a different, shallower dimension. The slice depth analysis confirms this: across conversation depths, Jaccard varies visibly (deeper slices anchor strategy choice) while BERTScore stays flat. The model produces semantically similar therapeutic text regardless of which strategies it picks. Swapping "confrontation" for "cognitive reframe" changes the plan but not the response surface enough for BERTScore to detect it.

This means BERTScore captures response *style* consistency, not decision *content* consistency. It serves as a sanity check (if BERTScore were low, the model would be generating erratic text) but does not distinguish between clinically different plans. The real signal for therapeutic stability lives in Jaccard (strategy decisions) and Alignment (plan-response coherence).

### 7. Seed does not produce deterministic output

A seed experiment tested whether fixing the API seed parameter eliminates variance. Mistral Large 3 was run with seed=42 for all 20 trials at T=0.0, T=0.075, and T=0.15 across all 6 vignettes (18 runs total). Results: Jaccard ranged 0.71-0.78, comparable to and sometimes worse than the unseeded main experiment runs. Deltas were small and inconsistent in direction (T=0.0: -0.089, T=0.075: +0.008, T=0.15: -0.093). BERTScore and Alignment showed no meaningful difference either.

The OpenRouter API (Mistral endpoint) does not honor the seed parameter for reproducibility. The variance in strategy selection is inherent to the model's inference process and cannot be mitigated by fixing the random seed. Data in `experiments/runs/seed_batch/`.

### 8. Conversation depth anchors strategy choice (slice depth analysis)

Mistral Large 3 was tested across 5 conversation depths (slices 1-5) at T=0.075 and T=0.15, 20 trials each (60 runs in `experiments/runs/slice_batch/`). Pooled Jaccard vs depth: rho=+0.339, p=0.008. Deeper slices show higher stability because prior therapeutic moves constrain the strategy space. BERTScore stays flat across depths, confirming it is insensitive to plan-level changes (see finding 6).

Slice 2 (used in the main experiment) is the most discriminating measurement point: early enough that the model has genuine decision freedom, late enough that there is sufficient therapeutic context. Later slices (4-5) approach Jaccard=1.0 due to anchoring, making them less useful for distinguishing between models or conditions.

### 9. N=20 trials is the minimum for stable rankings

The experiment was initially run at N=10 and extended to N=20. Key differences:
- Run-to-run Jaccard variance at N=10 was 0.15-0.20, with signal-to-noise ratio only 2.3x. At N=20, SD dropped by ~30%.
- Middle-tier model rankings (positions 3-9) shuffled between N=10 and N=20, confirming tier-based interpretation is more appropriate than individual rankings.
- Some effects only emerged at N=20. For example, Sonnet appeared near-immune at N=10 (J=0.966) but the extra trials exposed genuine strategy variation.
- Top and bottom tiers (GPT/Sonnet at top, Qwen 27B at bottom) were stable across both sample sizes.

### 10. The original GPT-5.4 sweep never varied temperature (corrected)

OpenRouter does not forward the `temperature` parameter for GPT-5.1+ models. Requests return 200 and the parameter is silently dropped, so all 600 original GPT-5.4 trials ran at OpenAI default sampling regardless of the nominal temperature. The framework's own data exposed it: GPT-5.4 was the only model whose BERTScore profile was flat to within 0.006 across the sweep, while every genuine responder declined by 0.03-0.24.

The re-collection went through the native OpenAI API (same dated snapshot, `gpt-5.4-2026-03-05`, temperature at `reasoning_effort: none`, validated by the API rather than ignored). Result: the flat Jaccard profile is genuine. GPT-5.4 stays at mean J 0.970-1.000 across the sweep while its BERTScore now declines 0.770 to 0.745, the same decisions-stable-wording-drifts signature as Sonnet 4.6. Full evidence chain in `docs/SOTA_LLMs.md`, provider pinning policy in `src/config/models.yaml`.

### 11. Command A behaves like a normal mid-field model

Command A was added as a control for the dense-architecture expectation behind Medium 3.5 (reDreamAI's successor chat model, expected to be more stable because a dense forward pass has no expert routing to vary between runs). It combines one of the broadest strategy repertoires (47% top-two share) with mid-ranking consistency (median J 0.812), a genuine temperature response, and the standard low-temperature optimum at T=0.15. Its plan validity is the lowest in the set (98.3%, 10 empty-plan trials). Nothing about the pinned-provider collection route produces qualitatively different behaviour from the original cohort. Together with Medium 3.5 it forms a 111-128B dense pair sitting at opposite ends of the consistency ranking. The control result answers the expectation: dense weights alone do not confer stability, and parameter count does not predict it.

## Supplementary experiments

| Experiment | Runs | Data location |
|---|---|---|
| Seed batch (Mistral Large 3, seed=42) | 18 | `experiments/runs/seed_batch/` |
| Slice depth (Mistral Large 3, slices 1-5) | 60 | `experiments/runs/slice_batch/` |
| Original GPT-5.4 (default sampling, excluded) | 30 | `experiments/runs/batch_20260321_gpt54_openrouter_default_sampling/` |

## Figures

| Figure | Description | File |
|---|---|---|
| 5.2 | Jaccard 3-panel by model family | `fig_5_2_jaccard` |
| 5.2b | Modal-set agreement (all models) | `fig_5_2b_modal_agreement` |
| 5.3 | BERTScore 3-panel by model family | `fig_5_3_bertscore` |
| 5.4 | Vignette heatmaps per temperature | `fig_5_4_vignette_slice` |
| 5.5 | Strategy vs semantic consistency (scatter) | `fig_5_5_correlations` |
| 5.6a | Alignment by temperature + per model | `fig_5_6_alignment` |
| 5.6b | Per-temperature correlation panels | `fig_5_6_correlations_by_temp` |
| Seed | Seeded vs unseeded comparison | `fig_seed_comparison` |
| Depth | Slice depth metrics (Mistral Large 3) | `fig_slice_depth_metrics` |
| Depth-h | Slice depth heatmap | `fig_slice_depth_heatmap` |
| D.1 | Strategy distribution by model | `fig_5_1_strategy_distribution` |
| A.1 | Plan validity rate | `fig_A1_validity` |

All regenerated 2026-07-28 for the 12-model set, in `thesis/figures/` (copied to `paper/figures/`), PDF + PNG.
