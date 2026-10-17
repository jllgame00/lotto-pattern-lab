# Phase 3 — Gap robustness와 prize-aware 연구

## 결론

예측·portfolio 우위는 확립되지 않았습니다. Gap-only Logistic의 coefficient 부호는 안정적이지만 Random·간단한 gap rule 대비 개선은 불확실합니다. Top12 제한은 unrestricted random보다 mean best matches를 낮췄으며 소수 five-match event로 보상 효과를 확립하지 못했습니다. 수익성을 계산하지 않습니다.

## 데이터 및 검증 범위와 CLI

```powershell
python main.py prize-eval
python -m pytest -q
```

`load_research_history`는 canonical 1..1244만 읽습니다. header와 최대1244 physical CSV rows만 읽고 suffix는 parsing·hashing·feature·selection에서 제외합니다. feature/model/backtest는1245+를 거부하며 unseal flag가 없습니다. canonical current prediction·collection은 차단합니다. alternate path도 target 1245나 canonical suffix 복사에 쓸 수 없습니다. response batch에 미래 draw가 섞일 수 있어 network collection을 막고 짧고 검증된 open-prefix offline import만 허용합니다.

이전 Phase의 `predict-current`는1245까지 사용했습니다. 이를 소급 취소할 수 없으므로 never-accessed 자료라고 부르지 않습니다. 이 연구는1245를 inspect하지 않고 이전 feature/current-prediction artifact를 재사용하지 않았습니다. seal은 현재 연구의 강제 경계이며 과거 접근 부재를 주장하지 않습니다.

사전 설정은 C=1·seed 42·cadence 26·starts401/501/601/701/801·end1244, primary601..1244입니다. feature는 target 105부터, open table51,300 rows입니다. primary15 specifications는 Random·gap/gap+periodicity Logistic·gap rules5·다른 Logistic groups6·same-number similarity입니다. 다른 start는 Random·두 gap Logistic·다섯 rules를 반복하며 tuning·tree replacement는 없습니다.

start window는 중첩되고 cadence phase도 달라 다섯 독립 반복이 아닌 sensitivity입니다. gap-only는 이전 결과를 보고 조사 대상으로 정했으므로 재사용한 구간은 탐색 증거이며 독립적인 전략 선택 검증이 아닙니다.

## 방법 — Gap-only robustness

paired mean-hit difference는 동일 target의 Gap Logistic - seeded Random입니다. 95% circular26-draw block bootstrap 2000회이며 robustness·heuristic table의 gap 비교는 같은 stream을 씁니다.

| Start | Targets through1244 | Gap average hits | Difference vs random | Paired95% interval |
|---|---:|---:|---:|---|
|401|844|.843602|+.041469|[-.030806, .117299]|
|501|744|.831989|+.026882|[-.057829, .112903]|
|601|644|.849379|+.051242|[-.032609, .133579]|
|701|544|.845588|+.069853|[-.016544, .159926]|
|801|444|.853604|+.085586|[-.006813, .175732]|

모든 interval이 zero를 포함합니다. primary early/middle/recent hit는 .809302/.869767/.869159, paired Random 차이는 -.046512/+.097674/+.102804입니다. 높은 전체 평균이 일관된 시간 우위는 아닙니다.

### Ranking을 결정하는 항

`coefficient_audit.csv`는 두 gap 모델·다섯 start의 모든 fit에 대해2520 rows입니다. signed standardized/raw coefficient·magnitude·training mean/std·imputation·intercept·C·정의·rows·cutoff를 저장합니다. `coefficient_stability.csv`는 sign/range, `ranking_contributions.csv`는 refit 없이 각 항을 뺐을 때 logit variation·평균 rank 변화를 audit합니다. 기계적 설명이며 causal importance가 아닙니다.

start601의 gap-only25 fits 평균 standardized coefficient는 다음과 같습니다.

| Feature | Mean coefficient | Sign changes | Mean absolute rank change if term removed |
|---|---:|---:|---:|
|current_gap|-.151255|0|15.33|
|gap_ratio|+.139851|0|8.62|
|median_gap|+.051890|0|11.33|
|gap_std|+.050674|0|9.45|
|mean_gap|-.027469|0|3.14|
|has_appeared|0|0|0|

큰 두 coefficient는 서로 반대이고 입력도 상관됩니다. raw current-gap contribution은 `gap * (b_current_gap + b_gap_ratio / historical_mean_gap)`이므로 단순 largest-gap / overdue rule이 아닙니다. historical median·variability도 순위를 바꿉니다. 상관된 한 항을 빼면 cancellation이 사라져 변화가 커질 수 있으며 rank change를 독립 contribution으로 합치면 안 됩니다. 여기서 `has_appeared`는 constant입니다.

audit는 ranking mechanism을 설명할 뿐, 추가 hit가 반복 가능한 signal 때문임을 입증하지 못합니다. sampling variation과 양립합니다.

### 투명한 비교 rule

모든 rule은 같은 causal feature와 training-only median imputation을 받습니다. zero/unsupported denominator는 neutral zero score입니다. 이전에 별도 문서화된 GapModel은 없었습니다.

| Rule | Score (larger ranks first) | Average hits,601..1244 | Gap logistic minus rule,95% interval |
|---|---|---:|---|
|Largest gap|current_gap|.804348|[-.055939, .150621]|
|Smallest gap|-current_gap|.810559|[-.046584, .113354]|
|Relative gap|current_gap / mean_gap|.801242|[-.048137, .150621]|
|Gap z-score|(current_gap+1-mean_gap) / gap_std|.822981|[-.071429, .125815]|
|Mean-reversion style|-abs(gap z-score)|.833851|[-.069876, .105629]|

z-score의 +1은 다음 draw에서 완성될 interval이며 출현 직후 current absence는0입니다. 과거 부재를 보상한다는 주장이 아닌 검증 가능한 rule입니다. 다섯 start의 gap-vs-rule25 intervals 중 zero를 제외한 것은 없습니다.

## Candidate-pool 결과

TopK의 exact uniform distribution은 `P(J=j)=C(6,j)*C(39,K-j)/C(45,K)`입니다. full0..6·>=3/4/5/6·expected count·exact reference·seeded Monte Carlo2000·paired difference·Clopper-Pearson interval을 저장합니다. latter는 iid Bernoulli 가정이며 일반 dependence-robust interval이 아닙니다. block bootstrap도 함께 제공합니다.

primary644 draws의 gap-only 결과입니다.

| Pool | Six-number combinations | >=5-winner events | Observed rate | Exact random rate | Random expected events | All-six events |
|---|---:|---:|---:|---:|---:|---:|
|Top6|1|0|0%|.002885%|.0186|0|
|Top8|28|0|0%|.025783%|.1660|0|
|Top10|210|2|.310559%|.110865%|.7140|0|
|Top12|924|4|.621118%|.332226%|2.1395|0|
|Top15|5005|8|1.242236%|1.167518%|7.5188|0|

empirical Random의 Top8/10/12/15 >=5는0/0/0/3입니다. zero Top12로 exact expectation2.14를 대신하면 안 됩니다. 15 specifications ×5 pool sizes의 >=5/all-six Bonferroni binomial upper-tail test는 모두1.0(150 planned tests)입니다. 다른 specification에 all-six가 한 번 있어도 전체 탐색 후 unusual함은 확립되지 않았습니다. event·time block을 export하지만 새 전략을 선택하지 않습니다.

## Periodicity의 추가 가치

start601에서 gap+periodicity를 gap-only와 직접 비교합니다.

- 평균 Top6: .804348 대 .849379, 차이 -.045031, paired95%[-.135093,.045070]입니다.
- mean winning rank:22.573758 대22.754917, 차이-.181159, interval[-.569397,.243012]이며 낮을수록 좋습니다.
- Top10 >=5:0 대2 events, 차이 interval[-.007764,0]입니다.
- Top12 >=5:2 대4 events, 차이 interval[-.010870,.003106]입니다.

평균 hit와 두 concentration count는 개선되지 않았고 rank 개선도 불확실합니다. 다섯 start를 모두 export하며 incremental periodicity benefit은 확립되지 않았습니다.

## 동일 예산 virtual portfolio

primary pool은 결과 전12로 고정했고 `--pool-size`는8,10,15도 지원합니다. budget1/5/10/20은 model/draw/seed별 한 deterministic20-ticket 생성의 prefix입니다. ticket은 six unique numbers, portfolio 안 ticket도 distinct입니다. Top6에는 조합 하나뿐이므로20 unique tickets를 만들 수 없습니다. target·bonus는 constructor 입력이 아닙니다.

- **Weighted:** 조합 weight는 여섯 number weight의 곱에 비례하며 Gumbel order로 distinct combination을 고릅니다. negative score는 nonnegative로 이동하고0.1% uniform mixture를 더합니다. calibrated prize probability나 이전 sequential sampler가 아닙니다.
- **Coverage:** 새 five-subsets, pairs를 순서대로 최대화하고 seeded score-weighted priority로 tie를 풉니다. C(15,6)=5005까지의 작은 공간만 enumerate합니다.
- **Random Top12:** RandomModel의 uniform ranked pool에 같은 절차를 적용합니다. **Uniform45:** 전체45에서 distinct ticket을 uniform sample하며8,145,060 공간을 enumerate하지 않습니다.

seeded replicate 세 개는 같은 실제 draw를 공유합니다. draw 안에서 seed 평균 후 paired block bootstrap하며 replicate별 count·prize draw interval도 저장합니다. seed나 nested budget을 독립 history로 세지 않습니다.

644 targets·세 seed 평균의 draw별 mean best main matches입니다.

| Budget | Gap weighted | Random Top12 weighted | Gap coverage | Random Top12 coverage | Uniform45 |
|---|---:|---:|---:|---:|---:|
|1|.797101|.792443|.797101|.792443|.823499|
|5|1.361801|1.365942|1.472567|1.480849|1.743271|
|10|1.499482|1.505694|1.536749|1.547619|2.099379|
|20|1.574017|1.577122|1.587992|1.586957|2.389752|

20 tickets에서 gap weighted - matched Random은 -.003106,95%[-.106121,.099896], coverage는 +.001035[-.100414,.102484]입니다. Uniform45 대비는 각각 -.815735[-.896506,-.733424], -.801760[-.882531,-.718414]입니다. 집중은 mean best matches를 희생하며 안정적인 five-match 이점을 확립하지 못했습니다.

20 tickets는 six-combinations20/924=2.1645%를 덮습니다. gap weighted의 Top12 five-subsets 평균은14.2465%, coverage는120/792=15.1515%입니다. combinatorial coverage 증가는 candidate prediction 우위가 아닙니다. 예산별 coverage·4+/5+·prize는 portfolio_summary.csv·portfolio_replicates.csv에 있습니다.

### Exact unrestricted-random 기준

M=C(45,6)의 distinct uniform B tickets 중 favorable F이면 `P(any favorable)=1-product(1-F/(M-i), i=0..B-1)`입니다. exact integrated best-match와 별도1st/2nd/3rd draw probability이며 overlap이 다른 임의 fixed portfolio의 null law가 아닙니다. `uniform_portfolio_reference.csv`는 이 law에서2000 historical runs를 sample하며 거대 ticket space를 생성하지 않습니다.

budget1/5/10/20의 expected mean best는 .800000/1.728936/2.082850/2.389641,644-target당 >=5 expected draws는 .0186/.0929/.1858/.3715입니다. 20 tickets의 Monte Carlo95% range는0..2입니다. random run의 rare-event zero는 이상하지 않으며 true baseline을 zero로 만들지 않습니다.

### Historical prize-equivalent — 구매하지 않은 가상 티켓

ticket 생성 후 bonus로 분류합니다. six main=1st, five+bonus=2nd, five without bonus=3rd, four=4th, three=5th입니다. bonus는 supervised positive에서 제외합니다. exact uniform numerator는1,6,228,C(6,4)C(39,2),C(6,3)C(39,3), denominator C(45,6)입니다.

budget20·세 seed에서 gap weighted는1st/2nd/3rd occurrences0/1/4, coverage는0/0/6입니다. 중복을 합치면 distinct second ticket 하나·third 여섯이며 draw 621,847,1225 세 회차뿐입니다.

second-equivalent는 draw 621, weighted replicate2, ticket index14로 budget20부터 포함된 `[2,6,9,16,19,42]`입니다. main `[1,2,6,16,19,42]`, bonus9였습니다. training cutoff600·feature620이며 draw 621 outcome은 scoring·construction에 들어가지 않았습니다.

15 specifications·두 방법·세 seed에서 rare occurrences44개는14 draws의27 distinct target/ticket이며1st0·2nd1·3rd26입니다. method/seed 중복은 독립 발견이 아닙니다. Uniform45 포함 max-budget instances1,197,840개이며 작은 budget은 prefix를 재사용합니다. second event 하나는 예측력·수익성의 증거가 아닙니다.

## 한계·의존성·검증·출력

당시 optional tree library는 없었습니다. `PIP_NO_INDEX=1`, HTTP/HTTPS proxy `127.0.0.1:9`를 확인했고 bounded PyPI probe는 ConnectionRefusedError/WinError10061로 실패했습니다. 제한을 해제하지 않았고 tree 실행·복잡한 replacement를 주장하지 않습니다. 당시 세부 기록 경로는 dependency_probe.json입니다.

main219.771s 중 portfolio100.794s, 이후 reporting refresh5.035s로 per-prize interval과 gap bootstrap 표를 맞췄습니다. exact-reference/combinatorial column도 saved outcome/formula에서 추가했습니다. 결과 후 model/ticket 설정은 변경하지 않았습니다. 독립 review의 candidate/import seal bypass·zero-event interval 누락은 regression test로 수정했습니다.

출력은 `reports/prize_research/`이며 주요 파일은 다음과 같습니다.

- `comparison.csv`, `ranking_comparisons.csv`, `ranking_time_blocks.csv`.
- `coefficient_audit.csv`, `coefficient_stability.csv`, `ranking_contributions.csv`.
- `gap_vs_heuristics.csv`, `gap_periodicity_comparison.csv`.
- `candidate_summary.csv`, `candidate_pools.csv`, `pool_5plus_events.csv`.
- `portfolio_summary.csv`, `portfolio_replicates.csv`, `portfolio_time_blocks.csv`.
- `prize_events.csv`, `uniform_portfolio_reference.csv`, `experiment.json`.

당시 artifact check는 rankings9660·pool counts 48300·equal-budget rows 239568·nested outcome과 rare44 occurrences를 open main/bonus로 재구성했습니다. target·feature cutoff는 seal을 지켰고 commit/push는 없었습니다.

당시 전체 테스트 **114 passed,2 skipped**(optional trees),14.67s이며 기존85개도 통과했습니다. compile·whitespace check도 통과했습니다.

## Prospective experiment와 다음 단계

이 가상 prize 결과는 prospective 당첨 증거가 아닙니다. 이후 완료된 [Phase 4](regime-research.md)와 [현재 prospective workflow](prospective-workflow.md)를 참고합니다.
