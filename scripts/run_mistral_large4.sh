#!/usr/bin/env bash
# Run ONLY Mistral Large 4, non-thinking (600 trials: 6 vignettes x 5 temps x
# 20 trials) into its own batch, judged so the alignment columns are filled.
# The canonical batches stay untouched: the batch aggregates separately into
# stats/data/mistral_large4_runs.csv, like the bridge batch.
set -euo pipefail
cd "$(dirname "$0")/.."

BATCH=experiments/runs/batch_20261022_mistral_large4

# --- Preflight ---------------------------------------------------------------
[ -f .env ] || { echo "ERROR: .env missing (OPENROUTER_API_KEY + GOOGLE_AI_STUDIO_API_KEY)"; exit 1; }
ls data/synthetic/frozen_histories/frozen_*/slice_2.json >/dev/null 2>&1 \
    || { echo "ERROR: frozen histories missing — restore data/synthetic/frozen_histories/"; exit 1; }

# --- Run (skipped if the batch is already complete: 30 = 6 vignettes x 5 temps)
mkdir -p "$BATCH"
# Count finished runs only: a failed run (e.g. upstream 429) leaves an empty dir
n_runs=$(find "$BATCH" -mindepth 2 -maxdepth 2 -name metrics.json | wc -l | tr -d ' ')
if [ "$n_runs" -ge 30 ]; then
    echo "Batch $BATCH already has $n_runs runs — skipping the API run, re-aggregating only."
else
    python3 scripts/run_experiment.py \
        --models mistral_large4 \
        --trials 20 \
        --temps 0.0 0.075 0.15 0.3 0.6 \
        --no-therapy-temp \
        --batch-dir "$BATCH"
fi

python3 stats/scripts/aggregate.py --tier experiment --runs-dir "$BATCH" \
    --output stats/data/mistral_large4_runs.csv

echo "Done: 30 rows expected in stats/data/mistral_large4_runs.csv."
echo "Check the provider field in the trial JSONs: every trial should be served by Mistral."
