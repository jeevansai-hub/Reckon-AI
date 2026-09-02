"""
Training loop: batches from io_vnbd.datasets.torch_dataset ->
io_vnbd.models.lstm.InertialDisplacementNet -> MSE loss -> Adam optimizer,
saving checkpoints to models/. Not yet implemented -- see PRD SRS-3,
Milestone 2.
"""
