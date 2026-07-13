#!/usr/bin/env bash
# Run ONLY Mistral Medium 3.5 (600 trials: 6 vignettes x 5 temps x 20 trials)
# into its own batch — the March batch stays untouched — then merge both
# batches at aggregation time and refresh descriptives + tests.
# Nothing from the original 10 models is re-run.
set -euo pipefail
cd "$(dirname "$0")/.."

BATCH=experiments/runs/batch_20260709_mistral_medium35
MARCH=experiments/latest

# --- Preflight ---------------------------------------------------------------
[ -f .env ] || { echo "ERROR: .env missing (OPENROUTER_API_KEY + GOOGLE_AI_STUDIO_API_KEY)"; exit 1; }
[ -e "$MARCH" ] || { echo "ERROR: $MARCH missing — restore the March batch first"; exit 1; }
ls data/synthetic/frozen_histories/frozen_*/slice_2.json >/dev/null 2>&1 \
    || { echo "ERROR: frozen histories missing — restore data/synthetic/frozen_histories/"; exit 1; }

# --- Run (skipped if the batch is already complete: 30 = 6 vignettes x 5 temps)
n_runs=$(find "$BATCH" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
if [ "$n_runs" -ge 30 ]; then
    echo "Batch $BATCH already has $n_runs runs — skipping the API run, re-aggregating only."
else
    mkdir -p "$BATCH"
    python3 scripts/run_experiment.py \
        --models mistral_medium35 \
        --trials 20 \
        --temps 0.0 0.075 0.15 0.3 0.6 \
        --no-therapy-temp \
        --batch-dir "$BATCH"
fi

# --- Merge with March data and refresh stats ----------------------------------
python3 stats/scripts/aggregate.py --tier experiment --runs-dir "$MARCH" "$BATCH"
python3 stats/scripts/descriptives.py --tier experiment
python3 stats/scripts/tests.py --tier experiment

echo "Done: 330 rows expected in stats/data/experiment_runs.csv (300 March + 30 new)."
echo "Figures: python3 stats/scripts/fig_{validity_strategy,jaccard,bertscore,vignette_slice,correlations,alignment}.py"
