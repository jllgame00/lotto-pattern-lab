# Phase 4 — Hazard·Bayesian·HMM·고정 ensemble 연구

## 목적과 연구 가설

서로 다른 통계 가정을 비교하며 시각적 패턴을 수익성 주장으로 바꾸지 않습니다. 기존 gap/prize default는 유지합니다. H2는 TESTED / INCONCLUSIVE이며 최종 H17 validated ensemble은 아직 BACKLOG입니다.

## CLI

```powershell
python main.py hazard-analysis
python main.py compare-regime-models
python -m pytest -q
```

출력은 `reports/regime_research/`, selected-number plot은 `plots/`이며 Git-ignored입니다. fixed retrospective loader는 실제1245 전에서 멈추고 새 결과를 가져오지 않습니다. canonical은1245까지이나 앞선 Phase 3 접근 때문에 pristine final holdout이라고 부르지 않습니다.

## 데이터·검증 범위와 Leakage 방지

primary601-1244, cadence 26입니다. 모든 모델은 target 105부터 같은 causal feature/label을 사용하고 fit은 target 전에 끝납니다. 1244까지51,300 rows입니다. current feature는 매 draw 갱신합니다. HMM parameter는 refit 사이 고정하고 forward state는 last completed draw만 관측하며 Bayesian count도 causally 갱신합니다. repeated scoring은 idempotent이고 skip/backward online target은 거부합니다.

ensemble weight 선택은601-900, frozen 평가901-1244입니다. latter는 이번 weight selection에서만 제외했으며 앞선 연구가 이미 사용해 pristine holdout은 없습니다. robustness는 start501/701 cadence 26,601 cadence 13이며 중첩되어 독립 반복이 아닙니다. latest draw·later 결과를 높이기 위한 설정 선택은 없었습니다.

### 핵심 정의 — Gap hazard

exact gap은 완료된 연속 absent draws로 마지막 출현이면 zero입니다. 고정 bucket은 `[1,3,5,8,13,20,30]`, relative `[.25,.5,1,1.5,2,3,4]`, standardized `(current_gap+1-mean_gap)/gap_std`의 경계는 `[-1,-.5,0,.5,1,2,3]`입니다. zero/undefined std는 unsupported입니다. 전체·세 era의 observations·successes·probability·6/45 deviation·Jeffreys95% marginal interval·adequacy200 rows flag를 보고하고 exact rare gap도 남깁니다. 회차 안 번호 row는 의존하므로 marginal interval은 보정 전 기술값입니다.

GapHazardModel은 고정 current-gap bucket에서 pooling하고 training label의 `(successes+75*6/45)/(observations+75)`를 씁니다. empty bin은 fair prior이며 absence 증가가 hazard를 높인다고 가정하지 않습니다. ratio/zscore bin은 지원하지만 default 실험은 best bin을 탐색하지 않습니다.

### Bayesian 경향

번호별 Beta(2,13) prior, static `alpha=2+successes`, `beta=13+failures`의 posterior mean입니다. recency는 `2**(-age/52)`로 discount 후 같은 prior를 더합니다. fractional-count Beta interval은 모델 설명이며 Lotto bias의 calibrated interval이 아닙니다. 45 marginal model은 joint six-without-replacement를 모델링하지 않습니다. empirical-Bayes·cross-number prior tuning은 없습니다.

### Bernoulli HMM

적절한 HMM 의존성이 없어 작은 NumPy 구현으로45 independent2-state/3-state Bernoulli를 batch합니다. supervised 최근260(최소104) observations이며 일반 HMM library가 아닙니다. scaled forward/backward EM, deterministic initializations 두 개, 최대40 iterations, tolerance1e-5, initial uniform입니다. transition pseudocount는 diagonal8·off1, emission2/13입니다. penalized likelihood 관점에서 Dirichlet=pseudocount+1·Beta(3,14) emission prior와 같으며 Bayesian Beta(2,13) posterior mean과 같은 추정이 아닙니다.

번호별 best penalized objective를 고르고 probability는[1e-6,1-1e-6]로 clip합니다. emission 순으로 cold/hot 또는 cold/neutral/hot label을 붙이지만 검증된 real regime을 뜻하지 않습니다. transition·emission·state probability·likelihood·convergence·iteration·initialization sensitivity를 export합니다. prediction/plot은 past-fitted parameter의 forward filtering이며 retrospective smoothing·full-history parameter를 쓰지 않습니다.

번호7/17/34의 최종260 open labeled observations를 count-preserving shuffle해 emission spread·mean diagonal transition·constant Bernoulli 대비 log-likelihood를 비교합니다. number/config별39 shuffles,18 diagnostics에 Bonferroni입니다. raw minimum .025라 강한 corrected evidence를 낼 수 없는 저비용 artificial-structure 진단입니다. causal hot/cold와 frequency·gap·periodicity·strong-regime의 Spearman은 탐색 요약이며 correlation p·causal 해석을 부여하지 않습니다.

### Ensemble 계산과 평가

rank normalization은 tie-average rank를0-1로, score normalization은 target min/max를0-1로 바꿉니다. constant는 .5이며 이미 출력한45 scores만 사용합니다. ranking utility이지 calibrated probability가 아닙니다.

각 normalization에서 Gap+Bayesian·Gap+HMM·Bayesian+HMM·세 가지·all·periodicity 제외·Similarity 제외의 equal weight를 비교합니다. 작은 development search는 equal 대 한 component만 두 배이며 development Top6만 선택하고 tie는 첫 설정입니다. later outcome 전에 weight를 동결합니다. All은 prespecified components이며 validated signals 전체라는 뜻이 아닙니다.

이전 ranking·pool·portfolio 구현을 재사용합니다. Top6/8/10/12/15의 전체 분포·exact hypergeometric·simulation·rare interval·multiple correction을 저장합니다. later는 Top12·unique1/5/10/20·weighted/five-subset coverage·세 seed·RandomTop12/Uniform45 동일 예산입니다. bonus는 ticket 후에만 읽습니다. paired interval은2000 circular26-draw block bootstrap이며 많은 실험의 unadjusted 기술값입니다. 개별 prize event는 우위의 증거가 아닙니다.

## Prospective capability — 당시 protocol

```powershell
python main.py freeze-next
```

별도 offline 명령으로 local header와1245 canonical rows까지만 읽고 다음 row·network는 읽지 않습니다. 당시 full data의 target은1246이었지만 이 Phase에서는 실제로 호출하지 않았고 실제1246 prediction을 만들지 않았습니다. synthetic test만 수행했습니다. 현재1246은 알려진 결과이며 새 prospective 대상이 아닙니다.

호출마다 `reports/prospective/`의 timestamp/UUID JSON을 exclusive 생성합니다. bounded-source byte hash·latest draw/date·next target·UTC·Git SHA/dirty·implementation hash·versions·config/seed·45 scores·Top6/10/12/15·20-ticket weighted/coverage와 smaller-budget prefix를 남깁니다. overwrite하지 않습니다. local file은 trusted timestamp나 outcome unknown의 cryptographic proof가 아닙니다.

fixed snapshot은 static/recency Bayesian·HMM2/3·Frequency52이며 별도 versioned policy입니다. 이 연구 winner·Logistic·ensemble을 자동 선택하지 않습니다. snapshot Bayesian은 draw 1부터, retrospective는105부터라 같은 policy라고 주장하지 않습니다. freeze 시 unseen임을 독립 확인한 target만 진정한 prospective로 볼 수 있고 결과는 별도로 가져와야 합니다. 이 명령은 결과를 가져오지 않습니다.

## 주요 결과

신뢰할 예측 우위는 확립되지 않았습니다. 601-1244의644 targets이며 seeded Random 대비 차이와95% paired26-draw block bootstrap interval입니다.

| Model | Average Top6 hits | Difference vs Random [95% interval] | Mean winner rank |
|---|---:|---:|---:|
| RandomModel | .7981 | reference |22.9332|
| Gap Logistic | .8494 |+.0512 [-.0357,.1398]|22.7549|
| GapHazard | .7811 |-.0171 [-.1165,.0808]|23.1910|
| Bayesian static | .7733 |-.0248 [-.1149,.0683]|23.2156|
| Bayesian recency | .7640 |-.0342 [-.1320,.0621]|23.1284|
| HMM2 | .7873 |-.0109 [-.0947,.0714]|22.9589|
| HMM3 | .7873 |-.0109 [-.0978,.0761]|22.9568|
| Frequency52 | .7842 |-.0140 [-.1134,.0807]|23.1294|
| Similarity | .7780 |-.0202 [-.1102,.0715]|23.3103|

uniform expectation은 .8 hit·mean rank23입니다. 모든 interval이 zero를 포함합니다. 다른 ordered model list의 공통 stream 때문에 이전 gap report와 bootstrap endpoint가 다를 수 있으며 기존 결과는 바뀌지 않았습니다.

### Null / surrogate와 hazard·regime 진단

| Current gap | Observations | Appearance rate | Marginal95% interval |
|---|---:|---:|---:|
|0|6840|.13670|[.12871,.14499]|
|1-2|10990|.13285|[.12660,.13929]|
|3-4|8330|.13121|[.12409,.13859]|
|5-7|8763|.13477|[.12774,.14204]|
|8-12|8327|.13414|[.12695,.14159]|
|13-19|4970|.13400|[.12475,.14369]|
|20-29|2286|.12555|[.11244,.13960]|
|30+|794|.12720|[.10540,.15173]|

모든 broad-bin interval은6/45를 포함하며 단조 overdue 증가가 없습니다. exact/relative/z-score/era는 `hazard.csv`입니다. smoothed model의 out-of-sample 결과가 이전 gap Logistic uplift에 robust한 근거를 주지 못했고 sampling variation이 가능합니다.

HMM2/3 median emission spread는 .00312/.00116로 많은 fit이 한 Bernoulli rate에 가깝습니다. mean .02584/.01547이며 일부 큰 분리도 있습니다. convergence99.82%/99.91%, 예외는 flag로 남깁니다. initialization spread range 평균 .000758/.002218입니다. transition prior가 persistence를 유도하므로 persistent estimate만으로 증거가 되지 않습니다.

18 selected-number null 모두 corrected p=1.0(raw minimum .225)입니다. 이 저비용 진단에서 count-preserving null보다 특이한 fitted state는 없었습니다. 45번호의 median hot-state Spearman은 다음과 같습니다.

| Feature | HMM2 | HMM3 |
|---|---:|---:|
|52-draw frequency|.267|.236|
|Current gap|-.447|-.437|
|Periodicity score|-.014|-.008|
|Causal strong-periodicity flag|-.036|-.024|

이 기술적 연관은 state가 주로 recent appearance를 따르고 periodicity regime과 넓은 대응은 약함을 시사합니다. 7/17/34 plot과 per-number 관계를 export했습니다.

### Later-period ensemble·ablation

frozen 선택은 Gap Logistic weight .2, 나머지 여덟 개 각각 .1입니다. development hit .8433,901-1244의344 targets에서 .7849, Random .7674(theory .8), paired 차이+.0174[-.0843,.1193]입니다.

| Later model | Avg hits | Mean winner rank | Recall6 | Recall10 | Recall15 |
|---|---:|---:|---:|---:|---:|
|RandomModel|.7674|22.9627|.1279|.2200|.3372|
|Gap Logistic|.8285|23.0252|.1381|.2195|.3290|
|GapHazard|.7151|23.4952|.1192|.2093|.3169|
|Bayesian static|.8314|23.3086|.1386|.2204|.3256|
|Bayesian recency|.7471|23.3983|.1245|.2093|.3188|
|HMM2|.7645|22.9976|.1274|.2224|.3295|
|HMM3|.7674|22.9850|.1279|.2209|.3314|
|Development-weight ensemble|.7849|23.2902|.1308|.2122|.3203|

later 모든 hit interval은 zero를 포함합니다. equal-rank all은 .7297, periodicity 제외 .7558, Similarity 제외 .7471입니다. normalized-score all .7936에서는 제외 시 .7616/.7645로 내려갑니다. component 이득은 조합에 의존해 robust하지 않습니다. full15 ablations·histogram·era를 저장하며 입증된 개선으로 채택하지 않습니다.

### 시간·시작점 robustness

| Model |501-1244, cadence26|601-1244, cadence26|701-1244, cadence26|601-1244, cadence13|
|---|---:|---:|---:|---:|
|RandomModel|.8051|.7981|.7757|.7981|
|Gap Logistic|.8320|.8494|.8456|.8525|
|GapHazard|.7984|.7811|.7923|.7748|
|Bayesian static|.7876|.7733|.7739|.7733|
|Bayesian recency|.7661|.7640|.7629|.7640|
|HMM2|.7769|.7873|.7721|.7609|
|HMM3|.7688|.7873|.7555|.7748|

해당 paired hit interval 모두 zero를 포함합니다. Bayesian은 causal count update가 refit과 같아 같은 start에서 cadence-invariant입니다. HMM은 start/cadence별 일관된 개선이 없습니다. primary early/middle/recent는 HMM2 .786/.870/.706, HMM3 .781/.842/.738, Random .856/.772/.766입니다. middle 이득이 다른 block에서 뒤집힙니다. individual models·Gap Logistic에 추가 fit을 했으며 ensemble의 추가 adaptive weight/cadence search를 정당화할 근거는 없었습니다. later ensemble time block도 별도입니다.

### Candidate-pool / prize-aware 결과

later에서 pool이 본번호 다섯 개 이상 포함한 draw 수입니다.

| Model |Top8|Top10|Top12|Top15|
|---|---:|---:|---:|---:|
|RandomModel|0|0|0|0|
|Gap Logistic|0|1|1|3|
|GapHazard|0|1|1|2|
|Bayesian static|0|0|1|6|
|Bayesian recency|0|0|0|3|
|HMM2|0|0|2|5|
|HMM3|0|0|0|6|
|Development-weight ensemble|0|0|0|4|
|Exact random expected count,344 draws|.089|.381|1.143|4.016|

이 모델들은 all-six zero입니다. 전체 policy 중 유일한 all-six는 기존 mean-reversion Top15입니다. corrected later pool p는 모두1.0입니다. seeded Random의 zero event로 positive exact expectation을 대체하지 않습니다. full0-6·3+/4+·interval·모든 pool size를 저장했습니다.

세 seed 평균 later mean best match, weighted Top12 portfolio입니다.

| Policy |1 ticket|5 tickets|10 tickets|20 tickets|
|---|---:|---:|---:|---:|
|Development-weight ensemble|.7490|1.3120|1.4360|1.4952|
|RandomModel Top12|.8072|1.3624|1.4884|1.5746|
|Uniform45 unrestricted|.8333|1.7665|2.1095|2.4099|

20 tickets에서 ensemble coverage1.5078 대 matched Random1.5862입니다. paired mean-best는 weighted -.0795[-.1996,.0475], coverage -.0785[-.2016,.0485]입니다. pool restriction은 broad coverage를 낮추므로 unrestricted Random이 필요합니다. 새 model의 prize-aware 개선은 확립되지 않았습니다. recency-Bayesian 일부 unadjusted interval 악화는 corrected inferiority 주장이 아닌 진단입니다.

30 policies·두 방법·세 seed·Uniform45에서 maximum-budget1,259,040 instances이며 작은 budget은 prefix입니다. rare27 occurrences는9 draws의15 distinct pairs로 **first0·second1·third14 equivalents**입니다. second ticket[10,12,18,39,42,43]은 draw 942·bonus39로 Bayesian+HMM 세 variant에 반복된 한 사건입니다. independent successes 세 개가 아닙니다. frozen ensemble·individual Bayesian/HMM에는 five-main ticket이 없고 GapHazard는1123에서 third-equivalent였습니다. zero-event의 nonzero uncertainty와 개별 prize는 `portfolio_replicates.csv`에 있습니다.

## 검증·의존성·한계

당시 전체 **136 passed,2 skipped**,21.67s이며 기존114개 포함입니다. skip은 optional tree입니다. 독립 review는 blocking causal/math defect를 찾지 않았고 한 HMM EM update를 exhaustive path로2.78e-17 이내 재현했습니다. missing-Git 경우 regression을 추가해 unknown을 false clean 대신 JSON null로 저장합니다. synthetic snapshot test는 network를 금지합니다.

전체291.34s에 null·portfolio·robustness가 포함됩니다. primary HMM2/HMM3는 각각644 targets에8.62/8.81s입니다. 최종 CSV는 saved result로 조립하고 refit·prediction 변경은 없었습니다.

당시 artifact 검증은 individual9660·later 10320 ranking records, pool99900·budget251808·filtered-state57960 rows·rare27를 bounded dataset에서 재구성했습니다. cutoff·target·nested budget·state normalization·prize·prefix hash가 일치했습니다.

당시 `hmmlearn`·scikit-learn·LightGBM·XGBoost는 없었습니다. `PIP_NO_INDEX=1`과 proxy127.0.0.1:9로 당시 허가된 Git push도 connection refused였습니다. network 우회·설치 반복·tree replacement·미래 결과 요청은 없었습니다.

당시 checkpoint는 commit `5b66beed885de7ee4d240e06100e474c03609497`, message `feat: add prize-aware validation and gap signal audit`였습니다. Phase 4 전114 passed,2 skipped로 재확인했습니다. push는 proxy에서 실패해 remote auth를 확인하지 못했습니다. 당시 duplicate checkpoint·history rewrite·second commit·Phase 4 push는 없었습니다. 이는 과거 이력이며 이번 문서 작업의 commit/push가 아닙니다.

## 해석과 다음 단계

HMM state label·local 진단·가상 당첨을 예측력과 구분합니다. H17 validated ensemble은 완료되지 않았습니다. 이후 동결 체계는 [Phase 5 원본](prospective-experiment.md)과 [현재 workflow](prospective-workflow.md)를 참고합니다.
