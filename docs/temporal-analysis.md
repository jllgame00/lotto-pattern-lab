# Temporal exploration: methods and usage

This phase describes temporal behavior of the six main numbers. Bonus is excluded.
It does not introduce a prediction strategy. All reports use the existing
validated snapshot through draw 1245; its third-party provenance limitations
remain unchanged.

## Commands

```powershell
python main.py inspect 17
python main.py inspect 7 --permutations 4999 --seed 42
python main.py inspect 34 --permutations 4999 --seed 42
python main.py analyze-all --permutations 4999 --seed 42
python main.py inspect 17 --no-plots --permutations 0
python main.py analyze-all --windows 26 52 104 --max-lag 52 --min-cycles 3 --percentile 90 --regime-history 52 --regime-length 3
```

`--reports-dir` changes the report root. Default reports are in `reports/`;
inspection tables are isolated in `reports/number_N/`, plots in `reports/plots/`.
Default simulations are 199 per eligible scope; the delivered research run uses
4,999. Zero skips simulations. Seeded results are reproducible; timings vary.
Changing scope or settings is another exploratory search, not independent confirmation.

The reusable entry points are `calendar_stats`, `rolling_stats`,
`autocorrelation_analysis`, `spectral_analysis`, `periodicity_metrics`,
`permutation_comparison`, `detect_regimes`, `recurrence_stats`, `analyze_history`
and `plot_number`, in the corresponding `src/analysis/` modules.

## Outputs

| File | Contents |
|---|---|
| `number_history_stats.csv` | One row per number: total/rate, all appearance draws and intervals (JSON arrays), gap stats, current gap, runs and longest observed absence |
| `appearance_history.csv` | One row per appearance: number, draw, date and interval from preceding appearance |
| `yearly_number_stats.csv` | Number × year: eligible draws, appearances/rate, expectation/deviation and within-year completed-gap statistics |
| `monthly_number_stats.csv` | Number × month 1–12: eligible draws, rate and ratio to number's full-history rate |
| `year_month_number_stats.csv` | Number × observed year-month, normalized by that month's eligible draws |
| `rolling_number_stats.csv` | Number × window size × endpoint: frequency/rate, gap statistics/status, ACF/spectrum/score, prior-only threshold and high-score flag |
| `periodicity_regimes.csv` | Contiguous confirmed high-score runs, support start, endpoint dates, confirmation/peak draw, score and dominant lag/period |
| `regime_recurrence.csv` | Raw regime starts and coalesced-episode intervals, variability and insufficient/irregular/candidate status |
| `periodicity_null.csv` | Conditional shuffle diagnostics for full history and latest complete window of each size, with raw and Bonferroni-adjusted Monte Carlo p-values |
| `temporal_analysis.json` | Configuration, cutoff, source/normalized CSV hashes, versions, timings, row counts, warnings, full number summaries and ACF/spectral arrays |
| `plots/number_NN_temporal.png` | Nine panels: appearances, gaps, yearly/monthly rates, rolling rates/score, full-history ACF/spectrum and regimes |

Blank CSV cells and JSON `null` mean unavailable measurements, not zero evidence.
The earliest and latest years are partial; their rates use actual draw counts.
Monthly ratios divide a number's month-specific rate by its overall rate. An
unobserved number or absent calendar month gives an unavailable ratio/rate.
The expected per-number appearance probability is 6/45. Yearly expected count is
eligible draws × 6/45; rate deviation is observed rate minus 6/45.

## Gaps and rolling boundaries

Appearance intervals count draws between hits (adjacent hits give 1). Current gap
counts absent draws after the latest hit (a hit at the endpoint gives 0).
The longest absence includes observed leading/trailing runs; a boundary flag
identifies when the longest observed run touches a censored boundary. That run
may continue outside the available data.

Within a calendar year or rolling window, completed-gap statistics use only
intervals whose two hits lie inside that context. Mean/median require one
completed interval; population standard deviation requires at least two. Fewer
than ten completed intervals are marked `unstable`. No completed intervals give
`insufficient`. This differs from the original whole-history utility, which
retains its existing population-std behavior for one interval.

A width-W endpoint-t window covers exactly draws t-W+1 through t. No padded or
partial windows are exported. If a number never appears in the window, its
current gap is unknown and `absence_lower_bound=W`; a prior hit outside the
window is deliberately not used. Completed gaps are boundary-truncated samples
and need not estimate the full-history gap distribution without bias.

## ACF, spectrum and score

Default guards are 20 observations, four appearances and four absences. Unsupported
sequences return an explicit status and null score. ACF maximum lag is further
capped by floor(n/3) and n−12. Each overlap side needs at least two appearances
and two absences. The demeaned biased estimator is:

```text
r(k) = sum_t [(x[t] - mean(x)) (x[t+k] - mean(x))]
       / sum_t [(x[t] - mean(x))^2]
```

Lag zero is never searched. The three strongest positive eligible lags are
reported. If all eligible correlations are nonpositive, the positive-strength
component is zero and the candidate lag is null. Lag 1 may describe persistence,
not a periodic cycle. The estimator attenuates longer lags.

The [SciPy periodogram](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.periodogram.html)
uses unit sampling frequency, a Hann window, constant detrending, one-sided
`spectrum` scaling and no zero padding. Search periods span 2 through n/3 draws
by default: at least three observable cycles. `--min-cycles` changes the guard
(minimum accepted value 2). Frequencies have finite resolution; neighboring bins
and harmonics are not independent cycles. Spectral power is not a probability.

Define A as the strongest positive ACF; S as the largest eligible spectral-bin
power divided by **all positive-frequency power**, including power excluded by
the long-period guard; G as `1/(1+CV_gap^2)` using population gap variability.

```text
periodicity_score = 0.4*A + 0.4*S + 0.2*G
```

All components lie in [0,1]. Missing components give a missing score, never an
optimistic partial score. Random binary histories can have a positive score;
especially, G has a positive random baseline. The weights are a first-pass
convention, not optimized. Scores across different window lengths have different
null distributions. This score is **not** a probability of future appearance.

## Regimes and recurrence

At each endpoint, compare the score with the same number/window's expanding
90th percentile of **earlier finite scores**, requiring at least 52 past valid
scores. Mark strictly greater values; ties do not qualify. Missing scores and
nonadjacent endpoints break a run. Require at least three consecutive qualifying
endpoints to record a regime.

`start_draw` and `end_draw` describe qualifying **window endpoints**. The earliest
underlying observation is `support_start_draw`. `confirmed_draw` is when the
minimum run length was known: a regime's earlier start is a retrospective label.
`open_at_cutoff` flags runs still qualifying at the available endpoint. The peak
lag and spectral period come from the highest-score endpoint, which can differ
from other endpoints in that regime. Regimes are not exact physical change points.

For recurrence, merge successive regimes whose underlying support windows
overlap. The exported `independent_episodes` column means these nonoverlapping
episodes; it does **not** assert statistical independence. Report both raw
regime-start intervals and episode-start intervals. A timing candidate requires:

1. At least four nonoverlapping episodes (three start intervals).
2. Episode interval coefficient of variation ≤0.25.
3. Episode representative spectral-period coefficient of variation ≤0.25.

Each episode's period is taken from its highest-score constituent regime. The
candidate interval is the mean episode-start gap. The other statuses distinguish
insufficient episodes from irregular timing/periods. Even a candidate is a
heuristic description, with no recurrence null test or significance claim.
Coalescing reduces obvious overlap artifacts but does not eliminate dependence.

## Null comparisons and false discovery

Shuffle each binary sequence while preserving its appearance count, then rerun
the complete score calculation, including the lag and spectral-bin searches.
For B shuffles and E scores at least as large as observed:

```text
p = (1 + E) / (B + 1)
```

This is a one-sided conditional Monte Carlo comparison of temporal order. It
does not test whether the appearance count itself is unusual. Plus-one adjustment
prevents zero p-values, consistent with the conservative randomized-test
convention described in [SciPy's permutation-test documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html).
Reports include null mean/95th quantile, exceedances, resolution and an approximate
Monte Carlo standard error. Small B gives coarse, noisy tail probabilities.

Tests concern predeclared fixed scopes: full history and the latest complete
26/52/104 windows. Bonferroni uses a planned family of 45 × 4 = 180, including
ineligible scopes conservatively. Inspection of one number uses the same family,
not a more favorable single-number correction. Custom window lists change this
family to 45 × (1 + number of listed windows).

The correction does **not** cover every rolling window, past peak, regime,
recurrence candidate, calendar contrast or alternative parameter setting. A
small fixed-scope p-value cannot validate a visually selected historical regime.
Null simulations across numbers preserve each marginal count; they are not
joint six-number draw simulations. Bonferroni does not require independent tests.

## Historical-data boundary

Raw rolling metrics, prior-score thresholds and high-score flags are prefix
invariant: appending/changing later draws cannot change earlier endpoints.
Window endpoint t includes draw t, so it can describe history before target t+1,
**not predict draw t**. Tests check this boundary and the original backtest tests
remain in place. Full calendar ratios, full-history null tests, completed regime
summaries and recurrence reports are explicitly retrospective. No exploration
artifact is passed to RandomModel or the backtest engine.

## Delivered run and observations

All-number run: draws 1–1245; seed 42; windows 26/52/104; default score and
regime settings; 4,999 shuffles per eligible fixed scope. Reports contain:

- 45 number summaries and 7,470 appearance events.
- 1,125 number-year, 540 number-month and 12,915 number-year-month rows.
- 160,020 trailing-window rows, 1,171 high-score regimes and 135 recurrence rows.
- 180 planned fixed-scope null comparisons: 155 eligible, 25 too sparse.
  Exactly 774,845 shuffles were completed.

Measured analysis time, excluding exports and plots: **502.8 seconds** (8.4
minutes), including 58.5 seconds for rolling/regime analysis and 439.6 seconds
for null simulations. Other inspection/testing processes ran concurrently, so
these wall-clock values are environment-specific. The default 199 simulations
reduces the simulation budget by about 25 times; rolling analysis cost remains.
The rolling CSV is approximately 35.6 MB. These settings are intentionally
configurable; fast tests use small fixtures and zero/9/19 shuffles.

Five fixed scopes had raw Monte Carlo p<0.05. **None** had Bonferroni-adjusted
p<0.05. The strongest raw result was number 8, latest 52 draws: score 0.447193,
13 of 4,999 shuffled scores at least as large, raw p=0.0028, adjusted p=0.504.
Thus the lowest single-scope p-value does not establish an unusual pattern after
the planned search across 180 scopes. This is not a proof of randomness or of
the absence of every possible pattern.

Three timing candidates passed the descriptive recurrence rules:

| Number | Window | Nonoverlapping episodes | Episode-start gaps | Mean candidate interval |
|---|---:|---:|---|---:|
| 8 | 104 | 4 | 294, 197, 235 | 242.00 draws |
| 13 | 52 | 5 | 200, 295, 194, 178 | 216.75 draws |
| 34 | 52 | 5 | 190, 239, 256, 237 | 230.50 draws |

These were selected by a heuristic scan, with no recurrence null test. Number
34's spectral-period CV is 0.2452, close to the chosen 0.25 limit; its candidate
designation is sensitive to that convention. The other 132 number/window
combinations had irregular timing/periods (102) or insufficient episodes (30).

Numbers **7, 17 and 34** were chosen before observing results and inspected with
the same seed and 4,999 shuffles. Aggregate and individual null tables agree
exactly. Their [plots](../reports/plots/) were rendered and visually reviewed.

- **7:** 21 detected regimes across the three window sizes; no timing candidate.
  Full-history conditional shuffle p=0.6272.
- **17:** 36 regimes, with changing dominant periods rather than stable timing.
  For example, the 104-draw regimes at endpoints 1051–1076 and 1124–1147 have
  peak spectral periods near 2.12 and 8.0 draws respectively. No timing candidate;
  full-history shuffle p=0.1462.
- **34:** 23 regimes and the 52-draw timing candidate above. Its latest 26-draw
  score is visually elevated (0.4151), but raw conditional shuffle p=0.09 and
  adjusted p=1.0; full-history p=0.6740.

All eligible fixed-scope adjusted p-values for these three numbers were 1.0.
Repeated high-score bands are visually interesting, but neither these examples
nor the aggregate results establish predictive power or statistically established
recurring regimes.

Sparse-window coverage also matters: only 25,625 of 54,900 width-26 windows had
supported scores, compared with 49,487/53,730 width-52 and 51,383/51,390 width-104.
Missing segments must not be interpreted as low-periodicity regimes.

Verification: **69 tests passed**, including all original 47. New tests cover
calendar denominators, supported lags/periods, missing-data statuses, null seeds,
rolling/past-threshold invariance, regime overlap and recurrence guards, exports,
PNG generation and CLI path safety. Canonical CSV SHA256 is unchanged:
`b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e`.
No advanced predictive models, commits or pushes were introduced.
