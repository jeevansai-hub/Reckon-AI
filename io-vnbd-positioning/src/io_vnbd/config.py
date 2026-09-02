"""
Loads the YAML files under configs/ into plain dicts.

Not yet wired into any pipeline code -- src/io_vnbd/data/windowing.py and
src/io_vnbd/data/bias.py still hold their own hardcoded constants as the
current source of truth. This loader exists so Milestone 2 training code
can read from configs/*.yaml from day one instead of hardcoding new
constants of its own; migrating windowing.py/bias.py to read from here
too is a follow-up, not done as part of this restructure.
"""
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "configs"


def load_config(name: str) -> dict:
    """name is the file stem, e.g. load_config('model') reads configs/model.yaml"""
    path = CONFIG_DIR / f"{name}.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
