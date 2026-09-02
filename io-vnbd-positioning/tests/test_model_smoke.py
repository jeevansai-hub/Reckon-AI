"""
Data-free smoke test -- confirms the model builds and runs a forward pass
with the right shapes, without needing the (large, LFS-gated) dataset
downloaded. Run this immediately after `pip install -e .[dev]`
to confirm your environment is sane before pulling any data.

Usage:
    pytest tests/test_model_smoke.py -v
"""
import torch

from io_vnbd.models.lstm import InertialDisplacementNet


def test_forward_pass_shape():
    model = InertialDisplacementNet(in_channels=6, hidden=32, layers=1)
    batch = torch.randn(4, 100, 6)  # (batch=4, seq_len=100, channels=6)
    out = model(batch)
    assert out.shape == (4, 2), f"expected (4, 2), got {tuple(out.shape)}"


def test_evaluate_metrics_run():
    import numpy as np

    from io_vnbd.evaluation.metrics import (
        absolute_trajectory_error,
        integrate_trajectory,
        relative_pose_error,
    )

    displacements = np.random.randn(50, 2) * 0.1
    pred_xy = integrate_trajectory(displacements)
    true_xy = pred_xy + np.random.randn(*pred_xy.shape) * 0.01

    ate = absolute_trajectory_error(pred_xy, true_xy)
    rpe = relative_pose_error(pred_xy, true_xy, delta=5)
    assert ate >= 0
    assert rpe >= 0
