# Workflow: Set up this project from scratch

Goal: go from a fresh clone to a working environment that can load real dataset runs.
Expect ~30-60 minutes, mostly waiting on the dataset download.

## 1. Prerequisites

- Python 3.11+ (`python --version`)
- Node.js 18+ (only needed for regenerating diagrams, not for the pipeline)
- Git LFS (`git lfs version`) — install from https://git-lfs.com if missing

## 2. Get the dataset

The dataset is **not** in this repo (GitHub LFS limits, plus the source repo ships no
license, so redistributing it from here is not cleared). Clone it from the source:

```bash
cd io-vnbd-positioning
git lfs install
git clone https://github.com/onyekpeu/IO-VNBD.git data/IO-VNBD
cd data/IO-VNBD
git lfs pull
cd ../..
```

`git lfs pull` is required — a plain clone only gives ~130-byte pointer files.
Expect ~2.2 GB across 727 files.

Only the **Synchronised** set is used (unsynchronised runs have no ground truth), so
`data/IO-VNBD/Unsynchronised V and S Dataset*` can be deleted if space is tight.

## 3. Install the package

From `io-vnbd-positioning/`:

```bash
python -m venv .venv
source .venv/Scripts/activate    # Windows Git Bash; .venv\Scripts\activate.bat for cmd.exe
pip install -e ".[dev]"
```

Editable install matters: it puts `io_vnbd` on the path so scripts, tests, and notebooks
all import the same code with no `sys.path` hacks.

Optional but recommended, once: `pre-commit install` (auto-runs ruff on every commit).

## 4. Confirm it works

```bash
python -m pytest tests/test_model_smoke.py -v
```

Builds the LSTM, runs a forward pass on random data, exercises the metrics. Needs no
dataset. If this fails it is an environment problem, not a data problem — fix it here
before going further.

## 5. Confirm the data is real and intact

Run the data verification workflow next: [`verify-data.md`](verify-data.md).

## Gotchas already hit (do not rediscover these)

- **Scripts are not on PATH** on this Windows setup. Use `python -m pytest`, `python -m ruff`,
  `python -m pre_commit` rather than the bare command names.
- **Console encoding**: prefix with `PYTHONIOENCODING=utf-8` when running scripts that print
  dataset column names, or Windows cp1252 will crash on the degree/micro symbols.
- **Folder names and file names differ** in the dataset (folder `Vta01a` contains `V-Vta1a.csv`).
  Always discover runs from actual filenames, never from folder names.
