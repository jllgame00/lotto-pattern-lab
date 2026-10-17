# 연구 가설 노트

## 문서의 역할

현재 가설·상태·다음 결정을 관리하는 canonical notebook입니다. 수치는 [문서 색인](README.md)의 Phase 결과를 참고합니다. Phase 번호는 실행 순서이며 H번호와 다릅니다.

표현을 바꾸면 구조가 보일 수 있지만,
표현 공간이 커질수록 random data에서도 구조처럼 보이는 패턴을
발견하기 쉬워진다.

## 번호 이관 안내

Older historical plans and frozen manifests may use legacy H-numbers.
Current active documentation uses the canonical H1–H17 numbering below.

과거 계획·동결 manifest의 H번호는 보존합니다. 옛 H9 spatial neighborhood / range-density는 현재 H8입니다. 옛 H8 delay / recurrence / tensor 묶음은 H9와 H15 등 별도 가설로 나눕니다. 동결 증거를 소급 수정·재생성하지 않습니다.

## Canonical 상태표

| ID | 가설 | 상태 |
|---|---|---|
| H1 | 개별 번호의 시간적 패턴 | TESTED / INCONCLUSIVE |
| H2 | Gap / periodicity / regime | TESTED / INCONCLUSIVE |
| H3 | 2D translational number patterns | TESTED / INCONCLUSIVE |
| H4 | Gap-conditioned 3D | TESTED / INCONCLUSIVE |
| H5 | Recent-frequency-conditioned 3D | TESTED / INCONCLUSIVE |
| H6 | Gap × frequency interaction | TESTED / INCONCLUSIVE |
| H7 | Full continuous 4D geometry | DEFERRED |
| H8 | Spatial neighborhood / range-density | TESTED / INCONCLUSIVE |
| H9 | Delay embedding / recurrence geometry | TESTED / INCONCLUSIVE |
| H10 | Wavelet / SSA multiscale structure | TESTED / INCONCLUSIVE |
| H11 | Mutual information / Transfer Entropy | TESTED / INCONCLUSIVE |
| H12 | Dynamic graph / Hypergraph | TESTED / INCONCLUSIVE |
| H13 | Modular / difference-space transforms | TESTED / INCONCLUSIVE |
| H14 | Entropy / compression / algorithmic randomness | TESTED / INCONCLUSIVE |
| H15 | Tensor decomposition | TESTED / INCONCLUSIVE |
| H16 | Symmetry / reflection structure | TESTED / INCONCLUSIVE |
| H17 | Validated weak-signal ensemble | BACKLOG |
| H18 | Change-point / piecewise-stationary regimes | TESTED / INCONCLUSIVE |
| H19 | Point process / Hawkes-like influence / renewal | TESTED / INCONCLUSIVE |
| H20 | Long-memory / fractal scaling / DFA | TESTED / INCONCLUSIVE |
| H21 | Random Matrix Theory / collective number modes | TESTED / INCONCLUSIVE |
| H22 | Topological Data Analysis / persistent structure | TESTED / INCONCLUSIVE |

## H1 — 개별 번호의 시간적 패턴

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

번호별 출현열의 calendar·rolling·ACF·spectrum에서 반복 구조를 찾는다.

**왜 검증할 가치가 있는가**

빈도 차이와 반복은 서로 다르므로 독립적으로 점검할 가치가 있다.

**검증 방법**

binary series의 ACF·periodogram·periodicity score를 고정 scope shuffle과 비교한다.

**현재까지 결과**

탐색적 peak는 있었으나 안정적 예측 우위는 확립되지 않았다.

**다음 결정**

기존 결과를 보존하고 새로운 scope는 별도 사전 선언 후 검증한다.

**주요 false-positive 위험**

번호·시기·주기 선택의 다중 탐색, 짧은 창의 가짜 peak.

**관련 문서**

[시간 분석](temporal-analysis.md)

## H2 — Gap / periodicity / regime

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

current gap·periodicity·hazard·Bayesian·HMM state가 다음 출현과 연관되는지 묻는다.

**왜 검증할 가치가 있는가**

서로 다른 시간 상태를 한꺼번에 합치면 조건부 차이가 감춰질 수 있다.

**검증 방법**

causal feature, feature ablation, development-frozen 설정과 later walk-forward를 비교한다.

**현재까지 결과**

Gap Logistic은 약하게 양의 역사 점추정치를 반복했지만 신뢰할 우위는 확립하지 못했다. 복잡한 regime 모델도 안정적으로 개선하지 못했다.

**다음 결정**

Gap Logistic을 비교 baseline으로 유지하고 우월한 모델이라고 주장하지 않는다.

**주요 false-positive 위험**

regime 사후 선택, scaling leakage, 중첩 평가 구간과 희귀 당첨의 과대해석.

**관련 문서**

[예측 실험](predictive-experiments.md) · [Gap / prize](gap-prize-research.md) · [Regime](regime-research.md)

## H3 — 2D translational number patterns

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

draw × number binary matrix에서 시간·번호 displacement와 chain을 찾는다.

**왜 검증할 가치가 있는가**

개별 번호를 고정하면 보이지 않는 이동 구조를 시험한다.

**검증 방법**

bounded shift·direction·chain·Hough·FFT의 complete-search maxima를 IID / fixed-margin과 비교하고 causal 예측을 별도로 평가한다.

**현재까지 결과**

Phase 6의 구조는 global correction을 통과하지 못했으며 예측 우위도 확립되지 않았다.

**다음 결정**

후속 조건부 표현과 비교하되 선택된 raw shift를 독립 증거로 재사용하지 않는다.

**주요 false-positive 위험**

번호 label의 공간적 의미 가정, 경계 분모, 겹치는 chain, best peak 선택.

**관련 문서**

[방법](spatiotemporal-analysis.md) · [결과](phase6-results.md)

## H4 — Gap-conditioned 3D

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

translation을 causal source gap 상태로 나눈다.

**왜 검증할 가치가 있는가**

pooled 2D에서 희석되는 조건부 구조가 있을 수 있다.

**검증 방법**

training-only gap encoding, source-state conditional search와 trajectory를 매 surrogate에서 재계산한다.

**현재까지 결과**

Phase 7은 global null correction과 walk-forward에서 신뢰할 개선을 확립하지 못했다.

**다음 결정**

coarse·clipped·relative 비교를 완료 결과로 보존한다.

**주요 false-positive 위험**

destination state leakage, sparse bin, 상태 경계 사후 선택, 겹치는 경로.

**관련 문서**

[방법](gap3d-analysis.md) · [결과](phase7-results.md)

## H5 — Recent-frequency-conditioned 3D

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

gap 대신 W10/W26/W52 출현 빈도 상태로 translation을 나눈다.

**왜 검증할 가치가 있는가**

같은 gap도 최근 출현 누적량은 다를 수 있다.

**검증 방법**

causal count / quantile / relative 상태와 같은 complete null search, 동일 target walk-forward를 사용한다.

**현재까지 결과**

Phase 8의 모든 주요 family는 보정 후 근거가 부족했다. 예측 우위도 확립되지 않았다.

**다음 결정**

사전 선언한 W26 track과 development-selected 진단을 구분해 보존한다.

**주요 false-positive 위험**

window 탐색, count 동률, 불완전 창, local follow-up을 독립 증거로 오인.

**관련 문서**

[방법](frequency3d-analysis.md) · [결과](phase8-results.md)

## H6 — Gap × frequency interaction

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

gap LOW/MID/HIGH × W26 COLD/NEUTRAL/HOT의 아홉 joint state를 시험한다.

**왜 검증할 가치가 있는가**

단일 상태보다 조합에서만 나타나는 구조가 있는지 묻는다.

**검증 방법**

같은 source population의 gap / frequency parent, joint propensity baseline, 전체 surrogate maxima와 비교한다.

**현재까지 결과**

Phase 9에서 두 parent와 비기하학 baseline을 넘어서는 신뢰할 개선은 확립되지 않았다.

**다음 결정**

categorical interaction과 continuous 4D를 구분하고 검증 범위를 확장하지 않는다.

**주요 false-positive 위험**

희소 joint cell, 조건 선택, 서로 다른 parent 분모, 낮은 support의 큰 lift.

**관련 문서**

[방법](joint-state-analysis.md) · [결과](phase9-results.md)

## H7 — Full continuous 4D geometry

**상태**

DEFERRED

**핵심 아이디어**

time·number·gap·frequency의 연속 좌표에서 geometry를 찾는 구상이다.

**왜 검증할 가치가 있는가**

범주화로 잃는 구조가 있을 가능성을 검토할 수 있다.

**검증 방법**

재개한다면 metric·scaling·bounded search·training-only fitting·global correction을 먼저 선언한다.

**현재까지 결과**

실행하지 않았다. 낮은 차원에서 충분한 근거가 없어 보류한다.

**다음 결정**

H6 결과를 연속 4D 검증 완료로 해석하지 않는다. 재개 근거가 생길 때 별도 설계한다.

**주요 false-positive 위험**

차원 증가, metric 선택, 거리 집중, sparse trajectory와 막대한 search freedom.

**관련 문서**

[Joint-state 방법](joint-state-analysis.md)

## H8 — Spatial neighborhood / range-density

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

1–45 finite number axis에서 주변 activity·range-density·hot-zone·spacing을 조사한다.

**왜 검증할 가치가 있는가**

번호 하나보다 국소 구간 수준의 표현이 유용한지 직접 시험한다.

**검증 방법**

고정 window·width·kernel, own / neighbor-only controls, 전체 null 탐색과 development-only selection을 사용한다.

**현재까지 결과**

Phase 10은 TESTED / INCONCLUSIVE. 선택된 W52 neighborhood는 smoothing이 없는 own-number control이며 neighbor 기여의 증거가 아니다.

**다음 결정**

완료 상태를 유지하고 raw hot-zone을 예측 근거로 승격하지 않는다.

**주요 false-positive 위험**

번호 인접성의 물리적 의미 가정, 겹치는 rolling window, edge normalization, 설정 선택.

**관련 문서**

[방법](number-space-analysis.md) · [결과](phase10-results.md)

## H9 — Delay embedding / recurrence geometry

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

delay-coordinate embedding으로 과거 관측 조합을 상태로 만들고 recurrence plots·RQA·nearest historical analogs를 조사한다.

**왜 검증할 가치가 있는가**

직접 고른 상태변수 대신 시간지연 표현이 유용할 수 있다. 핵심 질문은 **비슷한 과거 상태가 비슷한 미래 결과로 이어지는가?**이다.

**검증 방법**

Phase 11에서 A/B/C 표현·180개 embedding/metric·두 recurrence 정의를 사전 제한하고 Theiler / raw-support exclusion을 적용했다. RQA와 state distance → successor-similarity를 IID 199회·fixed-margin 199회의 동일한 전체 탐색 최대값과 비교했다.

**현재까지 결과**

가장 강한 successor 관계는 ρ=−0.02407, family 보정 p=0.400/0.425였다. 개발 401–900회에서 선택한 nearest/analog/continuation의 이후 901–1245회 평균 Top6 적중은 0.7855/0.7362/0.7884로, Gap Logistic 0.8348 대비 안정적 개선이 없었다. Ensemble은 NOT CURRENTLY JUSTIFIED이다.

**다음 결정**

역사 연구는 1–1245회로 완료하고 설정을 동결했다. 1246회는 어떤 연구 근거에도 사용하지 않았다. 1247 준비 gate는 구현했지만 기존 archive 부재로 PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION이다. 복원·검증 후 별도 명시적 단계에서만 1246회를 훈련에 추가하고 정확한 동결 설정으로 refit할 수 있다.

**주요 false-positive 위험**

지연 상태의 시간 중첩, successor 정렬 오류, distance concentration, metric / threshold 탐색, Takens 정리를 Lotto 재구성의 증명으로 오용.

**관련 문서**

[Phase 11 방법](recurrence-analysis.md) · [Phase 11 결과](phase11-results.md) · [현재 roadmap](../README.md) · [Prospective workflow](prospective-workflow.md)

## H10 — Wavelet / SSA multiscale structure

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

time-varying periodicity·multiscale decomposition·quasi-periodic structure를 조사한다.

**왜 검증할 가치가 있는가**

전 구간 FFT가 놓치는 시간에 따라 변하는 주기를 시험할 수 있다.

**검증 방법**

Phase12에서53개 series, Morlet8개 주기, SSA L26/52/104와5개 역사 window를 사전 제한했다. IID199회와 fixed-margin199회 각각이 자체 최고 번호·시간·scale·L·pair를 선택하는 전체 탐색 최대값을 여섯 family 보정으로 비교했다. 개발401–900회에서 설정을 선택하고901–1245회에서 training-prefix만으로 walk-forward 평가했다.

**현재까지 결과**

번호5의 약13.42회 SSA 성분이 인접 역사 window에서 안정적이었으며 두 null 모두 global p=0.005, family 보정 p=0.03이었다. Wavelet 지속 영역은 보정을 통과하지 못했다. 이후 Wavelet/SSA 평균 Top6는0.7739/0.8087로 Gap Logistic0.8348 대비 안정적 개선이 없었다. 두 ensemble 후보는 NOT CURRENTLY JUSTIFIED이다. 구조와 예측의 두 조건을 함께 만족하지 못해 PROMISING으로 승격하지 않는다.

**다음 결정**

1–1245회 역사 연구와 개발 선택 설정을 동결했다. SSA 구조 신호는 보존하되 예측 근거와 분리한다. 1246은 사용하지 않았다. draw1247_phase12_multiscale 준비 gate는 구현했지만 archive 부재로 PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION이며 발행하지 않았다. Phase12에서 멈추고 다음 가설과 final ensemble은 구현하지 않는다.

**주요 false-positive 위험**

scale·rank·구간 선택, boundary effect, 전체 자료 decomposition의 future leakage.

**관련 문서**

[Phase12 방법](multiscale-analysis.md) · [결과·검증](phase12-results.md) · [이전 시간 분석](temporal-analysis.md)

## H11 — Mutual information / Transfer Entropy

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

nonlinear dependence와 directional information flow를 조사한다.

**왜 검증할 가치가 있는가**

선형 correlation이 놓치는 의존성을 점검할 수 있다.

**검증 방법**

Phase13에서45개 binary, lag1/2/3/4/8/13/26, k/l각1/2를 사전 제한했다. occupied-state Miller–Madow 및 source-only circular shift19회로 finite-sample bias를 진단하고, IID199회·fixed-margin199회 각각이 모든 pair/lag/history를 새로 검색한 maximum을 다섯 family 보정으로 비교했다. 개발401–900회에서 MI14/TE56개 후보를 선택하고901–1245회에서 causal ranking·target-history ablation을 평가했다. 방향성은 causal effect와 구분한다.

**현재까지 결과**

최고 MI2→33/lag13의 보정p는0.225/0.175, 최고TE13→24/lag4/k2/l2 및 비대칭은 두 null 모두 보정p1이었다. 보정 후 directional information은 없었다. 이후MI/TE 평균Top6는0.8435/0.7797, Gap은0.8348이며 paired구간은0을 포함한다. TE의 target-own 대비 logloss 차이는+0.000986[+0.000553,+0.001409]로 source 추가가 악화 방향이었다. 두 ensemble 후보는 NOT CURRENTLY JUSTIFIED이다.

**다음 결정**

1–1245회만으로 역사 연구와 설정 동결을 완료했다. MI의 약한 양의 점추정치는 탐색용으로 보존하되 예측·인과 증거로 승격하지 않는다. 1246은 사용하지 않았다. draw1247_phase13_informationflow 준비 gate는 구현했지만 archive 부재로 PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION이며 발행하지 않았다. Phase13에서 멈추고 fullgraph 및 finalensemble은 구현하지 않는다.

**주요 false-positive 위험**

discretization 탐색, estimator bias, sparse joint distribution, 동시출현 제약을 방향성으로 오인.

**관련 문서**

[Phase13 방법](information-flow-analysis.md) · [결과·검증](phase13-results.md) · [연구 원칙](../README.md#연구-원칙)

## H12 — Dynamic graph / Hypergraph

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

number co-occurrence graph·communities·higher-order set relations를 표현한다.

**왜 검증할 가치가 있는가**

개별 번호보다 집합 관계에 구조가 있는지 묻는다.

**검증 방법**

W={26,52,104}, weighted spectral K={2,3}, threshold2, triple support>=3를 고정했다.
135개 graph, 2,057,700개 primary 후보 cell의 전체 검색을 IID199·fixed-margin199에도 동일하게 허용했다.

**현재까지 결과**

community 안정성 보정 p=0.10(IID),0.05(fixed-margin)로 두 null에 걸친 근거는 부족했다.
edge·triple·persistence·frequency-controlled successor의 보정 p는 모두1이었다.
node strength=5×빈도, 전체 triple participation=10×빈도임을 분리했다.
개발401–900에서 Graph W52 neighbor/communityK3, Hypergraph W104 support2 shrink10을 동결했다.
이후 평균Top6는Graph0.858/Hypergraph0.817/Gap0.835, 주요 paired 구간은0을 포함했다.
Graph는 탐색적 ENSEMBLE CANDIDATE로 보존하고 Hypergraph는 NOT CURRENTLY JUSTIFIED로 분류했다.

**다음 결정**

역사적 탐색 결과와 인과적 이후 평가를 보존한다. 실제1247 발행은 기존 archive 복원·검증 뒤에만 가능하다.
PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION.

**주요 false-positive 위험**

community resolution 탐색, 희소 hyperedge, 동일 회차의 음의 의존성, graph construction leakage.

**관련 문서**

[Phase14 방법](graph-hypergraph-analysis.md) · [결과·검증](phase14-results.md)

## H13 — Modular / difference-space transforms

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

modulo transforms·sorted-number differences·spacing sequences로 표현을 바꾼다.

**왜 검증할 가치가 있는가**

원래 label 공간에서 약한 구조가 변환 공간에서 보이는지 시험한다.

**검증 방법**

moduli{2,3,4,5,6,7}, lags{1,2,3,4,8,13,26}, absolute distance1..44와 normalized gap5를 고정했다.
다섯 family1793개 후보의 동일한 검색을 IID199·fixed-margin199개에도 적용했다.

**현재까지 결과**

다섯 family 모두 보정 후 유의하지 않았다. modular temporal의 가장 작은 보정 p도 fixed0.95/IID1이다.
개발401–900에서 mod7/lag13, distance lag3/support20, shapeK25/sigma1을 동결했다.
이후 평균Top6는 .786/.777/.838, Gap.835이며 주요 paired 구간은0을 포함했다.
Modular/Difference는 NOT CURRENTLY JUSTIFIED, GapShape는 K 민감도를 남긴 탐색적 ENSEMBLE CANDIDATE다.

**다음 결정**

선택된 단일 modulus·distance 모델과 약한 shape 후보를 보존한다. 최종 ensemble은 만들지 않는다.
1247 발행은 PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION이다.

**주요 false-positive 위험**

많은 modulus / transform 탐색, 정렬이 만드는 의존성, 되돌릴 수 없는 정보 손실.

**관련 문서**

[Phase15 방법](transformed-space-analysis.md) · [결과·검증](phase15-results.md)

## H14 — Entropy / compression / algorithmic randomness

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

permutation entropy·sample entropy·Lempel-Ziv complexity·compression ratios를 비교한다.

**왜 검증할 가치가 있는가**

단순 빈도와 별개로 규칙성·압축 가능성을 측정할 수 있다.

**검증 방법**

53개 encoding과 block L1–5, conditional h1/2, PE m3/4/5·tau1/2/4/8,
SampEn m2/3·r .15/.20/.25std, LZ78, zlib/bz2/lzma를 고정했다.
독립32IID calibration 뒤 전체5184개·개발3942개를 세 null199개씩 동일하게 검색했다.

**현재까지 결과**

전체 역사 여섯 family는 IID/fixed-margin/exact-draw-order shuffle 모두 보정 p=1이었다.
측정 가능한 complexity deficit·압축 이득·추가 chronological structure 근거는 없었다.
개발 gate가 실패해 ComplexityStateModel을 만들지 않았고 예측 평가·ensemble correlation은 생략했다.
true Kolmogorov complexity를 측정하거나 randomness를 증명한 것은 아니다.

**다음 결정**

결과와 local artifact를 보존한다. 정당화된 모델이 없어 H14 prospective capability는 생성하지 않았다.
기존 archive는 PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION이다.

**주요 false-positive 위험**

symbolization 선택, compressor header 비용, 표본 길이 차이, entropy 감소와 예측 가능성 혼동.

**관련 문서**

[Phase16 방법](complexity-analysis.md) · [결과·검증](phase16-results.md)

## H15 — Tensor decomposition

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

time × number × lag/activity/state tensor의 HOSVD/Tucker structure를 조사한다.

**왜 검증할 가치가 있는가**

여러 표현의 낮은 rank 공통 구조가 있는지 묻는다.

**검증 방법**

고정 IID scaling의 causal A/B/C,36개 Tucker rank 조합,165개 primary statistic cell을
독립32pilot로 calibration하고 IID199/fixed-margin199에서 동일한 자체 global maximum을 비교했다.
sign/rotation에 불변인 number subspace 안정성과 temporal factor의 lag1 smoothness를 구분했다.

**현재까지 결과**

다섯 family 모두 보정 후 유의하지 않았다. 전체 최소 보정 p는.400(fixed-margin effective rank),
IID 최소는.675(stability)였다. Tensor B/C의 smooth factor는 rolling overlap의 null에서도 생겼다.
실제가 더 low-rank이거나 안정적인 latent factor를 가진다는 근거를 확보하지 못했다.

**다음 결정**

개발1–900 gate 실패로 PREDICTIVE_MODEL_NOT_JUSTIFIED, ensemble은 NOT CURRENTLY JUSTIFIED다.
예측 평가와 draw1247_phase17_tensor capability는 만들지 않았다.
기존 archive는 PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION이다. H16/H17은 진행하지 않았다.

**주요 false-positive 위험**

rank 탐색, rotation / scaling 모호성, factor 해석의 사후 선택, 전체 tensor leakage.

**관련 문서**

[Phase17 방법](tensor-analysis.md) · [결과·검증](phase17-results.md)

## H16 — Symmetry / reflection structure

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

고정 중심 23에서 mirror(n) = 46 - n으로 번호를 반사한다. 예: 1 ↔ 45, 2 ↔ 44, …, 22 ↔ 24, 23 ↔ 23.

**왜 검증할 가치가 있는가**

ordered label 표현의 symmetry / anti-symmetry를 제한된 transform으로 직접 시험한다.

**검증 방법**

same-draw22mirror pairs,9lags,3activity windows,3regime windows와5secondary shifts를 사전 고정했다.
3862개 전체 후보를 IID199/fixed-margin199에서 재구성하고 각 family의 자체 global maximum을 비교했다.
개발401–900에서48개 Mirror 설정을 비교해 고정하고901–1245에서 causal ranking을 평가했다.

**현재까지 결과**

일곱 family 모두 전체 corrected p=1이었다. MirrorModel의 이후 평균Top6=.8261은
Random=.7681/Frequency=.7739보다 높았지만 Gap=.8348보다 낮고 주요 paired 구간은0을 포함했다.
Gap/Graph Spearman=.0072/.0245의 낮은 상관과 약한 양의 점추정치를 탐색적 ENSEMBLE CANDIDATE로 보존한다.
이는 statistical evidence 또는 H16 PROMISING 판정이 아니다. 최근 성능과 block 민감도가 남는다.

**다음 결정**

MirrorPairModel·shift predictor·dynamic center·H17 ensemble은 만들지 않았다.
prospective에 정당화된 모델이 없어 draw1247_phase18_symmetry capability도 만들지 않았다.
기존 archive는 PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION이다.

**주요 false-positive 위험**

중심·lag 탐색, 자기반사 23의 중복 집계, 우연한 mirrored pairs, 변환 후 best example 선택.

**관련 문서**

[Phase18 방법](symmetry-analysis.md) · [결과·검증](phase18-results.md)

## H17 — Validated weak-signal ensemble

**상태**

BACKLOG

**핵심 아이디어**

안정적인 약한 근거가 있고 서로 다른 정보를 쓰는 모델만 조합한다.

**왜 검증할 가치가 있는가**

개별 우위가 약해도 오류·순위의 상관이 낮으면 보완 가능성을 시험할 수 있다.

**검증 방법**

rank / prediction correlation을 측정하고 weight는 development에서만 선택한다. later-period evaluation과 prospective freeze를 수행하며 중복 정보를 여러 번 세지 않는다.

**현재까지 결과**

최종 validated ensemble은 만들지 않았다. Phase 4의 고정 ensemble 실험이나 Phase 6 조합은 이 가설의 완료를 뜻하지 않는다.

**다음 결정**

안정적 약한 predictive evidence와 정보 차별성을 모두 갖춘 후보가 있을 때만 진행한다.

**주요 false-positive 위험**

같은 gap / frequency 정보의 중복, weight 탐색 과적합, evaluation 재사용, 점추정치만으로 후보 승격.

**관련 문서**

[Regime 연구](regime-research.md) · [Prospective workflow](prospective-workflow.md)

## H18 — Change-point / piecewise-stationary regimes

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

단일 stationary history 대신 통계적 성질이 바뀌는 구간들이 존재하는지 검증한다.
기존 HMM latent state와 구분하며,경계·penalty·minimum length를 제한한 segmentation을 쓴다.

**검증 방법**

45binary appearance,nonoverlap block13/26/52 frequency,고정7shape를 각각 분석한다.
같은전체representation/config/prefix 검색을 IID/fixed-margin surrogate에 부여한다.
예측에서는 target마다<T prefix만 segmentation하고 현재구간 rate를 fixed-frequency와 비교한다.

**다음 결정**

Phase19 완료:2237cells의 IID199/fixed199 global-max,다섯 family 보정 p는 전체 구간에서 모두1이다.
20번585회 및22번507회 등의 개별 경계는 완전 검색 null보다 unusual하지 않았다.
Global A/B/C는 CP없음,개발60개 Regime 설정은 모두Top6=.780으로 동률이다.
이후Top6=.7942,Gap=.8348이며 adaptive boundary는 모든 target에서없어 cumulative frequency와 같았다.
NOT CURRENTLY JUSTIFIED로 분류하며 prospective capability를 만들지 않는다.
H17 ensemble은 남은 독립 가설 연구까지 BACKLOG로 미룬다.

**관련 문서**

[방법](change-point-analysis.md) · [결과·검증](change-point-results.md) · [Phase19 계획](superpowers/plans/2026-10-18-phase19.md)

## H19 — Point process / Hawkes-like influence / renewal

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

번호 출현 사건 이후 자기 자신 또는 다른 번호의 tendency가 일시적으로 바뀌는지 검증한다.
Renewal hazard와 self/cross excitation·inhibition을 구분하며 signed influence를 고전 Hawkes로 해석하지 않는다.

**검증 방법**

Lag1/2/3/4/8/13/26,세 kernel과 고정 renewal 표현을 IID/fixed-margin 전체 검색으로 보정한다.
개발401–900에서 설정을 동결하고 이후901–1245에서 source 추가 logloss와 ranking을 평가한다.

**다음 결정**

Phase20 완료:36135cell의 IID199/fixed199 global-max에서 corrected event evidence가 없었다.
이후 Renewal/Hawkes Top6=.7536/.7072,Gap=.8348이며 source-added logloss도 self-only보다 나빴다.
Renewal/Hawkes는 NOT CURRENTLY JUSTIFIED,Signed는 개발 gate 실패로 이후 평가에서 제외했다.
Prospective capability는 만들지 않았고 H17은 독립 가설 연구 종료까지 미룬다.

**관련 문서**

[방법](point-process-analysis.md) · [결과·검증](point-process-results.md) · [계획](superpowers/plans/2026-10-18-phase20.md)

## H20 — Long-memory / fractal scaling / DFA

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

개별 번호와 draw 전체 scalar/band count에서 여러 scale에 걸친 persistent/anti-persistent 의존성을 검증한다.

**검증 방법**

DFA1 primary,사전 scales8/13/21/34/52/78/104/156/208/312와 최소4segment 규칙을 고정했다.
R/S reference,제한된 crossover,aggregation,rolling 및 secondary spectrum/DFA2를 같은 전체 null 검색으로 비교했다.
전체/개발 각각 독립32pilot를 사용하고 IID199/fixed199의 own global-max와 여섯 primary family 보정을 적용했다.

**현재까지 결과**

Phase21 완료:3200cells(3145eligible),55series의 corrected long-memory evidence가 없었다.
Number22 alpha=.605785500,number35=.406336383이지만 persistent corrected p=.66(양 null),나머지 primary는1이었다.
Number16 boundary52 crossover의 큰 SSE 개선과 rolling 극단값도 같은 탐색을 한 null보다 unusual하지 않았다.
개발 gate와 era 안정성도 실패했다.312scale은 최소1248회가 필요해 역사1–1245에서 미지원으로 남겼다.

**다음 결정**

PREDICTIVE_MODEL_NOT_JUSTIFIED. LongMemoryModel/ScaleStateModel과 예측 비교를 만들지 않았고 ensemble은 NOT CURRENTLY JUSTIFIED다.
Prospective capability를 생성하지 않았으며 archive는 PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION이다.
H17은 BACKLOG,H21–H25는 미시작으로 유지하고 Phase21에서 종료한다.

**주요 false-positive 위험**

유한 binary sample의 alpha 편향,높은 log-log R²의 과해석,scale/window/series 선택,overlapping rolling 창의 중복 evidence,
crossover fit 개선과 asymptotic long-range dependence의 혼동,선택 이후 bootstrap CI의 과해석.

**관련 문서**

[방법](long-memory-analysis.md) · [결과·검증](long-memory-results.md) · [계획](superpowers/plans/2026-10-18-phase21.md)

## H21 — Random Matrix Theory / collective number modes

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

개별 pair 대신45번호 전체 covariance/correlation에 Lotto-valid noise를 넘는 collective mode가 존재하는지 검증한다.

**검증 방법**

Correlation primary,covariance secondary이며 fixed-six 구조의 zero mode를 제외했다.
W104/208/416/624,r1/2/3/5,작은 subspace recurrence와lag1/2/4/8/13 SVD를 사전 고정했다.
Full2443/dev1699cells를 IID199/fixed199에서 각각 새로 검색해 own global-max와 Bonferroni6을 적용했다.

**현재까지 결과**

Whole λ1=1.393598268,effective rank43.315875083이며 안정된 spectral outlier 근거가 없었다.
강한 localized mode IPR=.156765688도 corrected p=.480/.330(IID/fixed)이고 다른 family는1이었다.
Frozen Graph11window 비교는 descriptive이며 뚜렷한 일관된 loading/community 대응을 확인하지 못했다.

**다음 결정**

PREDICTIVE_MODEL_NOT_JUSTIFIED. SpectralFactorModel/ResidualModel,예측 비교/후보 rank 상관과prospective capability를 만들지 않았다.
Ensemble은 NOT CURRENTLY JUSTIFIED,H17은 독립 가설 검증 종료까지 BACKLOG다.
Archive는 PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION이며 Phase22 종료 시점에는 H22–H25를 미시작으로 유지했다.

**주요 false-positive 위험**

Fixed-six의구조적 zero mode를 anomaly로 오인,MP 경계의 과해석,여러window/rank/mode 선택,
degenerate basis의IPR·개별vector 회전,overlapping window의높은 stability,서로무관한winner의evidence 결합.

**관련 문서**

[방법](random-matrix-analysis.md) · [결과·검증](random-matrix-results.md) · [계획](superpowers/plans/2026-10-18-phase22.md)

## H22 — Topological Data Analysis / persistent structure

**상태**

TESTED / INCONCLUSIVE

**핵심 아이디어**

Draw set/shape와 비중첩 activity point cloud에서 random Lotto histories를 넘는 persistent 연결 구조가 있는지 검증한다.
Persistence를 attractor나 번호 예측력과 동일시하지 않는다.

**검증 방법**

A/Jaccard·Hamming,B/frozen shape7 Euclidean,C26/52 비중첩 activity Euclidean의5configs,
whole+W208/416/624,stride104를 고정했다. H0는 exact MST이며 finite n−1bars와 infinite component를 구분한다.
Full560/dev380cells의4family를 IID199/fixed199의 자체 complete-search global maximum과 Bonferroni4로 보정했다.
Independent IID32pilots/cutoff의 finite-sample center/scale와 동일 point 수를 적용했다.

**현재까지 결과**

가장 강한 lifetime은 C52/W208,313–520회의4points에서 .526656305(z4.083085729)였다.
IID/fixed global p=.215/.205,corrected p=.860/.820로 보정을 통과하지 못했다.
Total corrected p=.740/.640,entropy와 tail은 모두1이었다. 개발에서도 corrected evidence가 없었다.
H1_DEFERRED_DEPENDENCY_LIMITATION이며 loop 부재를 판정한 것은 아니다.
Graph/RMT의 frozen outputs만 descriptive로 비교하고 refit하지 않았다.

**다음 결정**

PREDICTIVE_MODEL_NOT_JUSTIFIED. TopologyStateModel,walk-forward 비교/후보 predictive rank 상관/1247 capability를 만들지 않았다.
Ensemble은 NOT CURRENTLY JUSTIFIED,H17은 BACKLOG다.
Archive는 PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION이며 H23/H24/H25는 미시작이다.

**주요 false-positive 위험**

고차원 거리 집중,rolling activity의 기계적 overlap,point 수·metric 단위 차이,
MST tie의 비유일한 attribution,임의 threshold/representation 선택,random loop의 과해석,
같은 history의 Graph/RMT 상관을 독립 evidence로 취급하는 오류.

**관련 문서**

[방법](topology-analysis.md) · [결과·검증](topology-results.md) · [계획](superpowers/plans/2026-10-18-phase23.md)

## 추가 독립 가설 backlog

아래 가설은 명칭만 별도 보존하며 Phase23에서 구현하지 않았다. 기존 H번호를 renumber하지 않는다.

| ID | 가설 | 상태 |
|---|---|---|
| H23 | Optimal Transport / Wasserstein geometry | BACKLOG |
| H24 | Symbolic Dynamics / Markov order | BACKLOG |
| H25 | Integrated randomness battery | BACKLOG |
