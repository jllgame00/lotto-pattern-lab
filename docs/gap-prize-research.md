# Gap robustness and prize-aware research

The result is **no established predictive or portfolio advantage**. Gap-only
logistic has stable coefficient signs, but its advantage over random and simple
gap rules remains uncertain. Concentrating tickets in Top12 lowers mean best
matches compared with unrestricted random portfolios; the few five-match events
do not establish a compensating reliable benefit. No profitability is calculated.

## Research boundary and reproduction

```powershell
python main.py prize-eval
python -m pytest -q
```

The command reads only canonical draws1..1244, using `load_research_history`.
It reads at most the header and1244 physical CSV rows; the suffix is not parsed,
hashed, passed into features, or used for selection. Features/models/backtest
boundaries reject1245+. There is no CLI unseal flag. Canonical current prediction
and collection are blocked. Alternate-path candidates cannot target1245, and
collection cannot copy the canonical suffix through an alternate destination.
Network collection is frozen because a response batch could contain later draws.
Only short validated open-prefix offline CLI imports remain supported.

Historical provenance caveat: the previous phase's `predict-current` command
used data through1245. That prior access cannot be undone, so the dataset cannot
be described as never previously accessed. This phase did not inspect1245 and
did not reuse the prior feature export or current-prediction artifacts. The seal
describes the enforced boundary for this research, not a retroactive claim.

Settings fixed before this run: C=1, seed42, cadence26, starts401/501/601/701/801,
end1244; primary window601..1244. Features begin at target105. The open feature
table has51,300 rows. Primary comparisons include15 specifications: RandomModel,
gap and gap+periodicity logistic, five gap rules, six other existing logistic
groups, and same-number similarity. Other starts repeat random, both gap
logistics and all five rules. No tuning or tree-model replacements were added.

Repeated start windows overlap, and their cadence phases differ. They are
sensitivity checks, not five independent replications. Gap-only was selected
for investigation after seeing earlier historical results; these reused periods
are exploratory evidence, not independent confirmation of strategy selection.

## Gap-only robustness

Paired mean-hit difference is Gap Logistic minus the same seeded RandomModel on
identical target draws. Intervals are estimated95% circular26-draw block-bootstrap
intervals,2000 replicates. The gap comparison uses the same bootstrap stream in
the robustness and heuristic tables.

| Start | Targets through1244 | Gap average hits | Difference vs random | Paired95% interval |
|---|---:|---:|---:|---|
|401|844|.843602|+.041469|[-.030806, .117299]|
|501|744|.831989|+.026882|[-.057829, .112903]|
|601|644|.849379|+.051242|[-.032609, .133579]|
|701|544|.845588|+.069853|[-.016544, .159926]|
|801|444|.853604|+.085586|[-.006813, .175732]|

Every interval includes zero. In the primary window, early/middle/recent mean
hits are .809302/.869767/.869159, but differences versus the paired random
baseline are -.046512/+.097674/+.102804. The higher aggregate is not a uniform
advantage over time.

### What actually drives the ranking

`coefficient_audit.csv` contains2520 rows for every fit of both gap models across
all five starts: signed standardized coefficient, magnitude, raw-unit coefficient,
training mean/std, imputation median, intercept, C, exact feature definition,
training rows and cutoff. `coefficient_stability.csv` summarizes sign changes
and ranges. `ranking_contributions.csv` audits within-target additive logit
variation and the mean rank change when each term is removed without refitting.
These are mechanical explanations, not causal feature importance.

At start601, the25 gap-only fits have these mean standardized coefficients:

| Feature | Mean coefficient | Sign changes | Mean absolute rank change if term removed |
|---|---:|---:|---:|
|current_gap|-.151255|0|15.33|
|gap_ratio|+.139851|0|8.62|
|median_gap|+.051890|0|11.33|
|gap_std|+.050674|0|9.45|
|mean_gap|-.027469|0|3.14|
|has_appeared|0|0|0|

The two largest standardized coefficients oppose each other and their inputs
are correlated. In raw units, the current-gap contribution is
`gap * (b_current_gap + b_gap_ratio / historical_mean_gap)`.
It is therefore **not** a simple largest-gap or overdue-number rule. Historical
median and variability also reorder numbers. Removing one correlated term can
have a large effect because it removes a cancellation; these rank changes must
not be summed as independent contributions. `has_appeared` is constant here.

This audit explains the ranking mechanism. It cannot establish that the extra
realized hits were caused by a repeatable signal; the observed differences remain
compatible with sampling variation.

### Transparent rules

All rules receive the same causal features and use training-only median
imputation for unsupported estimates. Zero/unsupported denominators give a
neutral zero score. No prior separate documented GapModel existed.

| Rule | Score (larger ranks first) | Average hits,601..1244 | Gap logistic minus rule,95% interval |
|---|---|---:|---|
|Largest gap|current_gap|.804348|[-.055939, .150621]|
|Smallest gap|-current_gap|.810559|[-.046584, .113354]|
|Relative gap|current_gap / mean_gap|.801242|[-.048137, .150621]|
|Gap z-score|(current_gap+1-mean_gap) / gap_std|.822981|[-.071429, .125815]|
|Mean-reversion style|-abs(gap z-score)|.833851|[-.069876, .105629]|

The +1 in z-score means the interval that would finish at the upcoming draw;
current absence is0 immediately after an appearance. These are testable simple
rules, not claims that lottery outcomes compensate for past absence. **None of
the25 gap-vs-rule mean-hit intervals across five starts excludes zero.**

## Candidate concentration

For a TopK set, the exact uniform winner-count distribution is
`P(J=j)=C(6,j)*C(39,K-j)/C(45,K)`. Reports include the full0..6 distribution,
>=3/4/5/6 rates, expected event counts, exact random references,2000 seeded
Monte Carlo runs, paired differences, and Clopper-Pearson event-rate intervals.
The latter assume iid Bernoulli draws; they are not general dependence-robust
confidence statements. Block-bootstrap paired intervals are also provided.

Primary gap-only results over644 draws:

| Pool | Six-number combinations | >=5-winner events | Observed rate | Exact random rate | Random expected events | All-six events |
|---|---:|---:|---:|---:|---:|---:|
|Top6|1|0|0%|.002885%|.0186|0|
|Top8|28|0|0%|.025783%|.1660|0|
|Top10|210|2|.310559%|.110865%|.7140|0|
|Top12|924|4|.621118%|.332226%|2.1395|0|
|Top15|5005|8|1.242236%|1.167518%|7.5188|0|

The empirical RandomModel has0/0/0/3 >=5-winner events at Top8/10/12/15.
Its zero Top12 count should not replace the exact expectation of2.14 events.
Across all15 specifications and five pool sizes, all Bonferroni-adjusted
>=5/all-six upper-tail random-null binomial tests equal1.0 (150 planned tests).
Some other specifications contain all six winners once; none is established as
statistically unusual after this search. Event identities and time blocks are
exported without selecting a new strategy from them.

## Does periodicity help the gap model?

Gap+periodicity, compared directly with gap-only at start601:

- Average Top6 hits: .804348 versus .849379; difference -.045031,
  paired95% interval[-.135093, .045070].
- Mean winning rank:22.573758 versus22.754917; lower is better. Difference
  -.181159, interval[-.569397, .243012].
- Top10 >=5 coverage:0 versus2 events; difference interval[-.007764, 0].
- Top12 >=5 coverage:2 versus4 events; difference interval[-.010870, .003106].

Average hits and these two concentration counts do not improve. Better mean
rank is uncertain. All five starting-window comparisons are exported; no
incremental periodicity benefit is established.

## Fixed-budget virtual portfolios

Primary pool size was fixed at12 before results. `--pool-size` also supports
8,10,15. Budgets1/5/10/20 are prefixes of one deterministic20-ticket construction
per model/draw/seed. Each ticket has six unique numbers and each portfolio has
distinct tickets. Top6 has only one possible ticket and cannot support20 unique
tickets. No target result or bonus enters either constructor.

- **Weighted:** each combination has weight proportional to the product of its
  six number weights. Gumbel ordering samples distinct combinations with those
  weights. Negative heuristic scores are shifted to nonnegative values; a0.1%
  uniform mixture keeps all candidates eligible. This is explicit combination
  weighting, not calibrated prize probabilities or the older sequential sampler.
- **Coverage:** greedily maximize newly covered five-subsets, then pairs, then
  use the same seeded score-weighted priority for ties. This reduces near-duplicate
  tickets. Only small spaces up toC(15,6)=5005 are enumerated.
- **Random Top12:** uses the same construction and budgets on RandomModel's
  uniformly ranked pool. **Uniform45:** independently samples distinct tickets
  uniformly across all45; the8,145,060-ticket space is never enumerated.

Three seeded replicates share the same actual historical draws. Summary means
average the seeds within each draw before paired block bootstrapping. Counts
for each replicate are exported separately, including per-prize draw intervals.
Do not treat the seeds or overlapping budget prefixes as independent history.

Mean best main matches per draw (644 targets, averaged over three seeds):

| Budget | Gap weighted | Random Top12 weighted | Gap coverage | Random Top12 coverage | Uniform45 |
|---|---:|---:|---:|---:|---:|
|1|.797101|.792443|.797101|.792443|.823499|
|5|1.361801|1.365942|1.472567|1.480849|1.743271|
|10|1.499482|1.505694|1.536749|1.547619|2.099379|
|20|1.574017|1.577122|1.587992|1.586957|2.389752|

At20 tickets, gap weighted minus matched random is -.003106 with95% interval
[-.106121,.099896]; coverage is +.001035[-.100414,.102484]. The corresponding
differences versus Uniform45 are -.815735[-.896506,-.733424] and
-.801760[-.882531,-.718414]. Concentrating tickets sacrifices mean best matches
without establishing a reliable five-match benefit.

Twenty tickets cover20/924=2.1645% of six-number combinations. Gap weighted
portfolios cover on average14.2465% of Top12 five-subsets; the coverage method
covers120/792=15.1515%. Greater combinatorial coverage is not evidence of better
candidate prediction. All budgets' coverage,4+/5+ draws and prize counts appear
in portfolio_summary.csv and portfolio_replicates.csv.

### Exact unrestricted-random budget reference

For B distinct uniform tickets among M=C(45,6), with F favorable combinations,
`P(any favorable)=1-product(1-F/(M-i), i=0..B-1)`. This gives the exact integrated
random-portfolio best-match distribution and separate1st/2nd/3rd draw probabilities.
It is not the null law for an arbitrary fixed portfolio with different overlaps.
`uniform_portfolio_reference.csv` includes2000 Monte Carlo historical runs sampled
from this exact best-match law without generating enormous ticket spaces.

Expected mean best matches for budgets1/5/10/20 are .800000/1.728936/2.082850/
2.389641. Expected >=5-match draws per644-target run are .0186/.0929/.1858/.3715.
At20 tickets the Monte Carlo95% range is0..2 such draws. An empirical random run
with zero rare events is unsurprising and does not set the true baseline to zero.

### Historical prize equivalents (virtual, not purchased tickets)

Classification uses bonus only after ticket construction: six main=1st; five
main+bonus=2nd; five without bonus=3rd; four=4th; three=5th. Bonus remains absent
from the supervised positive target. Exact uniform per-ticket probabilities
have numerators1,6,228,C(6,4)C(39,2),C(6,3)C(39,3), all overC(45,6).

At budget20 across three seeds, gap weighted produces0 first-,1 second-,4
third-prize ticket occurrences. Gap coverage produces0/0/6. Those overlap:
together they represent one distinct second-prize ticket and six distinct
third-prize tickets on only three historical draws (621,847,1225).

The second-prize equivalent is draw621, weighted seed replicate2, ticket index14
(first included at budget20): `[2,6,9,16,19,42]`. Main winners were
`[1,2,6,16,19,42]`, bonus9. Its model was trained through600 and its features
through620. No draw621 outcome entered scoring or construction.

Across all15 specifications, both methods and three seeds, there are44 rare
ticket occurrences, representing27 distinct target/ticket pairs on14 draws:
0 first-,1 second-,26 third-prize equivalents. Duplicates across methods/seeds
are not independent discoveries. There were1,197,840 generated ticket instances
at the maximum budget including Uniform45; smaller budgets reuse their prefixes.
The one second-prize event is not evidence of predictability or profitability.

## Dependencies, verification, artifacts

All optional tree libraries remain absent. Current diagnosis found
`PIP_NO_INDEX=1` and HTTP/HTTPS proxies pointing to`127.0.0.1:9`. A single bounded
PyPI HTTPS probe failed with ConnectionRefusedError/WinError10061. Restrictions
were not disabled. No Random Forest or boosting execution was claimed and no
complex replacement was implemented. Exact details are in dependency_probe.json.

The main experiment took219.771s, including100.794s for portfolios. A subsequent
5.035s reporting refresh added per-prize draw intervals and synchronized gap
bootstrap tables; exact-reference/combinatorial columns were also added from
saved outcomes and formulas. No model or ticket settings were changed after
results. The independent review caught candidate/import seal bypasses and missing
per-prize zero-event intervals; regression tests now cover each fix.

Reports are under`reports/prize_research/`. Main files:

- `comparison.csv`, `ranking_comparisons.csv`, `ranking_time_blocks.csv`.
- `coefficient_audit.csv`, `coefficient_stability.csv`, `ranking_contributions.csv`.
- `gap_vs_heuristics.csv`, `gap_periodicity_comparison.csv`.
- `candidate_summary.csv`, `candidate_pools.csv`, `pool_5plus_events.csv`.
- `portfolio_summary.csv`, `portfolio_replicates.csv`, `portfolio_time_blocks.csv`.
- `prize_events.csv`, `uniform_portfolio_reference.csv`, `experiment.json`.

Artifact verification reconstructed9660 rankings and48300 pool counts, checked
all239568 equal-budget records and nested outcomes, and independently classified
all44 rare ticket occurrences against the open-prefix main numbers and bonus.
All evaluated targets and feature cutoffs respect the seal. No commit or push.

Full test suite: **114 passed,2 skipped** (optional tree integrations),14.67s.
All original85 tests pass. Compile and whitespace checks also passed.
