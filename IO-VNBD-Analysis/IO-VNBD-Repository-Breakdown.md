# IO-VNBD Repository — Complete Deep-Dive Breakdown & Implementation Guide

Source repo: https://github.com/onyekpeu/IO-VNBD
Source paper: "IO-VNBD: Inertial and Odometry Benchmark Dataset for Ground Vehicle Positioning" — Uche Onyekpe, Vasile Palade, Stratis Kanarachos, Alicja Szkolnik (Coventry University), 2020.

This is an exhaustive, file-by-file and parameter-by-parameter reference for the repository — every top-level file, every category subfolder, every run inside it, every CSV column, with real example values pulled from the paper's appendix, what each thing physically means, what to watch out for, and a concrete implementation path.

---

## Table of Contents

1. Top-level repository files
2. Complete directory tree (every path in the repo)
3. `Categorised IOVNB Dataset/` — full per-run breakdown, driver by driver
4. `Uncategorised IOVNB Dataset/S-Dataset/` — flat file listing and usage
5. The `V-*.csv` schema — every column explained with examples and pitfalls
6. The `S-*.csv` schema — every column explained with examples and pitfalls
7. Driving styles, scenario taxonomy, and tyre-pressure codes — full tables
8. Cross-cutting parameters to consider before modeling
9. Known constraints / gotchas hit during analysis
10. Step-by-step implementation path (with code)

---

## 1. Top-level repository files

```
IO-VNBD/
├── .gitattributes
├── README.md
├── README_1.pdf
├── Synchronised V abd S datasets.zip
└── Synchronised V abd S datasets/
```

### 1.1 `.gitattributes`
**What it literally contains:** LFS filter rules, e.g. patterns like `*.csv filter=lfs diff=lfs merge=lfs -text`, `*.zip filter=lfs ...`, `*.JPG filter=lfs ...`.
**Why it exists:** GitHub repos have a soft 100MB per-file / multi-GB repo-size comfort zone. This dataset has ~90 driving runs, each with a CSV that can run into the tens of thousands of rows (one run alone — `V-Vw4` — has **126,573 rows**). Without LFS, cloning would download every historical version of every CSV on every `git clone`, which is unworkable.
**What to consider:**
- If you `git clone` without LFS installed, every `.csv`/`.zip`/`.JPG` you open will contain **three lines of pointer text** like:
  ```
  version https://git-lfs.github.com/spec/v1
  oid sha256:8f4b2c1e...
  size 9614832
  ```
  instead of real data. This is exactly what happened when this session tried to `WebFetch` a raw CSV URL — it returned a pointer, not content.
- Fix: install `git-lfs`, then either `git lfs clone` or `git clone` followed by `git lfs pull`.
- If you're on a metered or slow connection: `git lfs pull --include="Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/*"` lets you pull only one category at a time instead of the whole ~GB+ dataset.

### 1.2 `README.md`
**What it contains:** A single-paragraph abstract (see earlier analysis) — motivation, sensors used, total scale (40 hrs/1,300 km vehicle data, 58 hrs/4,400 km smartphone data).
**What it does NOT contain:** column definitions, folder explanations, scenario codes, or licensing terms. It is a landing-page teaser only.
**When to use it:** Only as a 30-second pitch when describing the dataset to teammates or in a hackathon slide — never as an implementation reference.

### 1.3 `README_1.pdf` (1.02 MB, 15 pages)
This is the **real documentation** and the single most important file in the repo. Structure:

| Page(s) | Section | Contents |
|---|---|---|
| 1 | Title/Abstract | Authors, affiliation, abstract |
| 1–2 | Introduction | Motivation, sensor list, Figures 1–2 (equipment photos, phone axis diagram) |
| 2 | Equipment | Racelogic VBOX Video HD2 (CAN-bus logger + GPS antenna, 10Hz), 3 Android phones (Huawei P20 Pro, Motorola Moto G7 Power, BlackBerry Priv) running AndroSensor |
| 2 | Experiment Setup | Vehicle used (Ford Fiesta Titanium, front-wheel drive) + 4 phone-carrying vehicles (Ford Fiesta, Volvo XC70, Renault Megane, Toyota Corolla Verso), Figure 3 (sensor placement diagram with vehicle dimensions) |
| 3 | Data Description | Explains `V-`/`S-` prefixes, sync process, GPS-outage tracking, gravity-channel purpose |
| 3 | Table 1 | Driving style per driver (A–H) |
| 4 | Table 2 | 32 driving/environmental scenarios captured |
| 4 | Table 3 | Full 29-column `V-*.csv` schema with units |
| 5 | Table 4 | Full 24-column `S-*.csv` schema with units |
| 5 | Table 5 | Tyre-pressure notation A–E, PSI per wheel |
| 5 | Conclusion | Total scale restated: ~5,700 km / 98 hrs across the *entire* collection (synchronized + non-synchronized) |
| 6 | References | 16 citations, mostly INS/GPS neural-network fusion papers — good reading list for the model architecture |
| 7–15 | Appendix Tables A1-1 through A7 | **Per-run metadata for every single dataset**: driver, dataset name, features/scenario tags, cities/towns, weather, collection date, velocity/acceleration range, total time+distance, total data points, matching smartphone dataset name |

**What to consider:** The appendix (pages 7–15) is effectively a **structured database trapped inside a PDF table**. Section 3 of this document transcribes all of it into a queryable form so you don't have to re-OCR the PDF yourself.

### 1.4 `Synchronised V abd S datasets.zip`
**What it is:** A zip of the exact same tree as the unzipped `Synchronised V abd S datasets/` folder below it. Redundant on purpose — convenience for a single-download workflow vs. Git-tracked folder browsing.
**What to consider:** Since it's tracked via Git LFS too, downloading the zip via `git lfs pull` and downloading the folder tree file-by-file cost the same total bytes — the zip just avoids per-file HTTP overhead (1 LFS object instead of ~350). Prefer the zip route for bulk downloads; prefer the unzipped folder for `git lfs pull --include=<glob>` partial/selective downloads.

---

## 2. Complete directory tree

Below is the **literal, complete file listing** of the repository (confirmed via the GitHub API tree endpoint), reproduced here so this document is a standalone reference without needing to re-crawl GitHub.

```
Synchronised V abd S datasets/
├── Categorised IOVNB Dataset/
│   ├── M (Driver B)/
│   │   └── S-M.csv, V-M.JPG, V-M.csv
│   ├── S (Driver A)/
│   │   ├── S1/  → S-S1.csv, V-S1.JPG, V-S1.csv
│   │   ├── S2/  → S-S2.csv, V-S2.JPG, V-S2.csv
│   │   ├── S3a/ → S-S3a.csv, V-S3a.JPG, V-S3a.csv
│   │   ├── S3b/ → S-S3b.csv, V-S3b.JPG, V-S3b.csv
│   │   ├── S3c/ → S-S3c.csv, V-S3c.JPG, V-S3c.csv
│   │   └── S4/  → S-S4.csv, V-S4.JPG, V-S4.csv
│   ├── Vf (Driver E)/
│   │   ├── V-Vfa01/ → S-Vfa01.csv, V-Vfa01.JPG, V-Vfa01.csv
│   │   └── V-Vfa02/ → S-Vfa02.csv, V-Vfa02.JPG, V-Vfa02.csv
│   ├── Vta (Driver E)/
│   │   └── Vta01a, Vta01b, Vta02 … Vta17, Vta19 … Vta30   (28 subfolders — Vta18 skipped in source data)
│   │       each → S-Vta<n>.csv, V-Vta<n>.JPG, V-vta<n>.csv   (note: lowercase "vta" in some V- filenames — inconsistent capitalization in the source repo itself)
│   ├── Vtb (Driver E)/
│   │   └── Vtb01 … Vtb12  (12 subfolders)
│   │       each → S-Vtb<n>.csv, V-Vtb<n>.JPG, V-vtb<n>.csv
│   ├── Vw (Driver E)/
│   │   └── Vw01 … Vw13, Vw14a, Vw14b, Vw14c, Vw15, Vw16a, Vw16b, Vw17  (20 subfolders)
│   │       each → S-Vw<n>.csv, V-Vw<n>.JPG, V-Vw<n>.csv
│   └── Y (Driver D)/
│       └── Y1/ → S-Y1.csv, V-Y1.JPG, V-Y1.csv
└── Uncategorised IOVNB Dataset/
    └── S-Dataset/
        └── 74 flat S-*.csv files (one per run listed above, no subfolders, no V- files, no images)
```

**Total run count in the Categorised folder: 74 synchronized runs** (4+1+1+2+28+12+20 as counted above — the exact per-category counts are also in the table in §3).

**Naming inconsistency to code around:** Notice `V-vta<n>.csv` and `V-vtb<n>.csv` use lowercase `vta`/`vtb` in several filenames while the parent folder and `S-` file use `Vta`/`Vtb` capitalized. A case-sensitive file-matching script (e.g. plain `glob.glob("V-Vta*.csv")` on Linux) will **silently miss files** — always do a case-insensitive match or build the file list from `os.listdir()` and filter with `.lower()`.

---

## 3. `Categorised IOVNB Dataset/` — full per-run breakdown

This section reproduces every row of the PDF's Appendix Tables A1-1 through A7, organized by the folder you'll actually find them in. Each entry shows: **what it physically represents, the exact metadata the paper reports, and what to consider when using it.**

### 3.1 `S (Driver A)/` — 6 runs, Coventry area, Defensive style

| Run | Roads / Scenario tags | Cities | Weather | Date | Speed / Accel range | Duration / Distance | Rows |
|---|---|---|---|---|---|---|---|
| **S1** | B-Road (B4101), Roundabout ×9, Reverse ×5, Hilly Road, A4053 Ring Road, Hard Brake, Tyre Pressure E | Coventry | 15/4°C, Sunny, Humidity 73% | 08/09/2019 | 0.0–93.8 km/h, −0.59…0.34 g | 86.3 min / 38.16 km | 51,790 |
| **S2** | B-Road (B4112, B4065), Roundabout ×18, Reverse ×8, Motorway, Dirt Road, U-Turn ×5, Country Road, Successive L/R Turns, Hard Brake, A-Road (A4600), Tyre Pressure E | Coventry, Nuneaton | 17/15°C, Passing clouds | 08/09/2019 | 0.0–105.2 km/h, −0.56…0.43 g | 156.5 min / 75.64 km | 93,900 |
| **S3a** | Roundabout ×15, U-turn/Reverse ×4, Motorway (M6), A-Road (A4600, A426), Hard Brake, Zig-Zag, Country Roads, Night-time, Sharp Turn L/R, Tyre Pressure E | Coventry, Rugby | 17/12°C, Passing clouds | 04/09/2019 | 0.0–98.0 km/h, −0.57…0.4 g | 41.1 min / 26.0 km | 24,660 |
| **S3b** | Successive L/R Turns ×21, Reverse/U-Turns ×1, Tyre Pressure E | Rugby | (same day as S3a) | 04/09/2019 | 0.0–44.8 km/h, −0.37…0.3 g | 11.4 min / 3.8 km | 6,840 |
| **S3c** | Roundabout ×4, A-Road (A428), Country Roads, Tyre Pressure E | Rugby, Coventry | (same day) | 04/09/2019 | 0.0–117.1 km/h, −0.36…0.35 g | 62.0 min / 44.28 km | 37,220 |
| **S4** | Roundabout ×14, U-turn, A-Road, Successive L/R Turns, Zig-Zag, Night-time, A-Road (A429, A45, A46), Ring Road (A4053), Tyre Pressure E | Coventry | 13/12°C, Passing clouds | 06/09/2019 | 0.0–109.6 km/h, −0.48…0.41 g | 163.0 min / 93.9 km | 97,824 |

**What to consider:** S3a/b/c/S3 look like one continuous drive split into 3 files (same date, contiguous locations Coventry→Rugby). If your pipeline treats runs as independent trajectories, concatenating S3a→S3b→S3c may reconstruct a longer, more realistic single trip — worth testing whether GPS end-of-S3a lines up with GPS start-of-S3b.

### 3.2 `M (Driver B)/` — 1 run, Coventry, Defensive style

| Run | Scenario tags | City | Weather | Date | Speed / Accel | Duration / Distance | Rows |
|---|---|---|---|---|---|---|---|
| **M** | Roundabout ×30, Successive L/R Turns, Hard Brake ×21, Zig-Zag ×5, Country Roads, Sharp Turn L/R, Daytime, U-Turn ×1, U-Turn Reverse ×7, Tyre Pressure E | Coventry | 15/12°C, Partly sunny | 07/09/2019 | 0.0–100.7 km/h, **−1.01…0.44 g** | 176.7 min / 105.44 km | 105,995 |

**What to consider:** This run has the **single most extreme longitudinal deceleration in the whole dataset (−1.01 g)** — i.e. harder than a typical panic stop. If you're building an anomaly/hard-brake detector, this is your strongest positive-class example. If you're building a smooth-driving trajectory regressor, this run is a stress-test/outlier case, not a "typical" training example — consider whether to downweight or specifically hold it out for edge-case evaluation.

### 3.3 `Y (Driver D)/` — 1 run, Coventry, Defensive style

| Run | Scenario tags | City | Weather | Date | Speed / Accel | Duration / Distance | Rows |
|---|---|---|---|---|---|---|---|
| **Y1** | Roundabout ×20, Successive L/R Turns, Hard Brake, Zigzag, Sharp Turn L/R, Reverse/U-Turn ×8, Tyre Pressure E | Coventry | 22/16°C, Passing clouds | 30/08/2019 | 0.0–87.5 km/h, −0.85…0.36 g | 117.2 min / 60.86 km | 70,341 |

**Note:** The PDF appendix also lists `V-Y2` (Coventry/Kenilworth, 08/03/2019) with **no corresponding S- file** ("N/A" in the Corresponding Smartphone Dataset column) — that's why only Y1 exists in the synchronized folder, not Y2.

### 3.4 `Vf (Driver E)/` — 2 runs, Aggressive style

| Run | Scenario tags | Cities | Weather | Date | Speed / Accel | Duration / Distance | Rows |
|---|---|---|---|---|---|---|---|
| **Vfa01** | A-Road (A444), Roundabout ×1, B-Road (B4116), Daytime, Hard Brake, Tyre Pressure A | Nuneaton, Twycross, Measham | 5–7°C, mix of clear/scattered clouds/light rain across the drive | 08/11/2019 | 0.0–98.4 km/h, −0.56…0.42 g | 19.2 min / 18.8 km | 11,535 |
| **Vfa02** | B-Road (B4116), Roundabout ×5, A-Road (A42, A641), Motorway (M1, M62), High-Rise Buildings, Hard Brake, Tyre Pressure C | Bradford, Measham | (same weather window as Vfa01) | 08/11/2019 | 0.0–117.9 km/h, −0.67…0.48 g | 112.9 min / 163.38 km | 67,755 |

**What to consider:** Vfa02 is a genuine long-distance motorway trip (163 km) — the best run in the whole dataset for testing long-horizon drift accumulation, since dead-reckoning error compounds with distance/time. Use this as your primary "does the model's error blow up over a long trip" stress test.

**Not synchronized (documented in PDF but absent from repo):** `V-Vfb01a/b/c/d` (Bradford city driving, night, wet road, all "N/A" for smartphone match) and `V-Vfb02a–g` (Nuthall/East Ardsley, motorway M1, night, all "N/A"). These exist only as vehicle-only CAN-bus data — usable if your project ever needs pure odometry data without a smartphone-noise counterpart, but you'd have to fetch them separately (they are NOT in "Synchronised V and S datasets" — check if the full repo has an un-synchronized folder elsewhere, or contact the maintainer).

### 3.5 `Vta (Driver E)/` — 28 runs, Peak District/Derbyshire area, Aggressive style, **all Tyre Pressure A**

This is the largest category by run-count. Weather was consistent across the whole collection day: **4–10°C / 3–6°C, passing/broken/scattered clouds, humidity 75–93%, wind ~5 mph SE** (collected 14/11/2019 and 06/11/2019).

| Run | Scenario tags | Location | Speed / Accel | Duration / Distance | Rows |
|---|---|---|---|---|---|
| Vta1a | Wet Road, Gravel Road, Country Road, Sloppy Roads, Roundabout ×3, Hard Brake on wet road | Nuneaton, Walton-on-Trent | 0.0–103.4 km/h, −0.54…0.35 g | 43.0 min / 40.74 km | 25,821 |
| Vta1b | Hard Brakes on Mud, Wet Road, Country Road | Coton-in-the-Elms, Walton-on-Trent | 0.1–77.7 km/h, −0.49…0.28 g | 1.6 min / 1.26 km | 956 |
| Vta2 | Roundabout ×2, A-Road (A511/A5121/A444), Country Road, Hard Brake | Walton-on-Trent, Burton-on-Trent | 0.0–81.6 km/h, −0.59…0.38 g | 18.3 min / 11.07 km | 10,995 |
| Vta3 | Roundabout ×1, Manoeuvres | Burton-on-Trent | 0.0–45.8 km/h, −0.31…0.27 g | 1.5 min / 0.38 km | 875 |
| Vta4 | A-Road (A511) | Burton-on-Trent | 5.9–51.7 km/h, −0.37…0.28 g | 3.0 min / 2.02 km | 1,809 |
| Vta5 | Roundabout ×1, A-Road (A511) | Burton-on-Trent | 29.2–51.1 km/h, −0.26…0.09 g | 0.6 min / 0.42 km | 357 |
| Vta6 | A-Road (A511) | Burton-on-Trent | 43.8–103.9 km/h, −0.24…0.13 g | 2.3 min / 2.62 km | 1,393 |
| Vta7 | Roundabout ×2, A-Road (A511), Hard Brake | Burton-on-Trent | 22.4–113.1 km/h, −0.54…0.18 g | 1.4 min / 1.54 km | 857 |
| Vta8 | Town Roads (Build-up), A-Road (A511) | Hatton Derby | 0.0–77.6 km/h, −0.45…0.3 g | 6.2 min / 3.43 km | 3,697 |
| Vta9 | Hard Brake, A-Road (A50) | Derby | 48.9–87.7 km/h, −0.6…0.14 g | 0.4 min / 0.43 km | 226 |
| Vta10 | Roundabout ×1, A-Road (A50) | Sudbury Ashbourne | 38.8–118.0 km/h, −0.28…0.13 g | 2.6 min / 3.95 km | 1,570 |
| Vta11 | Roundabout ×2, A-Road (A50) | Oaks Green Ashbourne | 26.8–97.7 km/h, −0.45…0.15 g | 1.0 min / 0.92 km | 589 |
| Vta12 | Change in Speed, A-Road (A515) | Ashbourne | 44.7–85.3 km/h, −0.44…0.13 g | 1.1 min / 1.27 km | 690 |
| Vta13 | A-Road (A515), Country Road, Hard Brake | Ashbourne | 72.7–103.6 km/h, −0.38…0.12 g | 0.8 min / 1.14 km | 473 |
| Vta14 | Hard Brake, Change in Speed, A-Road (A515) | Ashbourne | 52.8–91.0 km/h, −0.32…0.13 g | 4.8 min / 5.45 km | 2,893 |
| Vta15 | A-Road (A515) | Ashbourne | 60.1–78.8 km/h, −0.12…0.06 g | 1.4 min / 1.72 km | 869 |
| Vta16 | Roundabout ×3, Hilly Road, Country Road, A-Road (A515) | Thorpe, Ashbourne, Clifton | 0.0–93.9 km/h, −0.49…0.42 g | 18.9 min / 13.72 km | 11,361 |
| Vta17 | Hilly Road, Hard-Brake, Stationary (No Motion) | Ilam, Blore | 0.0–56.2 km/h, −0.51…0.28 g | 7.7 min / 4.19 km | 4,594 |
| Vta19 | Hilly Road | Ilam | 0.0–55.2 km/h, −0.35…0.22 g | 0.5 min / 0.26 km | 310 |
| Vta20 | Hilly Road, Approximate Straight-line Travel | Ilam | 0.0–44.8 km/h, −0.19…0.3 g | 5.4 min / 0.39 km | 3,223 |
| Vta21 | Hilly Road | Ilam | 0.0–74.8 km/h, −0.44…0.24 g | 3.5 min / 2.76 km | 2,088 |
| Vta22 | Hilly Road, Hard Brake | Ilam | 14.8–55.8 km/h, −0.53…0.16 g | 2.6 min / 1.67 km | 1,572 |
| Vta23 | Hilly Road, Hard Brake | Thorpe | 0.0–51.9 km/h, −0.57…0.42 g | 1.9 min / 1.1 km | 1,119 |
| Vta24 | Hilly Road | Thorpe | 0.0–56.4 km/h, −0.46…0.36 g | 2.0 min / 0.71 km | 1,184 |
| Vta25 | U-turn | Thorpe | 0.0–48.6 km/h, −0.46…0.3 g | 1.1 min / 0.16 km | 646 |
| Vta26 | Gravel Road, Dirt Road, Hilly Road | Thorpe | 0.0–55.1 km/h, −0.27…0.44 g | 3.2 min / 1.02 km | 1,947 |
| Vta27 | Gravel Road, Several Hilly Roads, Potholes, Country Road, A-Road (A515) | Ashbourne | 0.0–65.0 km/h, −0.43…0.29 g | 4.8 min / 3.16 km | 2,853 |
| Vta28 | Country Road, Hard Brake, Valley, A-Road (A515) | Milldale | 0.0–66.0 km/h, −0.58…0.31 g | 7.0 min / 3.94 km | 4,219 |
| Vta29 | Hard Brake, Country Road, Hilly Road, Windy Road, Dirt Road, Wet Road, Reverse ×2, Bumps, Rain, B-Road (B5053), U-Turn ×3, Valley | Wetton, Milldale | 0.0–102.0 km/h, −0.8…0.38 g | 39.6 min / 26.12 km | 23,737 |
| Vta30 | Rain, Wet Road, U-Turn ×2, A-Road (A53/A515), Inner Town Driving, B-Road (B5053) | Buxton | 0.0–100.0 km/h, −0.47…0.36 g | 28.6 min / 11.77 km | 17,179 |

**What to consider:**
- Most `Vta` runs are **extremely short** (under 5 minutes, some under 1 minute — e.g. Vta5 is 0.6 min / 357 rows, Vta9 is 0.4 min / 226 rows). These are not full trips — they are **short, targeted maneuver clips** (a single roundabout, a single hard brake). Treat them as a different data regime than the long `S`/`M`/`Vfa02` runs: good for training a model to recognize discrete events, bad for testing long-horizon trajectory drift (there isn't enough time for drift to accumulate).
- Vta17 explicitly contains a **Stationary (No Motion)** segment mixed into an otherwise moving run — unlike Vw1/Vw15 (fully stationary runs), here you'd need to find the stationary sub-window inside the CSV yourself (e.g. by thresholding wheel speed / GPS speed near zero) rather than treating the whole file as stationary.
- Vta18 is conspicuously missing from both folder names and the PDF appendix — not a bug in this document, it's actually absent from the source dataset numbering.

### 3.6 `Vtb (Driver E)/` — 12 runs, Peak District→Nuneaton corridor, Aggressive style, **all Tyre Pressure A**

Collected 06/11/2019, weather: 4–8°C/4°C, Rain/Passing clouds/Broken clouds/Chilly, humidity 94–98%.

| Run | Scenario tags | Location | Speed / Accel | Duration / Distance | Rows |
|---|---|---|---|---|---|
| Vtb1 | Valley, Rain, Wet Road, Country Road, U-Turn ×2, Hard Brake, Swift Manoeuvre, A-Road (A6/A6020/A623/A515), B-Road (B6405), Roundabout ×3, Daytime | Bakewell, Tideswell, Ashford-on-Water, Buxton | 0.0–101.2 km/h, −0.63…0.36 g | 54.1 min / 41.94 km | 32,459 |
| Vtb2 | Country Road, Wet Road, Dirt Road | Youlgreave | 0.0–61.1 km/h, −0.36…0.39 g | 9.5 min / 4.35 km | 5,712 |
| Vtb3 | Reverse, Wet Road, Dirt Road, Gravel Road, Night-time | Youlgreave | 0.0–37.5 km/h, −0.23…0.33 g | 13.8 min / 0.71 km | 8,289 |
| Vtb4 | Dirt Road, Country Road, Gravel, Wet Road | Youlgreave | 0.0–32.7 km/h, −0.31…0.27 g | 1.0 min / 0.27 km | 625 |
| **Vtb5** | Dirt Road, Country Road, Gravel Road, Hard Brake, Wet Road, B-Road (B6405/B6012/B5056), Inner Town Driving, A-Road, **Motorway (M42, M1)**, **Rush hour (Traffic)**, Roundabout ×6, A-Road (A5/A42/A38/A615/A6) | Atherstone, Nuthall, Hilcote, Matlock, Rowsley, Youlgreave | 0.0–112.9 km/h, −0.55…0.42 g | **107.7 min / 111.66 km** | 64,610 |
| Vtb6 | A-Road (A5) | Atherstone | 52.7–73.0 km/h, −0.11…0.11 g | 0.8 min / 0.89 km | 508 |
| Vtb7 | Approximate Straight-line Motion, Night-time, A-Road (A5) | Atherstone | 29.1–69.2 km/h, −0.37…0.13 g | 0.8 min / 0.72 km | 461 |
| Vtb8 | Approximate Straight-line Motion, Night-time, Wet Road, A-Road (A5) | Atherstone | 60.9–76.5 km/h, −0.35…0.08 g | 1.2 min / 1.35 km | 699 |
| Vtb9 | Approximate Straight-line Motion, Night-time, Wet Road, Hard Brake, A-Road (A5) | Nuneaton | 66.8–92.0 km/h, −0.14…0.1 g | 0.8 min / 0.98 km | 457 |
| Vtb10 | Roundabout, Wet Road, Night-time, A-Road (A5) | Nuneaton | 26.1–58.5 km/h, −0.24…0.12 g | 0.3 min / 0.23 km | 195 |
| Vtb11 | Approximate Straight-line Motion, Night-time, Wet Road, A-Road (A5) | Nuneaton | 65.1–75.3 km/h, −0.05…0.12 g | 0.7 min / 0.84 km | 433 |
| Vtb12 | Roundabout ×1, Wet Road, Night-time | Nuneaton | 22.2–71.6 km/h, −0.38…0.17 g | 0.8 min / 0.61 km | 490 |

**Note:** `V-Vtb13` (Parking, Wet Road, Nuneaton, 2.1 min/0.99 km) is documented in the PDF but has **no corresponding S- file** — not present in this repo folder.

**What to consider:** Vtb5 is the single richest run in the entire dataset — it's the only one tagging both **Motorway** and **Rush hour (Traffic)** simultaneously, meaning it contains stop-and-go low-speed traffic sections *and* high-speed motorway sections in one continuous trip. This is the ideal single run to visualize first when sanity-checking your pipeline, since it exercises almost the full velocity range (0–112.9 km/h) end to end.

### 3.7 `Vw (Driver E)/` — 20 runs, Nuneaton→Milton Keynes→Worcester corridor + M5/M42 night runs, Aggressive style

Collected across two sessions: 08/01/2020 (Vw1–13) and later dates within the same cold winter window for Vw14–17. Tyre pressure varies **within this category** (C, D, F — unlike Vta/Vtb which are fixed at A). Weather ranges 7–10°C with smoke/fog/drizzle/passing clouds noted.

| Run | Scenario tags | Location | Speed / Accel | Duration / Distance | Rows |
|---|---|---|---|---|---|
| **Vw1** | **Stationary (No Motion, sensor bias estimation)**, Daytime, Tyre Pressure C | Nuneaton | 0.00–0.00 km/h, 0.00 g | 34.1 min / 0.00 km | 20,475 |
| Vw2 | A-Road (A5, A421), Motorway (M5), Daytime, Roundabout ×22, U-Turn ×2, Inner city driving, Tyre Pressure C | Nuneaton, Hinckley, Milton Keynes | 0.0–115.4 km/h, −0.62…0.45 g | 87.9 min / 98.63 km | 52,712 |
| Vw3 | Roundabout ×6, Daytime, B-Road, Inner city driving, Tyre Pressure C | Milton Keynes | 0.0–77.4 km/h, −0.47…0.41 g | 6.6 min / 5.05 km | 3,942 |
| **Vw4** | Roundabout ×77(!), Swift Manoeuvres, Hard Brake, Inner City Driving, Reverse, A-Road, Motorway (M5/M40/M42), Country Road, Successive L/R Turns, Daytime, U-Turn ×3, Tyre Pressure D | Milton Keynes, Buckingham, Droitwich Spa, Kidderminster, Worcester | 0.0–**131.9 km/h** (fastest run in dataset), −0.66…0.45 g | **211.0 min / 214.62 km** (longest & farthest run in dataset) | **126,573** (most rows of any single run) |
| Vw5 | Successive L/R Turns, Daytime, Sharp Turn L/R, Tyre Pressure D | Worcester | 0.0–38.7 km/h, −0.4…0.21 g | 1.8 min / 0.7 km | 1,050 |
| Vw6 | Bumps, Swift Manoeuvres, Daytime, Sharp Turn L/R, Tyre Pressure F | Worcester | 3.3–40.7 km/h, −0.34…0.26 g | 2.1 min / 1.08 km | 1,288 |
| Vw7 | Successive L/R Turns, Daytime, Sharp Turn L/R, Tyre Pressure D | Worcester | 0.4–42.2 km/h, −0.37…0.37 g | 2.8 min / 1.23 km | 1,689 |
| Vw8 | Successive L/R Turns, Daytime, Sharp Turn L/R, Tyre Pressure D | Worcester | 0.0–46.4 km/h, −0.37…0.27 g | 2.7 min / 1.12 km | 1,599 |
| Vw9 | Zig-Zag Motion, Daytime, Hard Brake, Tyre Pressure D | Worcester | 3.8–42.0 km/h, −0.67…0.21 g | 1.0 min / 0.45 km | 601 |
| Vw10 | Hilly Road, Daytime, Tyre Pressure F | Worcester | 11.8–58.9 km/h, −0.42…0.11 g | 1.1 min / 0.74 km | 670 |
| Vw11 | Motorway (M5), Daytime, Roundabout ×5, Tyre Pressure D | — | 0.0–98.4 km/h, −0.37…0.33 g | 8.2 min / 5.85 km | 4,924 |
| Vw12 | Approximate Straight-line Motion, Daytime, Motorway (M5), Tyre Pressure D | — | 82.6–97.4 km/h, −0.06…0.07 g | 1.75 min / 2.64 km | 1,050 |
| Vw13 | Approximate Straight-line Motion, Daytime, Motorway (M5), Tyre Pressure D | — | 94.0–115.0 km/h, −0.07…0.06 g | 0.5 min / 0.82 km | 297 |
| Vw14a | Motorway (M5), Night-time, Tyre Pressure D | — | 61.9–109.4 km/h, −0.38…0.12 g | 5.2 min / 7.92 km | 3,140 |
| Vw14b | Motorway (M42), Night-time, Tyre Pressure D | — | 12.6–120.1 km/h, −0.28…0.28 g | 32.7 min / 41.21 km | 19,600 |
| Vw14c | Motorway (M42), Roundabout ×2, A-Road (A446), Night-time, Hard Brake, Tyre Pressure D | — | 0.0–100.5 km/h, −0.53…0.41 g | 26.4 min / 17.15 km | 15,857 |
| **Vw15** | **Stationary (No Motion, sensor bias estimation)**, Night-time, Tyre Pressure D | Dordon | 0.0–0.0 km/h, 0.00 g | 2.3 min / 0.00 km | 1,391 |
| Vw16a | A-Road (A5), Roundabout ×2, Tyre Pressure D | Atherstone | 0.0–83.5 km/h, −0.39…0.4 g | 10.0 min / 8.49 km | 6,000 |
| Vw16b | Hard Brake, Night-time, A-Road (A5), Approximate Straight-line travel, Tyre Pressure D | Nuneaton | 1.3–86.3 km/h, −0.75…0.29 g | 2.0 min / 1.99 km | 1,171 |
| Vw17 | Hard Brake, Night-time, A-Road (A5), Approximate Straight-line travel, Tyre Pressure D | Calcedote | 31.5–72.7 km/h, −0.8…0.19 g | 0.5 min / 0.54 km | 329 |

**What to consider — the two bias runs (Vw1, Vw15) in detail:**
- **Vw1**: 34.1 minutes, 20,475 rows, **all zeros for velocity/acceleration range**, Tyre Pressure C, daytime, Nuneaton. This is your **primary bias calibration source** — long duration means a statistically robust mean/std of the raw accelerometer and gyroscope noise floor while genuinely motionless.
- **Vw15**: only 2.3 minutes / 1,391 rows, Tyre Pressure D, night-time, Dordon. Shorter and under different lighting/temperature conditions — useful as a **second, independent bias sample** to check whether IMU bias drifts with temperature/time-of-day (a well-known MEMS IMU characteristic). If your two bias estimates differ meaningfully, that itself is a data point worth reporting (temperature-dependent bias drift), and you may want a per-run local bias correction rather than one global constant.
- **Do not** average Vw1 and Vw15 together blindly — they used **different tyre pressure settings (C vs D)** and were recorded on different dates; check whether that's expected to matter for a "vehicle stationary" reading (it shouldn't affect accelerometer/gyro bias directly, but confirms these are genuinely two separate calibration events, not duplicate data).

**Not synchronized (documented, absent here):** the entire `Vfb01a–d` / `Vfb02a–g` Driver E sub-series mentioned earlier under §3.4 — repeated note here since they were collected in the same Driver-E period as Vw/Vtb/Vta but with no smartphone pairing.

### 3.8 Summary table — run counts and totals per category

| Category | Folder | Runs (in repo) | Total rows (approx, summed) | Total distance (approx) | Total duration (approx) |
|---|---|---|---|---|---|
| S | `S (Driver A)` | 6 | ~312,234 | ~282 km | ~520 min |
| M | `M (Driver B)` | 1 | 105,995 | 105.44 km | 176.7 min |
| Y | `Y (Driver D)` | 1 | 70,341 | 60.86 km | 117.2 min |
| Vf | `Vf (Driver E)` | 2 | 79,290 | 182.18 km | 132.1 min |
| Vta | `Vta (Driver E)` | 28 | ~104,000+ | ~130 km | ~140 min |
| Vtb | `Vtb (Driver E)` | 12 | ~114,938 | ~166.4 km | ~189.7 min |
| Vw | `Vw (Driver E)` | 20 | ~257,689 | ~409.5 km | ~429.5 min |
| **Total** | — | **~70 runs** | **~1,044,000+ rows** | **~1,336 km** | **~1,705 min (~28.4 hrs)** |

*(Row/distance/duration sums are derived by adding the appendix table values above; treat as approximate — always recompute exact totals from the actual CSVs after `git lfs pull` rather than relying on this summary for anything precision-critical.)*

---

## 4. `Uncategorised IOVNB Dataset/S-Dataset/` — flat listing and usage

This folder contains **only** the `S-*.csv` files — same content as every `S-` file inside the categorised folders above, just copied into one flat directory with no subfolders, no `V-` counterparts, and no `.JPG` images.

**Full example of what you'd see with `ls`:**
```
S-M.csv        S-Vta14.csv   S-Vta9.csv    S-Vtb9.csv   S-Vw16a.csv
S-S1.csv       S-Vta15.csv   S-Vtb1.csv    S-Y1.csv     S-Vw16b.csv
S-S2.csv       S-Vta16.csv   S-Vtb10.csv   S-Vfa01.csv  S-Vw17.csv
S-S3a.csv      S-Vta17.csv   S-Vtb11.csv   S-Vfa02.csv  ...
S-S3b.csv      S-Vta19.csv   S-Vtb12.csv   S-Vw1.csv
S-S3c.csv      S-Vta1a.csv   S-Vtb2.csv    S-Vw2.csv
S-S4.csv       S-Vta1b.csv   S-Vtb3.csv    S-Vw3.csv
S-Vta10.csv    S-Vta2.csv    S-Vtb4.csv    S-Vw4.csv
S-Vta11.csv    S-Vta20.csv   S-Vtb5.csv    S-Vw5.csv
S-Vta12.csv    ... (etc — 74 files total)
```

**Why this folder exists:** Some users only care about the smartphone-only positioning problem (e.g. "can a phone in your pocket/dashboard estimate displacement without any vehicle CAN-bus access at all" — the realistic scenario for a consumer navigation app, as opposed to an OEM system with CAN-bus access). Rather than making that user recurse through 6 category folders, the maintainer flattened just the `S-` files here.

**What to consider before using this folder:**
1. **You lose the ground truth.** Without the matching `V-` file, you have no independent GPS/CAN-bus trajectory to train against — you'd have to rely on the `S-` file's own (noisier, 1Hz) GPS as ground truth instead, which is a materially different and harder problem (self-supervised / weakly-supervised positioning rather than supervised).
2. **You lose all metadata.** The filename `S-Vta12.csv` tells you nothing about weather, scenario, or duration — you must cross-reference back to §3 of this document (or the PDF appendix) using the run-name suffix (`Vta12` → Table row above: "Change in Speed, A-Road (A515), Ashbourne, 44.7–85.3 km/h, 1.1 min, 690 rows").
3. **Practical recommendation:** unless you specifically need a single `glob("S-*.csv")` call across everything with no folder traversal, prefer reading from the Categorised folder and just ignoring the `V-` files and images you don't need — you keep the metadata context for free.

---

## 5. `V-*.csv` schema — every column explained in depth

Source: Recorded live from the Ford Fiesta Titanium's CAN bus by the Racelogic VBOX Video HD2 data logger, sampling and updating at **10 Hz** (i.e., a new row every 0.1 seconds).

| # | Column | Unit | What it physically means | Example plausible value | What to consider |
|---|---|---|---|---|---|
| 1 | No. of GPS satellites available | count (N/A unit) | How many GNSS satellites the VBOX's GPS receiver had a lock on at that instant | `8` | Low counts (≤4) correlate with degraded GPS accuracy — a natural feature for **flagging GPS-unreliable windows** to either exclude from ground truth or to specifically construct "GPS-denied" training scenarios |
| 2 | Time since start of day | seconds | Time-of-day timestamp in seconds since midnight | `52341.2` | Use this (not row index) for any real-world time alignment; wraps at 86400 — handle midnight rollover if a run spans it |
| 3 | Latitude | degrees | GPS latitude, decimal degrees | `52.4068` (Coventry) | This + Longitude is your **primary ground-truth position** |
| 4 | Longitude | degrees | GPS longitude, decimal degrees | `-1.5197` | Convert to a local metric frame (e.g. UTM or an ENU tangent-plane projection centered on the run's start point) before computing displacement errors — raw lat/long degrees are not linear distance |
| 5 | Velocity | km/h | GPS-derived vehicle speed | `45.3` | This is the VBOX's own speed estimate (from GPS Doppler, typically very accurate — this is a "gold standard" speed, distinct from column 16 which comes from the ECU) |
| 6 | Heading | degrees | GPS-derived direction of travel, 0–360° | `187.5` | Discontinuous at the 0/360 wrap — always convert to sin/cos pair before feeding to a neural network, never use raw degrees as a regression target directly |
| 7 | Height | km | GPS altitude | `0.087` (87m) | Units are **km**, not m — a common bug source if you assume meters; cross-check against typical UK elevations (tens to low hundreds of meters, i.e. 0.0X–0.3X km) |
| 8 | Vertical velocity | km/h | Rate of altitude change | `0.4` | Usually near-zero on flat/urban roads; meaningfully nonzero on the Vta/Vtb "Hilly Road"/"Valley" runs — a useful auxiliary feature specifically for the Peak District (Vta/Vtb) runs |
| 9 | Sample period | seconds | The actual measured interval between this sample and the previous one | `0.0998` | Should be ≈0.1 throughout (10Hz), but check for gaps/jitter — a sample period significantly larger than 0.1 indicates a dropped sample or a logging hiccup that needs to be handled (e.g. re-index on cumulative time rather than assuming uniform row spacing) |
| 10 | Steering angle | degrees | Steering wheel angle | `-15.2` (turning left) | Sign convention (which direction is positive) is **not stated in the paper** — verify empirically against a known-turn segment (e.g. inside a tagged "Roundabout" run) before trusting sign in a heading-prediction model |
| 11–14 | Wheel Speed FL/FR/RL/RR | rad/s | Individual wheel rotational speed, all 4 wheels | `12.4, 12.6, 12.1, 12.3` | **This is your primary odometry input** — front-wheel drive means front wheels also steer, so FL vs FR divergence during a turn encodes yaw/turning radius (differential wheel speed ≈ Ackermann steering geometry); convert to linear speed via wheel radius (not given in the paper — must be measured/assumed for a Ford Fiesta, typically ~0.29–0.31 m rolling radius) |
| 15 | Yaw Rate | deg/s | Rate of rotation about the vertical axis | `8.7` | Directly integrable to heading change; compare against GPS-heading-derivative as a consistency check — large disagreement flags GPS heading noise or an actual turn faster than GPS update rate captured |
| 16 | Indicated Vehicle Speed | km/h | Speedometer-equivalent speed as read from the ECU (not GPS) | `44.0` | **Different source than column 5** — comparing these two gives you a real-world example of "odometry speed vs GPS speed" discrepancy, useful for building sensor-fusion confidence weighting |
| 17 | Indicated Longitudinal Acceleration | g | Forward/backward acceleration from the vehicle's own accelerometer | `-0.35` (braking) | Compare against derivative of column 5 (GPS velocity) as another cross-check; the M run's −1.01g extreme value (see §3.2) will show here |
| 18 | Indicated Lateral Acceleration | g | Sideways acceleration (cornering force) | `0.28` | Peaks during roundabouts/sharp turns — natural feature for automatically detecting "Roundabout"/"Sharp Turn" scenario windows without needing the manual PDF tags |
| 19 | Handbrake | 0 or 1 | Whether the handbrake is engaged | `0` | Useful as a hard filter — handbrake=1 rows should almost always coincide with velocity≈0; a mismatch (handbrake=1 while moving) indicates a sensor glitch |
| 20 | Gear Requested | 1–5 | Driver's requested gear | `3` | On a manual Fiesta, this may lag or differ momentarily from column 21 during a gear change — the gap between "requested" and "actual" is itself informative for clutch/gearshift-timing analysis, generally not needed for a pure positioning model |
| 21 | Gear | 1–5 | Actual engaged gear | `3` | Combined with engine speed (col 22) and wheel speed (col 11-14), this over-determines vehicle speed via gear ratio — mostly redundant for a positioning model, more relevant for a driving-behavior/fuel-efficiency model |
| 22 | Engine Speed | rev/min | Engine RPM | `2200` | Not directly useful for positioning, but a strong feature for a driving-style/aggressiveness classifier (Defensive vs Aggressive driver labeling) |
| 23 | Coolant Temperature | °C | Engine coolant temp | `88` | Irrelevant to positioning; potentially useful only to confirm the car had fully warmed up (affects nothing sensor-wise, but could correlate with tyre grip / cold-start behavior in edge analyses) |
| 24 | Clutch Position | 0/1 | Clutch engaged or not | `0` | Same category as Gear — driving-behavior signal, not positioning-relevant |
| 25 | Brake Pressure | PSI | Hydraulic brake line pressure | `450` | Strong hard-brake indicator, correlates directly with column 17 (longitudinal deceleration) — a second confirmatory signal for hard-brake event detection |
| 26 | Brake Position | 0/1 | Brake pedal pressed or not | `1` | Binary flag version of column 25 — use together (pressed=1 with pressure=0 briefly at pedal release is expected, not a glitch) |
| 27 | Battery Voltage | V | Vehicle electrical system voltage | `13.8` | Irrelevant to positioning; only useful for detecting logger power issues (voltage sag could correlate with data-quality problems in extreme cases) |
| 28 | Air Temperature | °C | Ambient/cabin air temperature | `15` | Cross-check against the PDF's weather-condition column per run (§3 tables) — should roughly match |
| 29 | Accelerator Pedal Position | % | Throttle position | `35` | Along with engine speed, useful for driving-style classification, not directly for positioning |

**Overall consideration for the whole `V-*.csv` file:** This file is simultaneously your **ground truth (columns 3–8: GPS position/velocity/heading)** *and* your **classical dead-reckoning baseline (columns 11–15: wheel speeds + yaw rate — this is exactly what a traditional, non-ML odometry system would use)**. A strong project should report both: (a) a neural INS model using only smartphone `S-` data, and (b) a classical wheel-odometry dead-reckoning baseline computed directly from these `V-` columns, as your point of comparison — the paper's own related work (IONet, LSTM/GPS-INS fusion) frames the contribution exactly this way.

---

## 6. `S-*.csv` schema — every column explained in depth

Source: Android phone (Huawei P20 Pro / Motorola Moto G7 Power / BlackBerry Priv) running the **AndroSensor** app, all channels sampled every 0.1s (10Hz) except GPS which the phone itself only refreshes at **1Hz**.

| # | Column | Unit | What it physically means | Example plausible value | What to consider |
|---|---|---|---|---|---|
| 1 | GPS Latitude | degrees | Phone's own GPS fix latitude | `52.4070` | Noisier and lower-rate than the `V-` file's VBOX GPS — expect meters-level disagreement between the two files' lat/long at the same timestamp |
| 2 | GPS Longitude | degrees | Phone's own GPS fix longitude | `-1.5195` | Same caveat as above |
| 3 | GPS Altitude | m | Phone GPS altitude estimate | `92.1` | **Units are meters here**, unlike the `V-` file's kilometers for the same physical quantity — another cross-file unit mismatch to code around explicitly |
| 4 | GPS Speed | km/h | Phone GPS-derived speed | `44.8` | Compare against `V-` column 5 (VBOX GPS speed) for the same instant — differences quantify realistic consumer-GPS noise, useful for a noise-injection/robustness ablation |
| 5 | GPS Accuracy | m | Phone-reported horizontal accuracy estimate (typically a 68% confidence radius) | `5.0` | **Directly usable as a per-sample confidence weight** — e.g. down-weight loss contribution from rows with accuracy > 15–20m, or use it to construct a "poor GPS" mask for testing model robustness under degraded conditions |
| 6 | GPS Orientation | ° | Phone GPS-derived bearing | `190.2` | Same wrap-around caveat as `V-` heading — convert to sin/cos before use |
| 7 | GPS Satellites In Range | count | Satellites visible to the phone | `6` | Typically lower/noisier than VBOX's dedicated antenna (column 1 of the `V-` file) — phones have inferior antennas, expect systematically fewer satellites here |
| 8 | Time Since Start | ms | Milliseconds since this specific logging session began | `18452` | Local-to-file clock, not wall-clock — do not compare directly across different run files without first anchoring to column 9 (Date) |
| 9 | Date | `YYYY-MO-DD HH-MI-SS_SSS` | Full wall-clock timestamp | `2019-09-08 14-32-07_123` | **This is your true cross-file synchronization anchor** — use it (not row index) to verify `S-` and `V-` files are actually aligned when you load a "synchronized" pair, and to splice/compare across runs if needed |
| 10–12 | Accelerometer X/Y/Z | m/s² | Raw phone accelerometer, **includes gravity component** | `X=0.8, Y=-0.3, Z=9.9` | This is the *uncorrected* signal — Z≈9.8 at rest confirms gravity is baked in; you must subtract the Gravity X/Y/Z channels (10–12 below) to get true linear (motion-only) acceleration before using it as an INS input |
| 13–15 | Gravity X/Y/Z | m/s² | Android's own low-pass-filtered estimate of the gravity vector in phone-frame coordinates | `X=0.1, Y=0.2, Z=9.79` | This is what makes `linear_accel = accelerometer - gravity` possible without needing your own complementary filter — a major convenience baked into this dataset that's easy to overlook if you only skim the column names |
| 16–18 | Gyroscope (Yaw/Pitch/Pitch) | rad/s | Angular velocity around each axis | `Yaw=0.05, Pitch=0.01, Roll(mislabeled "Pitch")=-0.02` | **The PDF's own Table 4 has a labeling typo** — the third gyroscope column is printed as "Gyroscope (Pitch)" a second time; it should almost certainly be **Roll**, matching the later Orientation columns which correctly list Yaw/Roll/Pitch. Verify against the actual CSV header string once you have real files — do not blindly trust the PDF label order for this one field |
| 19–21 | Magnetic Field X/Y/Z | μT | Raw magnetometer reading | `X=22.4, Y=-8.1, Z=-40.2` | Subject to vehicle magnetic interference (engine, metal body) — the paper itself flags vehicular vibration as a precision concern; treat magnetometer-derived heading as a weak/noisy auxiliary signal, not a primary heading source |
| 22–24 | Orientation (Yaw/Roll/Pitch) | ° | Android's fused device orientation estimate (from its own internal sensor fusion, typically accelerometer+gyro+magnetometer combined) | `Yaw=188.4, Roll=1.2, Pitch=-0.8` | This is a **pre-fused, higher-level signal** compared to raw gyro/accel/mag — you can use it directly as a coarse heading baseline, or ignore it and do your own fusion from the raw channels (16–21) for a fairer "what can a from-scratch INS model do" comparison |

**Overall consideration for the whole `S-*.csv` file:** This is the paper's central contribution — a smartphone-realistic INS input stream, complete with gravity-separation support, meant to be fed into a neural sequence model (LSTM/CNN) that learns to predict displacement directly from noisy IMU data, exactly mirroring the IONet-style approach cited in the paper's references (see §10 Step 6).

**Coordinate frame note (from Figure 2 in the PDF):** the smartphone's sensor axes are defined with **X pointing in the direction of travel**, Y to the side, Z vertical (right-hand rule) — but this is the axis convention only when the phone is mounted in the specific orientation shown in Figure 1 (windshield-mounted holder). If you ever mix in your own phone-collected data for testing generalization, you must physically replicate this mounting orientation or apply a rotation correction, or your X/Y axes will not mean "forward/lateral" the way they do in this dataset.

---

## 7. Driving styles, scenario taxonomy, and tyre-pressure codes — full tables

### 7.1 Driver → Driving Style (PDF Table 1)

| Driver | Driving Style | Present in this repo's synchronized folder as |
|---|---|---|
| A | Defensive | `S (Driver A)` |
| B | Defensive | `M (Driver B)` |
| C | Defensive | *not present* (V-St1/4/6/7 all "N/A" for smartphone match) |
| D | Defensive | `Y (Driver D)` (only Y1; Y2 has no S- match) |
| **E** | **Aggressive** | `Vf`, `Vta`, `Vtb`, `Vw` (Driver E) — **the overwhelming majority of the repo's data** |
| F | Defensive | *not present* — smartphone-only data collected independently in France, no vehicle CAN-bus counterpart |
| G | Defensive | *not present* — smartphone-only data collected independently in Nigeria |
| H | Defensive | *not present* — smartphone-only data collected independently in England |

**What to consider:** Of the 8 drivers documented in the paper, only **4 (A, B, D, E)** contribute any data to this repo's synchronized folder, and of those 4, **Driver E alone accounts for roughly 60+ of the ~70 total runs**. Any claim like "this model works well across driving styles" needs the A/B/D "Defensive" data specifically isolated as its own evaluation split — otherwise your test set is implicitly dominated by one aggressive driver's habits, routes, and vehicle.

### 7.2 Full 32-scenario taxonomy (PDF Table 2), with where you'll actually find each one

| # | Scenario | Example run(s) that tag it |
|---|---|---|
| 1 | Hard Brake | M, Y1, S1, Vta1a, Vfa01, Vw4, Vw9, Vw14c, Vw16b, Vw17 |
| 2 | Sharp Turn Left/Right | S3a, Vw5, Vw7, Vw8 |
| 3 | Swift Manoeuvres | Vtb1, Vw4, Vw6 |
| 4 | Round-about | nearly every run — Vw4 alone has ×77 |
| 5 | Rain | Vtb1, Vta29, Vta30 |
| 6 | Night and Day | S3a/S4 (night), Vfb-series (night, not synced), Vw14a/b/c (night), Vw16b/17 (night) |
| 7 | Skid | *no run explicitly tags this in the appendix — verify by inspecting yaw-rate/lateral-accel spikes instead of relying on the label* |
| 8 | Mountain/Hills | Vta16, Vta19–24, Vta28 ("Hilly Road") |
| 9 | Dirt Roads/Gravel Roads | S2, Vta1a, Vta26, Vta27, Vta29, Vtb2, Vtb3, Vtb4, Vtb5 |
| 10 | Country Roads | S2, S3c, Vta1a, Vta2, Vta13, Vta28, Vta29, Vtb1, Vtb2, Vtb4, Vw4 |
| 11 | Motorway | S3a (M6), Vfa02 (M1/M62), Vtb5 (M42/M1), Vw2/Vw4/Vw11/Vw12/Vw13/Vw14a/Vw14b (M5/M42) |
| 12 | Town Centre driving | Vfb01a (not synced), general "Inner city driving" tags on Vw2/Vw3/Vw4 |
| 13 | Traffic Congestion | Vtb5 ("Rush hour Traffic") |
| 14 | Successive left/right turns | S3b, M, Y1, Vw5, Vw7, Vw8 |
| 15 | Rapid accel/decel within short duration | S4, Vta12, Vta14, Vfb02e (not synced) |
| 16 | A-Roads | very widespread — S2, S3a-c, S4, Vfa01, Vta2–17, Vtb6–12, Vw16a, Vw16b, Vw17 |
| 17 | B-Roads | S1, S2, Vfa01, Vfa02, Vta29, Vta30, Vtb1, Vtb5 |
| 18 | Wet roads | Vta1a, Vta29, Vtb1–5, Vtb8–12, Vw2 (implied via rain runs) |
| 19 | U-turns/Reverse | S1, S2, S3a/b, Y1, Y2, M, Vta1b, Vta25, Vta29, Vta30, Vw2, Vw4 |
| 20 | Mud Road | Vta1b ("Hard Brakes on Mud") |
| 21 | Varying Tyre Pressure | encoded across the whole dataset via the run-level Tyre Pressure A–F tag, see §7.3 |
| 22 | Drifts | *no explicit run tag in the appendix — same caveat as "Skid"* |
| 23 | Bumps | Vw6, Vta29 |
| 24 | Inner City driving | Vw2, Vw3, Vw4, Vfb01a (not synced) |
| 25 | Winding Roads | implied by "Vtb29 Windy Road" tag and general Peak District Vta/Vtb runs |
| 26 | Zig-Zag drives | S4, M, Vw9 |
| 27 | Approximate Straight-line Motion | Vta20, Vw12, Vw13, Vw16b, Vw17, Vtb7–11 |
| 28 | Parking | Vtb13 (not synced — V- only) |
| 29 | Potholes | Vta27 |
| 30 | Residential Roads | *no run explicitly tags this — likely implicit within general "Town/Inner City" tags* |
| 31 | Stationary (No Motion) | **Vw1, Vw15** (dedicated), Vta17 (partial, embedded in a moving run) |
| 32 | Valley | Vta28, Vta29, Vtb1 |

**What to consider:** Two scenarios (**Skid**, **Drifts**) and one (**Residential Roads**) appear in the master taxonomy (Table 2) but are **not explicitly attached to any run's feature-tag list** in the appendix tables. This likely means either (a) they occur as unlabeled sub-segments within other runs (e.g. a skid moment inside a rain/wet-road run), or (b) they were captured in the non-synchronized portion of the full 98-hour dataset not included in this repo. Don't assume a `glob`/keyword search over folder or run names will find these scenarios — you'd need signal-level detection (e.g. sudden lateral-acceleration spikes combined with yaw-rate/wheel-speed mismatch for a skid).

### 7.3 Tyre Pressure notation (PDF Table 5)

| Code | Front Right | Front Left | Rear Right | Rear Left | Seen on |
|---|---|---|---|---|---|
| A | 16 psi | 15 psi | 14 psi | 14 psi | All Vta, all Vtb, Vfa01 |
| B | 31 psi | 31 psi | 25 psi | 25 psi | *(documented, not seen tagged on any repo run directly — cross-check per-run tags carefully)* |
| C | 33 psi | 33 psi | 31 psi | 27 psi | Vfa02, Vw1, Vw2, Vw3 |
| D | 33 psi | 33 psi | 26 psi | 26 psi | Vw4–5, Vw7–9, Vw11–17 |
| E | N/A | N/A | N/A | N/A | S1–S4, M, Y1 (i.e. "no special pressure test" / normal/default condition) |
| F | *(only referenced by letter on Vw6/Vw10, exact PSI not separately tabulated beyond A–E in Table 5 as transcribed)* | | | | Vw6, Vw10 |

**What to consider:** Codes A–D represent **deliberately under/over-inflated tyres as a controlled experiment variable** (note A is notably low pressure — 14–16 psi vs. a typical Fiesta spec of ~30-32 psi — while C/D are close to/above normal). Code E appears to mean "standard/unspecified pressure," used for the non-Driver-E runs. If your model uses wheel-speed-derived odometry (columns 11–14 of the `V-` schema), **tyre pressure directly affects the wheel's effective rolling radius**, which directly affects the correctness of a naive `speed = wheel_angular_velocity × radius` conversion. This is a real, physically-grounded confound: a model trained mostly on Tyre-Pressure-A data (Vta/Vtb, i.e. under-inflated) may need re-calibration or an explicit tyre-pressure input feature to generalize to E-condition (normal pressure) runs like the `S`/`M`/`Y` category.

---

## 8. Cross-cutting parameters to consider before modeling

This section pulls together the "what to watch for" points into a single pre-modeling checklist, organized by concern:

**Units & sign conventions**
- `V-` altitude is in **km**; `S-` altitude is in **m** — a 1000x unit mismatch if merged carelessly.
- Heading/orientation/GPS-orientation are all in degrees with a 0/360° wrap discontinuity — always transform to `(sin θ, cos θ)` before regression.
- Steering-angle sign convention is undocumented — empirically verify against a known-direction turn.
- The gyroscope column order in `S-*.csv` may not literally be Yaw/Pitch/Roll as printed in the PDF (probable typo, see §6) — verify against the real header.

**Sampling & synchronization**
- Both files are notionally 10 Hz, but always trust the `V-` file's own "Sample period" column (index 9) over an assumed-constant 0.1s, and use the `S-` file's "Date" column (index 9) as the authoritative timestamp for any cross-file alignment check.
- `S-` GPS fields refresh only at 1 Hz — 9 out of every 10 rows repeat the prior GPS fix; don't treat GPS-derived features as independent samples at the full 10Hz rate.

**Data volume imbalance**
- Run lengths range from **0.3 minutes (Vtb10, 195 rows)** to **211 minutes (Vw4, 126,573 rows)** — a >600x imbalance. Decide up front whether your windowing/sampling strategy will naturally balance this (e.g. fixed-length sliding windows across all runs will over-represent Vw4) or whether you need per-run or per-category weighting.
- Driver E dominates run count and total distance — see §7.1.

**Missing/absent data**
- Several run names appear in the PDF (`V-St1/4/6/7`, `V-Y2`, `V-Vfb01a-d`, `V-Vfb02a-g`, `V-Vtb13`) but have **no synchronized S- counterpart** and are therefore absent from this repo — don't assume the appendix tables and the repo folder contents are 1:1; always check the "Corresponding Smartphone Dataset" column (N/A = not in this repo).
- The GPS-outage index `.txt` file mentioned in the paper's Data Description section was **not found** in the indexed repo tree — check for it after a full `git lfs pull` of the zip; it may only exist inside the archive.

**Physical confounds**
- Tyre pressure (A–F) varies by run and is not itself a CSV column — must be manually re-attached from §7.3 if used as a model feature or a stratification variable.
- Weather (temperature/humidity/wind/precipitation) is per-run metadata, not per-row — if you want row-level weather features you'd need to treat it as constant across an entire run's rows.

---

## 9. Known constraints / gotchas hit during analysis of this repo

1. **Git LFS blocks naive scraping.** `raw.githubusercontent.com` and the GitHub REST tree API return LFS *pointer* text (a 3-line stub with an oid/size), not actual file bytes, for every `.csv`/`.zip`/`.JPG` in this repo — confirmed directly while researching this document. Any ingestion script needs real `git-lfs` tooling, not plain HTTP GET.
2. **No LICENSE file** exists in the repo. Before using this dataset in a hackathon submission, product, or publication, check the paper text for reuse terms or contact the maintainer (`onyekpeu@uni.coventry.ac.uk`) — absence of a license is a legal gray area, not implicit permission.
3. **The repo is pure data — zero code.** The paper's Data Description section mentions "useful python development tools" hosted alongside the data, but no such tooling exists in the indexed file tree as of this analysis — you should assume you're writing the entire loading/training pipeline from scratch.
4. **Filename capitalization is inconsistent** (`V-Vta12.csv` vs. actual `V-vta12.csv` in some subfolders — see §2) — build your file discovery with case-insensitive matching.
5. **The PDF's Table 4 has an apparent labeling typo** in the gyroscope columns (listing "Pitch" twice instead of Yaw/Pitch/Roll) — verify against the real CSV header before trusting column order blindly.

---

## 10. Step-by-step implementation path (with code)

### Step 1 — Data acquisition

```bash
git lfs install
git clone https://github.com/onyekpeu/IO-VNBD.git
cd IO-VNBD
git lfs pull
```

Verify real bytes landed (a real file should be many KB–MB, not ~130 bytes):
```bash
ls -la "Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S1/"
```

### Step 2 — Build a structured metadata table

Transcribe the tables in §3 and §7 of this document into a single machine-readable file, e.g. `run_metadata.json`, keyed by run name:

```json
{
  "Vw4": {
    "driver": "E",
    "style": "Aggressive",
    "category": "Vw",
    "cities": ["Milton Keynes", "Buckingham", "Droitwich Spa", "Kidderminster", "Worcester"],
    "tyre_pressure": "D",
    "date": "2020-01-08",
    "duration_min": 211.0,
    "distance_km": 214.62,
    "n_rows": 126573,
    "speed_range_kmh": [0.0, 131.9],
    "accel_range_g": [-0.66, 0.45],
    "scenarios": ["Roundabout", "Swift Manoeuvres", "Hard Brake", "Inner City Driving",
                  "Reverse", "A-Road", "Motorway", "Country Road",
                  "Successive Left-Right Turns", "Daytime", "U-Turn"]
  }
}
```
This becomes your single source of truth for filtering, splitting, and stratifying — never rely on folder names alone since they only encode driver/category, not weather, tyre pressure, or scenario tags.

### Step 3 — Shared loader with schema verification

```python
import pandas as pd
from pathlib import Path

V_COLUMNS = [
    "n_gps_satellites", "time_of_day_s", "lat", "lon", "velocity_kmh",
    "heading_deg", "height_km", "vertical_velocity_kmh", "sample_period_s",
    "steering_angle_deg", "wheel_speed_fl", "wheel_speed_fr",
    "wheel_speed_rl", "wheel_speed_rr", "yaw_rate_degs",
    "indicated_speed_kmh", "long_accel_g", "lat_accel_g", "handbrake",
    "gear_requested", "gear", "engine_rpm", "coolant_temp_c",
    "clutch_position", "brake_pressure_psi", "brake_position",
    "battery_voltage", "air_temp_c", "accel_pedal_pct",
]

S_COLUMNS = [
    "gps_lat", "gps_lon", "gps_alt_m", "gps_speed_kmh", "gps_accuracy_m",
    "gps_orientation_deg", "gps_sats_in_range", "time_since_start_ms", "date",
    "accel_x", "accel_y", "accel_z",
    "gravity_x", "gravity_y", "gravity_z",
    "gyro_yaw", "gyro_pitch", "gyro_roll",   # verify against real header — PDF mislabels this
    "mag_x", "mag_y", "mag_z",
    "orient_yaw", "orient_roll", "orient_pitch",
]

def find_run_files(root: Path, run_name: str):
    """Case-insensitive search for the V- and S- files of a given run."""
    candidates = list(root.rglob("*.csv"))
    v_file = next(f for f in candidates
                  if f.name.lower() == f"v-{run_name}.csv".lower())
    s_file = next(f for f in candidates
                  if f.name.lower() == f"s-{run_name}.csv".lower())
    return v_file, s_file

def load_run(root: Path, run_name: str):
    v_file, s_file = find_run_files(root, run_name)
    v_df = pd.read_csv(v_file, header=0)
    s_df = pd.read_csv(s_file, header=0)

    # ALWAYS verify real header matches expectation before renaming —
    # do not blindly assume PDF-documented order == actual CSV order.
    assert v_df.shape[1] == len(V_COLUMNS), f"{v_file} has {v_df.shape[1]} cols, expected {len(V_COLUMNS)}"
    assert s_df.shape[1] == len(S_COLUMNS), f"{s_file} has {s_df.shape[1]} cols, expected {len(S_COLUMNS)}"

    v_df.columns = V_COLUMNS
    s_df.columns = S_COLUMNS
    return v_df, s_df
```

### Step 4 — Bias calibration from the stationary runs

```python
def compute_imu_bias(root: Path):
    """Average raw accel/gyro readings over the two dedicated stationary runs."""
    bias_frames = []
    for run in ["Vw1", "Vw15"]:
        _, s_df = load_run(root, run)
        bias_frames.append(s_df[["accel_x","accel_y","accel_z",
                                  "gyro_yaw","gyro_pitch","gyro_roll"]])
    combined = pd.concat(bias_frames)
    return combined.mean()   # subtract this per-channel constant from every S- run before training

# Note: also compare Vw1 vs Vw15 bias separately (don't just average blindly) —
# they differ in tyre pressure (C vs D) and time-of-day (day vs night);
# meaningfully different results would indicate temperature-dependent bias drift.
```

### Step 5 — Windowing & train/test split (by driver/category, not by row)

```python
TEST_CATEGORIES = ["Vtb"]          # hold out an entire category as unseen-route test set
VAL_CATEGORIES  = ["Y", "M"]       # small defensive-driver runs as a style-generalization check
TRAIN_CATEGORIES = ["S", "Vf", "Vta", "Vw"]

def make_windows(df, window_size=100, stride=50):
    """100 rows = 10 seconds at 10Hz. Adjust per how much displacement drift you want per window."""
    for start in range(0, len(df) - window_size, stride):
        yield df.iloc[start:start+window_size]
```

### Step 6 — Baseline model (LSTM dead-reckoning-by-network, PyTorch skeleton)

```python
import torch, torch.nn as nn

class InertialDisplacementNet(nn.Module):
    """
    Input:  windowed, gravity-corrected S- IMU sequence
            (accel_x/y/z minus gravity_x/y/z, gyro_yaw/pitch/roll) -> 6 channels
    Output: relative displacement (dx, dy) over the window, in a local metric frame
            derived from the V- GPS ground truth.
    """
    def __init__(self, in_channels=6, hidden=128, layers=2):
        super().__init__()
        self.lstm = nn.LSTM(in_channels, hidden, layers, batch_first=True)
        self.head = nn.Linear(hidden, 2)   # (dx, dy)

    def forward(self, x):                  # x: (batch, seq_len, 6)
        out, _ = self.lstm(x)
        return self.head(out[:, -1, :])    # displacement prediction for the window
```

Integrate consecutive window predictions (cumulative sum of `dx, dy`) to reconstruct a full trajectory for evaluation.

### Step 7 — Evaluation

```python
import numpy as np

def absolute_trajectory_error(pred_xy, true_xy):
    return np.sqrt(np.mean(np.sum((pred_xy - true_xy) ** 2, axis=1)))

def relative_pose_error(pred_xy, true_xy, delta=10):
    pred_rel = pred_xy[delta:] - pred_xy[:-delta]
    true_rel = true_xy[delta:] - true_xy[:-delta]
    return np.sqrt(np.mean(np.sum((pred_rel - true_rel) ** 2, axis=1)))
```

Report ATE/RPE **broken down per category** (S/M/Y/Vf/Vta/Vtb/Vw) so you can show, e.g., "model degrades on Winding/Vtb runs vs. clean Motorway/Vfa runs" — exactly the axis of comparison the folder taxonomy was built to support.

---

*Document generated as a working reference for the SIH 2026 project. Regenerate/update this file after a full `git lfs pull` reveals the true CSV headers, or if the upstream repo's structure changes.*
