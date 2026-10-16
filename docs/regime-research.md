# Regime, Bayesian and frozen-ensemble research

This phase tests different statistical assumptions, not whether visually
interesting patterns can be turned into a profitability claim. The existing
gap/prize experiment and its defaults remain unchanged.

## Reproduce

```powershell
python main.py hazard-analysis
python main.py compare-regime-models
python -m pytest -q
```

Outputs go to `reports/regime_research/`, with selected-number plots under
`plots/`. Reports are generated artifacts and ignored by Git. The fixed
retrospective loader stops before actual draw1245. Nothing fetches new results.
The supplied canonical dataset still ends at1245; prior Phase3 access means
1245 must not be described as a pristine final holdout.

## Protocol and assumptions

The primary comparison covers601-1244 with26-draw retraining. All models
consume the same causal feature rows and labels beginning at draw105. Each fit
ends strictly before its target. The shared tables have51,300 rows through1244.
Current features update every draw. HMM parameters freeze between fits while
the forward state observes only the last completed draw; Bayesian counts also
update causally between fits. Repeated scoring is idempotent and skipped or
backward online targets are rejected.

Ensemble weight selection uses601-900. We evaluate frozen weights on901-1244.
This later block is untouched by this phase's weight selection, **not by all
previous research**. Results from earlier phases already examined those draws.
There is no genuinely pristine historical evaluation block available here.
Fixed robustness runs use starts501 and701 at cadence26, and601 at cadence13.
These overlap and are not independent replications. No settings were selected
to improve the latest draw or the later evaluation results.

### Gap hazards

Exact gap is the number of consecutive completed draws without an appearance;
zero means the number appeared in the last draw. Fixed bucket boundaries are
`[1,3,5,8,13,20,30]`. Relative-gap boundaries are
`[.25,.5,1,1.5,2,3,4]`; standardized gap is
`(current_gap+1-mean_gap)/gap_std` with boundaries`[-1,-.5,0,.5,1,2,3]`.
Zero/undefined gap standard deviation is unsupported rather than fabricated.
Reports contain observations, successes, empirical probabilities, deviations
from6/45, Jeffreys95% marginal intervals, and an adequacy flag (at least200 rows),
for all history and three chronological eras. Exact rare gaps remain visible
with inadequate-sample flags. Rows across numbers in a draw are dependent;
these marginal intervals are descriptive, not corrected significance tests.

GapHazardModel pools numbers within the fixed current-gap buckets. Its score
is`(successes+75*6/45)/(observations+75)` from training labels only. Empty bins
return the fair-number prior. It does not assume that absence raises hazard.
Alternate ratio/zscore bins are supported explicitly; the default experiment
does not search these for the best result.

### Bayesian tendencies

Each number has a fixed Beta(2,13) prior. Static posterior parameters are
`alpha=2+successes`, `beta=13+failures`; score is the posterior mean.
The recency variant discounts observations by`2**(-age/52)` before adding the
same prior. Its fractional-count Beta intervals describe the chosen model;
they are not empirically calibrated confidence statements about Lotto bias.
The45 marginal models do not model the joint six-without-replacement outcome.
No empirical-Bayes tuning or cross-number prior fitting is performed.

### Bernoulli HMM

No suitable HMM dependency is installed. The small NumPy implementation batches
45 independent2-state or3-state Bernoulli models, using the last260 available
supervised observations (minimum104). It is not a general-purpose HMM library.
EM uses scaled forward/backward recursion for training, two deterministic
initializations, at most40 iterations, and relative objective tolerance1e-5.
The initial state distribution is fixed uniform. Transition pseudocounts are8
on the diagonal and1 off-diagonal; emission success/failure pseudocounts are2/13.
Equivalently these updates maximize a penalized likelihood with Dirichlet
parameters pseudocount+1 and Beta(3,14) emission priors. They are not the same
estimation operation as the Bayesian model's Beta(2,13) posterior mean.

The best penalized objective is chosen separately for each number. Probabilities
are clipped to[1e-6,1-1e-6]. States are sorted by emission probability after fitting
and labeled cold/hot or cold/neutral/hot. Labels imply no verified real regime.
Fit exports include transition matrices, emissions, state probabilities,
likelihood, convergence, iteration count and initialization sensitivity.
Predictive state exports and plots use **forward filtering with past-fitted
parameters**, not retrospective smoothing or full-history fitted parameters.

For numbers7/17/34, count-preserving permutations of the final260 open labeled
observations compare emission spread, mean diagonal transition probability and
log-likelihood improvement over a constant Bernoulli model. There are39 shuffles
per number and configuration. The18 diagnostics receive Bonferroni adjustment.
The minimum attainable raw p-value is.025: this inexpensive diagnostic cannot
provide strong corrected evidence. Its purpose is to expose artificial structure.
Correlations of causal hot/cold probabilities with frequency, gap, periodicity
score and causal heuristic strong-regime flags are exploratory Spearman summaries.
No correlation p-values or predictive causal interpretation are assigned.

### Ensembles and evaluation

Cross-sectional rank normalization uses average ranks for ties, mapped to0-1.
Score normalization uses per-target min/max, also0-1. Constant scores map to.5.
Both use only the45 scores already emitted for the target. They are ranking
utilities, not calibrated appearance probabilities.

Equal weights are tested for Gap+Bayesian, Gap+HMM, Bayesian+HMM, all three,
all components, all except periodicity, and all except Similarity, under each
normalization. The small development search compares equal weights with doubling
just one component, using development Top6 hits only; ties prefer the first
configuration. Weights are frozen before any later outcome is evaluated.
"All" means all prespecified research components, not all validated signals.

Ranking, candidate pools and fixed-budget portfolios reuse the previous phase's
implementations. Top6/8/10/12/15 pool reports include full winner distributions,
exact hypergeometric references, empirical simulations, rare-event intervals and
multiple-testing adjustment. Later-period portfolios use Top12,1/5/10/20 unique
tickets, weighted and five-subset coverage construction, three deterministic
seeds, and equal-budget RandomTop12 and unrestricted Uniform45 references.
Bonus is used only after ticket construction for prize classification.
Paired ranking/portfolio intervals use2000 circular moving-block bootstraps
with26-draw blocks. They are descriptive, unadjusted intervals across many
experiments. Individual prize events are not evidence of an advantage.

## Prospective capability

```powershell
python main.py freeze-next
```

This is a separate, offline command. It reads at most the locally supplied
header and1245 canonical rows, never the next row; it does not access the network.
With the current full dataset its target would be1246. It is **not invoked on
the real dataset during this phase**, and no prediction for1246 is made here.
Synthetic tests exercise it without revealing any held-out actual outcome.

Each call creates a new exclusive timestamped/UUID JSON file under
`reports/prospective/`. It records the exact bounded-source byte hash, latest
draw/date, next target, UTC timestamp, Git SHA/dirty flag, implementation hashes,
dependency versions, configurations, seeds,45 scores, Top6/10/12/15 rankings,
and20-ticket weighted/coverage portfolios whose prefixes define smaller budgets.
It never silently overwrites an existing snapshot. Local files are not a trusted
timestamp service or a cryptographic proof that an outcome was unknown.

The fixed snapshot policies are static/recency Bayesian, HMM2/3 and Frequency52.
They are separately versioned policies, not automatically selected winners of
this experiment; no ensemble or Logistic winner is silently chosen. Bayesian
snapshots use local observations from draw1, explicitly recorded in their
configuration; retrospective Bayesian comparisons start105. Consequently the
snapshot policy is not claimed to be identical to those historical experiments.
Only a target independently known to be unseen at freeze time can later be
treated as a genuine prospective test. Its result must be retrieved separately
after freezing; this command never does so.

## Results of the fixed run

No reliable predictive advantage was established. The primary comparison uses
644 targets,601-1244. Differences below compare each model with the same seeded
RandomModel targets; brackets are95% paired26-draw-block bootstrap intervals.

| Model | Average Top6 hits | Difference vs Random [95% interval] | Mean winner rank |
|---|---:|---:|---:|
| RandomModel | .7981 | reference |22.9332|
| Gap Logistic | .8494 |+.0512 [-.0357,.1398]|22.7549|
| GapHazard | .7811 |-.0171 [-.1165,.0808]|23.1910|
| Bayesian static | .7733 |-.0248 [-.1149,.0683]|23.2156|
| Bayesian recency | .7640 |-.0342 [-.1320,.0621]|23.1284|
| HMM2 | .7873 |-.0109 [-.0947,.0714]|22.9589|
| HMM3 | .7873 |-.0109 [-.0978,.0761]|22.9568|
| Frequency52 | .7842 |-.0140 [-.1134,.0807]|23.1294|
| Similarity | .7780 |-.0202 [-.1102,.0715]|23.3103|

Theoretical uniform expectation is.8 hits and mean winning rank23. All intervals
include zero. Bootstrap Monte Carlo endpoints can differ from the earlier
gap-specific report because this report uses the common ranking-summary stream
across a different ordered model list; old commands/results are unchanged.

### What the hazard and regime diagnostics show

| Current gap | Observations | Appearance rate | Marginal95% interval |
|---|---:|---:|---:|
|0|6840|.13670|[.12871,.14499]|
|1-2|10990|.13285|[.12660,.13929]|
|3-4|8330|.13121|[.12409,.13859]|
|5-7|8763|.13477|[.12774,.14204]|
|8-12|8327|.13414|[.12695,.14159]|
|13-19|4970|.13400|[.12475,.14369]|
|20-29|2286|.12555|[.11244,.13960]|
|30+|794|.12720|[.10540,.15173]|

Every broad-bin interval contains6/45. There is no monotone overdue-number
increase. Exact-gap, relative-gap, z-score and era tables are in`hazard.csv`.
The smoothed model's out-of-sample result does not give the earlier gap Logistic
uplift a robust interpretable basis; sampling variation remains plausible.

HMM2/3 median emission spreads across fits are.00312/.00116: many fits almost
collapse to one Bernoulli rate. Mean spreads are.02584/.01547, with occasional
larger separations. Convergence fractions are99.82%/99.91%; exceptions remain
flagged in exports, not silently called converged. Mean initialization-dependent
spread ranges are.000758/.002218. Persistent transition estimates alone are not
evidence because the transition prior encourages persistence.

All18 selected-number null comparisons have corrected p=1.0 (raw minimum.225).
Real sequences did not show unusually strong fitted state structure relative
to count-preserving shuffles in this inexpensive diagnostic.
Across45 numbers, median hot-state Spearman correlations are:

| Feature | HMM2 | HMM3 |
|---|---:|---:|
|52-draw frequency|.267|.236|
|Current gap|-.447|-.437|
|Periodicity score|-.014|-.008|
|Causal strong-periodicity flag|-.036|-.024|

These descriptive associations suggest the fitted states mostly track recent
appearance behavior, with little broad correspondence to periodicity regimes.
Plots for7/17/34 and per-number relationships are exported.

### Later-period ensembles and ablations

The frozen weight search chose Gap Logistic weight.2 and each of the other eight
components weight.1. It achieved.8433 Top6 hits in development, then.7849 on the
344 later targets901-1244. Later RandomModel averaged.7674, with theoretical
expectation still.8. The paired difference is+.0174 [-.0843,.1193].

| Later model | Avg hits | Mean winner rank | Recall6 | Recall10 | Recall15 |
|---|---:|---:|---:|---:|---:|
|RandomModel|.7674|22.9627|.1279|.2200|.3372|
|Gap Logistic|.8285|23.0252|.1381|.2195|.3290|
|GapHazard|.7151|23.4952|.1192|.2093|.3169|
|Bayesian static|.8314|23.3086|.1386|.2204|.3256|
|Bayesian recency|.7471|23.3983|.1245|.2093|.3188|
|HMM2|.7645|22.9976|.1274|.2224|.3295|
|HMM3|.7674|22.9850|.1279|.2209|.3314|
|Development-weight ensemble|.7849|23.2902|.1308|.2122|.3203|

All later model/ensemble average-hit paired intervals include zero. Equal-rank
all-component averaging gives.7297; removing periodicity increases it to.7558,
and removing Similarity increases it to.7471. Equal normalized-score averaging
gives.7936; those removals instead decrease it to.7616/.7645. Thus component
benefits depend on the combination rule and are not robust. Full15-ensemble
ablations, hit distributions and era results are in the later CSVs. None is
adopted as a demonstrated improvement.

### Robustness

| Model |501-1244, cadence26|601-1244, cadence26|701-1244, cadence26|601-1244, cadence13|
|---|---:|---:|---:|---:|
|RandomModel|.8051|.7981|.7757|.7981|
|Gap Logistic|.8320|.8494|.8456|.8525|
|GapHazard|.7984|.7811|.7923|.7748|
|Bayesian static|.7876|.7733|.7739|.7733|
|Bayesian recency|.7661|.7640|.7629|.7640|
|HMM2|.7769|.7873|.7721|.7609|
|HMM3|.7688|.7873|.7555|.7748|

All corresponding paired average-hit intervals include zero. Bayesian results
are cadence-invariant at the same start because exact online count updates match
refitting. HMMs are not consistently better across starts or cadences. In the
primary early/middle/recent blocks, HMM2 scores.786/.870/.706 and HMM3
.781/.842/.738 versus Random.856/.772/.766. The middle-block uplift reverses in
other blocks. New individual models, plus Gap Logistic, receive these extra
fits; ensembles do not establish a promising advantage warranting further
adaptive weight/cadence searches. Every later ensemble has separate time blocks.

### Candidate concentration and portfolios

Counts of later draws with at least five main winners in the candidate pool:

| Model |Top8|Top10|Top12|Top15|
|---|---:|---:|---:|---:|
|RandomModel|0|0|0|0|
|Gap Logistic|0|1|1|3|
|GapHazard|0|1|1|2|
|Bayesian static|0|0|1|6|
|Bayesian recency|0|0|0|3|
|HMM2|0|0|2|5|
|HMM3|0|0|0|6|
|Development-weight ensemble|0|0|0|4|
|Exact random expected count,344 draws|.089|.381|1.143|4.016|

All these models have zero all-six pool events. The only all-six event among
all tested policies is the old mean-reversion heuristic at Top15. Every corrected
later pool test has p=1.0. The empirical random run's zero rare events does not
replace the positive exact expectations. The complete reports include0-6 winner
distributions,3+/4+ rates, intervals and all pool sizes.

Later mean best match per draw across three seeds (weighted Top12 portfolios):

| Policy |1 ticket|5 tickets|10 tickets|20 tickets|
|---|---:|---:|---:|---:|
|Development-weight ensemble|.7490|1.3120|1.4360|1.4952|
|RandomModel Top12|.8072|1.3624|1.4884|1.5746|
|Uniform45 unrestricted|.8333|1.7665|2.1095|2.4099|

At20 tickets, ensemble coverage yields1.5078 versus matched random coverage1.5862.
The ensemble's paired mean-best difference is-.0795 [-.1996,.0475] for weighted
and-.0785 [-.2016,.0485] for coverage. The candidate restriction lowers broad
ticket coverage; unrestricted random portfolios are a necessary practical
reference. None of the new models demonstrates better prize-aware performance.
The recency-Bayesian portfolio is worse than matched random in some unadjusted
intervals; this is a diagnostic, not a corrected inferiority claim.

Across all30 model policies, both methods, three seeds and the Uniform45 control,
there are1,259,040 maximum-budget ticket instances (smaller budgets reuse their
prefixes). They produce27 rare-event occurrences, representing15 distinct
draw/ticket pairs on9 draws: **0 first,1 second,14 third-prize equivalents**.
The second-equivalent ticket is[10,12,18,39,42,43] at942, with five main winners
and bonus39, repeated across three Bayesian+HMM construction variants. It is
one distinct historical event, not three independent successes. The frozen
development-weight ensemble and the individual Bayesian/HMM models produce no
five-main-match tickets here. GapHazard produces a third-equivalent at1123.
All individual prize counts and nonzero uncertainty bounds for zero-event
samples are retained in`portfolio_replicates.csv`.

## Verification and dependencies

Full suite: **136 passed,2 skipped** in21.67s, including all original114 passing
tests. The skips are optional tree dependencies. Independent code review found
no blocking causal or mathematical defect and reproduced one HMM EM update by
exhaustive state-path enumeration within2.78e-17. A missing-Git provenance case
was fixed with a failing-then-passing regression: unknown status is JSON null,
never falsely clean. Synthetic snapshot tests forbid network connections.

The complete default experiment took291.34s, including null diagnostics,
portfolios and the additional robustness fits. Primary HMM2/HMM3 took8.62/8.81s
for644 targets each. The final combined comparison CSV was assembled from saved
results without refitting or changing any predictions.

Artifact checks independently reconstructed9660 individual and10320 later
ranking records,99900 candidate-pool counts,251808 fixed-budget rows,57960
filtered-state probability rows and all27 rare ticket occurrences against the
bounded open dataset. Training cutoffs, target boundaries, nested budgets,
state normalization, prize classifications and the open-prefix hash agree.

`hmmlearn`,scikit-learn,LightGBM andXGBoost remain absent. `PIP_NO_INDEX=1`
blocks index lookup; the configured proxy127.0.0.1:9 refused the authorized Git
push in this session (connection refused). No network bypass, package-install
retry campaign, tree replacement, or future-result request was attempted.

The requested checkpoint already existed as clean commit
`5b66beed885de7ee4d240e06100e474c03609497`, with message
`feat: add prize-aware validation and gap signal audit`. It was reverified with
114 passed,2 skipped before Phase4 edits. Push failed at the proxy; remote
authentication could not be established. No duplicate checkpoint, history
rewrite, second commit or Phase4 push was performed.
