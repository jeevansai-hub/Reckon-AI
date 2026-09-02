# Workflow: Verify the dataset is real, intact, and matches the schema

Run this after any fresh dataset download, and any time the dataset is updated.
Two real bugs have already been caught by exactly these two checks — do not skip them.

## 1. Verify the CSV schema

```bash
PYTHONIOENCODING=utf-8 python scripts/verify_schema.py
```

Prints the real header row of one V- and one S- file next to the documented schema in
`src/io_vnbd/data/schema.py`.

**Good result:** `Real columns: 29 / Documented columns: 29` for the V-file,
`24 / 24` for the S-file, and every row lining up positionally with a sensible name.

**If it drifts:** fix `src/io_vnbd/data/schema.py` FIRST — every other module imports
column names from there, so a wrong entry silently mislabels data everywhere downstream
rather than raising an error.

> Bug this already caught: `orient_pitch` and `orient_roll` were swapped relative to the
> real file order (Yaw, Pitch, Roll). Nothing would have crashed — the data would just
> have been quietly wrong.

## 2. Verify every run loads

```bash
PYTHONIOENCODING=utf-8 python scripts/explore_dataset.py
```

Loads all 72 synchronised runs (not just a sample), checking schema, NaNs, sampling
rate, and distance per run. Writes `reports/eda_run_summary.csv`.

**Good result — these are the known-correct numbers:**

| Check | Expected |
|---|---|
| Runs loaded | 72, with 0 failures |
| NaN IMU cells | 0 across all runs |
| Median sample interval | exactly 0.1 s (10 Hz), zero variance |
| Total distance | ~1,344 km |
| Total driving time | ~29.7 hours |
| Driver E share | 89% of runs, 67% of distance |

Anything different means the dataset changed or the download is incomplete — investigate
before training on it.

> Bug this already caught: `pd.read_csv` had no encoding set, and every real S-file header
> contains a mis-encoded `m/s²` byte. This crashed 100% of runs — but only showed up when
> loading files in bulk, never when testing a single hand-picked file.

## 3. Sanity facts worth remembering

- `Vw1` and `Vw15` are the **stationary calibration runs** (0.05 km and 0.01 km travelled).
  They are used for IMU bias calibration and should never be treated as driving data.
- Nine runs are under one minute. At a 100-row (10 s) window they contribute barely one
  training window each — do not be surprised when some categories yield little data.
- The heavy Driver E skew is why the train/val/test split holds out whole driver groups.
  Never switch to a random row split: adjacent rows in one drive are near-duplicates and
  would leak the test set into training, producing fake-good accuracy.
