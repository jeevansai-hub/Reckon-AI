"""
Trajectory-level evaluation metrics: Absolute Trajectory Error (ATE) and
Relative Pose Error (RPE), reported per category as recommended in
Project-Context/IO-VNBD-Repository-Breakdown.md section 10, step 7.
"""

import numpy as np


def absolute_trajectory_error(pred_xy: np.ndarray, true_xy: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.sum((pred_xy - true_xy) ** 2, axis=1))))


def relative_pose_error(pred_xy: np.ndarray, true_xy: np.ndarray, delta: int = 10) -> float:
    pred_rel = pred_xy[delta:] - pred_xy[:-delta]
    true_rel = true_xy[delta:] - true_xy[:-delta]
    return float(np.sqrt(np.mean(np.sum((pred_rel - true_rel) ** 2, axis=1))))


def integrate_trajectory(
    displacements_xy: np.ndarray, start_xy: tuple[float, float] = (0.0, 0.0)
) -> np.ndarray:
    """Cumulative sum of per-window (dx, dy) predictions into an absolute path."""
    return np.cumsum(displacements_xy, axis=0) + np.array(start_xy)
