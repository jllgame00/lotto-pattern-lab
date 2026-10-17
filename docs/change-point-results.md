# Phase19 결과 — H18 Change-point / piecewise-stationary regimes

**H18: TESTED / INCONCLUSIVE.** 사전 제한한 표현·penalty·경계 grid에서는 실제 history의 change point가 complete-search null보다 특이하다는 근거가 없었다. Adaptive segment 예측의 우위도 확인되지 않았다. Lotto의 모든 가능한 비정상성을 배제한다는 뜻은 아니다.

## 시작 상태와 범위

Git root는 `C:/Users/Samsung/OneDrive/Desktop/university/personal/lotto-pattern-lab`, 시작 branch는 clean `main`, 시작 SHA 및 종료 HEAD는 `c16e6c81be6ff2f4ce3e85ec4771171cb9ef6b64`이다. 시작 시 Phase18/H16 완료 manifest의19개 changed-file hash를 모두 검증했다. 관련 없는 기존 변경은 없었다.

`README.md`, `docs/README.md`, `docs/research-ideas.md`, canonical CSV를 확인했다. 데이터는 main numbers draws1–1245이며 CSV SHA-256은 `3b7bb1e0a37c28ae4b4a97e098180d8407008ec007698c191ed6cf279db8225b`로 유지된다. bonus/실제1246은 representation,선택,검증,평가 어디에도 사용하지 않았다. 외부 fetch/import를 수행하지 않았다.

방법과 수학 정의는 [분석 방법](change-point-analysis.md), 실행 범위는 [계획](superpowers/plans/2026-10-18-phase19.md)에 있다. Local 결과는 `reports/change_point/` 아래에 있으며 [manifest](../reports/change_point/run_manifest.json)와 [독립 감사](../reports/change_point/audit_result.json)가 hash와 재계산 증거를 담는다.

## 표현·penalty·검색 규모

번호별45개 Bernoulli series, A(draw×45 binary), B13/B26/B52(nonoverlap block rate), C(sum/range/std/spacing mean/spacing std/consecutive-pair count/odd count)를 사용했다. A의 row-six 제약을 유지하며 composite Bernoulli likelihood를 물리적 독립 모형으로 해석하지 않았다. C scaler는 각 fitting prefix에서만 계산했다.

Exact dynamic programming은 A/C/개별번호의13회 경계 grid와 B의 complete block grid 안에서만 최적이다. Minimum segment draws={26,52,104}, penalty multiplier={1,2}; penalty=`multiplier×dimension×log(observation count)`이다. B52의26/52 minimum 중복도 그대로 포함했다. Full B13/B26/B52는 각각1235/1222/1196회까지 사용하고 tail10/23/49회를 segmentation에서 제외했다.

|항목|정확한 규모|
|---|---:|
|unit|45번호+5global=50|
|한 prefix의 segmentation|50×3minimum×2penalty=300fits|
|full stability prefix|800/900/1000/1100/1245|
|development stability prefix|500/600/700/800/900|
|한 history/cutoff의 segmentation|1500fits|
|fixed statistic cells|2237=585single+68global+24concentration+360concordance+1200stability|
|eligible cells(full/development)|1555/1566|
|5prefix DP state-unit 합(full/development)|115506/80988|
|5prefix admissible segment transition 합(full/development)|4159740/1989640|
|full CUSUM split 후보|1194개 위치×53개 scalar/vector score=63282|
|full concentration anchor|95위치×24cells=2280|
|개발 모델 grid|5표현×3minimum×2penalty×2shrinkage=60|
|개발 예측|60Regime+3fixed ×500targets=31500rows|

2237cells는 내부의 모든 경계 후보를 집계한 statistic 수이다. 내부 endpoint와 configuration별 DP 규모는 `real_summary.json`의 `space.prefix_inventory`에 별도로 공개한다. main null은398개 history×2cutoff×1500fits=**1194000 unit fits**이며 독립 pilot64개는 별도이다. 상수 pilot cell은 z-search에서 제외하고 mask를 보존했다.

Benchmark의 IID full/development 검색 한 쌍은1.20/1.24초,fixed-margin은3.67/2.67초였다. 결과에 따른 축소 없이 IID199+fixed199를 수행했으며 main runtime은449.22초였다.

## 가장 강한 구조와 안정성

Family 선택은 독립 pilot32개로 표준화한 cell z의 global maximum이다. z를 정규분포 p-value로 해석하지 않는다.

|항목|실제 결과|해석|
|---|---|---|
|single-number family leader|20번,minimum104/penalty1,경계585,rate.170940→.109091,차이.061849,z4.5872|support585/660;null global-max 대비 unusual하지 않음|
|가장 큰 raw adjacent rate jump|33번,minimum26/penalty1,경계689,rate.126270→.461538|다음26회에 국한된 선택된 작은 segment;전체 검출을 보정 없이 해석하지 않음|
|global family leader|45-vector CUSUM,583회,score.615920,z1.8123|CUSUM diagnostic이며 penalized multivariate CP가 아님|
|cross-number concentration leader|923회±13,min104/penalty1,distinct numbers2(5번923/43번936)|raw 절대 최대와 표준화 family leader를 구분|
|concordance leader|B26/B52 best-split proposal572회,F1=1|실제 detected CP는 두 표현 모두없음;독립 확인 아님|
|stability leader|22번507회,min104/penalty1,tolerance13,이전4prefix 모두재검출,score2.737683,z6.2606|null에서도 안정적으로 보이는 경계를 선택할 수 있음|

A/B13/B26/B52/C의 full penalized CP는 **모든30설정에서0개**이다. min104/penalty1의 best-single-split proposal은 A585(gain65.7424,penalty320.7101),B13 585(66.4102/204.9245),B26 572(61.8385/173.2566),B52 572(62.8696/141.0972),C1001(17.5576/49.8882)이다. 서로 가까운 number/block proposal은 존재하지만 강제된 분할의 유사성을 실제 regime evidence로 바꾸지 않았다.

|prefix|20번 detected CP(min104,p1)|22번 detected CP(min104,p1)|
|---:|---|---|
|800|637|351,507|
|900|637|351,507|
|1000|637|351,507,845|
|1100|637|351,507,845|
|1245|585|351,507,845|

20번의 경계는 마지막 prefix에서52회 이동해 tolerance13/26 기준으로 안정적이지 않았다. 22번507회는 유지됐지만 complete-search null에서 특이하지 않았다. 22번 해당 인접 segment의 rate는352–507회 .217949(156회),508–845회 .073964(338회)이다. 기술적 early/middle/recent는1–415/416–830/831–1245이며 full 후보를 고정해 `temporal_eras.csv`에 export했다. 각 era에서 유리한 번호/경계를 새로 선택하지 않았다.

전체 prefix/config의 검출 경계194개는 반복 설정과 prefix를 포함하는 수이며 독립 사건194개가 아니다. Full300fits의 경계 수 합은42개이다. Nonadjacent segment L1/JS/cosine/max-rate-shift는 `nonadjacent_segments.csv`에 기술적으로만 보존했다. Global segmentation이 한 구간이므로 반복하는 global regime을 주장할 근거는 없다. Recurring-regime predictor는 만들지 않았다.

## IID / fixed-margin global-max 결과

각 null마다 모든 표현·45번호·minimum/penalty·다섯 prefix·proposal/actual 경계·concordance/stability를 다시 검색했다. IID와 fixed-margin 각각199개이며 개발 cutoff900은 자체 margin으로 별도 생성했다. Cell normalization은 main과 독립인 pilot32개/cutoff(seed191001),main seed190042이다. p=`(1+exceedances)/200`,다섯 family Bonferroni를 적용했다.

|family|real max z|IID global p|fixed global p|IID/fixed corrected p|
|---|---:|---:|---:|---:|
|single number|4.587236|.850|.875|1/1|
|global shift|1.812329|.470|.500|1/1|
|boundary concentration|.205231|.970|.980|1/1|
|cross-representation concordance|1.270663|.705|.645|1/1|
|prefix stability|6.260567|.555|.525|1/1|

개발 구간의 corrected IID/fixed p는 single.325/.625,global1/1,concentration.875/1,concordance1/1,stability.525/.375였다. 어느 구간에서도 corrected threshold.05를 통과하지 않았다. Local/raw change의 눈에 띄는 정도와 complete-search 유의성을 구분해야 한다. 유한한199개 null과32개 pilot,13회 경계 grid,선택된 penalty family가 분석의 분해능을 제한한다.

## 개발 동결과 이후 예측

개발 target401–900에서 모든60Regime 후보는 평균Top6=.780으로 동률이었다. 선언 순서로 **A/minimum26/multiplier1/shrinkage26**을 동결했다. 개발 전후반은.880/.680이었다. Frequency26=.792,Frequency52=.862,Frequency104=.836이므로 비교 baseline은 개발에서 **Frequency52**로 고정했다. Later 성능으로 baseline을 바꾸지 않았다.

Selection SHA-256은 `31595a00fd4c1d1bbdf55c41938fa835effe74caee929b5f63979e3cbcea3a6e`이다. 개발 우위 요건을 만족하지 않아 Gap+Regime rank-average는 실행하지 않았다.

이후901–1245의345개 target마다 `<T`에서 다시 segmentation했다. 마지막 CP는 **전 target에서0**,current segment length는T−1이다. 따라서 Regime 결과는 adaptive 변화 검출의 성과가 아니라 **cumulative-history frequency**와 같다. 현재 segment raw45rate와 shrink된45rate를 export했고 각 prefix slice와 대조했다. Boundary가 미래 prefix에서 검출됐다는 이유로 과거 target에 소급하지 않았다.

|model(cadence26)|avg Top6|Recall@6|Recall@10|Recall@15|mean winning rank|
|---|---:|---:|---:|---:|---:|
|RandomModel|.768116|.128019|.219807|.336715|22.958454|
|Frequency26|.773913|.128986|.207246|.314493|23.336232|
|Frequency52(dev-selected)|.730435|.121739|.206763|.324155|23.500483|
|Frequency104|.750725|.125121|.214976|.323188|23.425604|
|Gap Logistic(frozen)|.834783|.139130|.216908|.330918|23.034300|
|RegimeFrequencyModel|.794203|.132367|.217391|.324155|23.327536|

Regime hit distribution0–6은 **147,135,50,13,0,0,0**이다. Top8/10/12/15 >=5 event는 **0/2/2/4**회이며 모든 model의 all-six pool event(Top6/8/10/12/15)는0회였다. 전체 비교표와 pool counts는 각 `walk_forward_*/summary.csv`에 있다. 희귀 pool event만 선택해 예측 우위로 판정하지 않았다.

|Regime−reference Top6 difference|point|95% paired block26 interval|block52 interval|
|---|---:|---|---|
|Random|+.026087|[−.063768,.121739]|[−.046377,.107246]|
|Frequency52|+.063768|[−.034783,.165217]|[−.017391,.147826]|
|Gap Logistic|−.040580|[−.139130,.060870]|[−.136232,.052174]|

각2000회의 paired circular block bootstrap이다. 주요 Top6 차이의 구간은 모두0을 포함한다. mean winning rank는 작을수록 좋으며 Regime는 Random/Gap보다 점추정치도 나빴다.

## Robustness・diversity・候補判定

Cadence13도 Regime=.794203,Random=.768116,Frequency52=.730435로 동일했고 frozen Gap=.831884였다. Regime−Gap=−.037681,block13 CI[−.159493,.081159]이다. Start901/1001/1101의 Regime 평균은.794203/.812245/.786207,115target씩의 early/middle/recent는.747826/.826087/.808696이었다. 모든 start/cadence에서 주요 비교의 Top6 구간은0을 포함했다.

근처 minimum52,penalty2,shrinkage104를 한 좌표씩 바꾼 세 설정도 모두.794203이었다. 임의의 한 설정에만 의존하지 않았지만 CP가 없어 같은 frequency로 축소된 결과이므로 regime 검출의 robustness로 부르지 않는다. 이후 성능으로 재선택하지 않았다.

|frozen reference(cadence26)|mean Spearman|Top6 overlap|Top10 overlap|Top15 overlap|
|---|---:|---:|---:|---:|
|Gap Logistic|−.436868|.023188|.269565|1.620290|
|Phase14 Graph|−.010114|.692754|1.994203|4.901449|
|Phase15 GapShape|.099748|1.037681|2.718841|5.588406|
|Phase18 Mirror|.019861|.933333|2.455072|5.234783|

이전 model은 manifest hash를 확인한 기존CSV를 읽었으며 재fit/재선택하지 않았다. Gap과의 음의 상관은 rank diversity이며 단독 예측 가치의 증명은 아니다.

**RegimeFrequencyModel: NOT CURRENTLY JUSTIFIED.** 개발에서 fixed-frequency에 못 미쳤고 corrected structural evidence가 없으며 이후에도 adaptive CP가 없어 primary metric의 안정적인 개선을 확인하지 못했다. H17 final ensemble은 만들지 않았다.

## 검증·prospective·변경 파일

Full pytest: **919 passed,1 skipped,0 failed**. 신규 Phase19 tests는140개다. 유일한 skip은 기존 optional LightGBM/XGBoost 미설치에 따른 `tests/test_predictive_models.py:52`이다. segment cost,exact DP/minimum/penalty,planted/no-change,causal representations,CUSUM constants,complete-search parity,model leakage,cutoff,development-only freeze,rank correlation,1246금지,archive guard를 포함한다.

독립 리뷰에서 발견한 calibration 재실행 시 인증 부족을 수정하고 두 cutoff의32pilot와 seed를 확인하는 회귀 테스트를 추가했다. 별도 구현의 audit는 project implementation을 import하지 않고 pilot평균/std/mask→own maxima→p값,모든 예측metric,bootstrap구간,rank diversity,전체345target의 rawsegmentrate,901/950/1000/1100/1245의 direct-slice DP를 재계산해 모두 일치함을 확인했다. Source/CSV/이전 Phase18 전용14files/frozen references의 hash도 일치했다.

요청한10plots를 `reports/change_point/plots/`에 저장했다. timeline,번호예시,block heatmap,shape예시,경계집중도,prefix stability,IID/fixed maxima,current-segment rate,역사적 ranking예시이다. Plot은 증거를 살펴보는 보조 수단이며 p-value를 대신하지 않는다.

**draw1247_phase19_changepoint: NOT CREATED — NO JUSTIFIED PREDICTIVE MODEL.** 실험용 historical 모델은 남기되 의미 없는 prospective infrastructure는 만들지 않았다. 이전 `reports/prospective` archive는 여전히 없으며 발행·복원·새snapshot 작성을 실행하지 않았다.

`PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION`

변경 파일은 아래 **22개**다. Local 연구 출력은 gitignore 대상이며 이 목록과 별도로 manifest에 hash를 저장한다.

```text
.gitignore
README.md
docs/README.md
docs/research-ideas.md
docs/change-point-analysis.md
docs/change-point-results.md
docs/superpowers/plans/2026-10-18-phase19.md
src/cli.py
src/change_point_cli.py
src/analysis/change_point.py
src/analysis/change_point_representation.py
src/analysis/change_point_search.py
src/analysis/change_point_diagnostics.py
src/backtest/change_point.py
src/models/change_point.py
tests/test_change_point.py
tests/test_change_point_representation.py
tests/test_change_point_search.py
tests/test_change_point_diagnostics.py
tests/test_change_point_backtest.py
tests/test_change_point_models.py
tests/test_change_point_cli.py
```

실제1246 fetch/import/use 없음,prospective publication 없음,commit/push 없음. H1–H17 번호를 보존하고 H18을 추가했다. H17은 BACKLOG,H19–H25는 docs상 backlog 이름만 있으며 미구현이다. Phase19에서 종료한다.
