# Temperature Sources and Verification

> Tracks the `therapy_temp` values in `src/config/models.yaml`.
> Each model's recommended therapy temperature follows the "lower bound" rule:
> when a vendor recommends a range, choose the lower end for clinical stability.
>
> **Verification status key:**
> - VERIFIED: value confirmed from primary source (API docs, generation_config.json)
> - NEEDS VERIFICATION: value from secondary source (Gemini analysis), primary source not yet checked or was inaccessible
> - DEFAULT: no vendor recommendation found, using platform default

---

## Mistral Large 3 -- therapy_temp: 0.15 [NEEDS VERIFICATION]

**Claimed source:** Mistral API Documentation (Sampling Parameters)

**What we found:**
- Mistral API docs say "recommend between 0.0 and 0.7" but the default is model-dependent ("call the `/models` endpoint to retrieve the appropriate value")
- No specific mention of 0.15 in the sampling docs at `docs.mistral.ai/capabilities/completion/sampling/`
- The Mistral Large 3 HuggingFace repo has no temperature in `generation_config.json`

**TODO:** Query the Mistral `/models` endpoint directly for `mistral-large-2512` to get the actual default. Alternatively, check the Mistral model card or La Plateforme dashboard.

**Lower bound rule applied:** 0.15 is at the low end of 0.0-0.7, consistent with the clinical stability rationale. If unverifiable, consider 0.3 as a safer midpoint.

---

## Qwen 3.5 27B -- therapy_temp: 0.6 [VERIFIED]

**Source:** HuggingFace generation_config.json
**URL:** https://huggingface.co/Qwen/Qwen3.5-27B/raw/main/generation_config.json
**Value in config:** `"temperature": 0.6`, `"top_k": 20`, `"top_p": 0.95`

**Notes:** 0.6 is the default for thinking mode. Non-thinking mode defaults to 0.7.
We run Qwen in non-thinking mode (`reasoning.effort: "none"`), so 0.7 could also be justified. 0.6 chosen as lower bound.

---

## OLMo 3.1 32B -- therapy_temp: 0.6 [VERIFIED]

**Source:** HuggingFace generation_config.json
**URL:** https://huggingface.co/allenai/OLMo-3.1-32B-Instruct/raw/main/generation_config.json
**Value in config:** `"temperature": 0.6`, `"top_p": 0.95`, `"max_new_tokens": 32768`

---

## Llama 3.3 70B -- therapy_temp: 0.6 [NEEDS VERIFICATION]

**Claimed source:** Meta Llama 3.1 HuggingFace generation_config.json

**What we found:**
- HuggingFace repo for Llama-3.3-70B-Instruct is gated (401), could not read generation_config.json directly
- Model card does not mention temperature, defers to llama-recipes repo
- The claimed source references Llama 3.1, not 3.3

**TODO:** Log into HuggingFace with gated access and check `meta-llama/Llama-3.3-70B-Instruct/raw/main/generation_config.json`. Alternatively check the llama-recipes repo for recommended generation parameters.

**Lower bound rule applied:** 0.6 is the lower end of the commonly cited 0.6-0.7 range for Llama instruct models.

---

## Command A -- therapy_temp: 0.3 [VERIFIED]

**Source:** Cohere Chat API v2 reference (docstring generated from the official API spec)
**URL:** https://docs.cohere.com/reference/chat (rendered), verifiable in plain text at https://raw.githubusercontent.com/cohere-ai/cohere-python/main/src/cohere/v2/client.py
**Value in spec:** `temperature` "Defaults to `0.3`."

**Notes:** Verified 2026-07-28. The API default is 0.3, so the lower bound rule
and the vendor default coincide. Cohere's prose guide (docs.cohere.com/docs/temperature)
suggests 1 as a generic "starting point" for creative use, which does not apply
to clinical stability. Command A has no reasoning mode, so no thinking-related
temperature caveats exist.

---

## DeepSeek V3.2 -- therapy_temp: 1.0 [VERIFIED]

**Source:** DeepSeek API Documentation
**URL:** https://api-docs.deepseek.com/quick_start/parameter_settings
**Default:** 1.0

**Vendor recommendations by use case (API scale):**
| Use case | API temp |
|----------|----------|
| Coding / Math | 0.0 |
| Data tasks | 1.0 |
| General conversation | 1.3 |
| Translation | 1.3 |
| Creative writing | 1.5 |

**Internal temperature scaling:** DeepSeek transforms API temperatures before they reach the model. API T=1.0 maps to internal T=0.3 (formula: T_api x 0.3). API T=1.3 maps to internal T=0.6 (formula: T_api - 0.7, for T_api > 1.0). This means the high-looking API values produce conservative internal behavior. Source for scaling formulas: TBD (not yet connected to primary documentation).

**Provider note:** OpenRouter routes to DeepSeek's own backend, so the internal temperature scaling is preserved. If using a different hosting provider that serves its own DeepSeek weights (e.g. Scaleway, Groq), the temperature scaling may not apply. For consistency, the experiment specifies `deepseek/deepseek-chat-v3-0324` via OpenRouter to ensure DeepSeek's backend handles the request.

**Notes:** 1.0 is the official default and maps to 0.3 internally, which falls in the clinical stability range. No "therapeutic" use case in their docs. Using the default as therapy_temp.

---

## GPT-5.4 -- therapy_temp: 0.7 [NEEDS VERIFICATION]

**Claimed source:** OpenAI API Reference: Chat Completions

**What we found:**
- OpenAI platform docs returned 403 (not publicly accessible without auth)
- Azure OpenAI reference (which mirrors OpenAI's spec for older models) says default is 1.0
- GPT-5.4 is a 2026 model, Azure docs may not reflect its specific defaults
- Requires `reasoning.effort: "none"` for temperature to take effect

**TODO:** Check OpenAI API reference while authenticated, or test empirically by sending a request with no temperature and checking the response metadata.

**Lower bound rule applied:** 0.7 is the standard OpenAI chat temperature. If actual default is 1.0, 0.7 is the lower-bound clinical choice.

---

## GPT-oss 120B -- therapy_temp: 1.0 [DEFAULT]

**Source:** HuggingFace generation_config.json
**URL:** https://huggingface.co/openai/gpt-oss-120b/raw/main/generation_config.json
**Value in config:** No temperature field. `"do_sample": true` only.

**Notes:** Without an explicit temperature, HuggingFace transformers defaults to 1.0. No vendor recommendation found. Using 1.0 as the platform default.

---

## Trinity Large -- therapy_temp: 0.8 [VERIFIED]

**Source:** HuggingFace generation_config.json
**URL:** https://huggingface.co/arcee-ai/Trinity-Large-Preview/raw/main/generation_config.json
**Value in config:** `"temperature": 0.8`, `"top_p": 0.8`

**Notes:** No separate therapeutic recommendation from Arcee AI. Blog post and tech report do not discuss temperature tuning. Using the generation_config default directly.

---

## Claude Sonnet 4.6 -- therapy_temp: 0.7 [VERIFIED]

**Source:** Anthropic API Documentation
**URL:** https://platform.claude.com/docs/en/api/messages

**Temperature range:** 0.0-1.0 (Claude's max is 1.0, not 2.0 like most other providers)
**Default:** 1.0
**Vendor guidance:** "Use temperature closer to 0.0 for analytical and multiple choice tasks. Use temperature closer to 1.0 for creative and generative tasks."

**Why included:** Anthropic's Claude models are character-trained for thoughtful, safety-aware interaction. Anthropic's model docs describe Claude 4 as "ideal for applications that require rich, human-like interactions." The character training emphasizes "open-mindedness and thoughtfulness" and "genuine curiosity about the views and values of the people it's talking with" (anthropic.com/research/claude-character). This makes Sonnet a relevant comparator for therapeutic stability testing.

**Pricing context:** $3/$15 per M tokens, close to GPT-5.4's $2.50/$15. Sonnet 4.6 is Anthropic's latest and most capable Sonnet-class model (training data cutoff Jan 2026), performing at near-Opus level while staying at the Sonnet price tier.

**Lower bound rule applied:** 0.7 chosen as midpoint of the 0.0-1.0 range. The vendor gives no specific "chat" recommendation beyond the analytical/creative split. 0.7 is a standard conversational temperature and matches GPT-5.4's therapy_temp.

**Note:** Claude max temperature is 1.0. Our scale caps at 1.0, so no compatibility issue. If the scale ever extends above 1.0, Sonnet would need to be capped.

---

## Gemini 3.1 Pro / Flash Lite (Judge) -- temperature: 1.0 [VERIFIED]

Gemini 3.1 Pro serves as the experiment judge and Flash Lite as the testing judge. Both are Gemini 3 series models and share the same temperature constraint. These are the only models in the experiment that run with thinking/reasoning enabled. All evaluation targets run in non-thinking mode.

### Standard temperatures

| Model | Default | Range | Role |
|-------|---------|-------|------|
| Gemini 3.1 Pro Preview | 1.0 | 0.0-2.0 | Experiment judge |
| Gemini 3.1 Flash Lite Preview | 1.0 | 0.0-2.0 | Testing judge |

### Source 1: Official architectural guidelines

**Google AI for Developers (2026). Gemini 3 Developer Guide.**
**URL:** https://ai.google.dev/gemini-api/docs/text-generation

> "For all Gemini 3 models, we strongly recommend keeping the temperature parameter at its default value of 1.0. [...] Gemini 3's reasoning capabilities are optimized for the default setting. Changing the temperature (setting it below 1.0) may lead to unexpected behavior, such as looping or degraded performance."

This is the primary technical justification for using T=1.0 instead of the conventional T=0.0 for judge models. The Gemini 3 architecture represents a paradigm shift: reasoning quality is coupled to the default temperature, and lowering it degrades the thinking process rather than improving determinism.

### Source 2: Academic precedent for Gemini 3.1 Pro as LLM judge

**Anonymous et al. (Mar 2026). "Quality-Driven Agentic Reasoning for LLM-Assisted Software Design: Questions-of-Thoughts (QoT) as a Time-Series Self-QA Chain." arXiv:2603.11082v1.**

This 2026 paper uses Gemini 3.1 Pro Preview within an automated LLM-as-a-judge framework for evaluating complex agentic outputs. Demonstrates that using Gemini 3.1 Pro as an evaluator is an accepted practice in current academic literature.

### Source 3: Empirical evidence that T=1.0 does not degrade evaluation quality

**Renze, M. (2024). "The Effect of Sampling Temperature on Problem Solving in Large Language Models." Findings of the Association for Computational Linguistics: EMNLP 2024, pp. 7346-7356.**
**URL:** https://aclanthology.org/2024.findings-emnlp.432/
**arXiv:** https://arxiv.org/abs/2402.05201

Peer-reviewed study testing 9 LLMs across multiple prompt-engineering techniques with temperature sweeps from 0.0 to 1.6. Key finding: "changes in temperature from 0.0 to 1.0 do not have a statistically significant impact on LLM performance for problem-solving tasks." Results generalize across LLMs, prompt techniques, and problem domains. Performance degrades only above T=1.0. Note: effect is weaker for small models (<7B), but all models in our experiment are >13B active parameters.

This counters the historical assumption that T=0.0 is necessary for consistent evaluation. For Gemini 3 models, this finding is doubly relevant: not only is there no accuracy loss at T=1.0, but lowering temperature actively harms reasoning quality per Google's own guidance (Source 1).

### Applied configuration

Judge temperature set to 1.0 in `models.yaml` (changed from initial 0.0). Evaluation consistency comes from:
- Structured ternary rubric (0=absent, 1=partial, 2=implemented)
- Explicit scoring format (`strategy: reasoning | score: N`)
- Gemini 3.1 Pro's thinking mode (reasoning traces published in `judgments.json`)

---

## Methodology: the "lower bound" rule

When a vendor recommends a temperature range for standard chat (e.g., 0.3-0.7), the therapy_temp uses the lower bound. Rationale:

- Lower temperatures prioritize predictability and clinical grounding
- Higher temperatures risk the model adopting the patient's emotional tone or validating dream logic
- For therapeutic personas, stability matters more than expressiveness

This rule comes from analysis of model behavior in the nightmare therapy context (IRT rescripting). Models at the upper bound of their range tend to be more creative but less clinically grounded.
