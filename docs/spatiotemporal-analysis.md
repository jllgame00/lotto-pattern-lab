# Phase 6: draw-number translations

This is an exploratory test of an ordered-label hypothesis. Lottery labels may
have no meaningful spatial relation. A diagonal that looks convincing is not
evidence of a mechanism, and a fitted score is not an appearance probability.

## Data boundary and artifacts

The matrix has 1,245 rows and 45 columns, exactly six main-number ones per row.
It uses draws1–1245. Bonus numbers are excluded. The bounded source reader
rejects an unknown suffix without parsing it. No result for1246 or later is
retrieved. Draw1245 is authorized historical data here, not a pristine holdout.
Old research commands retain their old cutoffs.

The Phase5 snapshot and registry remain byte-for-byte unchanged. The Phase6
freeze is separately namespaced in `reports/prospective/phase6/`, with a distinct
experiment ID, persistent reservation, exclusive file creation, SHA-256 record,
and its own append-only registry. Re-running `freeze-2d` refuses regeneration.
The source code is embedded and hashed because the working tree is uncommitted.

## Search definitions

For each dt1..52 and dn-15..15, only source cells whose destinations are inside
the rectangle are eligible. `valid_opportunities` counts observed ones at those
source cells, `observed_matches` counts observed translated pairs, and
`match_rate=matches/opportunities`. Its IID reference is p=6/45. `overlap_area`
counts all geometrically eligible cells, and `joint_rate=matches/area` has IID
reference p². Undefined conditional rates are NaN when no source exists.
`raw_z=(matches-opportunities*p)/sqrt(opportunities*p*(1-p))` is only a search
statistic: overlapping pairs and random denominators invalidate a naive local
normal significance interpretation. dn0 is exported as a reference, excluded
from translational maxima. Positive-time overlap is the nonredundant half of
2D autocorrelation; negative-time shifts are equivalent to opposite number
displacements. Same-draw/zero-displacement peaks are excluded.

Directional asymmetry compares positive and negative conditional rates using
their respective opportunity counts. Its simplified variance is calibrated by
the same surrogate maximum procedure, not used as a standalone significance test.

Chain counts search lengths3,4,5 across the same translations. The null expected
count is `(T-(L-1)*dt)*(45-(L-1)*abs(dn))*p**L`. The count z-score is descriptive.
`maximal_chains.csv` reports runs with no observed predecessor, their complete
length, geometric forward maximum, endpoints, and score `-L*log(p)` (not a
search-adjusted surprise). Nested shorter chains contribute to count statistics;
they are not reported as independent discoveries. Chains on distinct slopes may
still share points. A separate maximum-longest-chain statistic addresses runs
longer than5. The score does not reward a geometric impossibility.

The Hough search scans primitive slopes dt1..12 and dn±1..6, all intercepts
`dt*number_index-dn*draw_index`, minimum12 eligible lattice positions. It reports
support, eligible length, density, endpoints and a binomial-reference z-score.
Primitive directions avoid duplicate parameterizations of the same line. Every
line is searched; only the highest50 are exported. Retaining only the best line
per slope in surrogate output does not change the global maximum searched.

The 2D FFT uses row/column centering, Hann tapering on both axes, and nonzero
temporal and number frequencies. Power is normalized over the nonredundant
positive-time frequency half-plane. The largest normalized power is a sixth
complete-search statistic. Finite45-number boundaries, fixed six-per-row totals,
tapering, and discrete axes prevent interpreting a Fourier peak as a physical
or predictive cycle. FFT output is not used in either predictor.

## Nulls and search correction

199 seeded IID Lotto histories and199 independently initialized curveball
surrogates each undergo ALL the same searches. Curveball performs20*T random
row-pair trades, preserving exact row and column sums. Finite mixing is an
explicit limitation; exact margins do not imply exact uniform sampling from all
possible fixed-margin matrices. Changed-cell fractions are exported.

For each statistic, `global_p=(1+# null maxima >= real maximum)/(199+1)`.
The six searched statistics are shift, absolute direction, chain-count score,
longest chain, Hough score, and spectral concentration. Bonferroni across these
six gives `family_adjusted_p`. Require consistency under BOTH null families.
The minimum global p resolution is.005 and adjusted resolution.03; these are
Monte Carlo estimates, not exact analytic p-values. No local/raw score establishes
significance. Full surrogate maxima are retained for reproducible inspection.

## Predictors and evaluation

TranslationModel fits on the expanding prefix, estimates conditional overlap
with100 IID prior opportunities, and retains20 largest positive excess rates.
At targetT it looks at T-dt only, adds support to source_number+dn, and divides
by the sum of rule weights whose sources are geometrically valid for that
candidate. No wrapping occurs. Its ranking score is `p+(1-p)*support_fraction`.

ChainModel learns the probability of a third point given two prior collinear
points, with the same shrinkage. Scoring requires both predecessors at T-dt
and T-2dt. The score has the same bounded support definition. A pair on an
arbitrary slope is insufficient unless that slope acquired positive training
support. Neither model consumes full-history search reports or target outcomes.

Combined2D averages percentile ranks of the two models with fixed equal weights;
ties receive average ranks before combination, then smaller number breaks final
score ties. It is a predeclared experimental ablation, not an optimized winner.
The development401–900 average was.854 versus Translation.842 and Chain.766,
which provides a limited descriptive reason to retain this combination for the
separate freeze; it is not evidence of reliable superiority.

Walk-forward targets401–1245, fit cadence26; primary models are also rerun with
cadence13. Every score uses current history ending atT-1, while learned rules
and Logistic scaling remain fixed between fits. Gap Logistic uses the unchanged
six gap columns and existing fit/scoring implementation; a compatibility test
checks equality. RandomModel preserves the prior target-specific seed protocol.
The declared development period ends900, followed by later901–1245. Earlier
phases already used this historical period, so it is not a pristine holdout.

Start401/501/601/701/801/901 reports are nested slices of the same run, keeping
predictions and refit schedule fixed. Early/middle/recent blocks and the separate
cadence13 refit run diagnose instability. Direction and lag ablations use positive,
negative, short1–13, and longer14–52 shifts separately for both model families.

Average-hit differences and pool threshold/mean differences use2000 paired
26-draw circular block bootstrap replicates. These intervals are not corrected
for the many model/window/pool comparisons. Marginal Clopper–Pearson intervals
are independent-indicator diagnostic intervals only. A degenerate all-zero
bootstrap interval cannot rule out a rare event; exact hypergeometric rates and
marginal upper bounds remain essential. Rare pool events are distinct from
ticket prizes and from average ranking improvement.

## Files and commands

`python main.py analyze-2d --surrogates 199` writes shift, directional, maximal
chain, chain-count, Hough, spectral, rolling/era stability, and full null reports.
`python main.py compare-2d` writes audit predictions, ranking/pool comparisons,
development-only reports, time blocks, and individual5+ pool events.
`python main.py compare-2d --cadence 13 --primary-only` is the sensitivity run.
`python main.py freeze-2d` freezes three independent tracks with full rankings,
scores, Top6/8/10/12/15, direct Top6, and seeded weighted/coverage portfolios
of1/5/10/20 tickets. Budgets use prefixes of the same20-ticket generation, with
no portfolio search. Exact tickets are in the JSON and human-readable manifest.

All reports are under `reports/spatiotemporal/`, plots in its `plots/` subfolder.
`plot_matrix(x,path,start=...,end=...)` supports arbitrary allowed draw ranges.
`verify_2d(snapshot)` checks hashes, registry pointers and frozen structure without
loading a target result. Phase5's evaluator is not repurposed to evaluate Phase6.
