# Lotto Pattern Lab

A local Python research project for Korean Lotto 6/45 historical data. No web
app or frontend. This first pass provides data collection and validation,
binary number histories, frequency/gap statistics, and a reproducible random
baseline backtester. It does **not** establish predictive performance.

## Quick start

Python 3.11 or newer is required. From this directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

An interactive terminal shows a small menu. With redirected input, the same
command prints dataset status and help without blocking. All work is also
available through subcommands:

```powershell
python main.py collect
python main.py validate
python main.py inspect 17
python main.py export-series
python main.py candidates --seed 42
python main.py backtest --mode checkpoints --checkpoints 100 --tickets 5 --repeats 10 --seed 42 --report reports/random_checkpoints
python main.py backtest --mode walk-forward --min-train 299 --seed 42 --report reports/random_walk_forward
python -m pytest -q
```

Use `--data path/to/history.csv` **before** the subcommand to use another dataset.
Relative output paths are relative to your working directory; default paths are
relative to the project root. No command downloads data implicitly except
`collect` without `--input`.

## Data and provenance

Canonical file: `data/raw/lotto_history.csv`.

Columns: `draw_no, draw_date, num1, num2, num3, num4, num5, num6, bonus`.
Main numbers are sorted within each draw; draws are sorted ascending. Calendar
fields (`year`, `month`, `iso_week`, `weekday`, Monday=0) are derived on loading.

The first collected snapshot contains **1,245 draws**, from **2002-12-07
(draw 1) through 2026-10-10 (draw 1245)**, with no missing draws. This is the
available snapshot range, not a promise that a future run is up to date.

The primary collector targets the [Donghaeng results website](https://www.dhlottery.co.kr/lt645/result)
and its website endpoint:
`https://www.dhlottery.co.kr/lt645/selectPstLt645InfoNew.do?srchDir=center&srchLtEpsd=1`.
Its response is a batch in `data.list`, with `ltEpsd`, `ltRflYmd`,
`tm1WnNo` through `tm6WnNo`, and `bnsWnNo`. This is an undocumented website
endpoint, not a guaranteed public API. The old
`common.do?method=getLottoNumber&drwNo=...` route was investigated but is not
assumed to remain available after the website redesign.

During implementation, direct Python HTTP requests to Donghaeng failed with
connection refusal (WinError 10061) in the restricted environment. The live
official JSON adapter therefore remains **unverified end to end**. Tests cover
its expected schema and error handling; the collector reports retrieval failure
and never interprets it as proof that all draws have been collected.

To run the actual historical pipeline, public snapshots were retrieved using the
available GitHub connector and explicitly imported:

- Draws 1–1156: [hyomuel/Lotto/data.json](https://github.com/hyomuel/Lotto/blob/main/data.json).
- Draws 1157–1245: individual files in
  [johyunchol/lottogo-python](https://github.com/johyunchol/lottogo-python/tree/main/src/constant/draw_no).
- Draws 1, 500 and 1156 were compared between the two snapshots and matched.
  These are spot checks, not full independent official verification.

`data/raw/sources.json` records source ranges, retrieval details and snapshot
hashes. `lotto_history.metadata.json` records import/collection events, input
hashes, the canonical CSV hash and missing/error diagnostics. The original
normalized snapshots remain locally in `data/raw/snapshots/` (Git-ignored).
These are third-party mirrors; valid schema and spot checks cannot prove all
values match official results. There is no automatic silent mirror fallback.

Explicit offline import, also useful in restricted environments:

```powershell
python main.py collect --input data/raw/snapshots/combined_history.csv --source-label "Public GitHub snapshots; see data/raw/sources.json"
```

Reruns merge by draw number. Identical rows collapse; conflicting outcomes stop
the import and preserve the existing CSV. Invalid values are not repaired.
Official collection skips existing draws, retrieves missing ones with bounded
retries/timeouts and paced requests, and retains successful partial progress on
source failure. Failures and missing draws are reported in JSON with exit code 1.
CSV writes use a same-directory temporary file and atomic replacement. Run only
one collector/import writer at a time; concurrent writers are not supported.

Validation rejects null/fractional/boolean numbers, duplicate main numbers,
numbers outside 1–45, a bonus in the main numbers, duplicate draw identifiers,
and dates inconsistent with the weekly calendar starting 2002-12-07. Collection
may store partial progress, but analysis and backtests refuse incomplete history.
Missing draws are never converted into zero appearances. Completeness is checked
through the stored/requested endpoint; it does not certify source freshness.

## Descriptive analysis

`binary_series(history)` returns a draw-indexed, 45-column `uint8` DataFrame.
Exactly six entries per row are 1. **Bonus is excluded.** The exported file is
`data/processed/number_series.csv`.

`inspect_number(history, number)` reports total frequency, appearance rate,
recent 26/52/104-draw frequency and rate, completed appearance intervals, mean,
median, population variance/std, adjacent appearance pairs, longest/current run,
and time since last appearance.

An appearance interval is the distance between appearances: adjacent draws give
an interval of 1. Current gap is the number of absent draws since the last
appearance, so an appearance in the latest draw gives 0. If a number has never
appeared, current gap is `None` and the observed absence length is a lower bound.
Without two appearances, completed-gap statistics are `None`. Boundary gaps are
censored and excluded. Recent-window output includes its actual denominator
when fewer than N draws are available. Small completed-gap samples are flagged.

## No future data leakage

At target draw N, `run_backtest` supplies a fresh, unfitted model with a deep
copy of **draws 1 through N−1 only**. Extra columns are removed before invoking
models so precomputed future-dependent features cannot accidentally enter.
Context contains only the target draw number and the next scheduled date derived
from the final training draw. Actual target numbers are read only after the
model returns a valid ticket.

Models implement `score_numbers(history, target_draw_context)` and/or
`predict(history, context=None, k=6, seed=None)`. `RandomModel` scores all numbers
equally and samples six unique integers uniformly without replacement. The
engine takes a model **factory**, never a shared fitted model. A new instance is
created per ticket; no model is reused between checkpoints or repetitions.

Future models must compute and normalize features entirely inside their supplied
history, including any fitting or selection of similar regimes and their known
outcomes. Model factories must return fresh, unfitted instances. The interface
is not a security sandbox: models must not access global full-history files,
prefitted state, or external future data. Full-history analysis exports are
exploratory artifacts and must not be reused as prediction inputs.

Tests inspect exact training boundaries, mutate target/future outcomes, check
prediction invariance, attempt history mutation and verify fresh model instances.

## Backtesting and interpretation

- `--min-train 299` starts at target 300 with draws 1–299 as training data.
- Walk-forward evaluates each eligible draw, including the final stored draw.
- Checkpoints sample eligible targets without replacement using `--seed`.
- `--start` and `--end` restrict evaluated target draws, not the training prefix.
- `--tickets` produces tickets per target per repetition; `--repeats` repeats
  ticket simulation on the same target set with independent deterministic seeds.
- Ticket seeds depend on root seed, target, repetition and ticket index, so a
  target's first ticket is reproducible even in a smaller evaluation range.
- Tickets can coincide by chance; each ticket itself always has six distinct
  numbers. Repetitions do not create additional historical draws.

Reports contain per-ticket CSV audit trails and JSON summaries: average matches,
0–6 distribution, 3+/4+/5+ rates, best match, per-repeat means, configuration,
package versions, dataset hash/provenance and approximate 95% mean intervals.
Intervals bootstrap target-draw averages, keeping tickets/repetitions for a draw
together. They assume independent draws; adaptive strategies with serially
dependent errors will need a temporal block bootstrap. Rare-event rate intervals
and multiple-comparison adjustments are deferred.

The exact uniform baseline is hypergeometric:
`P(matches=m) = C(6,m) * C(39,6-m) / C(45,6)`.
Its expected average is **0.8 matches per ticket**. This first pass compares
RandomModel simulations with that theoretical baseline; comparisons among
learned strategies will come after those strategies exist. The best ticket
depends on how many tickets are generated and is not evidence of skill.

Initial seed-42 verification:

| Run | Targets | Tickets | Mean matches | Approx. 95% CI | Best |
|---|---:|---:|---:|---|---:|
| Walk-forward, draws 300–1245 | 946 | 946 | 0.788584 | 0.738901–0.837209 | 4 |
| 100 checkpoints, 5 tickets × 10 repeats | 100 | 5,000 | 0.788800 | 0.767200–0.810205 | 4 |

Both intervals contain the 0.8 random expectation. These runs verify the
evaluation pipeline; **no predictive advantage is claimed**.

## Structure and next phases

```text
data/raw/             canonical CSV, provenance, local source snapshots
data/processed/       derived binary series
src/collect/          dataset validation, official source, collection/import
src/analysis/         binary series and frequency/gap statistics
src/models/           model interface and RandomModel
src/backtest/         isolated evaluation and metrics
src/cli.py            command-line interface
tests/                offline validation, collection, analysis, leakage and CLI tests
reports/              per-ticket CSVs and summary JSONs
docs/                 design, implementation plan and execution record
main.py               entry point
requirements.txt      dependencies
```

Deferred deliberately: year/month normalized comparisons, rolling periodicity,
autocorrelation/periodograms/FFT, regime similarity, FrequencyModel, GapModel,
SeasonalityModel, PeriodicityModel, SimilarityModel, EnsembleModel and multi-model
comparison. Their acceptance criterion is leakage-safe out-of-sample evaluation
against RandomModel, not visually interesting patterns.

Tests require no network. Test scratch directories inherit normal permissions
because the Windows sandbox cannot reopen pytest's owner-only directories;
pytest's optional cache is disabled for the same reason. The complete suite was
run with Python 3.13.1. No commits or pushes were made.
