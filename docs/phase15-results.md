# Phase15 결과 — H13 Modular / Difference-Space Transforms

**H13: TESTED / INCONCLUSIVE.** ModularResidueModel·DifferenceRelationModel은 **NOT CURRENTLY JUSTIFIED**,
GapShapeModel은 **탐색적 ENSEMBLE CANDIDATE**로 보존한다.

199 IID +199 fixed-margin의 동일한 전체 검색에서 다섯 primary family 모두 보정을 통과하지 못했다.
이후 Modular/Difference의 평균Top6는0.8 미만이며 Gap보다 낮았다.
GapShape는 개발 .836에서 이후 .838을 유지하고 Gap/Graph와 낮은 순위 상관을 보였지만,
주요 paired 구간은0을 포함하고 K 선택에 민감했다. 이 후보 분류는 예측 우위가 입증됐다는 뜻이 아니다.

## 시작 상태·데이터

- Git root: `C:/Users/Samsung/OneDrive/Desktop/university/personal/lotto-pattern-lab`.
- branch `main`, 시작 SHA **`c99cd7b1ab21b0165a3fbdd42d54e225d046c796`**.
- root·branch·`git status --short`, README3개·CSV를 먼저 확인했다. 시작 상태는 clean이며 Phase14/H12 완료 상태였다.
- Phase14 manifest20개 source hash가 일치했다. 이후에는 공용 안내/CLI5개 외 Phase14 전용 파일을 보존했다.
- canonical **1–1245회 본번호만**, bonus제외,45열 binary 각 draw6개 active를 사용했다.
- CSV SHA-256: `3b7bb1e0a37c28ae4b4a97e098180d8407008ec007698c191ed6cf279db8225b`.
- **실제1246을 fetch/import/파싱하거나 transform/modulus/lag/model 선택·튜닝·역사 평가에 사용하지 않았다.**
- [방법·수식·support](transformed-space-analysis.md) · [사전 설계·실행 계획](superpowers/plans/2026-10-18-phase15.md).

## 표현과 정확한 검색 규모

Modulus **{2,3,4,5,6,7}**, lag **{1,2,3,4,8,13,26}**를 고정했다.
mod2는 parity reference다. residue0..k−1의 histogram, occupied classes, HHI, entropy(bits),
6−occupied 및 repeatedclasses, 실제 classpopulation을 반영한 hypergeometric imbalance를 계산했다.
단순히 모든 residue의 기대count를6/k로 두지 않았다.

Difference는 정렬한 번호6개, adjacent gaps5개, unordered pair distances15개,
anchored shape=[0,x2−x1,...,x6−x1], normalized gaps=gaps/range다.
wrap은 없다. d0는 temporal self reference로만 보존하며 primary distance는1..44다.
작은 distance의45−d개 pair 기회를 보정했고 adjacent gap에는 별도의 정확한 조합 기대값을 사용했다.

| Primary 범위 | 후보 cell |
|---|---:|
| 정적 modular residue imbalance |27|
| k6 × lag7 × histogram/HHI/entropy |126|
| k/lag/residue/sourcecount0..6 successor |1323|
| **Modular primary 합계** |**1476**|
| temporal lag7 × absolute distance44 |308|
| normalized gap lag7 및 causal neighbor K10/25 |9|
| **Difference/shape primary 합계** |**317**|
| **다섯 family 총합** |**1793**|

1323개 successor cell 중 실제811개가 support>=20·분산·비상수 조건을 통과했다.
각 surrogate에도 같은 조건을 다시 적용하므로 eligible 수는 달라질 수 있다.
위 숫자는 지원 이전 upper bound이며 독립 검정 개수가 아니다.
within-draw pair/adjacent의44+44개 distribution bin은 별도 descriptive reference이고 새 primary family가 아니다.
shape의 query끝점은104,130,...,1222,1244의45개다. 마지막 successor는1245다.
이45개 query의 eligible 과거 candidate 비교는29,246쌍이며 각 K가 동일한 거리 규칙을 적용한다.
모델 개발 후보는 Modular42개·Difference14개·GapShape4개, 합60개다.

## 가장 강한 modular 구조

- **정적 imbalance:**mod7/residue2의 전체 count1111, IID expected1162, z=−1.729321.
  fixed-margin은 모든 번호 총량을 보존하므로 이 residue 총량도 보존된다. 이 family의 fixed p=1은 예상된 불변성이다.
- **Temporal:**mod3/lag26, concentration(HHI) correlation=+.082890.
- **Successor:**mod5/lag3/residue3, sourcecount0일 때 future 같은 residue 평균1.070234,
  aligned future baseline1.219002, support299, normalized z=−3.142090.
  이는 선택된 조건의 local 차이이며 global 보정을 통과하지 못했다.
- 단일 draw/recent state는 같은 residue count로만 조건화했다. cross-residue grammar나 수십 modulus는 검색하지 않았다.

## Difference·gap shape 결과

within-draw pair opportunity로 보정한 가장 큰 descriptive lift는 d13이었다.
count650, expected603.636, lift1.07681, 기회당count20.3125(IID18.8636)다.
다음은 d15의609/565.909(lift1.07614), d28의344/320.682(lift1.07271)였다.
이는 distribution 설명이며 각 lift에 독립 p-value를 부여하거나 발견 근거로 주장하지 않는다.

**가장 강한 temporal lag×distance는 lag1/d27**이었다.
observed729, source-position opportunity5991, IID conditional expected798.8, z=−2.782027이다.
이는 초과 출현이 아니라 부족 출현이며 특정 거리를 hardcode하는 데 사용하지 않았다.
308개 후보 전체 최대를 null의 자체 최대와 비교했다.

Gap-shape family 최대는 lag2의 normalized gap pooled correlation−.025510,
scaled |r|√N=.899383이었다. causal-neighbor successor MSEgain paired-t는
K10=−.525850, K25=−.561747로 둘 다 baseline보다 나빴다.
45개 query의 평균 MSEgain은 각각−.00057655/−.00027006이었다.
과거에서 가까운 shape를 찾는 것은 가능했지만 그 다음 shape가 더 잘 예측된다는 근거는 없었다.

GapShapeModel은 실제 successor 번호를 smoothing해 ranking하므로 위 normalized-shape MSE와 target이 다르다.
이 두 결과를 독립적인 확인 근거로 합치지 않는다.

## IID·fixed-margin 전체 최대값 비교

각 surrogate가 모든 representation을 재구축하고 자신의 modulus·lag·residue state·distance·shape 설정을 골랐다.
실제 최고 후보 위치에 null을 고정하지 않았다.

| Family | Real max | IID global p | IID 보정 p | Fixed global p | Fixed 보정 p |
|---|---:|---:|---:|---:|---:|
| Modular imbalance |1.729321|.825|1.00|1.000|1.00|
| Modular temporal |.082890|.225|1.00|.190|.95|
| Modular successor |3.142090|.730|1.00|.735|1.00|
| Absolute distance |2.782027|.820|1.00|.750|1.00|
| Gap shape |.899383|.440|1.00|.445|1.00|

p=(1+exceed)/(199+1), 다섯family Bonferroni=min(1,5p), empirical 해상도 .005다.
어느 family도 두 null에서 unusual한 구조를 보이지 않았다.
fixed-margin Curveball20rowtrades는 row6개·전체 번호 빈도를 보존하지만 유한 mixing 한계가 있다.
정적 residue family를 시간 구조의 증거로 해석하거나 두 null 중 유리한 것만 고르지 않는다.

## 개발 선택과 동결

개발 target **401–900(500개)**, 이후 **901–1245(345개)**다.
앞선 Phase에서도 사용한 역사이므로 pristine holdout은 아니다.
개발은 정확히1..900만 받았으며 평균Top6, tie선언순서로 선택했다.

| 모델 | 선택 | 개발 평균Top6 |
|---|---|---:|
| ModularResidueModel |single mod7, lag13, support20, shrink50|.888|
| DifferenceRelationModel |lag3, support20, shrink100, source-opportunity/boundary correction|.880|
| GapShapeModel |K25, normalized-gap Euclidean, exclusion26, Gaussian sigma1|.836|
| Frequency26 |own frequency26|.792|
| equal-rank main 조합 진단 |**허용 안 됨**|.872|

GapShape의 두 개발절반 평균 .808/.864가 사전 조건>.8을 통과했고 전체 평균도 Frequency26을 넘었다.
따라서 optional 모델을 이후 평가에 포함했다. 조합은 두 parent를 이기지 못해 이후 모델로 추가하지 않았다.
Modular는 single-modulus 모델이며 여러 modulus 조합을 사후 만들지 않았다.
Difference는 특정 d를 골라 hardcode하지 않고 training의 모든 지원 distance weight를 학습한다.

설정 SHA-256: **`f6cac03e51aa8036824301d4d07a559900fb18a3674f2a2826b8c99eacfc3eb3`**.
transition·distance table·neighbor·normalization은 모든 target에서 prefix<T로 다시 계산했다.
cache key는 prefix bytes·shape·고정 parameter다. 실제 transformed cutoff는T−1이며 cadence outer anchor를 따로 기록했다.

## 이후 walk-forward

주 결과는 Gap cadence26이다. transformed 모델은 매 target에서 업데이트한다.
모든 비무작위 Top6는 deterministic하며 같은 score는 작은 번호 우선이다.
Modular는 같은 residue 안에 동점이 많다는 표현상의 제한이 있다.

| 모델 | 평균Top6 | Recall@6 | Recall@10 | Recall@15 | Mean winning rank↓ |
|---|---:|---:|---:|---:|---:|
| Random |.7681|.1280|.2198|.3367|22.9585|
| Frequency26 |.7739|.1290|.2072|.3145|23.3362|
| Gap Logistic |.8348|.1391|.2169|.3309|23.0343|
| Modular |.7855|.1309|.2155|.3217|23.3068|
| Difference |.7768|.1295|.2227|.3333|22.9850|
| GapShape |.8377|.1396|.2353|.3454|22.8357|

| 모델 | hits0 | hits1 | hits2 | hits3 | hits4 | hits5 | hits6 | Top8≥5 | Top10≥5 | Top12≥5 | Top15≥5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Random |149|135|53|8|0|0|0|0|0|0|0|
| Frequency26 |142|144|54|5|0|0|0|0|0|0|4|
| Gap |141|135|55|13|1|0|0|0|1|1|4|
| Modular |144|139|55|6|1|0|0|0|0|0|2|
| Difference |140|145|57|3|0|0|0|0|0|0|0|
| GapShape |139|136|58|11|1|0|0|1|1|2|5|

**Top6/8/10/12/15 all-six 사건은 모든 모델에서0회**였다.
희귀사건0에 따른 퇴화 bootstrap 구간은 사건확률0을 뜻하지 않는다.

paired circular block-bootstrap2000회, block26의 평균Top6 차이와95% 구간:

| 모델 | 기준선 | 차이 | 95% interval |
|---|---|---:|---|
| Modular |Random|+.0174|[−.0957,.1391]|
| Modular |Gap|−.0493|[−.1333,.0348]|
| Difference |Random|+.0087|[−.0899,.1014]|
| Difference |Gap|−.0580|[−.1739,.0464]|
| GapShape |Random|+.0696|[−.0406,.1768]|
| GapShape |Gap|+.0029|[−.1014,.1159]|

주요 구간은 모두0을 포함했다. Difference가 Frequency26보다 .0029 높다는 점추정치도 우위 증거가 아니다.
여러 모델·metric·기간 전체에 대한 동시구간으로 해석하지 않는다.

## 시간·parameter 강건성

| 모델 | early901–1015 | middle1016–1130 | recent1131–1245 | start1001 | start1101 |
|---|---:|---:|---:|---:|---:|
| Modular |.6261|.8261|.9043|.8490|.8690|
| Difference |.8087|.8087|.7130|.7714|.7034|
| GapShape |.8000|.8783|.8348|.8735|.8621|
| Gap |.7565|.9130|.8348|.8653|.8828|
| Frequency26 |.6696|.9043|.7478|.8122|.7586|
| Random |.7739|.8261|.7043|.7673|.6966|

Modular의 최근 상승과 early 급락은 불안정하다. Difference는 recent/start1101에서 약해졌다.
start1101의 Difference−Gap 차이는−.1793, 구간[−.3448,−.0345]로 나빴다.
GapShape−Gap는 start1001에서+.0082 [−.1143,.1429], start1101에서−.0207 [−.1862,.1241]이다.
여러 시작은 고정 예측열의 subset이며 새 설정을 고르지 않았다.

cadence13에서는 Gap 평균 .8319, 세 transformed 평균은 그대로였다.
Gap 대비 차이/구간은 Modular−.0464 [−.1449,.0551], Difference−.0551 [−.1537,.0464],
GapShape+.0058 [−.1101,.1275]였다. block52 sensitivity에서도 세 모델의 Random/Gap 구간 모두0을 포함했다.
특히 GapShape−Gap의 block52 구간은[−.0812,.0928]이다.

사전60개 후보의 later sensitivity는 진단용으로만 계산했다.
mod7/lag8=.8174, mod7/lag13=.7855, mod7/lag26=.7594, mod6/lag13=.8377로 modulus/lag 의존성이 있다.
Difference lag3/support40=.7768로 지원 경계 변경은 같았지만 lag2=.7072, lag4=.7565, lag8=.8029였다.
선택된 lag3가 강건한 양의 후보가 되지는 못했다.
GapShape K25에서 sigma2=.8261로 좁은 smoothing 변경에는 양의 점추정치가 남았으나
K10/sigma1=.7478, K10/sigma2=.7797로 neighbor 수에 민감했다.
이후 최고 설정으로 교체하거나 consensus를 사후 추가하지 않았다.

전체 역사에서 선택한 고정 구조의 세 era 진단도 저장했다.

| 구조 | early1–415 | middle416–830 | recent831–1245 |
|---|---:|---:|---:|
| mod7/residue2 정적 imbalance z |−.9593|−2.3688|+.3328|
| mod3/lag26 HHI correlation |+.0678|+.0829|+.0969|
| selected mod5/lag3 successor z |−2.3957|−3.1843|+.3100|
| lag1/d27 z |−1.6989|−2.6330|−.4691|

modular temporal 방향은 유지됐지만 global null 보정은 유의하지 않았다.
선택된 successor 차이는 최근 사라졌고 distance 부족도 최근 약해졌다.
W208·step52 rolling은 고정 규칙의 descriptive trace이며 새로운 independent 검정이나 tuning 구간이 아니다.

## Rank diversity·후보 결정

번호 좌표를 맞춘345회 평균 Spearman 및 TopK 교집합이다.

| 모델 | 기준 | Spearman | Top6 overlap | Top10 | Top15 |
|---|---|---:|---:|---:|---:|
| Modular |Gap|−.1058|.6522|2.1159|4.3072|
| Modular |frozen Graph|+.0066|.7391|2.2029|5.0754|
| Difference |Gap|−.0017|.6725|2.0290|4.9101|
| Difference |frozen Graph|−.0163|.7391|2.1623|4.9101|
| GapShape |Gap|−.0357|.6609|1.9971|4.7565|
| GapShape |frozen Graph|+.0024|.7855|2.2290|5.0464|

**기존 Phase14 Graph prediction CSV만 읽었으며 Graph를 refit/reselect/retune하지 않았다.**
같은 cadence의 고정 출력과 비교했고 원본 artifact hash 불변을 검증했다.

- **ModularResidueModel: NOT CURRENTLY JUSTIFIED.** 개발 .888에서 이후 .786으로 약화했고 early/recent 편차가 크다.
- **DifferenceRelationModel: NOT CURRENTLY JUSTIFIED.** 낮은 상관만으로 부족하다. 개발 .880에서 이후 .777로 약화하고 recent에 나빴다.
- **GapShapeModel: ENSEMBLE CANDIDATE — 탐색적 보존용.** 개발/이후 .836/.838, 세 era .8 이상,
  양 baseline ranking과 낮은 상관을 보존한다. 그러나 주요 신뢰구간은0을 포함하고 K 민감도가 있다.
  이후 H17에서 검증할 다양성 후보라는 분류이며 통계적으로 확인된 transformed-space 예측 신호는 아니다.

**H13은 PROMISING 조건을 충족하지 않는다.** unusual 구조와 강건한 예측 우위를 함께 확인하지 못했다.
표본·표현 손실 한계를 고려하여 모든 가능한 변환 관계를 영구 부정하는 결론도 내리지 않는다.

## 실행·그림·검증

2+2 benchmark의 sequential398회 예상은180.22초였다.
workers4의 전체199+199 검색은 **138.61초**, 개발 선택은154.81초였다.
결과가 매력적인지에 따라 null 노력이나 탐색 범위를 줄이지 않았다.
새 package 설치나 draw-data network 수집 없이 기존 NumPy/SciPy를 사용했다.

`reports/transformed_space/plots/`에10개 PNG를 저장했다.

```text
residue_distribution_overview.png
strongest_residue_temporal.png
modular_real_vs_null.png
absolute_difference_expectation.png
lag_distance_heatmap.png
strongest_distance_through_time.png
adjacent_gap_projection.png
difference_real_vs_null.png
model_ranking_example.png
rank_correlation_comparison.png
```

그림은 evidence 자체가 아니다. 역사 target1245의 세 모델 점수를 <=1244만으로 재계산해 저장값과 정확히 일치함을 확인했다.
binary·modular histogram/conditional tables·difference/gap arrays·distance tables·shape query와
398개 null progress/maxima/hash, 개발·later sensitivity, 두 cadence의 예측/전체지표/paired/diversity/protocol을 보존했다.
원시 local값·null 초과수·family 보정값은 CSV/NPZ에 남겼다.
정확한 로컬 산출물48개(manifest자체 제외)의 목록·크기·SHA-256 및 변경source21개의 hash는
[run manifest](../reports/transformed_space/run_manifest.json)에 있다.

전체 `python -m pytest -q -rs`: **545 passed,1 skipped**,94.50초.
skip은 기존 `tests/test_predictive_models.py:52`의 optional LightGBM/XGBoost 미설치다.
새 테스트57개가 modular/parity·lag·conditional table,15differences/gaps/anchor,
opportunity/finite-axis variance·planted distance, causal shape neighbors,
source cutoff1245·future suffix 거부·모델prefix입력·walk-forward cutoff,
동일한 surrogate 검색/global-max·개발전용선택/hash·rank correlation·archive block을 검증했다.
독립 리뷰는 수식·경계·causality·gate와 저장된 두 cadence의 모든 지표/cutoff/paired/diversity를 확인했고
critical/important finding은 없었다.

## Prospective·정확한 변경 파일·종료 범위

**PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**.

`draw1247_phase15_transformedspace`의 설정 및 기존 archive 검증 준비 gate를 구현했다.
실제 CLI가 archive 부재에서 위 상태로 거부하는 것을 확인했다. target1246은 항상 금지다.
archive가 복원돼도 기존 verifier·원본 protected inventory와 명시적 import/refit/publication이 더 필요하므로
실제1247 publication 준비 완료를 주장하지 않는다.
**어떤 prospective snapshot도 발행하지 않았으며 부재한 archive·옛 순위·hash를 재구성하지 않았다.**

Git-visible 기존 수정5개:

```text
.gitignore
README.md
docs/README.md
docs/research-ideas.md
src/cli.py
```

새 파일16개:

```text
docs/phase15-results.md
docs/transformed-space-analysis.md
docs/superpowers/plans/2026-10-18-phase15.md
src/analysis/difference_space.py
src/analysis/modular_space.py
src/analysis/transformed_plots.py
src/analysis/transformed_search.py
src/backtest/transformed_space.py
src/models/transformed_space.py
src/phase15_freeze.py
src/transformed_cli.py
tests/test_difference_space.py
tests/test_modular_space.py
tests/test_transformed_models.py
tests/test_transformed_pipeline.py
tests/test_transformed_search.py
```

추가 생성된 ignore된 보고서·그림·검증 script도 manifest에서 모두 열거한다.
canonical CSV·Phase14 전용 파일·frozen Graph 예측·HEAD 불변과 `git diff --check`를 검증했다.
**draw1246 미사용, prospective publication 없음, commit/push 없음**을 확인했다.
Phase15에서 종료했다. H14 Entropy/Compression, Tensor, Symmetry/Reflection, H17 최종 ensemble은 구현하지 않았다.
