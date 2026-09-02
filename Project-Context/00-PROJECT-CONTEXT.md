# Project Context — GPS-Denied Vehicle Positioning (IO-VNBD)

This is the single master document for this project. It exists so that anyone — a teammate joining cold, a judge asking "what is this and why," a future version of you six weeks from now who's forgotten the details, or an AI assistant picking this back up in a new session — can read one file and come away with the full picture: what the project is, why it exists, the technical background needed to understand it, what dataset it's built on and why, what's already been built, what decisions have already been made (and why, so they don't get silently re-litigated), and exactly what's left to do.

This folder also contains a full copy of [`IO-VNBD-Repository-Breakdown.md`](IO-VNBD-Repository-Breakdown.md) — the complete, exhaustive, file-by-file and column-by-column reference for the dataset itself. This document is the layer above that one: it's about the *project* built around the dataset — the problem, the reasoning, the architecture, the plan — not a restatement of the dataset's contents.

---

## Table of Contents

1. Executive summary
2. Background: what problem this actually solves, and why it's hard
3. Why machine learning instead of classical physics
4. Why the IO-VNBD dataset specifically
5. Where this fits in SIH 2026
6. Full project folder structure, explained
7. The dataset — key facts and why each one matters to this project
8. The technical pipeline, stage by stage
9. The model, explained in depth
10. How success is measured
11. What "done" looks like
12. Current build status
13. Phased roadmap
14. Key decisions already made, and the reasoning behind each
15. Risks, open questions, and things to watch for
16. Glossary of terms

---

## 1. Executive summary

This project builds and evaluates a machine-learning system that estimates how a vehicle is moving — its position, speed, and heading over time — using **only** the motion sensors already inside an ordinary smartphone (accelerometer, gyroscope, magnetometer), with **no dependence on GPS** for that estimate. The motivation is that GPS is not always available or trustworthy (tunnels, dense urban canyons, parking structures, deliberate jamming/spoofing), yet many systems — navigation apps, fleet tracking, autonomous or driver-assist vehicles — still need a usable position estimate during those gaps. The classical physics-based way of doing this (called "dead reckoning": integrating raw acceleration and rotation measurements over time) is notoriously unreliable on cheap sensors because tiny measurement errors compound every time step, and within seconds the estimated position can be wildly wrong. This project instead trains a neural network (a Long Short-Term Memory network, LSTM — a type of model built specifically to learn patterns in sequences of data over time) to learn the *real* relationship between noisy raw sensor data and actual physical displacement, using thousands of real-world examples where both the noisy sensor input and the true GPS-verified answer are known. The data for this comes from IO-VNBD, a public research dataset built exactly for this purpose. The end deliverable is a trained model plus an evaluation pipeline that can show, quantitatively and visually, how closely a phone-sensor-only reconstruction of a drive matches the vehicle's true recorded path — and how that compares to the older, purely physics-based approach.

## 2. Background: what problem this actually solves, and why it's hard

### 2.1 What "positioning" means here

At any moment, a moving vehicle has a **position** (where it is), a **velocity** (how fast and in what direction it's moving), and a **heading** (which way it's pointing). GPS answers all three directly, but only when it has a clear view of enough satellites. The moment that view is blocked or degraded, the vehicle needs some other way to keep updating its best guess of position — this is the general problem of **navigation**, and doing it without external references like GPS is called **inertial navigation** or **dead reckoning**.

### 2.2 What a smartphone can actually measure

A smartphone (or any low-cost Inertial Measurement Unit, "IMU") contains three families of sensors relevant here:
- An **accelerometer**, which measures the forces acting on the phone along three axes (forward/back, left/right, up/down) — including gravity, which is always present and has to be separated out from actual motion.
- A **gyroscope**, which measures how fast the phone is rotating around each of those three axes.
- A **magnetometer**, which senses the direction of the Earth's magnetic field, giving a rough compass heading.

None of these directly measures "position." They measure *rates of change* — acceleration is the rate of change of velocity; velocity is the rate of change of position. To get from raw sensor readings to an actual position, you mathematically have to **integrate** (essentially, repeatedly add up small changes over time) the readings twice: acceleration → velocity → position.

### 2.3 Why the classical (physics-only) approach fails quickly

This double-integration is where the whole problem lives. Every real sensor reading has a small amount of error — random noise, and also a small constant offset called **bias** (the sensor doesn't read exactly zero even when the phone is perfectly still). When you integrate a signal that has even a tiny constant bias, that bias doesn't stay small — it accumulates. A bias of a fraction of a percent in the accelerometer, after being integrated twice, can translate into a position estimate that is off by tens or hundundreds of meters after less than a minute. This runaway accumulation of error is called **drift**, and it is the single defining challenge of inertial navigation on cheap, consumer-grade sensors (as opposed to the extremely expensive, precision-manufactured IMUs used in aircraft and submarines, which drift far more slowly but cost orders of magnitude more).

Vibration makes this worse: a smartphone mounted in a moving car picks up constant small shaking from the engine, the road surface, and the mount itself, which shows up as extra noise on top of the real motion signal, further corrupting a naive physics-based integration.

### 2.4 The real-world situations this actually matters for

- Driving through a tunnel (GPS is fully blocked)
- Driving through a dense city with tall buildings on both sides (GPS signals bounce off buildings — "multipath" — giving inaccurate or jumpy position fixes, sometimes worse than no signal at all)
- Multi-level parking structures
- Deliberate GPS jamming or spoofing (a real and growing concern for defense, logistics, and increasingly civilian applications — GPS spoofing incidents affecting shipping and aviation have been reported repeatedly worldwide)
- Any situation where a backup/fallback position estimate needs to bridge a short GPS outage smoothly, so that whatever system depends on positioning (navigation, autonomous driving, fleet tracking) doesn't just freeze or fail the moment GPS blips

## 3. Why machine learning instead of classical physics

Traditional inertial navigation systems try to fight drift using hand-engineered techniques — most commonly a **Kalman filter**, a well-established statistical method that combines the noisy sensor readings with a mathematical model of how a vehicle is expected to move, constantly correcting itself. These methods work reasonably well with expensive, high-precision IMUs, but on cheap smartphone-grade sensors they still drift substantially, because the underlying assumption (that sensor noise behaves in a simple, predictable statistical way) doesn't hold well enough in practice — real sensor error is messier and more dependent on things like vibration patterns, mounting angle, and vehicle dynamics than a hand-built physics model can easily capture.

The approach this project follows instead — and the one the IO-VNBD dataset was explicitly built to support — is to treat the relationship between "noisy raw sensor sequence" and "actual real-world displacement" as something a neural network can *learn directly from data*, rather than something to model by hand. Instead of writing down equations for how bias and vibration corrupt the signal, you show the model thousands of real examples of "here's 10 seconds of raw noisy sensor data, and here's exactly how far the vehicle actually moved during those same 10 seconds" (known because the vehicle's true GPS position was recorded at the same time), and let the model discover the pattern itself. This is the same idea behind a body of published research the IO-VNBD paper cites directly — most notably **IONet** ("Learning to Cure the Curse of Drift in Inertial Odometry") — where researchers found that a trained sequence model (an LSTM, the same type of model this project uses) substantially outperforms classical integration-based dead reckoning on real, noisy consumer-grade sensor data.

**In short:** classical physics integration is a fixed formula applied to noisy data, and the formula has no way to account for or correct the noise. A trained neural network, given enough real examples, learns to recognize and compensate for the *specific* noise patterns present in real driving — vibration, bias, mounting-angle quirks — because it has actually seen thousands of examples of what those patterns really correspond to in terms of true motion.

## 4. Why the IO-VNBD dataset specifically

To train a model like this at all, you need a specific, fairly rare kind of dataset: real driving data where a noisy phone-grade sensor stream and a trustworthy, independently-verified ground-truth position were recorded **simultaneously on the same drive**. This is harder to produce than it sounds — you need two separate, properly time-synchronized recording systems running in the same vehicle at once, and you need enough driving, across enough different conditions, that a model trained on it will actually generalize rather than just memorizing one specific route.

The IO-VNBD paper's own introduction makes exactly this point: prior published research in this space each used their own privately-collected data, which meant no two papers' results could be fairly compared to each other, and nobody outside the original research group could verify or build on the work. IO-VNBD was published specifically to close that gap — a large (~1,300+ km, ~70 synchronized runs, over a million individual sensor readings), publicly available, real-world dataset spanning a genuinely wide range of driving conditions: city streets, motorways, roundabouts, hard braking, wet and gravel roads, hilly terrain, and both day and night driving. That range matters directly for this project, because it means a model trained and evaluated on this data is being tested against realistic variety, not one artificially clean scenario — which is exactly the kind of credibility this project needs if the goal is a hackathon submission that has to survive scrutiny from judges who may ask "how do you know this actually works, and not just on your one demo clip?"

## 5. Where this fits in SIH 2026

This work sits inside the broader `SIH 2026` working directory alongside `sih-2026-problem-statements` and `SIH_Rankings`, i.e. it is being developed as a candidate solution direction for Smart India Hackathon 2026, in the general problem space of **autonomous and assisted vehicle navigation resilience**. A few reasons this specific angle is a strong hackathon direction, worth keeping in mind when framing the pitch:

- **The problem is immediately understandable without technical background.** "Your phone's GPS can drop out in a tunnel or a parking garage — this keeps tracking your car anyway" is a one-sentence pitch a non-technical judge grasps instantly, unlike many deep-tech ideas that need several minutes of setup before the value is clear.
- **There is a real, citable public benchmark behind it**, which lends credibility that a purely self-collected or synthetic dataset wouldn't have — you can point to the published Coventry University research paper and say "we're building on peer-reviewed, publicly benchmarked work," not just an idea.
- **The demo writes itself visually.** A side-by-side or overlaid map showing the true GPS path, the naive physics-only estimate drifting away from it, and the model's corrected path staying close, is an extremely strong, intuitive visual for a judging panel — it doesn't require the judge to read a table of numbers to understand that the system works.
- **It's extensible into several adjacent, judge-relevant angles** if there's time: defense/border-security relevance (GPS jamming resilience), fleet/logistics tracking in dense urban India where GPS multipath from tall buildings is a real, everyday problem, or driver-assistance/autonomous vehicle safety more broadly.

## 6. Full project folder structure, explained

```
SIH 2026/
├── IO-VNBD-Analysis/
│   └── IO-VNBD-Repository-Breakdown.md      <- pure dataset reference (also copied into this folder)
├── Project-Context/                          <- YOU ARE HERE
│   ├── 00-PROJECT-CONTEXT.md                 <- this file: the project's why, what, and plan
│   └── IO-VNBD-Repository-Breakdown.md       <- copy of the dataset reference, for convenience
└── io-vnbd-positioning/                       <- the actual code project
    ├── README.md                              <- step-by-step setup instructions
    ├── requirements.txt                        <- exact Python packages needed
    ├── .gitignore                              <- keeps the large dataset and trained models out of git
    ├── data/IO-VNBD/                           <- (empty until you clone the real dataset here — see README Step 1)
    ├── src/
    │   ├── schema.py                          <- documented column names for both CSV file types
    │   ├── loader.py                          <- finds and loads one matched vehicle/phone run pair
    │   ├── bias.py                             <- IMU bias calibration using the two stationary runs
    │   ├── windowing.py                       <- cuts a long drive into short fixed-length training chunks, and defines which runs go into training vs. validation vs. testing
    │   ├── model.py                            <- the LSTM neural network architecture itself
    │   └── evaluate.py                         <- scoring: reconstructs a full path from short predictions and measures how far off it is from the truth
    ├── scripts/
    │   ├── verify_schema.py                   <- sanity-checks that the real downloaded CSV files actually match the documented column layout
    │   └── project_gps.py                     <- converts GPS latitude/longitude into plain real-world x/y distances in meters
    ├── notebooks/                              <- (empty — for exploration and visualization, not yet started)
    └── tests/
        └── test_model_smoke.py                <- confirms the Python environment and model code work correctly, without needing the real dataset downloaded
```

**Why the documentation and the code are kept in separate folders:** `IO-VNBD-Analysis` and this `Project-Context` folder are pure reference material — markdown files only, nothing that requires a Python environment or the (large, multi-gigabyte) real dataset to be downloaded. They're meant to be readable from any device, instantly, by anyone who just wants to understand the project or the data without setting anything up. `io-vnbd-positioning` is the actual working software project: it has real dependencies, needs the dataset physically downloaded to run, and is where all further development happens. Keeping these separate means "I just want to understand this project" and "I want to run/build this project" are two clearly different, non-overlapping starting points.

## 7. The dataset — key facts and why each one matters to this project

*(This is a project-relevant summary of the most important facts. For the complete, exhaustive detail — every run, every column, every scenario tag — see the companion [`IO-VNBD-Repository-Breakdown.md`](IO-VNBD-Repository-Breakdown.md) in this same folder.)*

- **~70 synchronized driving runs, roughly 1,300+ km of driving, over a million individual sensor readings.** This is the scale needed for a sequence model like an LSTM to have any real chance of learning a general pattern rather than memorizing a handful of specific routes — small datasets are a common reason sequence models fail to generalize.
- **Each run provides two parallel recordings of the same drive**: a professional vehicle-grade file (GPS position, wheel speeds, steering angle, and more, from the car's own CAN-bus and a dedicated GPS unit) and a smartphone-grade file (accelerometer, gyroscope, magnetometer, and the phone's own weaker GPS). The vehicle file is the **ground truth** this project trains against; the phone file is the **realistic noisy input** the model has to learn to interpret.
- **Driving conditions are deliberately varied**: city streets, motorways, roundabouts, hard braking, wet and gravel roads, hilly terrain, day and night. This variety is exactly what lets this project make a credible claim about how well the model generalizes, rather than a narrow claim that only holds on one type of road.
- **The data is heavily skewed toward one driver ("Driver E," an "aggressive" driving style)**, with a much smaller amount of data from other, "defensive"-style drivers. This matters a great deal for this project: without deliberate care in how the training/validation/test split is built, the model risks mostly learning one person's specific driving habits rather than driving behavior in general — which is exactly why this project's data-splitting strategy explicitly holds out entire driver/route groups rather than randomly mixing everything together (see §14 below).
- **Two specific runs are recorded with the vehicle completely stationary**, sensors running the whole time, existing purely so the small built-in measurement bias of each phone's IMU can be calculated and removed before that phone's data is used for anything else. This is a foundational calibration step this project performs before any training happens.
- **Individual runs vary enormously in length** — from under half a minute to over three and a half hours — which matters for how the data gets cut into training chunks: without care, one very long run could dominate the training data simply by contributing far more chunks than everything else combined.

## 8. The technical pipeline, stage by stage

This is the sequence of transformations the raw data goes through, end to end, from "a folder of CSV files" to "a trained model that produces an accuracy score." Each stage corresponds to a specific file already built in `io-vnbd-positioning/src/`.

**Stage 1 — Load a matched pair.** For a given drive, find and read both the vehicle file and the phone file, and confirm the columns in the real file actually match what's documented (rather than assuming blindly). *(`src/loader.py`, `scripts/verify_schema.py`)*

**Stage 2 — Establish true ground-truth distance.** The vehicle file's GPS gives latitude/longitude in degrees, which isn't directly usable as a distance measurement — two points 0.0001 degrees apart could be a few meters or dozens of meters apart depending on where on Earth you are. This stage converts every GPS point in a run into plain x/y coordinates measured in real meters, relative to wherever that run started. *(`scripts/project_gps.py`)*

**Stage 3 — Remove sensor bias.** Using the two dedicated stationary runs, calculate the small constant offset each phone sensor reads even when perfectly still, and subtract that constant from every other run's phone data before using it. Without this step, the model would partly be learning to compensate for a fixed, boring offset instead of learning real motion patterns. *(`src/bias.py`)*

**Stage 4 — Cut long drives into short chunks.** A drive that's an hour long can't be fed to the model all at once — it's split into many short, overlapping windows (e.g. 10 seconds each). For every chunk, the pipeline records what the phone's sensors measured during those 10 seconds, and — from Stage 2's converted GPS data — exactly how far the vehicle actually moved during that same window. This turns "one long drive" into "thousands of small, labeled training examples." *(`src/windowing.py`)*

**Stage 5 — Split runs into training, validation, and test groups.** Rather than shuffling all the short chunks together randomly (which would let chunks from the same drive appear in both training and testing, letting the model effectively cheat by half-remembering a route it partially saw), entire runs — grouped by driver/category — are assigned wholesale to either training, validation, or testing. This ensures the model is genuinely tested on driving it has never seen any part of. *(`src/windowing.py`, same file — the split logic lives right alongside the chunking logic)*

**Stage 6 — Train the model.** Feed the training chunks to the neural network repeatedly, each time comparing its distance guess against the real answer and adjusting the model's internal parameters slightly to reduce the error, over and over across the full training set, many passes ("epochs"). *(planned — `src/train.py`, not yet built; see §12–13)*

**Stage 7 — Reconstruct a full trajectory.** The model only ever predicts short-window displacements. To evaluate whether it can track a whole drive, its many short predictions for one run are added up in sequence, reconstructing an estimated full path, which is then compared against the true path from Stage 2. *(`src/evaluate.py`)*

**Stage 8 — Score and report.** Compute a small number of standard accuracy metrics (see §10) between the reconstructed path and the true path, reported separately per driving category (city, motorway, hilly, etc.) rather than as one blended number, since real-world accuracy genuinely differs between these conditions and a single average would hide that. *(`src/evaluate.py`)*

## 9. The model, explained in depth

**What kind of model, and why.** The model used is an **LSTM (Long Short-Term Memory) network**, a type of neural network specifically designed to process *sequences* of data where earlier parts of the sequence can meaningfully affect how later parts should be interpreted — exactly the situation here, since the physical motion of a vehicle at any instant is influenced by its motion just before it (a car doesn't instantly teleport to a new speed or direction). LSTMs are a long-established, well-understood choice for exactly this class of problem, and are the same family of model used in the IONet research the IO-VNBD paper itself cites as prior work.

**What goes in.** For each short time window (e.g. 10 seconds of driving, sampled 10 times per second, so 100 individual readings per window), the model receives: the phone's linear acceleration on each of the three axes (the raw accelerometer reading with the constant pull of gravity mathematically subtracted out, using the dataset's own gravity-channel data — see the breakdown doc for why this is provided directly rather than needing to be estimated), and the phone's rotation rate on each of the three axes (from the gyroscope). That's 6 numbers per instant, 100 instants per window.

**What comes out.** For that same window, the model outputs two numbers: how far the vehicle moved sideways and how far it moved forward (in real metric units, e.g. meters) during those 10 seconds — the displacement, in the local flat-ground coordinate frame established in Stage 2 of the pipeline.

**How it learns.** During training, for every window, the model's guessed displacement is compared against the *true* displacement (known because the vehicle file's GPS was recorded at the same time). The difference between the guess and the truth is measured with a loss function (typically Mean Squared Error — the average of the squared differences, which penalizes larger errors more heavily than small ones). The model's internal numbers (its "weights") are then nudged, a tiny amount at a time, in the direction that would have reduced that error, using an optimization algorithm (commonly "Adam," a standard, well-tested choice). This is repeated across every training window, many times over (multiple "epochs"), until the model's predictions stop meaningfully improving.

**Why this specific model architecture is a reasonable starting point, not the final word.** An LSTM taking raw (gravity-corrected) accelerometer and gyroscope readings as direct input is the simplest, most literature-standard baseline for this problem — it's a deliberately conservative starting point precisely so the *whole pipeline* (data loading → bias correction → windowing → training → evaluation) can be proven to work end to end before investing time in architectural improvements. Once that baseline is working and evaluated, natural next steps to consider (not yet built, listed here so the reasoning isn't lost) include: adding the magnetometer data as an extra input channel, adding a CNN layer before the LSTM to let the model learn its own short-range signal features rather than only raw readings, or experimenting with window size and overlap.

## 10. How success is measured

Two standard trajectory-accuracy metrics, both borrowed directly from the wider robotics/navigation research field (the same metrics used to evaluate visual and inertial odometry systems generally, not something invented for this project):

- **Absolute Trajectory Error (ATE):** after reconstructing a full estimated path for a drive (by adding up all the model's short-window predictions in sequence) and lining it up against the true recorded path, ATE measures the average straight-line distance between the estimated path and the true path at each point in time. This answers "overall, how far off was the whole reconstructed trip from reality?"
- **Relative Pose Error (RPE):** rather than looking at total accumulated drift, RPE measures how much error builds up over a fixed short stretch of driving (e.g. every 1 second of travel), regardless of how far into a long drive that stretch occurs. This answers "over any given short interval, how accurate is the model locally?" — useful because ATE alone can be dominated by drift that accumulated early in a long drive, making later, locally-accurate stretches look worse than they really are.

**Reported per category, not as one number.** Both metrics are computed separately for each driving-condition category in the dataset (calm city driving, motorway, hilly/winding roads, etc.), because real accuracy genuinely differs between these conditions, and collapsing everything into a single average would hide exactly the kind of nuance ("works great on motorways, struggles on winding roads") that makes for a credible, specific result rather than a vague, easily-challenged claim.

**The comparison baseline.** Both metrics are also planned to be computed for a simple, non-machine-learning baseline — either the classical physics-based double-integration of the same phone sensor data, or the vehicle's own wheel-speed-based dead reckoning — specifically so the model's numbers mean something in context. A judge or reviewer asking "is 15 meters of error good or bad?" needs a comparison point, and "the classical approach was off by 200 meters over the same stretch" is what makes the number meaningful.

## 11. What "done" looks like

A complete version of this project lets you take a phone's raw sensor recording from a drive the model has genuinely never seen before (held out during training, per the driver/category-based split described above), feed it through the trained model in short rolling chunks, reconstruct an estimated path purely from that sensor data, and show that reconstructed path closely tracking the real GPS-verified path — including through a deliberately simulated "GPS-denied" stretch — with a quantified error measurement (ATE and RPE, in real meters) reported separately per driving category, since accuracy genuinely differs between them.

A strong, hackathon-ready version goes further and shows the **side-by-side comparison against the non-ML baseline** described above, so a judge can see — numerically and visually, on the same map — exactly how much better the trained model performs than the straightforward classical alternative, without needing to already understand the underlying math to appreciate the result.

## 12. Current build status

| Piece | Status | What it does | File |
|---|---|---|---|
| Dataset understanding & documentation | ✅ Done | Full reference covering every file, folder, and CSV column | `IO-VNBD-Repository-Breakdown.md` |
| Load a matched sensor/GPS run pair | ✅ Built | Finds and reads one drive's two files | `src/loader.py` |
| Convert GPS coordinates to real distances | ✅ Built | Turns lat/lon degrees into metric x/y | `scripts/project_gps.py` |
| Remove phone sensor bias | ✅ Built | Calibrates and subtracts the constant sensor offset | `src/bias.py` |
| Cut long drives into short training chunks | ✅ Built | Produces the short labeled windows the model trains on | `src/windowing.py` |
| Correct train/validation/test splitting | ✅ Built | Splits by whole driver/route group, not randomly | `src/windowing.py` |
| The neural network itself | ✅ Built (untrained) | The LSTM architecture, ready to be trained | `src/model.py` |
| Stitch short predictions into a full path + score accuracy | ✅ Built | Computes ATE/RPE from a reconstructed trajectory | `src/evaluate.py` |
| Environment/wiring sanity check | ✅ Built | Confirms everything imports and runs correctly with no real data needed | `tests/test_model_smoke.py` |
| Feed many drives' worth of chunks to the model in batches | ❌ Not built | Needed to actually train on more than one run at a time | `src/dataset.py` (does not exist yet) |
| The actual training loop | ❌ Not built | The code that repeatedly trains the model on the data | `src/train.py` (does not exist yet) |
| Non-ML comparison baseline | ❌ Not built | Classical wheel-speed or physics-integration dead reckoning, for comparison | not started |
| Real dataset downloaded onto this machine | ❌ Not done | Requires `git lfs pull` — see the io-vnbd-positioning README, Step 1 | — |
| Model actually trained on real data | ❌ Not done | Depends on everything above | — |
| Exploratory notebook / first look at real data | ❌ Not done | Plotting a GPS track and raw sensor signals before writing more pipeline code | `notebooks/01_explore_one_run.ipynb` (does not exist yet) |
| Results/demo (charts, before-vs-after visualization) | ❌ Not done | Depends on everything above | — |

## 13. Phased roadmap

**Phase 0 — Foundations (mostly complete).** Understand the dataset thoroughly, document it exhaustively, and build the individual pipeline pieces (loading, GPS conversion, bias correction, windowing, model architecture, evaluation) as isolated, testable units — all done at this point except for actually running against real downloaded data.

**Phase 1 — First real data contact.** Download the actual dataset (`git lfs pull`), set up the Python environment, run the smoke test, run the schema verification script against a real file, and open one run in a notebook to actually look at it — plot the GPS track, plot the raw sensor signal — before writing any more pipeline code around assumptions that haven't been checked against real data yet.

**Phase 2 — End-to-end wiring.** Build the two missing pieces — `src/dataset.py` (batches many runs' worth of windowed chunks together for training) and `src/train.py` (the actual training loop) — and get a first, even rough, trained model running end to end. The goal of this phase is proving the whole pipeline works, not accuracy.

**Phase 3 — Baseline comparison.** Build the simple non-ML dead-reckoning baseline, so the trained model's results have a meaningful point of comparison.

**Phase 4 — Real evaluation and iteration.** Evaluate the trained model properly (ATE/RPE, per category, against the baseline), look at where it's weakest (likely: longer drives, where drift has more time to accumulate; the driving conditions least represented in training data), and iterate — this is where architectural changes (adding the magnetometer, adding a CNN front-end, tuning window size) would be considered, guided by where the actual errors are concentrated rather than guessed at up front.

**Phase 5 — Demo and presentation.** Build the visual before/after comparison (true path vs. naive baseline vs. model output, ideally overlaid on an actual map), package the results into a clear, judge-legible narrative, and prepare the pitch materials.

## 14. Key decisions already made, and the reasoning behind each

These are settled, deliberate choices — recorded here specifically so they don't get silently re-argued or accidentally reversed in a future session without someone realizing there was already a reason behind them.

- **Only the synchronized subset of the dataset is used.** Runs with only vehicle data or only phone data (no matching pair) are excluded entirely, because there's no ground truth to check a phone-only run's predictions against, and no realistic noisy phone input to test a vehicle-only run with. Using unpaired data would require an entirely different, weaker training approach (self-supervised, using the phone's own noisy GPS as a substitute ground truth) — deliberately out of scope for the current plan.
- **Splitting is done by whole driver/route group, never by randomly shuffling individual chunks.** Two chunks taken from adjacent moments in the same drive are nearly identical to each other; a random split would let near-duplicate data end up on both sides of the train/test boundary, producing misleadingly good-looking accuracy numbers that wouldn't hold up on genuinely new driving. Holding out entire categories (e.g. one full folder of runs) forces a fair, honest test.
- **IMU bias is calibrated from the two dedicated stationary runs, and the two are checked separately before being combined into one number.** They were recorded at different times of day, under different tyre-pressure settings, and with different ambient conditions — if their individually-calculated bias values turn out to disagree meaningfully, that itself is a real, worth-reporting finding (temperature- or condition-dependent sensor bias drift), not noise to be blindly averaged away without checking first.
- **GPS coordinates are converted into plain real-world meters before any distance or accuracy calculation happens**, never left as raw latitude/longitude degrees. Degrees are not linearly comparable to physical distance (the same 0.0001-degree difference represents a different real distance depending on location and direction), so skipping this conversion would silently produce meaningless or wrong error numbers without any obvious sign that something was broken.
- **The project deliberately keeps a non-ML baseline in scope, not just the neural network.** A model that "gets to within 15 meters over a 2km drive" means very little in isolation — a judge, reviewer, or future collaborator needs a point of comparison to know whether that's an impressive result or an unremarkable one, and "here's what the classical, non-learned approach gets on the exact same data" is the most honest and legible way to provide that.
- **The model architecture chosen first (a plain LSTM on raw gravity-corrected accelerometer + gyroscope data) is a deliberately simple, literature-standard starting point, not a final design.** The priority in the earliest phase of this project is proving the entire pipeline works correctly end to end — data in, model trained, accuracy measured out — before spending any time on architectural improvements that would be premature to evaluate against a pipeline that hasn't even been run once.

## 15. Risks, open questions, and things to watch for

- **The real CSV headers might not exactly match the documented schema.** The source paper's own documentation has at least one apparent labeling inconsistency (in the gyroscope column names — see the breakdown doc for detail), and this project has not yet been able to open a real, non-pointer CSV file to confirm the actual header row (`git lfs` was not available in earlier analysis sessions). This is exactly why `scripts/verify_schema.py` exists and must be run before trusting the rest of the pipeline against real data.
- **The dataset's heavy skew toward one aggressive driver could limit how well the model generalizes** to calmer, more typical driving styles unless the train/validation/test split (already designed to hold out the smaller, differently-styled driver groups) is actually respected in practice and the results from those held-out groups are given real weight in the final evaluation, not treated as a footnote.
- **Very short runs (some under a minute) versus very long runs (several hours) create a natural imbalance** in how much training data each contributes once cut into fixed-length windows — a small number of very long runs could end up dominating the training set purely by volume unless this is deliberately corrected for (e.g. by capping how many windows are drawn from any single run, or weighting the loss function).
- **No license file exists in the source dataset's repository.** Before this project (or any output built from it) is submitted, published, or used beyond personal research/learning, the terms of reuse should be confirmed against the paper itself or by contacting the dataset's authors — this is a genuine open item, not yet resolved.
- **The real-world deployment gap.** This project trains and evaluates entirely on data recorded from a specific research vehicle and a specific set of phones, mounted in a specific, consistent way. A model that performs well on this dataset is not automatically guaranteed to perform identically on a different phone, a different mounting position/angle, or a different vehicle — this is worth stating plainly and honestly in any presentation of results, rather than overclaiming general real-world readiness from benchmark performance alone.

## 16. Glossary of terms

- **IMU (Inertial Measurement Unit):** the combination of an accelerometer and a gyroscope (sometimes plus a magnetometer) that measures motion and rotation. A smartphone's built-in motion sensors are an IMU.
- **Dead reckoning:** estimating current position by starting from a known position and continuously adding up measured movement over time, without any external reference like GPS.
- **Drift:** the gradual, and often rapidly worsening, accumulation of position error over time when using dead reckoning on noisy sensors — the core problem this whole project exists to reduce.
- **Bias:** a small, roughly constant offset error in a sensor's reading (e.g. an accelerometer that reads a small nonzero value even when perfectly still).
- **GPS-denied:** any situation or environment where GPS signal is unavailable, blocked, degraded, or deliberately jammed/spoofed.
- **Ground truth:** the trusted, verified "correct answer" a model is trained and evaluated against — in this project, the vehicle's professional-grade GPS/CAN-bus recording.
- **LSTM (Long Short-Term Memory network):** a type of neural network designed to learn patterns in sequences of data over time, where earlier parts of a sequence can influence how later parts should be interpreted.
- **Window / chunk:** a short, fixed-length slice of a longer recording (e.g. 10 seconds), used as one individual training example for the model.
- **Epoch:** one complete pass of the model through the entire training dataset during the training process; models are typically trained over many epochs.
- **Loss function:** the mathematical measure of how wrong a model's prediction was compared to the true answer, used to guide how the model's internal parameters get adjusted during training.
- **ATE (Absolute Trajectory Error):** a metric measuring the average distance between a reconstructed estimated path and the true path, over an entire drive.
- **RPE (Relative Pose Error):** a metric measuring how much position error accumulates over a fixed short interval of travel, regardless of where in a longer drive that interval falls.
- **CAN-bus:** the internal digital communication network inside a modern vehicle that carries data between its various electronic systems (engine, wheel speed sensors, brakes, etc.) — this is where the dataset's vehicle-side ground-truth data comes from.

---

*This document is the entry point for understanding this project. For anything about the dataset itself — specific columns, specific runs, specific folders — see [`IO-VNBD-Repository-Breakdown.md`](IO-VNBD-Repository-Breakdown.md) in this same folder. For how to actually set up and run the code, see [`../io-vnbd-positioning/README.md`](../io-vnbd-positioning/README.md).*
