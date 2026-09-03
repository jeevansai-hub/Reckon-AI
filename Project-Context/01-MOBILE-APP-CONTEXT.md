# Mobile App Context — Reckon-AI Companion App

This document is the single entry point for the **mobile app** — the product that end users
and judges actually touch. It exists so that whoever picks up app work (a teammate, a future
session, you in six weeks) can read one file and know what the app is, why it's a separate
project, what it needs from the ML side, and what to build first.

It deliberately does **not** repeat the ML pipeline's own context — for the dataset, the model,
training, or evaluation, see [`00-PROJECT-CONTEXT.md`](00-PROJECT-CONTEXT.md). This file is
scoped to the app alone.

> **Note on scope:** the ML repo's own PRD lists on-device mobile deployment as an explicit
> non-goal for its current phase (it's a research/training repo, not a product repo). That
> non-goal applies to the ML repo's scope, not to this app's existence — this document treats
> the app as a real, separate workstream with its own timeline, not blocked by that PRD.

---

## Table of Contents

1. Executive summary
2. Why the app is a separate repo
3. What the app actually needs from the ML side
4. Tech stack — and why
5. What the app does, screen by screen
6. App-side architecture
7. Current status
8. Phased roadmap
9. Decisions already made
10. Open questions
11. Glossary

---

## 1. Executive summary

The app is what a driver, a judge, or a demo audience actually sees: a live map that keeps
tracking a vehicle's position through a GPS-denied stretch (a tunnel, an underground car park,
a dense urban canyon) without freezing, and hands back to real GPS smoothly — no visible jump —
the moment signal returns. Underneath, it runs a trained model on-device, snaps the estimate onto
the real road network, and blends sources continuously. Everything the ML repo builds and proves
exists to feed this app one thing: a small, fast, on-device model that turns raw phone sensor
readings into a position estimate.

## 2. Why the app is a separate repo, not a folder in this one

Already decided, restated here for permanence:

- **No toolchain overlap.** This repo is Python (pip, pytest, ruff). The app is a different
  language and build system entirely. Neither project's tooling helps the other.
- **The interface between them is one artifact, not shared source.** The ML repo exports a
  trained model file; the app consumes that file. That's the entire contract — the app never
  needs this repo's dataset, training code, or config YAMLs.
- **Different timelines.** The ML repo is mid-research (no trained model yet). The app's core
  screens and architecture can be scaffolded independently of that timeline, without either
  side blocking the other.
- **Already burned once by nesting.** A sub-project folder inside this repo broke CI silently,
  because GitHub Actions only reads `.github/` at the true repo root. A mobile build nested the
  same way would hit the same failure class, worse — Android/Flutter tooling is even more
  sensitive to running from the wrong directory.

**Repo name (suggested):** `reckon-ai-mobile`, created as an independent GitHub repository,
owned separately from `Reckon-AI`.

## 3. What the app actually needs from the ML side — the model contract

This is the one place the two repos touch. Whoever builds the app should be able to build
almost the entire thing against a **stub** matching this contract, without ever running the
ML repo's own Python code.

| Item | Contract |
|---|---|
| **Model file format** | TensorFlow Lite (`.tflite`) — free, open-source, the standard for on-device inference on both Android and iOS/Flutter |
| **Input** | A window of 100 timesteps × 6 channels: gravity-corrected accelerometer (x, y, z) + gyroscope (yaw, pitch, roll), sampled at the phone's native rate and resampled to match the model's training rate |
| **Output** | Two floats per window: distance travelled (metres) and heading change (radians) — **not** raw (dx, dy) in a global frame; see `00-PROJECT-CONTEXT.md` for why |
| **Update cadence** | One inference per window; a new window becomes available every `stride` samples (currently 50, i.e. every 5 seconds at the training rate — the app should not expect faster updates than this without retraining on a shorter stride) |
| **Delivery** | A tagged release in the ML repo (e.g. `model-v1`) with the `.tflite` file attached and a short changelog entry stating input/output shape and any changes since the last version |

Until a real model is exported, the app can develop against a **fake model** that returns
plausible-looking random distance/heading values, so UI, state management, and map rendering
can all be built and demoed before training finishes.

## 4. Tech stack — and why (free-only, matching this project's constraint)

| Layer | Choice | Why |
|---|---|---|
| Framework | **Flutter** | Single codebase for Android + iOS, fastest path to a working demo in hackathon time; the SIH pitch names "Android (Kotlin/Java) or Flutter" as either acceptable |
| On-device inference | **`tflite_flutter`** | Free, open-source binding to TensorFlow Lite; matches the model export format above |
| Map rendering | **`flutter_map`** (Leaflet-based) or **MapLibre GL** with OpenStreetMap tiles | Fully free, no API key, no usage billing — unlike Google Maps SDK or Mapbox SDK, both of which have paid tiers beyond a free credit (the same reasoning already applied to the ML repo's map-matching choice) |
| Road network / map-matching data | **OpenStreetMap** extracts, same source the ML repo's `mapmatch` module uses | Keeps the app and the ML repo's map-matching demo visually and data-consistent |
| Sensor access | Flutter's `sensors_plus` package | Free; reads accelerometer, gyroscope, magnetometer at native rate |
| State management | Provider or Riverpod (either is free and standard) | Whichever the app developer is already comfortable with — not a consequential choice for a hackathon timeline |

**Explicitly avoided, same reasoning as the ML repo:** Google Maps SDK, Mapbox SDK — both carry
paid usage tiers; OSM-based free alternatives cover the same need.

## 5. What the app does, screen by screen

Derived directly from the SIH26168 pitch's success criteria — the app's job is to make these
visibly true, not just claim them.

1. **Live map screen (primary).** Shows the vehicle's current position, continuously, in all
   three modes: GPS mode, dead-reckoning mode, fusion/reacquisition mode. The user should never
   be able to tell which mode is active just by looking — that indistinguishability *is* the
   product's success criterion.
2. **Mode indicator (subtle, for demo purposes).** A small, dismissible status chip — "GPS",
   "Sensor-only", "Reconnecting" — useful for a judge demo, but designed so it can be hidden for
   a "look, it's seamless" moment.
3. **Outage demo mode.** A deliberately included judge-facing feature: a button that simulates
   a GPS outage of a configurable duration/distance, so the seamless-handover behavior can be
   demonstrated on demand without needing to physically drive into a tunnel.
4. **Trip summary / accuracy view (stretch).** After a drive, show the reconstructed path
   alongside where GPS confirms it should have been — the same before/after visual the ML repo's
   evaluation produces, but live and on-device.

## 6. App-side architecture

```
Phone sensors (accelerometer, gyroscope, magnetometer, GPS)
        |
Sensor Manager -- buffers readings into rolling windows matching the model contract
        |
Signal Quality Monitor -- watches GPS accuracy/satellite count, decides current mode
        |
        +-- GPS available --> pass GPS position straight through
        |
        +-- GPS lost --> On-Device Model (TFLite) -- distance + heading change
                                |
                          Position Integrator -- accumulates heading + distance into a path
                                |
                          Map-Matcher (mirrors ML repo's mapmatch module logic, run on-device
                                        or against a pre-downloaded local OSM extract)
                                |
        +-- GPS reacquired --> Fusion Blender -- blends sensor estimate back to GPS over 2-5s
        |
Map Renderer -- draws the final fused position on the live map
```

This mirrors the five-layer system architecture already diagrammed for the ML side
(`reports/system-architecture.html` in the `Reckon-AI` repo) — the app is effectively Layers
1, 2 (partially, on-device), 3 (inference only, not training), 4, and 5 of that same diagram,
running in real time instead of offline on recorded data.

## 7. Current status

**Not started.** No repository exists yet. This document is planning only.

Nothing in this document requires the ML repo's training to finish first — screens, sensor
collection, map rendering, and the outage-demo UI can all be built against the stub model
described in §3, in parallel with ML work continuing in `Reckon-AI`.

## 8. Phased roadmap

**Phase 0 — Repo and shell.** Create `reckon-ai-mobile`, scaffold a Flutter project, get a map
rendering with a hardcoded position. No sensors, no model yet.

**Phase 1 — Sensor collection.** Read real accelerometer/gyroscope data, buffer into windows
matching the model contract's shape. Verify against real phone sensor logs before trusting it.

**Phase 2 — Stub inference.** Wire a fake model (random plausible outputs) into the pipeline so
the full mode-switching logic (GPS → dead-reckoning → fusion) can be built and demoed end to end
before a real model exists.

**Phase 3 — Real model integration.** Swap the stub for the ML repo's exported `.tflite` file
the moment `model-v1` is tagged. This should be close to a drop-in replacement if the contract
in §3 was respected.

**Phase 4 — Map-matching + outage demo.** Add the road-snapping layer and the judge-facing
outage simulation button.

**Phase 5 — Polish for demo.** Mode indicator, trip summary, visual polish, rehearse the
tunnel-outage demo flow.

## 9. Decisions already made

- **Separate repo**, not nested in `Reckon-AI` — §2.
- **Flutter**, not native Android/iOS separately — single codebase for hackathon timeline.
- **Free-only mapping stack** (OSM + flutter_map/MapLibre) — no Google Maps/Mapbox billing risk.
- **TFLite** as the model export/runtime format — free, standard, matches the pitch's own
  named tech stack.
- **The app can be built ahead of a trained model**, against a stub — decouples the two repos'
  timelines rather than making the app wait.

## 10. Open questions

- **Native OSM extract vs. live tile fetching.** A tunnel/underground demo likely has no network
  — the app may need a pre-downloaded local map extract for the demo route, not live tiles.
  Needs deciding before Phase 4.
- **On-device map-matching cost.** Running HMM/Viterbi map-matching on a phone in real time is a
  heavier ask than the ML repo's offline batch use of the same technique — may need a lighter
  on-device approximation, decided once real timing is measured.
- **iOS vs. Android-only for the demo.** Flutter supports both, but if the physical demo device
  is fixed (e.g. one Android phone), iOS support may not need finishing for the hackathon itself.
- **Who owns this repo/timeline.** Not yet assigned to a specific teammate.

## 11. Glossary

See `00-PROJECT-CONTEXT.md` §16 for terms shared with the ML side (IMU, dead reckoning, drift,
bias, ATE/RPE, etc.). App-specific terms:

- **Stub model:** a placeholder that mimics the real model's input/output shape with fake data,
  used to build and test the app before a real trained model exists.
- **Mode:** the app's current position-source state — GPS, sensor-only (dead-reckoning), or
  fusion/reacquisition (blending back to GPS).
- **Outage demo mode:** a judge-facing feature that manually triggers a simulated GPS loss, so
  the handover behavior can be shown without physically driving into a real GPS-denied area.

---

*For the ML pipeline this app depends on, see [`00-PROJECT-CONTEXT.md`](00-PROJECT-CONTEXT.md).
For the exact dataset details, see
[`IO-VNBD-Repository-Breakdown.md`](IO-VNBD-Repository-Breakdown.md).*
