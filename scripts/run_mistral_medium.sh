#!/usr/bin/env bash
# Run ONLY Mistral Medium 3.5 (600 trials: 6 vignettes x 5 temps x 20 trials)
# into its own batch — the March batch stays untouched; batches are merged
# at aggregation time.
set -euo pipefail
cd "$(dirname "$0")/.."

BATCH=experiments/runs/batch_20260709_mistral_medium35
mkdir -p "$BATCH"

python3 scripts/run_experiment.py \
    --models mistral_medium35 \
    --trials 20 \
    --temps 0.0 0.075 0.15 0.3 0.6 \
    --no-therapy-temp \
    --batch-dir "$BATCH"
