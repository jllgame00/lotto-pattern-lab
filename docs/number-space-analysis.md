# Phase10 number-space methods

This is a representation hypothesis, not an extra continuous state dimension.
Numerical adjacency of lottery labels need not have a physical or causal meaning.
The [predeclared protocol](superpowers/plans/2026-10-17-phase10.md) fixes all
windows, widths, kernels, search families, selection and ticket rules.

## Causal finite-axis signals

For target T, activity uses only completed draws<T. Full windows10/26/52 are
required. Each row has exactly6 unique main numbers, bonus excluded. Ranges of
width3/5/7/9 have43/41/39/37 valid starts respectively; neither number axis nor
time axis wraps. Every range table preserves its last included draw and next
target index. That index may be1246 without reading or labeling its result.

Range density=count/(W*width), expected p=6/45. Per-draw range count has
hypergeometric variance6*(width/45)*(1-width/45)*39/44, multiplied by W.
The raw z-score is descriptive, not a local significance claim.

Primary kernels: none[1], triangular1[.5,1,.5], triangular2[.25,.5,1,.5,.25],
Gaussian2[exp(-2),exp(-.5),1,exp(-.5),exp(-2)]. Descriptive box radii1..4 add
multiscale checks. Remaining weights are renormalized at the finite boundaries.
Neighbor-only removes the center BEFORE normalization; none has no neighbor-only
variant. For normalized weights a, smoothed mean variance under IID Lotto is
p*(1-p)*(45*sum(a*a)-1)/(44*W), accounting for negative same-draw covariance.
Constant input stays constant even at1/45. No45-to1 spillover is possible.

## Zones, motion and spacing

Top3 non-identical positive-z ranges are grouped when they overlap, transitively.
Three overlapping windows do not become three independent discoveries. Strongest
range ties favor the smaller start. Persistence is the longest identical-range
run. Movement is the longest same-direction nonzero center-step run with absolute
step<=4. Exact +/-1..4 repetitions, mean absolute movement and interval Jaccard
overlap are also reported. Rolling windows overlap heavily, mechanically creating
persistence; null histories use exactly the same overlap and tie convention.

Per draw, export sorted numbers, five ordered spacings, min/max/mean/median and
variance, consecutive pairs, range, mean point nearest-neighbor distance, small
gaps<=2, large gaps>=10, cluster counts at distance thresholds2/4 and five9-number
region counts. These17 metrics contain correlated/redundant summaries, not17
independent sources of evidence. Ordered spacing motifs form all positive5-tuples
whose sum<=44, a universe of C(44,5)=1,086,008; no arbitrary motif is preselected.

## Complete-search null correction

The complete search includes all valid rolling endpoints up to1245. At this
cutoff:584,000 range cells;2,463,750 number/kernel/signal cells;14,600 strongest-
zone endpoint records;144 aggregate zone/movement metrics;83,215 spacing-window
metric cells;1,086,008 possible motifs. The12 range,12 primary kernel and45
kernel/signal settings describe those same cells and are not extra tests.
These counts are computational opportunities, not independent hypotheses.

Six globally calibrated families: maximum range z, maximum neighborhood z,
strongest-zone persistence, directional movement, maximum absolute rolling
spacing/clustering z and maximum motif repeat count. Clustering windows are
1/10/26/52. Independent50,000 IID draws, seed1010 in50 deterministic batches,
provide reference metric means/SDs, not estimated from real history.

199 IID and199 fixed-margin curveball histories use seed100042. The latter
preserve exact row/column sums with20*T trades; finite mixing is approximate.
Every surrogate recomputes ALL counts, zones, smoothing and spacing and performs
the SAME search. Empirical p=(1+exceedances)/(B+1), Bonferroni6 within each null;
evidence must withstand both. Raw resolution0.005; adjusted resolution0.030.
Marginal/local z-values never override complete-search calibration.

## Models and development discipline

RangeDensityModel takes a selected W,width. Each interval rate shrinks toward p
using26 prior draws. Average positive excess over p across intervals containing
each candidate, then add p. Averaging overlap softens internal range boundaries
and adjusts edge membership counts. These are ranking supports, not calibrated
predictive probabilities.

NeighborhoodModel smooths causal recent rates using one frozen kernel. Candidate
configurations are3 windows x4 primary kernels; neighbor-only variants are
separate ablations. None is an explicit own-number control. GapNeighborhoodModel
rank-averages unchanged Gap Logistic and the selected neighborhood score using
one of gap weights .25/.5/.75. Equal scores receive average percentile rank.

Development draws401..900 alone select best mean Top6 hits, with ties retaining
the declared order. Selection is saved with SHA256 BEFORE later scoring. Cadence13
must reuse cadence26 selection without choosing again. Development data hash
guards accidental reuse with another prefix. Full401..1245 reports include
selection optimism and are exploratory; primary comparisons are901..1245.
That later segment is selection-excluded here but NOT a pristine holdout after
earlier research. Historical start slices preserve refit calendars from401.

All models get identical target sets. Existing Random/GapLogistic code remains
unchanged. Scores/rankings/cutoffs/seeds are audited. Paired circular26-draw
bootstrap2000, seed42, compares with Random, raw FrequencyW26 and Gap Logistic;
intervals are unadjusted exploratory intervals, not proof after model search.
Exact hypergeometric pool expectations and full0..6 distributions are exported.

## Equal-budget portfolios

Generate unique nested1/5/10/20 tickets, seed42+target, Top15 pool for model
methods. Compare rawFrequencyW26, Gap Logistic, selected neighborhood/range and
combination weighted tickets, range-aware coverage and uniform45 tickets.
Range coverage uses64 fixed weighted proposals per slot and lexicographic new
five-subset coverage, uncovered-zone representation, new-pair coverage and seeded
priority. Outside grouped zones is its own representation category. No2+2 quota,
target outcome or bonus enters construction. A target's actual/bonus is accessed
only after ALL portfolios exist; prizes1/2/3 are counted separately.

Uniform45 portfolios explore more distinct number coverage than Top15 portfolios;
this is intentional practical comparison at equal ticket budget. Exact uniform
portfolio laws do not apply to arbitrary overlapping range portfolios. Paired
uncertainty and rare-event marginal intervals accompany outcomes. A range-aware
prospective allocation is deferred unless historical robust superiority to both
uniform and its weighted control is demonstrated.

## Separate prospective publication

The publisher writes ONLY its own phase10 namespace/registry, never prior
experiments. Preserve three independently selected score tracks, full45 scores,
rank/ties/Top6/8/10/12/15, direct Top6, seed42 weighted/coverage Top12 portfolios.
Recompute scores from archived causal counts and frozen gap features/scaler/
coefficients during validation, then reproduce ranking/ticket consistency.
Selection/configuration/source/environment/dataset/prior-file hashes are archived.
Serialization and validation complete before permanent reservation. File creation
is exclusive and regeneration refused. All25 prior files are checked before and
after publication. No future result retrieval or evaluation occurs.
