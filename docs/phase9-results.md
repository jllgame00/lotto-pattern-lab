# Phase 9 — Gap × frequency interaction 결과

## 결론

**H6: TESTED / INCONCLUSIVE.** global null-search와 leakage-safe ranking에서 유용한 joint interaction을 확립하지 못했습니다. 탐색적 역사 결과이며 예측력·수익성 주장이 아닙니다.

## 가설

gap과 W26 frequency를 함께 조건화한 상태가 두 단일 상태 parent보다 유용한지 검증했습니다.

## 데이터 및 검증 범위

canonical 1-1245,마지막2026-10-10만 사용했습니다. 당시1246 결과를 가져오기·검색·확인·import·평가하지 않았고 Phase 5-8 hash inventory를 보호했습니다. 당시 commit/push는 없었습니다.

## 방법

[당시 protocol](superpowers/plans/2026-10-17-phase9.md)은 W26·gap 3 bins ×frequency3 bins·pair100·continuation20·6/45의 prior 100·positive top20을 고정했습니다. outcome tuning·ensemble selection은 없습니다. development 401-900·later 901-1245를 분리하며 later도 앞선 연구에 사용되어 pristine holdout은 아닙니다.

state t는 draws<t만 사용합니다. gap=t-1-last appearance,W26=t-26..t-1입니다. 두 quantile은 training-only이며 refit 사이 고정,missing=-1입니다. full-history descriptive edge는 gap 2/7(LOW0-2,MID3-7,HIGH>=8),W26 count 3/4(COLD0-3,NEUTRAL4,HOT>=5)이고 predictive는 자체 refit합니다.

## Support audit

historical56,025 중54,854 states와7,470 중7,313 winning sources에 두 차원이 있습니다. W26 warmup·never-seen gap은 ordinary state로 바꾸지 않고 제외합니다. 아래 percentage는 missing 포함 전체 state/source를 분모로 합니다.

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

pooled 아홉 source count는100 초과지만 geometry·short era가 rule support를 줄입니다. continuation은 아홉 configurations만20 observations를 충족합니다.

## 정확한 탐색 범위

- conditional14,508 =9 states×52 positive dt×31 dn(zero reference 포함)입니다.
- 같은 tuple의 interaction14,508 evaluations입니다.
- geometric chain23,400 중 length3/4/5의4,212는 subset입니다.
- unique37,908·statistic cells52,416입니다.
- pruning 전574,565,004 overlapping starts는 독립 검정이 아닙니다.
- parent11,284 rows는 추가 maximized family가 아닙니다.

full-history14,508 pairs는 support 100입니다. descriptive chain dt1-13,dn±1-6,predictive는 parent의dt1-52,dn±1-15를 유지합니다. 임의 state progression·continuous 4D geometry는 탐색하지 않았습니다.

## 주요 결과와 parent control

두 차원이 알려진 같은 source population을 사용하고 disjoint joint cell에서 parent를 pooling합니다. raw rate와 joint shrinkage를 함께 표시합니다.

| joint_label | delta_draw | delta_number | valid_opportunities | matches | raw_z | unconditional_rate | gap_rate | frequency_rate | match_rate | joint_shrunk_rate | interaction_lift |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HIGH x NEUTRAL | 9 | 15 | 187 | 45 | 4.3168 | 0.1384 | 0.1385 | 0.1580 | 0.2406 | 0.2033 | 0.3056 |
| HIGH x NEUTRAL | 13 | -3 | 283 | 61 | 4.0686 | 0.1387 | 0.1500 | 0.1507 | 0.2155 | 0.1941 | 0.2978 |
| MID x HOT | 26 | -15 | 462 | 91 | 4.0237 | 0.1319 | 0.1457 | 0.1406 | 0.1970 | 0.1856 | 0.2809 |

### Interaction-lift 최대

Interaction lift=joint shrunken rate/max(gap-parent shrunken rate,frequency-parent shrunken rate)-1입니다. 확률·검정이 아닌 기술 contrast이며 모두6/45의 Beta-style100 prior를 사용합니다.

| joint_label | delta_draw | delta_number | valid_opportunities | matches | raw_z | unconditional_rate | gap_rate | frequency_rate | match_rate | joint_shrunk_rate | interaction_lift |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HIGH x HOT | 4 | -14 | 136 | 31 | 3.2456 | 0.1305 | 0.1342 | 0.1406 | 0.2279 | 0.1879 | 0.3409 |
| HIGH x NEUTRAL | 47 | 12 | 204 | 43 | 3.2542 | 0.1410 | 0.1335 | 0.1388 | 0.2108 | 0.1853 | 0.3397 |
| HIGH x HOT | 43 | 15 | 127 | 27 | 2.6278 | 0.1289 | 0.1328 | 0.1317 | 0.2126 | 0.1777 | 0.3377 |

최대 lift34.1%는 HIGH×HOT의(+4,-14),31/136입니다. shrunken0.1879 대 gap 0.1341·frequency0.1401이며 동일하게 강한 null 탐색에서 보통 수준입니다.

## Same-state chain

| state | label | start_draw | start_number | delta_draw | delta_number | chain_length | support | geometric_maximum | end_draw | end_number | overlaps_longer | nested_fragments_suppressed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | LOW x HOT | 832 | 43 | 6 | -5 | 4 | 4 | 9 | 850 | 28 | False | 2 |
| 3 | MID x COLD | 924 | 34 | 2 | -3 | 4 | 4 | 12 | 930 | 25 | False | 2 |
| 6 | HIGH x COLD | 938 | 16 | 6 | 3 | 4 | 4 | 10 | 956 | 25 | False | 2 |
| 3 | MID x COLD | 895 | 38 | 7 | -2 | 4 | 4 | 19 | 916 | 32 | False | 2 |
| 6 | HIGH x COLD | 745 | 12 | 13 | -3 | 4 | 4 | 4 | 784 | 3 | False | 2 |
| 6 | HIGH x COLD | 329 | 35 | 2 | -4 | 4 | 4 | 9 | 335 | 23 | False | 2 |

최장 같은 joint-state는 four points,이 범위에서 length-five는 없습니다. 긴 path 안 nested fragment를 억제하고 overlap metadata를 저장합니다. raw chain만으로 증거가 아니며 state transition·unrestricted4D/Hough는 범위 확장을 막기 위해 보류했습니다.

## Null / surrogate 비교

199 IID·199 exact-margin에 동일 protocol,seed 90042입니다. causal gap·W26·두 quantile·joint state를 매번 재계산합니다. six per draw·per-number exact count를 보존하며 statistic별 전체 maximum을 남깁니다.

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

global p=(1+real 이상 surrogate maxima)/(199+1)이며 null별 네 family Bonferroni입니다. 두 null 모두 통과해야 하나 통과 family는 없습니다. 최소 resolution0.005입니다. null mean max lift는 IID0.3819·fixed0.3710으로 real0.3409보다 큽니다. local z·marginal Wilson은 탐색 후 유의성을 확립하지 않습니다.

## Walk-forward 결과

401-1245의845 targets,cadence 26,expanding training,seed 42입니다. target은 fit·binning·normalization·selection에 들어가지 않습니다. 기존 여덟 baseline은 Phase 8의 cadence별6,760 rows를 score/rank/cutoff/hit까지 재현합니다.

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

### Paired 불확실성

common-seed circular26-draw block bootstrap 2,000회,unadjusted95%입니다. positive 차이는 joint 우세이며 full-period interval 모두 zero를 포함합니다. geometry는 joint propensity와도 비교합니다.

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

joint Translation은2D/frequency parent보다 높으나 gap보다 낮고 Chain은2D/gap보다 낮습니다. 두 single-state parent나 propensity를 넘어서는 개선은 확립되지 않았습니다.

## Candidate-pool / prize-aware 결과

같은845 targets의 >=5·all-six를 각기 집계합니다. full distribution·>=3/>=4·exact hypergeometric·marginal/paired interval은 pools.csv입니다. 개별 rare event는 예측 근거가 아닙니다.

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

## 시간 robustness와 later 평가

nested starts401/501/601/701/801/901은 원래 refit calendar를 유지합니다. 각 start의 ranking·pool·hit distribution·paired export를 저장합니다.

### Cadence 13 sensitivity와 later

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

### Cadence 26 later (901-1245)

| model | targets | avg_hits | delta_vs_random | paired_ci_low | paired_ci_high |
| --- | --- | --- | --- | --- | --- |
| JointStateFrequencyBaseline | 345 | 0.7478 | -0.0203 | -0.1420 | 0.1043 |
| JointStateTranslationModel | 345 | 0.8145 | 0.0464 | -0.0725 | 0.1768 |
| JointStateChainModel | 345 | 0.7652 | -0.0029 | -0.1159 | 0.1130 |
| RandomModel | 345 | 0.7681 | 0.0000 | 0.0000 | 0.0000 |

### Historical era

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

### 사후 선택 rule의 안정성

최대 interaction HIGH×HOT(+4,-14)는 era별43-47 opportunities로100 미만입니다. 260-draw rolling도 모두100 미만이며 plot에서 subthreshold 기술값으로 표시합니다. 안정성·변화 trend를 확립하지 못하고 full-history 경계·postselection 때문에 독립 prediction validation이 아닙니다.

| era | valid_opportunities | matches | match_rate | interaction_lift | search_eligible |
| --- | --- | --- | --- | --- | --- |
| early | 45 | 14 | 0.3111 | 0.3938 | False |
| middle | 43 | 9 | 0.2093 | 0.1096 | False |
| recent | 47 | 8 | 0.1702 | -0.0374 | False |

## 출력·runtime·검증

`reports/spatiotemporal_joint/`와 walk_forward_26/·walk_forward_13/에 full audit를 저장했습니다. 8 plots는 support·LOW×COLD/HIGH×HOT·parent·interaction·rolling·chain·null maximum입니다.

descriptive/398-surrogate293.0 seconds,cadence 26 106.5 seconds,cadence 13 156.8 seconds입니다. test·freeze 제외이며 null budget은 조절 가능합니다. dependency 설치·network는 필요하지 않았습니다.

당시 전체 **265 passed,2 dependency skips**,40.14 seconds였습니다. plot 가독성 후 focused6 passed,3.15 seconds입니다. 독립 review는 causal timing·parent denominator·null maximum·publisher integrity를 검토했고 baseline-score consistency 문제를 regression으로 수정했습니다.

## Prospective experiment

JointStateFrequencyBaseline·JointStateTranslationModel·JointStateChainModel만 독립 동결하고 조합은 정당화하지 않았습니다. full score/rank·Top6/8/10/12/15·directTop6·seeded weighted/coverage5/10/20을 보존합니다. [원본 기록](phase9-prospective.md)을 연결하며 Phase 5-8은 보호합니다.

한 번 생성한 ID는 **draw 1246_phase9_joint4dstate_20261017T094322096047_14004a94**,상태는 **FROZEN_UNEVALUATED**입니다. [원본](phase9-prospective.md)에 순위·ticket link·hash가 있습니다. 당시 이전20파일·canonical이 전후 같았습니다. geometric track의44-number tie는 작은 번호 우선으로 정렬해 low-number fallback은 선호 증거가 아닙니다. publication 후 model/setting 변경은 없었습니다.

## 해석

큰 interaction lift도 동일한 전체 null 탐색에서 흔했습니다. joint state의 추가 예측 가치가 확립되지 않았습니다.

## 한계

희소 joint cell, 부모 분모, 중첩된 경로, finite mixing과 역사 구간 재사용이 한계입니다.

## 다음 단계

후속 [Phase 10은 완료](phase10-results.md)되었습니다. 현재 1246회는 알려진 결과이며 [현재 workflow](prospective-workflow.md)에서 원본 가용성과 당시 상태를 구분합니다.
