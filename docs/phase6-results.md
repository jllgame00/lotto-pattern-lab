# Phase 6 results: TESTED / INCONCLUSIVE

Canonical input: draws1–1245, 1,245×45 binary main-number matrix; six ones per
row. SHA-256: `b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e`.
No draw1246 or later result was retrieved, inspected, or evaluated. Phase5 files
and registry retain their original hashes. No commit or push was made.

## Descriptive findings and full-search nulls

The strongest raw shift is (+42 draws, -5 numbers):960 matches/6,426 eligible
source points, rate.149393, IID expectation.133333, lift1.120448, raw z3.787162.
The next strongest are (+1,+8),895/6,131, and (+38,+14),731/4,969. These are
full-history exploratory selections, not rules used retrospectively in backtests.

The (+42,-5) conditional rates are.152827 in draws1–415, .146293 in416–830,
and.147117 in831–1245. This same-sign pattern is descriptive and selection-biased;
the complete-search corrected test below remains inconclusive. Rolling260-draw
plots and all top10 candidates' era tables are exported.

The longest maximal chains have7 points. Examples: draw873/number3 to
draw903/number21 at (+5,+3), and draw280/number37 to draw334/number13 at (+9,-4).
All398 surrogate histories contain chains at least as long; random longest
chains averaged approximately7.8. Overlapping subchains are not independent discoveries.

The strongest Hough line has displacement(+9,-2),12 observed points out of23
eligible positions, density.521739, from draw498/number45 to draw696/number1.
Its raw z5.479667 is ordinary among complete surrogate searches. The largest
2D spectral normalized power is.0003561; it also is ordinary under both nulls.

| Search statistic | IID global p | Fixed-margin global p | IID six-family adjusted p | Fixed-margin adjusted p |
|---|---:|---:|---:|---:|
| Shift | .055 | .080 | .330 | .480 |
| Directional asymmetry | .285 | .255 | 1 | 1 |
| Chain-count score | .650 | .635 | 1 | 1 |
| Longest chain | 1 | 1 | 1 | 1 |
| Hough line | .375 | .405 | 1 | 1 |
| Spectral concentration | .795 | .725 | 1 | 1 |

199 histories per null, seed60042. Both null families changed about23.1% of
matrix cells on average. Fixed-margin trades preserve exact number frequencies
and row sums; finite mixing remains a limitation. No tested structure survives
search correction. Absence of evidence in this bounded search is not proof that
every conceivable structure is absent.

## Walk-forward ranking

All model settings were declared before results. Development401–900, later
evaluation901–1245, cadence26. Later means later than this phase's development;
earlier project phases already used these historical draws. Paired intervals
below are2000-replicate26-draw circular block bootstrap intervals, not corrected
for the many comparisons.

| Model | All401–1245 avg Top6 | Later901–1245 avg Top6 | Later difference vs Random | Paired95% interval |
|---|---:|---:|---:|---|
| Uniform Random | .802367 | .768116 | 0 | baseline |
| Translation | .815385 | .776812 | +.008696 | [-.092754,.107246] |
| Chain | .794083 | .834783 | +.066667 | [-.043478,.171087] |
| Fixed equal-rank combination | .841420 | .823188 | +.055072 | [-.043478,.168116] |
| Existing Gap Logistic | .842604 | .823188 | +.055072 | [-.046449,.168116] |

| Model, later period | Winning-number mean rank | Recall@6 | Recall@10 | Recall@15 |
|---|---:|---:|---:|---:|
| Random |22.9585|.128019|.219807|.336715|
| Translation |23.0444|.129469|.219324|.316425|
| Chain |22.7884|.139130|.225604|.326570|
| Combination |22.8744|.137198|.222222|.336232|
| Gap Logistic |23.0478|.137198|.218357|.330918|

Every primary paired hit interval includes zero across starts401/501/601/701/801/901.
Translation's early/middle/recent average hits are.8546/.8298/.7616, while Chain's
are.7482/.8121/.8221. Their relative behavior changes across periods.
Cadence13 later results are Translation.7681, Chain.8029, combination.8116,
Gap Logistic.8203, Random.7681; all paired intervals still include zero.

Later-period ablations: Translation positive.7594, negative.8522, short.8638,
long.7623; Chain positive.8406, negative.8029, short.7739, long.8087. All their
paired hit intervals also include zero. The highest observed ablation is not
promoted to the prospective model after examining this evaluation period.

## Candidate pools and rare events

Counts of pools containing at least5 winners over all845 targets:

| Model | Top8 | Top10 | Top12 | Top15 | Top15 all6 |
|---|---:|---:|---:|---:|---:|
| Random |0|0|2|8|0|
| Translation |0|0|1|5|0|
| Chain |0|1|1|3|1|
| Combination |0|0|2|7|0|
| Gap Logistic |0|2|5|10|0|

The Chain all-six Top15 event occurred at draw466, in development. It is a
candidate-pool event, not an actual six-number ticket prize. Under uniform
ranking,845 targets yield about9.87 Top15 >=5 events and.519 all-six events on
average. One all-six event amid many searches is not evidence of predictability.

On later345 targets, Top15 >=5 counts are Translation3, Chain1, combination3,
Gap3, Random0; Top12 counts are1/0/1/1/0; Top10 counts0/0/0/1/0; Top8 all zero.
All-six pools are absent there. The zero events in this one seeded Random
control do not imply zero random probability. Exact >=5 rates are.000258 for
Top8, .001109 forTop10, .003322 forTop12, .011675 forTop15.
Exports contain full0..6 distributions, >=3/4/5/6 rates, exact baselines,
marginal intervals and paired block intervals. Degenerate all-zero bootstrap
intervals are explicitly flagged and do not rule out rare outcomes.

## Validation, runtime and prospective separation

The full regression suite is run after implementation, including synthetic
known paths, exact margin invariants, complete-search maxima equivalence,
target poisoning for both models, unchanged Gap Logistic scores, deterministic
portfolios, immutable artifact publication and registry-integrity corruption.
Final result: **183 passed,2 dependency-related skipped**,48.78 seconds.

Complete199+199 null searches took approximately465.5 seconds, measured between
the first raw export and final surrogate export while other jobs ran concurrently.
A final plot-label formatting failure was reproduced and fixed; plots were
rendered from the completed saved searches, without rerunning or selecting nulls.
Cadence26 backtest including features and summaries took108.9 seconds;
cadence13 primary sensitivity took85.6 seconds. Pool uncertainty was subsequently
expanded from saved per-target predictions without changing predictions.

The independent Phase6 freeze uses Translation, Chain, and the predeclared
equal-rank combination, full rankings/scores and fixed-seed Top12 portfolios.
Combination development average.854 exceeds each component's point estimate,
but supplies no validated advantage; it remains experimental. Exact portfolios,
configuration, fitted rules, source code and hashes are in the new manifest/JSON.
Phase5 is not changed, and no prospective outcome is evaluated.

See `reports/spatiotemporal/global_null_comparison.csv`, `surrogate_maxima.csv`,
`walk_forward_26/`, `walk_forward_13/`, and `plots/` for machine-readable evidence.
H3 is **TESTED / INCONCLUSIVE**. H4 remains planned; no3D model was implemented.

## Frozen experiment record

Created2026-10-17T08:12:26.305582+09:00, target1246, cutoff1245,
Git`6ce221ce15fb1c8996a1a8b134811b202d16d646`, intentional dirty Phase6 working tree.
Status: **FROZEN_UNEVALUATED**.

- Experiment:`draw1246_phase6_2d_20261017T081226305582_3b783b3c`
- [Snapshot](../reports/prospective/phase6/draw1246_phase6_2d_20261017T081226305582_3b783b3c.json)
  SHA-256:`eda0f22b15f11d967484849391779de5187faf6c420e71052b9e48d7c82c5d01`
- [Manifest and exact ticket portfolios](../reports/prospective/phase6/draw1246_phase6_2d_20261017T081226305582_3b783b3c_manifest.md)
  SHA-256:`4def791e4a57e8ed802529a50a221d414523da7a3d5059b76b50a241c05c5b9b`
- [Integrity record](../reports/prospective/phase6/draw1246_phase6_2d_20261017T081226305582_3b783b3c_integrity.json)
  SHA-256:`a9392735ad80ea2122082521138816c36f280305fd57e241ddf5a7a6607f46c0`
- [Separate Phase6 registry](../reports/prospective/phase6/registry.csv)

Full ranked Top15 lists (Top6/8/10/12 are their respective prefixes):

- Translation:`3,11,38,8,41,39,40,23,13,17,25,36,26,28,12`
- Chain:`25,45,14,5,15,2,39,37,1,3,4,6,7,8,9`
- Combination:`25,39,3,11,37,38,15,8,41,45,40,23,13,14,17`

Exact ties use smaller number first; tied positions are not evidence of stronger
model preference. In particular the Chain ranking has a large tied baseline
group. Full score vectors and tie groups are preserved in the snapshot. No
model or portfolio was redesigned after inspecting these frozen rankings.

The Phase5 snapshot, manifest, integrity record, reservation and registry were
all verified byte-for-byte unchanged after publication. Canonical hash is also
unchanged. No result for1246 or later was retrieved, inspected, or evaluated.
