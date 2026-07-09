#!/usr/bin/env bash
# Run ONLY Mistral Medium 3.5 (600 trials: 6 vignettes x 5 temps x 20 trials)
# and append the runs to the existing March batch — nothing else is re-run.
set -euo pipefail
cd "$(dirname "$0")/.."

python scripts/run_experiment.py \
    --models mistral_medium35 \
    --trials 20 \
    --temps 0.0 0.075 0.15 0.3 0.6 \
    --no-therapy-temp \
    --batch-dir experiments/runs/batch_20260321_final
