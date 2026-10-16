# Phase7 historical results

H4 ? Gap-conditioned 3D translational patterns: **TESTED / INCONCLUSIVE**.

No tested structure survives global null-search correction, and no primary conditioned model establishes predictive improvement. Model settings and the two primary prospective tracks were predeclared before examining outcomes. No combination or representation winner was selected. No draw1246 result was retrieved, inspected, imported, searched for, or evaluated.

## Scope and causal states

Canonical history: draws1?1245, latest2026-10-10; binary matrix1245 by45; main numbers only. SHA-256: `b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e`. The sparse historical table contains56,025 number/target rows.

Gap for target t is t-1 minus the last appearance draw. There are55,665 known pre-states and360 never-seen states, explicitly excluded. Gap min0, max73, median4, 95th percentile21, 99th percentile33. Coarse descriptive bins are0?2,3?7,8+; exact/clipped cap21; relative bins <=0.5, (0.5,1.5], >1.5. Predictive thresholds are fitted separately on each training prefix.

| representation | state | observations | winning_source_points |
|---|---|---|---|
| quantile | -1 | 360 | 45 |
| quantile | 0 | 19418 | 2633 |
| quantile | 1 | 18537 | 2448 |
| quantile | 2 | 17710 | 2344 |

## Exact search space

Searches use dt1?52, dn?1?15 for conditional/destination pairs; zero number displacement is excluded by the translational protocol. True3D and trajectories use dt1?13, dn?1?6, clipped-gap displacement-3..3.

- Conditional source tests:43,680 across all three representations;34,492 supported.
- Source/destination coarse-bin tests:14,040; all supported; DESCRIPTIVE ONLY.
- True3D displacement tests:1,092; all supported; DESCRIPTIVE ONLY.
- Trajectory length3/4/5 tuples:4,680;444 supported for continuation scores.
- All geometrically possible trajectory rule/length tuples:18,772, including lengths beyond5.
- Total unique parameter configurations:77,584 (do not add the length3/4/5 subset again).
- Trajectory rule/length/start-position opportunities:518,137,360 before outcome pruning. These overlap and are not independent tests.

Null caps ranged19?22 under the same training-derived recipe, with73,736?79,456 total configurations per surrogate. Complete search uses that same adaptive recipe for every history. Minimum support100 for pairs,20 for trajectory continuation; longest trajectory has its own maximum correction. Optional3D Hough search was deferred because its intercept family would add poorly interpretable sparse searches.

## Strongest descriptive observations

The strongest source-conditioned shift is (+50,+4), clipped source gap3:105 matches/535 opportunities, rate0.1963, lift1.4720, raw z4.2818. Its early/middle/recent rates are0.1871/0.2079/0.2025; these are post-selection descriptive checks, not independent validation.

| representation | gap_state | delta_draw | delta_number | valid_opportunities | matches | match_rate | raw_z |
|---|---|---|---|---|---|---|---|
| clipped | 3 | 50 | 4 | 535 | 105 | 0.1963 | 4.2818 |
| relative | 1 | 1 | 8 | 2185 | 357 | 0.1634 | 4.1326 |
| clipped | 4 | 20 | 3 | 510 | 99 | 0.1941 | 4.0381 |
| quantile | 1 | 1 | 8 | 2027 | 332 | 0.1638 | 4.0336 |
| clipped | 5 | 25 | 3 | 439 | 87 | 0.1982 | 3.9968 |


Strongest true3D displacement: (+13,-4,+2 clipped-gap units),70/350=0.2000, raw z3.6690. Saturated clipped-gap changes are not necessarily raw-gap changes. Destination conditions are never predictive inputs.

Longest same-state trajectory:6 points, high gap, (draw523,number45) to(draw533,number15), displacement(+2,-6), raw starting gap38, clipped21, geometric maximum8. Nested fragments are suppressed. Longest exact repeated clipped-gap trajectory has4 points; a nonzero-gap example starts(draw1138,number16,gap9), displacement(+8,+3,-2), ending(draw1162,number25,gap3).

Strongest supported trajectory continuation: medium state, (+10,+3), length3,10/31 continuations, raw z3.0997. Raw support and the longest path are separately null-calibrated.

The Phase6 (+42,-5) follow-up remains positive in every coarse state, strongest in high gaps: low0.1470, medium0.1439, high0.1579 versus IID0.1333. The high-state local follow-up p is0.005 for each null (the Monte Carlo floor), but the rule was selected from Phase6 history and the complete conditional search is not unusual. This is not independently preregistered evidence.

## Complete-search null comparisons

199 IID six-of45 histories and199 exact-margin randomized histories; seed70042. Gaps, historical mean intervals, clipping caps, and bins are recomputed for every surrogate. Fixed margins use20*T curveball trades; finite mixing is approximate. Five statistic families are Bonferroni-corrected separately within each null, and evidence must survive both nulls.

| null_model | statistic | real_max | global_p | adjusted_p |
|---|---|---|---|---|
| fixed_margins | conditional | 4.2818 | 0.5850 | 1.0000 |
| fixed_margins | destination | 4.5044 | 0.1000 | 0.5000 |
| fixed_margins | displacement | 3.6690 | 0.2450 | 1.0000 |
| fixed_margins | trajectory | 3.0997 | 0.7900 | 1.0000 |
| fixed_margins | longest_trajectory | 6.0000 | 0.1250 | 0.6250 |
| iid | conditional | 4.2818 | 0.6250 | 1.0000 |
| iid | destination | 4.5044 | 0.1450 | 0.7250 |
| iid | displacement | 3.6690 | 0.2300 | 1.0000 |
| iid | trajectory | 3.0997 | 0.7350 | 1.0000 |
| iid | longest_trajectory | 6.0000 | 0.1050 | 0.5250 |


None survives correction. Empirical raw resolution0.005, adjusted resolution0.025. A selected local peak is not a corrected discovery. The full search and exports took601.6 seconds; plots add a few seconds.

## Walk-forward ranking comparison

Targets401?1245 (845 draws), expanding history, refit every26 draws, seed42. All scores precede target outcome access. Gap Logistic and both2D parents retain their previous defaults. The new pair/chain models require100/20 opportunities and condition only on the most recent source pre-gap.

| model | avg_hits | mean_winning_rank | recall_6 | recall_10 | recall_15 |
|---|---|---|---|---|---|
| TranslationModel | 0.8154 | 22.6675 | 0.1359 | 0.2274 | 0.3371 |
| ChainModel | 0.7941 | 23.0469 | 0.1323 | 0.2199 | 0.3241 |
| GapConditionedTranslationModel | 0.8296 | 22.8771 | 0.1383 | 0.2264 | 0.3428 |
| GapConditionedChainModel | 0.7680 | 23.0953 | 0.1280 | 0.2160 | 0.3320 |
| GapLogistic | 0.8426 | 22.8529 | 0.1404 | 0.2260 | 0.3389 |
| RandomModel | 0.8024 | 23.0156 | 0.1337 | 0.2221 | 0.3327 |


The theoretical average Top6 hit count is0.8. Larger mean winning rank is worse. Gap conditioning slightly improves translation Top6 hits but worsens its mean winning rank; it reduces chain Top6 hits. No reliable advantage is established.

Paired95% intervals below use2000 circular26-draw block bootstrap replicates, shared resampling seed42. They are unadjusted exploratory intervals. The legacy comparison.csv preserves its existing bootstrap seed streams, so its Monte Carlo endpoints differ slightly; paired_2d_3d.csv is the common-seed comparison for new models.

| model | reference | evaluation_start | difference | ci_low | ci_high |
|---|---|---|---|---|---|
| GapConditionedTranslationModel | RandomModel | 401 | 0.0272 | -0.0497 | 0.1030 |
| GapConditionedTranslationModel | TranslationModel | 401 | 0.0142 | -0.0521 | 0.0769 |
| GapConditionedChainModel | RandomModel | 401 | -0.0343 | -0.1065 | 0.0343 |
| GapConditionedChainModel | ChainModel | 401 | -0.0260 | -0.0970 | 0.0462 |
| GapConditionedTranslationModel | RandomModel | 901 | 0.0899 | -0.0290 | 0.2116 |
| GapConditionedTranslationModel | TranslationModel | 901 | 0.0812 | -0.0146 | 0.1826 |
| GapConditionedChainModel | RandomModel | 901 | -0.0058 | -0.1044 | 0.0957 |
| GapConditionedChainModel | ChainModel | 901 | -0.0725 | -0.1652 | 0.0203 |


Later targets901?1245 are later than the declared development window401?900, but are not a pristine holdout after earlier phases. No hyperparameters or model choice were tuned on these results.

## State ablations and robustness

All three representations use the same predeclared settings; coarse bins remain primary. These are fixed comparisons, not a search for new thresholds.

| model | avg_hits | mean_winning_rank |
|---|---|---|
| TranslationModel | 0.8154 | 22.6675 |
| ChainModel | 0.7941 | 23.0469 |
| GapConditionedTranslationModel | 0.8296 | 22.8771 |
| GapConditionedChainModel | 0.7680 | 23.0953 |
| GapConditionedTranslationModel_clipped | 0.7953 | 22.9095 |
| GapConditionedTranslationModel_relative | 0.8201 | 23.0037 |
| GapConditionedChainModel_clipped | 0.7515 | 23.0858 |
| GapConditionedChainModel_relative | 0.7929 | 22.9456 |
| GapLogistic | 0.8426 | 22.8529 |
| RandomModel | 0.8024 | 23.0156 |


Historical start points are nested slices of the same prediction run, preserving its refit calendar. This avoids silently changing predictions when selecting a reporting period.

| evaluation_start | GapConditionedChainModel | GapConditionedTranslationModel | RandomModel |
|---|---|---|---|
| 401 | 0.7680 | 0.8296 | 0.8024 |
| 501 | 0.7705 | 0.8161 | 0.8054 |
| 601 | 0.7721 | 0.8202 | 0.7984 |
| 701 | 0.7541 | 0.8239 | 0.7761 |
| 801 | 0.7393 | 0.8225 | 0.7685 |
| 901 | 0.7623 | 0.8580 | 0.7681 |


Early/middle/recent blocks of the full walk-forward run:

| model | block | start_draw | end_draw | avg_hits | delta_vs_random |
|---|---|---|---|---|---|
| TranslationModel | early | 401 | 682 | 0.8546 | -0.0106 |
| TranslationModel | middle | 683 | 964 | 0.8298 | 0.0532 |
| TranslationModel | recent | 965 | 1245 | 0.7616 | -0.0036 |
| ChainModel | early | 401 | 682 | 0.7482 | -0.1170 |
| ChainModel | middle | 683 | 964 | 0.8121 | 0.0355 |
| ChainModel | recent | 965 | 1245 | 0.8221 | 0.0569 |
| GapConditionedTranslationModel | early | 401 | 682 | 0.8546 | -0.0106 |
| GapConditionedTranslationModel | middle | 683 | 964 | 0.7801 | 0.0035 |
| GapConditionedTranslationModel | recent | 965 | 1245 | 0.8541 | 0.0890 |
| GapConditionedChainModel | early | 401 | 682 | 0.7695 | -0.0957 |
| GapConditionedChainModel | middle | 683 | 964 | 0.7766 | 0.0000 |
| GapConditionedChainModel | recent | 965 | 1245 | 0.7580 | -0.0071 |
| GapLogistic | early | 401 | 682 | 0.8404 | -0.0248 |
| GapLogistic | middle | 683 | 964 | 0.8511 | 0.0745 |
| GapLogistic | recent | 965 | 1245 | 0.8363 | 0.0712 |
| RandomModel | early | 401 | 682 | 0.8652 | 0.0000 |
| RandomModel | middle | 683 | 964 | 0.7766 | 0.0000 |
| RandomModel | recent | 965 | 1245 | 0.7651 | 0.0000 |


The translation gain over Random is concentrated in the recent block; its first block is slightly negative. The gap-conditioned chain is nonpositive in all three blocks. The13-draw cadence sensitivity independently refits primary models:

| model | evaluation_start | avg_hits | paired_ci_low | paired_ci_high |
|---|---|---|---|---|
| TranslationModel | 401 | 0.8118 | -0.0521 | 0.0698 |
| ChainModel | 401 | 0.7846 | -0.0864 | 0.0533 |
| GapConditionedTranslationModel | 401 | 0.8260 | -0.0509 | 0.0983 |
| GapConditionedChainModel | 401 | 0.7645 | -0.1101 | 0.0355 |
| GapLogistic | 401 | 0.8391 | -0.0367 | 0.1136 |
| RandomModel | 401 | 0.8024 | 0.0000 | 0.0000 |
| TranslationModel | 901 | 0.7681 | -0.1014 | 0.1072 |
| ChainModel | 901 | 0.8029 | -0.0754 | 0.1362 |
| GapConditionedTranslationModel | 901 | 0.8261 | -0.0638 | 0.1913 |
| GapConditionedChainModel | 901 | 0.7739 | -0.0870 | 0.1044 |
| GapLogistic | 901 | 0.8203 | -0.0522 | 0.1652 |
| RandomModel | 901 | 0.7681 | 0.0000 | 0.0000 |


No primary positive hit difference survives paired uncertainty across these protocols. Cadence26 with all ablations took70.9s; cadence13 with primary models took54.9s, including feature generation and reports.

## Candidate-pool concentration

Counts of targets containing at least5 main winners, and all6; full period845 draws, cadence26. The machine-readable pool report also includes complete0?6 distributions, exact hypergeometric expectations, marginal intervals, and paired differences.

| model | pool_size | count_5plus | count_6plus |
|---|---|---|---|
| TranslationModel | 8 | 0 | 0 |
| TranslationModel | 10 | 0 | 0 |
| TranslationModel | 12 | 1 | 0 |
| TranslationModel | 15 | 5 | 0 |
| ChainModel | 8 | 0 | 0 |
| ChainModel | 10 | 1 | 0 |
| ChainModel | 12 | 1 | 0 |
| ChainModel | 15 | 3 | 1 |
| GapConditionedTranslationModel | 8 | 0 | 0 |
| GapConditionedTranslationModel | 10 | 1 | 0 |
| GapConditionedTranslationModel | 12 | 4 | 1 |
| GapConditionedTranslationModel | 15 | 14 | 1 |
| GapConditionedChainModel | 8 | 0 | 0 |
| GapConditionedChainModel | 10 | 0 | 0 |
| GapConditionedChainModel | 12 | 1 | 0 |
| GapConditionedChainModel | 15 | 6 | 1 |
| GapLogistic | 8 | 0 | 0 |
| GapLogistic | 10 | 2 | 0 |
| GapLogistic | 12 | 5 | 0 |
| GapLogistic | 15 | 10 | 0 |
| RandomModel | 8 | 0 | 0 |
| RandomModel | 10 | 0 | 0 |
| RandomModel | 12 | 2 | 0 |
| RandomModel | 15 | 8 | 0 |


Exact random P(pool>=5): Top8=0.000258, Top10=0.001109, Top12=0.003322, Top15=0.011675. Expected event counts over845 draws are0.218,0.937,2.807,9.865. Exact all6 probabilities are0.00000344,0.00002578,0.00011344,0.00061447 respectively.

The primary conditioned translation has14 Top15 five-plus events versus8 for seeded Random, but the paired rate difference0.00710 has interval[-0.00473,0.02130]. Its Top12 difference0.00237 has interval[-0.00355,0.00828]. Isolated all6 pool events are not six-match tickets or proof of an advantage. Some sparse comparisons with the2D parent have bootstrap bounds at zero; multiple search, small event counts, and non-independent nested pools prevent significance claims.

## Outputs and prospective boundary

[Method details](gap3d-analysis.md), [predeclared plan](superpowers/plans/2026-10-17-phase7.md). Reports live in reports/spatiotemporal3d/: historical states, gap distribution/support, every conditional/destination/displacement test, maximal trajectories, global null maxima with seeds/search counts, selected-rule temporal stability, follow-up tables, and seven plots. walk_forward_26/ and walk_forward_13/ retain full score/ranking audits, metrics, pool distributions, paired parent comparisons, eras, and protocols.

Only the two predeclared coarse-bin models are frozen independently under reports/prospective/phase7/. Weighted and coverage portfolios use Top12, seed42, unique nested budgets1/5/10/20 plus directTop6. No combination or ablation winner is frozen. Prior Phase5/6 artifacts and both earlier registries remain immutable. A separate freeze record links the final artifacts and hashes. No draw1246 result is accessed.


## Verification and publication

Full suite:212 passed,2 existing dependency skips,56.01s. Final focused checks:17 passed. Independent review reproduced model counts/scores using scalar synthetic calculations and checked artifact publication.

The [separate Phase7 freeze](phase7-prospective.md) was created once at2026-10-17T08:48:08.689811+09:00. It preserves both predeclared primary tracks and remains FROZEN_UNEVALUATED. All10 earlier prospective files and the canonical dataset SHA-256 remain unchanged. No commit/push or future-result access occurred.
