# Phase 7 — Gap-conditioned 3D 방법

## 목적과 연구 가설

추가 상태는 CURRENT GAP 하나입니다. recent frequency·calendar·periodicity·HMM state·다른 차원·4D predictor를 추가하지 않았습니다. 상태 pooling이 translation을 가린다는 것은 가설입니다. Phase 5/6 예측은 보존하며 당시 미래 결과를 사용하지 않았습니다. H4는 TESTED / INCONCLUSIVE입니다.

## 데이터 표현과 핵심 정의

target t의 `gap=t-1-last_appearance_draw`이며 t 이전 draw만 씁니다. 마지막 출현 100이면 target 104의 gap은 3입니다. 104 출현은 105 상태부터 reset합니다. never-seen의 gap은 NaN, encoded state는 -1이며 첫 winning occurrence는 conditioned search에서 제외합니다. relative gap은 과거 출현 두 번으로 completed mean interval을 정의해야 합니다. 이전 출현으로 `(last-first)/(appearances-1)`을 계산합니다.

`causal_states(X)`는 target states 1..T+1 배열을 반환합니다. `state_table`은 labeled historical targets 1..T만 export하며 `feature_cutoff=target_draw-1`, `appeared_next`는 명시된 target draw의 출현입니다. dense 3D cube 없이 기존 binary draw×number matrix를 유지합니다.

encoder는 training pre-state에만 fit합니다.

- Exact/clipped: integer gap cap은 `min(26,ceil(training95th percentile))`입니다.
- Quantile: training 1/3·2/3 quantile의 `higher` convention으로 low/medium/high를 만듭니다. 경계 동률은 lower bin에 남기고 empty bin은 merge·retune하지 않습니다.
- Relative: gap/causal mean interval을 `<=.5`, `(.5,1.5]`, `>1.5`로 나누며 undefined mean은 missing입니다.

predictive encoder는 training cutoff에서 refit 후 다음 fit까지 고정합니다. descriptive full-history bin을 이전 forecast에 재사용하지 않습니다. 실제 전체 pre-state의 cap21과 coarse 0–2,3–7,8+는 기술값이며 predictor 상수가 아닙니다.

## 계산 방법과 분모

세 encoding 모두 dt1..52, dn±1..15를 탐색합니다. 사전 translation 범위에서 zero number displacement를 제외하며 fixed-number temporal은 H1/H2에 속합니다. PRE-source gap이 맞고 destination이 finite rectangle 안인 observed source만 opportunity입니다. Rate=matching destination ones / opportunities이며 wrapping은 없습니다. 최소 100 opportunities입니다. sparse row는 export하되 maximum·predictive selection에서 제외합니다.

raw statistic은 `(matches-n*p)/sqrt(n*p*(1-p))`, p=6/45입니다. marginal Wilson은 dependence·selection을 무시하므로 둘 다 탐색 후 유의성 검정이 아닙니다. geometry별 opportunity와 full-search surrogate maximum으로 경계·다중 탐색을 다룹니다.

destination 분석은 같은 shift의 3×3 coarse source/destination bin을 봅니다. destination pre-gap은 자기 회차 직전에 알아도 source 시점에는 모를 수 있습니다. DESCRIPTIVE_ONLY이며 predictor 입력이 아닙니다. true3D는 dt1..13,dn±1..6, clipped pre-gap difference -3..3, 최소 100 opportunities이며 역시 기술 분석입니다. saturated tail에서 clipped displacement는 raw-gap displacement와 다릅니다.

trajectory는 작은 shift grid에서 일정 coarse state 또는 반복 clipped difference -3..3입니다. 길이 3/4/5 continuation은 이전 L-1 observed points와 마지막 pre-state를 요구하며 final outcome을 조건으로 쓰지 않습니다. continuation z는 최소 20 opportunities입니다. longest trajectory는 그 filter 없이 별도 calibration하고 기하학적으로 가능한 5 초과 길이도 포함합니다.

compatible observed predecessor가 없는 maximal path만 export하며 raw/clipped start gap·geometric maximum·endpoints·억제한 nested fragment 수를 보존합니다. 서로 다른 parameter도 점을 공유하므로 독립성을 주장하지 않습니다. count에는 rule/length tuple과 모든 rule/length/start-position을 포함합니다. data-driven pruning으로 effective search를 줄이지 않습니다. sparse search 확장을 피하기 위해 3D Hough intercept는 보류했습니다.

## Null / surrogate 설계와 Global search correction

199 IID와 199 constrained history마다 causal gap·cap/bin을 다시 계산·fit한 뒤 동일 탐색을 합니다. fixed-margin은 20*T independent curveball trades로 row별 six points와 per-number totals를 보존합니다. finite mixing은 근사이며 exact uniform sampling을 보장하지 않습니다. 실제 gap state를 shuffled points에 붙이지 않습니다.

다섯 maximum family는 모든 표현의 conditional source state·destination·true3D displacement·trajectory continuation·longest trajectory입니다. `p_global=(1+count(null_max>=real_max))/(B+1)` 뒤 각 null 안에서 5-family Bonferroni를 적용하며 두 null 모두 통과해야 합니다. 199 replicates에서 raw resolution은 .005, adjusted는 .025입니다. 동일 recipe로 학습하는 cap 때문에 surrogate별 configuration 수가 조금 변할 수 있어 count·seed를 보존합니다.

(+42,-5)는 Phase 6에서 선택한 follow-up입니다. coarse-state별 local null을 export하지만 독립 preregistered evidence는 아닙니다. 같은 rule은 global conditional search에 포함됩니다.

## Leakage 방지와 예측 protocol

primary는 사전 coarse source-gap bin입니다. pair / chain은 최소 100 / 20 training opportunities, 6/45의 prior 100으로 shrink하며 상위 20 positive excess를 남깁니다. Chain은 observed predecessor 두 개와 최근 source PRE-gap을 조건으로 씁니다. destination 조건과 full-history 발견은 입력이 아닙니다. ranking support는 calibrated probability가 아닙니다.

동일 targets 401–1245, cadence 26에서 기존 Phase 6 parent·Gap Logistic·seeded Random과 비교하며 sensitivity cadence 13입니다. development는 900까지, later는 901–1245이며 pristine holdout이 아닙니다. starts 401/501/601/701/801/901은 한 실행을 slice하고 refit calendar를 유지합니다. 세 표현은 고정 ablation으로 evaluation에서 winner를 선택하지 않습니다. 새 모델에는 sparse-support filter도 있으므로 기존 parent와의 전체 model 비교이며 conditioning만 분리한 효과가 아닙니다.

## 평가 지표

2000회 paired 26-draw circular block bootstrap으로 Random·같은 2D parent 대비 hit·rank·recall·pool을 비교합니다. winning-number rank는 낮을수록 좋습니다. interval은 탐색적이며 multiplicity correction이 없습니다. zero rare-event bootstrap 퇴화는 미래 사건을 배제하지 않습니다. pool containment와 ticket prize를 구분합니다.

## Prospective experiment

사전 coarse-bin 두 모델만 동결하고 ensemble은 선택하지 않았습니다. 별도 `reports/prospective/phase7/`에 score/rank·Top6/8/10/12/15·direct Top6·Top12 weighted/coverage nested 1/5/10/20 portfolio·설정·encoder·rule·source·environment·integrity를 보존했습니다. 당시 Phase 5/6 hash를 전후 확인했고 target 결과를 가져오거나 평가하지 않았습니다. [당시 원본](phase7-prospective.md)은 그대로 보존합니다.

## 출력 파일과 CLI

출력은 `reports/spatiotemporal3d/`입니다. `python main.py analyze-gap3d`, `python main.py compare-gap3d`, sensitivity `--cadence 13 --primary-only`가 있습니다. 당시 동결 명령은 `freeze-gap3d`입니다.

## 한계와 현재 결과

희소 상태·경로 중첩·finite mixing·역사 구간 재사용이 한계입니다. [완료 결과](phase7-results.md)와 [현재 workflow](prospective-workflow.md)를 참고합니다.
