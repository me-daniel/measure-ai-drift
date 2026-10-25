# Final read-through (2026-10-23)

Full pass over `main.tex` (abstract, ethics) and every section incl. appendix, against `docs/STYLE.md` and the current data (`stats/data/experiment_runs.csv`, 390 runs). Nothing in this list is applied yet. Already applied before this pass: Qwen 27B rho -0.49 → -0.48 (`05_results.tex:34`), Command A "non-reasoning variant" (`04_setup.tex:11`).

Open by decision: Mistral Large 4 licence TODO (`04_setup.tex:26`), Nemotron stays out of the paper.

Sections: A = factual precision (small, data-checked), B = claims that need your decision, C = clarity, D = shortening, E = STYLE.md violations.

## A. Factual precision

| # | Where | Now | Problem | Proposed |
|---|---|---|---|---|
| A1 | `main.tex:37` | `\date{July 2026}` | Large 4 was collected 2026-10-22 | `\date{October 2026}` (or the submission month) |
| A2 | `06_discussion.tex:12` | "at validity 0.99+" | Command A is at 98.3% (`05_results.tex:9`) | "at validity of 98\% or more" |
| A3 | `06_discussion.tex:17` | "The gap grows at higher temperatures, where Mistral Large~3 falls to 0.700 while the proprietary models stay at 0.87 or above." | Only true at T=0.6. At T=0.3 the gap is 0.05 (Large 3 0.805, Sonnet 0.854), smaller than at T=0.15 (0.059), and Sonnet is below 0.87 | "At $T{=}0.6$ the gap grows: Mistral Large~3 falls to 0.700 while the proprietary models stay at 0.87 or above." |
| A4 | `06_discussion.tex:21` | "the 24--32B dense models (Mistral Small~3.2, OLMo~3.1) sit at or near the top" | Qwen 3.5 27B is also 24-32B dense and sits at the bottom | "two of the three 24--32B dense models (Mistral Small~3.2, OLMo~3.1) sit at or near the top" |
| A5 | `05_results.tex:36` | "The pattern is clearest in the Mistral family: Mistral Small~4 rises ..., Mistral Large~3 from ..., and Llama~3.3~70B from 0.719 to 0.775" | Llama is listed under the Mistral family | "The pattern is clearest in the Mistral family: Mistral Small~4 rises from 0.777 at $T{=}0.0$ to 0.881 at $T{=}0.15$ and Mistral Large~3 from 0.796 to 0.848. Llama~3.3~70B shows it too, rising from 0.719 to 0.775 at $T{=}0.075$." |
| A6 | `07_conclusion.tex:11` | "the four earlier Mistral models peak at their vendor default" | Small 3.2 and Medium 3.5 peak at 0.075, the default is 0.15. Discussion 6.3 already says "the region of their vendor default" | "peak near their vendor default" |
| A7 | `01_introduction.tex:22` | Contribution 3 names Medium 3.5 and Large 4 | Command A is missing, though "the model-set enlargements" covers three additions | "Mistral Medium~3.5 and Command~A were added four months after the main runs, and Mistral Large~4 seven months after, all on identical frozen histories with a single configuration entry each." |
| A8 | `03_method.tex:29` | "anonymised session data from the prior reDreamAI efficacy study" | The intro says the RCT tested the web-based predecessor, and reDreamAI is its successor. The ethics statement says "a prior efficacy study". Please confirm which is right | "anonymised session data from the prior efficacy study \citep{voss2026efficacy}" |
| A9 | `05_results.tex:90` | "the steepest response-level temperature reaction among the top-ranked models" | OLMo (rho -0.91) and Qwen 122B (-0.89) also reach median J 1.000 and react more steeply. True against GPT-5.4 (-0.23), Sonnet (-0.56), Large 4 (-0.63) | "steeper than both proprietary models and Large~4" |
| A10 | `05_results.tex:57` | "although the latter comes closer: patient profile affects response wording more than strategy selection." | States an effect from p=.072, two sentences before "absence of evidence" | "although the latter comes closer ($p=.072$)." |

## B. Claims that need your decision

**B1. The temperature recommendation contradicts the data for five models** (`06_discussion.tex:27`).

Now: "The practical recommendation is to operate at or near the vendor-recommended temperature ... Models designed for a temperature range tend to be most stable within it".

Setup 4.2 gives the vendor defaults: Qwen 3.5 and OLMo 0.6, Llama about 0.6, Command A 0.3. These models are least or second-least consistent at their own default:

| Model | Default | Mean J at default | Best mean J |
|---|---|---|---|
| Qwen 3.5 122B | 0.6 | 0.716 | 0.989 (T=0.075) |
| OLMo 3.1 32B | 0.6 | 0.753 | 1.000 (T=0.0) |
| Qwen 3.5 27B | 0.6 | 0.530 | 0.775 (T=0.0) |
| Llama 3.3 70B | ~0.6 | 0.638 | 0.775 (T=0.075) |
| Command A | 0.3 | 0.736 | 0.861 (T=0.15) |

Only Mistral's 0.15 falls on its optimum. Proposed rewrite of the first two sentences:

> The practical recommendation is to verify stability for the specific model at the intended temperature. Neither greedy decoding nor the vendor default guarantees it. For Qwen~3.5, OLMo~3.1 and Llama~3.3 the vendor default sits at or near $T{=}0.6$, where these models are least consistent, while Mistral's $T{=}0.15$ falls inside its optimum. In this sweep a low non-zero temperature ($T{=}0.075$ to $0.15$) is the best single setting for ten of thirteen models, and only three models degrade significantly across the sweep (OLMo~3.1~32B, Qwen~3.5~122B, Qwen~3.5~27B).

Conclusion item 3 ("Deployments should verify stability at the vendor-recommended setting rather than assume $T{=}0.0$ is safest") would then read "at the intended setting".

**B2. "Most stable model" is never defined, and two sentences conflict.**

- `05_results.tex:90`: Medium 3.5 "lands at the top of the stability ranking".
- `05_results.tex:94`: "GPT-5.4 is the most decision-stable model in the set (modal-set agreement 0.993)".
- `06_discussion.tex:19`: Medium 3.5 "is the most stable model in the entire set".
- Abstract and conclusion item 5: Medium 3.5 "tops the overall stability ranking".

Medium 3.5 ties for the highest median Jaccard, has the highest BERTScore, and is second on modal-set agreement (0.972 vs 0.993). Proposed: define it once in 6.2, "the most stable model overall: perfect median decision consistency, the highest response-level consistency, and second only to GPT-5.4 on modal-set agreement", and replace "in the entire set" with "overall". Abstract and conclusion can stay as they are.

**B3. One sentence in the bridge paragraph states a cause the paragraph itself calls confounded** (`05_results.tex:96`).

Now: "...also shows that quantisation as such does not cause the instability. The variation between stacks does."

Two sentences earlier the paragraph says the comparison is confounded with four months of serving changes. Proposed: "The variation between stacks, or the four months between the collections, is the more likely source."

## C. Clarity

| # | Where | Now | Proposed |
|---|---|---|---|
| C1 | Abstract, finding (4) | "BERTScore detects when the tone changes" | "when the wording changes" ("tone" means something else in therapy, the body says wording) |
| C2 | `05_results.tex:9` | "The structured format turns out to be essentially free:" | "Models follow the structured format almost without failure:" |
| C3 | `05_results.tex:13` | "Large~4 never selects confrontation (0 of 1{,}200 picks)." sits inside the ranking | Move it to the end of the paragraph |
| C4 | `05_results.tex:34` | "The most capable models hold their therapeutic decisions stable" | "The proprietary models hold ..." (capability is not measured) |
| C5 | `05_results.tex:64` | "Mistral Small~4 presents an interesting case: moderate decision consistency but the lowest response similarity" | "Mistral Small~4 combines moderate decision consistency with the lowest response similarity in the set, so ..." |
| C6 | `05_results.tex:98` | "...(77\% top-two share, no confrontation at all), so part of it is distributional (Section~\ref{sec:validity}), in contrast with Medium~3.5's 59\%." | "...(77\% top-two share against Medium~3.5's 59\%, no confrontation at all), so part of it is distributional (Section~\ref{sec:validity})." |
| C7 | `06_discussion.tex:10` | "Neither is a failure of BERTScore itself, but a consequence of how therapeutic language is structured." | "Both follow from how therapeutic language is structured, not from a flaw in BERTScore." |
| C8 | `06_discussion.tex:12` | "two patients, or the same patient after a page reload" | "two patients with the same presentation, or the same patient after a page reload" |
| C9 | `06_discussion.tex:21` | "it adapts its strategy to the patient but not to the sampling seed" | "... but not to sampling noise" (the study sets no seed) |
| C10 | `07_conclusion.tex:16` | "what was a small gap for Mistral Large~3 at its recommended temperature became, with Mistral Medium~3.5, the top of the ranking" | "the small gap Mistral Large~3 left at its recommended temperature closes with Mistral Medium~3.5, which tops the ranking" |
| C11 | Heading 5.7 | "Robustness to Model-Set Changes" | Also covers the GPT-5.4 re-collection and the bridge. Option: "Robustness to Model Additions and Serving Regime" |

## D. Shortening

Estimated total about 230 words (2% of 10,000), roughly half a page. Most of the gain is readability, not length.

| # | Where | What | Saves |
|---|---|---|---|
| D1 | `05_results.tex:96` bridge paragraph | About 390 words and 16 sentences (STYLE.md cap: 8). Split into three paragraphs: (a) design plus Large 3 and Qwen 27B, (b) Small 4 and Qwen 122B reproduce, so the effect is model-specific, (c) confounds plus conclusion. Shorten "This is not a dropped-parameter artefact of the kind diagnosed above: its BERTScore falls ... so sampling variance demonstrably reaches the model while its decisions hold still" to one clause, since the Medium 3.5 paragraph already makes the same argument | ~70 |
| D2 | `01_introduction.tex:8` | Cut "Capability and stability are distinct properties, but current evaluations conflate them." (restates the sentence before). Shorten the consistency-literature list to one clause, since Related Work 2.3 repeats the same four citations with the same contrast | ~50 |
| D3 | `06_discussion.tex:19` and `:21` | The Large 4 vs Medium 3.5 comparison appears in both paragraphs. Keep it once (in :19), cut "Large~4, the largest model in the set (1.05T total, 52B active), does not outrank the 128B dense Medium~3.5." from :21. Paragraph :19 is also 11 sentences | ~25 |
| D4 | `06_discussion.tex:19` | "They corroborate a successor decision that reDreamAI had already made on certification grounds (Section~\ref{sec:models}), they did not drive it." repeats 4.1 in full. Shorten to "They corroborate reDreamAI's earlier successor decision (Section~\ref{sec:models})." | ~12 |
| D5 | `03_method.tex:8, 13, 20` | Decoupling is explained in 3.1 body and again in the Figure 1 caption. The slice cut point is stated in 3.2 body, the Figure 2 caption and 3.3. Cut "This separation is a deliberate design choice.", the last caption sentence of Figure 1, and the last sentence of 3.2 | ~40 |
| D6 | `06_discussion.tex:32` | Drop the first-pass failure detail "(19 of 30 conditions failed on the first pass, failed runs left no partial trials)" and the display-metadata line counts | ~30 |
| D7 | `06_discussion.tex:52` | Limitations paragraph with two topics (serving regime, judge), 9 sentences. Split at "The judge endpoints are versioned previews" | 0 |
| D8 | `05_results.tex:45` | BERTScore paragraph ends with between-model differences, a second idea. Move that sentence to the end of the first BERTScore paragraph (:43) | 0 |

## E. STYLE.md violations

Semicolons in prose (stats parentheses and table cells excluded):

| Where | Text | Fix |
|---|---|---|
| `03_method.tex:29` | "efficacy study; data protection requirements prevent" | full stop |
| `03_method.tex:92` | "rather than scored zero; invalid plans are already penalised" | ", since invalid plans ..." |
| `04_setup.tex:7` | "non-thinking mode; where a model exposes" | full stop |
| `04_setup.tex:54` | "``stable enough''; clinical significance thresholds" | colon |
| `06_discussion.tex:32` | "display metadata; no metric, aggregation" | full stop |
| `06_discussion.tex:52` | "differ between requests; the later collections" | full stop |
| `appendix.tex:23` | "``agency'' category); the resolution was" | full stop |

Words on the avoid list:

| Where | Word | Fix |
|---|---|---|
| `01_introduction.tex:4` | "demonstrated the efficacy" | "showed" |
| `01_introduction.tex:4` | "reliability is non-negotiable" | Cut the clause. The sentence also repeats "deployment context", which opens the next paragraph |
| `02_related_work.tex:14` | "survey the consistency landscape" | "survey consistency research" |
| `03_method.tex:29` | "demonstrate that expert-defined" | "show" |
| `03_method.tex:36`, `05_results.tex:90`, `05_results.tex:96` | "demonstrably" (3x) | Drop it ("so temperature reaches the model") |
| `06_discussion.tex:39` | "more robust" | "more stable" or "less sensitive to the category boundaries" |

"Robust" in `04_setup.tex:9` and `07_conclusion.tex:13` ("robust to model-set changes") is the technical sense, matching the robustness section. I would keep those.

## Checked and fine

- All numbers in Results 5.2 to 5.6 against `experiment_test_results.json` and the CSV: pooled and per-model rho, KW H/eta2, significant-pair counts (22/20/38 of 78), vignette tests, cross-metric rho (0.543, 0.245 → conclusion's 0.25 is correct), ten of thirteen non-zero peaks, Qwen 122B above 397B at every temperature, Medium 3.5 BERTScore drop 0.13 (peak T=0.075 to T=0.6, rho -0.66).
- Discussion 6.2 Large 3 vs proprietary at T=0.15 (0.848 / 1.000 / 0.907).
- Appendix median-Jaccard table matches the CSV medians (the other appendix tables were not rechecked).
- The `---` in the appendix prompt and rubric are verbatim prompt text and stay.

## Brief for paper-editor

Apply every item above (A1 to A10, B1 to B3, C1 to C11, D1 to D8, E) with these decisions:

- A1: `\date{October 2026}`.
- A8: use the neutral wording "anonymised session data from the prior efficacy study" (drop "reDreamAI", no new citation). It matches the ethics statement.
- B1 to B3, C, E and D3 to D8: use the proposed text as written. Where a cut leaves a seam, change at most the words next to it.
- C11: rename the heading, keep `\label{sec:robustness-results}`.
- B1: also change conclusion item 3 "at the vendor-recommended setting" → "at the intended setting".
- D1 (bridge paragraph, `05_results.tex:96`): three paragraphs, at most 330 words in total (now about 390). Keep Daniel's sentences wherever the split does not force a change. (a) Design, Large 3 and Qwen 27B. Fold the dropped-parameter argument into one clause ("..., and its BERTScore still falls from 0.952 to 0.854 across the sweep, so temperature reaches the model"). (b) Small 4 and Qwen 122B. (c) Time confound, endpoints and quantisation, the B3 sentence, the closing sentence with the two section references.
- D2 (`01_introduction.tex:8`): delete "Capability and stability are distinct properties, but current evaluations conflate them." Rewrite the consistency-literature sentence as one sentence of at most 45 words that keeps all four citations and ends on the therapeutic-decision contrast.

### Writing rules on top of STYLE.md

These target the patterns that make text read as machine-written. They are binding for every word the agent writes.

1. Minimal diff. Touch only the listed text. Do not polish neighbouring sentences.
2. No new "not X but Y", "X rather than Y" or "X, not Y" contrasts. The paper already uses that figure often.
3. No groups of three for rhythm (three adjectives, three parallel clauses).
4. At most one colon per sentence, and never colons in two consecutive sentences.
5. No closing sentence that sums up or draws a moral ("This shows ...", "In short ...", "Taken together ...").
6. No signposting or intensifiers: "notably", "importantly", "crucially", "indeed", "overall", "in other words", "clearly", "substantially", "significantly" (except in the statistical sense).
7. No rhetorical questions, no sentence fragments as punchlines.
8. Do not start two consecutive sentences with "This", "It" or "The".
9. Use the paper's own terms: decision consistency, response similarity, pinned regime, default routing, bridge re-collection.
10. No number that is not already in the paper or in this file.
