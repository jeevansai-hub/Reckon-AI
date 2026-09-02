"""
Run this FIRST after `git lfs pull`, before trusting anything else in src/.

Prints the real header row of one V- and one S- file side-by-side against
the documented schema in src/schema.py, so you can eyeball whether the PDF's
documented column order actually matches what's in the file (see the
gyroscope-column typo flagged in Project-Context/IO-VNBD-Repository-Breakdown.md
section 6 -- this is exactly the kind of mismatch this script exists to catch).

Usage:
    python scripts/verify_schema.py
"""

from pathlib import Path

from io_vnbd.data.schema import S_COLUMNS, V_COLUMNS

DATA_ROOT = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "IO-VNBD"
    / "Synchronised V abd S datasets"
    / "Categorised IOVNB Dataset"
    / "S (Driver A)"
    / "S1"
)


def main():
    v_file = DATA_ROOT / "V-S1.csv"
    s_file = DATA_ROOT / "S-S1.csv"

    for label, file, documented in [("V-S1.csv", v_file, V_COLUMNS), ("S-S1.csv", s_file, S_COLUMNS)]:
        if not file.exists():
            print(f"[MISSING] {file} -- did you run `git lfs pull`? See README.md Step 1.")
            continue

        with open(file, "r", encoding="utf-8", errors="replace") as f:
            real_header = f.readline().strip().split(",")

        print(f"\n=== {label} ===")
        print(f"Real columns:       {len(real_header)}")
        print(f"Documented columns: {len(documented)}")
        if len(real_header) != len(documented):
            print("  !! COUNT MISMATCH -- update src/schema.py before trusting src/loader.py")
        for i, (real, doc) in enumerate(zip(real_header, documented)):
            flag = "" if real.strip().lower().replace(" ", "") != "" else "  <-- blank in real file"
            print(f"  [{i:2d}] real='{real:<30}'  documented='{doc}'{flag}")


if __name__ == "__main__":
    main()
