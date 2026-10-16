# Phase7: causal gap-conditioned translations

This phase adds exactly one state variable: CURRENT GAP. No recent frequency,
calendar, periodicity, HMM state, other third dimension, or4D predictor is added.
The premise that pooling different states can hide a translation is a hypothesis,
not evidence. Phase5/6 predictions remain immutable, and no future result is accessed.

## Timing and state representation

For target draw t, `gap=t-1-last_appearance_draw`, using draws strictly before t.
Last appearance100 implies gap3 for target104. If the number appears in104, that
only resets the state for105. Never-seen numbers have NaN gap and encoded state-1;
their first winning occurrences are excluded from conditioned searches. Relative
gap additionally needs two prior appearances to define a completed historical
mean interval. The mean is `(last-first)/(appearances-1)` using prior appearances.

`causal_states(X)` returns arrays for target states1..T+1. `state_table` exports
only labeled historical targets1..T, with `feature_cutoff=target_draw-1` and
`appeared_next` denoting appearance in that explicitly named target draw. There
is no dense3D cube. The existing binary draw×number matrix is retained unchanged.

The encoder fits training pre-states only:

- Exact/clipped: integer gap capped at `min(26,ceil(training95th percentile))`.
- Quantile: low/medium/high from training1/3 and2/3 quantiles, observation-based
  `higher` convention. Boundary ties remain in the lower bin; empty bins remain
  explicit and cannot acquire support by merging or retuning.
- Relative: gap/causal historical mean interval, fixed bins `<=.5`, `(.5,1.5]`,
  `>1.5`. Undefined means remain missing.

Predictive encoders are refitted only at training cutoffs, then held fixed
between fits. Descriptive full-history bins are not reused in earlier forecasts.
All real data pre-states give cap21 and coarse bins0–2,3–7,8+; these are descriptive
values, not universal predictor constants.

## Searches and denominators

Conditional pair search scans dt1..52 and dn±1..15 for all three state encodings.
Zero number displacement is excluded by the predeclared translational scope;
fixed-number temporal behavior belongs to the earlier H1/H2 research.
An eligible opportunity is an observed source point with matching PRE-source gap
and a destination inside the finite rectangle. Rate=matching destination ones /
opportunities. No number wrapping. Minimum100 opportunities; sparse rows are
exported but excluded from search maxima and predictive selection.

The raw statistic is `(matches-n*p)/sqrt(n*p*(1-p))`, p=6/45. Marginal Wilson
intervals ignore dependence and selection. Neither is a significance test after
searching. Geometric opportunity counts and full-search surrogate maxima address
the boundary and multiple-search issues respectively.

Destination analysis scans all3×3 coarse source/destination bin combinations
over the same shifts. Destination pre-gap is known just before its own draw but
not necessarily at the earlier source time. These tables are DESCRIPTIVE_ONLY;
predictive models never use them. The true3D family scans dt1..13,dn±1..6 and
clipped pre-gap difference-3..3 with minimum100 opportunities, also descriptive.
Clipped-gap displacements are not raw-gap displacements in the saturated tail.

Trajectories use the smaller shift grid and either one constant coarse state or
a repeated clipped-gap difference-3..3. For lengths3/4/5, continuation opportunities
require the previous L-1 observed points to obey the rule and the final pre-draw
state to be eligible. They do not require the final outcome. Minimum20 such
opportunities for a continuation z statistic. The longest trajectory is separately
calibrated without that support filter, including lengths beyond5 where geometric
bounds permit. This prevents simply ignoring an unusually long rare path.

Only maximal paths (no observed compatible predecessor) are exported, including
raw and clipped starting gap, geometric maximum, endpoints, and suppressed nested
fragment counts. Distinct parameterizations may still share points; no independence
is asserted. Configuration counts include both rule/length tuples and all possible
rule/length/start-position tests. Data-driven early pruning does not reduce the
effective search space. A3D Hough intercept search is deliberately deferred: the
optional extra family would expand a sparse search without a clearer hypothesis.

## Surrogates and evidence

Each of199 IID and199 constrained histories undergoes the SAME search, including
recomputed causal gap arrays and refitted cap/bin boundaries. Fixed-margin nulls
perform20*T independent curveball trades, preserving six points per row and exact
per-number totals. Finite mixing is approximate; exact margins do not prove exact
uniform sampling of all constrained histories. The null does not attach real gap
states to shuffled points.

Five maximum families: conditional source state (all representations together),
destination states, true3D displacement, trajectory continuation, longest trajectory.
`p_global=(1+count(null_max>=real_max))/(B+1)`; Bonferroni across5 families is then
applied separately for both nulls. Any evidence must survive both. For199 replicates,
the raw resolution is.005, adjusted resolution.025. Configuration counts may vary
slightly by surrogate because the clipping cap is learned by the same fixed recipe;
those counts and seeds are retained.

The(+42,-5) conditional follow-up was chosen from Phase6 data. Local null comparisons
by coarse state are exported, but are NOT independent preregistered evidence. The
same rule is already included in the corrected global conditional search.

## Predictive protocol and interpretation

The predeclared primary models use coarse source-gap bins. Pair and chain rules
require minimum100 and20 training opportunities respectively, shrink with100 prior
opportunities at6/45, and retain20 strongest positive excess rates. Chain prediction
requires two observed predecessors and conditions on the most recent source's
PRE-draw gap. Destination conditions and descriptive full-history discoveries are
not predictor inputs. Ranking support is not a calibrated appearance probability.

Both new models are compared with their unchanged Phase6 parents, unchanged Gap
Logistic and the identical seeded Random baseline on targets401–1245, cadence26;
primary sensitivity cadence13. Development ends900. The later901–1245 period is
later in this protocol, not a pristine historical holdout after earlier phases.
Starts401/501/601/701/801/901 slice one run and preserve its refit calendar. All
three state representations are fixed ablations; no winner is selected on evaluation.
New models also impose the requested sparse-support safeguards. Parent defaults
are preserved, so this comparison measures the complete conditioned model change,
not a mathematical isolation of conditioning from minimum-support filtering.

Paired26-draw circular block bootstrap intervals use2000 replicates, versus both
Random and the matching2D parent, for hits, ranks, recall and pool coverage. Higher
winning-number rank is worse; lower is better. Intervals are exploratory and not
multiplicity-corrected. Degenerate bootstrap intervals for zero rare events do not
exclude future events. Pool containment is distinct from ticket prize events.

Only the two predeclared coarse-bin models are prospectively frozen. No ensemble
is selected. Separate `reports/prospective/phase7/` files contain all scores/ranks,
Top6/8/10/12/15, directTop6, deterministic weighted/coverage Top12 portfolios with
nested1/5/10/20 budgets, configurations, encoder boundaries, fitted rules, source
code, environment and integrity hashes. Original Phase5/6 hashes are recorded and
verified before and after publication. No target result is fetched or evaluated.
