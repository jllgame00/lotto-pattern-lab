# Predictive experiments

Historical Phase3 report. The subsequent fixed research seal now limits CLI
analysis to draws1..1244 and blocks canonical current prediction. See
[gap/prize research](gap-prize-research.md) for the active protocol and caveats.

These are exploratory chronological ranking experiments. A fitted score is not
evidence that Lotto can be predicted. There is no hyperparameter search, final
draw optimization, neural network, HMM, or web frontend.

## Run

```powershell
python main.py compare-models --ablations --tickets 20
python main.py predict-current --model logistic
python main.py explain-number 17 --neighbors 10
python -m pytest -q
```

Optional tree backends: `python -m pip install -r requirements-ml.txt` in an
environment with package access. If LightGBM cannot be installed, install
XGBoost explicitly; the adapter prefers LightGBM when both exist. The CLI
reports missing libraries in the console and experiment metadata, never as
zero performance or a substitute tree classifier. SciPy logistic regression
and similarity need only the existing core requirements.

During implementation scikit-learn, LightGBM and XGBoost were absent. Pip was
configured with no package index; an HTTPS probe to PyPI also failed with
WinError 10061. Environment restrictions were not disabled. Random Forest and
boosting adapters therefore cannot be evaluated here; their integration tests
skip explicitly. This is an outstanding validation limitation.

## Protocol fixed before results

104 draws of feature history; first supervised target 105. Evaluation starts
at draw 601 and ends at the penultimate canonical draw (1244 in this snapshot).
Draw 1245 is reserved from comparisons. Every 26 evaluation targets, refit on
all labeled opportunities with `target_draw < current_target`; reuse that fit
between retraining points while updating current features. CLI `--start`,
`--end`, `--cadence`, and `--seed` are explicit. No random row splitting.

At target 601, training labels end at 600 and current features end at 600.
Targets 602 through 626 retain the fit/scaler/neighbors through 600 while their
features update through their respective preceding draw. Target 627 refits
through 626. Every model receives the same features. No target outcomes are
passed to `score_rows`. The original stateless RandomModel engine is unchanged.

`predict-current` trains on all available labeled opportunities, including
the comparison-reserved draw, to describe the next scheduled draw. This does
not evaluate or tune against that next draw. Its default is fixed logistic
regression, not the winner of the historical comparison.

## Canonical features

`src.analysis.features.build_features` validates the source and returns one
row per target and number. Only main numbers are positive. Features are computed
before joining labels. Prefix invariance and target poisoning are regression
tested. No retrospective calendar tables or merged retrospective regimes enter
the feature dataset.

The default full set has 31 predictor columns: categorical number identity;
12 frequency features (counts and rates for 5/10/26/52/104, 10-to-104 rate ratio,
two immediately preceding appearances); six gap features (current gap,
ever-appeared flag, complete historical mean/median/population std, current/mean
ratio); eight periodicity/regime features; and four cyclic calendar features.
Count and rate pairs are intentionally exported and retained in the initial
fixed feature groups; they are redundant scaled representations, not independent
evidence. No interactions or hyperparameter search are added.

The periodicity features use only the trailing 104 draws and Phase 2 safeguards.
Unsupported metrics stay missing. A strong regime requires three consecutive
scores above the 90th percentile of at least 52 *earlier* supported scores.
Regime age begins at zero on the third qualifying endpoint, never on a
retroactively inferred start. Time since strong regime is missing until a
confirmed endpoint has occurred, zero during confirmed strong endpoints, then
counts subsequent draws. `strong_regime=0` means not confirmed, including when
there is insufficient history. These are causal descriptors, not recurrence
predictions.

Gap std requires at least two complete gaps. A never-observed number's current
gap is the observed absence lower bound, distinguished by `has_appeared=0`.
Missing values use training-only medians, or zero when the entire training
column is missing, then training-only population z-scores. Fixed categorical
number vocabulary 1..45 becomes 45 one-hot columns; no ordinal identity slope.
Month and ISO week use sine/cosine encodings; raw month/week remain in exports.

Metadata columns include target number/date, feature cutoff, month/week and
`appeared_next`. Selecting feature groups explicitly excludes labels and draw
IDs. The 31 raw predictor columns become 75 transformed columns in the full
model due to identity encoding. Calendar-only pooled scores tie for all 45
numbers on a target, so that ablation's deterministic tie break is a fixed
ticket, not a learnable per-number seasonal effect.

## Models

- Similarity: same number only; its own training medians/scales; 30 nearest
  prior labeled states by Euclidean distance. Configurable feature subset, K,
  Euclidean/Manhattan metric and uniform/distance weights. Distance weights
  `1/(1+d)` rescale to sum to the neighbor count; score is
  `(weighted appearances + 2)/(neighbor count + 15)` (fixed mean 6/45 prior).
  Neighbor target draw/date, state cutoff, distance and outcome are explainable.
  Frozen neighbors between refits deliberately omit newly observed outcomes.
- Pooled logistic: SciPy L-BFGS minimizes mean binary log loss plus
  `||w||²/(2*C*n)`, C=1, unpenalized intercept, no class weighting. Convergence
  failure raises instead of silently exporting scores. Standardized signed
  coefficients are exported, not interpreted as causal importance.
- Random Forest adapter: sklearn RandomForestClassifier, 100 trees, depth 4,
  minimum leaf 50, square-root feature sampling, one thread, fixed seed.
- Boosting adapter: LightGBM 100 trees, learning rate .03, 7 leaves, depth 3,
  minimum leaf 100, L2=1, one thread and deterministic settings. Explicit
  XGBoost fallback uses 100 trees, .03 rate, depth 3, minimum child weight 15,
  L2=1, histogram trees, one thread, fixed seed.

Tree importance is exported for every fitted cutoff when dependencies exist.
No SHAP or cross-number similarity variant is included.

## Evaluation and uncertainty

All 45 numbers are ranked. Top 6 ties use increasing number for predictive
models; RandomModel uses a seeded uniform ticket plus random ordering within
and outside that ticket. The baseline's uniform scores and sampled ranking
are both recorded; its ranking is not produced by a deterministic tie break.

Metrics: mean hits, 0..6 histogram, 3+/4+/5+ rates, best, mean winning rank,
Recall@6/10/15. Under uniform random selection the expected mean hits is 0.8,
mean winning rank 23, and Recall@k is k/45.

The optional weighted tickets are a separate stream: normalize nonnegative
scores, add a 0.1% uniform mixture to permit six selections even for sparse
scores, sample without replacement with explicit target/ticket seeds. They
never replace deterministic ranking metrics. Scores are not externally
calibrated probabilities; weighted sampling is not probability calibration.

Random reference simulations generate 2,000 runs of exact hypergeometric
ticket hits across the same target count. Target draws are paired against one
fixed empirical seeded RandomModel. Mean-hit and paired-difference intervals
use 2,000 circular moving-block bootstrap replicates with block length 26.
Early/middle/recent blocks are reported. Intervals are descriptive and not
familywise corrected; random-reference tails also have a Bonferroni column
across compared learned specifications. The random reference describes a
random policy, not a general test proving a learned policy's predictability.
Small differences or isolated favorable blocks are insufficient evidence.

All seven feature ablations use the same protocol and fixed logistic model.
`ablation_differences.csv` directly pairs frequency+gap+periodicity against
frequency+gap, including mean-hit bootstrap interval and ranking differences.
This is the predeclared incremental periodicity comparison; no best group is
selected for subsequent tuning or the latest draw.

## Artifacts

Default directory: `reports/prediction/` (override with `--reports-dir`).

- `features.csv`: full supervised table; `feature_sample.csv`: first 10 targets.
- `comparison.csv`: rankings and uncertainty; `time_blocks.csv`: temporal stability.
- `prediction_audit.csv`: per-model/target scores for 45 numbers, full ranking,
  top 6, actual main numbers, hits, feature cutoff, fit cutoff, seeds/config.
  `--no-audit` omits verbose scores/outcomes/config but retains target metrics.
- `feature_importance.csv`: fitted cutoff and signed coefficients/tree importance.
- `ablation_differences.csv`: paired incremental periodicity results.
- `experiment.json`: protocol, source hash, availability, package versions,
  dimensions, runtime, bootstrap and simulation settings, cautions.

Canonical data and provenance paths are protected against report overwrites.
Reports are local ignored generated artifacts. No commit or push is performed.

## Observed first experiment (2026-10-17)

Command: `python main.py compare-models --ablations --tickets 20`.
The source remained 1,245 draws, 2002-12-07 through 2026-10-10, SHA256
`b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e`.
The export has 51,345 supervised rows and 37 total columns (31 predictors).
All comparisons use 644 targets, draws 601..1244, 25 expanding fits per learned
specification. Draw 1245 is not evaluated. No configurations were tuned.

| Model/group | Mean hits | Recall@6 | Recall@10 | Recall@15 | Mean winning rank |
|---|---:|---:|---:|---:|---:|
| RandomModel | .798137 | .133023 | .224120 | .338768 | 22.933230 |
| Same-number similarity, full | .777950 | .129658 | .219462 | .329451 | 23.310300 |
| Logistic, frequency | .781056 | .130176 | .214803 | .330745 | 23.253623 |
| Logistic, gap | .849379 | .141563 | .228261 | .340839 | 22.754917 |
| Logistic, periodicity | .824534 | .137422 | .228261 | .346791 | 22.552277 |
| Logistic, calendar | .767081 | .127847 | .213251 | .333333 | 23.042961 |
| Logistic, frequency + gap | .781056 | .130176 | .222826 | .327122 | 23.024845 |
| Logistic, frequency + gap + periodicity | .796584 | .132764 | .227484 | .336957 | 22.671066 |
| Logistic, full | .796584 | .132764 | .221532 | .329451 | 22.981884 |

Random Forest and both boosting packages were unavailable and **not evaluated**.
The logistic results use the explicitly documented SciPy implementation.

Every learned specification's paired 95% interval for mean-hit difference
versus RandomModel includes zero. Gap-only has the largest observed mean,
but its difference is +.051242 with interval [-.035714, .139790]. Its upper-tail
random-reference fraction is .055972, Bonferroni .447776. This is not a finding
of predictive advantage. Its early/middle/recent differences versus baseline
are -.046512, +.097674, +.102804; superiority is not consistent across blocks.
Similarity differences are -.139535, +.060465, +.018692 across those blocks.
Full logistic differences are -.088372, +.088372, -.004673.

The predeclared periodicity increment (frequency+gap+periodicity minus
frequency+gap) is +.015528 hits, 95% paired interval [-.054348, .090062].
The three block differences are +.013953, +.074419, -.042056. Mean winning rank
improves by .353778 ranks (lower is better), but its difference interval
[-.711704, .002899] also includes zero. Recall@6/10/15 incremental intervals
all include zero. These are uncorrected descriptive intervals across several
metrics; **no reliable incremental periodicity value is established**.

The 2,000 repeated random runs average .799244 hits (theory .8), with a 95%
range for a 644-ticket run of [.737578, .860248]. Full match histograms and
3+/4+/5+ rates are in comparison.csv; the best observed deterministic result
was four hits, with no five- or six-hit tickets in these nine specifications.

Completed experiment runtime: **163.349 seconds**, including 47.380s feature
generation, 35.562s similarity and 29.911s full logistic. Other logistic
ablations each took 4.2..11.4s. A diagnostic-heavy earlier attempt was canceled
before results; replacing unnecessary neighbor explanations in the scoring path
preserved exact scores and improved runtime without changing the protocol.
The later added ranking-metric bootstrap columns were calculated from the
unchanged saved audit, without model refitting or selecting new specifications.

Exports: 5,796 audited model-target rows, 3,725 coefficient rows, 27 time-block
rows, and 115,920 separate seeded weighted tickets summarized per model-target.
An independent artifact check reconstructed all outcomes/hits, confirmed 45
scores/ranks and six unique choices for every target, and verified every fit
cutoff against the 26-draw schedule. Latest-draw reservation remained intact.

`predict-current --model logistic` also completed on real data, using cutoff
1245 for scheduled target 1246, in 55.17s. It is experimental output, not a
recommended or validated ticket. Real-data `explain-number 17 --neighbors 5`
was also exercised. No source data was changed.
