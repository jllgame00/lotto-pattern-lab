# Phase 2 exploratory temporal analysis

Implement the user's detailed phase 2 scope without predictive models or changes
to backtest isolation. Existing dataset and 47 baseline tests are the starting
point. No commits/pushes. Work in the requested existing repository.

Modules: periodicity.py (ACF, spectrum, score, conditional shuffle comparison),
temporal.py (calendar and trailing-window tables), regimes.py (causal thresholds,
contiguous regimes and exploratory timing recurrence), exploration.py (report
orchestration), plots.py (nine panels). Extend descriptive history and CLI.

All primary analysis excludes bonus. Use every available appearance; absent or
unsupported measurements are null with status fields, never fabricated zeros.
Year/month tables normalize by eligible draws; calendar summaries are explicitly
retrospective. Trailing-window values at endpoint t use only observations <=t.
Prediction for t+1 may consume such a prefix, never full-history exports.

Default periodicity guards: >=20 observations, >=4 appearances and >=4 absences,
>=3 cycles, ACF overlap >=12 and >=2 of each binary class on each overlap side.
Max ACF lag 52, further limited by floor(n/3) and overlap constraints. Lag zero
is excluded. Use demeaned biased ACF with denominator sum(x-mean(x))^2.
Use SciPy's Hann-window, constant-detrended, one-sided periodogram, no padding.
Periods must be >=2 and <=n/3. Spectral concentration is the strongest eligible
bin's power divided by ALL positive-frequency power (including excluded long
periods). This avoids inflating concentration by dropping unsupported power.

Score = 0.4 * max(0, eligible ACF peak) + 0.4 * spectral concentration
      + 0.2 / (1 + population_gap_CV^2).
Score is null if the sequence/component guards fail. It is in [0,1], a heuristic
description, not an appearance probability, calibrated significance or predictor.
Gap stability has a positive random baseline; shuffle comparisons reflect it.

Regime thresholds: prior-only expanding 90th percentile, >=52 valid past scores;
strictly above threshold, >=3 consecutive endpoints. Record confirmation draw,
window support start, endpoint dates, peak lag/period and open-at-cutoff status.
The regime label describes window endpoints, not an exact physical change point.
Recurrence coalesces regimes whose supporting windows overlap, needs >=4 resulting
episodes, interval CV <=0.25 and peak-period CV <=0.25 before emitting a timing
candidate. No recurrence statistical test or significance claim is implied.

Null comparison: condition on observed appearance count and shuffle positions;
repeat the entire score calculation (including lag/frequency scans). Plus-one
upper-tail Monte Carlo p=(1+exceedances)/(B+1), seed required/default42. Default
B=199, configurable including 0 to skip. Evaluate fixed full-history and latest
26/52/104 scopes, not selected peaks. Bonferroni family=45*(1+number of window
sizes); no correction claim for all rolling windows, regimes or chosen settings.
Report Monte Carlo uncertainty/resolution and scope-specific limitations.

CLI inspect accepts any number and produces a nine-panel PNG plus supporting
CSV/JSONs; --no-plots supports quick/tests. analyze-all exports all 45 numbers,
calendar tables, rolling tables, regimes, recurrence and fixed-scope null tables.
Output path guards preserve canonical data/provenance. Include dataset/config
fingerprints, cutoffs, timings and library versions. At least numbers 7,17,34
are inspected, chosen before looking at results.
