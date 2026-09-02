"""
Fixed-length sliding-window generation over a run, plus the
driver/category-based train/val/test split described in
Project-Context/IO-VNBD-Repository-Breakdown.md section 10, step 5.

Splitting by category (not by random row) matters because adjacent rows
in the same drive are highly correlated -- a random row split would leak
the test trajectory into training.
"""

from dataclasses import dataclass

import pandas as pd

from io_vnbd.config import load_config

_split = load_config("data")["split"]
_model_cfg = load_config("model")["windowing"]

TRAIN_CATEGORIES = _split["train_categories"]
VAL_CATEGORIES = _split["val_categories"]  # small defensive-driver runs: style-generalization check
TEST_CATEGORIES = _split["test_categories"]  # entire category held out: unseen-route test


@dataclass
class Window:
    imu: pd.DataFrame  # gravity-corrected accel + gyro, window_size rows
    dx: float  # ground-truth displacement (metres, local frame) over the window
    dy: float
    run_name: str
    start_row: int


def make_windows(
    s_df: pd.DataFrame,
    xy: pd.DataFrame,
    run_name: str,
    window_size: int = _model_cfg["window_size"],
    stride: int = _model_cfg["stride"],
) -> list[Window]:
    """window_size=100 rows = 10s at 10Hz. Shrink this if you need faster-updating
    displacement predictions; grow it if per-window drift is too noisy at 10s.

    `xy` must be a DataFrame with local-metric-frame `x`, `y` columns aligned
    row-for-row with `s_df` (see notebooks/01_explore_one_run.ipynb for how
    to project V- GPS lat/lon into that frame).
    """
    windows = []
    n = len(s_df)
    for start in range(0, n - window_size, stride):
        end = start + window_size
        imu_slice = s_df.iloc[start:end]
        dx = xy["x"].iloc[end - 1] - xy["x"].iloc[start]
        dy = xy["y"].iloc[end - 1] - xy["y"].iloc[start]
        windows.append(Window(imu=imu_slice, dx=dx, dy=dy, run_name=run_name, start_row=start))
    return windows
