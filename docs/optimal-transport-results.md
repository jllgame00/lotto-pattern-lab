# Phase 24 — H23 Optimal Transport / Wasserstein geometry 결과

**H23: TESTED / INCONCLUSIVE.** 동일 complete-search null calibration 후 OT geometry의 추가 구조 근거가 남지 않았다.
**PREDICTIVE_MODEL_NOT_JUSTIFIED / NOT CURRENTLY JUSTIFIED**다.
이는 randomness의 증명이나 모든 transport 구조의 부재 판정은 아니다.
[방법](optimal-transport-analysis.md) · [계획·review 기록](superpowers/plans/2026-10-18-phase24.md).

## 시작 상태·자료·prospective 원본

- Git root: `D:/univ/personal/lotto-pattern-lab`; branch: `main`.
- 시작 SHA: `d416099e729b99bd5837c70ef430df3c70d8c3e9`. 처음 worktree는 clean이었고 Phase23/H22 완료 상태였다.
- README/docs index/research ideas/canonical CSV/src/tests 존재를 확인했다. 무관한 source/data 변경은 없었다.
- 실제 자료는 **1–1245회**, 개발1–900, 이후901–1245다. 1246회 결과는 어떤 역사 분석·선택·null·평가에도 쓰지 않았다.
- Canonical CSV SHA-256: `b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e`.
- **PROSPECTIVE_ARCHIVE_STATUS = VERIFIED**. 기존 Phase5–10 archive는30files이며6integrity records의12대상 SHA-256이 모두 일치한다.
- Registry/reservation/integrity record를 포함한30파일 전체 byte hash가 종료 audit에서도 동일하다.
- VERIFIED는 기존 기록과의 일치를 뜻하며 독립적인 역사 archive 완전성 증명은 아니다. 누락물을 docs에서 재구성하지 않았다.

전체 초기 archive inventory와 각 검증 결과는 `reports/optimal_transport/starting_state.json`에 있다.
당시 디렉터리가 없었던 이전 Phase 문서의 archive 상태를 이번 결과로 소급 수정하지 않는다.

## 표현·검색공간

각 draw는 `μ=(1/6)Σδ[x_(i)]`, 정렬된 여섯 equal mass다.
Monotone matching의 exact `W1=mean(abs(b_i-a_i))`, `W2=sqrt(mean((b_i-a_i)^2))`를 사용한다.
W1 primary/W2 secondary이며 Sinkhorn/regularization은 사용하지 않는다.
Signed vector는 여섯 **order statistics**의 이동이며 물리적 공의 정체성 이동이 아니다.

Lag={1,2,3,4,8,13,26}, rolling W={26,52,104}, step={1,4,13,26}, barycenter W={10,26,52}다.
개발·전체 모두 **132cells/132eligible**, family별36/19/10/39/24/4cells를 검색했다.
전체 inventory·각 cell raw값·z는 `development_metrics.csv`, `full_metrics.csv`에 있다.
Parameters는 [방법 문서](optimal-transport-analysis.md)에 명시했으며 결과에 따라 늘리거나 줄이지 않았다.

IID32pilot를 scope별로 독립 생성하고 abs z를 동결했다. Main은 **IID199 + fixed-margin199**이며 scope별로 새로 생성했다.
Surrogate마다 모든 measure/vector/lag/rolling state/barycenter/geodesic을 재구성하고 **자신의 family global maximum**을 저장했다.
Full+development raw vectors796개를 보존했다. Main seed240042/pilot seed241001, fixed-margin20trades/row다.
`p=(1+exceed)/200`, Bonferroni6을 적용한다. 두 null은 각각 보고하며 유리한 한쪽을 선택하지 않는다.
Windows named-pipe 제한으로 workers1을 사용했고 main runtime은 779.594초였다.

## 전체 1–1245 global-max 결과

각 행은 해당 family의 실제 전체 winner다. p는 **global / corrected** 순서다.

| Family | Winner | Raw | max abs z | IID p | Fixed-margin p |
|---|---|---|---|---|---|
| lag_magnitude | W1_lag8_std | 3.664935418 | 2.281286148 | 0.385 / 1.000 | 0.390 / 1.000 |
| direction | acceleration_repeat_cosine | -0.583475957 | 2.104644416 | 0.400 / 1.000 | 0.435 / 1.000 |
| successor | euclidean_nearest_distance | 0.324248117 | 2.518794805 | 0.255 / 1.000 | 0.205 / 1.000 |
| rolling_drift | W52_step4_reversal | 0.681215022 | 2.640947744 | 0.290 / 1.000 | 0.325 / 1.000 |
| barycenter | W10_W1_movement | 0.746461372 | 2.103629663 | 0.335 / 1.000 | 0.295 / 1.000 |
| geodesic | W2_std | 3.242546669 | 0.173549630 | 0.985 / 1.000 | 0.990 / 1.000 |

모든 corrected p가 .05보다 크므로 **OT geometry는 이번 null calibration을 통과하지 못했다**.
Family winner가 secondary statistic이어도 생략하지 않았다.

## 개발 1–900 결과·동결 gate

| Family | Winner | Raw | max abs z | IID p | Fixed-margin p |
|---|---|---|---|---|---|
| lag_magnitude | W1_lag4_std | 3.776480208 | 3.359169508 | 0.065 / 0.390 | 0.100 / 0.600 |
| direction | normalized_dot_lag1 | -0.362679589 | 3.121343614 | 0.035 / 0.210 | 0.040 / 0.240 |
| successor | euclidean_cosine_gain | 0.203234025 | 1.642139889 | 0.620 / 1.000 | 0.550 / 1.000 |
| rolling_drift | W26_step13_reversal | 0.882646266 | 2.071221003 | 0.675 / 1.000 | 0.635 / 1.000 |
| barycenter | W10_W1_movement | 0.757686539 | 3.292056455 | 0.040 / 0.240 | 0.045 / 0.270 |
| geodesic | W1_std | 2.905729603 | 0.622269548 | 0.865 / 1.000 | 0.905 / 1.000 |

Continuation은 선택 metric의 cosine/distance gain 각각에 방향상 유리한 corrected evidence가 두 null 모두 필요하다.
양의 raw gain, 큰 양방향 family anomaly 또는 unrelated nearest-vector anomaly만으로 모델을 허용하지 않는다.
그 gate는 실패했다. 선택 파일은 `selected_configuration.json`, SHA-256은
`2419411740965b8ca79f907c1e83865aceaa4087fbf0de878d91673bfe2b93dc`다.
이 결정에는901회 이후 자료·full null 결과를 사용하지 않았다. 고정 parameter 외 smoothing/kernel/model을 later에서 선택하지 않았다.

## Draw-to-draw 분포와 magnitude memory

연속 W1의 n=1244, 평균=7.278403001, std=3.479367012,
median=6.666666667, 5–95%=2.833333333–14.308333333,
범위=1.333333333–22.500000000다.
연속 W2 평균=8.527771922, std=3.754602740다.

| Lag | W1 mean | W1 std | W1 median |
|---|---|---|---|
| 1 | 7.278403001 | 3.479367012 | 6.666666667 |
| 2 | 7.374631268 | 3.582151113 | 6.500000000 |
| 3 | 7.386070853 | 3.620799109 | 6.666666667 |
| 4 | 7.404109589 | 3.656938985 | 6.666666667 |
| 8 | 7.426704392 | 3.664935418 | 6.833333333 |
| 13 | 7.272862554 | 3.456232794 | 6.666666667 |
| 26 | 7.361908668 | 3.523787825 | 6.666666667 |

가장 큰 lag-family anomaly는 위 표의 W1 lag8 std이며 global correction을 통과하지 못했다.
W1 magnitude lag1 Spearman=0.123537745이다. 나머지 bounded-lag 값과 conditional quartile은
`descriptive_summary.json`에 있다. Transport-specific memory 이상의 장기 의존성 주장은 하지 않는다.

## 방향·반전·successor

연속 transport cosine=-0.420896061, normalized dot=-0.380943504,
mean-shift sign agreement=0.333065165, coordinate sign agreement=0.296862430다.
Directional lag16cells만의 가장 큰 standardized anomaly는 `cosine_lag1`, raw=-0.420896061, abs z=1.850090471다.
Direction family 전체 winner는 acceleration-repeat cosine이며 같은 family 보정에 포함했다.
중간 draw를 공유하는 IID에서도 반전이 생기므로 음의 cosine 자체는 evidence가 아니다.

| Vector metric | -rho(X,next cosine) | rho(X,next distance) | NN cosine gain | NN distance gain |
|---|---|---|---|---|
| euclidean | 0.140424834 | 0.219737547 | 0.213450947 | 1.857053527 |
| cosine | 0.188875658 | 0.142342882 | 0.233653006 | 1.849973083 |

Disjoint event pair는85905개, nearest query는1240개다. Pair 간 dependence를 독립 표본 p-value로 처리하지 않고
whole-history surrogate에 동일하게 재구성했다. NN gain은 같은 admissible historical successor 평균 대비다.
Raw positive relation/gain은 존재하지만 surrogate global-max를 넘는 continuation 근거는 없다.
Euclidean scale은 완성된 분석 scope 전체에서 구한 retrospective scale이며 causal walk-forward 성능이 아니다.

## Rolling distribution drift

ν는 이전 W completed draw의6W출현을 normalized mass로 만든다. Discrete W1은 CDF 차이 절댓값의 합이다.
아래 raw peak는 descriptive이며 overlap을 포함한 동일 null에서 보정했다.

| W | Step | Mean W1 | Peak W1 | Peak endpoint |
|---|---|---|---|---|
| 26 | 1 | 0.283150333 | 0.826923077 | 839 |
| 26 | 4 | 0.577434421 | 1.730769231 | 95 |
| 26 | 13 | 1.004036284 | 3.134615385 | 1135 |
| 26 | 26 | 1.400356483 | 3.814102564 | 1138 |
| 52 | 1 | 0.140679068 | 0.516025641 | 213 |
| 52 | 4 | 0.286977483 | 0.778846154 | 515 |
| 52 | 13 | 0.497883150 | 1.221153846 | 915 |
| 52 | 26 | 0.681133649 | 1.916666667 | 922 |
| 104 | 1 | 0.068502944 | 0.224358974 | 312 |
| 104 | 4 | 0.144219503 | 0.402243590 | 157 |
| 104 | 13 | 0.249734562 | 0.671474359 | 861 |
| 104 | 26 | 0.358784808 | 0.871794872 | 869 |

가장 강한 drift-family winner는 W52/step4의 adjacent signed-CDF movement cosine이다.
이 표의 smoothness/peak/return을 별도 유의한 신호로 세지 않는다. Family 보정 후 근거가 없다.

## Barycenter·geodesic·acceleration

평균 quantile은 W2 barycenter이며 **trivial sorted-position mean과 정확히 같다**.
W1 barycenter의 median과 구분하고 실수 좌표를 반올림하지 않는다.
Training-only rolling center에 대한 next-draw W1과 causal cumulative mean baseline은 다음과 같다.

| Window | Next W1 | Cumulative mean baseline W1 | Baseline minus rolling | Sorted mean max difference |
|---|---|---|---|---|
| 10 | 5.535438596 | 5.308195774 | -0.227242823 | 0 |
| 26 | 5.371395217 | 5.293999947 | -0.077395270 | 0 |
| 52 | 5.334289767 | 5.298725007 | -0.035564761 | 0 |

모든 window에서 cumulative baseline보다 next distance가 더 컸다. 최근 draw의 in-sample 근접성을 예측력으로 보지 않는다.
IID/fixed-margin barycenter-family global comparison도 통과하지 못했다. 별도의 WassersteinBarycenterModel은 정당화되지 않는다.
전체 causal quantile trajectory·최근 평균/다음 draw distance는 `barycenters.csv`,
각 최근 draw의 개별 거리는 `barycenter_recent_distances.csv`에 저장했다.

Historical unconditional 비교로 각 training endpoint의 전체 과거 draw empirical distribution을
같은 recent barycenter에 대입한 평균 W1도 계산했다. 아래는 추가 **descriptive inspection**이며 새 p-value·선택·모델 gate에 사용하지 않았다.
Null 범위는 이미 사전 검색한 next-distance cell의199history 평균 통계의5–95%다. 개별 next draw prediction interval이 아니다.

| Window | Historical unconditional mean W1 | Observed next mean W1 | IID null mean-stat 5–95% | Fixed null mean-stat 5–95% |
|---|---|---|---|---|
| 10 | 5.576479594 | 5.535438596 | 5.356621–5.581131 | 5.346686–5.591703 |
| 26 | 5.458868843 | 5.371395217 | 5.231079–5.436409 | 5.212206–5.440524 |
| 52 | 5.426311742 | 5.334289767 | 5.177875–5.387884 | 5.176167–5.410582 |

Geodesic midpoint residual의 평균 W1=6.321802092, W2=7.349365771다.
미래 draw를 사용하는 **DESCRIPTIVE ONLY**이며 smoother-than-null 근거가 없다.
Acceleration absolute 평균=12.643604183, RMS 평균=14.698731542다.
Geodesic residual=acceleration magnitude/2의 동일성을 확인했으며 독립 evidence로 중복 계산하지 않는다.

## 시간 안정성

고정된 full family winner의 raw 통계를 early1–415/middle416–830/recent831–1245에서 다시 보았다.
서로 다른 표본 크기의 통계를 새로운 검정으로 비교하거나 유리한 era를 선택하지 않는다.

| Family | Fixed winner | Early | Middle | Recent |
|---|---|---|---|---|
| lag_magnitude | W1_lag8_std | 3.891763835 | 3.465093646 | 3.647900901 |
| direction | acceleration_repeat_cosine | -0.589670350 | -0.566276091 | -0.595376408 |
| successor | euclidean_nearest_distance | 0.390682388 | 0.405874000 | 0.393264034 |
| rolling_drift | W52_step4_reversal | 0.684826645 | 0.672737501 | 0.676076508 |
| barycenter | W10_W1_movement | 0.776031353 | 0.737747525 | 0.731600660 |
| geodesic | W2_std | 3.246794114 | 3.126245167 | 3.349799865 |

전체132cells의 세 era 및 W208/stride52/final endpoint rolling 값은 `era_metrics.csv`, `rolling_metrics.csv`에 있다.
Global-null evidence가 없는 관계를 일부 기간의 peak로 승격하지 않는다.

## 모델·평가·ensemble·prospective 결정

- **TransportContinuationModel: NOT JUSTIFIED.** Corrected development gate가 실패했다.
- **WassersteinBarycenterModel: NOT JUSTIFIED.** 단순 mean과 동일하고 추가 근거도 없다.
- Walk-forward Top6/Recall@6/10/15/mean winning rank/Top8·10·12·15 >=5 events: 해당 없음.
- Random/Frequency26/Gap Logistic 비교·paired block bootstrap·여러 start point 평가: 정당화된 신규 모델이 없어 실행하지 않았다.
- Gap/Graph/GapShape/Mirror와 ranking Spearman·Top6/10/15 overlap: 신규 fixed ranking이 없어 해당 없음.
- **ENSEMBLE: NOT CURRENTLY JUSTIFIED.** H17 final ensemble은 만들지 않았다.
- **PROSPECTIVE_CAPABILITY_NOT_CREATED_NO_JUSTIFIED_MODEL.** Archive는 VERIFIED지만
  `draw1247_phase24_optimaltransport` 기능이나 실제 snapshot을 생성·발행하지 않았다.
- Target1246 거부 테스트를 유지했다. Archive absent이면 복원 대기, integrity failure이면 prospective 거부 규칙도 검증했다.

## 검증·제한

수식/monotone matching/transport/lag/direction/successor/rolling overlap/CDF-W1/barycenter/geodesic/acceleration,
synthetic persistence/reversal, deterministic null rebuilding/search parity, development-only selection,
wrong-direction gate 거부, source1246suffix·target1246거부, archive두schema/tamper/read-only 등을 테스트했다.
Phase24 전용 **23passed**다. 독립 reviewer도 두 수정 회귀 테스트를 재실행했고 남은 critical/important 지적은 없다.

최종 전체 `python -m pytest -q`: **4 failed, 1207 passed, 2 skipped in 219.90s (0:03:39)**.
실패 네 건은 기존 complexity/RMT/recurrence/topology의 parallel-versus-serial 테스트다.
모두 Python multiprocessing named pipe 생성 중 **PermissionError / WinError5**이며 기존 source/tests를 변경해 숨기지 않았다.
`full_tests_final.log`에 전체 결과를 보존했다. 전체 테스트가 모두 green이라고 주장하지 않는다.

Audit은 다음을 통과했다:64pilot seed replay, 대표8main seed replay,796saved metric vectors의 own-max와
24global-p행/796maxima행 재계산, 모든 lag의 독립 산술, discrete W1의 SciPy 대조,
rolling raw count와 barycenter mean 직접 재계산, geodesic/acceleration 항등식,
selection hash·398protected artifact hashes·archive30file hashes·HEAD 불변.
모든398main history를 다시 생성한 검증은 아니다. Fixed-margin20trades/row의 finite mixing,
32pilot scale 추정 오차, p해상도 .005, 검정한 parameter family 범위의 한계가 남는다.

Windows parallel 생성 실패 attempt와 review 이전 중단 run은 각각 `parallel_attempt/`, `pre_review_attempt/`에
분리 보존했다. 최종 canonical evidence는 그 밖의 현재 report root다. 수정 후 전체 pilot/null을 동일 seed로 재생성했다.

## 출력·변경 파일

Plots는 `reports/optimal_transport/plots/`의11PNG다: monotone transport, W1분포, lag별W1,
direction/null, successor, rolling drift, barycenter trajectory, next barycenter distance,
IID global-max, fixed-margin global-max, descriptive geodesic/acceleration.
예측 모델이 없어 predictive-ranking plot은 해당 없다.

Git 변경 파일은 아래와 같다. Raw data와 이전 Phase별 분석 source/결과 문서/prospective artifact는 수정하지 않았다.

- `.gitignore`
- `README.md`
- `docs/README.md`
- `docs/optimal-transport-analysis.md`
- `docs/optimal-transport-results.md`
- `docs/research-ideas.md`
- `docs/superpowers/plans/2026-10-18-phase24.md`
- `src/analysis/optimal_transport.py`
- `src/analysis/optimal_transport_diagnostics.py`
- `src/analysis/optimal_transport_search.py`
- `src/cli.py`
- `src/optimal_transport_cli.py`
- `tests/test_optimal_transport.py`
- `tests/test_optimal_transport_cli.py`
- `tests/test_optimal_transport_diagnostics.py`
- `tests/test_optimal_transport_search.py`

Git-ignored 생성 출력의 정확한 경로·SHA-256 목록은 `reports/optimal_transport/output_inventory.json`,
source/docs/test 변경 목록은 같은 위치의 `changed_files.txt`다.
최종 **draw1246미사용 / 자동 fetch·import없음 / commit없음 / push없음**을 확인했다.
H24 Symbolic Dynamics, H25 randomness battery는 미시작, H17은 남은 독립 가설 완료까지 유보다.
Phase24에서 종료한다.
