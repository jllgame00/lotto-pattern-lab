# Phase20 결과 — H19 Point process / Hawkes-like influence / renewal

**H19: TESTED / INCONCLUSIVE.** 보정된 event structure와 causal predictive improvement를 확인하지 못했다. 구현한 Hawkes-like cross 추가는 이후 self-only보다 logloss가 나빴다. 이는 모든 가능한 point-process 설명을 배제하는 결론이 아니며,사전 제한한 분석과 실험용 모델의 결과이다.

## 범위와 시작 검증

Git root: `C:/Users/Samsung/OneDrive/Desktop/university/personal/lotto-pattern-lab`.
시작은 clean `main`,SHA `35f97c295832ee8da92ddcdcff6479ec706910d2`이다. README,문서 색인,연구 가설 노트,canonical CSV와 Phase19 완료 상태를 확인했으며 기존22files hash가 모두 일치했다. 관련 없는 기존 수정은 없었다.

Main numbers draws1–1245만 사용했다. Bonus·실제1246은 설계/선택/검증/평가에서 제외했고 외부 fetch/import를 하지 않았다. CSV SHA-256은 `3b7bb1e0a37c28ae4b4a97e098180d8407008ec007698c191ed6cf279db8225b`이다. 여섯 활성 번호가 있는45binary event vector이므로 번호별 likelihood는 pseudo-likelihood이다.

[방법](point-process-analysis.md) · [계획](superpowers/plans/2026-10-18-phase20.md) · [local manifest](../reports/point_process/run_manifest.json) · [독립 감사](../reports/point_process/audit_result.json)

## 정확한 검색 범위

Lag는 **{1,2,3,4,8,13,26}**,self45개와 ordered cross1980개로 총2025relations×7lag=14175 관계를 계산했다. Renewal은 clipped27/coarse6/relative5states이다. 첫 own event 이전을 left-censored로 제외하고 gap0과 interarrival1을 구분했다. Relative mean은 완료된 prior interarrival에서만 계산했다. Structural shrinkage26,minsource support30,minrenewal support20을 고정했다.

|family|cell 수|
|---|---:|
|renewal hazard deviation|1710|
|self excitation|315|
|self inhibition|315|
|cross excitation|13860|
|cross inhibition|13860|
|kernel exp2/exp8/finite|6075|
|전체|**36135**|

Pilot mask eligible은 full35559/development35435개,실제자료의 support도 만족한 cell은35549/35427개였다. 이 수는 지원되지 않은 후보를 제거한 값이며 선언된 전체 검색 수와 다르다. 예측 grid는 Renewal6+Hawkes24+Signed24=54개로 따로 기록한다.

Benchmark의 full/development 검색 한 쌍은 IID.20/.075초,fixed-margin1.07/1.18초였다. 목표를 축소하지 않고 **199IID+199fixed-margin**을 각 cutoff에 실행했다. Main runtime173.31초. Full1245와 development900의 fixed margins를 각각 별도 생성하고 모든 event/gap/표현/pair/lag/kernel을 surrogate 자신에게서 재구성했다.

## 가장 강한 실제 event 관계

다음은 독립 pilot로 표준화한 각 family global-max가 고른 관계이다. 한 번호/한 pair만 정해 검정한 local p가 아니다.

|family leader|support/hits|baseline|raw rate|shrunk conditional|effect|
|---|---|---:|---:|---:|---:|
|Renewal40번 clipped gap12|29/9|.138999|.310345|.229345|+.090346|
|Self14→14,lag8|172/38|.137380|.220930|.209959|+.072579|
|Self5→5,lag8|153/7|.124601|.045752|.057205|−.067396|
|Cross26→22,lag2|165/36|.117647|.218182|.204496|+.086849|
|Cross16→10,lag3|170/10|.130469|.058824|.068328|−.062142|

Self excitation/inhibition의 lift는1.5283/.4591,log-odds 차이는+.5120/−.8526이다. Cross excitation/inhibition의 lift는1.7382/.5237,log-odds 차이는+.6565/−.7159이다. Number40의 높은 hazard는 support29의 선택된 sparse state이며 전체 null p=.94이다. Raw lift만으로 Hawkes behavior를 주장하지 않는다.

Pooled clipped gap0/1/2의 raw hazard는.13773/.14028/.12726으로 IID6/45=.13333 주변에서 변했다. 기존 GapHazard와 같은 self-history 정보를 다시 표현한 부분이 크다. 기존 GapHazard는8bin pooled table·prior75였고,새 Renewal은 번호별 baseline과27/6/5state shrinkage를 썼다. 직접 재사용할 frozen GapHazard historical prediction CSV가 없어 그 모델의 수치 비교는 수행하지 않았다. 이전 seal을 바꾸지 않았다.

가장 강한 kernel은 **13→7,exp8**,raw score5.461529,amplitude−.033824였다. Lag1/2/3/4/8/13/26 effect는−.072779,+.013559,−.015245,−.034479,−.018215,+.001514,−.014760이었다. 매끄러운 감쇠를 직접 확인한 결과가 아니라 사전 exponential basis에 투영한 값이다. Standardized cell z18.4899를 Gaussian tail p로 해석하지 않는다.

## Complete-search null 결과

Cutoff별 독립 IID pilot32(seed201001)로 평균/std와 finite mask를 고정했다. Main seed200042,각 null199개이다. Empirical p=(1+exceedances)/200,six-family Bonferroni를 적용했다.

|family|real maximum z|IID global p|fixed global p|IID corrected p|fixed corrected p|
|---|---:|---:|---:|---:|---:|
|renewal|4.293767|.940|.940|1|1|
|self excitation|5.094891|.585|.630|1|1|
|self inhibition|6.138537|.125|.095|.750|.570|
|cross excitation|7.869975|.915|.940|1|1|
|cross inhibition|9.508795|.200|.235|1|1|
|kernel structure|18.489913|.105|.120|.630|.720|

Development의 가장 작은 corrected p도 cross inhibition의 fixed.45였다(IID.84). 그 밖은 모두1이었다. **어느 event influence도 correction을 통과하지 않았다.** 32pilot의 cell scale은 noisy하며 독립 보정 도구일 뿐이고,main null의 global maximum 비교가 검정의 기준이다.

## 시간 안정성과 Graph 연결

Full leader의 source/target/lag를 고정하고 early1–415,middle416–830,recent831–1245에서 계산했다. 다음의 strongest lag는 같은 pair에 대해 각 era에서 찾은 기술적 요약으로,독립 confirmation이나 predictive parameter 재선택이 아니다.

|고정 관계|early effect|middle effect|recent effect|각 era의 strongest lag|
|---|---:|---:|---:|---|
|14→14 lag8|+.087901|+.022614|+.057334|8/4/8|
|5→5 lag8|−.072760|−.071767|−.008049|8/8/26|
|26→22 lag2|+.099299|+.055238|+.042200|2/13/1|
|16→10 lag3|−.051025|−.059454|−.033805|3/3/3|

26→22는 시기별 best lag가 달랐고5번의 inhibition은 최근 약해졌다. 16→10은lag3 방향이 유지됐지만 corrected null evidence가 없었다. Rolling416/stride52 분석과 지원 수는 `relation_time.csv`에 보존했다. Minimum source support30 미달은 근거로 해석하지 않았다.

Primary influence matrix의 pair별 lag와 effect는 **개발900회**에서 고정했다. Full effect를 표시할 때도 같은 lag만 썼다. Full-history max-absolute-lag matrix는 기술적 탐색 출력으로 별도 분리하고 예측에 쓰지 않았다.

기존 Phase14 `structural_cache.npz`의 hash를 검증하고 사전 W26 마지막 저장 matrix를 읽었다. Graph fit/재선택은 하지 않았다. 양방향 평균 absolute influence와 same-draw edge의 Spearman=.061648,top45 edge overlap2/45였다. Positive/inhibitory summary의 상관은−.022993/.048064,overlap2/45·1/45였다. Incoming influence와 graph node strength의 상관은 absolute.007963,positive.143935,negative−.182938이다. 서로 다른 기간·요약 방식의 기술 비교이며 유의한 새 정보나 독립 검정을 뜻하지 않는다.

## 개발에서 선택·동결한 설정

개발 target401–900,outer cadence26에서54configs×500targets=**27000rows**를 평가했다. Selection metric은 평균 per-number logloss 최소,동률은 선언 순서이다. Outer fit에서만 edges/scalers/baseline/coefficients를 적합하고 target<T에서 current source state를 갱신했다.

|모델|개발 선택|개발 logloss|개발 Top6|nested self-only logloss|
|---|---|---:|---:|---:|
|Renewal|clipped gap,alpha104|.394354|.754|해당없음|
|Hawkes excitation-only|exp8,incoming3,alpha104,ridge10|.393589|.820|.393483|
|Signed screening candidate|exp8,incoming3,alpha104,ridge10|.393438|.784|.393497|

Hawkes의 source 추가 logloss는 개발 전반.393667 vs self.393488,후반.393510 vs self.393479로 모두 나빴다. `development_positive=false`이며 이후 결과는 explicit experimental falsification 비교이다.

Signed는 후반 logloss가 positive 및 자체 self-only보다 나빴고 Top6도 positive보다 낮았다. `signed_allowed=false`로 동결했으므로 **Signed의 이후 walk-forward를 실행하지 않았다.** 개발 screening용 class/config는 보존하지만 실제 예측 모델로 승격하지 않았다.

선택 SHA-256: `78c84105ebbd688e0edbbc7a401d6fb5e20cf5ceecbd33db10b7e6495d309cd7`. 이후 데이터로 설정·edge 수·shrinkage·ridge·kernel을 다시 고르지 않았다.

## 이후901–1245 walk-forward

Cadence26의345targets 결과이다. 낮은 mean winning rank가 좋다. Gap은 기존 manifest로 검증된 frozen output을 읽었다.

|모델|avg Top6|Recall@6|Recall@10|Recall@15|mean winning rank|per-number logloss|
|---|---:|---:|---:|---:|---:|---:|
|Random|.768116|.128019|.219807|.336715|22.958454|.392674|
|Frequency26|.773913|.128986|.207246|.314493|23.336232|.466310|
|Gap Logistic|.834783|.139130|.216908|.330918|23.034300|미보고|
|Renewal|.753623|.125604|.212077|.321256|23.191787|.394223|
|HawkesInfluence|.707246|.117874|.210145|.316908|23.491304|.393644|

Random의 likelihood reference는 ranking 난수가 아닌 일정한6/45 확률이다. Gap rank score는 검증된 확률 출력이 아니므로 logloss를 계산하지 않았다. Frequency26에는 zero empirical rate가 있어 logloss 계산 시1e−9 clipping을 적용했으며,smoothed 모델 대비 큰 loss를 그대로 예측 우위의 근거로 삼지 않는다. 주요 source 검정은 동일 설정의 smoothed self-only와 비교한다.

Renewal의0–6 hit distribution은 **151/138/46/10/0/0/0**,Hawkes는 **162/131/43/9/0/0/0**이었다. Top8/10/12/15 >=5 events는 Renewal **0/0/2/5**,Hawkes **0/0/1/4**회다. All-six pool event는 Hawkes Top15에서1회,그 밖의 신규 모델/pool에서는0회였다. 희귀 pool event 하나를 전체 순위 성능의 개선으로 해석하지 않는다. Baseline을 포함한 전체 분포는 `walk_forward_*/summary.csv`에 있다.

|Top6 paired difference(block26)|point|95% interval|
|---|---:|---|
|Renewal−Random|−.014493|[−.121739,.104348]|
|Renewal−Gap|−.081159|[−.182609,.031884]|
|Hawkes−Random|−.060870|[−.150797,.040580]|
|Hawkes−Gap|−.127536|[−.226087,−.023188]|
|Hawkes−Renewal|−.046377|[−.153623,.052246]|

2000회 paired circular block bootstrap이다. Block52의 Hawkes−Gap interval도[−.211594,−.037681]로 불리했다. 다른 비교가0을 포함한다는 사실은 동등성이나 우위의 증명이 아니다.

## 핵심 진단 — source를 추가하면 uncertainty가 줄었는가?

같은 own kernel/offset/ridge로 **별도 적합한 nested self-only** logloss는.393312,Hawkes cross-added는.393644였다. Difference(full−self)=**+.000332**로 오히려 나빴다.

|구간/cadence|full−self logloss|95% paired interval|
|---|---:|---|
|901–1245,cadence26,block26|+.000332|[+.000087,+.000586]|
|901–1245,cadence26,block52|+.000332|[+.000054,+.000601]|
|901–1245,cadence13,block13|+.000362|[+.000139,+.000585]|
|1001–1245,cadence26,block26|+.000136|[−.000125,+.000404]|
|1101–1245,cadence26,block26|+.000005|[−.000346,+.000374]|

현재 구현과 설정에서는 **cross-number events가 own history를 넘어 예측 정보를 준다는 근거가 없다.** 전체 이후 구간에서는 source 추가의 손해가 관측됐고 더 최근 start에서도 개선을 확인하지 못했다. 이 결론은 Phase13 TE의 표현을 그대로 재사용한 것이 아니라 명시적 event convolution과 pooled logistic의 nested 비교에서 나온 결과이다.

## Robustness / rank diversity / 후보 판정

Cadence13에서 Renewal Top6=.762319,Hawkes=.713043,Random=.768116,Gap=.831884였다. Start901/1001/1101의 Top6는 Renewal .753623/.787755/.731034,Hawkes .707246/.730612/.751724였다. 이후345targets를115개씩 나눈 early/middle/recent는 Renewal .634783/.930435/.695652,Hawkes .678261/.730435/.713043이었다. Renewal의 양의 구간은 middle에 집중됐고 전체적 우위로 유지되지 않았다.

아래는 cadence26의 평균 Spearman과 평균 overlap count이다. 모든 이전 model은 hash-verified historical CSV만 읽었으며 새 fit/재선택을 하지 않았다.

|신규 model / frozen reference|Spearman|Top6 overlap|Top10 overlap|Top15 overlap|
|---|---:|---:|---:|---:|
|Renewal / Gap|−.200153|.495652|1.515942|3.695652|
|Renewal / Graph|.037052|.895652|2.466667|5.298551|
|Renewal / GapShape|.060075|1.011594|2.544928|5.353623|
|Renewal / Mirror|−.003898|.811594|2.344928|5.043478|
|Hawkes / Gap|−.383480|.223188|.779710|2.344928|
|Hawkes / Graph|−.023702|.707246|2.052174|4.736232|
|Hawkes / GapShape|.084094|.921739|2.524638|5.481159|
|Hawkes / Mirror|.017166|.826087|2.315942|5.118841|

Cadence13의 Gap 상관은 Renewal−.195418,Hawkes−.380519로 비슷했다. 낮은 상관은 diversity일 뿐 성능이 부족한 모델을 승격하는 근거가 아니다.

- **RenewalModel: NOT CURRENTLY JUSTIFIED.** 기존 gap 정보의 재해석이며 이후 개선과 temporal robustness가 없었다.
- **HawkesInfluenceModel: NOT CURRENTLY JUSTIFIED.** corrected event evidence가 없고,개발 및 이후 source-added logloss가 불리했으며 Top6도 낮았다.
- **SignedInfluenceModel: 이후 평가 제외.** 개발 gate 실패,prospective/ensemble 후보가 아니다.

H19는 TESTED / INCONCLUSIVE이며 PROMISING 기준을 만족하지 않는다. H17 final ensemble은 만들지 않았다.

## 검증·prospective·변경 파일

전체 테스트는 **1012 passed,1 skipped,0 failed**,신규 Phase20 tests는93개다. 유일한 skip은 기존 optional LightGBM/XGBoost 미설치(`tests/test_predictive_models.py:52`)이다. 실행 명령과 결과는 `reports/point_process/test_result.json`,JUnit 및pytest.log에 기록했다. Phase19 전용17개 파일과 이전 frozen reference를 별도로 보호한다.

리뷰와 독립 감사에서 발견한 미지원 lag 선택,합계 likelihood의 line-search 정밀도,보조 Frequency26 paired logloss의 DataFrame index 정렬을 회귀 테스트로 보강했다. 마지막 문제는 저장 예측/설정 hash를 유지한 채 target-aligned 배열로 paired 표만 재계산했다. Null 통계나 scientific parameter grid는 바뀌지 않았다.

독립 audit는 project implementation을 import하지 않았다. 실제36135raw통계와 event/gap/relative/lagcount를 재구성하고 pilot mask→모든 저장 null own maxima→p값,모든 이후 ranking/logloss/paired bootstrap/diversity를 재계산해 일치를 확인했다. 별도 optimizer로901/950/1000/1100/1245의 활성 모델을 cadence별로 재구성한20개 사례도 통과했다. 원래 null histories 전체나 모든 target의 모델을 독립 재생성했다는 뜻은 아니다. 그 밖 target은 저장 확률/상태/cutoff의 arithmetic 및 frozen-state audit이다. 보호한 Phase19 전용17files와 이전 frozen reference도 hash가 일치했다.

`reports/point_process/plots/`에는 hazard2개,self lag profile,positive/inhibitory matrices,strongest pair lag/time profiles,IID/fixed global maxima,Hawkes 역사적 ranking의10plots가 있다. Inspection aid이며 검정을 대신하지 않는다.

**draw1247_phase20_pointprocess: NOT CREATED — NO JUSTIFIED PREDICTIVE MODEL.** 과거 archive는 여전히 부재이며 prospective 복원·발행·새 snapshot 생성은 수행하지 않았다.

`PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION`

변경 파일은 아래 **20개**다. Local 연구 출력은 별도로 gitignore 처리하고 manifest에 hash를 기록한다.

```text
.gitignore
README.md
docs/README.md
docs/research-ideas.md
docs/point-process-analysis.md
docs/point-process-results.md
docs/superpowers/plans/2026-10-18-phase20.md
src/cli.py
src/point_process_cli.py
src/analysis/point_process.py
src/analysis/point_process_search.py
src/analysis/point_process_diagnostics.py
src/models/point_process.py
src/backtest/point_process.py
tests/test_point_process.py
tests/test_point_process_search.py
tests/test_point_process_models.py
tests/test_point_process_backtest.py
tests/test_point_process_cli.py
tests/test_point_process_diagnostics.py
```

실제1246 fetch/import/use 없음,prospective publication 없음,commit/push 없음. H1–H18 번호를 보존하고 H19만 추가했으며 H20–H25/H17은 미구현이다. Phase20에서 종료한다.
