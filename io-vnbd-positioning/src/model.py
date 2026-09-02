"""
Baseline LSTM dead-reckoning-by-network model, per
IO-VNBD-Analysis/IO-VNBD-Repository-Breakdown.md section 10, step 6.

Input:  windowed, gravity-corrected IMU sequence
        (accel_x/y/z minus gravity_x/y/z, gyro_yaw/pitch/roll) -> 6 channels
Output: relative displacement (dx, dy) over the window, in a local metric
        frame derived from the V- GPS ground truth.
"""
import torch
import torch.nn as nn


class InertialDisplacementNet(nn.Module):
    def __init__(self, in_channels: int = 6, hidden: int = 128, layers: int = 2):
        super().__init__()
        self.lstm = nn.LSTM(in_channels, hidden, layers, batch_first=True)
        self.head = nn.Linear(hidden, 2)  # (dx, dy)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, in_channels)
        out, _ = self.lstm(x)
        return self.head(out[:, -1, :])
