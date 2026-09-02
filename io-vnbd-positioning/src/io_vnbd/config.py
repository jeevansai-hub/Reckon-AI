"""
Loads the YAML files under configs/ into plain dicts.

configs/*.yaml is the source of truth for split categories, bias
calibration runs, windowing, and model hyperparameters -- io_vnbd.data.
windowing, io_vnbd.data.bias, and io_vnbd.models.lstm all read their
defaults from here via load_config(), so changing an experiment setting
means editing a YAML file, not hunting through source.
"""

from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "configs"


def load_config(name: str) -> dict:
    """name is the file stem, e.g. load_config('model') reads configs/model.yaml"""
    path = CONFIG_DIR / f"{name}.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
