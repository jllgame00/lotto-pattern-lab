# Lotto Pattern Lab: first-pass design

Build a local Python research CLI, with no frontend. The user supplied the scope
and instructed immediate incremental implementation; no commits or pushes.

The canonical dataset is data/raw/lotto_history.csv with draw_no, draw_date,
num1..num6 and bonus. Strict validation rejects fractional values, duplicate
main numbers, bonus overlap, invalid dates, conflicting draws and missing draws.
Identical duplicate rows may be collapsed by collection. Analysis requires a
continuous history beginning at draw 1; missing draws are never filled with zeros.

Use the official Donghaeng website JSON results endpoint as the primary source.
Use explicit offline CSV import for snapshots when network access is unavailable.
Record source URLs, retrieval time, content hashes and collection diagnostics.
Write through temporary files and atomic replacement. Never silently overwrite
conflicting historical outcomes or reinterpret network failure as end of history.

Create a 45-column binary matrix excluding bonus. Provide frequency, recent
26/52/104 frequencies, observed inter-appearance distances, population gap
variance/std, consecutive run lengths and current absence length. Unobserved
gaps are missing values, not fabricated intervals.

RandomModel implements a common model interface; uniform six-number sampling
uses an explicit seed. Backtesting takes a model factory and creates a fresh
model for each ticket, protecting against state carried from later checkpoints.
At target N, the model receives only copied canonical rows 1..N-1 and a context
with draw number and a scheduled date derived from the training cutoff. Actual
target numbers are read only after prediction. All feature engineering belongs
inside the model on that restricted history. This is API isolation, not a sandbox
against malicious models accessing files or globals.

Support seeded random checkpoints and full walk-forward, repeated simulations,
multiple tickets per target, auditable ticket CSVs and summary JSON. Report
0..6 match distribution, mean, 3+/4+/5+ rates and best ticket; compare with exact
hypergeometric random expectation (6*6/45 = 0.8). Approximate confidence intervals
use draw-level averages, with caveats for serial dependence and small samples.

Defer year/month analysis, periodicity, similarity and all nonrandom strategies.
Test validation, import reruns/conflicts, HTTP response parsing, binary series,
hand-calculated gaps, seeded predictions, boundary controls, target/future
perturbation invariance, model state isolation and mutation protection.
