# First-pass implementation plan

> Execute inline using superpowers:executing-plans and test-driven-development.

**Goal:** A usable, verified historical-data and random-backtest foundation.

**Architecture:** CSV validation at boundaries; pure analysis functions; fresh
models receiving only historical prefixes; separate collection and evaluation.

**Tech stack:** Python 3.11+, numpy, pandas, scipy, pytest; standard-library HTTP.

**Spec:** ../specs/2026-10-17-first-pass-design.md

## Global constraints
- No frontend; no commits or pushes.
- No target/future observations in model history or feature preprocessing.
- No fabricated historical data or predictive-performance claims.

## Review focus
- Corrupt remote responses and changed schemas must fail explicitly (task 1).
- Conflicting reruns must preserve existing bytes (task 1).
- Missing history must not become negative observations (tasks 1/2/3).
- Reused mutable models must not carry future checkpoint state (task 3).
- CLI invalid arguments and absent files need useful errors (task 4).

## Task 1: Dataset and collector
Files: src/collect/{dataset,sources,collector}.py, tests/test_dataset.py,
tests/test_collector.py, requirements.txt, .gitignore.
Interfaces: validate_history(frame, require_complete=True) -> DataFrame;
merge_history(existing, incoming) -> DataFrame; collect_history(path, end=None,
source=None) -> report; import_history(path, input_path, source_label) -> report.
- [x] Write and run failing tests for validation, reruns, conflicts and source parsing.
- [x] Implement sorted canonical validation, atomic storage, official JSON adapter,
  explicit CSV import, source diagnostics and missing-draw reporting.
- [x] Run dataset and collector tests; require all passing.

## Task 2: Binary series and descriptive statistics
Files: src/analysis/{series,statistics}.py, tests/test_analysis.py.
Interfaces: binary_series(history) -> DataFrame; inspect_number(history, number)
-> dict; appearance_gaps(series) -> list[int].
- [x] Write and run failing tests with hand-computed intervals and censored cases.
- [x] Implement binary indicators and descriptive stats, excluding bonus.
- [x] Run all tests; require passing.

## Task 3: Random model and backtests
Files: src/models/{base,random_model}.py, src/backtest/{engine,metrics}.py,
tests/test_backtest.py.
Interfaces: model.predict(history, context=None, k=6, seed=None) -> list[int];
run_backtest(history, model_factory, mode, min_train, seed, tickets, repeats,
checkpoints, start, end) -> DataFrame; summarize(results, seed) -> dict.
- [x] Write and run tests for legal/reproducible tickets and leakage prevention.
- [x] Implement isolated prefixes, fresh model factories, seeded checkpoints and
  tickets, scoring and draw-clustered uncertainty with random expectations.
- [x] Run the complete test suite; require passing.

## Task 4: CLI, live execution and documentation
Files: main.py, src/cli.py, README.md, tests/test_cli.py, reports/.
- [x] Add tests for noninteractive commands and errors, run red.
- [x] Implement collect/import, validate, inspect, export-series, backtest,
  candidates and a small interactive menu.
- [x] Run collection/import, all tests and real historical random backtests.
- [x] Review code and report exact provenance, range, limitations and metrics.
