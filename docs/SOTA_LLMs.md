# SOTA LLMs - Living Reference (July 2026)

> **Purpose:** This file overrides Claude's training data on model availability and performance.
> LLM landscape changes faster than any training cutoff can track. Before recommending or configuring models, **always check live sources first** rather than relying on built-in knowledge.
>
> **Last verified:** 2026-07-24
>
> **Live sources to check before any model decision:**
> - [Artificial Analysis Leaderboard](https://artificialanalysis.ai/leaderboards/models) - intelligence, speed, price rankings
> - [OpenRouter Models](https://openrouter.ai/models) - available models, pricing, free tier
> - [OpenRouter Rankings](https://openrouter.ai/rankings) - community usage rankings
> - [LM Arena](https://lmarena.ai/) - head-to-head human preference rankings

---

## How to Use This File

1. **Before any model selection discussion**, fetch the live sources above
2. **Cross-check** this file against live data, as it may already be outdated
3. **Update this file** whenever new information is confirmed
4. **Flag staleness**: if `Last verified` is more than 2 weeks old, re-research before trusting the content below

---

## Recent News (July 2026)

Verified 2026-07-24 against Artificial Analysis, OpenRouter, vendor docs, and HuggingFace model cards. The March 2026 sections below are kept as a historical snapshot matching the main data collection.

### Frontier Closed Models

- **GPT-5.6 family** (limited preview Jun 26, public Jul 9): three tiers named Sol, Terra, Luna (most to least capable). Sol is the flagship. OpenRouter `openai/gpt-5.6-sol`, $5.00/$30.00 per M, 1M context. Supports `reasoning_effort: none` but the default changed to `medium` (GPT-5.4 defaulted to none), so `none` must be set explicitly. AA Intelligence Index 59 (max effort). Temperature: **stripped via OpenRouter** (same as GPT-5.4, proven empirically 2026-07-24). Native API support at effort none is likely (the documented GPT-5.1 through 5.4 policy) but the 5.6 docs no longer carry the explicit parameter-compatibility sentence and no community confirmation exists yet. One probe with a real OpenAI key settles it
- **Claude Sonnet 5** (Jun 30): `anthropic/claude-sonnet-5`, $2/$10 intro until Aug 31 then $3/$15, 1M context. Adaptive thinking on by default, can be disabled. **Returns HTTP 400 for any non-default `temperature`, `top_p`, or `top_k`.** Unusable for temperature-sweep protocols. New tokenizer (~30% more tokens for same text)
- **Claude Fable 5** (Jun 9, redeployed Jul 1 after export-control suspension): Anthropic's actual frontier, "Mythos-class" above Opus. $10/$50 per M. Thinking cannot be disabled. AA Index 60, currently rank 1. No Opus 5 exists, top Opus remains Opus 4.8
- **AA top 5 (Jul 24):** Claude Fable 5 (60), GPT-5.6 Sol max (59), GPT-5.6 Sol xhigh (58), Kimi K3 (57, weights unreleased), GPT-5.6 Sol high / Opus 4.8 max (56)
- **GPT-5.4 and Sonnet 4.6 both remain live on OpenRouter** with no deprecation notice. Existing March data stays reproducible for now

### Open-Weight Models

- **GLM 5.2** (Z.ai, mid-Jun): current open-weight leader on AA (Index 51). MoE, ~744B total (some sources say 753B) / ~40B active, MIT, 1M context. OpenRouter `z-ai/glm-5.2`, ~$0.77/$2.42 per M. Has a genuine non-thinking mode via `enable_thinking: false` (vLLM) or `thinking: {type: disabled}` (z.ai API). Whether the OpenRouter reasoning toggle maps cleanly to non-thinking mode is unverified, smoke test needed
- **Kimi K3** (Moonshot, announced Jul 17): 2.7-2.8T MoE, AA ~57 per secondary reporting. **Open weights due Jul 27.** Will likely displace GLM 5.2 as top open-weight model
- **Kimi K2.6** (Apr 20, 1T/32B active) superseded K2.5. K2.7-Code (Jun 12) is coding-focused
- **Qwen family moved closed at the top:** Qwen 3.6-Plus (Apr 2), 3.7-Max, and 3.8-Max-Preview (Jul 19) are API-only. The only open 3.6 release is Qwen3.6-27B (Apr 22, Apache 2.0). **Qwen 3.5 397B/122B remain the largest open Qwen checkpoints**
- **Other new open-weight entries on AA:** MiniMax-M3 (44), DeepSeek V4 Pro (44, 1.6T/49B), MiMo-V2.5-Pro (Xiaomi, 42, 1T/42B), Inkling (Thinking Machines, 41), Nemotron 3 Ultra 550B (38)
- **Dense models above ~70B are nearly extinct:** every 2026 flagship open model above ~100B is MoE. The only general-purpose dense instruct models in the 70-150B class with hosted inference are Mistral Medium 3.5 (128B dense, modified MIT, `mistralai/mistral-medium-3-5`, $1.50/$7.50, sole-provider) and **Cohere Command A** (111B dense, Mar 2025, CC-BY-NC weights, `cohere/command-a`, $2.50/$10.00, 256K context, served solely by Cohere, no reasoning mode at all). Devstral 2 123B dense is coding-specialised and being folded into Medium 3.5. K2-V2 70B still has no hosted inference. Apertus 70B (Swiss, dense, Apache 2.0) is EU-sovereign but not on OpenRouter

### Mistral Ecosystem

- **Mistral Medium 3.5** (Apr 29 or 30 depending on source): 128B dense per HF card, modified MIT, 262K context on OpenRouter. Consolidates and replaces Magistral and Devstral 2. Official replacement for deprecated `mistral-large-2411`. `reasoning_effort` takes only "none" or "high", default "none"
- No Large 3.x update since Large 3 2512. A new sparse MoE family entered early access in July per press coverage, unverified, not on OpenRouter

### Gemini Lineup and Judge Considerations

- **Gemini 3.6 Flash** (GA Jul 21): stable ID `gemini-3.6-flash`, $1.50/$7.50 per M. AA Index 50, identical to 3.5 Flash (speed doubled, no intelligence gain). **Sampling parameters (`temperature`, `top_p`, `top_k`) are deprecated and ignored as of Jul 21** for 3.6 Flash, 3.5 Flash-Lite, and all future Gemini models
- **`gemini-3-flash-preview`** (current judge): still live but on Google's deprecations page, "no shutdown date announced". Never got a stable GA ID and is two Flash generations behind. Sibling previews died within months of their successors (3-pro-preview shut down Mar 9, 3.1-flash-lite-preview May 25)
- **`gemini-3.1-pro-preview`** (fallback judge): still the newest callable Pro. Gemini 3.5 Pro is in partner testing, not released. Gemini 4 only teased
- Google's bulk-scoring recommendation: `gemini-3.5-flash-lite` ($0.30/$2.50, AA 36) for high-volume extraction, `gemini-3.6-flash` as the quality tier

### Protocol-Relevant Trend

Frontier vendors are removing user control over sampling. Claude Sonnet 5 and Opus 4.7+ reject non-default temperature outright (Anthropic docs state the restriction unconditionally, with no thinking-disabled exemption). Gemini 3.6+ ignores the parameter. OpenAI GPT-5.x models expose no temperature at all through OpenRouter. Temperature-sweep stability protocols can no longer run on these models. Stability evaluation of closed frontier models increasingly means accepting vendor-controlled decoding.

### Sampling-Parameter Support via OpenRouter (probed empirically 2026-07-24)

Direct API probes with `provider: {require_parameters: true}`. Without that flag OpenRouter returns 200 and silently drops parameters the endpoint does not support, so a 200 alone proves nothing. **All future runs must set `require_parameters: true` and log the serving provider per trial.**

| Model | temperature via OpenRouter | Evidence |
|---|---|---|
| `anthropic/claude-sonnet-5` | **No** (404 with require_parameters, not in supported_parameters) | Plain requests 200 because OpenRouter drops the param |
| `openai/gpt-5.6-sol` | **No** (404 with require_parameters) | Same silent-drop behaviour |
| `openai/gpt-5.4` | **No, confirmed stripped, also during the March 2026 collection** | Four-way evidence. (1) OpenAI's own archived docs (2026-03-18) say GPT-5.4 accepts temperature only at `reasoning_effort: none`, so the model itself supported it. (2) Wayback snapshots of the OpenRouter models API show temperature absent from gpt-5.4's supported_parameters in every snapshot from launch through 2026-03-21 (mid-collection) to today. (3) Strip behaviour proven empirically: temperature plus `effort: high` returns 200 from provider OpenAI, a combination OpenAI natively rejects, so OpenRouter removes the field before forwarding. (4) The March data shows the corresponding signature: BERTScore flat within 0.006 across all five temperatures while Sonnet 4.6 declines monotonically 0.844 to 0.743. Conclusion: the GPT-5.4 sweep never varied temperature, all 150 runs used OpenAI default sampling. A genuine sweep remains possible via the native OpenAI API at `reasoning_effort: none` |
| `anthropic/claude-sonnet-4.6` | **Yes** (200 with require_parameters, provider Anthropic) | Last sweepable Anthropic Sonnet. Temperature or top_p, not both |
| `z-ai/glm-5.2` | **Yes** (200 with require_parameters) | Non-thinking mode also confirmed working via OpenRouter reasoning toggle |
| `cohere/command-a` | **Yes** (200 with require_parameters, provider Cohere) | Documented range 0 to 1, default 0.3 |
| `mistralai/mistral-medium-3-5` | Yes (listed in supported_parameters) | |

The other ten study models are unaffected: the 2026-03-23 registry snapshot (mid-collection) lists temperature for all of them, every current provider of the multi-provider models supports it, and each shows a genuine BERTScore temperature response in the March data (+0.032 to +0.242 from t=0 to t=0.6, versus +0.001 for GPT-5.4). Sonnet 4.6's flat Jaccard is genuine robustness, not a dropped parameter: its BERTScore declines cleanly.

Also discovered: **`allenai/olmo-3.1-32b-instruct` is delisted from OpenRouter.** Only `allenai/olmo-3-32b-think` remains. The study's OLMo data cannot be re-collected or extended through OpenRouter.

---

## Recent News (March 2026)

### Releases in Last 2-4 Weeks

- **GPT-5.4** (Mar 5): Combines GPT-5.3-Codex coding strength with improved reasoning and computer use. 83% on GDPval (professional knowledge work). Replaces GPT-5.2 as frontier ceiling. Variants: GPT-5.4 Thinking, GPT-5.4 Pro. 1M context. $2.50/$15.00 per M tokens (cached input: $0.25/M)
- **Gemini 3.1 Flash Lite** (Mar 3): Cheapest Gemini model. $0.25/$1.50 per M tokens. 2.5x faster TTFT than 2.5 Flash. 86.9% GPQA Diamond
- **Gemini 3 Flash** (~Feb 2026): Default Gemini app model. Outperforms 2.5 Pro at 3x speed. $0.50/$3.00 per M tokens
- **DeepSeek V4** (early Mar): ~1T total / ~32B active MoE. 1M context. Native multimodal (vision + audio + text). Optimized for Huawei Ascend chips. Apache 2.0. Not EU-sovereign. Active EU GDPR issues persist
- **GPT-5.3-Codex** (Feb 24): 400K context. Industry-leading coding. $1.75/$14.00 per M tokens
- **Gemini 3.1 Pro** (Feb 19): Google's latest flagship. 77.1% ARC-AGI-2, 1M context, 65K output tokens. Gemini 3 Pro Preview shut down Mar 9
- **Qwen 3.5** (Feb 16-24): Full family released. 397B-A17B flagship (512 experts, 10+1 active, Gated DeltaNet hybrid), 122B-A10B (256 experts), 35B-A3B, 27B dense. All 262K-1M context. Apache 2.0. Native multimodal
- **MiniMax M2.5** (Feb 12): 230B MoE, 10B active. Lightning Attention. 205K context. 80.2% SWE-Bench Verified. Modified MIT license. Chinese origin (Shanghai). Available on OpenRouter. Extremely cheap ($0.15/$1.20 per M tokens for standard variant)
- **GLM-5** (Feb 11): 744B MoE, 40B active, 256 experts. 205K context, 128K output. 77.8% SWE-bench, 92.7% AIME 2026. Trained entirely on Huawei Ascend (zero NVIDIA dependency). MIT license. Chinese origin (Zhipu AI / Z.ai). Available on OpenRouter
- **GPT-5.2** (Feb 2026): 400K context, 100% AIME 2025, hallucination rate 6.2%. Superseded by GPT-5.4
- **Kimi K2.5** (Jan 27): 1T MoE, 32B active, 384 experts. 256K context. Native multimodal (MoonViT 400M vision encoder). Agent swarm mode (up to 100 sub-agents). Modified MIT license. Chinese origin (Moonshot AI). Available on OpenRouter
- **Guide Labs Steerling-8B** (Feb 23): Every output token traceable to training data origins. Interesting for clinical interpretability arguments
- **Inception Mercury 2** (Feb 24): First reasoning diffusion LLM (dLLM). 1,000 tok/s. Not relevant for stability evaluation
- **Mistral Small 4** (Mar 16): 119B MoE (6.5B active, 128 experts, 4 active per token). Multimodal. Unifies Small/Magistral/Pixtral/Devstral lines. Configurable `reasoning_effort`. 256K context. Apache 2.0. $0.15/$0.60 per M tokens. On OpenRouter (`mistralai/mistral-small-2603`)
- **NVIDIA Nemotron 3 Super** (Mar 11): 120B MoE (12B active, 512 routed + 1 shared expert, 22 active per token). Hybrid Mamba-Transformer LatentMoE. 1M context. Nemotron Open license (permissive, not Apache 2.0). On OpenRouter (free tier available). Nemotron 3 Ultra (~500B) expected H1 2026
- **NVIDIA Nemotron 3 Nano** (available): 3.2B active / 31.6B total, hybrid Mamba-Transformer MoE, 1M context

### Mistral Ecosystem Updates

- **Mistral acquired Koyeb** (Feb 17): Paris-based cloud startup (ex-Scaleway founders). Signals full-stack EU-sovereign AI cloud ambitions
- **Mistral Compute** (announced Jun 2025) + Koyeb = building European inference infrastructure independent of US cloud
- **Mistral Small 4** (Mar 16): 119B MoE replaces Small 3.x. Unifies instruct, reasoning, multimodal, and coding into one model. 128 experts (4 active, 6.5B active params). Configurable `reasoning_effort` parameter. Apache 2.0. $0.15/$0.60 per M tokens
- **Ministral 3** (Dec 2025): 3B/8B/14B dense models, Apache 2.0. The 14B reasoning variant scores 85% on AIME '25
- **Devstral 2** (Dec 2025): 123B dense for coding, 256K context. Devstral Small 2: 24B, Apache 2.0

### OpenAI GPT-4.1 Family (Still API-Available)

GPT-4.1 was released Apr 2025 and retired from ChatGPT Feb 13, 2026, but all three variants remain available via API and OpenRouter. The family was specifically optimized for instruction following and structured outputs.

- **GPT-4.1**: $2.00/$8.00 per M tokens. 1M context. Strong instruction following
- **GPT-4.1 mini**: $0.40/$1.60 per M tokens. 1M context. Mid-tier
- **GPT-4.1 nano**: $0.10/$0.40 per M tokens. 1M context. Cheapest quality OpenAI model

### EU Sovereignty Developments

- **OpenEuroLLM**: 37.4M EUR budget (20M from EU Digital Europe Programme). 20 European institutions. First versions mid-2026, final by 2028. Covers all 24 EU languages. AI Act compliant from the ground up
- **EU AI Act Article 53** enforcement begins Aug 2026: training data summaries mandatory for all GPAI providers
- **Mistral Large 3** remains the only frontier-class EU-sovereign open-weight model currently available

---

## EU Legality and Training Data Provenance

Legal usability and data provenance vary across models. Relevant for EU deployment and research transparency.

### EU Legality by Model

| Model | EU-Legal? | Training Data Transparency | Risk Notes |
|---|---|---|---|
| **Mistral Large 3** | Yes (EU company) | Undisclosed, but EU-origin likely compliant | Lowest risk. Apache 2.0, 675B MoE |
| **Mistral Small 3.2** | Yes (EU company) | Undisclosed, but EU-origin likely compliant | Low risk. Apache 2.0, 24B dense |
| **K2-V2 Instruct** | Yes (Apache 2.0) | **Fully open** - 12T tokens from TxT360, all mixtures published | Lowest risk. Best provenance story. No hosted inference |
| **OLMo 3.1 Instruct** | Yes (Apache 2.0) | **Fully open** - 9.3T token Dolma 3 corpus, all sources documented | Lowest risk. Allen AI nonprofit |
| **Qwen 3 / 3.5** | Yes if self-hosted (Apache 2.0) | High-level disclosure (36T tokens), but no detailed source list. No EU GDPR representative | Medium. Chinese origin, opaque data details |
| **Llama 3.3 70B** | Yes (text-only, EU ban is multimodal-only) | Undisclosed | Medium. US company, opaque data |
| **Llama 4 (all)** | **No** - entire family is multimodal, EU excluded from license | Undisclosed | capabilities low/ benchmarks faked | Blocked. Do not use |
| **DeepSeek R1/V3/V4** | Legally yes if self-hosted (MIT) | Undisclosed | High risk. Active GDPR enforcement across EU. Bad optics for therapy |
| **Gemma 3 27B** | Yes (open weights) | Undisclosed | Low-medium. Google has EU data processing agreements |
| **GLM-5** | Yes if self-hosted (MIT) | Undisclosed (28.5T tokens) | High risk. Chinese origin (Zhipu AI). No EU GDPR representative. Same risk profile as DeepSeek |
| **Kimi K2.5** | Yes if self-hosted (Modified MIT) | Undisclosed (15T tokens, multimodal) | High risk. Chinese origin (Moonshot AI). Native multimodal complicates EU licensing. Same risk profile as DeepSeek |
| **MiniMax M2.5** | Yes if self-hosted (Modified MIT) | Undisclosed | High risk. Chinese origin (MiniMax, Shanghai). No EU GDPR representative |
| **GPT-5 / 5.2 / 5.4** | Yes (API, OpenAI has EU DPA) | Closed | Low. Standard API use, no self-hosting |
| **GPT-oss-120B** | Yes (Apache 2.0) | Partially open | Low. OpenAI's first open-weight model |

### Key Regulations

- **EU AI Act Article 53**: All GPAI providers must publish training data summaries and demonstrate copyright compliance (enforcement from Aug 2026)
- **Llama 4 EU ban**: Meta excluded EU from all multimodal Llama models due to AI Act concerns. Text-only Llama 3.3 is unaffected
- **DeepSeek**: Italian, German, and Belgian DPAs have launched investigations. Multiple EU countries restricting deployment in early 2026

---

## EU-Sovereign Options (Self-Hostable in EU)

| Model | Params | Provider | Notes |
|---|---|---|---|
| **Mistral Large 3** | 675B (41B active, MoE) | OpenRouter / Mistral API / Scaleway | Released Dec 2025. Apache 2.0. 256K context |
| **Mistral Medium 3.1** | undisclosed | OpenRouter / Mistral API | EU-origin, closed weights. Mistral vertical scaling |
| **Mistral Small 4** | 119B (6.5B active, MoE) | OpenRouter / Mistral API | Released Mar 2026. Apache 2.0. 256K context. Replaces Small 3.x |
| **Mistral Small 3.2** | 24B dense | Scaleway (EU) | Apache 2.0. Superseded by Small 4 |
| **Ministral 3 14B** | 14B dense | Mistral API | Apache 2.0. Reasoning variant: 85% AIME '25. Edge deployment |
| **OpenEuroLLM** | TBD | EU consortium | First versions mid-2026. 24 EU languages |

**Sovereignty narrative strengthened** by Mistral's Feb 2026 Koyeb acquisition (EU cloud infrastructure) and Mistral Compute platform. Mistral is building a full-stack EU-sovereign AI cloud.

---

## Best Non-Reasoning Instruct Models (Mid-to-Large)

Non-reasoning, instruction-following models in the mid-to-large size range.

### Tier 1: Fully Open (weights + training data + code)

Best for academic defensibility. You can cite exactly what these were trained on.

| Model | Size | Origin | Performance | License |
|---|---|---|---|---|
| **K2-V2 Instruct** | 70B dense | MBZUAI (UAE) / LLM360 | Rivals Qwen 2.5 72B, approaches Qwen 3 235B. Strong on GPQA-Diamond. No hosted inference | Fully open (LLM360) |
| **OLMo 3.1 32B Instruct** | 32B | Allen AI (US nonprofit) | Competitive with Qwen 3 32B, beats Gemma 3 and Llama 3.1 at scale. 5+ point gains over OLMo 3.0 on AIME/IFEval | Apache 2.0 |

### Tier 2: EU-Origin (sovereignty + Apache 2.0, opaque training data)

| Model | Size | Origin | Performance | License |
|---|---|---|---|---|
| **Mistral Large 3** | 675B MoE (41B active) | Mistral (France) | #2 open model on LMArena. Strong multilingual, 256K context | Apache 2.0 |
| **Mistral Small 4** | 119B MoE (6.5B active) | Mistral (France) | NEW (Mar 2026). Replaces Small 3.x. 128 experts. Multimodal. Configurable reasoning. 256K context. $0.15/$0.60 | Apache 2.0 |
| **Mistral Small 3.2** | 24B dense | Mistral (France) | Superseded by Small 4. Comparable to 70B models despite 24B size | Apache 2.0 |

### Tier 3: Open Weights (good license, opaque data, non-EU origin)

| Model | Size | Origin | Performance | License |
|---|---|---|---|---|
| **Qwen 3.5 397B-A17B** | 397B MoE (17B active) | Alibaba (China) | NEW (Feb 2026). 512 experts (10+1 active), Gated DeltaNet hybrid. 262K-1M context. Multimodal. On OpenRouter ($0.39/$2.34) | Apache 2.0 |
| **Qwen 3.5 27B** | 27B dense | Alibaba (China) | NEW (Feb 2026). 800K+ context. Successor to Qwen 3 32B | Apache 2.0 |
| **Qwen 3.5 35B-A3B** | 35B (3B active, MoE) | Alibaba (China) | NEW (Feb 2026). Exceeds 1M context on 32GB VRAM. Extremely efficient | Apache 2.0 |
| **GLM-5** | 744B MoE (40B active) | Zhipu AI / Z.ai (China) | NEW (Feb 2026). 205K context, 128K output. 77.8% SWE-bench, 92.7% AIME 2026. Trained on Huawei Ascend. On OpenRouter | MIT |
| **Kimi K2.5** | 1T MoE (32B active) | Moonshot AI (China) | NEW (Jan 2026). 256K context. Native multimodal. Agent swarm mode. On OpenRouter | Modified MIT |
| **MiniMax M2.5** | 230B MoE (10B active) | MiniMax (China) | NEW (Feb 2026). 205K context. Lightning Attention. 80.2% SWE-bench. Extremely cheap. On OpenRouter | Modified MIT |
| **Qwen 3 32B** | 32B dense | Alibaba (China) | Benchmark leader at 32B. Hybrid thinking modes. Superseded by Qwen 3.5 27B | Apache 2.0 |
| **Gemma 3 27B** | 27B | Google (US) | Same size class as Mistral Small. Good comparator | Open |
| **Qwen 3.5 122B-A10B** | 122B MoE (10B active) | Alibaba (China) | NEW (Feb 2026). 256 experts, Gated DeltaNet hybrid. 262K-1M context. On OpenRouter | Apache 2.0 |
| **Nemotron 3 Super** | 120B MoE (12B active) | NVIDIA (US) | NEW (Mar 2026). 512 experts, hybrid Mamba-Transformer LatentMoE. 1M context. On OpenRouter (free tier) | Nemotron Open |
| **Llama 3.3 70B** | 70B | Meta (US) | Text-only = EU-legal. Reliable 70B baseline | Meta license |
| **GPT-oss-120B** | 120B | OpenAI (US) | Apache 2.0. OpenAI's first open-weight model. Strong reasoning | Apache 2.0 |

---

## Frontier Closed Models (March 2026)

| Model | Provider | Tier | Notes |
|---|---|---|---|
| **GPT-5.4** | OpenAI | Top | (Mar 5). $2.50/$15.00. 1M context. 83% GDPval |
| **Gemini 3.1 Pro** | Google | Top | (Feb 19). 77.1% ARC-AGI-2, 1M context, 65K output. Thinking mode |
| **Claude Opus 4.6** | Anthropic | Top | Top reasoning performance. 1M context (beta). 128K output |
| **Claude Sonnet 4.6** | Anthropic | Top | Strong reasoning, faster than Opus. Best value at frontier tier |
| **GPT-5.2** | OpenAI | High | 400K context, 100% AIME 2025. Superseded by GPT-5.4 |
| **GPT-5** | OpenAI | High | Previous flagship, still strong |

---

## Free Models on OpenRouter (March 2026)

Rate limits: 20 RPM, 200 req/day without credits, higher with credits.

| Model | Params | Notes |
|---|---|---|
| **Llama 3.3 70B** | 70B | GPT-4 level, reliable baseline |
| **DeepSeek R1** | 671B MoE | Strong reasoning, Chinese-origin (high EU risk) |
| **DeepSeek V3** | 671B MoE | General purpose, same risk as R1 |
| **Qwen3 Coder 480B** | 480B MoE | Strongest free coding model, 262K context |
| **Mistral Small 3.1** | 24B | Slightly older than 3.2 |
| **Gemma 3 27B** | 27B | Google, open weights, 27B class |
| **NVIDIA Nemotron Nano 9B v2** | 9B | Fast, good for testing |
| **GLM-5** | 744B MoE (40B active) | Frontier-class open-weight. MIT license. Chinese-origin (high EU risk) |
| **MiniMax M2.5** | 230B MoE (10B active) | Extremely cheap. Modified MIT. Chinese-origin (high EU risk) |
| **Dolphin Mistral Venice 24B** | 24B | Uncensored Mistral fine-tune. Venice-hosted |

---

## Models to Watch

| Model | Why | Timeline |
|---|---|---|
| **DeepSeek V4** | ~1T MoE, ~32B active. Apache 2.0. Native multimodal | Released early Mar 2026, not yet on hosted API |
| **DeepSeek V3.2 structured output** | Currently json_object only, no json_schema | Ongoing |
| **NVIDIA Nemotron 3 Ultra** | ~500B. Hybrid Mamba-Transformer MoE. Super counterpart released Mar 11 | H1 2026 |
| **OpenEuroLLM** | EU institutional sovereign LLM | Mid-2026 |
| **K2-V2 hosted inference** | 70B fully open, no hosted inference yet | No timeline |
| **Guide Labs Steerling-8B** | Every output token traceable to training data origins. Interesting for interpretability | Available now, 8B only |

---

## Staleness Checklist

When updating this file, verify:
- [ ] Are the "free on OpenRouter" models still free?
- [ ] Have any new Mistral models been released?
- [ ] Has OpenEuroLLM shipped anything yet?
- [ ] Are the frontier model rankings still accurate?
- [ ] Have rate limits or pricing changed?
- [ ] Any new open-weight models in the 24-32B range?
- [ ] Is K2-V2 available on any hosted provider?
- [ ] Has DeepSeek V4 landed on hosted APIs?
- [ ] Any new EU-sovereign options beyond Mistral?
