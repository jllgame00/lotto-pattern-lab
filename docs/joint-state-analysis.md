# Phase9 categorical interaction methods

The hypothesis is that HIGH gap AND HOT frequency may reveal a translation
diluted within either parent state. This is exploratory; higher dimensionality
increases false-discovery risk. Only nine categorical states are added, without
continuous4D displacement vectors, arbitrary state sequences or neural networks.
The [predeclared protocol](superpowers/plans/2026-10-17-phase9.md) fixes all choices.

## Timing and support

For target t, gap=t-1-last_appearance_draw; W26 count sums t-26..t-1. Missing
previous appearance or fewer than26 completed draws makes the joint state
missing(-1). Gap and frequency thresholds each use training-prestate1/3,2/3
quantiles, higher convention, boundary ties lower; thresholds stay frozen between
fits. Joint id=3*g+f, with LOW/MID/HIGH and COLD/NEUTRAL/HOT indexed0..2.

The sparse target/number table includes both causal state values, categories,
feature cutoff and main-number target label; bonus is excluded. The support
audit includes all9 cells, even zeros. Percentages use ALL number-states/main
winning points, including missing cases in their denominator. Displacement
opportunities overlap across shifts; summed opportunities are not independent.

Minimum100 pair opportunities and20 chain opportunities were declared before
examining support or scores. Empty/sparse bins remain explicit and are never
merged to obtain attractive rates. All rates shrink toward6/45 with100 prior
observations. The propensity baseline also requires100 number-state exposures.

## Interaction and complete search

Pair shifts are dt1..52,dn-15..15, including0 as a fixed-number reference.
Predictive rules and translational leader summaries exclude0. Opportunities are
observed source points with destinations inside the finite rectangle; no wrap.
Raw z=(matches-n*p)/sqrt(n*p*(1-p)), p=6/45. Marginal Wilson intervals ignore
dependence/selection and are not corrected evidence.

Parents pool disjoint joint cells from the SAME source population where both
dimensions are known. Gap pools three frequency cells, frequency pools three
gap cells, unconditional pools all9. All use identical geometric boundaries.
This avoids missing-history artifacts. Historical parent models separately retain
their earlier defaults; these descriptive controls are matched-population rates.

Interaction lift=joint_shrunk/max(gap_shrunk,frequency_shrunk)-1. Export all raw/
shrunken rates, source/opportunity/match counts and the absolute rate difference.
Positive lift exceeds BOTH parents. This is an interpretable contrast, not a
causal effect, additive-model interaction test or calibrated future probability.

Same-joint-state chains use dt1..13,dn+/-1..6. Length3/4/5 continuation requires
L-1 observed predecessors and final compatible PRE-state, not the final outcome.
The longest path is calibrated separately over all geometric lengths3+.
Maximal paths suppress nested fragments; different rules may still overlap.

14,508 pair tuples and23,400 chain rule/length tuples give37,908 unique parameter
tuples. Testing conditional and interaction statistics on the same pair tuples
gives52,416 parameter/statistic cells. The4,212 length3/4/5 tuples are a subset,
not an additional search. The11,284 supporting parent aggregates are not separately
maximized. There are574,565,004 geometric chain start candidates before pruning.

199 IID six-of45 histories and199 exact-margin histories (20*T curveball trades),
seed90042, each recompute BOTH causal features and refit BOTH encoders. Each runs
the SAME complete search. Finite constrained mixing is approximate. Four global
families are conditional z, positive interaction lift, chain continuation z and
longest chain. Empirical p=(1+exceedances)/(B+1), Bonferroni4 within each null;
evidence must survive both. Seeds, thresholds, counts and maxima are retained.
Raw resolution0.005; adjusted resolution0.020. Local values never override this.

## Models, development and evaluation

JointStateTranslationModel retains20 positive shrunken joint excesses above p,
requiring100 opportunities. It learns every rule from the current training prefix;
descriptive full-history leaders are not predictor inputs. It does not hard-filter
to positive interaction lift; diagnostics identify inherited parent effects.

JointStateChainModel requires two observed predecessors in the SAME joint state,
minimum20 opportunities, prior100/top20. Candidate state is unconstrained, unlike
the full descriptive path. Diagnostics compute broader same-gap/same-frequency
chain controls allowing the other dimension to vary. Phase7 gap chains condition
only their latest source, so model ablations do not isolate every filter change.
Both models use the existing p+(1-p)*weighted active-rule fraction and strict
number boundaries. Scores are support, not calibrated appearance probabilities.

JointStateFrequencyBaseline pools causal number-state exposures and appearance
labels by joint cell. It scores the current candidate state with
(positives+100*p)/(observations+100), or p if sparse/missing. This tests propensity
without geometry. Exposures within a draw are dependent; the estimate does not
establish non-randomness. Baseline-versus-geometry comparisons are exported.

All configurations are fixed before inspecting outcomes and saved before
evaluation, then checked unchanged. Development401..900, later901..1245; no
outcome-based tuning or combination selection. Later historical data is not a
pristine holdout after earlier phases. Targets401..1245, expanding fits, cadence26
and sensitivity13, seed42. Multiple starts are nested slices retaining the same
refit calendar. Parent and Random/GapLogistic defaults remain unchanged.

Paired circular26-draw block bootstrap2000 seed42 compares each new model with
Random and matching2D/gap3D/frequency3D parents. Geometric models also compare
with joint propensity. Hits, rank, recalls and pools are exported with exact
hypergeometric references. Intervals are exploratory, not model-search corrected;
rare-event zero bounds can degenerate and do not establish impossibility.

## Immutable prospective publication

Exactly three independent models are frozen under reports/prospective/phase9/;
no combined model is justified by a point estimate. Preserve all45 scores/ranks/
ties, Top6/8/10/12/15, directTop6 and Top12 weighted/coverage unique nested
1/5/10/20 portfolios, seed42. Archive encoder/rules/parent controls, baseline
sufficient statistics/current states, sources, configuration, environment/Git,
dataset and earlier-file hashes. Baseline scores must match archived posteriors.

Publication validates/renders before reserving, creates files exclusively and
refuses regeneration. It writes only its own registry and checks all20 earlier
files before and after. No future result is retrieved, searched for, inspected,
imported or evaluated. No commit or push is performed.
