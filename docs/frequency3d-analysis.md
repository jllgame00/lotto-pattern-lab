# Phase8 methods: recent-frequency-conditioned translations

Frequency replaces gap as the third state dimension. They are different summaries:
two numbers with gap2 can have different counts of appearances before their latest
occurrence. This phase asks whether source COLD/NEUTRAL/HOT frequency state
conditions a draw/number translation. It is exploratory. Gap is used only by the
unchanged, separately evaluated historical baseline models. It is never an input
to a frequency-conditioned predictor. No4D model, neural network, or additional
state family is implemented.

## Causal states and missing observations

For target t, W is exactly10,26,52. Count uses draws t-W through t-1, inclusive;
rate=count/W. State t is unchanged when outcome t is altered. Earlier than W
completed draws, both count and rate are missing, encoded-1 and excluded from
conditioned source searches. Partial windows are not divided by W.

The prior number rate is appearances in all completed draws before t divided by
t-1. Relative frequency is recent_rate/prior_rate; zero prior rate makes the
relative state missing. It is not replaced with zero or infinity. Zero recent
count with a positive prior denominator is a legitimate cold observation.
The feature table includes deviations from6/45 and from the prior historical
rate. Bonus numbers are excluded. The labeled table uses target_draw t and
feature_cutoff t-1; appeared_next denotes appearance in that explicitly named
target. There is no dense cube or actual future target label.

Count0..W and normalized rate0..1 are bijective within a window. Both are exposed
and exported, but their identical partitions are searched once under `count`.
Quantile states fit training-prestate1/3 and2/3 count quantiles using `higher`;
edge ties go to the lower bin. Unequal supports or an empty bin caused by ties
are retained, not repaired by threshold optimization. Relative bins have fixed
boundaries0.5 and1.5. Full-history descriptive bins never enter historical
predictions; each model has its own training-prefix encoder, frozen between fits.

## Complete descriptive search

Conditional pairs use dt1..52 and dn-15..15, including zero as a fixed-number
reference. Translational leader summaries and predictive rules exclude zero.
Every opportunity is an observed winning source in a supported causal state
with destination inside the finite draw/number rectangle. No number wrapping.
Rate=matches/opportunities; baseline6/45; lift=rate/(6/45). Minimum100 source
opportunities. Sparse rows are exported but cannot win supported maxima.

Raw z=(matches-n*p)/sqrt(n*p*(1-p)). Wilson intervals are marginal diagnostics
that ignore dependence and selection. They are not corrected significance tests.

Directional pairs normalize positive and negative displacement separately using
their own geometric opportunity counts. The raw contrast divides rate difference
by sqrt(p*(1-p)*(1/n_positive+1/n_negative)); both directions must have support100.
The coarse HOT-minus-COLD interaction subtracts these directional rate differences
and sums their reference variances. Overlap and dependence invalidate a simple
normal p-value, so absolute contrast maxima are calibrated against full null runs.

True count-displacement search uses dt1..13,dn±1..6,delta_count-1..1. Destination
pre-count relationships are DESCRIPTIVE_ONLY. Predictors do not consume those
tables or conditions. Same-state trajectories use coarse bins; count trajectories
use the same bounded repeated count increments. There is no arbitrary categorical
state progression. Tested geometric arithmetic is reused from Phase7, with
frequency-count arrays; no gap history is computed by that search.

Continuation counts for lengths3/4/5 require the previous L-1 observed points and
the final pre-state condition, but not the final outcome. Minimum20 opportunities.
The longest path is separately calibrated, including all geometrically possible
lengths beyond5. Exported paths are maximal under their rule: nested fragments
are suppressed and counted. Different parameterizations can still overlap, and
neither configurations nor paths are asserted independent. Search counts include
all parameter tuples and geometric rule/length/start-position candidates before
data-driven pruning. Optional3D Hough search is deferred: the added sparse
intercept family offers little interpretability beyond these declared tests.

## Nulls and multiplicity

Every one of199 IID histories has exactly six unique uniform numbers per draw.
Every one of199 constrained histories preserves both row sums and number totals,
using20*T curveball trades. Finite mixing is approximate; exact margins do not
establish uniform sampling of every possible fixed-margin history. Seed80042
generates explicit independent child seeds retained in reports.

For each surrogate, recompute all W10/26/52 causal frequency histories, prior
number rates and quantile boundaries. Run the SAME complete search. Real states
are never attached to randomized points. Five statistic families pool ALL
windows/representations: conditional overlap, directional contrast, true count
displacement, trajectory continuation, longest trajectory.

`p_global=(1+count(null_max>=real_max))/(199+1)`. Bonferroni5 is applied across
the major families within each null; evidence must survive both nulls. The raw
Monte Carlo resolution is0.005; adjusted resolution0.025. Per-window maxima are
stored as diagnostic detail, never used to sidestep all-window correction.
The Phase6-selected(+42,-5) follow-up gets matching per-window/state local null
comparisons. Those are not independently preregistered evidence and do not
override the complete conditional search correction.

## Predictors and evaluation

FrequencyConditionedTranslationModel learns positive source-state translation
excesses, requiring100 training opportunities. FrequencyConditionedChainModel
requires two observed predecessors with the SAME pre-frequency state and20
training opportunities; it does not condition on the candidate destination state.
Both shrink with100 prior opportunities at6/45, retain20 positive excess rules,
and use dt1..52,dn±1..15. All rules, encoders and scaling are training-only.
At scoring, only the unchanged fitted prefix plus completed later observations
before the target are accepted. Scores are weighted rule support, not calibrated
appearance probabilities. Diagnostics expose source draw/number/count/state,
training opportunities and per-rule contribution. Exact score ties use smaller
number first.

The direct ablation preserves earlier model defaults. Phase8 chains require both
predecessor states to match, while the Phase7 gap chain conditions its most recent
source only. New models also impose sparse-support filtering. Thus this compares
the declared complete models; it does not mathematically isolate state choice
from every other eligibility difference.

W26 was predeclared as the primary prospective hypothesis before inspecting any
Phase8 result. W10 andW52 are independent fixed ablations. No representation,
threshold or window is selected using draw1246 or the complete evaluation period.
An explicitly development-only selector maximizes mean Top6 hits on401..900,
ties26 then10 then52; its later performance is exported separately. It does not
replace the two predeclared prospective tracks or create an ensemble.

Historical evaluation uses identical targets401..1245, expanding training,
cadence26 and sensitivity13, seed42. Unchanged Random, Gap Logistic,2D parents and
gap3D models share the exact target draws. Multiple starts401/501/601/701/801/901
are nested slices preserving the original refit schedule. The later901..1245
period is later than development but is not pristine after earlier phases.
Results are not characterized as untouched prospective evidence.

Paired circular26-draw block bootstrap intervals use2000 replicates and shared
seed42 versusRandom, matching2D parent and matching gap3D model. Metrics cover
hits, winning-number rank, recalls and candidate pools. Intervals are exploratory,
not multiple-model corrected. Degenerate zero-event bootstrap intervals cannot
establish an event is impossible. Legacy comparison exports keep their existing
bootstrap streams; common-seed parent comparisons have their own explicit file.
Exact hypergeometric pool expectations and full0..6 distributions are exported.
Pool concentration and actual six-number ticket prize outcomes remain distinct.

## Isolated prospective publication

Only two predeclared W26 models are frozen under reports/prospective/phase8/.
No Phase8 combination is justified merely by an attractive historical estimate.
The snapshot archives45 scores/ranks, Top6/8/10/12/15, exact ties, directTop6,
Top12 weighted/coverage portfolios, seed42 and unique nested1/5/10/20 budgets.
It also includes encoder/rules, model/source versions, source hashes, protocol,
environment, currentGit state, dataset hash/cutoff and prior-artifact hashes.

Publication checks all15 earlier files before and after writing only its own
directory and registry. It prevalidates and renders before reserving an ID, uses
exclusive creation, and refuses regeneration. Snapshot/manifest integrity is
recorded separately. Validation is tied to the versioned contract rather than
future mutable model defaults. No command fetches or evaluates a future result.
