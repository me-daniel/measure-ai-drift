"""Exploratory run: Nemotron 3 Mamba-Transformer hybrids (branch 24_Nemotron).

Runs one model per call into a shared batch, judged. Each model gets the
standard sweep plus its therapy_temp (NVIDIA recommends T=1.0 for every mode),
so 6 vignettes x 6 temps x 20 trials = 720 trials per model.

Resumable: conditions with a metrics.json are skipped, and a failed condition
(e.g. upstream 429) is deleted and retried with exponential backoff. Only the
model's own run dirs are touched, so the three models can run in parallel.

Usage (from the repo root):
    HF_HUB_OFFLINE=1 uv run python scripts/run_nemotron.py nemotron3_ultra
Aggregate afterwards:
    uv run python stats/scripts/aggregate.py --tier experiment \
        --runs-dir experiments/runs/batch_20261023_nemotron \
        --output stats/data/nemotron_runs.csv
"""
import asyncio
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, ".")
sys.path.insert(0, "scripts")
from run_experiment import DEFAULT_TEMPS, VIGNETTES, find_slice_path, run_single  # noqa: E402

BATCH = Path("experiments/runs/batch_20261023_nemotron")
MODELS = ["nemotron3_ultra", "nemotron3_super", "nemotron3_nano"]
TRIALS = 20


def therapy_temp(model: str) -> float:
    cfg = yaml.safe_load(open("src/config/models.yaml"))
    return next(float(t["therapy_temp"]) for t in cfg["evaluation_targets"] if t["name"] == model)


def own_dirs(model: str) -> list[Path]:
    return [d for d in BATCH.iterdir() if d.is_dir() and f"_{model}_" in d.name]


def done(model: str) -> set[tuple[str, float]]:
    out = set()
    for d in own_dirs(model):
        if (d / "metrics.json").exists():
            c = yaml.safe_load(open(d / "config.yaml"))
            out.add((c["vignette"], float(c["temperature"])))
    return out


def clean_failed(model: str) -> None:
    for d in own_dirs(model):
        if not (d / "metrics.json").exists():
            shutil.rmtree(d)


async def main(model: str) -> None:
    BATCH.mkdir(parents=True, exist_ok=True)
    clean_failed(model)
    temps = sorted(set(DEFAULT_TEMPS + [therapy_temp(model)]))
    have = done(model)
    todo = [(v, t) for v in VIGNETTES for t in temps if (v, t) not in have]
    print(f"{model}: {len(todo)} of {len(VIGNETTES) * len(temps)} conditions to run", flush=True)
    for v, t in todo:
        for attempt in range(8):
            try:
                r = await run_single(model, v, find_slice_path(v, 2), TRIALS, t, BATCH)
                print(f"OK {model} {v} T={t}: J={r['jaccard']:.3f} B={r['bertscore']:.3f} "
                      f"A={r['alignment']} ({r['elapsed']}s)", flush=True)
                break
            except Exception as e:
                clean_failed(model)
                wait = min(60 * 2 ** attempt, 900)
                print(f"FAIL {model} {v} T={t} attempt {attempt + 1}: {str(e)[:160]} -> wait {wait}s", flush=True)
                await asyncio.sleep(wait)
        else:
            print(f"GAVE UP {model} {v} T={t}", flush=True)
    print(f"{model} done: {len(done(model))}/{len(VIGNETTES) * len(temps)}", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in MODELS:
        sys.exit(f"usage: run_nemotron.py {{{'|'.join(MODELS)}}}")
    asyncio.run(main(sys.argv[1]))
