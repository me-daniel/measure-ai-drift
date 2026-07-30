#!/usr/bin/env bash
# Run the pinned bridge pair — Mistral Large 3 and Qwen 3.5 27B — with the
# judge disabled (600 trials each: 6 vignettes x 5 temps x 20 trials) into
# their own batch. No judge means no alignment scores and no Google API key.
# The existing batches stay untouched.
set -euo pipefail
cd "$(dirname "$0")/.."

BATCH=experiments/runs/batch_20260730_bridge_pinned

# --- Preflight ---------------------------------------------------------------
[ -f .env ] || { echo "ERROR: .env missing (OPENROUTER_API_KEY)"; exit 1; }
ls data/synthetic/frozen_histories/frozen_*/slice_2.json >/dev/null 2>&1 \
    || { echo "ERROR: frozen histories missing — restore data/synthetic/frozen_histories/"; exit 1; }

# --- Run (skipped if the batch is already complete: 60 = 2 models x 6 vignettes x 5 temps)
mkdir -p "$BATCH"
n_runs=$(find "$BATCH" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
if [ "$n_runs" -ge 60 ]; then
    echo "Batch $BATCH already has $n_runs runs — skipping the API run."
else
    python3 scripts/run_experiment.py \
        --models mistral_large qwen35_27b \
        --trials 20 \
        --temps 0.0 0.075 0.15 0.3 0.6 \
        --no-therapy-temp \
        --no-judge \
        --batch-dir "$BATCH"
fi

echo "Done: 60 runs expected in $BATCH (alignment columns will be empty)."
echo "Aggregate with: python3 stats/scripts/aggregate.py --tier experiment --runs-dir $BATCH"
