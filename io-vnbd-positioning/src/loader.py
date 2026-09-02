"""
Locate and load a synchronized V-/S- run pair from a local IO-VNBD checkout.

Usage:
    from pathlib import Path
    from src.loader import load_run

    root = Path("data/IO-VNBD/Synchronised V abd S datasets/Categorised IOVNB Dataset")
    v_df, s_df = load_run(root, "Vw4")
"""
from pathlib import Path

import pandas as pd

from .schema import S_COLUMNS, V_COLUMNS


def find_run_files(root: Path, run_name: str) -> tuple[Path, Path]:
    """Case-insensitive search for a run's V- and S- CSVs under `root`.

    The source repo is inconsistent about capitalization (e.g. some
    Vta/Vtb files are literally named `V-vta12.csv` not `V-Vta12.csv`),
    so this deliberately does not use a case-sensitive glob.
    """
    candidates = list(root.rglob("*.csv"))
    v_matches = [f for f in candidates if f.name.lower() == f"v-{run_name}.csv".lower()]
    s_matches = [f for f in candidates if f.name.lower() == f"s-{run_name}.csv".lower()]

    if not v_matches:
        raise FileNotFoundError(f"No V-{run_name}.csv found under {root}")
    if not s_matches:
        raise FileNotFoundError(f"No S-{run_name}.csv found under {root}")

    return v_matches[0], s_matches[0]


def load_run(root: Path, run_name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load one synchronized run and rename columns per the documented schema.

    Raises an AssertionError if the real file's column count doesn't match
    the documented schema -- that's a deliberate early failure so a schema
    mismatch is caught here, not silently mislabeling data downstream.
    """
    v_file, s_file = find_run_files(root, run_name)

    # encoding_errors="replace": every real S-*.csv header has a mis-encoded
    # unit symbol (literal byte 0xB2 for "m/s²" instead of valid UTF-8) --
    # confirmed across the full dataset, not a one-off file. Harmless here
    # since the header text is immediately discarded below.
    v_df = pd.read_csv(v_file, header=0, encoding="utf-8", encoding_errors="replace")
    s_df = pd.read_csv(s_file, header=0, encoding="utf-8", encoding_errors="replace")

    assert v_df.shape[1] == len(V_COLUMNS), (
        f"{v_file.name} has {v_df.shape[1]} columns, expected {len(V_COLUMNS)}. "
        "Re-check the real header against src/schema.py before proceeding."
    )
    assert s_df.shape[1] == len(S_COLUMNS), (
        f"{s_file.name} has {s_df.shape[1]} columns, expected {len(S_COLUMNS)}. "
        "Re-check the real header against src/schema.py before proceeding."
    )

    v_df.columns = V_COLUMNS
    s_df.columns = S_COLUMNS
    return v_df, s_df
