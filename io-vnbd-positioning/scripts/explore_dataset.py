"""
Full-dataset exploratory analysis -- run this to sanity-check every single
run in the Synchronised dataset, not just one sample file.

Checks, per run:
  - can the V-/S- pair actually be found and loaded (schema assertion passes)
  - row count, implied duration, implied sampling rate
  - NaN counts per channel
  - rough distance travelled (haversine on raw lat/lon, not the local
    projection -- this script is a sanity check, not the real pipeline)

Then rolls everything up per category, to check the paper's own scale and
driver-skew claims against the actual files on disk.

Usage:
    python scripts/explore_dataset.py
"""

import math
from pathlib import Path

import pandas as pd

from io_vnbd.data.loader import load_run

ROOT = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "IO-VNBD"
    / "Synchronised V abd S datasets"
    / "Categorised IOVNB Dataset"
)

CATEGORY_DRIVER = {
    "S": "Driver A",
    "M": "Driver B",
    "Y": "Driver D",
    "Vf": "Driver E",
    "Vta": "Driver E",
    "Vtb": "Driver E",
    "Vw": "Driver E",
}


def haversine_km(lat, lon):
    lat = lat.dropna().to_numpy()
    lon = lon.dropna().to_numpy()
    if len(lat) < 2:
        return 0.0
    R = 6371.0
    lat_r = [math.radians(x) for x in lat]
    lon_r = [math.radians(x) for x in lon]
    total = 0.0
    for i in range(1, len(lat_r)):
        dlat = lat_r[i] - lat_r[i - 1]
        dlon = lon_r[i] - lon_r[i - 1]
        a = math.sin(dlat / 2) ** 2 + math.cos(lat_r[i - 1]) * math.cos(lat_r[i]) * math.sin(dlon / 2) ** 2
        total += 2 * R * math.asin(min(1, math.sqrt(a)))
    return total


def discover_runs(category_dir: Path):
    """Find run names from actual V-*.csv filenames, not folder names --
    folder names and file names don't always match (e.g. folder 'Vta01a'
    contains 'V-Vta1a.csv')."""
    runs = []
    for f in category_dir.rglob("V-*.csv"):
        run_name = f.stem[2:]  # strip "V-"
        runs.append(run_name)
    return sorted(set(runs))


def main():
    rows = []
    failures = []

    for category_dir in sorted(ROOT.iterdir()):
        if not category_dir.is_dir():
            continue
        category = category_dir.name.split(" ")[0]
        run_names = discover_runs(category_dir)

        for run_name in run_names:
            try:
                v_df, s_df = load_run(ROOT, run_name)
            except Exception as e:
                failures.append((category, run_name, str(e)))
                continue

            n_rows = len(s_df)
            dt = s_df["time_since_start_ms"].diff().median() / 1000.0 if n_rows > 1 else float("nan")
            duration_s = n_rows * dt if pd.notna(dt) else float("nan")
            dist_km = haversine_km(v_df["lat"], v_df["lon"])

            imu_cols = ["accel_x", "accel_y", "accel_z", "gyro_yaw", "gyro_pitch", "gyro_roll"]
            nan_counts = s_df[imu_cols].isna().sum().sum()

            rows.append(
                {
                    "category": category,
                    "driver": CATEGORY_DRIVER.get(category, "?"),
                    "run": run_name,
                    "n_rows": n_rows,
                    "median_dt_s": round(dt, 3) if pd.notna(dt) else None,
                    "duration_min": round(duration_s / 60, 1) if pd.notna(duration_s) else None,
                    "dist_km": round(dist_km, 2),
                    "nan_imu_cells": int(nan_counts),
                }
            )

    df = pd.DataFrame(rows)

    print("=" * 80)
    print(f"Runs successfully loaded: {len(df)}   Runs failed to load: {len(failures)}")
    print("=" * 80)

    if failures:
        print("\n--- FAILURES ---")
        for cat, run, err in failures:
            print(f"  [{cat}] {run}: {err}")

    print("\n--- PER-CATEGORY ROLLUP ---")
    rollup = (
        df.groupby(["category", "driver"])
        .agg(
            n_runs=("run", "count"),
            total_rows=("n_rows", "sum"),
            total_minutes=("duration_min", "sum"),
            total_km=("dist_km", "sum"),
            total_nan_imu_cells=("nan_imu_cells", "sum"),
        )
        .round(1)
    )
    print(rollup.to_string())

    print("\n--- TOTALS ---")
    print(f"Total runs: {df['n_rows'].count()}")
    print(f"Total driving time: {df['duration_min'].sum() / 60:.1f} hours")
    print(f"Total distance: {df['dist_km'].sum():.1f} km")
    print(f"Total NaN IMU cells across all runs: {df['nan_imu_cells'].sum()}")

    print("\n--- SAMPLING RATE CHECK (median dt per run, should cluster near 0.1s = 10Hz) ---")
    print(df["median_dt_s"].describe().to_string())

    out_path = Path(__file__).resolve().parent.parent / "reports" / "eda_run_summary.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"\nFull per-run table written to {out_path}")


if __name__ == "__main__":
    main()
