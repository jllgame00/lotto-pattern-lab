# Phase17 — Tensor decomposition / H15 결과

## 판정과 작업 시작 확인

**H15 — Tensor decomposition: TESTED / INCONCLUSIVE**.

실제 history가 두 Lotto null보다 더 low-rank이거나 안정적인 latent structure를 가진다는
corrected evidence를 확보하지 못했다. 이것은 무작위성의 증명이나 모든 tensor 방법의 반증은 아니다.
사전 고정한 작은 HOSVD 검색에서 근거가 부족하다는 판정이다.

- Git root: `C:/Users/Samsung/OneDrive/Desktop/university/personal/lotto-pattern-lab`.
- 시작 branch: `main`; 시작 SHA: `4f0aa96632884c411961d4e6bf0c9290a1f2bffe`.
- `git rev-parse --show-toplevel`, 현재 branch, `git status --short`를 확인했으며 시작은 clean이었다.
- README.md, docs/README.md, docs/research-ideas.md, data/raw/lotto_history.csv를 읽었다.
- 완료된 Phase16 manifest의 source18개 hash가 모두 일치했다. 무관한 변경은 없었다.
- canonical CSV는1–1245회이며 bonus는 tensor에서 제외했다.
- CSV SHA-256: `3b7bb1e0a37c28ae4b4a97e098180d8407008ec007698c191ed6cf279db8225b`.
- 기존 reports/prospective archive는 없었다. 복원·발행하지 않았다.

## 표현·차원·rank 검색

| Tensor | 고정 feature | 유효 anchor | 전체 shape | 개발 shape |
|---|---|---|---|---|
| A | binary lag0/1/2/4/8/13/26 |27–1245|1219×45×7|874×45×7|
| B | causal appearance rate10/26/52 |52–1245|1194×45×3|849×45×3|
| C | appearance/gap clip52÷52/rate26/rate52 |52–1245|1194×45×4|849×45×4|

scaling은 고정 IID mean/std다. rate는 anchor를 포함한 completed draw만 쓰고,
gap은 appearance 시0, never-seen은 마지막 appearance draw0으로 초기화한다.
고정 geometric moments와 missing-history 정책은 [방법](tensor-analysis.md)에 명시했다.
full-history fitted scaling이나 future-filled feature는 없다.

HOSVD는 NumPy/SciPy thin SVD, mode unfolding, core projection, diagonal sign convention으로 구현했다.
tensorly 미설치로 optional CP는 생략했으며 설치·network 작업은 하지 않았다.
Tucker rank는 time8 × number{2,3,4,6} × feature{1,2,3}, 각 tensor12개, **총36개**다.
HOSVD는 Tucker optimum 전체를 비선형 최적화한 결과가 아니라 고정 mode-SVD truncation이다.

primary cells는 concentration36, reconstruction36, effective_rank9, stability36, temporal48:
**각 scope165개**다. IID32pilot에서 상수인 B의 feature-mode rank3 누적 energy 한 cell을
제외해 실제/null 모두 **164개 eligible**이었다. raw와 standardized 값은 모두 보존했다.
유효한 관측 history의 각 SVD는 최대rank를 한 번 fit하고 core를 잘라36개 rank 조합을 계산한다.
factor stability용으로 tensor별3개 block도 별도 fit한다. primary search는 scope당12개 HOSVD fit이다.

개발1–900과 전체1–1245는 별도 calibration·null을 쓴다. 본 null은 scope마다
IID199 + fixed-margin199이며, 총796개 surrogate history를 재구성했다.
독립 pilots64개와 real2scope를 합치면862개 complete search,142230개 raw statistic 평가,
31032개 Tucker rank 조합이다. benchmark의 별도8scope-search와 synthetic tests는 이 검정 수에 포함하지 않는다.

## 가장 강했던 실제 구조

각 family 안에서 독립 IID pilot로 정규화한 z가 가장 큰 후보다.
서로 단위가 다른 raw statistic의 크기만으로 후보를 고르지 않는다.

| Family | 실제 strongest cell | raw 값 | z |
|---|---|---:|---:|
| concentration |C time-mode rank8 누적 energy|.292013|2.310072|
| reconstruction |C Tucker(8,6,1) relative error|.891933|2.302800|
| effective_rank |C time-mode effective rank/thin dimension|.476190|2.101967|
| stability |A number rank2, middle vs recent block|.129295|3.811021|
| temporal |B early block의 fourth temporal factor abs lag1 correlation|.993599|2.127904|

C time-mode effective rank는 약85.714/180이다. reconstructed tensor의 전체 Frobenius error는
작을수록 좋은데, 가장 강했던 C 후보도 원자료 energy의 약20.446%만 보존한다.
이는 cumulative mode energy .292013과 다른 수치다.
core concentration은 descriptive로만 저장했으며 추가 p-value family를 만들지 않았다.

최대 진단 rank(8,6,3)의 결과:

| Tensor | relative reconstruction error | retained tensor energy | 최대 core cell/core energy |
|---|---:|---:|---:|
| A |.995274|.009429|.040775|
| B |.841244|.292309|.221957|
| C |.883261|.219850|.207524|

B의 더 낮은 raw error는 smoothed rate 표현의 특성과 함께 해석해야 한다.
null도 같은 overlapping rate tensor를 만들기 때문에 이 자체는 발견이 아니다.

## IID / fixed-margin complete-search 검정

각 surrogate가 A/B/C,모든 rank,block pair,temporal component 중 자신의 strongest cell을 선택했다.
IID pilot32개/cutoff의 고정 mean/std로 z를 만들고 family별 own maximum을 비교했다.
global empirical p=(1+exceedances)/200, corrected p=min(1,5p)다.

| Family | IID exceed/199 | IID global p | IID corrected p | fixed exceed/199 | fixed global p | fixed corrected p |
|---|---:|---:|---:|---:|---:|---:|
| concentration |55|.280|1.000|33|.170|.850|
| reconstruction |38|.195|.975|16|.085|.425|
| effective_rank |32|.165|.825|15|.080|.400|
| stability |26|.135|.675|18|.095|.475|
| temporal |109|.550|1.000|102|.515|1.000|

**어느 family도 보정 후 유의하지 않았다. 실제 tensor가 null보다 더 low-rank라고 판정하지 않는다.**
fixed-margin은 각 draw6개와 전체 번호별 출현수를 보존하는 기존 Curveball20×N trades다.
finite mixing surrogate이며 가능한 모든 fixed-margin matrix의 완전한 균등 표본임을 증명한 것은 아니다.
IID와 fixed-margin은 별도로 보고했다. Monte Carlo 최소 p=.005, 보정 최소=.025이며,
32pilot calibration의 추정 불확실성·bounded rank/representation 검색 한계도 남는다.

## Factor 안정성·시간 구조·rank 민감도

full-history block 경계는 A:27–433/434–839/840–1245,
B/C:52–449/450–847/848–1245다. block별 factor sign을 그대로 비교하지 않고
number subspace의 평균 squared principal-angle cosine을 썼다.

A의 rank2 안정성은 early-middle .073375,early-recent .027706,middle-recent .129295다.
가장 높은 마지막 pair도 양 null 보정을 통과하지 않았다. 특히 early-recent는 낮아
전 시대에 같은 번호 factor가 유지됐다는 해석은 성립하지 않는다.
같은 middle-recent pair에서 A rank3/4/6은 .116341/.139120/.152644다.
rank가 높아질수록 무작위 subspace도 overlap이 늘므로 raw 값 상승을 안정성 개선으로 보지 않는다.

feature rank1 고정 시 number rank2/3/4/6의 reconstruction error:

| Tensor | rank2 | rank3 | rank4 | rank6 |
|---|---:|---:|---:|---:|
| A |.999302|.999116|.998783|.998478|
| B |.939524|.915865|.892374|.850147|
| C |.955830|.938025|.921437|.891933|

모든 근처 rank 조합이 이미 complete search에 포함됐다. 한 rank만의 매력적인 그림으로
정당화한 factor나 forecast는 없다. number factor와 단순 전체 빈도 사이 최대 절대 Pearson correlation은
A .1985,B .4699,C .4430이다. 빈도와 완전히 독립인 factor라는 주장은 하지 않는다.
기존 Graph의 직접 비교 가능한 latent loading은 없으며 이 비교를 위해 Graph를 다시 fit하지 않았다.

B 전체 leading4 temporal factor의 abs lag1 correlation은 .9914/.9891/.9874/.9858,
C는 .9836/.9767/.9778/.9710이다. 그러나 primary temporal maximum의 corrected p는 양 null 모두1이다.
**smoothness는 보이지만 random rolling tensor를 넘어선 시간 구조나 temporal-factor stability는 입증되지 않았다.**
서로 다른 시간 block의 temporal loading을 같은 좌표의 component처럼 정렬해 비교하지 않았다.
동일 factor의 의미·반복 regime·change point가 재현됐다는 claim도 하지 않는다.

targeted tensor-time-slice shuffle 후 B의 abs lag1 correlation은 .0460/.0297/.0401/.0007,
C는 .0156/.0001/.0192/.0135로 줄지만 singular spectrum과 reconstruction error는 보존된다.
consistent number-label shuffle도 두 구조량을 보존한다. 최대 spectrum 차이는1.54e−11 이하,
최대 error 차이는6.2e−15 이하였다. 이는 단일 deterministic control이며 새 유의성 검정은 아니다.
이미 구성한 overlapping tensor를 순열한 control과 원시 draw에서 tensor를 재구성한 Lotto null을 혼동하지 않는다.

## 개발 결정·예측·ensemble

개발1–900의 strongest descriptive cell은 C number rank6의 early-recent subspace stability였다.
raw .238292,z3.853182. 개발 corrected p:

| Family | IID | fixed-margin |
|---|---:|---:|
| concentration |1.000|.550|
| reconstruction |.525|.450|
| effective_rank |.750|.250|
| stability |.275|.225|
| temporal |1.000|1.000|

stability와 다른 structural family가 각각 양 null에서 corrected p≤.05라는 사전 gate를
통과하지 못했다. 개발 JSON에는 rank 후보,고정 normalization,선택된 diagnostic cell,
결정,source/calibration/raw-null artifact hash를 동결했다.
selection SHA-256: `ea0eac3a49dcb62e85469c4d6c73e4c151c6b41ba11522105d4987908cec0771`.
선택에는900회 metrics만 사용했다.901–1245는 이 설정을 고르거나 gate를 통과시키는 데 사용하지 않았다.

**PREDICTIVE_MODEL_NOT_JUSTIFIED**.

TensorFactorModel과 alternative latent predictor를 만들지 않았다. 따라서 AR forecast,
later walk-forward,Random/Frequency/Gap Logistic 대비 지표·paired bootstrap,
multiple-start predictive robustness·rank correlation은 **해당 없음**이다.
Graph/GapShape ranking도 이를 위해 재학습하지 않았다.
좋은 score가 나올 때까지 임의 predictor를 추가하지 않았다.
ensemble 분류는 **NOT CURRENTLY JUSTIFIED**이며 H17 ensemble은 구현하지 않았다.

## 그림·검증·산출물

reports/tensor/plots 아래9개:

```text
singular_spectra.png
real_vs_iid.png
real_vs_fixed_margin.png
number_factor_loadings.png
temporal_factors.png
tucker_core_energy.png
reconstruction_by_rank.png
factor_stability.png
tensor_slice_reconstruction.png
```

예측 모델이 없어 predictive ranking plot은 만들지 않았다. 그림은 inspection aid다.
전체 `python -m pytest -q -rs --junitxml=reports/tensor/pytest.xml`:
**723 passed,1 skipped**, pytest170.57초(wrapper 포함181.06초).
skip은 기존 `tests/test_predictive_models.py:52`의 optional LightGBM/XGBoost 미설치다.
Phase17 신규98개 테스트는 A/B/C 인덱스·rate·gap·prefix invariance,1246 차단,
unfold/mode product/core/reconstruction/rank/energy,entropy/effective rank,sign/rotation,
low-rank 및 full-rank synthetic,complete-search parity·determinism·자체 maximum,
개발 prefix900 fixed margin·selection·gate,calibration 길이/무결성,canonical artifact 변조,
prospective target/archive guard를 검증했다.

리뷰 수정 후 실제2scope,pilot64개,null796개를 모두 재생해 **모든 raw statistic이
bitwise 동일함**을 확인했다(replay278.21초). primary p-value나 eligible cell 수는 바뀌지 않았다.
첫 main complete-search는225.95초였고, 목표199+199를 축소하지 않았다.

독립 리뷰에서 rank-deficient tensor의 arbitrary SVD nullspace 방향이 stability/temporal 후보에
들어가는 경계를 재현했다. 원본 singular spectrum에 따른 numerical-rank 식별성과 constant-series
undefined 처리를 추가했다. canonical 동결에는32pilot/199null counts·prefix identity·900회 raw-null에서
재계산한 maxima/p 검증을 추가했고 artifact 덮어쓰기도 차단했다. 재리뷰에서 Important 이슈는 해소됐다.

원시 pilot/real/null vector,모든 own maximum,source binary matrix,A/B/C 및 전체 HOSVD spectrum/core/
factor/reconstruction,targeted controls,동결 설정,그림·로그를 로컬에 보존했다.
정확한 파일별 크기·SHA-256은 [run manifest](../reports/tensor/run_manifest.json)에 기록한다.
manifest는 별도 산술 audit로 raw vector→z→global maximum→20개 p-value/보정을 재계산한다.
canonical CSV,이전 Phase16 전용13개 source,frozen Graph/GapShape 예측 파일,Git HEAD가
그대로인지와 `git diff --check`도 확인한다. 로컬 artifact37개(manifest 자체 제외)를 보존했다.

## Prospective 상태·정확한 변경 파일·종료

전체 prospective 상태는 **PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**이다.
Phase17 capability `draw1247_phase17_tensor`는 **NOT_CREATED_NO_JUSTIFIED_MODEL**이다.
archive 복원 대기와 H15 모델 미정당화는 서로 다른 사유다. archive가 복원돼도
unsupported tensor model을 자동 발행하지 않는다. Phase17 publication 명령 자체를 만들지 않았고,
기존 target1246 금지/archive guard를 회귀 검증했다. **실제 prospective snapshot 발행은 없었다.**

기존 수정5개:

```text
.gitignore
README.md
docs/README.md
docs/research-ideas.md
src/cli.py
```

새 파일12개:

```text
docs/tensor-analysis.md
docs/phase17-results.md
docs/superpowers/plans/2026-10-18-phase17.md
src/analysis/tensor_representation.py
src/analysis/tensor_decomposition.py
src/analysis/tensor_search.py
src/analysis/tensor_plots.py
src/tensor_cli.py
tests/test_tensor_representation.py
tests/test_tensor_decomposition.py
tests/test_tensor_search.py
tests/test_tensor_pipeline.py
```

ignore된 로컬 보고서·그림·검증 script도 manifest에서 모두 열거한다.
**draw1246을 fetch/import/use하지 않았으며 commit/push도 하지 않았다.**
Phase17에서 종료한다. Symmetry/Reflection 및 Final weak-signal Ensemble은 구현하지 않았다.
