# Build the arXiv preprint.
# Figures are generated into ../thesis/figures/ by stats/scripts/fig_*.py;
# `make figures` copies the cited PDFs here so the paper source is self-contained
# (arXiv wants a flat, symlink-free tarball).

FIGS = fig_3_1_pipeline fig_3_2_measurement fig_3_3_eval_stack \
       fig_5_1_strategy_distribution fig_5_2_jaccard fig_5_2b_modal_agreement \
       fig_5_3_bertscore fig_5_4_vignette_slice fig_5_5_correlations \
       fig_5_6_alignment fig_A1_validity fig_seed_comparison

.PHONY: all figures clean arxiv

all: figures
	latexmk -pdf -interaction=nonstopmode main.tex

figures:
	@for f in $(FIGS); do \
		test -f ../thesis/figures/$$f.pdf && cp ../thesis/figures/$$f.pdf figures/ || echo "missing: $$f.pdf"; \
	done
	@cp ../thesis/figures/dialogue_generation.png figures/

arxiv: all
	tar czf arxiv_submission.tar.gz main.tex sections/*.tex references.bib figures/*.pdf figures/*.png main.bbl

clean:
	latexmk -C main.tex
	rm -f main.bbl arxiv_submission.tar.gz
