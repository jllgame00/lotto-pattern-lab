# Phase27 / H17 결과

**NO_ENSEMBLE_ADVANTAGE_ESTABLISHED.** Development에서 고른 GapShape60%/Mirror40%는 validation을 통과하지 못했다. 사전 fallback인 네 후보 equal-rank 평균의 final Top6는0.765217, MWR는23.417391이다. Gap·development-best GapShape의 Top6=.834783보다 낮고 paired uncertainty는 개선을 지지하지 않는다. 후보 다양성이 조합의 예측 가치를 보장하지 않았다.

이 문서는 frozen 산출물의 결과 보고다. 자세한 설계·provenance는 [방법](final-ensemble-analysis.md), 원래 후보 결과와 현재 판정은 [후보 원장](weak-signal-candidates.md)에 있다. 전체 역사 연구는1–1245에 제한했다. 이전 Phase에서 반복 검토한 **retrospective** 자료이며 pristine holdout이 아니다.

## 실행·무결성

- Root: `D:/univ/personal/lotto-pattern-lab`; branch `main`; clean 시작 SHA `01d2eb7ef04c20a8052ab577a405811df418d7dc`.
- Dataset SHA256: `b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e`.
- PROSPECTIVE_ARCHIVE_STATUS=VERIFIED. 기존30files,12recorded SHA256. 원본 bytes를 유지한다.
- 공통901–1245(345), development901–1015 / validation1016–1130 / final1131–1245, 각각115targets.
- Gap/Graph/GapShape/Mirror는 연구 입력, MI는 AUDIT_ONLY로 제외. Baseline 포함7모델/2415causal rows의 기존 hit분포가 전부 재현되었다. 원본 missing CSV bytes를 검증했다고 주장하지 않는다.
- 47unique weights,11equal subsets; stacking과 raw-score ensemble은 구현하지 않았다.
- `python main.py final-ensemble prepare/replay/develop/validate/evaluate/robustness/finish/plots/audit`를 각 단계별로 실행했다. `evaluate`는 한 번이며 `final_started.json`이 재실행을 차단한다.

## 선택과 validation

후보 provenance의 machine-readable 전체 표는 [candidate_provenance.csv](../reports/final_ensemble/candidate_provenance.csv)다. 각 행은 exact configuration, 원래 prediction/config artifact 경로, 새 replay 경로, 평가 범위, 원래/재실행 Top6, paired uncertainty, robustness/sensitivity, null evidence, diversity, 이전 ensemble classification, 재현 여부를 담는다.

| 후보 | 공통901–1245 replay Top6 | 과거 원문 Top6 | 범위/재현 해석 |
|---|---:|---:|---|
| Gap Logistic | .834783 | .849379 | 원문 primary601–1244와 범위·fit calendar가 다름. H17은 후속901anchor cadence26 기록의 hit분포와 일치 |
| GraphStructureModel | .857971 | .8580 | 동일901–1245; 원문 반올림과 일치 |
| GapShapeModel | .837681 | .8377 | 동일901–1245; 원문 반올림과 일치 |
| MirrorModel | .826087 | .826087 | 동일901–1245 |
| MutualInformationModel | .843478 | .8435 | 동일901–1245; 감사용으로만 재현 |

모든 후보의 historical output을 새로 재현할 수 있었으나 과거 missing 원본의 byte-identical 재현 여부는 확인할 수 없다. 원래 paired intervals와 sensitivity는 [후보 원장](weak-signal-candidates.md)에서 범위별로 그대로 보존한다.

| 전략 | Development Top6 / MWR | Validation Top6 / MWR | gate |
|---|---|---|---|
| equal-all4 | .800000 /22.894203 | .965217 /22.613043 | fallback 기준 |
| 일반 equal subset: GapShape/Mirror50/50 | .886957 /22.423188 | .878261 /22.813043 | 실패 |
| diversity-aware subset: 동일50/50 | .886957 /22.423188 | .878261 /22.813043 | 실패 |
| primary weighted: GapShape/Mirror60/40 | .843478 /22.350725 | .913043 /22.753623 | 실패 |
| 개발 best single: GapShape | .800000 /22.457971 | .878261 /22.581159 | reference |
| Gap Logistic | .756522 /23.169565 | .913043 /22.662319 | reference |

개발 MWR 기준 최선 equal subset은50/50이다. 높은 개발 Top6나 validation에서 좋은 다른 weights를 보고 설정을 바꾸지 않았다. 동결 최종 audit subset은Gap/Graph/GapShape/Mirror, weights=.25씩이다. 이는 검증된 ensemble 승격이 아니다.

## Reporting-only 정정

처음 `main_summary.json`의 random-weight raw tail=.005는 CSV default float parser의 동률 손실이었다. 동일 fallback197개가 약9e−17 낮게 읽혀 `>=`에서 제외되었다. `round_trip` parsing과1e−12 numerical tolerance로 올바른 값은 **.990=(1+197)/200**이다. Random-candidate는.445로 동일하다. 원래 summary·protocol·development·validation·final-start·configuration seals를 보존하고 [reporting_correction.json](../reports/final_ensemble/reporting_correction.json)에 원본 SHA와 정정 근거를 남겼다. 선택·final 평가·판정·readiness는 변경하지 않았다. 이후 표와 해석은 정정값을 따른다.

정정 명령은 `python -m src.analysis.final_ensemble_reporting`이다. 이미 존재하는 정정 record는 덮어쓰지 않는다. 원래 scientific source는 동결 증거로 유지했으므로 `finish`의 raw tail을 단독 인용하지 않는다. `audit`가 정정 record와 원본 SHA를 검증한다. 이 역사 실행은 일반적인 미래 모델 선택 서비스로 배포하지 않는다.

## 최종 해석

Gate가 실패했으므로 promoted gain=0이며 promotion tail inference는 해당 없음이다. Random-weight gate2/199, random-candidate gate11/199로 임의 혼합/순위에서도 일부 validation 통과가 발생했다. 두 raw tail fractions는 selection 진단이지 calibrated p-value가 아니다. .990/.445 어느 쪽도 ensemble 우위를 확립하지 않는다.

세 구간 audit ensemble Top6=.800000/.965217/.765217로 validation의 상승이 final에 이어지지 않았다. Cadence13 final도 Top6=.756522로 약했다. Final 시작점을1170/1208로 바꾸어도 MWR가 Gap보다 나쁘다. LOO에서 Mirror를 빼면 세 구간 MWR가 좋아지지만 Top6 방향은 일관되지 않는다. Final에서 GapShape 제거 시 Top6가 좋아지는 것은 사후 관찰이며 동결 조합을 고치는 근거로 사용하지 않았다.

최종 ledger에서 네 연구 입력과 MI 모두 H17 **AUDIT_ONLY**다. 이전 Graph/GapShape/Mirror의 탐색적 ENSEMBLE CANDIDATE 기록과 MI의 NOT CURRENTLY JUSTIFIED는 삭제하지 않았다. 새로운 predictor/feature family를 만들지 않았고 검증된 ensemble로 배포하지 않는다.

Configuration-only record는 `H17_CONFIGURATION_FROZEN_NOT_CURRENTLY_JUSTIFIED`, **ready_for_1247=false**다. 실제1246을 fetch/import/사용하지 않았고1247 번호 예측도 생성하지 않았다. 기존 prospective archive는 수정하지 않았다. Commit/push는 하지 않았다.

<!-- GENERATED_METRICS -->

## Frozen output 상세

아래 수치는 저장된 CSV/NPZ에서만 렌더링했으며 모델을 재실행하거나 재선택하지 않았다.

### Final metrics

| model | avg_top6 | mean_winning_rank | recall6 | recall10 | recall15 |
|---|---|---|---|---|---|
| GapLogistic | 0.834783 | 23.271014 | 0.139130 | 0.215942 | 0.321739 |
| GraphStructureModel | 0.878261 | 22.326087 | 0.146377 | 0.243478 | 0.350725 |
| GapShapeModel | 0.834783 | 23.468116 | 0.139130 | 0.236232 | 0.336232 |
| MirrorModel | 0.791304 | 23.628986 | 0.131884 | 0.215942 | 0.320290 |
| MutualInformationModel | 0.886957 | 22.386957 | 0.147826 | 0.242029 | 0.359420 |
| RandomModel | 0.704348 | 23.089855 | 0.117391 | 0.208696 | 0.326087 |
| Frequency26 | 0.747826 | 23.659420 | 0.124638 | 0.200000 | 0.297101 |
| EqualAll | 0.765217 | 23.417391 | 0.127536 | 0.233333 | 0.339130 |
| OrdinarySubset | 0.782609 | 23.747826 | 0.130435 | 0.218841 | 0.320290 |
| DiversitySubset | 0.782609 | 23.747826 | 0.130435 | 0.218841 | 0.320290 |
| WeightedWinner | 0.713043 | 23.718841 | 0.118841 | 0.221739 | 0.320290 |
| SelectedEnsemble | 0.765217 | 23.417391 | 0.127536 | 0.233333 | 0.339130 |

Best single은 final 최고 모델을 사후 선택한 것이 아니라 development에서 고정한 GapShape다. Final에서는 Graph가 더 좋았지만 선택을 바꾸지 않았다.

Hit distribution과 ≥5/all-six pool events:

| model | hits0 | hits1 | hits2 | hits3 | hits4 | hits5 | hits6 | ge5_pool8 | ge5_pool10 | ge5_pool12 | ge5_pool15 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GapLogistic | 46 | 46 | 19 | 4 | 0 | 0 | 0 | 0 | 1 | 1 | 1 |
| GraphStructureModel | 39 | 54 | 19 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| GapShapeModel | 44 | 50 | 18 | 2 | 1 | 0 | 0 | 1 | 1 | 1 | 2 |
| MirrorModel | 48 | 46 | 18 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| MutualInformationModel | 44 | 44 | 23 | 4 | 0 | 0 | 0 | 0 | 0 | 1 | 2 |
| RandomModel | 53 | 45 | 15 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Frequency26 | 48 | 51 | 13 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| EqualAll | 52 | 42 | 18 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| OrdinarySubset | 47 | 50 | 14 | 4 | 0 | 0 | 0 | 0 | 1 | 1 | 2 |
| DiversitySubset | 47 | 50 | 14 | 4 | 0 | 0 | 0 | 0 | 1 | 1 | 2 |
| WeightedWinner | 50 | 50 | 13 | 2 | 0 | 0 | 0 | 0 | 0 | 1 | 2 |
| SelectedEnsemble | 52 | 42 | 18 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |

모든 비교의 final all-six pool events(6/8/10/12/15)는0이다. 전체36행/모든 metric은 [performance.csv](../reports/final_ensemble/performance.csv)에 있다.

### Paired bootstrap

양수 improvement가 ensemble에 유리하다. 아래 nominal95% 및 각 비교98.333% Bonferroni 구간은 모두0을 포함한다. 후자는 metric별3references에 대해95% family-wise coverage를 목표로 하며 두 metric을 합친6개 비교의 동시구간은 아니다.

| reference | metric | difference | ci_low | ci_high | simultaneous_low | simultaneous_high |
|---|---|---|---|---|---|---|
| RandomModel | mean_winning_rank_improvement | -0.327536 | -1.131884 | 0.521920 | -1.264300 | 0.663768 |
| RandomModel | top6_improvement | 0.060870 | -0.113043 | 0.243478 | -0.142101 | 0.286957 |
| GapLogistic | mean_winning_rank_improvement | -0.146377 | -0.801522 | 0.513152 | -0.919336 | 0.649771 |
| GapLogistic | top6_improvement | -0.069565 | -0.182609 | 0.034783 | -0.200000 | 0.060870 |
| GapShapeModel | mean_winning_rank_improvement | 0.050725 | -0.853659 | 0.876993 | -1.078792 | 1.012693 |
| GapShapeModel | top6_improvement | -0.069565 | -0.217391 | 0.086957 | -0.252174 | 0.121739 |

Block13/52 sensitivity를 포함한 전체 구간은 [paired.csv](../reports/final_ensemble/paired.csv). 유리한 block을 골라 결론을 바꾸지 않는다.

### Diversity

| left | right | spearman | winner_rank_error_correlation | top6_hit_correlation | top6_overlap | top10_overlap | top15_overlap |
|---|---|---|---|---|---|---|---|
| GapLogistic | GraphStructureModel | 0.061103 | 0.143083 | 0.163140 | 1.043478 | 2.739130 | 5.507246 |
| GapLogistic | GapShapeModel | -0.035679 | 0.002793 | -0.074736 | 0.660870 | 1.997101 | 4.756522 |
| GapLogistic | MirrorModel | 0.007219 | 0.042242 | 0.049839 | 0.739130 | 2.000000 | 5.043478 |
| GapLogistic | MutualInformationModel | -0.209532 | -0.205301 | -0.003918 | 0.478261 | 1.524638 | 3.162319 |
| GraphStructureModel | GapShapeModel | 0.002410 | 0.013139 | 0.004566 | 0.785507 | 2.228986 | 5.046377 |
| GraphStructureModel | MirrorModel | 0.024562 | 0.046147 | 0.010889 | 0.947826 | 2.394203 | 5.150725 |
| GraphStructureModel | MutualInformationModel | -0.006221 | -0.167767 | -0.052857 | 0.742029 | 2.098551 | 4.765217 |
| GapShapeModel | MirrorModel | -0.005878 | -0.000375 | 0.047071 | 0.739130 | 2.205797 | 5.008696 |
| GapShapeModel | MutualInformationModel | 0.057248 | 0.057655 | 0.169067 | 1.023188 | 2.634783 | 5.414493 |
| MirrorModel | MutualInformationModel | -0.002914 | -0.072491 | 0.002641 | 0.742029 | 2.231884 | 5.020290 |

Gap–GapShape Spearman≈−.0357, Gap–Graph≈.0611, Mirror와 다른 입력은≈−.0059~.0246이다. Gap과GapShape는 같은 ranking이 아니며 Mirror/Graph도 다른 순위를 제공했다. MI–Gap≈−.2095의 차이도 MI의 예측 자격을 복원하지 않는다. 낮은 상관은 정보나 예측력의 증거가 아니다.

### Frozen robustness

| start | end | model | targets | avg_top6 | mean_winning_rank |
|---|---|---|---|---|---|
| 1131 | 1245 | SelectedEnsemble | 115 | 0.765217 | 23.417391 |
| 1131 | 1245 | GapLogistic | 115 | 0.834783 | 23.271014 |
| 1131 | 1245 | GapShapeModel | 115 | 0.834783 | 23.468116 |
| 1170 | 1245 | SelectedEnsemble | 76 | 0.763158 | 23.826754 |
| 1170 | 1245 | GapLogistic | 76 | 0.789474 | 23.554825 |
| 1170 | 1245 | GapShapeModel | 76 | 0.828947 | 23.616228 |
| 1208 | 1245 | SelectedEnsemble | 38 | 0.763158 | 23.197368 |
| 1208 | 1245 | GapLogistic | 38 | 0.736842 | 23.057018 |
| 1208 | 1245 | GapShapeModel | 38 | 0.921053 | 22.723684 |

Cadence13:

| scope | model | avg_top6 | mean_winning_rank |
|---|---|---|---|
| development | SelectedEnsemble | 0.817391 | 22.891304 |
| development | GapLogistic | 0.756522 | 23.168116 |
| development | GapShapeModel | 0.800000 | 22.457971 |
| validation | SelectedEnsemble | 0.982609 | 22.589855 |
| validation | GapLogistic | 0.913043 | 22.600000 |
| validation | GapShapeModel | 0.878261 | 22.581159 |
| final | SelectedEnsemble | 0.756522 | 23.405797 |
| final | GapLogistic | 0.826087 | 23.242029 |
| final | GapShapeModel | 0.834783 | 23.468116 |

### Leave-one-component-out

Change는 제거후−full이다. MWR change 음수가 개선이며 correlation은 full조합과의 Spearman이다.

| scope | removed | avg_top6 | mean_winning_rank | top6_change | winner_rank_change | spearman_with_full |
|---|---|---|---|---|---|---|
| development | GapLogistic | 0.886957 | 22.884058 | 0.086957 | -0.010145 | 0.853207 |
| development | GraphStructureModel | 0.860870 | 22.604348 | 0.060870 | -0.289855 | 0.854663 |
| development | GapShapeModel | 0.808696 | 23.139130 | 0.008696 | 0.244928 | 0.855553 |
| development | MirrorModel | 0.834783 | 22.795652 | 0.034783 | -0.098551 | 0.849469 |
| validation | GapLogistic | 1.008696 | 22.711594 | 0.043478 | 0.098551 | 0.854246 |
| validation | GraphStructureModel | 1.008696 | 22.575362 | 0.043478 | -0.037681 | 0.849829 |
| validation | GapShapeModel | 0.808696 | 22.652174 | -0.156522 | 0.039130 | 0.848369 |
| validation | MirrorModel | 0.921739 | 22.514493 | -0.043478 | -0.098551 | 0.846043 |
| final | GapLogistic | 0.765217 | 23.223188 | 0.000000 | -0.194203 | 0.841525 |
| final | GraphStructureModel | 0.817391 | 23.746377 | 0.052174 | 0.328986 | 0.844393 |
| final | GapShapeModel | 0.913043 | 23.265217 | 0.147826 | -0.152174 | 0.844549 |
| final | MirrorModel | 0.782609 | 23.115942 | 0.017391 | -0.301449 | 0.841889 |

### Placebo diagnostics

| kind | replicates | gate_pass | final_raw_gain_mean | final_raw_gain_q025 | final_raw_gain_q975 |
|---|---|---|---|---|---|
| random_candidate | 199 | 11 | -0.003802 | -0.837754 | 0.910290 |
| random_weight | 199 | 2 | 0.046967 | 0.050725 | 0.050725 |

정정된 raw exceedance: random-weight=.990, random-candidate=.445. 실제 gate실패로 promotion inference는 해당 없음. [398replicates](../reports/final_ensemble/placebos.csv)와 [정정](../reports/final_ensemble/reporting_correction.json)을 함께 읽는다.

### Equal-budget portfolios

각 count는115draw에 대한10seed 평균이다. 동일 예산/seed와 nested unique prefixes를 사용했다. Mean best main matches는 ticket portfolio당 가장 좋은 main match 수다. BestSingle은GapShape다.

| method | budget | mean_best_main | ge4_mean_count | ge5_mean_count | prize2_mean_count | prize3_mean_count |
|---|---|---|---|---|---|---|
| SelectedEnsembleWeighted | 1 | 0.820870 | 0.400000 | 0.000000 | 0.000000 | 0.000000 |
| SelectedEnsembleWeighted | 5 | 1.412174 | 1.000000 | 0.000000 | 0.000000 | 0.000000 |
| SelectedEnsembleWeighted | 10 | 1.546957 | 2.700000 | 0.000000 | 0.000000 | 0.000000 |
| SelectedEnsembleWeighted | 20 | 1.613913 | 4.500000 | 0.000000 | 0.000000 | 0.000000 |
| SelectedEnsembleCoverage | 1 | 0.820870 | 0.400000 | 0.000000 | 0.000000 | 0.000000 |
| SelectedEnsembleCoverage | 5 | 1.502609 | 1.200000 | 0.000000 | 0.000000 | 0.000000 |
| SelectedEnsembleCoverage | 10 | 1.580000 | 2.700000 | 0.000000 | 0.000000 | 0.000000 |
| SelectedEnsembleCoverage | 20 | 1.632174 | 4.800000 | 0.000000 | 0.000000 | 0.000000 |
| GapLogisticWeighted | 1 | 0.759130 | 0.300000 | 0.000000 | 0.000000 | 0.000000 |
| GapLogisticWeighted | 5 | 1.313043 | 1.200000 | 0.100000 | 0.000000 | 0.100000 |
| GapLogisticWeighted | 10 | 1.425217 | 1.600000 | 0.100000 | 0.000000 | 0.100000 |
| GapLogisticWeighted | 20 | 1.482609 | 2.200000 | 0.100000 | 0.000000 | 0.100000 |
| BestSingleWeighted | 1 | 0.828696 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| BestSingleWeighted | 5 | 1.387826 | 0.500000 | 0.000000 | 0.000000 | 0.000000 |
| BestSingleWeighted | 10 | 1.530435 | 1.200000 | 0.000000 | 0.000000 | 0.000000 |
| BestSingleWeighted | 20 | 1.596522 | 2.200000 | 0.000000 | 0.000000 | 0.000000 |
| UniformRandom | 1 | 0.838261 | 0.300000 | 0.000000 | 0.000000 | 0.000000 |
| UniformRandom | 5 | 1.746957 | 1.300000 | 0.100000 | 0.000000 | 0.100000 |
| UniformRandom | 10 | 2.100000 | 1.700000 | 0.100000 | 0.000000 | 0.100000 |
| UniformRandom | 20 | 2.392174 | 3.200000 | 0.100000 | 0.000000 | 0.100000 |

Uniform random의5/10/20ticket best-match가 더 높다. Top12 집중은 coverage를 제한하므로 이 결과를 ranking 자체와 같은 지표로 해석하지 않는다. Ensemble20ticket의≥4빈도가 상대적으로 높은 것은 희귀 기술치이며 우위 검증이 아니다. 모든2nd-equivalent는0,3rd-equivalent는 일부Gap/random seed에서만1회였다. 수익성 주장은 하지 않는다. [전체23,000records](../reports/final_ensemble/portfolio_draws.csv).

### Configuration-only freeze

[configuration_freeze.json](../reports/final_ensemble/configuration_freeze.json)은 후보·원래설정·weights·ticket rules·seeds·cutoff·Git/data/source hashes를 담는다. 실제번호 예측은 없다.

- File SHA256: `094c1cc46a600a7ad98febc8ccd19df6da09ed8313774d605f018d2c07cffc23`
- Canonical payload SHA256: `f0015558c86beb3531bad81fc1e2cef5a5ce498213bdba48cc968f1f2f117de5`

**H17_CONFIGURATION_FROZEN_READY_FOR_1247=false.** Negative 연구 설정의 보존이며 prospective 실행 승인이나 추천이 아니다.

### Plots와 감사

[plots/](../reports/final_ensemble/plots/)의12개 그림은 후보성능·Spearman·Top6overlap·세구간·subset·weights·두placebo·finalcomparison·LOO·winner-rank·portfolio를 포함한다. 그림은 검사 보조자료다.

[audit_result.json](../reports/final_ensemble/audit_result.json)은 source/archive/stagechain, 모든performance/paired/diversity/LOO/robustness, 대표base-score 재현, placebo seed/replay sample, 전체portfolio 기록을 독립 검사한다. Gap의 전체 fit을 감사에서 다시 학습하지 않았다는 제한은 명시했다.

## 테스트·최종 검증

`python -m pytest -q --basetemp=reports/final_ensemble/pytest_full`:
**1336 passed, 4 failed, 2 skipped**, 225.85초. 전체 suite가 모두 통과했다고 주장하지 않는다.
실패는 작업 전 baseline에서도 재현된 동일4건이며 모두 Windows multiprocessing named-pipe `CreateFile`의 `PermissionError: [WinError 5]`다.

```text
tests/test_complexity_search.py::test_independent_calibration_complete_null_determinism
tests/test_random_matrix_search.py::test_worker_count_does_not_change_seeded_results
tests/test_recurrence_pipeline.py::test_parallel_null_same_as_serial
tests/test_topology_search.py::test_parallel_seeds_equal_serial_searches
```

이전 Phase부터 알려진 병렬 worker 생성 환경 문제로, H17 변경 후 새 실패는 없다. 기존4테스트나 multiprocessing 구현을 임의 변경/skip하지 않았다. [시작 baseline log](../reports/final_ensemble/windows_baseline_tests.log)와 [전체 log](../reports/final_ensemble/full_tests.log)를 보존했다.

최종 H17/ledger 집중 테스트는 **90 passed**([log](../reports/final_ensemble/targeted_tests.log)). 기존 ledger10개에서19개로 늘었고 H17 신규71개를 추가했다. Representation loading·정확한 교집합·ties·correlation·TopK·chronological isolation·47templates·validation·bootstrap·LOO·두placebo·portfolio·ledger history·configuration-only freeze·actual1246차단·1247미생성·archive integrity·동률 정정을 검증했다. RED→GREEN regression과 Astra 설계/최종 review를 수행했다.

최종 `evidence_ledger --check`, `git diff --check`, `final-ensemble audit`를 확인했다. Audit는 **PASS**, 기존 보호파일435개와 archive30files/12recorded hashes가 시작 inventory와 같다. Data hash와 HEAD도 동일하다. 그림12개를 렌더링하여 확인했다. Seal hash chain은 현재 파일 일관성의 증거이며 외부 trusted timestamp는 아니다.

## 정확한 변경 파일

Git 기준 기존파일10개 수정, 신규16개, 총26개다. 그 외 기존 source/model/data는 변경하지 않았다.

```text
M  .gitignore
M  README.md
M  docs/README.md
M  docs/research-evidence-synthesis.md
M  docs/research-ideas.md
M  docs/weak-signal-candidates.json
M  docs/weak-signal-candidates.md
M  src/analysis/evidence_ledger.py
M  src/cli.py
M  tests/test_evidence_ledger.py
A  docs/final-ensemble-analysis.md
A  docs/final-ensemble-results.md
A  docs/superpowers/plans/2026-10-18-phase27.md
A  src/analysis/final_ensemble.py
A  src/analysis/final_ensemble_audit.py
A  src/analysis/final_ensemble_inputs.py
A  src/analysis/final_ensemble_plots.py
A  src/analysis/final_ensemble_portfolio.py
A  src/analysis/final_ensemble_reporting.py
A  src/final_ensemble_cli.py
A  tests/test_final_ensemble.py
A  tests/test_final_ensemble_audit.py
A  tests/test_final_ensemble_cli.py
A  tests/test_final_ensemble_inputs.py
A  tests/test_final_ensemble_portfolio.py
A  tests/test_final_ensemble_reporting.py
```

`A`는 아직 commit/stage하지 않은 신규 working-tree 파일이다. Git-ignored 연구 산출물은 `reports/final_ensemble/`에 있다. [delivery_manifest.json](../reports/final_ensemble/delivery_manifest.json)에 위26파일과 연구 산출물의 정확한 상대경로/SHA256을 기록했다. Pytest 임시 작업 디렉터리와 manifest 자기 자신은 산출물 inventory에서 제외했다.

**확인:** 실제1246 미사용·미수집·미import,1247number prediction 미생성, old prospective archive 무변경, 신규 가설/feature family 없음, commit/push 없음. Phase27/H17 역사 ensemble 연구와 감사용 configuration freeze에서 종료했다.

