# Phase 7 — Gap-conditioned 3D 결과

## 결론

H4 — Gap-conditioned 3D: **TESTED / INCONCLUSIVE**.

global null-search correction을 통과한 구조나 primary conditioned model의 예측 개선은 확립되지 않았습니다. 설정·두 prospective track을 결과 전에 선언했고 조합·representation winner는 선택하지 않았습니다. 당시1246 결과를 가져오기·확인·import·검색·평가하지 않았습니다.

## 가설

source의 causal gap 상태에 따라 2D에서 희석된 translation이나 trajectory가 나타나는지 검증했습니다.

## 데이터 및 검증 범위

gap source state에서 translation을 시험했습니다. canonical 1–1245, latest2026-10-10, binary1245×45 본번호입니다. SHA-256은 `b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e`이며 sparse table은56,025 rows입니다.

target t gap=t-1-last appearance입니다. known pre-state55,665·never-seen360을 구분하고 후자는 제외합니다. gap min0·max73·median4·95th21·99th33입니다. descriptive coarse0–2,3–7,8+, clipped cap21, relative<=0.5,(0.5,1.5],>1.5입니다. predictive threshold는 prefix별 fit입니다.

| representation | state | observations | winning_source_points |
|---|---|---|---|
| quantile | -1 | 360 | 45 |
| quantile | 0 | 19418 | 2633 |
| quantile | 1 | 18537 | 2448 |
| quantile | 2 | 17710 | 2344 |

## 방법과 정확한 탐색 범위

conditional/destination pair는 dt1–52,dn±1–15이며 zero displacement는 제외합니다. true3D/trajectory는 dt1–13,dn±1–6,clipped-gap displacement-3..3입니다.

- source conditional43,680, supported34,492입니다.
- source/destination14,040은 모두 supported이며 DESCRIPTIVE ONLY입니다.
- true3D1,092도 모두 supported·DESCRIPTIVE ONLY입니다.
- length3/4/5 tuples4,680 중 continuation444 supported입니다.
- 전체 geometric rule/length18,772에는5 초과도 포함합니다.
- unique77,584이며 length3/4/5 subset을 더하지 않습니다.
- pruning 전 rule/length/start opportunities518,137,360은 겹치며 독립 검정이 아닙니다.

동일 training recipe에서 null cap19–22, surrogate당 configurations 73,736–79,456입니다. 모든 history에 같은 adaptive search입니다. pair support 100·continuation20, longest는 별도 maximum correction입니다. sparse intercept family의 해석 한계로3D Hough는 보류했습니다.

## 주요 결과

source-conditioned 최대는(+50,+4), clipped gap 3,105/535, rate 0.1963·lift1.4720·z 4.2818입니다. early/middle/recent0.1871/0.2079/0.2025는 post-selection 기술 확인이며 독립 검증이 아닙니다.

| representation | gap_state | delta_draw | delta_number | valid_opportunities | matches | match_rate | raw_z |
|---|---|---|---|---|---|---|---|
| clipped | 3 | 50 | 4 | 535 | 105 | 0.1963 | 4.2818 |
| relative | 1 | 1 | 8 | 2185 | 357 | 0.1634 | 4.1326 |
| clipped | 4 | 20 | 3 | 510 | 99 | 0.1941 | 4.0381 |
| quantile | 1 | 1 | 8 | 2027 | 332 | 0.1638 | 4.0336 |
| clipped | 5 | 25 | 3 | 439 | 87 | 0.1982 | 3.9968 |

true3D 최대는(+13,-4,+2 clipped units),70/350=0.2000,z 3.6690입니다. saturated clipped 변화는 raw 변화와 다르며 destination 조건은 predictor가 쓰지 않습니다.

same-state 최장은 high gap 6 points,523/45→533/15,(+2,-6),raw start38·clipped21·geometric max8입니다. nested fragment는 억제합니다. exact clipped 반복 최장은4 points이며 nonzero 예는1138/16/gap 9→1162/25/gap 3,(+8,+3,-2)입니다.

supported continuation 최대는 medium,(+10,+3),length3,10/31,z 3.0997입니다. raw support·longest는 따로 null calibration합니다.

Phase 6의(+42,-5)는 coarse 모든 상태에서 positive이며 low0.1470·medium0.1439·high0.1579 대 IID0.1333입니다. high local p 0.005는 두 null 모두 floor이지만 Phase 6에서 선택한 rule이고 complete search는 unusual하지 않습니다. 독립 preregistration이 아닙니다.

## Null / surrogate 비교

199 IID six-of45·199 exact-margin,seed 70042입니다. 매 surrogate에서 gap·mean interval·cap·bin을 다시 계산합니다. 20*T curveball의 finite mixing은 근사입니다. null별 다섯 family Bonferroni이며 두 null 모두 통과해야 합니다.

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

보정 후 통과가 없습니다. raw resolution0.005·adjusted0.025입니다. 선택 local peak는 corrected discovery가 아닙니다. 전체 search/export601.6 seconds, plot은 추가 수 초입니다.

## Walk-forward 결과

401–1245의845 targets,expanding history,cadence 26,seed 42입니다. score 후 outcome을 읽습니다. 기존 Gap Logistic·2D parent default를 유지합니다. pair/chain은100/20 opportunities와 최근 source pre-gap만 조건으로 씁니다.

| model | avg_hits | mean_winning_rank | recall_6 | recall_10 | recall_15 |
|---|---|---|---|---|---|
| TranslationModel | 0.8154 | 22.6675 | 0.1359 | 0.2274 | 0.3371 |
| ChainModel | 0.7941 | 23.0469 | 0.1323 | 0.2199 | 0.3241 |
| GapConditionedTranslationModel | 0.8296 | 22.8771 | 0.1383 | 0.2264 | 0.3428 |
| GapConditionedChainModel | 0.7680 | 23.0953 | 0.1280 | 0.2160 | 0.3320 |
| GapLogistic | 0.8426 | 22.8529 | 0.1404 | 0.2260 | 0.3389 |
| RandomModel | 0.8024 | 23.0156 | 0.1337 | 0.2221 | 0.3327 |

theoretical Top6 hit는0.8,mean winning rank는 낮을수록 좋습니다. gap conditioning은 Translation hit를 약간 높이나 rank는 악화하고 Chain hit는 낮춥니다. 신뢰할 우위는 확립되지 않았습니다.

2000 circular26-draw bootstrap,shared seed 42의 paired95% unadjusted interval입니다. legacy comparison.csv는 기존 stream이라 endpoint가 조금 다르며 paired_2d_3d.csv가 common-seed 파일입니다.

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

later 901–1245는 development 401–900 이후이지만 앞선 Phase 사용으로 pristine holdout이 아닙니다. 이 결과로 parameter/model을 tune하지 않았습니다.

## 상태 ablation과 시간 robustness

세 representation은 사전 설정이며 coarse primary를 유지합니다. 새 threshold 탐색이 아닙니다.

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

start는 같은 prediction run의 nested slice로 refit calendar를 유지하며 reporting period 선택으로 prediction을 바꾸지 않습니다.

| evaluation_start | GapConditionedChainModel | GapConditionedTranslationModel | RandomModel |
|---|---|---|---|
| 401 | 0.7680 | 0.8296 | 0.8024 |
| 501 | 0.7705 | 0.8161 | 0.8054 |
| 601 | 0.7721 | 0.8202 | 0.7984 |
| 701 | 0.7541 | 0.8239 | 0.7761 |
| 801 | 0.7393 | 0.8225 | 0.7685 |
| 901 | 0.7623 | 0.8580 | 0.7681 |

전체 run의 early/middle/recent block입니다.

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

Translation의 Random 대비 이득은 recent에 집중되고 첫 block은 약하게 negative입니다. gap Chain은 세 block 모두 nonpositive입니다. cadence 13은 primary를 별도 refit합니다.

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

여러 protocol의 paired uncertainty에서 primary positive difference가 입증되지 않았습니다. cadence 26 전체 ablation70.9s,cadence 13 primary54.9s에 feature/report가 포함됩니다.

## Candidate-pool / prize-aware 결과

전체845 targets,cadence 26의 >=5·all6 containment입니다. 출력은 full0–6·exact hypergeometric·marginal/paired interval도 포함합니다.

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

exact P(pool>=5)는 Top8=0.000258,Top10=0.001109,Top12=0.003322,Top15=0.011675입니다. 845 draws 기대는0.218,0.937,2.807,9.865,all6 probability는 각각0.00000344,0.00002578,0.00011344,0.00061447입니다.

primary Translation의 Top15 >=5는14 대 Random8,paired rate 0.00710[-0.00473,0.02130]입니다. Top12 차이0.00237[-0.00355,0.00828]입니다. all6 pool은 six-match ticket이나 우위 증거가 아닙니다. 2D parent 대비 sparse interval의 zero bound도 multiplicity·작은 count·nested dependence 때문에 유의성 근거로 쓰지 않습니다.

## 출력 파일

[방법](gap3d-analysis.md)·[당시 protocol](superpowers/plans/2026-10-17-phase7.md). `reports/spatiotemporal3d/`는 historical state·support·conditional/destination/displacement·maximal paths·seed/count/null maxima·stability·follow-up·일곱 plots를 저장합니다. walk_forward_26/·walk_forward_13/에 full score/rank audit·metrics·pool·parent·era·protocol이 있습니다.

## Prospective experiment

사전 coarse-bin 두 모델만 별도 `reports/prospective/phase7/`에 동결했습니다. Top12·seed 42·weighted/coverage unique nested1/5/10/20·directTop6이며 combination/ablation winner는 없습니다. Phase 5/6 원본과 registry는 보존했습니다. 당시1246 결과에 접근하지 않았습니다.

## 검증과 publication

당시 전체212 passed,2 dependency skips,56.01s;focused17 passed입니다. 독립 scalar synthetic review로 count/score와 publication을 검증했습니다.

[Phase 7 동결 원본](phase7-prospective.md)은2026-10-17T08:48:08.689811+09:00에 한 번 생성했고 사전 두 track의 FROZEN_UNEVALUATED를 보존합니다. 당시 이전10파일·canonical hash가 전후 같았고 commit/push·미래 결과 접근은 없었습니다.

## 해석

gap conditioning의 일부 양의 점추정치는 paired uncertainty와 전체 null 탐색을 넘어서는 근거가 되지 못했습니다.

## 한계

희소 상태, trajectory 중첩, finite mixing, parent와의 filter 차이 및 역사 구간 재사용이 한계입니다.

## 다음 단계

후속 [Phase 8은 완료](phase8-results.md)되었습니다. 현재 1246회는 알려진 결과이며 [현재 workflow](prospective-workflow.md)와 당시 동결 기록을 구분합니다.
