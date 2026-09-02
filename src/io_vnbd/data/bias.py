"""
IMU bias calibration using the dataset's two dedicated stationary runs
(Vw1, Vw15) -- see Project-Context/IO-VNBD-Repository-Breakdown.md section 3.7
for why these two specifically, and why they should be inspected separately
before being combined.
"""

from pathlib import Path

import pandas as pd

from io_vnbd.config import load_config

from .loader import load_run

BIAS_CHANNELS = ["accel_x", "accel_y", "accel_z", "gyro_yaw", "gyro_pitch", "gyro_roll"]
STATIONARY_RUNS = load_config("data")["bias_calibration"]["stationary_runs"]


def per_run_bias(root: Path) -> dict[str, pd.Series]:
    """Bias estimate from each stationary run separately.

    Compare these two before combining -- Vw1 (day, tyre pressure C, 34 min)
    and Vw15 (night, tyre pressure D, 2.3 min) differ enough that a large
    discrepancy is a real finding (temperature-dependent bias drift), not
    a bug.
    """
    biases = {}
    for run in STATIONARY_RUNS:
        _, s_df = load_run(root, run)
        biases[run] = s_df[BIAS_CHANNELS].mean()
    return biases


def combined_bias(root: Path) -> pd.Series:
    """Row-weighted average bias across both stationary runs."""
    frames = []
    for run in STATIONARY_RUNS:
        _, s_df = load_run(root, run)
        frames.append(s_df[BIAS_CHANNELS])
    return pd.concat(frames).mean()


def apply_bias_correction(s_df: pd.DataFrame, bias: pd.Series) -> pd.DataFrame:
    """Subtract the calibrated bias from a run's IMU channels. Returns a copy."""
    corrected = s_df.copy()
    for ch in BIAS_CHANNELS:
        corrected[ch] = corrected[ch] - bias[ch]
    return corrected
