# Paper changes: Mistral Large 4 as 13th model

> Brief for the `paper-editor` agent. Branch `23_mistral_l4`.
> Data: `stats/data/experiment_runs.csv` now holds 390 runs (360 + 30 from `experiments/runs/batch_20261022_mistral_large4/`). Descriptives, tests and all figures are regenerated and copied to `paper/figures/`. Only the text is left.
> Every number below comes from the regenerated stats. Don't compute or round anything yourself. If something is missing, leave `% TODO:` in the .tex.

## How to work through this

- Each item names the file, an exact `Find` string, and what the new text must say.
- "Swap" = replace the numbers only, nothing else in the sentence changes.
- "Rewrite" = new wording, written in the paper's voice (see the agent instructions and `docs/STYLE.md`). Keep length close to the original unless the item says otherwise.
- "New" = new text at the given spot.
- Don't touch anything that isn't listed. Captions and figure includes stay as they are.

## Mistral Large 4 facts

| What | Value |
|---|---|
| Model | Mistral Large 4, released 2026-10-06 as a public preview (API only), MoE with 1.05T total and 52B active parameters. Weights announced for end of October 2026, licence not published (see addendum) |
| Collection | 2026-10-22, 600 trials, non-thinking mode (reasoning effort `none`) |
| Serving | Pinned to Mistral's base endpoint. Mistral serves Large 4 from three endpoints on OpenRouter (base, zero-data-retention, EU) and a plain provider slug matches all three, so the two variants are excluded. All 600 trials logged as served by Mistral |
| Plan validity | 100% |
| Median Jaccard (pooled) | 1.000, tied at the top with GPT-5.4, Medium 3.5, Small 3.2, OLMo 3.1 32B, Qwen 3.5 122B |
| Mean Jaccard by T (0.0 / 0.075 / 0.15 / 0.3 / 0.6) | 0.956 / 0.930 / 0.931 / 0.889 / 0.818, best at T=0.0 |
| Temperature trend | Spearman rho = -0.31, p = .095, not significant |
| Modal-set agreement | 0.892, 5th of 13 (GPT-5.4 0.993, Medium 3.5 0.972) |
| One strategy set in all 20 trials | 19 of 30 conditions (GPT-5.4: 28 of 30) |
| Mean BERTScore F1 | 0.746, 7th of 13. Falls from 0.794 at T=0.0 to 0.691 at T=0.6 |
| Mean alignment | 0.963, 6th of 13 |
| Strategy repertoire | Narrowest in the set: top-two share 77% (self_empowerment 44.9%, sensory_modulation 32.2%). Never picks confrontation (0 of 1,200 picks) |
| Weakest vignette | avoidant, median Jaccard 0.653. All other vignettes 0.933 or higher |
| Significant pairs (Bonferroni, 78) | Jaccard: above Llama 3.3 70B and Qwen 3.5 27B. BERTScore: below Medium 3.5. Alignment: below GPT-5.4, Sonnet 4.6, Qwen 3.5 397B, above Small 4 |
| Judge | 0 errors, 0 unjudgeable, 0 fallback re-judgings |
| Collection effort | One registry entry (Medium 3.5's shape plus one `ignore` line for the endpoint variants), four lines of figure display metadata. No metric, aggregation or test code changed. Figure code only needed label and legend placement for the 13th model. Wall clock 1 h 20 min including re-runs: on the first pass 19 of 30 conditions failed with upstream rate limits (HTTP 429), failed runs left no partial trials, and they were re-run with backoff |

## Global numbers, old → new

| Statistic | 12 models | 13 models |
|---|---|---|
| Runs / trials | 360 / 7{,}200 | 390 / 7{,}800 |
| Bonferroni comparisons | 66 | 78 |
| Declared strategy picks | 14{,}361 | 15{,}561 |
| Pick shares: sensory / cognitive / self_emp / safety / social / confrontation (%) | 26.7 / 25.4 / 20.0 / 10.4 / 9.6 / 7.9 | 27.1 / 24.2 / 21.9 / 9.9 / 9.6 / 7.3 |
| Jaccard × temperature | rho -0.215, H(4) 21.7, eta² 0.060 | rho -0.220, H(4) 24.1, eta² 0.062 (p < .001 both) |
| Grand median Jaccard T=0.0 → T=0.6 | 0.967 → 0.747 | 1.000 → 0.767 |
| Models best at non-zero T | 10 of 12 | 10 of 13 |
| Jaccard × model | H(11) 104.5, eta² 0.291, 20 of 66 | H(12) 109.6, eta² 0.282, 22 of 78 |
| BERTScore × temperature | rho -0.489, H(4) 93.6, eta² 0.261 | rho -0.499, H(4) 104.6, eta² 0.269 |
| BERTScore medians T=0.0 → T=0.6 | 0.787 → 0.705 | unchanged |
| BERTScore × model | H(11) 92.0, eta² 0.256, 19 of 66 | H(12) 92.0, eta² 0.237, 20 of 78 |
| Vignette, Jaccard | H(5) 6.3, p .280, eta² 0.018 | H(5) 5.4, p .370, eta² 0.014 |
| Vignette, BERTScore | H(5) 11.0, p .052, eta² 0.031 | H(5) 10.1, p .072, eta² 0.026 |
| Median Jaccard by vignette, range | 0.818 (cooperative) to 1.000 (anxious, skeptic) | 0.821 (cooperative, resistant) to 1.000 (anxious, skeptic) |
| rho Jaccard–BERTScore | 0.552, n 360 | 0.543, n 390 |
| rho alignment–Jaccard / alignment–BERTScore | 0.293 / 0.403 | 0.245 / 0.382 |
| Alignment × temperature | rho -0.069, p .19 | rho -0.058, p .25 |
| Alignment × model | H(11) 155.8, eta² 0.434, 34 of 66 | H(12) 164.9, eta² 0.424, 38 of 78 |
| Judge fallback share | 9 trials (0.13%) | 9 trials (0.12%) |

Unchanged and still correct: validity 99.8% (Command A lowest at 98.3%), seventeen malformed trials, 17 unjudgeable, median Jaccard range 0.69--1.00, modal-set range 0.993 to 0.670, BERTScore highest/lowest (Medium 3.5 0.816, Small 4 0.697), alignment range 1.000 to 0.810, the three significantly degrading models, every pairwise conclusion among the old 12 models. The 66 → 78 step moves no old pair across the significance boundary.

## main.tex (abstract)

A1. Swap. Find `Twelve models, spanning` → `Thirteen models, spanning`.

A2. Swap. Find `are evaluated across 7{,}200 trials at five temperatures` → `7{,}800`.

A3. Swap. Find `Ten of twelve models reach their best mean consistency at a low non-zero temperature, a pattern` → `Ten of thirteen`.

## sections/01_introduction.tex

I1. Swap. Find `applying this framework to 12 models across 6 patient vignettes, 5 temperatures, and 20 trials per condition (7{,}200 trials)` → `13 models`, `7{,}800 trials`.

I2. Rewrite. Find `Mistral Medium~3.5 was added four months after the main runs, on identical frozen histories, with a single configuration entry.` The sentence must cover both extensions: Medium 3.5 four months after the main runs and Mistral Large~4 seven months after, both on identical frozen histories with a single configuration entry each. The next sentence (`All substantive findings survive the model-set enlargement.`) stays, plural if it reads better.

## sections/04_setup.tex

S1. Swap. Find `through 70B dense and 119--675B MoE up to two proprietary ceilings` → `119B--1.05T MoE`.

S2. New paragraph right after the paragraph ending `so Sonnet~4.6 is the last Anthropic model that admits a temperature sweep.` Three to four sentences: Mistral Large~4 (released 2026-10-06, 1.05T MoE with 52B active, open weights) was added last by the same single-entry route. It is the newest Mistral flagship and Large~3's successor, so it tests whether the newest EU-sovereign flagship matches Medium~3.5. It runs in non-thinking mode. Mistral serves it from three endpoints (base, zero-data-retention, EU), a plain provider slug matches all three, so the request pins the base endpoint and excludes the two variants.

S3. New table row, directly after `    Mistral Large 3 & 675B MoE (41B act.) & Apache 2.0 \\`:
`    Mistral Large 4 & 1.05T MoE (52B act.) & open weights \\ % TODO: license name`

S4. Swap. Find `The full design crosses 12 models` → `13 models`. Find `7{,}200 trials in total.` → `7{,}800 trials in total.`

S5. Swap. Find `($\binom{12}{2}=66$ comparisons)` → `($\binom{13}{2}=78$ comparisons)`.

S6. Rewrite. Find `Command~A on 2026-07-28, and the bridge re-collection (Section~\ref{sec:robustness-results}) on 2026-07-30.` Add Mistral Large~4 on 2026-10-22 as the last item of the list.

## sections/05_results.tex

R1. Swap. Find `computed over 360 experiment runs (12 models` → `390`, `13 models`. Find `Bonferroni correction over $\binom{12}{2}=66$ comparisons.` → `$\binom{13}{2}=78$`.

R2. Swap. Find `Across 14{,}361 declared strategy picks` → `15{,}561`, then the six shares in the same sentence: 27.1, 24.2, 21.9, 9.9, 9.6, 7.3 (same category order as now). `No category exceeds a third of picks` stays true.

R3. Rewrite. Find `OLMo~3.1~32B and Qwen~3.5~122B concentrate most (73\% and 71\% of picks in their top two categories)`. Mistral Large~4 now concentrates most (77%), followed by OLMo (73%) and Qwen 122B (71%). Add that Large~4 never selects confrontation (0 of 1{,}200 picks). Rest of the sentence (proprietary 65--67%, widest 46--49%) stays.

R4. Swap. Find `ranges from 1.000 (GPT-5.4, Mistral Medium~3.5, Mistral Small~3.2, OLMo~3.1~32B, Qwen~3.5~122B)` → insert `Mistral Large~4` after `GPT-5.4`.

R5. Swap. Find `(pooled Spearman $\rho=-0.215$, $p<.001$; Kruskal--Wallis $H(4)=21.7$, $p<.001$, $\eta^2=0.060$): the grand median falls from 0.967 at $T{=}0.0$ to 0.747 at $T{=}0.6$.` → rho -0.220, H(4)=24.1, eta² 0.062, grand median 1.000 → 0.767. The per-model sentence after it stays (Large 4's trend is not significant, so "the Mistral family and Command~A show no significant trend" still holds).

R6. Swap + rewrite. Find `Ten of the twelve models reach their best mean Jaccard` → `Ten of the thirteen`. Then rewrite `The post-hoc additions follow the same pattern:` so it says the first two additions follow the pattern, and add one sentence after the Command A clause: Mistral Large~4 does not, its mean is highest at $T{=}0.0$ (0.956) and lowest at $T{=}0.6$ (0.818).

R7. Swap. Find `$H(11)=104.5$, $p<.001$, $\eta^2=0.291$; 20 of 66 Bonferroni-corrected pairs significant` → `$H(12)=109.6$`, `$\eta^2=0.282$`, `22 of 78`.

R8. Swap. Find `($\rho=-0.489$, $p<.001$; $H(4)=93.6$, $p<.001$, $\eta^2=0.261$)` → `$\rho=-0.499$`, `$H(4)=104.6$`, `$\eta^2=0.269$`.

R9. Swap. Find `A per-pair analysis over all 68{,}400 trial pairs quantifies this.` → `A per-pair analysis over all 68{,}400 trial pairs of the original 360 runs quantifies this.` (This analysis was not re-run, see open points.)

R10. Swap. Find `$H(11)=92.0$, $p<.001$, $\eta^2=0.256$; 19 of 66 pairs significant` → `$H(12)=92.0$`, `$\eta^2=0.237$`, `20 of 78`.

R11. Swap + small rewrite. Find `($H(5)=6.3$, $p=.280$, $\eta^2=0.018$)` → `($H(5)=5.4$, $p=.370$, $\eta^2=0.014$)`. Find `($H(5)=11.0$, $p=.052$, $\eta^2=0.031$), although the latter sits at the boundary` → numbers `$H(5)=10.1$, $p=.072$, $\eta^2=0.026$`, and replace "sits at the boundary" (p = .072 is no longer at .05) with wording that says it comes closer. Find `Median Jaccard spans a narrow 0.818 (cooperative) to 1.000 (anxious, skeptic).` → `0.821 (cooperative, resistant)`.

R12. Swap. Find `(Spearman $\rho=0.552$, $p<.001$, $n=360$)` → `$\rho=0.543$`, `$n=390$`. Find `($\rho=0.293$) and moderately with BERTScore ($\rho=0.403$)` → `0.245`, `0.382`.

R13. Swap. Find `five models sit at perfect median decision consistency` → `six models`.

R14. Swap. Find `temperature-independent ($\rho=-0.069$, $p=.19$)` → `($\rho=-0.058$, $p=.25$)`.

R15. Swap. Find `($H(11)=155.8$, $p<.001$, $\eta^2=0.434$; 34 of 66 pairs significant)` → `$H(12)=164.9$`, `$\eta^2=0.424$`, `38 of 78`. Find `Judge accounting: of 7{,}200 trials` → `7{,}800`. Find `9 trials (0.13\%)` → `9 trials (0.12\%)`.

R16. New paragraph in Section 5.7, after the bridge paragraph (ends `taken up in Sections~\ref{sec:sovereign-deployment} and~\ref{sec:limitations}.`) and before `Each enlargement tightens the Bonferroni correction`. One paragraph, 6 to 8 sentences, using the facts table above. It must say:
- Large~4 is the third post-hoc addition, collected seven months after the main set under the pinned regime (base endpoint, provider logged for all 600 trials).
- Median Jaccard 1.000, but modal-set agreement 0.892 (fifth), one strategy set in all 20 trials in 19 of 30 conditions, mean BERTScore 0.746, alignment 0.963.
- No low-temperature optimum: mean Jaccard highest at T=0.0 (0.956), 0.818 at T=0.6, trend not significant (rho = -0.31, p = .095). BERTScore falls from 0.794 to 0.691.
- The ceiling median comes with the narrowest repertoire in the set (77% top-two share, no confrontation), so part of it is distributional (refer back to Section~\ref{sec:validity}). Contrast with Medium~3.5 (59%).
- Its remaining instability sits mostly in one vignette (avoidant, median 0.653).
- Comparisons with the main cohort are cross-regime, and seven months of serving changes lie in between.

R17. Rewrite. Find `from $\binom{10}{2}=45$ to $\binom{11}{2}=55$ and now $\binom{12}{2}=66$ comparisons, moving two marginal pairs below significance in total`. Add the fourth step to $\binom{13}{2}=78$ and say the two crossings came from the earlier steps, the latest step moves no pair. Keep the parenthesis with the two pairs. Then in the last sentence (`All substantive findings of the original study hold under model-set enlargement and under the GPT-5.4 correction.`) add one qualification: the Mistral low-temperature optimum does not extend to Large~4.

## sections/06_discussion.tex

D1. Swap. Find `($\rho=-0.49$ vs.\ $-0.22$)` → `($\rho=-0.50$ vs.\ $-0.22$)`.

D2. New, two or three sentences, right after `with Medium~3.5 an EU-sovereign open-weight model tops the stability ranking.` The newest and largest Mistral model does not change this: Large~4 also reaches median 1.000, but trails Medium~3.5 on modal-set agreement (0.892 vs 0.972) and response similarity (0.746 vs 0.816), and its ceiling rests on the narrowest repertoire in the set. The recommendation for Medium~3.5 stands.

D3. New, one sentence, in the paragraph starting `Parameter count does not straightforwardly predict stability`, after the Command A / Medium 3.5 sentence: Large~4, the largest model in the set (1.05T total, 52B active), ranks below the 128B dense Medium~3.5 on every stability measure except median Jaccard, where both sit at 1.000.

D4. Rewrite. Find `Ten of twelve models reach their best mean decision consistency at a non-zero temperature, and the entire Mistral family peaks between $T{=}0.075$ and $T{=}0.15$, exactly the region of its vendor default.` → ten of thirteen. The four earlier Mistral models peak between $T{=}0.075$ and $T{=}0.15$, the region of their vendor default. Large~4 is the exception, highest at $T{=}0.0$ (0.956). The sentence after (`Pushing a model to $T{=}0.0$ ...`) stays.

D5. Rewrite. Find `Command~A later required the same single registry entry,`. Add Large~4 in the same sentence or one short sentence: one registry entry plus one line excluding two endpoint variants, four lines of display metadata, collection 1 h 20 min including re-runs after upstream rate limits (19 of 30 conditions on the first pass, failed runs left no partial trials). Then find `shows all substantive findings survive both enlargements, with two marginal Bonferroni boundary crossings in total.` → all three enlargements, two crossings in total, none from the latest.

D6. New, one sentence, in the Limitations serving paragraph, right after `inherit that confound.`: Large~4 was collected under the pinned regime as well, so its position relative to the main cohort is a cross-regime comparison.

## sections/07_conclusion.tex

C1. Swap. Find `Three evaluation methods were applied to twelve models across 7{,}200 trials` → `thirteen`, `7{,}800`.

C2. Rewrite. Find `Ten of twelve models reach their best mean consistency at a low non-zero temperature, and the Mistral family peaks at its vendor default,` → ten of thirteen, and the four earlier Mistral models peak at their vendor default (Large~4 is best at $T{=}0.0$). The rest of the item stays.

C3. Swap. Find `($\rho = 0.29$ to $0.55$)` → `($\rho = 0.25$ to $0.54$)`.

C4. Rewrite. Find `Mistral Medium~3.5, an EU-sovereign open-weight model, tops the overall stability ranking.` (item 5, conclusion only, not the abstract) → add that it stays ahead of the newer and far larger Mistral Large~4.

## sections/appendix_tables.tex

Add one row after the `Mistral Large 3` row in each table:

T1. Median Jaccard table, after `    Mistral Large 3 & 0.772 & 0.709 & 0.877 & 0.775 & 0.712 \\`:
`    Mistral Large 4 & 1.000 & 1.000 & 1.000 & 1.000 & 0.854 \\`

T2. Mean BERTScore table, after `    Mistral Large 3 & 0.742 & 0.756 & 0.764 & 0.743 & 0.705 \\`:
`    Mistral Large 4 & 0.794 & 0.771 & 0.751 & 0.720 & 0.691 \\`

T3. Mean alignment table, after its `Mistral Large 3` row:
`    Mistral Large 4 & 0.954 & 0.952 & 0.971 & 0.969 & 0.969 \\`

## Addendum 2026-10-22: Large 4 is a preview, not yet open weights

Large 4 is currently a public preview served only through Mistral's API. Mistral announced the weights for the end of October 2026 (launch post, 2026-10-06: "Weights drop end of this month"). No licence has been published, and there is no Large 4 checkpoint on Mistral's Hugging Face page yet. The paper still calls it "open weights" in two places. The measured checkpoint is the preview, and the released weights may differ from it.

P1. Rewrite. In `04_setup.tex`, find `Mistral Large~4 (released 2026-10-06, 1.05T MoE with 52B active parameters, open weights) was added last by the same single-entry route.` Drop `open weights` from the parenthesis and say it was released 2026-10-06 as a public preview. Add one short sentence after it: Mistral serves the preview through its API only and has announced the open weights for the end of October 2026, with the licence not yet published. Every other sentence of that paragraph stays.

P2. Swap. In the models table, replace the row
`    Mistral Large 4 & 1.05T MoE (52B act.) & open weights \\ % TODO: license name`
with
`    Mistral Large 4 & 1.05T MoE (52B act.) & preview, weights pending \\ % TODO: licence once the weights ship (announced for end of Oct 2026)`

P3. New, one sentence, in the Limitations serving paragraph (`06_discussion.tex`), right after `so its position relative to the main cohort is a cross-regime comparison.`: Large~4 was also measured as a public preview, so the open-weight release may not behave like the measured checkpoint.

## Addendum 2026-10-23: model-set cut-off and date-scoped proprietary claim

Facts: the main set was collected 2026-03-21 to 2026-03-24. At that time GPT-5.4 (released 2026-03-05) and Sonnet~4.6 (released 2026-02-17) were the newest models of their vendors' lines. The proprietary pair has not been updated since. GPT-5.4 was only re-collected through the native API on 2026-07-28, as the same model. OpenAI has released newer models since then (GPT-5.5 onwards). Whether they admit a temperature sweep was not tested, so the paper must not claim anything about them beyond "not evaluated". Large~4 on 2026-10-22 is the last collection, and the model set is closed with it.

P4. Rewrite. In `04_setup.tex`, find the sentence starting `The proprietary ceilings are also the newest models of their vendors' lines on which this study is possible:`. The present-tense claim is out of date. Rewrite it so it says the proprietary pair was fixed at the main collection (March 2026), when both were their vendors' newest models of their lines, and was not updated with later releases. Keep the Anthropic part with its citation: models released after Sonnet~4.6, including the entire Claude~5 family, reject any non-default temperature regardless of reasoning mode, so Sonnet~4.6 is the last Anthropic model that admits a temperature sweep. Add that newer OpenAI models were not evaluated. Two or three sentences in total.

P5. New, one sentence, in `04_setup.tex`, in the data paragraph, right after the collection-date list that ends with `and Mistral Large~4 on 2026-10-22.`: the model set was closed with the Large~4 collection, and models released later are not part of this study. Wording is yours, keep it short.

## Addendum 2026-10-23 (2): age-gap caveat for Command A

Facts: Command A was released in March 2025 (model ID `command-a-03-2025`), Mistral Medium 3.5 on 2026-04-30, about a year later. The dense-pair comparison therefore differs in training generation as well as vendor. The conclusion that dense weights alone do not confer stability still holds. What the pair cannot do is say whether the gap comes from the vendor or from the newer training generation.

P6. New, one sentence, in `06_discussion.tex`, in the paragraph starting `Parameter count does not straightforwardly predict stability`, right after `dense weights alone do not confer stability.`: the pair also differs in age, Command A (March 2025) being about a year older than Medium~3.5 (April 2026), so the comparison cannot separate vendor from training generation as the source of the gap. Keep it under about 30 words. Change nothing else.

## Open points (for Daniel, not the agent)

- Large 4 licence: not published yet (state 2026-10-22). Most likely the modified MIT licence of Medium 3.5 (free use, except companies above $20M monthly revenue). Mistral's two strongest open releases since December 2025, Devstral 2 and Medium 3.5, both use it, while Large 3 and the 119B Small 4 stayed Apache 2.0. Fill the table TODO once the weights ship.
- The 68,400-pair BERTScore analysis (`stats/scripts/pairwise_jaccard_bertscore.py`) needs the raw trials of all batches, which aren't on this machine. Re-run it where `experiments/latest/` lives, then drop the "original 360 runs" qualifier from R9.
- Already in the paper before this change: Qwen 3.5 27B's per-model rho is printed as -0.49, the data gives -0.4848 (→ -0.48). Not touched here.
- `docs/analysis.md` still describes the 12-model set. `docs/LLM_run_recordings.md` already has the new batch and endpoint snapshot.
- After the edits: rebuild the PDF, check page breaks and orphans (the text gets longer) and overfull boxes.
