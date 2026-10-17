# Phase 10 — Number-space 결과

## 결론

**H8: TESTED / INCONCLUSIVE.** IID·constrained complete search에서 corrected spatial structure가 없었고 development-frozen later 우위도 확립되지 않았습니다. 수치 인접성은 물리 인접성이 아니며 예측·수익성 주장은 없습니다. 과거 H9는 현재 H8이며 동결 원본의 번호는 보존합니다.

## 가설

번호 하나보다 주변 activity와 국소 구간의 density가 유용한지 검증했습니다.

## 데이터 및 검증 범위

finite number-space activity를 시험했습니다. canonical 1..1245,마지막2026-10-10입니다. 당시1246 결과를 가져오기·검색·확인·import·평가하지 않았습니다. 이전 Phase 5-9의25 prospective 파일을 사전 inventory로 보호했고 commit/push는 없었습니다.

## 방법과 정확한 탐색 범위

[당시 protocol](superpowers/plans/2026-10-17-phase10.md)은 window 10/26/52·width 3/5/7/9·primary kernel 네 개·box radii1..4를 고정합니다. own·neighbor-only·smoothed를 구분하고 score는 target 전 완료 draw·finite1..45·no wrap입니다.

| range_density_cells | kernel_cells | zone_endpoint_cells | zone_movement_metrics | spacing_cells | motif_universe | range_configurations | primary_kernel_configurations | kernel_signal_configurations | families |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 584000 | 2463750 | 14600 | 144 | 83215 | 1086008 | 12 | 12 | 45 | 6 |

이 수는 computational cells/records이며 독립 가설이 아닙니다. range/kernel configuration은 같은 cell을 가리키고 zone endpoint도 range에서 파생합니다. 여섯 family는 range density·neighborhood·persistence·movement·spacing/clustering·motif입니다. motif universe는 합44 이하인 ordered positive spacings 전체 C(44,5)이며 미관측도 포함합니다.

## 주요 결과 — Spacing과 broad region

spacing.csv에 sorted number·ordered gap·cluster·broad region을 저장합니다. region은 descriptive입니다. reference mean/SD는 real과 별개인50,000 IID draws입니다. exact range expectation230/7=32.8571·mean adjacent gap 46/7=6.5714와 작은 차이는 Monte Carlo error입니다.

| metric | reference_mean | reference_std | historical_mean |
| --- | --- | --- | --- |
| minimum_spacing | 1.7709 | 1.0247 | 1.8056 |
| maximum_spacing | 14.3886 | 4.8093 | 14.1092 |
| mean_spacing | 6.5823 | 1.3488 | 6.5418 |
| median_spacing | 5.2402 | 2.0255 | 5.2988 |
| spacing_variance | 25.8073 | 21.0825 | 24.6589 |
| consecutive_pairs | 0.6699 | 0.7276 | 0.6602 |
| draw_range | 32.9114 | 6.7442 | 32.7092 |
| nearest_mean | 4.5645 | 1.4039 | 4.5290 |
| gaps_le2 | 1.2578 | 0.8832 | 1.2394 |
| gaps_ge10 | 1.1979 | 0.6989 | 1.1719 |
| clusters_2 | 4.7422 | 0.8832 | 4.7606 |
| clusters_4 | 3.7604 | 0.9252 | 3.7655 |
| region_0 | 1.2022 | 0.9210 | 1.1647 |
| region_1 | 1.1977 | 0.9204 | 1.2514 |
| region_2 | 1.1980 | 0.9229 | 1.1839 |
| region_3 | 1.1948 | 0.9181 | 1.1888 |
| region_4 | 1.2073 | 0.9243 | 1.2112 |

## Raw hot-zone 최대

| end_draw | target_draw | window | width | start_number | end_number | occurrences | density | expected_density | lift | raw_z | support_draws |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 13 | 14 | 10 | 7 | 36 | 42 | 21 | 0.3000 | 0.1333 | 2.2500 | 4.4140 | 10 |
| 11 | 12 | 10 | 3 | 40 | 42 | 12 | 0.4000 | 0.1333 | 3.0000 | 4.3978 | 10 |
| 697 | 698 | 10 | 3 | 33 | 35 | 12 | 0.4000 | 0.1333 | 3.0000 | 4.3978 | 10 |
| 427 | 428 | 10 | 3 | 26 | 28 | 12 | 0.4000 | 0.1333 | 3.0000 | 4.3978 | 10 |
| 820 | 821 | 52 | 3 | 10 | 12 | 38 | 0.2436 | 0.1333 | 1.8269 | 4.1464 | 52 |
| 13 | 14 | 10 | 5 | 38 | 42 | 16 | 0.3200 | 0.1333 | 2.4000 | 4.0724 | 10 |
| 427 | 428 | 10 | 5 | 26 | 30 | 16 | 0.3200 | 0.1333 | 2.4000 | 4.0724 | 10 |
| 168 | 169 | 10 | 5 | 39 | 43 | 16 | 0.3200 | 0.1333 | 2.4000 | 4.0724 | 10 |
| 697 | 698 | 10 | 7 | 33 | 39 | 20 | 0.2857 | 0.1333 | 2.1429 | 4.0357 | 10 |
| 657 | 658 | 10 | 7 | 38 | 44 | 20 | 0.2857 | 0.1333 | 2.1429 | 4.0357 | 10 |

W10 endpoint13은36..42 안에60 winning occurrences 중21개, density0.3000·lift2.25·z 4.4140입니다. selected maximum은 typical null maxima보다 약합니다. 겹친 range/endpoint는 독립 발견이 아니며 최신 positive Top3는 transitive grouping합니다.

## Neighborhood peak

| window | kernel | signal | end_draw | number | score | raw_z |
| --- | --- | --- | --- | --- | --- | --- |
| 10 | none | smoothed | 780 | 21 | 0.7000 | 5.2715 |
| 26 | none | smoothed | 715 | 33 | 0.4615 | 4.9231 |
| 10 | triangular1 | neighbor_only | 780 | 20 | 0.5000 | 4.8796 |
| 10 | box1 | neighbor_only | 780 | 20 | 0.5000 | 4.8796 |
| 10 | gaussian2 | neighbor_only | 780 | 20 | 0.4362 | 4.8591 |
| 52 | triangular1 | neighbor_only | 821 | 11 | 0.2885 | 4.7076 |
| 52 | box1 | neighbor_only | 821 | 11 | 0.2885 | 4.7076 |
| 26 | triangular1 | neighbor_only | 796 | 20 | 0.3462 | 4.5668 |
| 26 | box1 | neighbor_only | 796 | 20 | 0.3462 | 4.5668 |
| 10 | gaussian2 | smoothed | 697 | 34 | 0.3886 | 4.5606 |

family 최대는 own-number control입니다. number21이 ending780의10 draws에 seven appearances입니다. 20 주변 neighbor-only peak는21 activity를 일부 상속합니다. null은 own/neighbor를 동등하게 탐색하며 local peak는 spatial mechanism의 증거가 아닙니다.

## Hot-zone persistence와 movement

| window | width | range_start | range_end | start_endpoint | end_endpoint | length |
| --- | --- | --- | --- | --- | --- | --- |
| 10 | 3 | 41 | 43 | 761 | 771 | 11 |
| 10 | 5 | 10 | 14 | 802 | 814 | 13 |
| 10 | 7 | 36 | 42 | 10 | 20 | 11 |
| 10 | 9 | 36 | 44 | 652 | 664 | 13 |
| 26 | 3 | 20 | 22 | 400 | 423 | 24 |
| 26 | 5 | 26 | 30 | 430 | 450 | 21 |
| 26 | 7 | 18 | 24 | 1072 | 1100 | 29 |
| 26 | 9 | 13 | 21 | 337 | 367 | 31 |
| 52 | 3 | 20 | 22 | 400 | 455 | 56 |
| 52 | 5 | 11 | 15 | 1030 | 1058 | 29 |
| 52 | 7 | 2 | 8 | 606 | 641 | 36 |
| 52 | 9 | 34 | 42 | 162 | 210 | 49 |

| window | width | latest_grouped_zones | identical_run | direction_run | mean_abs_movement | overlap_mean | positive_1_run | positive_2_run | positive_3_run | positive_4_run | negative_1_run | negative_2_run | negative_3_run | negative_4_run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | 3 | [(11, 13), (18, 20), (32, 34)] | 11 | 3 | 5.8761 | 0.5690 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 10 | 5 | [(9, 14), (16, 20)] | 13 | 3 | 5.3951 | 0.6262 | 2 | 1 | 1 | 1 | 1 | 2 | 1 | 1 |
| 10 | 7 | [(7, 13), (18, 24), (32, 38)] | 11 | 3 | 5.4235 | 0.6293 | 3 | 2 | 2 | 2 | 3 | 2 | 1 | 1 |
| 10 | 9 | [(10, 20)] | 13 | 3 | 4.3377 | 0.6955 | 1 | 2 | 2 | 1 | 1 | 1 | 1 | 1 |
| 26 | 3 | [(11, 13), (18, 20), (42, 44)] | 24 | 2 | 4.3601 | 0.6884 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 26 | 5 | [(9, 13), (16, 22)] | 21 | 2 | 3.6637 | 0.7527 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 26 | 7 | [(12, 22)] | 29 | 2 | 3.4774 | 0.7576 | 2 | 2 | 2 | 1 | 2 | 1 | 1 | 1 |
| 26 | 9 | [(11, 21)] | 31 | 2 | 3.4479 | 0.7720 | 1 | 1 | 1 | 1 | 2 | 2 | 1 | 1 |
| 52 | 3 | [(13, 15), (30, 33)] | 56 | 2 | 2.8575 | 0.8102 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 52 | 5 | [(24, 32)] | 29 | 2 | 2.4820 | 0.8260 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 52 | 7 | [(25, 33)] | 36 | 2 | 2.8047 | 0.8310 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 |
| 52 | 9 | [(24, 34)] | 49 | 2 | 1.9204 | 0.8775 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |

최장 identical strongest-range는 W52·20..22에서 ending400..455의56 endpoints입니다. rolling overlap으로 자연히 길어집니다. bounded direction run 최대는3 steps입니다. 두 family 모두 null을 통과하지 못했습니다. fixed-width trace는 adaptive expansion/contraction law가 아니며 grouped extent는 descriptive이고 movement predictor는 없습니다.

## Null / surrogate 비교

| null_model | statistic | real_max | null_mean | null_q95 | exceedances | replicates | global_p | adjusted_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed_margins | range_density | 4.4140 | 4.9837 | 5.4973 | 191 | 199 | 0.9600 | 1.0000 |
| fixed_margins | neighborhood | 5.2715 | 5.5141 | 6.2017 | 175 | 199 | 0.8800 | 1.0000 |
| fixed_margins | persistence | 56.0000 | 56.3869 | 75.3000 | 87 | 199 | 0.4400 | 1.0000 |
| fixed_margins | movement | 3.0000 | 3.2513 | 4.0000 | 197 | 199 | 0.9900 | 1.0000 |
| fixed_margins | spacing_clustering | 5.8035 | 6.3661 | 7.8204 | 136 | 199 | 0.6850 | 1.0000 |
| fixed_margins | spacing_motif | 1.0000 | 1.7136 | 2.0000 | 199 | 199 | 1.0000 | 1.0000 |
| iid | range_density | 4.4140 | 4.9451 | 5.5024 | 188 | 199 | 0.9450 | 1.0000 |
| iid | neighborhood | 5.2715 | 5.5726 | 6.2104 | 176 | 199 | 0.8850 | 1.0000 |
| iid | persistence | 56.0000 | 57.4271 | 75.0000 | 102 | 199 | 0.5150 | 1.0000 |
| iid | movement | 3.0000 | 3.2663 | 4.0000 | 197 | 199 | 0.9900 | 1.0000 |
| iid | spacing_clustering | 5.8035 | 6.4611 | 7.8374 | 157 | 199 | 0.7900 | 1.0000 |
| iid | spacing_motif | 1.0000 | 1.7085 | 2.0000 | 199 | 199 | 1.0000 | 1.0000 |

199 IID·199 exact-margin마다 recent activity·neighborhood·zone·motion·spacing을 재계산해 전체 탐색합니다. six per draw·exact per-number count는 유지하나 finite curveball mixing은 근사입니다. p=(1+exceedances)/(199+1),null별 Bonferroni6이며 양쪽 모두 통과 family가 없습니다. local z는 local test가 아니며 resolution0.005/0.030입니다.

## Development-only 선택

401..900만으로 range12·kernel 12·선택 neighborhood의 gap weights .25/.5/.75를 비교합니다. tie는 선언 순서이며 later 결과로 선택을 바꾸지 않았습니다.

선택 range는 **W26,width 3**,neighborhood는 **W52,kernel=none**,gap weight는 **0.75**이며 나머지는 neighborhood percentile rank입니다.

**smoothing이 선택되지 않았습니다.** frozen NeighborhoodModel은 own-number W52 frequency control이고 조합은75% Gap Logistic rank +25% own W52 rank입니다. neighbor가 도움 된다는 증거로 읽으면 안 됩니다. 실제 smoothing/neighbor-only는 모두 ablation으로 보고합니다.

frozen configuration SHA256은 `2ce1f1b9d9005e50089cc4be587bad9fec19550fd84d16a5b0aa13d507af3301`입니다.

later 전에 selection을 저장하고 cadence 13은 재사용합니다. prospective publication 전 두 cadence의 development prefix hash·canonical descriptive hash·normalized full-input hash를 확인합니다. source-binding gate 누락은 독립 review에서 발견해 publication 전 failing/passing regression으로 수정했습니다.

## Walk-forward 결과 — Later901..1245

later는 Phase 10 선택에서 제외했지만 이전 연구 이후 pristine holdout이 아닙니다. full401..1245는 selection optimism을 포함한 탐색치입니다. 기존 Random/Gap Logistic은 Phase 9의 cadence별1,690 rows를 score/rank/cutoff/hit까지 재현합니다.

| model | targets | avg_hits | mean_winning_rank | recall_6 | recall_10 | recall_15 | hits_0 | hits_1 | hits_2 | hits_3 | hits_4 | hits_5 | hits_6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Frequency26 | 345 | 0.7739 | 23.3362 | 0.1290 | 0.2072 | 0.3145 | 142 | 144 | 54 | 5 | 0 | 0 | 0 |
| GapLogistic | 345 | 0.8232 | 23.0478 | 0.1372 | 0.2184 | 0.3309 | 147 | 129 | 53 | 15 | 1 | 0 | 0 |
| RandomModel | 345 | 0.7681 | 22.9585 | 0.1280 | 0.2198 | 0.3367 | 149 | 135 | 53 | 8 | 0 | 0 | 0 |
| RangeDensityModel | 345 | 0.7652 | 23.0391 | 0.1275 | 0.2140 | 0.3391 | 140 | 155 | 42 | 7 | 1 | 0 | 0 |
| NeighborhoodModel | 345 | 0.7304 | 23.5005 | 0.1217 | 0.2068 | 0.3242 | 146 | 150 | 45 | 4 | 0 | 0 | 0 |
| GapNeighborhoodModel | 345 | 0.7507 | 23.1720 | 0.1251 | 0.2155 | 0.3198 | 161 | 122 | 51 | 9 | 2 | 0 | 0 |

### Paired 불확실성

circular26-draw block bootstrap 2,000,seed 42입니다. model search에 대해 unadjusted인 탐색 interval이며 positive hit difference는 첫 model 우세입니다. Random/Frequency26/Gap Logistic 대비 pool mean·3+/4+/5+/all6도 export합니다.

| model | reference | difference | ci_low | ci_high |
| --- | --- | --- | --- | --- |
| RangeDensityModel | RandomModel | -0.0029 | -0.0928 | 0.0812 |
| RangeDensityModel | Frequency26 | -0.0087 | -0.0899 | 0.0609 |
| RangeDensityModel | GapLogistic | -0.0580 | -0.1392 | 0.0319 |
| NeighborhoodModel | RandomModel | -0.0377 | -0.1536 | 0.0696 |
| NeighborhoodModel | Frequency26 | -0.0435 | -0.1420 | 0.0580 |
| NeighborhoodModel | GapLogistic | -0.0928 | -0.1855 | -0.0058 |
| GapNeighborhoodModel | RandomModel | -0.0174 | -0.1188 | 0.0986 |
| GapNeighborhoodModel | Frequency26 | -0.0232 | -0.1304 | 0.0841 |
| GapNeighborhoodModel | GapLogistic | -0.0725 | -0.1420 | -0.0058 |

combination은 Gap Logistic보다 낮은 점추정치입니다. 간단한 baseline을 넘어서는 robust neighborhood/range 개선은 없습니다.

### Candidate-pool 결과

pools.csv는 full0..6·mean winner·3+/4+/5+/all6·exact hypergeometric·marginal/paired interval입니다. rare event만으로 증거가 아닙니다.

| model | pool_size | count_3plus | count_4plus | count_5plus | count_6plus | exact_random_5plus | exact_random_6plus |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Frequency26 | 8 | 18 | 1 | 0 | 0 | 0.000258 | 3.44e-06 |
| Frequency26 | 10 | 33 | 4 | 0 | 0 | 0.0011 | 2.58e-05 |
| Frequency26 | 12 | 55 | 7 | 0 | 0 | 0.0033 | 0.000113 |
| Frequency26 | 15 | 100 | 21 | 4 | 0 | 0.0117 | 0.000614 |
| GapLogistic | 8 | 27 | 2 | 0 | 0 | 0.000258 | 3.44e-06 |
| GapLogistic | 10 | 43 | 6 | 1 | 0 | 0.0011 | 2.58e-05 |
| GapLogistic | 12 | 68 | 11 | 1 | 0 | 0.0033 | 0.000113 |
| GapLogistic | 15 | 116 | 31 | 3 | 0 | 0.0117 | 0.000614 |
| RandomModel | 8 | 20 | 1 | 0 | 0 | 0.000258 | 3.44e-06 |
| RandomModel | 10 | 35 | 6 | 0 | 0 | 0.0011 | 2.58e-05 |
| RandomModel | 12 | 71 | 14 | 0 | 0 | 0.0033 | 0.000113 |
| RandomModel | 15 | 111 | 34 | 0 | 0 | 0.0117 | 0.000614 |
| RangeDensityModel | 8 | 18 | 2 | 1 | 0 | 0.000258 | 3.44e-06 |
| RangeDensityModel | 10 | 44 | 3 | 1 | 0 | 0.0011 | 2.58e-05 |
| RangeDensityModel | 12 | 65 | 14 | 1 | 0 | 0.0033 | 0.000113 |
| RangeDensityModel | 15 | 113 | 35 | 6 | 0 | 0.0117 | 0.000614 |
| NeighborhoodModel | 8 | 16 | 1 | 0 | 0 | 0.000258 | 3.44e-06 |
| NeighborhoodModel | 10 | 32 | 3 | 0 | 0 | 0.0011 | 2.58e-05 |
| NeighborhoodModel | 12 | 55 | 15 | 1 | 0 | 0.0033 | 0.000113 |
| NeighborhoodModel | 15 | 100 | 37 | 4 | 0 | 0.0117 | 0.000614 |
| GapNeighborhoodModel | 8 | 26 | 2 | 0 | 0 | 0.000258 | 3.44e-06 |
| GapNeighborhoodModel | 10 | 43 | 5 | 0 | 0 | 0.0011 | 2.58e-05 |
| GapNeighborhoodModel | 12 | 66 | 8 | 0 | 0 | 0.0033 | 0.000113 |
| GapNeighborhoodModel | 15 | 105 | 23 | 0 | 0 | 0.0117 | 0.000614 |

## Window·width·kernel ablation

모든 설정은 사전 선언했습니다. later 결과를 replacement 선택에 쓰지 않고 development/later 평균 Top6로 보고합니다.

### Raw frequency

| model | development | later |
| --- | --- | --- |
| Frequency10 | 0.8100 | 0.7826 |
| Frequency26 | 0.7920 | 0.7739 |
| Frequency52 | 0.8620 | 0.7304 |

### Range width와 window

| model | development | later |
| --- | --- | --- |
| Range_W10_D3 | 0.7960 | 0.7159 |
| Range_W10_D5 | 0.8000 | 0.7971 |
| Range_W10_D7 | 0.7900 | 0.7739 |
| Range_W10_D9 | 0.8080 | 0.7855 |
| Range_W26_D3 | 0.8100 | 0.7652 |
| Range_W26_D5 | 0.7660 | 0.7826 |
| Range_W26_D7 | 0.7740 | 0.8000 |
| Range_W26_D9 | 0.7600 | 0.7855 |
| Range_W52_D3 | 0.7900 | 0.8029 |
| Range_W52_D5 | 0.8080 | 0.7826 |
| Range_W52_D7 | 0.8080 | 0.7739 |
| Range_W52_D9 | 0.7720 | 0.7710 |

### Primary smoothing kernel

| model | development | later |
| --- | --- | --- |
| Neighborhood_W10_gaussian2 | 0.7940 | 0.7275 |
| Neighborhood_W10_none | 0.8100 | 0.7826 |
| Neighborhood_W10_triangular1 | 0.7960 | 0.6928 |
| Neighborhood_W10_triangular2 | 0.7980 | 0.7246 |
| Neighborhood_W26_gaussian2 | 0.7920 | 0.7507 |
| Neighborhood_W26_none | 0.7920 | 0.7739 |
| Neighborhood_W26_triangular1 | 0.8040 | 0.7623 |
| Neighborhood_W26_triangular2 | 0.7620 | 0.7420 |
| Neighborhood_W52_gaussian2 | 0.8080 | 0.7739 |
| Neighborhood_W52_none | 0.8620 | 0.7304 |
| Neighborhood_W52_triangular1 | 0.8100 | 0.7623 |
| Neighborhood_W52_triangular2 | 0.8000 | 0.7855 |

### Neighbor-only control

| model | development | later |
| --- | --- | --- |
| NeighborOnly_W10_gaussian2 | 0.8040 | 0.7420 |
| NeighborOnly_W10_triangular1 | 0.7960 | 0.7768 |
| NeighborOnly_W10_triangular2 | 0.7920 | 0.7159 |
| NeighborOnly_W26_gaussian2 | 0.7340 | 0.7188 |
| NeighborOnly_W26_triangular1 | 0.7680 | 0.7565 |
| NeighborOnly_W26_triangular2 | 0.7560 | 0.7797 |
| NeighborOnly_W52_gaussian2 | 0.7680 | 0.8000 |
| NeighborOnly_W52_triangular1 | 0.7800 | 0.8522 |
| NeighborOnly_W52_triangular2 | 0.7600 | 0.7855 |

### 같은 W의 own 대비 neighbor 기여

| window | kernel | signal | avg_hits | own_avg_hits | difference | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | triangular1 | neighbor_only | 0.7768 | 0.7826 | -0.0058 | -0.1044 | 0.0928 |
| 10 | triangular1 | own_plus_neighbors | 0.6928 | 0.7826 | -0.0899 | -0.1623 | -0.0174 |
| 10 | triangular2 | neighbor_only | 0.7159 | 0.7826 | -0.0667 | -0.1768 | 0.0291 |
| 10 | triangular2 | own_plus_neighbors | 0.7246 | 0.7826 | -0.0580 | -0.1450 | 0.0261 |
| 10 | gaussian2 | neighbor_only | 0.7420 | 0.7826 | -0.0406 | -0.1478 | 0.0638 |
| 10 | gaussian2 | own_plus_neighbors | 0.7275 | 0.7826 | -0.0551 | -0.1362 | 0.0290 |
| 26 | triangular1 | neighbor_only | 0.7565 | 0.7739 | -0.0174 | -0.1246 | 0.0986 |
| 26 | triangular1 | own_plus_neighbors | 0.7623 | 0.7739 | -0.0116 | -0.0812 | 0.0493 |
| 26 | triangular2 | neighbor_only | 0.7797 | 0.7739 | 0.0058 | -0.1073 | 0.1159 |
| 26 | triangular2 | own_plus_neighbors | 0.7420 | 0.7739 | -0.0319 | -0.0957 | 0.0290 |
| 26 | gaussian2 | neighbor_only | 0.7188 | 0.7739 | -0.0551 | -0.1594 | 0.0522 |
| 26 | gaussian2 | own_plus_neighbors | 0.7507 | 0.7739 | -0.0232 | -0.0957 | 0.0464 |
| 52 | triangular1 | neighbor_only | 0.8522 | 0.7304 | 0.1217 | 0.0290 | 0.2232 |
| 52 | triangular1 | own_plus_neighbors | 0.7623 | 0.7304 | 0.0319 | -0.0493 | 0.1102 |
| 52 | triangular2 | neighbor_only | 0.7855 | 0.7304 | 0.0551 | -0.0435 | 0.1682 |
| 52 | triangular2 | own_plus_neighbors | 0.7855 | 0.7304 | 0.0551 | -0.0319 | 0.1392 |
| 52 | gaussian2 | neighbor_only | 0.8000 | 0.7304 | 0.0696 | -0.0493 | 0.1942 |
| 52 | gaussian2 | own_plus_neighbors | 0.7739 | 0.7304 | 0.0435 | -0.0233 | 0.1130 |

later performance로 새 winner를 고르지 않은 ablation입니다. positive unadjusted estimate도 global/robustness 근거가 필요하며 neighborhood 가설을 확립하지 못했습니다.

## 시작점·cadence robustness

starts401/501/601/701/801/901은401 refit calendar를 유지합니다. 901 이전 start는 development와 겹치므로 독립 later validation이 아닙니다.

### Cadence26 시작점별 평균 hit

| model | 401 | 501 | 601 | 701 | 801 | 901 |
| --- | --- | --- | --- | --- | --- | --- |
| Frequency26 | 0.7846 | 0.7732 | 0.7767 | 0.7743 | 0.7730 | 0.7739 |
| GapLogistic | 0.8426 | 0.8336 | 0.8388 | 0.8330 | 0.8472 | 0.8232 |
| GapNeighborhoodModel | 0.8142 | 0.7933 | 0.8109 | 0.8000 | 0.7978 | 0.7507 |
| NeighborhoodModel | 0.8083 | 0.7893 | 0.7829 | 0.7817 | 0.7685 | 0.7304 |
| RandomModel | 0.8024 | 0.8054 | 0.7984 | 0.7761 | 0.7685 | 0.7681 |
| RangeDensityModel | 0.7917 | 0.7839 | 0.7984 | 0.7963 | 0.8135 | 0.7652 |

### Cadence13 시작점별 평균 hit

| model | 401 | 501 | 601 | 701 | 801 | 901 |
| --- | --- | --- | --- | --- | --- | --- |
| Frequency26 | 0.7846 | 0.7732 | 0.7767 | 0.7743 | 0.7730 | 0.7739 |
| GapLogistic | 0.8391 | 0.8322 | 0.8403 | 0.8349 | 0.8472 | 0.8203 |
| GapNeighborhoodModel | 0.8059 | 0.7919 | 0.8062 | 0.7963 | 0.7933 | 0.7449 |
| NeighborhoodModel | 0.8083 | 0.7893 | 0.7829 | 0.7817 | 0.7685 | 0.7304 |
| RandomModel | 0.8024 | 0.8054 | 0.7984 | 0.7761 | 0.7685 | 0.7681 |
| RangeDensityModel | 0.7917 | 0.7839 | 0.7984 | 0.7963 | 0.8135 | 0.7652 |

### Later early/middle/recent

| model | block | start_draw | end_draw | targets | avg_hits | delta_vs_random |
| --- | --- | --- | --- | --- | --- | --- |
| Frequency26 | early | 901 | 1015 | 115 | 0.6696 | -0.1043 |
| Frequency26 | middle | 1016 | 1130 | 115 | 0.9043 | 0.0783 |
| Frequency26 | recent | 1131 | 1245 | 115 | 0.7478 | 0.0435 |
| GapLogistic | early | 901 | 1015 | 115 | 0.7565 | -0.0174 |
| GapLogistic | middle | 1016 | 1130 | 115 | 0.8957 | 0.0696 |
| GapLogistic | recent | 1131 | 1245 | 115 | 0.8174 | 0.1130 |
| RandomModel | early | 901 | 1015 | 115 | 0.7739 | 0.0000 |
| RandomModel | middle | 1016 | 1130 | 115 | 0.8261 | 0.0000 |
| RandomModel | recent | 1131 | 1245 | 115 | 0.7043 | 0.0000 |
| RangeDensityModel | early | 901 | 1015 | 115 | 0.6783 | -0.0957 |
| RangeDensityModel | middle | 1016 | 1130 | 115 | 0.8261 | 0.0000 |
| RangeDensityModel | recent | 1131 | 1245 | 115 | 0.7913 | 0.0870 |
| NeighborhoodModel | early | 901 | 1015 | 115 | 0.6435 | -0.1304 |
| NeighborhoodModel | middle | 1016 | 1130 | 115 | 0.8435 | 0.0174 |
| NeighborhoodModel | recent | 1131 | 1245 | 115 | 0.7043 | 0.0000 |
| GapNeighborhoodModel | early | 901 | 1015 | 115 | 0.6435 | -0.1304 |
| GapNeighborhoodModel | middle | 1016 | 1130 | 115 | 0.8174 | -0.0087 |
| GapNeighborhoodModel | recent | 1131 | 1245 | 115 | 0.7913 | 0.0870 |

rolling104-target 성능도 export/plot합니다. era·cadence에 걸친 stable positive effect가 없습니다. range/neighborhood는 fitted temporal parameter가 없어 fixed-config 결과가 cadence-invariant이고 Gap Logistic/combination은 달라질 수 있습니다.

## Candidate-pool / prize-aware — 동일 예산 virtual portfolio

동일 target·budget1/5/10/20·seed 42+target·unique nested tickets입니다. model은Top15,uniform은 전체45로 practical concentration과 broad coverage를 비교합니다. 모든 portfolio 후 actual/bonus를 읽으며 bonus는 training에 넣지 않습니다. coverage는 new five-subsets→uncovered grouped zones/outside→new pairs→seeded priority입니다. 2+2 quota는 없고 individual coverage는 pair에 암묵 포함되며 별도 최적 reward가 아닙니다.

| model | method | budget | mean_best_match | draws_ge4 | draws_ge5 | prize1_tickets | prize2_tickets | prize3_tickets | delta_best_vs_uniform | paired_ci_low | paired_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Frequency26 | weighted | 1 | 0.7304 | 0 | 0 | 0 | 0 | 0 | -0.0725 | -0.1681 | 0.0203 |
| Frequency26 | weighted | 5 | 1.4116 | 3 | 0 | 0 | 0 | 0 | -0.2870 | -0.3913 | -0.1768 |
| Frequency26 | weighted | 10 | 1.6116 | 4 | 0 | 0 | 0 | 0 | -0.4203 | -0.5362 | -0.2986 |
| Frequency26 | weighted | 20 | 1.7188 | 7 | 0 | 0 | 0 | 0 | -0.6406 | -0.7594 | -0.5101 |
| GapLogistic | weighted | 1 | 0.7884 | 0 | 0 | 0 | 0 | 0 | -0.0145 | -0.1333 | 0.1072 |
| GapLogistic | weighted | 5 | 1.5159 | 1 | 0 | 0 | 0 | 0 | -0.1826 | -0.2986 | -0.0754 |
| GapLogistic | weighted | 10 | 1.6580 | 3 | 0 | 0 | 0 | 0 | -0.3739 | -0.4725 | -0.2754 |
| GapLogistic | weighted | 20 | 1.7913 | 8 | 1 | 0 | 0 | 1 | -0.5681 | -0.6841 | -0.4493 |
| NeighborhoodModel | weighted | 1 | 0.7739 | 0 | 0 | 0 | 0 | 0 | -0.0290 | -0.1420 | 0.0899 |
| NeighborhoodModel | weighted | 5 | 1.4580 | 6 | 0 | 0 | 0 | 0 | -0.2406 | -0.3363 | -0.1391 |
| NeighborhoodModel | weighted | 10 | 1.6522 | 10 | 0 | 0 | 0 | 0 | -0.3797 | -0.4841 | -0.2725 |
| NeighborhoodModel | weighted | 20 | 1.7652 | 17 | 0 | 0 | 0 | 0 | -0.5942 | -0.7188 | -0.4580 |
| RangeDensityModel | weighted | 1 | 0.8609 | 2 | 0 | 0 | 0 | 0 | 0.0580 | -0.0522 | 0.1565 |
| RangeDensityModel | weighted | 5 | 1.4609 | 2 | 0 | 0 | 0 | 0 | -0.2377 | -0.3333 | -0.1275 |
| RangeDensityModel | weighted | 10 | 1.6899 | 3 | 0 | 0 | 0 | 0 | -0.3420 | -0.4638 | -0.2231 |
| RangeDensityModel | weighted | 20 | 1.8493 | 11 | 0 | 0 | 0 | 0 | -0.5101 | -0.6464 | -0.3797 |
| RangeDensityModel | range_coverage | 1 | 0.8406 | 2 | 0 | 0 | 0 | 0 | 0.0377 | -0.0696 | 0.1478 |
| RangeDensityModel | range_coverage | 5 | 1.5565 | 2 | 0 | 0 | 0 | 0 | -0.1420 | -0.2319 | -0.0464 |
| RangeDensityModel | range_coverage | 10 | 1.7623 | 3 | 0 | 0 | 0 | 0 | -0.2696 | -0.3855 | -0.1449 |
| RangeDensityModel | range_coverage | 20 | 1.8725 | 7 | 0 | 0 | 0 | 0 | -0.4870 | -0.6116 | -0.3681 |
| GapNeighborhoodModel | weighted | 1 | 0.8000 | 0 | 0 | 0 | 0 | 0 | -0.0029 | -0.1304 | 0.1130 |
| GapNeighborhoodModel | weighted | 5 | 1.4696 | 1 | 0 | 0 | 0 | 0 | -0.2290 | -0.3362 | -0.1275 |
| GapNeighborhoodModel | weighted | 10 | 1.6522 | 1 | 0 | 0 | 0 | 0 | -0.3797 | -0.5043 | -0.2580 |
| GapNeighborhoodModel | weighted | 20 | 1.7826 | 4 | 0 | 0 | 0 | 0 | -0.5768 | -0.7014 | -0.4522 |
| Uniform45 | uniform | 1 | 0.8029 | 1 | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| Uniform45 | uniform | 5 | 1.6986 | 2 | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| Uniform45 | uniform | 10 | 2.0319 | 4 | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| Uniform45 | uniform | 20 | 2.3594 | 9 | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |

range-aware20-ticket mean best1.8725 대 uniform2.3594입니다. 정보 없는 작은 pool 제한은 coverage를 줄이며 range allocation의 우위를 확립하지 못했습니다. 별도 정당화된 전략으로 range-aware allocation을 동결하지 않습니다. 세 scoring track은 experimental weighted/coverage portfolio를 남기되 우위를 주장하지 않습니다.

cadence별 portfolio_prize_events.csv를 저장했습니다. nested budget은 독립 event가 아니며 같은 ticket이 여러 budget에 나타납니다. five-main event 하나는 skill 증거가 아닙니다.

| model | method | target_draw | budget | prize1 | prize2 | prize3 |
| --- | --- | --- | --- | --- | --- | --- |
| GapLogistic | weighted | 1225 | 20 | 0 | 0 | 1 |

## 출력과 검증

당시 finite-axis 분석·두 scoring model·frozen gap combination·development selection·matched evaluation/portfolio·offline CLI·isolated publisher를 추가했습니다. 기존 formula/default는 유지했습니다.

명령은 `analyze-number-space`, `compare-number-space --cadence 26`, `compare-number-space --cadence 13`, `freeze-number-space`입니다. 연구 출력은 `reports/number_space/`이며11 plots에 rolling ranking·global null maxima도 포함됩니다. 전체45 score/rank/cutoff audit를 저장했습니다.

당시 baseline265 passed,2 skips에서 최종 **289 passed,2 dependency skips in45.05s**였습니다. verification.json에 기록했고 새 timing·boundary·selection·seeded null·ticket·publication·score consistency·integrity 테스트는 synthetic입니다. dependency 설치·network는 필요하지 않았습니다.

398 complete search 포함 analysis237.3s,frozen-selection rerun26은63.4s·13은65.1s입니다. 최초 development/평가136.9s이며 verified rerun에서 재선택하지 않았습니다. concurrent workload 영향을 받는 runtime입니다.

## Prospective experiment

한 번 독립 동결한 뒤 [Phase 10 원본](phase10-prospective.md)을 기록했습니다. 이전 Phase 5-9를 보존했고 당시 실제1246 결과 접근·commit/push는 없었습니다.

한 번 생성한 ID는 **draw 1246_phase10_numberspace_20261017T100839079270_ccb21ee9**,상태는 **FROZEN_UNEVALUATED**입니다. [원본](phase10-prospective.md)에 ranking·ticket/artifact link·SHA256이 있습니다. 당시 이전25파일·canonical hash가 같았고 frozen prediction 확인 뒤 model/parameter 변경은 없었습니다.

## 해석

선택된 neighborhood는 smoothing 없는 own-number control입니다. 이를 neighbor contribution의 근거로 해석할 수 없습니다.

## 한계

번호축 인접성의 의미, rolling overlap, finite mixing, development 선택과 역사 구간 재사용이 한계입니다.

## 다음 단계

[방법](number-space-analysis.md)과 [가설 노트](research-ideas.md)를 참고합니다. 다음 Phase 11 / H9는 BACKLOG이며 아직 실행되지 않았습니다. 현재 1246회는 새 prospective 대상이 아닙니다.
