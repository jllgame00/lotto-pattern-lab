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
| H13 | Modular / difference-space transforms | BACKLOG |
| H14 | Entropy / compression / algorithmic randomness | BACKLOG |
| H15 | Tensor decomposition | BACKLOG |
| H16 | Symmetry / reflection structure | BACKLOG |
| H17 | Validated weak-signal ensemble | BACKLOG |

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

BACKLOG

**핵심 아이디어**

modulo transforms·sorted-number differences·spacing sequences로 표현을 바꾼다.

**왜 검증할 가치가 있는가**

원래 label 공간에서 약한 구조가 변환 공간에서 보이는지 시험한다.

**검증 방법**

modulus·정렬·차분 정의를 사전 제한하고 동일 변환 탐색을 null에도 적용한다.

**현재까지 결과**

별도 가설은 미실행이다. Phase 10의 spacing 기술 통계가 이 전체 가설을 검증한 것은 아니다.

**다음 결정**

중복 표현과 경계 조건을 정리한 후 독립 protocol로 검증한다.

**주요 false-positive 위험**

많은 modulus / transform 탐색, 정렬이 만드는 의존성, 되돌릴 수 없는 정보 손실.

**관련 문서**

[Number-space 방법](number-space-analysis.md)

## H14 — Entropy / compression / algorithmic randomness

**상태**

BACKLOG

**핵심 아이디어**

permutation entropy·sample entropy·Lempel-Ziv complexity·compression ratios를 비교한다.

**왜 검증할 가치가 있는가**

단순 빈도와 별개로 규칙성·압축 가능성을 측정할 수 있다.

**검증 방법**

encoding·block length·estimator와 compressor 설정을 고정하고 동일 길이·margin null로 calibration한다.

**현재까지 결과**

미실행이다. 낮은 entropy가 예측력을 뜻한다는 결론은 없다.

**다음 결정**

유한 표본 bias와 encoding 의존성부터 synthetic 자료로 검증한다.

**주요 false-positive 위험**

symbolization 선택, compressor header 비용, 표본 길이 차이, entropy 감소와 예측 가능성 혼동.

**관련 문서**

[연구 원칙](../README.md#연구-원칙)

## H15 — Tensor decomposition

**상태**

BACKLOG

**핵심 아이디어**

time × number × feature tensor의 CP/Tucker-style structure를 조사한다.

**왜 검증할 가치가 있는가**

여러 표현의 낮은 rank 공통 구조가 있는지 묻는다.

**검증 방법**

feature·rank·regularization을 제한하고 training-only factorization과 동일 null rank search를 설계한다.

**현재까지 결과**

미실행이며 latent factor나 예측 성능을 보고하지 않는다.

**다음 결정**

낮은 차원 연구 근거와 계산량을 검토한 뒤 별도 protocol을 작성한다.

**주요 false-positive 위험**

rank 탐색, rotation / scaling 모호성, factor 해석의 사후 선택, 전체 tensor leakage.

**관련 문서**

[연구 가설 노트](research-ideas.md)

## H16 — Symmetry / reflection structure

**상태**

BACKLOG

**핵심 아이디어**

고정 중심 23에서 mirror(n) = 46 - n으로 번호를 반사한다. 예: 1 ↔ 45, 2 ↔ 44, …, 22 ↔ 24, 23 ↔ 23.

**왜 검증할 가치가 있는가**

ordered label 표현의 symmetry / anti-symmetry를 제한된 transform으로 직접 시험한다.

**검증 방법**

same-draw mirrored pairs, lagged mirror relationships, draw-level symmetry score와 MirrorModel을 사전 선언한다. IID / fixed-margin global-max tests를 사용하고 고정 중심 23부터 시작한다.

**현재까지 결과**

미실행이며 MirrorModel은 아직 구현하지 않았다.

**다음 결정**

고정 중심 증거가 확장을 정당화할 때만 dynamic centers를 고려한다.

**주요 false-positive 위험**

중심·lag 탐색, 자기반사 23의 중복 집계, 우연한 mirrored pairs, 변환 후 best example 선택.

**관련 문서**

[연구 원칙](../README.md#연구-원칙)

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
