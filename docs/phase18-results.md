# Phase18 — Symmetry / Reflection / H16 결과

## 판정·시작 상태

**H16 — Symmetry / Reflection: TESTED / INCONCLUSIVE**.

고정 중심 reflection,anti-symmetry,제한된 shift가 complete-search null을 넘어선다는 근거를
확보하지 못했다. 역사 비교용 MirrorModel은 약한 양의 점추정치와 낮은 순위 상관을 보였다.
이를 **탐색적 ENSEMBLE CANDIDATE**로 보존하지만,통계적 예측 우위나 H16 PROMISING 판정은 아니다.
prospective에 정당화된 모델은 없으며 H17 final ensemble도 만들지 않았다.

- Git root: `C:/Users/Samsung/OneDrive/Desktop/university/personal/lotto-pattern-lab`.
- 시작 branch `main`,SHA `4082663dab77489b47843f182c3f28bb5c71c480`.
- `git rev-parse --show-toplevel`,현재 branch,`git status --short`를 확인했다. 시작은 clean이었다.
- README.md,docs/README.md,docs/research-ideas.md,data/raw/lotto_history.csv를 읽었다.
- 완료된 Phase17 manifest의 source17개 hash가 모두 일치했다. 무관한 변경은 없었다.
- CSV는1–1245회이며 bonus를 분석에서 제외했다. 실제1246은 가져오거나 사용하지 않았다.
- CSV SHA-256: `3b7bb1e0a37c28ae4b4a97e098180d8407008ec007698c191ed6cf279db8225b`.
- 기존 reports/prospective archive는 부재했다. 복원·재생성·publication하지 않았다.

## Transform·same-draw 결과

primary mirror(n)=46−n,중심23,22쌍1↔45,…,22↔24다.
mirror(mirror(n))=n이며23은 self point로 따로 처리했다. wrap/clip/dynamic center 탐색은 없다.
pair 수P,center indicator C에서 draw symmetry=2P/(6−C),Jaccard=(2P+C)/(12−2P−C)다.
side balance와 mirror symmetry는 다른 지표다.

| 지표 | 실제 | 정확한 IID 기대 |
|---|---:|---:|
| draw당 complete mirror pairs |.345382|.333333|
| draw당 paired numbers |.690763|.666667|
| normalized draw symmetry |.117055|.113178|
| Jaccard(A,M(A)) |.083704|.082492|
| below23 count |2.942972|2.933333|
| above23 count |2.937349|2.933333|
| absolute left/right imbalance |1.783936|1.747022|
| center23 포함 draw 수 |149|166|

전체1245회에서 complete pairs는430개였고,pair count0/1/2/3의 draw 수는844/373/27/1이었다.
최대3쌍이 한 draw에서 나타났지만 이것만으로 signal이라고 해석하지 않는다.
정확한 IID joint distribution과 side distribution을 별도 저장했다.
같은 draw 안의 pair들을 독립 표본으로 세지 않았다.

## Pooled lag·strongest pair·방향성

lag={0,1,2,3,4,8,13,26,52}다. source23을 primary에서 제외했다.
lag0의 IID 조건부 기준은5/44이며 positive lag는6/45다.

| lag | source events | mirror hits | rate | lift |
|---:|---:|---:|---:|---:|
|0|7321|860|.117470|1.033739|
|1|7315|994|.135885|1.019139|
|2|7309|992|.135723|1.017923|
|3|7303|995|.136245|1.021840|
|4|7297|989|.135535|1.016514|
|8|7274|1011|.138988|1.042411|
|13|7245|953|.131539|.986542|
|26|7167|943|.131575|.986815|
|52|7014|956|.136299|1.022241|

strongest pooled candidate는 lag8,risk difference=.005655,pilot z=1.352508이었다.
draw-block52 bootstrap1000개의 descriptive95% rate interval은[.131830,.146940]이다.
이것은9lag 선택 보정 구간이 아니며,global pooled p는IID .595/fixed .640이었다.
center23의 lag0 hit율1은 별도 reference이며 primary evidence가 아니다.

strongest pair는 **13→33,lag8**이다. support179,hit42,조건부 rate=.234637,
aligned target baseline=.140663,risk difference=.093974,lift=1.668079,pilot z=4.145042였다.
44방향×9lags와 activity 후보까지 검색한 global pair p는IID .225/fixed .160이다.
이 pair의 local working z=3.616284를 uncorrected p-value로 변환하지 않았다.

strongest directional asymmetry는 **9↔37,lag3**이다.
9→37:27/136=.198529,37→9:12/174=.068966,차이=.129564,pilot z=4.440297.
global asymmetry p는IID .365/fixed .245로 directionality evidence는 남지 않았다.
lag0의 conditional asymmetry는 source marginal 차이로도 생길 수 있어 정보 흐름으로 부르지 않는다.

## Anti-symmetry·regime·shift

global anti winner는 **27의 W26 activity→19 activity,lag26**의 correlation **−.288353**이다.
pilot z=3.460942,global anti p=IID .370/fixed .405,보정은 모두1이다.
whole/early/middle/recent correlation은−.2884/−.1968/−.4203/−.1915였다.
강한 음의 그림도 같은 검색의 null 최대값보다 특별하지 않았다.
별도의 strongest negative binary relation은6→40,lag13이었다:
13/165=.078788,baseline=.137175,risk=−.058387. 이를 global anti winner와 혼동하지 않았다.

rolling whole-system W={26,52,104},step26+최종 endpoint를 사용했다.
regime family winner는draw105–208,W104의 **side imbalance2.173077**,z2.935597이었다.
이는 mirror symmetry regime와 다르다.
가장 큰 normalized mirror-symmetry 후보는draw1093–1118,W26의 mean symmetry=.194872,
mean pairs=.576923(26회에15쌍),z2.483112였다.
rolling mean binary correlation도 같은 family에 포함했다.
regime global p=IID .620/fixed .660으로 일시적 regime의 corrected evidence는 없었다.

secondary T_k(n)=46−n+k,k={−4,−2,0,2,4}의 winner는**k=−2,lag0**이었다.
valid source labels41개,source events6834,hit848,rate=.124085,기준5/44,lift1.091952,
risk difference=.010449,z2.208425였다. shift global p=IID .655/fixed .700이다.
범위 밖 target/source23/transform fixed point 제외 정책과 label별 opportunity를 저장했다.
다른 source가 target23으로 매핑되는 것은 허용했으며 wrap/clip이나 임의 중심 검색은 하지 않았다.

## Exact search 공간·null 결과

| Family | 전체1245 cells | 개발900 cells | IID global p | IID corrected p | fixed global p | fixed corrected p |
|---|---:|---:|---:|---:|---:|---:|
| same_draw |4|4|.335|1.000|.355|1.000|
| pooled |9|9|.595|1.000|.640|1.000|
| pair |1518|1518|.225|1.000|.160|1.000|
| asymmetry |198|198|.365|1.000|.245|1.000|
| regime |560|404|.620|1.000|.660|1.000|
| anti |1528|1528|.370|1.000|.405|1.000|
| secondary shift |45|45|.655|1.000|.700|1.000|
| 전체 |**3862**|**3706**| | | | |

pair family는396개 binary conditional risk와1122개 positive activity correlation이다.
anti는이들의 negative orientation,pool negative9개,mean imbalance1개다.
regime는full140개/development101개 window×4metrics다. shift0 pooled9개는 의도된 reference 중복이다.
모든 actual candidate가 eligible였으며 파일별 pilot/null eligibility도 보존했다.

독립 IID32pilot/cutoff(seed181001)와 main IID199+fixed199/cutoff(seed180042)를 사용했다.
scope마다 surrogate에서 원시 draw→mirror/activity/regime/shift를 재구성하고 각 family 자체 maximum을 골랐다.
global p=(1+exceedances)/200,seven-family Bonferroni=min(1,7p)다.
**고정 중심 symmetry·anti-symmetry·secondary shift 어느 것도 보정 후 남지 않았다.**
finite Monte Carlo 및32pilot calibration의 불확실성,Curveball finite mixing 한계는 남는다.
이 결과는 모든 reflection 관계의 부재나 완전한 randomness를 증명하는 것은 아니다.

전체·개발 raw3862/3706cells,64pilot,796개 main surrogate history의 raw vector/maxima를 보존했다.
real2scopes까지 합치면862개 complete search,총3261808개 raw statistic 평가다.
별도 benchmark8scope-search와 모델 개발48configs는 이 null 검정 수에 넣지 않는다.
main complete search는144.57초로 목표199+199를 축소하지 않았다.

## 역사적 안정성

구조 진단 시대는early1–415,middle416–830,recent831–1245다.
13→33 lag8의 risk difference는.086231/.057343/.140751,
조건부 rate는.211538/.209677/.285714,source support52/62/63이었다.
방향 차이9→37 minus37→9는.168648/.152778/.069501로 최근 작아졌다.
6→40 lag13의 negative risk는−.045533/−.081697/−.039632였다.
같은 pair를 유지한 rolling W26/52/104의 raw rate/support도 저장했다.
rolling source support10 미만은 descriptive plot에서 제외했고 primary pair support20과 구분했다.
이후 era/rolling 진단은 full-history selected pair를 다시 보는 것이므로 독립 확인이 아니다.

## Development-selected MirrorModel

descriptive/null을 완료한 뒤 pooled causal MirrorModel을 구현했다.
W{10,26,52}×positive lags8개×shrinkage{50,200}=48개를target401–900에서 비교했다.
고정된 계수·source-support attenuation·score 수식은 [방법](symmetry-analysis.md)에 있다.
번호별 source/target mean을 제거하며Gap/Graph feature는 넣지 않았다. center23 score는 중립 p=6/45다.

선택: **window10,lag1,shrinkage200,support20,pooled linear ridge,score별 available-prefix 재fit**.
개발평균Top6=.896,Frequency26=.792였다.
개발401–650/651–900의 Mirror=.948/.844,Frequency=.820/.764였다.
선택에 사용한900회 prefix hash는 `a969e5a2e4254fb56e86ed6c8aa550ecef9cb19b7e61d66366df9a4ab13bd3c3`다.
selection SHA-256: `6476edcd3f8e989c89a93aa76dc1c83c81f62ead1c4047348f0f0a7c7c00b1a9`.
이후 결과를 보기 전에 설정을 동결했으며 더 좋은 later 설정으로 교체하지 않았다.

개발의 corrected p는pair family 양 null 모두1이었다.
asymmetry는IID .455/fixed .490,regime .280/.560으로 이들도 통과하지 못했다.
따라서 sparse pair predictor인 MirrorPairModel과 secondary-shift predictor는 구현하지 않았다.
역사 실험 MirrorModel의 존재가 구조 가설의 유의성이나 prospective 정당화를 뜻하지 않는다.

## 이후901–1245 성능

345개 target마다 history<T만 사용했다. Gap은 authenticated Phase15 frozen output을 읽었으며 재학습하지 않았다.
Random/Frequency/Mirror는causal engine에서 평가했다.
이 구간은 앞선 Phase들도 사용한 역사 자료이며 pristine holdout이나 실제 prospective 검증이 아니다.

| 모델(cadence26 기준) | 평균Top6 | Recall@6 | Recall@10 | Recall@15 | 평균 winning rank |
|---|---:|---:|---:|---:|---:|
| MirrorModel |.826087|.137681|.224638|.325604|23.139614|
| RandomModel |.768116|.128019|.219807|.336715|22.958454|
| Frequency26 |.773913|.128986|.207246|.314493|23.336232|
| GapLogistic |.834783|.139130|.216908|.330918|23.034300|

Mirror의0–6 hit distribution은138/143/52/10/2/0/0이다.
Top8/10/12/15≥5 event는0/0/0/1회이며,모든6/8/10/12/15 pool의 all-six event는0이었다.
희귀 event의 bootstrap 구간이0으로 퇴화하는 경우를 확실한 확률0으로 해석하지 않는다.

평균Top6의 paired block26 bootstrap2000회,95% interval:

| 기준 | Mirror−기준 |95% interval|
|---|---:|---|
| Random |+.057971|[−.026087,.142029]|
| Frequency |+.052174|[−.055072,.162319]|
| Gap |−.008696|[−.110145,.089855]|

cadence13에서도 Mirror/Frequency/Random은 target마다 갱신되어 같은 순위다.
frozen Gap13의 평균은.831884였다. block13 interval은Random[−.037681,.159420],
Frequency[−.066667,.176812],Gap[−.107246,.098551]로 모두0을 포함했다.
block52 민감도에서Random 차이 구간은[.005797,.104348]로 약하게 양수였으나,
Frequency[−.037681,.139203],Gap[−.095652,.072464]는0을 포함했다.
여러 starts/metrics/blocks 중 유리한 구간 하나를 독립적인 예측 증거로 선택하지 않았다.

## Predictive robustness·다양성·candidate 결정

| 이후 시작 | Mirror | Random | Frequency | Gap26 |
|---:|---:|---:|---:|---:|
|901|.826087|.768116|.773913|.834783|
|1001|.804082|.767347|.812245|.865306|
|1101|.793103|.696552|.758621|.882759|

이후 early901–1015/middle1016–1130/recent1131–1245의 Mirror는.834783/.852174/.791304다.
최근 성능은 이론적 Random 기대.8보다 낮다. 시작1101의Random realization이 특히 낮아
그 부분의 양의 paired 구간만으로 절대적인 우위를 주장하지 않는다.

인접 설정의 이후 평균Top6(모두 shrink200,재선택 없음):
W10/lag1=.826087,W10/lag2=.820290,W26/lag1=.886957,W26/lag2=.881159.
작은 주변 grid의 전체 점추정치는 양수였지만 더 좋은W26을 사후에 채택하지 않았다.

각 reference345target와의 평균 diversity:

| 기준 | Spearman | Top6 overlap | Top10 overlap | Top15 overlap |
|---|---:|---:|---:|---:|
| Gap Logistic |.007219|.739130|2.000000|5.043478|
| frozen GraphStructure |.024548|.947826|2.394203|5.150725|
| frozen GapShape |−.005878|.739130|2.205797|5.008696|
| frozen MI |−.002914|.742029|2.231884|5.020290|

기존 모델은 diversity를 위해 refit/reselect하지 않았다. 번호별 assigned rank 좌표에서 Spearman을 계산했다.
**MirrorModel: ENSEMBLE CANDIDATE(탐색적 보존)**.
약한 양의 전체/주변 설정 점추정치와 낮은 Gap/Graph 상관을 보존하는 사후 연구 분류다.
주요 CI는0을 포함하고 최근 성능이 약하며 corrected 구조 근거가 없으므로
statistical evidence,안정적인 predictive benefit,final ensemble 채택으로 해석하지 않는다.
MirrorPairModel은 미구현이며 별도 candidate로 분류하지 않는다.

## Tests·그림·무결성

전체 `python -m pytest -q -rs --junitxml=reports/symmetry/pytest.xml`:
**779 passed,1 skipped**,pytest160.72초(wrapper163.25초).
skip은 기존 `tests/test_predictive_models.py:52`의 optional LightGBM/XGBoost 미설치다.
신규56개 테스트는mirror45/involution/23,exact expectation/side balance,lag/pool/pair/asymmetry,
causal activity/anti/shift boundary,synthetic relation,global own-max/rebuild/parity/determinism,
prefix900 fixed-margin,Mirror leakage/constant/null/synthetic,개발선택/frozen reference hash/
walk-forward cutoff/rank diversity,1246 source seal 및 target/archive guard를 검증했다.

독립 리뷰에서 Critical/Important 이슈는 없었다. minor인 center0support,shift opportunity 보존,
selected-pair rolling을 보강했다. 별도 row-loop 계산은48모델 설정과1e−14 안에서 일치했고,
stale outer fit으로 더 긴 completed prefix를 score해도 최신 causal fit과 일치했다.

reports/symmetry/plots의11개 inspection 그림:

```text
mirror_mapping.png
same_draw_symmetry.png
pooled_lag_strength.png
pair_lag_heatmap.png
directional_asymmetry.png
rolling_symmetry.png
strongest_pair_time.png
symmetry_anti.png
global_max_null.png
model_ranking.png
secondary_shift_heatmap.png
```

raw→pilot z→family maximum→28개 global p/보정을 독립 audit하고,예측 metric·paired CI·rank diversity도
저장된 ranking에서 확인한다. exact source/artifact hash·테스트·선택·그림 inventory는
[run manifest](../reports/symmetry/run_manifest.json)에 기록했다.
로컬 artifact63개(manifest 자체 제외)의 경로·크기·SHA-256을 보존했다.
원본CSV,이전Phase17 전용12개source,Graph/GapShape/MI frozen 출력,HEAD의 무변경을 확인했다.

## Prospective·정확한 변경 파일·종료

**PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**.

`draw1247_phase18_symmetry` capability는 **NOT_CREATED_NO_JUSTIFIED_PREDICTIVE_MODEL**이다.
역사 실험 모델은 있으나 corrected 구조와 robust 예측 개선이 없어 prospective 기능을 만들지 않았다.
archive 복원 대기와 예측 미정당화는 별개다. archive가 복원돼도 unsupported 모델을 자동 발행하지 않는다.
**실제1247 snapshot 발행은 없었으며 실제1246을 fetch/import/use하지 않았다.**
마지막 역사 ranking example도target1245,training1244이며 prospective가 아니다.

기존 수정5개:

```text
.gitignore
README.md
docs/README.md
docs/research-ideas.md
src/cli.py
```

새 파일14개:

```text
docs/symmetry-analysis.md
docs/phase18-results.md
docs/superpowers/plans/2026-10-18-phase18.md
src/analysis/symmetry.py
src/analysis/symmetry_search.py
src/analysis/symmetry_plots.py
src/models/symmetry.py
src/backtest/symmetry.py
src/symmetry_cli.py
tests/test_symmetry.py
tests/test_symmetry_search.py
tests/test_symmetry_models.py
tests/test_symmetry_backtest.py
tests/test_symmetry_pipeline.py
```

ignore된 로컬 보고서·그림·검증 script도 manifest에 열거했다.
**commit/push 없음**이며 Phase18에서 종료했다. H17 final weak-signal Ensemble은 구현하지 않았다.
