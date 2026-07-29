# Writing Style Guide

Rules for all `.md` files in this project. Referenced from `CLAUDE.md`.

This guide distinguishes between **project docs** (master.md, decision docs, CLAUDE.md) and **thesis-facing docs** (thesis_extended_structure.md, anything feeding into the final thesis).

## Punctuation (all files)

- No em-dashes (`—`), double-dashes (`--`), or semicolons (`;`)
- Exception: semicolons in citation parentheses `(Author, 2023; Author, 2024)` are fine
- Use `:` for definitions, `,` for clause breaks, `→` for flow/causal relationships, `-` for headings
- Use `\-` for content lines that should render as plain text, not bullet points

## Project Docs (master.md, decision docs, CLAUDE.md)

- Active voice, direct tone
- Contractions are fine ("don't", "isn't")
- Plain words: "uses" not "leverages", "shows" not "demonstrates"
- Cut filler: no "it should be noted", "it is worth noting", "as previously discussed"
- Short paragraphs, max 4-5 sentences

## Thesis-Facing Docs (thesis_extended_structure.md, LaTeX chapters)

- Formal academic register
- No contractions ("do not" instead of "don't")
- Passive voice where conventional ("the metric is computed" rather than "we compute the metric")
- Precise terminology is expected, but avoid gratuitous jargon
- "This study", "the proposed framework" over "we" where appropriate
- Still avoid genuinely empty filler ("it is important to note that"), but standard academic phrasing is fine

## Structure (all files)

- One idea per bullet point
- Tables over long lists when comparing 3+ items with multiple attributes
- Bold for key terms on first use, then plain text

## Thesis (LaTeX)

Applies to all files in `thesis/`. Inherits the Thesis-Facing Docs rules above, plus:

### Language

- British English throughout: "behaviour", "stabilise", "generalise", "colour", "modelling"
- Exception: direct quotes, model names, and API terms keep their original spelling
- First person plural ("we") is acceptable for describing own contributions ("we propose", "we evaluate")
- Passive voice for established facts ("BERTScore is computed as...")
- Active voice for own decisions ("we chose DeBERTa-XLarge-MNLI because...")

### Citations

- APA in-text format via biblatex: `\textcite{Author2024}` for narrative, `\parencite{Author2024}` for parenthetical
- First mention of a concept: cite the foundational paper. Do not re-cite in every subsequent mention
- Multiple citations in one parenthetical: chronological order, separated by semicolons

### Model and Technical Names

- Use `\modelname{}` for model names: `\modelname{Mistral Large 3}`, `\modelname{Gemini 3.1 Pro}`
- Use `\techil{}` for code-level identifiers: `\techil{slice\_1}`, `\techil{metrics.json}`
- Use `\gls{}` for acronyms on first use per chapter: `\gls{llm}`, `\gls{irt}`
- Strategy categories in sans-serif or typewriter: `\techil{confrontation}`, `\techil{self\_empowerment}`

### Figures and Tables

- Every figure and table must be referenced in the text before it appears
- Use `\figref{}` / `\tabref{}` for parenthetical references, `\figureref{}` / `\tableref{}` for inline
- Captions: first sentence is a standalone summary (used in List of Figures). Subsequent sentences add detail
- Figures go at top of page (`[t]`) unless inline placement is required for reading flow

### Paragraph Structure

- Opening sentence states the point. Remaining sentences support it
- One idea per paragraph. If you need a "however" or "in contrast", start a new paragraph
- Transition between sections through the argument, not through filler ("Having discussed X, we now turn to Y")
- Keep paragraphs under 8 sentences

### LaTeX Conventions

- `\ie`, `\eg`, `\vs` for abbreviations (defined in preamble, handles spacing)
- Comments with `% TODO:` for unwritten content, `% GROUNDING:` for links to other sections
- `\include{}` for chapters (page breaks), `\input{}` only if embedding within a chapter

## Paper (LaTeX, `paper/`)

Inherits all Thesis rules above, with these additions from the July 2026 revision:

### Headings, Bold Lead-ins, and Bullet Lists

- Paragraphs NEVER open with a bold run-in. `\paragraph{...}` is banned entirely: the thesis never used it, and it is the typical AI paragraph style. If a block of prose needs a label, give it a real numbered heading (`\subsection{}` / `\subsubsection{}`); if it does not deserve a heading, it does not deserve a bold lead either
- The single exception, taken verbatim from the thesis: `\textbf{Contribution 1.}` in the introduction
- No claim or topic sentence in bold, anywhere: not as a heading, not as a `\textbf{}` lead of an `\item`, not as a paragraph opener. `\item \textbf{Single protocol phase and depth.}` and `\paragraph{Method 1: Plan consistency.}` are both banned patterns
- Bullet lists only for genuinely enumerable items (conditions, dimensions, rubric levels). Argumentative content (limitations, discussion points, implications) is written as prose paragraphs
- Numbered findings lists (Conclusion) are fine, but items start with a plain sentence, not a bold one

### Figures

- Fonts are sized for print width, not screen width. A figure drawn N inches wide and printed at 6.5in scales fonts by 6.5/N, so effective print size = font size × 6.5/N. Target 7-9pt effective
- All data-figure scripts call `set_paper_style()` from `stats/scripts/model_display.py` (base 13pt) and keep multi-panel canvases at or under ~13.5in wide
- Wide multi-panel figures use the overhang trick in LaTeX: `\makebox[\textwidth]{\includegraphics[width=1.12\textwidth]{...}}`
- Trim dead axis space: axis limits hug the data range, empty quadrants waste effective figure size
- Figures that illustrate a null result or need cell-by-cell consultation (e.g. the per-vignette heatmaps) go in the appendix at full size, with a one-line pointer from the main text
- Hand-tuned label placements live in an explicit per-item offset dict with a warning fallback, not an if-chain, so adding a model fails loudly instead of overlapping silently

## Things to Avoid (all files)

- Starting multiple consecutive sentences with "This" or "It"
- Stacking adjectives: "robust, scalable, efficient framework" → pick the one that matters most
- Repeating the same information in different words within the same section
- Adding qualifiers that don't add meaning: "quite", "rather", "somewhat", "fairly"
