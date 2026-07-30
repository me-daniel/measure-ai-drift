# LLM Run Recordings

> **Purpose:** per-collection record of the serving conditions behind every experiment batch: gateway, routing mode, provider pinning, quantisation. The bridge re-collection (2026-07-30) showed that serving infrastructure contributes materially to measured stability, so the serving state of each collection is part of the experiment record.
>
> **Last updated:** 2026-07-30

## Collection register

| Batch | Date | Models | Routing | Provider in trials | Judged |
|---|---|---|---|---|---|
| `batch_20260321_final` | 2026-03-21 to 03-24 | 9 original targets (270 runs) | OpenRouter default routing. No pinning in the config at collection time (verified from git history) | not recorded | yes |
| `batch_20260321_gpt54_openrouter_default_sampling` | 2026-03-21 | GPT-5.4 | OpenRouter default routing. Temperature silently dropped, batch excluded from all analyses | not recorded | yes |
| `batch_20260709_mistral_medium35` | 2026-07-09 | Mistral Medium 3.5 | OpenRouter. The current config pins Mistral, but the pinning state at collection time is not verifiable (config change uncommitted, no provider logged). OpenRouter lists only the first-party Mistral endpoint as of 2026-07-30, so serving was very likely single-provider either way | not recorded | yes |
| `batch_20260728_command_a` | 2026-07-28 | Command A | Pinned to Cohere (`allow_fallbacks: false`, `require_parameters: true`) | yes (Cohere) | yes |
| `batch_20260728_gpt54_native` | 2026-07-28 | GPT-5.4 | Direct OpenAI API, no gateway. Replaces the excluded March batch | n/a | yes |
| `batch_20260730_bridge_pinned` | 2026-07-30 | Mistral Large 3, Qwen 3.5 27B, Mistral Small 4, Qwen 3.5 122B | Pinned first-party (Mistral, Alibaba), `require_parameters: true` | yes (Mistral, Alibaba) | no (judge skipped, alignment columns empty) |

Trial-level provider logging exists from 2026-07-28 onward. Earlier trials carry no provider field, so the actual serving mix of the March cohort cannot be reconstructed.

The bridge batch is deliberately excluded from `stats/data/experiment_runs.csv` (the canonical 360 runs). It aggregates separately into `stats/data/bridge_runs.csv`.

## OpenRouter endpoint snapshot, 2026-07-30

Source: OpenRouter endpoints API (`https://openrouter.ai/api/v1/models/<id>/endpoints`), accessed 2026-07-30. Endpoint lists change over time. This snapshot does not describe what was available in March 2026.

| Model | Endpoints (provider, quantisation) |
|---|---|
| `mistralai/mistral-large-2512` | Mistral (unknown). Single endpoint |
| `mistralai/mistral-small-2603` | Mistral (unknown), Venice (fp8) |
| `mistralai/mistral-medium-3-5` | Mistral (unknown). Single endpoint |
| `qwen/qwen3.5-27b` | Alibaba (fp8), SiliconFlow (fp8), DeepInfra (fp8), AtlasCloud (fp8), Novita (bf16), Phala (unknown) |
| `qwen/qwen3.5-122b-a10b` | Alibaba (fp8), SiliconFlow (fp8), DeepInfra (fp4), AtlasCloud (fp8), Novita (bf16) |
| `cohere/command-a` | Cohere (unknown). Single endpoint |

Reading notes:

- Alibaba serves both Qwen models at fp8. The pinned bridge runs are therefore consistently quantised, and Qwen 3.5 27B is ceiling-stable under them. Quantisation as such does not cause the measured instability, variation between stacks does.
- The only bf16 (unquantised) Qwen host is Novita. Pinning trades native precision for first-party serving.
- Under default routing, Qwen 3.5 27B trials could bounce across six stacks (fp8, bf16, unknown) and Qwen 3.5 122B across five, including fp4 at DeepInfra.
- Mistral and Cohere do not disclose the precision of their first-party endpoints.
- Mistral Large 3 and Medium 3.5 list a single endpoint. If that was already true in March, the original Large 3 runs were de facto single-provider, and its bridge lift would be mostly temporal (four months of serving-stack changes) rather than routing variance.

## Why this matters

The bridge re-collection reruns models from the original cohort under pinned first-party serving on identical frozen histories. Qwen 3.5 27B moved from the bottom of the consistency ranking (pooled median Jaccard 0.727) to the ceiling (1.000 at every temperature) while its BERTScore still fell across the sweep, so part of what the original regime measured as model instability was serving variance. Details: paper Section 5.7 and [analysis.md](analysis.md).

Maintenance: snapshot the endpoint lists again at every new collection and append to the register above.
