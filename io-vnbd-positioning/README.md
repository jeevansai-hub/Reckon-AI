# io-vnbd-positioning

GPS-denied ground-vehicle positioning using the IO-VNBD dataset (smartphone IMU → displacement estimation, evaluated against vehicle CAN-bus/GPS ground truth).

Full data reference: [`../IO-VNBD-Analysis/IO-VNBD-Repository-Breakdown.md`](../IO-VNBD-Analysis/IO-VNBD-Repository-Breakdown.md) — read that first if any column name or run here is unfamiliar.

## Project layout

```
io-vnbd-positioning/
├── requirements.txt
├── .gitignore
├── data/
│   └── IO-VNBD/              <- the cloned dataset repo goes here (gitignored, not committed)
├── src/
│   ├── schema.py             <- documented V-/S- CSV column names
│   ├── loader.py             <- find + load a synchronized run pair
│   ├── bias.py                <- IMU bias calibration from the stationary runs
│   ├── windowing.py          <- sliding windows + train/val/test category split
│   ├── model.py               <- baseline LSTM displacement model
│   └── evaluate.py            <- ATE / RPE metrics
├── scripts/
│   ├── verify_schema.py      <- run this FIRST after pulling data
│   └── project_gps.py        <- lat/lon -> local metric (x, y) frame
├── notebooks/                <- exploration, empty for now
├── tests/
│   └── test_model_smoke.py   <- data-free sanity test
└── models/                   <- trained checkpoints go here (gitignored)
```

## Step 0 — Prerequisites

- Python 3.11+ (`python --version`)
- Git with Git LFS support (`git lfs version` — if missing, install from https://git-lfs.com)

## Step 1 — Get the dataset

The dataset lives in a **separate repo** (`onyekpeu/IO-VNBD`), not this project. It uses Git LFS, so a plain clone gives you empty pointer files, not real CSVs.

```bash
git lfs install
git clone https://github.com/onyekpeu/IO-VNBD.git data/IO-VNBD
cd data/IO-VNBD
git lfs pull
cd ../..
```

Sanity-check real bytes landed (should be several MB, not ~130 bytes):
```bash
ls -la "data/IO-VNBD/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S1/"
```

## Step 2 — Python environment

From `io-vnbd-positioning/`:

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; use .venv\Scripts\activate.bat for cmd.exe
pip install -r requirements.txt
```

## Step 3 — Confirm the environment works (no data needed yet)

```bash
pytest tests/test_model_smoke.py -v
```
This builds the LSTM model and runs a forward pass on random data, plus checks the evaluation metrics run — if this fails, it's an environment/dependency problem, not a data problem. Fix this before moving on.

## Step 4 — Verify the real CSV schema matches what's documented

The PDF documentation and the actual CSV header are not guaranteed to match 1:1 (a known typo exists in the gyroscope column labels — see the breakdown doc, §6). Check this **before** trusting any loader code:

```bash
python scripts/verify_schema.py
```
Read the output. If column counts or names don't line up, fix `src/schema.py` first — every other script imports from there.

## Step 5 — Load one run and look at it

```python
from pathlib import Path
from src.loader import load_run

root = Path("data/IO-VNBD/Synchronised V abd S datasets/Categorised IOVNB Dataset")
v_df, s_df = load_run(root, "S1")

print(v_df[["lat", "lon", "velocity_kmh"]].head())
print(s_df[["accel_x", "accel_y", "accel_z", "gravity_x", "gravity_y", "gravity_z"]].head())
```
Do this in a notebook (`notebooks/01_explore_one_run.ipynb`) first, not a script — you want to eyeball plots (GPS track, acceleration over time) before writing pipeline code around assumptions that might be wrong.

## Step 6 — Project GPS to a local metric frame

```python
from scripts.project_gps import project_to_local_xy

xy = project_to_local_xy(v_df["lat"], v_df["lon"])
```
Needed because raw lat/lon degrees aren't linear distance — every displacement target and every ATE/RPE calculation depends on this.

## Step 7 — Calibrate IMU bias

```python
from src.bias import per_run_bias, combined_bias, apply_bias_correction

biases = per_run_bias(root)
print(biases["Vw1"])
print(biases["Vw15"])   # compare these two before combining -- see breakdown doc §3.7

bias = combined_bias(root)
s_df_corrected = apply_bias_correction(s_df, bias)
```

## Step 8 — Build windows and the train/val/test split

```python
from src.windowing import make_windows, TRAIN_CATEGORIES, VAL_CATEGORIES, TEST_CATEGORIES

windows = make_windows(s_df_corrected, xy, run_name="S1", window_size=100, stride=50)
```
Do this per-run across every run in `TRAIN_CATEGORIES` / `VAL_CATEGORIES` / `TEST_CATEGORIES` (see the category-to-folder mapping in the breakdown doc §3) to build your full dataset — a `Dataset`/`DataLoader` wrapper around `Window` objects is the natural next file to write (`src/dataset.py`, not yet created).

## Step 9 — Train the baseline model

Not yet written as a script (`src/train.py` placeholder) — once `src/dataset.py` exists, a standard PyTorch loop: batch windows → `InertialDisplacementNet` → MSE loss against `(dx, dy)` → Adam optimizer. See the breakdown doc §10 step 6 for the model skeleton this project's `src/model.py` already implements.

## Step 10 — Evaluate

```python
from src.evaluate import integrate_trajectory, absolute_trajectory_error, relative_pose_error

pred_path = integrate_trajectory(predicted_displacements)
true_path = integrate_trajectory(true_displacements)

print("ATE:", absolute_trajectory_error(pred_path, true_path))
print("RPE:", relative_pose_error(pred_path, true_path, delta=10))
```
Report this **per category** (S, M, Y, Vf, Vta, Vtb, Vw) — that's the whole reason the dataset is organized that way.

## What's already built vs. what's next

| Done | File | Not yet built |
|---|---|---|
| ✅ | `src/schema.py`, `src/loader.py` | — |
| ✅ | `src/bias.py` | — |
| ✅ | `src/windowing.py` (windowing + split constants) | `src/dataset.py` — PyTorch `Dataset`/`DataLoader` wrapper around `Window` |
| ✅ | `src/model.py` | — |
| ✅ | `src/evaluate.py` | — |
| ✅ | `scripts/verify_schema.py`, `scripts/project_gps.py` | — |
| — | — | `src/train.py` — the actual training loop |
| — | — | `notebooks/01_explore_one_run.ipynb` — exploratory plots |
| — | — | classical wheel-odometry baseline computed directly from `V-` columns 11–15, for comparison against the neural model (see breakdown doc §5) |
