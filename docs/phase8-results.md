# Phase8 historical results

This report records recent frequency as a replacement third dimension. Gap and frequency are not combined. No4D model or neural network is implemented. All actual historical inputs stop at1245; no draw1246 result is accessed. **H5: TESTED / INCONCLUSIVE.** No statistic family survives complete-search correction under either null, and leakage-safe prediction does not establish superiority. No combination or evaluation-selected window is promoted.

## Causal state definitions and support

For target t, count_W sums draws t-W through t-1 only. A full window is required. Rate=count/W; the historical rate uses all completed draws before t. Relative frequency is recent_rate/historical_rate, missing if the denominator is zero. Missing states are excluded, never silently mapped to an ordinary state. Bonus numbers are excluded. The exported historical feature table has168,075 rows (1245 draws x45 numbers x3 windows).

Raw counts and normalized rates are identical partitions within W and are searched once, with both values exported. Quantile boundaries are training-only1/3 and2/3 quantiles using higher, boundary ties lower. Relative bins use fixed0.5/1.5 boundaries. Descriptive full-history bins and observed ranges:

| W | Possible counts | Observed counts | COLD | NEUTRAL | HOT |
|---|---|---|---|---|---|
|10|0..10|0..7|0..1|2|3+|
|26|0..26|0..12|0..3|4|5+|
|52|0..52|0..17|0..6|7..8|9+|

These descriptive thresholds are never reused in earlier predictions. Missing state -1 means insufficient past history. Counts below:

| window | representation | state | observations | winning_sources |
|---|---|---|---|---|
| 10 | quantile | -1 | 450 | 60 |
| 10 | quantile | 0 | 33801 | 4483 |
| 10 | quantile | 1 | 13997 | 1866 |
| 10 | quantile | 2 | 7777 | 1061 |
| 26 | quantile | -1 | 1170 | 156 |
| 26 | quantile | 0 | 29251 | 3904 |
| 26 | quantile | 1 | 11326 | 1487 |
| 26 | quantile | 2 | 14278 | 1923 |
| 52 | quantile | -1 | 2340 | 312 |
| 52 | quantile | 0 | 23967 | 3179 |
| 52 | quantile | 1 | 16090 | 2148 |
| 52 | quantile | 2 | 13628 | 1831 |


Coarse supports are unequal because count ties are retained. Full raw count distributions, including zero-support possible states, quantiles and relative-state supports are exported. Extreme raw states have fewer than100 winning sources: W10 counts5+, W26 counts8+, and W52 counts0..1 or13+. They cannot dominate supported maxima, even if their raw rates look extreme.

## Exact search space

- Conditional configurations:175,708;67,447 meet minimum100 source opportunities. Includes dt1..52,dn-15..15 and all declared window/state representations. Zero displacement is an included fixed-number reference; predictive rules and translational leader summaries exclude zero.
- Directional configurations:87,360;34,843 supported. Includes positive-minus-negative contrasts with separate boundary denominators and coarse HOT-minus-COLD interactions.
- True count-displacement configurations:1,404; dt1..13,dn+/-1..6,delta_count-1..1. Destination conditions DESCRIPTIVE ONLY.
- Trajectory length3/4/5 configurations:8,424, a subset of43,212 total geometrically possible rule/length tuples.
- Total distinct parameter configurations:307,684. Do not add the length3/4/5 subset again.
- Geometric trajectory rule/length/start-position candidates:1,095,903,536 before data pruning; these overlap and are not independent.

All windows are pooled in the five global statistic families. Optional Hough3D was deferred because the extra sparse intercept family adds little interpretability.

## Strongest raw conditional and trajectory findings

Translational leaders per window, across representations, requiring minimum100 opportunities:

| window | representation | state | delta_draw | delta_number | valid_opportunities | matches | match_rate | raw_z |
|---|---|---|---|---|---|---|---|---|
| 10 | quantile | 2 | 7 | 6 | 914 | 169 | 0.1849 | 4.5863 |
| 26 | quantile | 2 | 12 | 6 | 1673 | 282 | 0.1686 | 4.2386 |
| 52 | count | 4 | 18 | -11 | 435 | 86 | 0.1977 | 3.9493 |


These are raw selected observations, not predictive discoveries. True bounded count-displacement leaders:

| window | delta_draw | delta_number | delta_count | valid_opportunities | matches | raw_z |
|---|---|---|---|---|---|---|
| 10 | 5 | 5 | 1 | 1384 | 225 | 3.1999 |
| 52 | 11 | -5 | 0 | 724 | 125 | 3.1122 |
| 26 | 10 | 6 | 0 | 1032 | 170 | 2.9669 |


Strongest supported continuation statistics:

| window | kind | rule | delta_draw | delta_number | chain_length | valid_opportunities | matches | raw_z |
|---|---|---|---|---|---|---|---|---|
| 10 | same_bin | 0 | 9 | -4 | 3 | 192 | 44 | 3.9064 |
| 26 | same_bin | 0 | 9 | -4 | 3 | 119 | 30 | 3.8113 |
| 10 | same_bin | 0 | 11 | 2 | 4 | 22 | 9 | 3.8049 |


Longest maximal paths:

| window | kind | rule | start_draw | start_number | start_count | delta_draw | delta_number | chain_length | end_draw | end_number |
|---|---|---|---|---|---|---|---|---|---|---|
| 10 | same_bin | 0 | 289 | 33 | 1 | 9 | -4 | 6 | 334 | 13 |
| 10 | delta_count | 0 | 289 | 33 | 1 | 9 | -4 | 6 | 334 | 13 |
| 10 | same_bin | 0 | 523 | 45 | 0 | 2 | -6 | 6 | 533 | 15 |
| 10 | same_bin | 0 | 945 | 9 | 0 | 11 | 2 | 6 | 1000 | 19 |
| 10 | same_bin | 0 | 1154 | 22 | 1 | 3 | -2 | 6 | 1169 | 12 |
| 26 | same_bin | 2 | 563 | 32 | 6 | 8 | -6 | 6 | 603 | 2 |


A W10 COLD path from(draw289,number33,count1) through(draw334,number13) has6 points under(+9,-4), all with count1. The same points qualify as both a coarse COLD chain and zero-count-displacement chain; these are overlapping descriptions, not independent discoveries. Nested fragments are suppressed.

## Identical-target walk-forward comparison

Targets401..1245 (845 draws), expanding past-only fitting, cadence26, seed42. Existing baseline score/ranking/cutoff/hit records exactly reproduce all5,070 prior Phase7 rows at each of the26 and13 cadences. Every new model and reference uses the same target draws.

| model | avg_hits | mean_winning_rank | recall_6 | recall_10 | recall_15 |
|---|---|---|---|---|---|
| TranslationModel | 0.8154 | 22.6675 | 0.1359 | 0.2274 | 0.3371 |
| ChainModel | 0.7941 | 23.0469 | 0.1323 | 0.2199 | 0.3241 |
| GapConditionedTranslationModel | 0.8296 | 22.8771 | 0.1383 | 0.2264 | 0.3428 |
| GapConditionedChainModel | 0.7680 | 23.0953 | 0.1280 | 0.2160 | 0.3320 |
| FrequencyConditionedTranslationModel_W10 | 0.8036 | 23.0854 | 0.1339 | 0.2207 | 0.3272 |
| FrequencyConditionedTranslationModel | 0.7964 | 22.9535 | 0.1327 | 0.2252 | 0.3359 |
| FrequencyConditionedTranslationModel_W52 | 0.7976 | 22.9501 | 0.1329 | 0.2203 | 0.3387 |
| FrequencyConditionedChainModel_W10 | 0.7621 | 23.1677 | 0.1270 | 0.2128 | 0.3256 |
| FrequencyConditionedChainModel | 0.7467 | 23.1120 | 0.1245 | 0.2146 | 0.3290 |
| FrequencyConditionedChainModel_W52 | 0.7787 | 23.0872 | 0.1298 | 0.2134 | 0.3318 |
| GapLogistic | 0.8426 | 22.8529 | 0.1404 | 0.2260 | 0.3389 |
| RandomModel | 0.8024 | 23.0156 | 0.1337 | 0.2221 | 0.3327 |


Theoretical random Top6 expectation is0.8. Every frequency variant has a full-period hit difference versusRandom with an interval containing zero. Frequency-chain point estimates are lower than their2D parents. Mean winning rank is better when lower. Full0..6 hit distributions and ranking/pool metrics are exported.

Paired new-model differences against all three required references,2000 circular26-draw block bootstrap replicates, seed42. Unadjusted exploratory intervals:

| model | reference | difference | ci_low | ci_high |
|---|---|---|---|---|
| FrequencyConditionedTranslationModel_W10 | RandomModel | 0.0012 | -0.0639 | 0.0651 |
| FrequencyConditionedTranslationModel_W10 | TranslationModel | -0.0118 | -0.0769 | 0.0497 |
| FrequencyConditionedTranslationModel_W10 | GapConditionedTranslationModel | -0.0260 | -0.0994 | 0.0497 |
| FrequencyConditionedTranslationModel | RandomModel | -0.0059 | -0.0828 | 0.0710 |
| FrequencyConditionedTranslationModel | TranslationModel | -0.0189 | -0.0841 | 0.0485 |
| FrequencyConditionedTranslationModel | GapConditionedTranslationModel | -0.0331 | -0.1030 | 0.0355 |
| FrequencyConditionedTranslationModel_W52 | RandomModel | -0.0047 | -0.0757 | 0.0686 |
| FrequencyConditionedTranslationModel_W52 | TranslationModel | -0.0178 | -0.0828 | 0.0521 |
| FrequencyConditionedTranslationModel_W52 | GapConditionedTranslationModel | -0.0320 | -0.0947 | 0.0343 |
| FrequencyConditionedChainModel_W10 | RandomModel | -0.0402 | -0.1136 | 0.0343 |
| FrequencyConditionedChainModel_W10 | ChainModel | -0.0320 | -0.0982 | 0.0343 |
| FrequencyConditionedChainModel_W10 | GapConditionedChainModel | -0.0059 | -0.0698 | 0.0521 |
| FrequencyConditionedChainModel | RandomModel | -0.0556 | -0.1290 | 0.0189 |
| FrequencyConditionedChainModel | ChainModel | -0.0473 | -0.1196 | 0.0249 |
| FrequencyConditionedChainModel | GapConditionedChainModel | -0.0213 | -0.0746 | 0.0296 |
| FrequencyConditionedChainModel_W52 | RandomModel | -0.0237 | -0.0983 | 0.0497 |
| FrequencyConditionedChainModel_W52 | ChainModel | -0.0154 | -0.0970 | 0.0639 |
| FrequencyConditionedChainModel_W52 | GapConditionedChainModel | 0.0107 | -0.0533 | 0.0757 |


The direct chain ablation changes the declared source-state requirement as well as state family: Phase8 requires both predecessors in the same state; Phase7 gap chains condition on the most recent source. Earlier defaults are preserved. This is a complete-model comparison, not mathematical isolation of every eligibility change.

## Historical robustness and window selection

Multiple start points are nested slices of the original refit schedule, not a search for favorable new predictions:

| evaluation_start | FrequencyConditionedChainModel | FrequencyConditionedTranslationModel | RandomModel |
|---|---|---|---|
| 401 | 0.7467 | 0.7964 | 0.8024 |
| 501 | 0.7436 | 0.8107 | 0.8054 |
| 601 | 0.7442 | 0.8062 | 0.7984 |
| 701 | 0.7541 | 0.8037 | 0.7761 |
| 801 | 0.7191 | 0.8247 | 0.7685 |
| 901 | 0.7362 | 0.8348 | 0.7681 |


Historical block boundaries are401..682,683..964,965..1245. Frequency-model averages and differences versusRandom vary through time:

| model | block | avg_hits | delta_vs_random |
|---|---|---|---|
| FrequencyConditionedTranslationModel_W10 | early | 0.7518 | -0.1135 |
| FrequencyConditionedTranslationModel_W10 | middle | 0.8723 | 0.0957 |
| FrequencyConditionedTranslationModel_W10 | recent | 0.7865 | 0.0214 |
| FrequencyConditionedTranslationModel | early | 0.7695 | -0.0957 |
| FrequencyConditionedTranslationModel | middle | 0.7943 | 0.0177 |
| FrequencyConditionedTranslationModel | recent | 0.8256 | 0.0605 |
| FrequencyConditionedTranslationModel_W52 | early | 0.8227 | -0.0426 |
| FrequencyConditionedTranslationModel_W52 | middle | 0.7730 | -0.0035 |
| FrequencyConditionedTranslationModel_W52 | recent | 0.7972 | 0.0320 |
| FrequencyConditionedChainModel_W10 | early | 0.7801 | -0.0851 |
| FrequencyConditionedChainModel_W10 | middle | 0.7305 | -0.0461 |
| FrequencyConditionedChainModel_W10 | recent | 0.7758 | 0.0107 |
| FrequencyConditionedChainModel | early | 0.7411 | -0.1241 |
| FrequencyConditionedChainModel | middle | 0.7660 | -0.0106 |
| FrequencyConditionedChainModel | recent | 0.7331 | -0.0320 |
| FrequencyConditionedChainModel_W52 | early | 0.7979 | -0.0674 |
| FrequencyConditionedChainModel_W52 | middle | 0.7695 | -0.0071 |
| FrequencyConditionedChainModel_W52 | recent | 0.7687 | 0.0036 |


Cadence13 sensitivity refits all windows independently:

| model | evaluation_start | avg_hits | paired_ci_low | paired_ci_high |
|---|---|---|---|---|
| TranslationModel | 401 | 0.8118 | -0.0521 | 0.0698 |
| ChainModel | 401 | 0.7846 | -0.0864 | 0.0533 |
| GapConditionedTranslationModel | 401 | 0.8260 | -0.0509 | 0.0983 |
| GapConditionedChainModel | 401 | 0.7645 | -0.1101 | 0.0355 |
| FrequencyConditionedTranslationModel_W10 | 401 | 0.8059 | -0.0615 | 0.0746 |
| FrequencyConditionedTranslationModel | 401 | 0.8367 | -0.0355 | 0.1112 |
| FrequencyConditionedTranslationModel_W52 | 401 | 0.7799 | -0.0876 | 0.0462 |
| FrequencyConditionedChainModel_W10 | 401 | 0.7598 | -0.1148 | 0.0320 |
| FrequencyConditionedChainModel | 401 | 0.7479 | -0.1219 | 0.0189 |
| FrequencyConditionedChainModel_W52 | 401 | 0.7775 | -0.1006 | 0.0497 |
| GapLogistic | 401 | 0.8391 | -0.0367 | 0.1136 |
| RandomModel | 401 | 0.8024 | 0.0000 | 0.0000 |
| TranslationModel | 901 | 0.7681 | -0.1014 | 0.1072 |
| ChainModel | 901 | 0.8029 | -0.0754 | 0.1362 |
| GapConditionedTranslationModel | 901 | 0.8261 | -0.0638 | 0.1913 |
| GapConditionedChainModel | 901 | 0.7739 | -0.0870 | 0.1044 |
| FrequencyConditionedTranslationModel_W10 | 901 | 0.7826 | -0.0928 | 0.1188 |
| FrequencyConditionedTranslationModel | 901 | 0.8464 | -0.0290 | 0.1942 |
| FrequencyConditionedTranslationModel_W52 | 901 | 0.7652 | -0.1333 | 0.1333 |
| FrequencyConditionedChainModel_W10 | 901 | 0.7768 | -0.1072 | 0.1304 |
| FrequencyConditionedChainModel | 901 | 0.7333 | -0.1507 | 0.0928 |
| FrequencyConditionedChainModel_W52 | 901 | 0.7768 | -0.1014 | 0.1304 |
| GapLogistic | 901 | 0.8203 | -0.0522 | 0.1652 |
| RandomModel | 901 | 0.7681 | 0.0000 | 0.0000 |


The development-only selector uses outcomes401..900, ties26 then10 then52. At cadence26 it selected W10 Translation (development0.816; later0.7855) and W52 Chain (development0.780; later0.7768). The later901..1245 period is excluded from selection, but is not a pristine holdout after earlier project phases. These choices do not establish reliable superiority and do not replace the prospectively predeclared W26 tracks. No combination was added. Selection decisions and later metrics are exported at both cadences.

## Candidate-pool concentration

Full-period counts for at least5 main winners and all6, by pool size. These are candidate-pool containment events, not ticket prize wins:

| model | Top8_5plus | Top8_all6 | Top10_5plus | Top10_all6 | Top12_5plus | Top12_all6 | Top15_5plus | Top15_all6 |
|---|---|---|---|---|---|---|---|---|
| TranslationModel | 0 | 0 | 0 | 0 | 1 | 0 | 5 | 0 |
| ChainModel | 0 | 0 | 1 | 0 | 1 | 0 | 3 | 1 |
| GapConditionedTranslationModel | 0 | 0 | 1 | 0 | 4 | 1 | 14 | 1 |
| GapConditionedChainModel | 0 | 0 | 0 | 0 | 1 | 0 | 6 | 1 |
| FrequencyConditionedTranslationModel_W10 | 0 | 0 | 1 | 0 | 3 | 0 | 8 | 0 |
| FrequencyConditionedTranslationModel | 0 | 0 | 1 | 0 | 4 | 0 | 7 | 0 |
| FrequencyConditionedTranslationModel_W52 | 0 | 0 | 0 | 0 | 2 | 0 | 8 | 2 |
| FrequencyConditionedChainModel_W10 | 0 | 0 | 0 | 0 | 3 | 0 | 8 | 0 |
| FrequencyConditionedChainModel | 1 | 0 | 1 | 0 | 2 | 0 | 6 | 2 |
| FrequencyConditionedChainModel_W52 | 0 | 0 | 0 | 0 | 3 | 0 | 6 | 1 |
| GapLogistic | 0 | 0 | 2 | 0 | 5 | 0 | 10 | 0 |
| RandomModel | 0 | 0 | 0 | 0 | 2 | 0 | 8 | 0 |


Exact random P(pool>=5) is0.000258/0.001109/0.003322/0.011675 for Top8/10/12/15. Over845 draws these imply expected counts0.218/0.937/2.807/9.865. The primary W26 translation produced0/1/4/7 events and no all6 containment. W26 chain produced1/1/2/6 five-plus events and two Top15 all6 events. These rare counts are not proof of an advantage; all pool distributions, exact expectations, marginal intervals and paired intervals are exported. Zero-event bootstrap intervals can degenerate. Multiplicity and nested-pool dependence remain important.

## Files and reproducibility

[Methods](frequency3d-analysis.md); [predeclared protocol](superpowers/plans/2026-10-17-phase8.md). Reports are under reports/spatiotemporal_frequency/: causal historical states, count/quantile/relative support, conditional/directional/displacement tables, maximal paths, complete surrogate maxima/seeds, follow-up tables, rolling/era stability, static plots, and walk_forward_26/ plus walk_forward_13/ audits and metrics.

All actual inputs stop at1245, canonical SHA-256 `b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e`. HEAD before Phase8: `d6fde72b65e7311f5c6d532938db26a1ff353bdf`. The full suite passed245 tests with2 existing dependency skips in39.35s. Independent synthetic scalar review matched search and predictor counts/scores and verified artifact isolation. The complete pipeline also handles short histories without complete rolling windows.

## Completed global-null evidence

All199 IID and199 fixed-margin searches completed, recomputing states and quantile boundaries each time. Every surrogate used the same307,684 configurations and1,095,903,536 potential trajectory start-position candidates. No family survives correction.

| null_model | statistic | real_max | global_p | adjusted_p |
|---|---|---|---|---|
| fixed_margins | conditional | 4.5863 | 0.3800 | 1 |
| fixed_margins | directional | 3.9307 | 0.9350 | 1 |
| fixed_margins | displacement | 3.1999 | 0.7350 | 1 |
| fixed_margins | trajectory | 3.9064 | 0.3800 | 1 |
| fixed_margins | longest_trajectory | 6.0000 | 0.8700 | 1 |
| iid | conditional | 4.5863 | 0.3300 | 1 |
| iid | directional | 3.9307 | 0.9300 | 1 |
| iid | displacement | 3.1999 | 0.6600 | 1 |
| iid | trajectory | 3.9064 | 0.3200 | 1 |
| iid | longest_trajectory | 6.0000 | 0.8950 | 1 |

The five families pool ALL windows and representations; Bonferroni5 is applied within each null. All adjusted p-values are1.0. The six-point longest chain is very common among random histories' best chains: global p0.895 IID and0.870 fixed margins. Raw attractive trajectories and local peaks therefore supply no unusual structure under this search.

The Phase6(+42,-5) follow-up has COLD/NEUTRAL/HOT match rates:

| window | state_label | match_rate | local_followup_p |
|---|---|---|---|
| 10 | COLD | 0.1540 | 0.0050 |
| 10 | NEUTRAL | 0.1409 | 0.1550 |
| 10 | HOT | 0.1453 | 0.1650 |
| 26 | COLD | 0.1520 | 0.0050 |
| 26 | NEUTRAL | 0.1380 | 0.3000 |
| 26 | HOT | 0.1521 | 0.0400 |
| 52 | COLD | 0.1536 | 0.0050 |
| 52 | NEUTRAL | 0.1401 | 0.1900 |
| 52 | HOT | 0.1533 | 0.0100 |

COLD is strongest forW10; COLD andHOT are similar forW26/W52, with lower NEUTRAL rates. This is not an exclusive HOT-state relationship. Several local p-values reach0.005, but the shift was chosen in Phase6 and the complete conditional maximum has global p0.330/0.380. It is not independent preregistered evidence. Both-null local details are retained in the CSV.

Complete descriptive/null/export/plot runtime: 1039.3s (about17.3 minutes). Walk-forward cadence26 took77.0s; cadence13 took99.1s, including features and reports. Eight static plots were saved and representative heatmaps/trajectories inspected. Rolling curves suppress windows below100 source opportunities; the CSV retains their counts/rates/eligibility.

## Prospective decision

Historical selection is complete. Exactly the two predeclared quantileW26 tracks were frozen independently. No model redesign, window promotion, ensemble or threshold adjustment follows the historical results. The optional development-selected diagnostics do not justify an additional prospective track. The [prospective record](phase8-prospective.md) links the single new snapshot, exact tickets, registry and hashes. Earlier Phase5/6/7 evidence remains immutable.


The Phase8 snapshot was created once at 2026-10-17T09:18:15.127269+09:00; verified FROZEN_UNEVALUATED. All15 earlier files and canonical SHA-256 are unchanged after publication. No commit/push or target-result access occurred.
