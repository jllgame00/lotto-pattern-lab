# Phase 8 — Recent-frequency-conditioned 3D 방법

## 목적과 연구 가설

세 번째 상태를 gap에서 frequency로 바꿉니다. gap 2가 같아도 최근 출현 전의 빈도는 다를 수 있습니다. source COLD/NEUTRAL/HOT가 draw/number translation을 조건화하는지 탐색합니다. gap은 기존 별도 baseline에서만 사용하고 frequency predictor에는 넣지 않습니다. 4D·neural network·추가 state family는 구현하지 않았습니다. H5는 TESTED / INCONCLUSIVE입니다.

## 데이터 표현과 핵심 정의

target t의 W는 10,26,52이며 t-W..t-1을 포함해 count, rate=count/W를 계산합니다. 결과 t를 바꿔도 state t는 같습니다. 완료 draw가 W 미만이면 count/rate는 missing, encoded -1로 source search에서 제외합니다. partial window를 W로 나누지 않습니다.

prior number rate는 t 이전 전체 appearances/(t-1)입니다. relative frequency=recent_rate/prior_rate이며 prior가 0이면 missing입니다. zero·infinity로 대체하지 않습니다. positive prior에서 recent count 0은 유효한 cold observation입니다. feature에는 6/45와 historical rate 대비 deviation을 포함하고 bonus는 제외합니다. target_draw t, feature_cutoff t-1, appeared_next는 해당 target의 출현입니다. dense cube·실제 미래 label은 만들지 않습니다.

count 0..W와 rate 0..1은 window 안에서 bijective이므로 둘 다 export하지만 동일 partition은 `count`로 한 번만 탐색합니다. training-prestate 1/3·2/3 quantile에 `higher`를 사용하고 경계 동률은 lower bin입니다. 불균등 support·empty bin을 그대로 두며 threshold를 최적화하지 않습니다. relative bin 경계는 0.5·1.5입니다. full-history descriptive bin은 과거 예측에 쓰지 않고 모델별 training encoder를 refit 사이에 고정합니다.

## 계산 방법

conditional pair는 dt1..52, dn-15..15이며 zero는 fixed-number reference입니다. translational leader와 predictive rule은 zero를 제외합니다. causal state가 있고 destination이 finite rectangle 안인 winning source가 opportunity이며 wrapping은 없습니다. Rate=matches/opportunities, baseline6/45, lift=rate/(6/45), 최소 100 opportunities입니다. sparse row는 export하되 supported maximum이 될 수 없습니다.

raw z=(matches-n*p)/sqrt(n*p*(1-p))입니다. Wilson interval은 dependence·selection을 무시한 marginal 진단이며 보정된 유의성 검정이 아닙니다.

directional pair는 양·음 displacement의 분모를 따로 정규화합니다. rate difference/sqrt(p*(1-p)*(1/n_positive+1/n_negative))이며 두 방향 모두 support 100이 필요합니다. coarse HOT-minus-COLD interaction은 방향별 차이를 빼고 reference variance를 합칩니다. overlap·dependence 때문에 단순 normal p-value 대신 absolute contrast maximum을 전체 null로 calibration합니다.

true count displacement는 dt1..13,dn±1..6,delta_count-1..1입니다. destination pre-count 관계는 DESCRIPTIVE_ONLY이며 predictor가 쓰지 않습니다. same-state trajectory는 coarse bin, count trajectory는 같은 bounded count increment를 사용합니다. 임의 categorical progression은 없습니다. Phase 7의 geometry를 frequency-count array에 적용하며 gap history는 계산하지 않습니다.

길이 3/4/5 continuation은 이전 L-1 observed points와 마지막 pre-state만 요구하고 final outcome은 요구하지 않습니다. 최소 20 opportunities입니다. longest path는 5 초과를 포함한 전체 가능한 길이로 별도 calibration합니다. rule별 maximal path만 export하고 nested fragment를 억제·집계합니다. 다른 parameter도 중첩될 수 있어 독립성을 주장하지 않습니다. count에는 pruning 전 모든 tuple과 rule/length/start-position이 포함됩니다. sparse intercept family의 해석 한계로 3D Hough는 보류했습니다.

## Null / surrogate 설계와 Global search correction

199 IID history는 매 draw에 uniform unique six numbers, 199 constrained history는 20*T curveball trades로 정확한 row/column sums를 보존합니다. finite mixing은 근사이며 exact margins가 모든 history의 uniform sampling을 뜻하지 않습니다. seed 80042의 독립 child seed를 보고서에 보존합니다.

surrogate마다 W10/26/52 causal frequency·prior rates·quantile boundaries를 다시 계산하고 같은 전체 탐색을 합니다. 실제 state를 randomized point에 붙이지 않습니다. 다섯 family는 모든 window/representation을 합친 conditional overlap·directional contrast·count displacement·trajectory continuation·longest trajectory입니다.

`p_global=(1+count(null_max>=real_max))/(199+1)` 뒤 각 null 안에서 Bonferroni5를 적용하며 두 null 모두 통과해야 합니다. raw resolution0.005, adjusted0.025입니다. window별 maximum은 진단용이며 전체 보정을 우회하지 않습니다. Phase 6의 (+42,-5) follow-up에는 window/state별 local null을 붙이지만 독립 preregistration이 아니며 global correction을 대신하지 않습니다.

## Leakage 방지와 예측 모델

FrequencyConditionedTranslationModel은 최소 100 training opportunities의 양의 source-state excess를 학습합니다. FrequencyConditionedChainModel은 같은 pre-frequency state의 predecessor 두 개와 최소 20 opportunities를 요구하고 destination state는 조건으로 쓰지 않습니다. 둘 다 6/45의 prior 100·top20 positive rule·dt1..52,dn±1..15를 씁니다. rule·encoder·scaling은 training-only입니다. scoring에는 바뀌지 않은 fitted prefix와 target 전 완료 draw만 허용합니다. score는 weighted rule support이며 calibrated probability가 아닙니다. source draw/number/count/state·opportunities·rule contribution을 노출하고 tie는 작은 번호 우선입니다.

direct ablation은 이전 default를 유지합니다. Phase 8 chain은 두 predecessor state 일치를 요구하지만 Phase 7 gap chain은 최근 source만 조건화합니다. sparse-support filter도 추가되므로 state choice만의 순수 효과가 아니라 선언된 전체 모델을 비교합니다.

W26은 Phase 8 결과 전에 primary prospective 가설로 선언했습니다. W10·W52는 고정 ablation입니다. 1246회나 전체 evaluation으로 representation·threshold·window를 선택하지 않았습니다. 별도 development-only selector는 401..900의 평균 Top6를 최대화하고 tie는 26→10→52입니다. later 성능은 별도 export하며 사전 두 prospective track을 대체하거나 ensemble을 만들지 않습니다.

## 평가 지표와 Walk-forward

동일 targets 401..1245, expanding training, cadence 26 / sensitivity13, seed 42입니다. 기존 Random·Gap Logistic·2D parent·gap3D와 같은 draw를 사용합니다. starts401/501/601/701/801/901은 원래 refit 일정의 nested slice입니다. later 901..1245는 development 이후이지만 앞선 Phase가 사용했으므로 pristine prospective evidence가 아닙니다.

2000회 paired circular26-draw block bootstrap, shared seed 42로 Random·matching2D·matching gap3D 대비 hit·rank·recall·pool을 비교합니다. interval은 탐색적이며 multiple-model correction이 없습니다. zero-event 퇴화는 불가능성을 뜻하지 않습니다. legacy export는 기존 bootstrap stream, common-seed parent 비교는 별도 파일입니다. exact hypergeometric과 full0..6 분포를 내보내며 pool concentration과 실제 six-number ticket prize를 구분합니다.

## Prospective experiment

사전 W26 두 모델만 `reports/prospective/phase8/`에 동결했습니다. 좋은 역사 점추정치만으로 조합을 정당화하지 않습니다. 45 score/rank·Top6/8/10/12/15·ties·direct Top6·Top12 weighted/coverage·seed 42·unique nested1/5/10/20 budget을 보존합니다. encoder/rules·source versions/hashes·protocol·environment·Git·dataset cutoff/hash·prior hashes도 포함합니다.

당시 이전 15개 파일을 전후 검사하고 자기 directory·registry에만 썼습니다. ID reservation 전 validation/rendering, exclusive creation, regeneration 거부를 사용합니다. snapshot/manifest integrity는 별도 기록이며 validation은 버전 계약을 따릅니다. 당시 미래 결과를 가져오거나 평가하지 않았습니다. [원본 기록](phase8-prospective.md)은 보존합니다.

## 출력 파일과 CLI

`reports/spatiotemporal_frequency/`에 저장합니다. `python main.py analyze-frequency3d --surrogates 199`, `python main.py compare-frequency3d`, `--cadence 13` sensitivity가 있습니다. 당시 동결 명령은 `freeze-frequency3d`입니다.

## 한계와 현재 결과

count tie·희소 상태·겹치는 경로·finite mixing·과거 구간 재사용이 한계입니다. [완료 결과](phase8-results.md)와 [현재 workflow](prospective-workflow.md)를 참고합니다.
