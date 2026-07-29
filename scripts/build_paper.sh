#!/usr/bin/env bash
# Build the arXiv paper PDF (paper/main.pdf).
#
# Usage:
#   ./scripts/build_paper.sh          # copy figures + latexmk (fast, the usual case)
#   ./scripts/build_paper.sh --figs   # also regenerate the six data figures from the CSV first
#   ./scripts/build_paper.sh --arxiv  # build + pack paper/arxiv_submission.tar.gz
set -euo pipefail
cd "$(dirname "$0")/.."

if [ "${1:-}" = "--figs" ]; then
    for f in fig_validity_strategy fig_jaccard fig_bertscore fig_vignette_slice fig_correlations fig_alignment; do
        PYTHONPATH=stats/scripts python3 "stats/scripts/$f.py"
    done
    shift || true
fi

if [ "${1:-}" = "--arxiv" ]; then
    make -C paper arxiv
else
    make -C paper
fi

echo "Built paper/main.pdf"
