# Phase 9 - Joint gap x W26 frequency interaction

**H6: TESTED / INCONCLUSIVE.** Neither global null-search comparisons nor leakage-safe historical ranking comparisons establish useful joint-state interaction. These are exploratory historical results, not predictive or profitability claims.

## Scope and frozen protocol

Actual canonical data: draws 1-1245 only, ending 2026-10-10. No draw-1246 result was retrieved, searched for, inspected, imported or evaluated. Prior Phase 5-8 prospective artifacts are protected by a before-work hash inventory. No commit or push was made.

The [predeclared protocol](superpowers/plans/2026-10-17-phase9.md) fixes W26, three gap bins x three frequency bins, pair support 100, chain continuation support 20, a 100-observation prior at 6/45, and top 20 positive rules. No outcome-based tuning or ensemble selection was performed. Development draws 401-900 and later draws 901-1245 are reported separately. The later historical period has already appeared in earlier phases and is not a pristine holdout.

Causal state t uses draws <t. Gap is t-1-last appearance; W26 counts draws t-26 through t-1. Both parent quantiles are fitted only on the permitted training prefix and frozen between refits. Missing states use -1. Full-history descriptive edges are gap 2/7 (LOW 0-2, MID 3-7, HIGH >=8) and W26 count 3/4 (COLD 0-3, NEUTRAL 4, HOT >=5); predictive refits learn their own edges.

## Support audit

54,854 of 56,025 historical number states have both dimensions; 7,313 of 7,470 winning source points have both. The initial W26 warmup and never-seen-number gaps are excluded rather than assigned ordinary states. Percentages below use all historical states/winning points, including missing states in the denominator.

| label | observations | winning_sources | source_opportunities_before_geometry | percent_all_states | percent_winning_sources |
| --- | --- | --- | --- | --- | --- |
| LOW x COLD | 6736 | 924 | 924 | 12.0232 | 12.3695 |
| LOW x NEUTRAL | 4578 | 623 | 623 | 8.1714 | 8.3400 |
| LOW x HOT | 7742 | 1023 | 1023 | 13.8188 | 13.6948 |
| MID x COLD | 8749 | 1158 | 1158 | 15.6162 | 15.5020 |
| MID x NEUTRAL | 4386 | 563 | 563 | 7.8286 | 7.5368 |
| MID x HOT | 5124 | 700 | 700 | 9.1459 | 9.3708 |
| HIGH x COLD | 13765 | 1821 | 1821 | 24.5694 | 24.3775 |
| HIGH x NEUTRAL | 2362 | 301 | 301 | 4.2160 | 4.0295 |
| HIGH x HOT | 1412 | 200 | 200 | 2.5203 | 2.6774 |

All nine pooled source counts exceed 100, but geometric boundaries and short eras reduce rule-specific support. Only nine chain-continuation configurations meet the required 20 observations.

## Exact search space

- 14,508 conditional translation configurations = 9 states x 52 positive draw shifts x 31 number shifts (including zero as a fixed-number reference).
- 14,508 interaction-statistic evaluations on those same configurations.
- 23,400 geometrically feasible same-state rule/chain-length configurations, including 4,212 length-3/4/5 configurations. The latter are a subset, not extra tests.
- 37,908 unique parameter tuples; 52,416 parameter/statistic cells.
- 574,565,004 possible overlapping chain start positions before pruning; these are not independent tests.
- 11,284 pooled parent-control rows, not an additional maximized search family.

All 14,508 full-history conditional pair configurations meet support 100. Descriptive chains search draw shifts 1-13 and number shifts x1-6. Predictive models retain the parent models' draw shifts 1-52 and number shifts x1-15. No arbitrary state progression or continuous four-dimensional geometry was searched.

## Strongest raw rules and parent controls

Parents use exactly the same eligible source population, with both dimensions known. Raw match rates are shown alongside joint shrinkage. Parent controls are pooled from disjoint joint-state cells.

| joint_label | delta_draw | delta_number | valid_opportunities | matches | raw_z | unconditional_rate | gap_rate | frequency_rate | match_rate | joint_shrunk_rate | interaction_lift |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HIGH x NEUTRAL | 9 | 15 | 187 | 45 | 4.3168 | 0.1384 | 0.1385 | 0.1580 | 0.2406 | 0.2033 | 0.3056 |
| HIGH x NEUTRAL | 13 | -3 | 283 | 61 | 4.0686 | 0.1387 | 0.1500 | 0.1507 | 0.2155 | 0.1941 | 0.2978 |
| MID x HOT | 26 | -15 | 462 | 91 | 4.0237 | 0.1319 | 0.1457 | 0.1406 | 0.1970 | 0.1856 | 0.2809 |

### Interaction-lift leaders

Interaction lift = joint shrunken rate / max(gap-parent shrunken rate, frequency-parent shrunken rate) - 1. It is a descriptive contrast, not a probability or statistical test. Every rate uses the same Beta-style 100-observation prior at 6/45.

| joint_label | delta_draw | delta_number | valid_opportunities | matches | raw_z | unconditional_rate | gap_rate | frequency_rate | match_rate | joint_shrunk_rate | interaction_lift |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HIGH x HOT | 4 | -14 | 136 | 31 | 3.2456 | 0.1305 | 0.1342 | 0.1406 | 0.2279 | 0.1879 | 0.3409 |
| HIGH x NEUTRAL | 47 | 12 | 204 | 43 | 3.2542 | 0.1410 | 0.1335 | 0.1388 | 0.2108 | 0.1853 | 0.3397 |
| HIGH x HOT | 43 | 15 | 127 | 27 | 2.6278 | 0.1289 | 0.1328 | 0.1317 | 0.2126 | 0.1777 | 0.3377 |

The largest interaction lift, 34.1%, is HIGH x HOT at (+4 draws, -14 numbers): 31 matches from 136 opportunities. Its shrunken rate is 0.1879 versus 0.1341 for the gap parent and 0.1401 for the frequency parent. This contrast is ordinary under equally aggressive null searches.

## Same-state chains

| state | label | start_draw | start_number | delta_draw | delta_number | chain_length | support | geometric_maximum | end_draw | end_number | overlaps_longer | nested_fragments_suppressed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | LOW x HOT | 832 | 43 | 6 | -5 | 4 | 4 | 9 | 850 | 28 | False | 2 |
| 3 | MID x COLD | 924 | 34 | 2 | -3 | 4 | 4 | 12 | 930 | 25 | False | 2 |
| 6 | HIGH x COLD | 938 | 16 | 6 | 3 | 4 | 4 | 10 | 956 | 25 | False | 2 |
| 3 | MID x COLD | 895 | 38 | 7 | -2 | 4 | 4 | 19 | 916 | 32 | False | 2 |
| 6 | HIGH x COLD | 745 | 12 | 13 | -3 | 4 | 4 | 4 | 784 | 3 | False | 2 |
| 6 | HIGH x COLD | 329 | 35 | 2 | -4 | 4 | 4 | 9 | 335 | 23 | False | 2 |

The longest detected same-joint-state chains have length four; no length-five chain was found in this bounded geometry. Nested fragments are suppressed within a longer path and overlap metadata is exported. Raw chains are not evidence by themselves. State-transition chains and unrestricted 4D/Hough geometry were deferred to avoid expanding the search beyond the stated hypothesis.

## Complete-search null comparisons

199 IID Lotto histories and 199 exact-margin constrained histories were searched with the same full protocol (seed 90042). Every surrogate recomputes causal gaps, W26 histories, both quantile boundaries and joint states. Constrained randomization preserves six per draw and exact per-number counts. Each surrogate contributes the maximum over the entire searched space for each statistic.

| null_model | statistic | real_max | null_mean | null_q95 | exceedances | replicates | global_p | adjusted_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed_margins | joint_conditional | 4.3168 | 4.1405 | 4.7525 | 53 | 199 | 0.2700 | 1.0000 |
| fixed_margins | interaction_lift | 0.3409 | 0.3710 | 0.4517 | 151 | 199 | 0.7600 | 1.0000 |
| fixed_margins | chain_continuation | 0.8771 | 1.6774 | 3.0261 | 171 | 199 | 0.8600 | 1.0000 |
| fixed_margins | longest_chain | 4.0000 | 4.2513 | 5.0000 | 199 | 199 | 1.0000 | 1.0000 |
| iid | joint_conditional | 4.3168 | 4.1333 | 4.7361 | 43 | 199 | 0.2200 | 0.8800 |
| iid | interaction_lift | 0.3409 | 0.3819 | 0.4498 | 163 | 199 | 0.8200 | 1.0000 |
| iid | chain_continuation | 0.8771 | 1.6510 | 2.8504 | 173 | 199 | 0.8700 | 1.0000 |
| iid | longest_chain | 4.0000 | 4.2513 | 5.0000 | 199 | 199 | 1.0000 | 1.0000 |

Empirical global p = (1 + surrogate maxima at least as large as real)/(199 + 1). Adjusted p applies Bonferroni across four statistic families within each null. Evidence would need to withstand both nulls. Minimum empirical resolution is 0.005. No family survives correction. The null mean maximum interaction lift is 0.3819 (IID) and 0.3710 (fixed margins), both above the real maximum 0.3409. Local z-scores and marginal Wilson intervals do not establish significance after this search.

## Matched walk-forward ranking comparison

845 targets, draws 401-1245, cadence 26, expanding training, seed 42. No target result enters fitting, binning, normalization or rule selection. All eight earlier baselines reproduce their Phase 8 score/rank/cutoff/hit outputs exactly: 6,760 rows at each cadence.

| model | avg_hits | mean_winning_rank | recall_6 | recall_10 | recall_15 | best |
| --- | --- | --- | --- | --- | --- | --- |
| TranslationModel | 0.8154 | 22.6675 | 0.1359 | 0.2274 | 0.3371 | 4 |
| ChainModel | 0.7941 | 23.0469 | 0.1323 | 0.2199 | 0.3241 | 4 |
| GapConditionedTranslationModel | 0.8296 | 22.8771 | 0.1383 | 0.2264 | 0.3428 | 3 |
| GapConditionedChainModel | 0.7680 | 23.0953 | 0.1280 | 0.2160 | 0.3320 | 3 |
| FrequencyConditionedTranslationModel | 0.7964 | 22.9535 | 0.1327 | 0.2252 | 0.3359 | 4 |
| FrequencyConditionedChainModel | 0.7467 | 23.1120 | 0.1245 | 0.2146 | 0.3290 | 4 |
| JointStateFrequencyBaseline | 0.7716 | 23.1073 | 0.1286 | 0.2205 | 0.3351 | 4 |
| JointStateTranslationModel | 0.8201 | 23.0469 | 0.1367 | 0.2201 | 0.3272 | 4 |
| JointStateChainModel | 0.7621 | 23.1256 | 0.1270 | 0.2118 | 0.3302 | 3 |
| GapLogistic | 0.8426 | 22.8529 | 0.1404 | 0.2260 | 0.3389 | 4 |
| RandomModel | 0.8024 | 23.0156 | 0.1337 | 0.2221 | 0.3327 | 3 |

### Paired uncertainty

Common-seed circular 26-draw block bootstrap, 2,000 replicates; unadjusted exploratory 95% intervals. Positive hit differences favor the joint model. All full-period hit intervals below include zero. Geometry is additionally compared with the joint-state propensity baseline.

| model | reference | difference | ci_low | ci_high |
| --- | --- | --- | --- | --- |
| JointStateFrequencyBaseline | RandomModel | -0.0308 | -0.1089 | 0.0438 |
| JointStateFrequencyBaseline | TranslationModel | -0.0438 | -0.1077 | 0.0178 |
| JointStateFrequencyBaseline | GapConditionedTranslationModel | -0.0580 | -0.1231 | 0.0059 |
| JointStateFrequencyBaseline | FrequencyConditionedTranslationModel | -0.0249 | -0.0899 | 0.0402 |
| JointStateTranslationModel | RandomModel | 0.0178 | -0.0592 | 0.0911 |
| JointStateTranslationModel | TranslationModel | 0.0047 | -0.0628 | 0.0710 |
| JointStateTranslationModel | GapConditionedTranslationModel | -0.0095 | -0.0734 | 0.0533 |
| JointStateTranslationModel | FrequencyConditionedTranslationModel | 0.0237 | -0.0462 | 0.0899 |
| JointStateTranslationModel | JointStateFrequencyBaseline | 0.0485 | -0.0166 | 0.1136 |
| JointStateChainModel | RandomModel | -0.0402 | -0.1136 | 0.0331 |
| JointStateChainModel | ChainModel | -0.0320 | -0.1136 | 0.0497 |
| JointStateChainModel | GapConditionedChainModel | -0.0059 | -0.0627 | 0.0473 |
| JointStateChainModel | FrequencyConditionedChainModel | 0.0154 | -0.0237 | 0.0533 |
| JointStateChainModel | JointStateFrequencyBaseline | -0.0095 | -0.0793 | 0.0686 |

The joint translation point estimate is above its 2D and frequency parents but below its gap parent. The joint chain point estimate is below its 2D and gap parents. Neither establishes improvement beyond both single-state parents or beyond the non-geometric propensity baseline.

## Candidate-pool concentration

Counts among the same 845 targets; each cell reports >=5-main-winner events and all-six events independently. Complete distributions, >=3/>=4 rates, exact hypergeometric expectations, marginal intervals and paired comparisons are exported in pools.csv. Isolated rare events are not evidence of predictability.

| model | pool_size | count_5plus | count_6plus | exact_random_5plus | exact_random_6plus |
| --- | --- | --- | --- | --- | --- |
| JointStateFrequencyBaseline | 8 | 0 | 0 | 0.0003 | 0.0000 |
| JointStateFrequencyBaseline | 10 | 1 | 0 | 0.0011 | 0.0000 |
| JointStateFrequencyBaseline | 12 | 4 | 0 | 0.0033 | 0.0001 |
| JointStateFrequencyBaseline | 15 | 13 | 1 | 0.0117 | 0.0006 |
| JointStateTranslationModel | 8 | 0 | 0 | 0.0003 | 0.0000 |
| JointStateTranslationModel | 10 | 1 | 0 | 0.0011 | 0.0000 |
| JointStateTranslationModel | 12 | 2 | 0 | 0.0033 | 0.0001 |
| JointStateTranslationModel | 15 | 9 | 0 | 0.0117 | 0.0006 |
| JointStateChainModel | 8 | 0 | 0 | 0.0003 | 0.0000 |
| JointStateChainModel | 10 | 1 | 0 | 0.0011 | 0.0000 |
| JointStateChainModel | 12 | 2 | 0 | 0.0033 | 0.0001 |
| JointStateChainModel | 15 | 6 | 0 | 0.0117 | 0.0006 |
| RandomModel | 8 | 0 | 0 | 0.0003 | 0.0000 |
| RandomModel | 10 | 0 | 0 | 0.0011 | 0.0000 |
| RandomModel | 12 | 2 | 0 | 0.0033 | 0.0001 |
| RandomModel | 15 | 8 | 0 | 0.0117 | 0.0006 |

## Robustness and later evaluation

Nested evaluation starts 401/501/601/701/801/901 retain the original refit calendar rather than creating different fitting schedules. All ranking, pool, hit-distribution and paired exports are available for these starts.

### Cadence 13 sensitivity and later period

| model | evaluation_start | targets | avg_hits | delta_vs_random | paired_ci_low | paired_ci_high |
| --- | --- | --- | --- | --- | --- | --- |
| JointStateFrequencyBaseline | 401 | 845 | 0.7586 | -0.0438 | -0.1183 | 0.0308 |
| JointStateTranslationModel | 401 | 845 | 0.8260 | 0.0237 | -0.0509 | 0.1018 |
| JointStateChainModel | 401 | 845 | 0.7621 | -0.0402 | -0.1101 | 0.0320 |
| RandomModel | 401 | 845 | 0.8024 | 0.0000 | 0.0000 | 0.0000 |
| JointStateFrequencyBaseline | 901 | 345 | 0.7420 | -0.0261 | -0.1449 | 0.0957 |
| JointStateTranslationModel | 901 | 345 | 0.8000 | 0.0319 | -0.0957 | 0.1710 |
| JointStateChainModel | 901 | 345 | 0.7710 | 0.0029 | -0.1072 | 0.1188 |
| RandomModel | 901 | 345 | 0.7681 | 0.0000 | 0.0000 | 0.0000 |

### Cadence 26 later period (901-1245)

| model | targets | avg_hits | delta_vs_random | paired_ci_low | paired_ci_high |
| --- | --- | --- | --- | --- | --- |
| JointStateFrequencyBaseline | 345 | 0.7478 | -0.0203 | -0.1420 | 0.1043 |
| JointStateTranslationModel | 345 | 0.8145 | 0.0464 | -0.0725 | 0.1768 |
| JointStateChainModel | 345 | 0.7652 | -0.0029 | -0.1159 | 0.1130 |
| RandomModel | 345 | 0.7681 | 0.0000 | 0.0000 | 0.0000 |

### Historical eras

| model | block | start_draw | end_draw | avg_hits | delta_vs_random |
| --- | --- | --- | --- | --- | --- |
| JointStateFrequencyBaseline | early | 401 | 682 | 0.8298 | -0.0355 |
| JointStateFrequencyBaseline | middle | 683 | 964 | 0.7447 | -0.0319 |
| JointStateFrequencyBaseline | recent | 965 | 1245 | 0.7402 | -0.0249 |
| JointStateTranslationModel | early | 401 | 682 | 0.8227 | -0.0426 |
| JointStateTranslationModel | middle | 683 | 964 | 0.8298 | 0.0532 |
| JointStateTranslationModel | recent | 965 | 1245 | 0.8078 | 0.0427 |
| JointStateChainModel | early | 401 | 682 | 0.7518 | -0.1135 |
| JointStateChainModel | middle | 683 | 964 | 0.7908 | 0.0142 |
| JointStateChainModel | recent | 965 | 1245 | 0.7438 | -0.0214 |
| RandomModel | early | 401 | 682 | 0.8652 | 0.0000 |
| RandomModel | middle | 683 | 964 | 0.7766 | 0.0000 |
| RandomModel | recent | 965 | 1245 | 0.7651 | 0.0000 |

### Postselected rule stability

The strongest interaction rule HIGH x HOT (+4,-14) has only 43-47 opportunities in each era, below the required 100. All 260-draw rolling windows for that rule are also below 100; the plot marks these as subthreshold descriptive estimates. These data cannot establish stability or a reliable changing trend. Descriptive full-history boundaries and postselection make these plots unsuitable as independent predictive validation.

| era | valid_opportunities | matches | match_rate | interaction_lift | search_eligible |
| --- | --- | --- | --- | --- | --- |
| early | 45 | 14 | 0.3111 | 0.3938 | False |
| middle | 43 | 9 | 0.2093 | 0.1096 | False |
| recent | 47 | 8 | 0.1702 | -0.0374 | False |

## Artifacts, runtime and verification

Reports: `reports/spatiotemporal_joint/`, with complete score/rank audits under `walk_forward_26/` and `walk_forward_13/`. Eight static plots under `plots/` cover support, LOW x COLD/HIGH x HOT translations, parent comparison, interaction map, rolling stability, selected chain and null maxima.

Descriptive and 398-surrogate search: 293.0 seconds. Cadence-26 experiment: 106.5 seconds. Cadence-13 experiment: 156.8 seconds. Timings exclude the test suite and final prospective freeze. Null runtime is configurable; no dependency installation or network access was required.

Full regression verification: **265 passed, 2 existing dependency-related skips**, 40.14 seconds. Focused synthetic publisher/backtest/plot verification after plot readability changes: 6 passed, 3.15 seconds. Independent code review checked causal timing, parent denominators, null maxima and publisher integrity; its baseline-score consistency finding was fixed and regression-tested.

The prospective decision is fixed: freeze only JointStateFrequencyBaseline, JointStateTranslationModel and JointStateChainModel as separate experimental tracks. No combination is justified. Each preserves full scores/ranks, Top6/8/10/12/15, direct Top6 and seeded weighted/coverage portfolios of 5/10/20 tickets. The [Phase 9 prospective record](phase9-prospective.md) is written after the one-time publication. Prior Phase 5-8 evidence remains immutable.

Publication completed once: **draw1246_phase9_joint4dstate_20261017T094322096047_14004a94**, status **FROZEN_UNEVALUATED**. The [prospective record](phase9-prospective.md) contains the frozen rankings, portfolio links and hashes. All 20 earlier prospective files and the canonical dataset were verified unchanged afterward. The geometric tracks each have a 44-number tie, resolved by the predeclared smaller-number-first rule; these low-number fallback ranks are not evidence of preference. No models or settings were changed after publication.
