"""
Baseline LSTM dead-reckoning-by-network model, per
Project-Context/IO-VNBD-Repository-Breakdown.md section 10, step 6.

Input:  windowed, gravity-corrected IMU sequence
        (accel_x/y/z minus gravity_x/y/z, gyro_yaw/pitch/roll) -> 6 channels
Output: relative displacement (dx, dy) over the window, in a local metric
        frame derived from the V- GPS ground truth.
"""

import torch
import torch.nn as nn

from io_vnbd.config import load_config

_model_cfg = load_config("model")["model"]


class InertialDisplacementNet(nn.Module):
    def __init__(
        self,
        in_channels: int = _model_cfg["in_channels"],
        hidden: int = _model_cfg["hidden_size"],
        layers: int = _model_cfg["num_layers"],
    ):
        super().__init__()
        self.lstm = nn.LSTM(in_channels, hidden, layers, batch_first=True)
        self.head = nn.Linear(hidden, 2)  # (dx, dy)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, in_channels)
        out, _ = self.lstm(x)
        return self.head(out[:, -1, :])
