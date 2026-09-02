# Reckon-AI — IO-VNBD GPS-denied positioning

GPS-denied ground-vehicle positioning using the IO-VNBD dataset (smartphone IMU → displacement estimation, evaluated against vehicle CAN-bus/GPS ground truth).

Full data reference: [`Project-Context/IO-VNBD-Repository-Breakdown.md`](Project-Context/IO-VNBD-Repository-Breakdown.md) — read that first if any column name or run here is unfamiliar. Product/technical spec: see the `PRD — AI-ML Intelligent Dead Reckoning System` page in the project's Notion workspace (SRS sections SRS-1 through SRS-7 map directly onto the packages below).

## Project layout

```
Reckon-AI/
├── pyproject.toml            <- dependencies + tool config (replaces requirements.txt)
├── .pre-commit-config.yaml   <- auto-lint/format before each commit (ruff, free)
├── .github/workflows/ci.yml  <- lint + data-free tests on every push (GitHub Actions, free)
├── configs/
│   ├── data.yaml              <- dataset root, category/driver map, train/val/test split
│   ├── model.yaml              <- window size, stride, LSTM hyperparameters
│   └── paths.yaml              <- where models/reports/logs get written
├── Project-Context/            <- project docs, dataset reference
├── .agent/workflows/           <- repeatable task playbooks
├── data/
│   └── IO-VNBD/                <- the cloned dataset repo goes here (gitignored, not committed)
├── src/io_vnbd/                 <- the installable package
│   ├── config.py                <- loads configs/*.yaml
│   ├── data/
│   │   ├── schema.py             <- documented V-/S- CSV column names
│   │   ├── loader.py             <- find + load a synchronized run pair
│   │   ├── projection.py         <- lat/lon -> local metric (x, y) frame
│   │   ├── bias.py                <- IMU bias calibration from the stationary runs
│   │   └── windowing.py          <- sliding windows + train/val/test category split
│   ├── datasets/torch_dataset.py  <- PyTorch Dataset/DataLoader batching (not yet built)
│   ├── models/lstm.py             <- baseline LSTM displacement model
│   ├── baseline/dead_reckoning.py <- classical double-integration baseline (not yet built)
│   ├── mapmatch/matcher.py        <- HMM/Viterbi road-network snapping (not yet built)
│   ├── fusion/ekf.py              <- GPS-outage simulation + EKF resync (not yet built)
│   ├── evaluation/metrics.py      <- ATE / RPE metrics
│   └── training/train.py          <- the training loop (not yet built)
├── scripts/                     <- thin CLI entrypoints only, no logic
│   ├── verify_schema.py          <- run this FIRST after pulling data
│   ├── explore_dataset.py        <- full-dataset EDA (every run, not just one file)
│   ├── run_baseline.py           <- Milestone 2 (not yet built)
│   ├── run_training.py           <- Milestone 2 (not yet built)
│   ├── run_evaluation.py         <- Milestone 6 (not yet built)
│   └── run_demo.py               <- Milestone 7 (not yet built)
├── notebooks/                    <- exploration, empty for now
├── reports/                      <- generated EDA/plots/tables (eda_run_summary.csv lives here)
├── tests/                        <- mirrors src/io_vnbd/ 1:1
│   └── test_model_smoke.py       <- data-free sanity test
└── models/                       <- trained checkpoints go here (gitignored)
```

## Step 0 — Prerequisites

- Python 3.11+ (`python --version`)
- Git with Git LFS support (`git lfs version` — if missing, install from https://git-lfs.com)

## Step 1 — Get the dataset

The dataset lives in a **separate repo** (`onyekpeu/IO-VNBD`), not this project — it is **not** committed here (see `.gitignore`), both because of GitHub's LFS storage/bandwidth limits and because the source repo ships with no license file, so redistributing the raw data from this repo hasn't been cleared. Clone it directly from the source instead:

```bash
git lfs install
git clone https://github.com/onyekpeu/IO-VNBD.git data/IO-VNBD
cd data/IO-VNBD
git lfs pull
cd ../..
```

A plain `git clone` alone only gives you ~130-byte LFS pointer files, not real CSVs — the `git lfs pull` step is required. Expect this to pull down **~2.2 GB** of real data (727 LFS-tracked files: both the `Synchronised V and S datasets` and `Unsynchronised V and S Dataset` folders, each also available as a `.zip`) and to take a while depending on connection speed.

This project's pipeline only uses the **Synchronised** dataset (see §14 of `Project-Context/00-PROJECT-CONTEXT.md` — unsynchronized runs have no matching ground truth to train against), so if disk space or bandwidth is tight, it's safe to delete `data/IO-VNBD/Unsynchronised V and S Dataset*` after cloning.

Sanity-check real bytes landed (should be several MB, not ~130 bytes):
```bash
ls -la "data/IO-VNBD/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S1/"
```

## Step 2 — Python environment

From the repo root:

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; use .venv\Scripts\activate.bat for cmd.exe
pip install -e ".[dev]"
```

This installs the `io_vnbd` package in editable mode (so `import io_vnbd...` works from anywhere — scripts, tests, notebooks — without `sys.path` hacks) plus dev tools (`pytest`, `ruff`).

Optional, once: `pre-commit install` — auto-runs lint/format on every commit.

## Step 3 — Confirm the environment works (no data needed yet)

```bash
pytest tests/test_model_smoke.py -v
```
This builds the LSTM model and runs a forward pass on random data, plus checks the evaluation metrics run — if this fails, it's an environment/dependency problem, not a data problem. Fix this before moving on.

## Step 4 — Verify the real CSV schema matches what's documented

The PDF documentation and the actual CSV header are not guaranteed to match 1:1 (a known typo exists in the orientation column labels — see the breakdown doc, §6 — already caught and fixed in `src/io_vnbd/data/schema.py`). Check this **before** trusting any loader code, and re-run it any time the dataset is updated:

```bash
python scripts/verify_schema.py
```
Read the output. If column counts or names don't line up, fix `src/io_vnbd/data/schema.py` first — every other module imports from there.

## Step 4b — Full-dataset sanity check

```bash
python scripts/explore_dataset.py
```
Loads and checks every run (not just one sample file): schema, NaNs, sampling rate consistency, distance travelled, per-category rollup. Writes `reports/eda_run_summary.csv`. Already run once — confirmed all 72 runs load cleanly, zero NaNs, a consistent 10Hz sample rate, and Driver E accounting for 89% of runs / 67% of total distance.

## Step 5 — Load one run and look at it

```python
from pathlib import Path
from io_vnbd.data.loader import load_run

root = Path("data/IO-VNBD/Synchronised V abd S datasets/Categorised IOVNB Dataset")
v_df, s_df = load_run(root, "S1")

print(v_df[["lat", "lon", "velocity_kmh"]].head())
print(s_df[["accel_x", "accel_y", "accel_z", "gravity_x", "gravity_y", "gravity_z"]].head())
```
Do this in a notebook (`notebooks/01_explore_one_run.ipynb`) first, not a script — you want to eyeball plots (GPS track, acceleration over time) before writing pipeline code around assumptions that might be wrong.

## Step 6 — Project GPS to a local metric frame

```python
from io_vnbd.data.projection import project_to_local_xy

xy = project_to_local_xy(v_df["lat"], v_df["lon"])
```
Needed because raw lat/lon degrees aren't linear distance — every displacement target and every ATE/RPE calculation depends on this.

## Step 7 — Calibrate IMU bias

```python
from io_vnbd.data.bias import per_run_bias, combined_bias, apply_bias_correction

biases = per_run_bias(root)
print(biases["Vw1"])
print(biases["Vw15"])   # compare these two before combining -- see breakdown doc §3.7

bias = combined_bias(root)
s_df_corrected = apply_bias_correction(s_df, bias)
```

## Step 8 — Build windows and the train/val/test split

```python
from io_vnbd.data.windowing import make_windows, TRAIN_CATEGORIES, VAL_CATEGORIES, TEST_CATEGORIES

windows = make_windows(s_df_corrected, xy, run_name="S1", window_size=100, stride=50)
```
Do this per-run across every run in `TRAIN_CATEGORIES` / `VAL_CATEGORIES` / `TEST_CATEGORIES` (see the category-to-folder mapping in the breakdown doc §3, mirrored in `configs/data.yaml`) to build your full dataset — `src/io_vnbd/datasets/torch_dataset.py` (a `Dataset`/`DataLoader` wrapper around `Window` objects) is the next thing to implement.

## Step 9 — Train the model, and the classical baseline

Neither is implemented yet (`src/io_vnbd/training/train.py`, `src/io_vnbd/baseline/dead_reckoning.py`). Build both **in parallel** — the baseline needs zero training time and guarantees a comparison number exists even if training runs long. See the PRD's Milestone 2 for the full rationale.

## Step 10 — Evaluate

```python
from io_vnbd.evaluation.metrics import integrate_trajectory, absolute_trajectory_error, relative_pose_error

pred_path = integrate_trajectory(predicted_displacements)
true_path = integrate_trajectory(true_displacements)

print("ATE:", absolute_trajectory_error(pred_path, true_path))
print("RPE:", relative_pose_error(pred_path, true_path, delta=10))
```
Report this **per category** (S, M, Y, Vf, Vta, Vtb, Vw) — that's the whole reason the dataset is organized that way.

## What's already built vs. what's next

| Done | Module | Not yet built |
|---|---|---|
| ✅ | `io_vnbd.data.schema`, `io_vnbd.data.loader` | — |
| ✅ | `io_vnbd.data.bias` | — |
| ✅ | `io_vnbd.data.windowing` (windowing + split constants) | `io_vnbd.datasets.torch_dataset` — PyTorch `Dataset`/`DataLoader` wrapper |
| ✅ | `io_vnbd.models.lstm` | — |
| ✅ | `io_vnbd.evaluation.metrics` | — |
| ✅ | `scripts/verify_schema.py`, `scripts/explore_dataset.py` | — |
| — | — | `io_vnbd.training.train` — the actual training loop |
| — | — | `io_vnbd.baseline.dead_reckoning` — classical comparison baseline |
| — | — | `io_vnbd.mapmatch.matcher` — HMM/Viterbi road-network snapping |
| — | — | `io_vnbd.fusion.ekf` — GPS-outage simulation + smooth resync |
| — | — | `notebooks/01_explore_one_run.ipynb` — exploratory plots |
