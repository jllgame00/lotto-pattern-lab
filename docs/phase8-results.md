# Phase 8 — Recent-frequency-conditioned 3D 결과

## 결론

frequency를 gap 대신 세 번째 차원으로 시험했으며 둘을 결합하지 않았습니다. 4D·neural network는 없습니다. 실제 history는1245까지이며 당시1246 결과를 사용하지 않았습니다. **H5: TESTED / INCONCLUSIVE.** 두 null의 complete-search 보정 후 통과 family나 leakage-safe 예측 우위는 없었습니다. 조합·evaluation-selected window를 승격하지 않았습니다.

## 가설

W10/W26/W52의 source frequency 상태가 translation과 chain의 예측 가치를 높이는지 검증했습니다.

## 데이터 및 검증 범위

target t count_W는 t-W..t-1의 full window만 사용합니다. rate=count/W, historical rate는 t 이전 전체입니다. relative=recent_rate/historical_rate로 denominator zero면 missing입니다. missing을 ordinary state로 바꾸지 않고 제외하며 bonus도 제외합니다. export168,075 rows=1245 draws×45 numbers×3 windows입니다.

count/rate는 W 안에서 같은 partition이므로 한 번만 탐색하고 둘 다 export합니다. training-only1/3·2/3 quantile,higher·boundary tie lower입니다. relative는0.5/1.5 고정이며 아래는 full-history descriptive 값입니다.

| W | Possible counts | Observed counts | COLD | NEUTRAL | HOT |
|---|---|---|---|---|---|
|10|0..10|0..7|0..1|2|3+|
|26|0..26|0..12|0..3|4|5+|
|52|0..52|0..17|0..6|7..8|9+|

이 threshold는 과거 예측에 재사용하지 않습니다. state-1은 history 부족이며 count는 다음과 같습니다.

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

count tie를 유지해 support가 다릅니다. zero-support 가능 state까지 raw distribution·quantile·relative support를 export합니다. W10 counts 5+,W26 counts 8+,W52 counts 0..1/13+는 winning source100 미만이라 extreme rate여도 supported maximum이 될 수 없습니다.

## 방법

causal frequency encoding과 동일한 전체 surrogate 탐색을 사용합니다.

## 정확한 탐색 범위

- conditional175,708 중67,447개가 support 100입니다. dt1..52,dn-15..15와 모든 window/state를 포함합니다. zero는 reference이며 predictive/leader에서 제외합니다.
- directional87,360 중34,843 supported이며 각 boundary denominator와 HOT-minus-COLD를 포함합니다.
- true displacement1,404개:dt1..13,dn+/-1..6,delta_count-1..1,destination은 DESCRIPTIVE ONLY입니다.
- length3/4/5는8,424개로 전체43,212 geometric rule/length의 subset입니다.
- unique307,684이며 length3/4/5를 더하지 않습니다.
- pruning 전 start 후보1,095,903,536은 겹치며 독립 검정이 아닙니다.

전체 window를 다섯 global family에 pooling합니다. sparse intercept 추가의 해석 한계로 Hough3D는 보류했습니다.

## 주요 결과

각 window·모든 representation에서 support 100 이상인 translation leader입니다.

| window | representation | state | delta_draw | delta_number | valid_opportunities | matches | match_rate | raw_z |
|---|---|---|---|---|---|---|---|---|
| 10 | quantile | 2 | 7 | 6 | 914 | 169 | 0.1849 | 4.5863 |
| 26 | quantile | 2 | 12 | 6 | 1673 | 282 | 0.1686 | 4.2386 |
| 52 | count | 4 | 18 | -11 | 435 | 86 | 0.1977 | 3.9493 |

raw selected observation이며 predictive discovery가 아닙니다. 다음은 bounded count-displacement leader입니다.

| window | delta_draw | delta_number | delta_count | valid_opportunities | matches | raw_z |
|---|---|---|---|---|---|---|
| 10 | 5 | 5 | 1 | 1384 | 225 | 3.1999 |
| 52 | 11 | -5 | 0 | 724 | 125 | 3.1122 |
| 26 | 10 | 6 | 0 | 1032 | 170 | 2.9669 |

최강 supported continuation입니다.

| window | kind | rule | delta_draw | delta_number | chain_length | valid_opportunities | matches | raw_z |
|---|---|---|---|---|---|---|---|---|
| 10 | same_bin | 0 | 9 | -4 | 3 | 192 | 44 | 3.9064 |
| 26 | same_bin | 0 | 9 | -4 | 3 | 119 | 30 | 3.8113 |
| 10 | same_bin | 0 | 11 | 2 | 4 | 22 | 9 | 3.8049 |

longest maximal path입니다.

| window | kind | rule | start_draw | start_number | start_count | delta_draw | delta_number | chain_length | end_draw | end_number |
|---|---|---|---|---|---|---|---|---|---|---|
| 10 | same_bin | 0 | 289 | 33 | 1 | 9 | -4 | 6 | 334 | 13 |
| 10 | delta_count | 0 | 289 | 33 | 1 | 9 | -4 | 6 | 334 | 13 |
| 10 | same_bin | 0 | 523 | 45 | 0 | 2 | -6 | 6 | 533 | 15 |
| 10 | same_bin | 0 | 945 | 9 | 0 | 11 | 2 | 6 | 1000 | 19 |
| 10 | same_bin | 0 | 1154 | 22 | 1 | 3 | -2 | 6 | 1169 | 12 |
| 26 | same_bin | 2 | 563 | 32 | 6 | 8 | -6 | 6 | 603 | 2 |

W10 COLD의289/number33/count 1→334/13은(+9,-4)의6 points이며 모두 count 1입니다. 같은 점이 COLD chain·zero-count-displacement 양쪽에 속하므로 독립 발견이 아닌 중첩 설명입니다. nested fragment를 억제합니다.

## Walk-forward 결과

401..1245의845 targets,expanding past-only fit,cadence 26,seed 42입니다. 기존 baseline은 Phase 7의26/13 cadence별5,070 rows의 score/rank/cutoff/hit를 정확히 재현했습니다. 모든 새 model/reference는 같은 targets입니다.

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

random Top6 expectation0.8입니다. 모든 frequency variant의 full-period Random 차이 interval은 zero를 포함합니다. frequency-chain 점추정치는2D parent보다 낮습니다. mean winning rank는 낮을수록 좋으며 full0..6·ranking/pool을 export합니다.

세 reference 대비2000 circular26-draw block bootstrap,seed 42의 unadjusted exploratory interval입니다.

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

chain ablation은 state family뿐 아니라 eligibility도 바꿉니다. Phase 8은 두 predecessor의 동일 state,Phase 7은 최근 source 조건입니다. 기존 default를 보존한 전체 model 비교이며 모든 filter 차이를 분리한 것이 아닙니다.

## 시간 robustness와 window 선택

multiple start는 기존 refit schedule의 nested slice이며 유리한 새 prediction 탐색이 아닙니다.

| evaluation_start | FrequencyConditionedChainModel | FrequencyConditionedTranslationModel | RandomModel |
|---|---|---|---|
| 401 | 0.7467 | 0.7964 | 0.8024 |
| 501 | 0.7436 | 0.8107 | 0.8054 |
| 601 | 0.7442 | 0.8062 | 0.7984 |
| 701 | 0.7541 | 0.8037 | 0.7761 |
| 801 | 0.7191 | 0.8247 | 0.7685 |
| 901 | 0.7362 | 0.8348 | 0.7681 |

block은401..682,683..964,965..1245입니다. frequency의 평균·Random 차이는 시간에 따라 변합니다.

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

cadence 13 sensitivity는 각 window를 별도 refit합니다.

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

development-only401..900 selector의 tie는26→10→52입니다. cadence 26에서 W10 Translation(development 0.816,later 0.7855),W52 Chain(0.780,0.7768)을 골랐습니다. 901..1245는 선택에서 제외했어도 pristine holdout은 아닙니다. 신뢰할 우위나 사전 W26 대체를 정당화하지 못했고 조합도 없습니다. 두 cadence의 selection/later를 따로 export합니다.

## Candidate-pool / prize-aware 결과

full-period pool별 >=5·all6 count입니다. ticket prize가 아닌 containment입니다.

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

Top8/10/12/15 exact P>=5는0.000258/0.001109/0.003322/0.011675,845 draws 기대0.218/0.937/2.807/9.865입니다. primary W26 Translation은0/1/4/7·all6 없음,Chain은1/1/2/6·Top15 all6 두 번입니다. 희귀 count는 우위 증거가 아닙니다. 모든 분포·expectation·marginal/paired interval을 저장하며 zero-event 퇴화·multiplicity·nested dependence를 주의합니다.

## 출력과 재현

[방법](frequency3d-analysis.md)·[당시 protocol](superpowers/plans/2026-10-17-phase8.md). `reports/spatiotemporal_frequency/`는 causal state·support·conditional/directional/displacement·maximal paths·surrogate maxima/seeds·follow-up·rolling/era·plots·walk_forward_26/·walk_forward_13/ audit를 저장합니다.

실제 input은1245까지,canonical SHA-256 `b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e`,당시 HEAD `d6fde72b65e7311f5c6d532938db26a1ff353bdf`입니다. 전체245 tests·2 dependency skips,39.35s였습니다. 독립 scalar synthetic review로 search/predictor count·score·isolation을 확인했고 complete rolling window가 없는 short history도 처리합니다.

## Null / surrogate 비교

199 IID·199 fixed-margin 모두 state·quantile을 재계산해 같은307,684 configurations·1,095,903,536 potential starts를 탐색했습니다. 보정 후 통과가 없습니다.

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

다섯 family는 전체 window/representation을 합치고 null별 Bonferroni5입니다. adjusted p는 모두1.0입니다. six-point chain도 random best에서 흔하며 global p는 IID0.895·fixed0.870입니다. 눈에 띄는 raw path/local peak가 unusual structure를 제공하지 못합니다.

Phase 6의(+42,-5) follow-up COLD/NEUTRAL/HOT rate입니다.

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

W10은 COLD 최대,W26/W52는 COLD·HOT가 비슷하고 NEUTRAL이 낮습니다. HOT만의 관계가 아닙니다. 일부 local p 0.005여도 Phase 6 선택이고 complete maximum global p 0.330/0.380이라 독립 preregistration이 아닙니다. 두 null local detail은 CSV에 있습니다.

전체 descriptive/null/export/plot1039.3s(약17.3 minutes),walk-forward26은77.0s,13은99.1s로 feature/report 포함입니다. 8 static plots와 대표 heatmap/path를 확인했습니다. rolling plot은 support 100 미만을 숨기나 CSV는 count/rate/eligibility를 남깁니다.

## Prospective experiment

historical selection 후 사전 quantileW26 두 track만 독립 동결했습니다. model 재설계·window 승격·ensemble·threshold 변경은 없었습니다. optional development 진단도 추가 track을 정당화하지 못했습니다. [원본 기록](phase8-prospective.md)에 snapshot·exact tickets·registry·hash가 있고 이전 Phase 5/6/7은 보존합니다.

snapshot은2026-10-17T09:18:15.127269+09:00에 한 번 생성해 당시 FROZEN_UNEVALUATED를 검증했습니다. 당시 이전15파일·canonical hash는 같았고 commit/push·target result 접근은 없었습니다.

## 해석

일부 local follow-up과 rare pool event는 전체 탐색에서 선택된 결과이므로 독립적인 예측 증거가 아닙니다.

## 한계

희소 상태, count 동률, window 선택, 겹치는 경로와 역사 구간 재사용이 한계입니다.

## 다음 단계

후속 [Phase 9는 완료](phase9-results.md)되었습니다. 현재 1246회는 알려졌으며 [현재 workflow](prospective-workflow.md)와 당시 기록을 구분합니다.
