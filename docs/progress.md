# First-pass execution ledger

Ruling: User has supplied detailed scope and explicitly asked to implement and
run it; proceed inline without redundant approval gates. No commit steps.
Ruling: Empty intended workspace is already isolated; no Git worktree needed.
Ruling: Standard-library urllib avoids a missing requests dependency and supports
timeouts and bounded retries. Public connector retrieval is used only to stage
explicitly attributed offline snapshots because shell networking is restricted.
Pre-flight: tasks 2 and 3 consume task 1 canonical DataFrames; task 4 consumes all
public interfaces. Only raw canonical columns may enter model histories.

Task 1: complete. Strict dataset validation, official JSON source adapter,
incremental collector, atomic CSV storage and attributed snapshot import.
Task 2: complete. Binary main-number series and hand-checked descriptive stats.
Task 3: complete. RandomModel, exact historical prefixes, reproducible checkpoint
and walk-forward evaluation, multi-ticket/repeat streams and bootstrap summaries.
Task 4: complete. Interactive/noninteractive CLI, documentation and real-data runs.

Validation ledger:
- New module tests were run before implementation and failed on absent modules.
- Dataset/collection/analysis suite: 26 passed after implementation.
- With backtesting: 42 passed; with CLI: 44 passed.
- Independent review found output/input collisions and null draw_no rows silently
  dropped by pandas groupby. Three regression tests reproduced the failures.
- Fixed path collisions and retained null groups for strict validation. Full
  suite: 47 passed, including both regressions and unchanged-input assertions.
- Windows sandbox reproduced a pytest directory issue: mode 0700 directories
  cannot be reopened, mode 0777/inherited ACLs work. Local test fixture uses
  inherited permissions; optional pytest cache is disabled. No ACLs were changed.
- Official collector ran and returned a clear network error (WinError 10061).
- Explicit public-snapshot import validated 1,245 contiguous draws,
  2002-12-07 through 2026-10-10. No direct official-source verification claimed.
- Walk-forward targets 300..1245, seed 42: 946 tickets, mean 0.7885835095,
  best 4 matches. Checkpoints: 100 targets, 5 tickets x 10 repeats, mean 0.7888.
- Binary export, inspect number 17 and noninteractive main.py exercised.

No Git repository was created; no commits or pushes. Files are in the user's
original empty project directory. The first-pass scope is implemented; advanced
models and periodicity remain explicitly deferred as requested.

## Phase 2 temporal exploration

Plan: docs/superpowers/plans/2026-10-17-temporal.md. User requested the complete
exploratory scope, with no advanced predictors and no commits/pushes. Repository
now has user-created initial commit 0d633e7; work remains in the requested path.
Baseline before edits: clean Git status, 47 passing tests.

Implemented appearance history extensions, calendar tables, guarded ACF/spectrum,
descriptive score and count-preserving shuffles; trailing windows, causal
thresholds, endpoint regimes and support-overlap-aware recurrence; aggregate and
per-number exports, plots and CLI. Source/backtest/model logic was not modified.

Test-first cycle: new-module tests initially failed on missing modules. Calendar
and periodicity suite then reached 61 passing tests. Regime fixture expectations
were corrected after inspecting expanding quantiles: a repeated equal high score
eventually equals its own threshold and must not qualify under strict >.
Yearly report fixture spans 2002, 2003 and 2004 (60 draws), so two numbers give
six year rows, not four. These were fixture arithmetic corrections, not changes
to production thresholds or grouping rules.

Independent review checked numeric safeguards and real-data prefix invariance.
It found one CLI null-score formatting error for nonempty unsupported windows.
A new regression reproduced the TypeError; CLI now prints unavailable/status.
Final suite after fix and progress messages: 69 passed, including original 47.
Compile checks and git diff --check passed (Git only noted CRLF conversion).

Numbers 7,17,34 were selected before observing outcomes, inspected with 4,999
shuffles per eligible scope, and their nine-panel PNGs visually reviewed.
Dataset SHA256 remains b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e.
All-number aggregate completed successfully: 160,020 rolling rows, 1,171 regimes,
135 recurrence rows and 180 fixed-scope null rows. Of those, 155 eligible scopes
received 4,999 shuffles each (774,845 total); 25 had insufficient appearances.
Measured runtime 502.815s total, 58.540s rolling/regimes, 439.630s null tests.
Five raw p-values <.05; none after Bonferroni correction across 180 planned scopes.
Lowest raw p=.0028 (number8, latest52), adjusted=.504. Three heuristic recurrence
candidates: number8/window104 (242 draws), number13/window52 (216.75),
number34/window52 (230.5). No recurrence significance test or predictive claim.
Aggregate and selected-number null CSVs matched exactly. Detailed observations,
limitations, output schemas and runtime are in docs/temporal-analysis.md.
Phase 2 scope complete. No commits or pushes.

## Phase 3 predictive experiments - 2026-10-17

Added canonical causal supervised features; same-number nearest-state model;
pooled SciPy L2 logistic regression; optional sklearn Random Forest and
LightGBM/XGBoost adapters. Separate ranking engine supports frozen fits at a
configurable cadence, weighted tickets, exact random-reference simulations,
paired block-bootstrap uncertainty, time blocks, ablations and full audits.
CLI: compare-models, predict-current, explain-number. Original backtests intact.

Protocol fixed before results: feature history104, first feature target105,
evaluation601..1244, reserved1245, cadence26, seed42, no tuning. Export contains
51,345 rows x37 columns including31 predictors. Full feature transform75cols.
644 targets x9 available model/group specifications =5,796 audited rows;
3,725 coefficient rows; 27 time blocks; 115,920 separately sampled tickets.
Seven logistic feature groups evaluated on the identical target set.

RandomModel mean hits .798137, Similarity .777950, full Logistic .796584.
Gap-only .849379 had paired interval vs random [-.035714,.139790]. No model's
paired mean-hit interval excludes zero. Incremental periodicity vs frequency+
gap is +.015528 hits, CI[-.054348,.090062], inconsistent across time blocks.
Incremental recall and mean-winning-rank intervals also include zero.
No validated predictive advantage or incremental periodicity value established.

Completed fixed experiment163.349s (features47.380s, similarity35.562s, full
logistic29.911s). An earlier diagnostic-heavy similarity attempt was canceled;
avoiding unused neighbor explanations preserved exact scores and improved
runtime. No configuration or evaluation boundaries changed. Real-data current
logistic command55.17s; number17 similarity explanation45.91s.

Independent review found no causal leakage and caught missing configuration
in --no-audit metadata. Regression reproduced it; configurations/runtime now
persist independently of detailed audit. Artifact verification checked all
target outcomes, hits, rankings, 45 scores, ticket counts and fit cutoffs.
Final suite:85 passed,2 skipped in19.02s (all original69 still pass).
Compile and git diff --check pass. Canonical SHA256 unchanged.

Remaining environment blocker: sklearn, LightGBM, XGBoost are absent; package
installation attempts failed and HTTPS to PyPI was refused (WinError10061).
Forest/boosting adapters were not executed and their integration tests skip.
No algorithm was silently substituted. SciPy logistic backend is explicit.
See docs/predictive-experiments.md and reports/prediction/ for methods/results.
No commits or pushes.
