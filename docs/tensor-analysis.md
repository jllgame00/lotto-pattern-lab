# Phase17 — Tensor decomposition / H15 방법

## 질문과 범위

시간 × 번호 × lag/state를 동시에 본 Lotto history가 같은 제약의 random history보다
더 low-rank이고 안정적인가를 검증한다. 예쁜 factor loading만으로 구조를 주장하지 않는다.
연구 자료는 bonus를 제외한 draws1–1245이며 실제1246은 어떤 설계·선택·평가에도 쓰지 않는다.
NumPy/SciPy HOSVD를 사용한다. tensorly가 설치되어 있지 않아 CP는 생략한다.

## Causal tensor와 정규화

입력은 정확한 completed-history prefix다. cutoff를 주면 입력 길이와 같아야 하며,
future row를 받아 몰래 자르지 않는다. 예측 target T라면 prefix는 T−1에서 끝나야 한다.

| Tensor | feature mode | 첫 anchor | 전체 shape | 개발 shape |
|---|---|---:|---|---|
| A | appearance lag{0,1,2,4,8,13,26} |27|1219×45×7|874×45×7|
| B | completed anchor 포함 rate{10,26,52} |52|1194×45×3|849×45×3|
| C | appearance, gap/52, rate26, rate52 |52|1194×45×4|849×45×4|

gap은 마지막 appearance 이후 completed draw 수이며 현재 appearance이면0이다.
한 번도 보이지 않은 번호는 마지막 appearance를 draw0으로 초기화한다. gap은52에서 clip한다.
B/C는 이력이52개 쌓이기 전 행을 제외한다. null에서도 같은 초기 정책을 쓴다.

primary scaling은 데이터에 fit하지 않는다. p=6/45, q=1−p를 고정하고 appearance는
(x−p)/sqrt(pq), W-rate는 (rate−p)/sqrt(pq/W)로 변환한다.
G가 P(G=g)=pq^g인 stationary nonnegative geometric일 때
E[min(G,52)]=Σ(k=1..52)q^k,
E[min(G,52)²]=Σ(k=1..52)(2k−1)q^k를 써 gap/52의 고정 mean/std를 구한다.
raw transform도 API로 제공하지만 별도 가설 검색에는 넣지 않는다.
row 합6 및 rate overlap이 만드는 low-rank/smoothness는 이론상 생길 수 있으며,
독립 시간·feature 관측으로 취급하지 않는다.

## HOSVD와 rank

각 mode를 행으로 두고 나머지를 C-order로 펼친 thin SVD를 구한다.
각 factor 열의 최대 절대 loading이 양수가 되도록 부호를 고정하며 core도 같은 부호를 쓴다.
core는 X×₀Uₜᵀ×₁Uₙᵀ×₂U𝒻ᵀ, reconstruction은 역방향 mode product다.
오차는 ||X−Xhat||F/||X||F다. mode energy는 해당 mode singular value 제곱의 누적 비율이다.
이는 실제 joint Tucker retained energy와 다르므로 구분한다.

temporal rank8 고정, number rank{2,3,4,6}, feature rank{1,2,3}:
각 tensor12개, 전체36개 조합이다. 최대 rank(8,6,3) 한 번의 core/factor를 잘라
다른 rank를 계산한다. full spectrum은 보존하지만 square temporal factor는 저장하지 않는다.
primary rank는 결과를 보고 추가하지 않는다. core concentration은 descriptive만 보고한다.

## 고정 primary search

| Family | cell 정의 | 후보 수 |
|---|---|---:|
| concentration |3 tensors × mode별 누적 energy(time ranks1/2/4/8, number1/2/3/4/6, feature1/2/3)|36|
| reconstruction |3×4 number ranks×3 feature ranks, negative relative error|36|
| effective_rank |3×3 modes, −exp(H(pᵢ))/thin dimension; pᵢ=σᵢ²/Σσ²|9|
| stability |각 tensor를 시간순3개 비중첩 block,3 block pairs×4 number ranks×3 tensors|36|
| temporal |전체+3blocks 각각 leading4 temporal factor의 absolute lag1 correlation×3tensors|48|
| 전체 |5 family 자체 strongest cell을 선택|165|

spectral entropy H는 squared singular energy의 Shannon entropy(nats)다.
정규화 spectral entropy도 helper로 제공한다. effective rank는 exp(H)다.
thin dimension=min(mode size, 나머지 mode size의 곱)이므로 큰 time-axis의 정규화 분모도 명시한다.
stability는 두 orthonormal number subspace의 principal-angle cosine 제곱 평균이다.
sign/permutation/rotation에 불변이다. 개별 component가 동일하다는 뜻은 아니다.
원본 unfolding singular value가 max(matrix dimensions)×machine epsilon×최대 singular value보다
작은 방향은 식별되지 않은 것으로 보고 stability/temporal 후보에서 제외한다.
상수 temporal series의 correlation도 undefined로 제외한다. 저rank tensor의 임의 nullspace 방향을 evidence로 쓰지 않는다.
block은 np.array_split로 각 tensor의 유효 행을3등분하며 실제 draw 경계를 저장한다.
가장 안정적인 한 block pair의 최대값을 검색하므로 전 시대 안정성을 자동으로 보장하지 않는다.
temporal correlation은 smoothness 진단이며 temporal factor identity의 재현성을 뜻하지 않는다.

## Calibration과 complete-search null

독립 IID pilot32개를 cutoff1245/900 각각 만들어 cell별 oriented mean/std를 고정한다.
pilot seed171001은 본 검정 seed170042와 분리한다. 유효 pilot가75% 이상이며
std>1e−12인 cell만 이용한다. 상수인 B feature-rank3 누적 energy 등은 null/real 공통으로 제외한다.
각 cell을 z=(oriented value−pilot mean)/pilot std로 표준화한다.
독립 calibration이므로 실제 데이터나 본 null의 가장 매력적인 위치에 맞춰 정규화하지 않는다.

본 검정은 IID199 + fixed-margin199다. fixed-margin은 기존 Curveball constrained generator를 쓴다.
각 surrogate에서45 binary series, A/B/C,3blocks,mode SVD,36 rank조합,165cells 전부를
다시 계산하고 각 family의 자체 최대 z를 저장한다. 실제가 고른 위치만 null에 적용하지 않는다.
개발900의 fixed margins도 실제1–900에서 별도로 만들며 이후901–1245의 빈도를 빌리지 않는다.
raw null vector/pilot vector를 NPZ로 보존해 global maxima를 재계산할 수 있다.
global p=(1+null max≥real max인 수)/(199+1), family correction=min(1,5p)다.
두 null은 서로 대체하지 않으며 PROMISING은 양쪽에서 일관된 corrected 근거를 요구한다.
최소 p=.005이므로 보정 최소는.025이며 검정력과 finite Monte Carlo 오차의 한계가 있다.

## Targeted controls와 해석

이미 구성된 tensor의 time slice 순열은 mode spectra와 Tucker reconstruction error를
보존하지만 시간 factor의 lag1 correlation은 바꾼다. 따라서 low rank 자체만으로
chronological predictability를 주장할 수 없다. number label을 전체 history에 일관되게
순열해도 singular spectrum은 변하지 않는다. 두 control은 diagnostic이며 IID/fixed-margin을 대신하지 않는다.
seed170777의 단일 예시이며 별도 primary p-value를 만들지 않는다.
number factor와 full-history appearance frequency의 Pearson correlation은 descriptive로만 보존한다.
기존 Graph/GapShape의 latent factor가 직접 저장되어 있지 않으면 이 비교를 위해 재학습하지 않는다.

## Development gate와 예측

개발은1–900, 이후는901–1245다. 전체 데이터는 역사적 구조 검정에만 쓰며
예측을 정당화하는 선택은 개발 comparison만 읽는다. JSON/hash를 exclusive-create하여 동결한다.
canonical 동결 CLI는 두 calibration의 길이·32pilot,199개씩의 null identity,source hash,
900회 raw null vector에서 재계산한 자체 maximum·p-value를 검증하며 evidence hash를 함께 동결한다.
검토 대상 tensor/cell은 개발 z의 최대값(동률은 고정 순서)을 기록한다.
이는 predictive rank 선택 완료를 뜻하지 않는다.

사전 gate는 (a)stability 이외 한 primary family가 양 null corrected p≤.05이고
(b)stability도 양 null corrected p≤.05이어야 한다.
둘 다 통과해야 작은 AR(1) temporal-factor forecast의 개발 hindcast 검토를 시작한다.
구조 gate 통과만으로 TensorFactorModel을 만들거나 예측 우위를 주장하지 않는다.
불통과이면 `PREDICTIVE_MODEL_NOT_JUSTIFIED`로 model·walk-forward·Rank correlation·
draw1247_phase17_tensor capability를 생략한다. 예측이 없으므로 Random/Gap 대비 지표를 꾸며내지 않는다.

현재 과거 prospective archive가 부재하다. 어떤 경우에도 복원·검증 전 실제1247 snapshot을
발행하지 않는다. 상태는 `PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION`이다.
기존 target1246 거부/archive gate 테스트를 재사용하며 Phase17 CLI에 발행 명령을 만들지 않는다.

## 재현과 산출물

```powershell
$env:PYTHONPATH='.;.deps/docs-checks'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
python main.py tensor calibrate --pilots 32
python main.py tensor benchmark
python main.py tensor analyze --surrogates 199 --workers 4
python main.py tensor decision
python main.py tensor diagnostics
python main.py tensor plots
python -m pytest -q -rs
```

출력은 reports/tensor 아래로 제한하고 기존 evidence 덮어쓰기를 거부한다.
그림은 inspection aid이며 결과 판정은 complete-search null 표를 따른다.
최종 수치·무결성·파일 inventory는 [Phase17 결과](phase17-results.md)를 참조한다.
