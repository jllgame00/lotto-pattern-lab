# Phase 9 — Gap × frequency interaction 방법

## 목적과 연구 가설

HIGH gap AND HOT frequency에서 각 parent에 희석된 translation이 나타나는지 탐색합니다. 차원 증가는 false discovery 위험을 늘립니다. categorical 아홉 상태만 추가하며 continuous4D·arbitrary state sequence·neural network는 구현하지 않습니다. [당시 protocol](superpowers/plans/2026-10-17-phase9.md)에 설정을 고정했습니다. H6는 TESTED / INCONCLUSIVE입니다.

## 데이터 표현과 핵심 정의

target t에서 gap=t-1-last_appearance_draw, W26 count=t-26..t-1입니다. 이전 출현이 없거나 완료 draw가 26 미만이면 joint state는 missing(-1)입니다. 각 training-prestate 1/3,2/3 quantile의 higher convention, boundary tie lower를 사용하고 refit 사이에 경계를 고정합니다. joint id=3*g+f이며 LOW/MID/HIGH와 COLD/NEUTRAL/HOT는 0..2입니다.

sparse target/number table에는 두 causal state·category·cutoff·본번호 target label을 넣고 bonus는 제외합니다. support audit은 zero를 포함한 9개 cell을 모두 담습니다. percentage 분모는 missing을 포함한 전체 number-states/main winning points입니다. shift별 opportunity는 겹치므로 합계를 독립 관측 수로 해석하지 않습니다.

최소 pair100·chain20 opportunities를 support·score 확인 전에 선언했습니다. empty/sparse bin을 merge하지 않습니다. rate는 6/45의 prior 100으로 shrink합니다. propensity baseline도 number-state exposures100을 요구합니다.

## 계산 방법과 interaction

pair shift는 dt1..52,dn-15..15이며 0은 fixed-number reference입니다. predictive rule·leader는 0을 제외합니다. finite rectangle 안으로 이동 가능한 observed source가 opportunity이며 wrap은 없습니다. raw z=(matches-n*p)/sqrt(n*p*(1-p)), p=6/45입니다. marginal Wilson은 dependence·selection을 무시해 보정 증거가 아닙니다.

두 차원이 알려진 동일 source population의 disjoint joint cell을 parent로 pooling합니다. gap은 frequency 세 cell, frequency는 gap 세 cell, unconditional은 전체 9개를 합치고 geometry도 같습니다. missing-history artifact를 막기 위한 matched-population control이며 역사 parent 모델 자체는 기존 default를 유지합니다.

Interaction lift=joint_shrunk/max(gap_shrunk,frequency_shrunk)-1입니다. raw/shrunken rate·source/opportunity/match count·absolute rate difference를 export합니다. positive lift는 두 parent 모두를 넘는다는 뜻이나 causal effect·additive-model interaction test·calibrated future probability는 아닙니다.

same-state chain은 dt1..13,dn+/-1..6입니다. 길이3/4/5 continuation은 이전 L-1 observed points와 final compatible PRE-state를 요구하며 final outcome은 조건이 아닙니다. longest path는 모든 geometric lengths3+로 별도 calibration합니다. maximal path는 nested fragment를 억제해도 다른 rule과 중첩될 수 있습니다.

14,508 pair tuple + 23,400 chain rule/length tuple = 37,908 unique tuple입니다. 같은 pair에 conditional·interaction을 적용해 52,416 statistic cells입니다. length3/4/5의 4,212개는 subset이며 추가 탐색이 아닙니다. parent aggregate11,284개는 별도 maximize하지 않습니다. pruning 전 chain start 후보는 574,565,004개입니다.

## Null / surrogate 설계와 Global search correction

199 IID six-of45와 199 exact-margin history(20*T curveball), seed 90042마다 두 causal feature·encoder를 다시 계산·fit해 같은 전체 탐색을 합니다. finite mixing은 근사입니다. 네 family는 conditional z·positive interaction lift·chain continuation z·longest chain입니다. p=(1+exceedances)/(B+1), 각 null 안에서 Bonferroni4이며 두 null 모두 통과해야 합니다. seed·threshold·count·maximum을 보존합니다. raw resolution0.005, adjusted0.020입니다. local 값이 전체 보정을 대신하지 않습니다.

## Leakage 방지와 모델

JointStateTranslationModel은 최소 100 opportunities에서 p 초과 positive shrunken joint excess 상위 20개를 남깁니다. 현재 training prefix에서 rule을 학습하며 full-history leader를 입력으로 쓰지 않습니다. positive interaction lift를 hard filter하지 않으며 parent 효과의 상속 여부를 진단합니다.

JointStateChainModel은 같은 joint state의 observed predecessor 두 개·최소20 opportunities·prior 100/top20을 요구합니다. descriptive path와 달리 candidate state는 제한하지 않습니다. 다른 차원을 바꿀 수 있는 same-gap/same-frequency control도 계산합니다. Phase 7은 최근 source만 조건화하므로 모든 filter 차이를 분리한 ablation이 아닙니다. 두 모델은 기존 p+(1-p)*weighted active-rule fraction과 strict number boundary를 사용하며 calibrated probability가 아닙니다.

JointStateFrequencyBaseline은 joint cell별 causal exposures와 appearance label을 pooling하여 (positives+100*p)/(observations+100)으로 score합니다. sparse/missing이면 p입니다. geometry 없는 propensity control이며 회차 안 exposure는 의존하므로 non-randomness를 입증하지 않습니다. baseline/geometry 비교를 export합니다.

설정은 결과 전에 고정하고 evaluation 전에 저장한 뒤 변경 여부를 확인합니다. development 401..900, later 901..1245이며 outcome tuning·combination selection은 없습니다. later는 pristine holdout이 아닙니다. targets 401..1245, expanding fit, cadence 26/sensitivity13, seed 42입니다. multiple start는 원래 refit calendar의 nested slice이며 기존 parent·Random/GapLogistic default를 유지합니다.

## 평가 지표

paired circular26-draw block bootstrap 2000, seed 42로 Random·matching2D/gap3D/frequency3D parent와 비교합니다. geometry는 joint propensity와도 비교합니다. hit·rank·recall·pool과 exact hypergeometric reference를 export합니다. interval은 model-search 보정 전 탐색치이며 rare-event zero bound 퇴화가 불가능성을 뜻하지 않습니다.

## Prospective experiment

별도 `reports/prospective/phase9/`에 세 독립 모델만 동결했으며 점추정치로 조합을 정당화하지 않습니다. 45 score/rank/tie·Top6/8/10/12/15·direct Top6·Top12 weighted/coverage nested1/5/10/20·seed 42를 보존합니다. encoder/rules/parent·baseline sufficient statistics/current states·source·configuration·environment/Git·dataset/prior hash도 보존하며 baseline score는 archived posterior와 맞아야 합니다.

reservation 전 validation/rendering 후 exclusive creation하며 regeneration은 거부합니다. 당시 자기 registry만 쓰고 이전 20파일을 전후 확인했습니다. 당시 미래 결과를 가져오기·검색·확인·import·평가하지 않았고 commit/push도 하지 않았습니다. [당시 원본 기록](phase9-prospective.md)은 보존합니다.

## 출력 파일과 CLI

`reports/spatiotemporal_joint/`에 저장합니다. `python main.py analyze-joint --surrogates 199`, `python main.py compare-joint`, `--cadence 13`이 있습니다. 당시 publisher는 `freeze-joint`입니다.

## 한계와 현재 결과

희소 joint cell·부모 분모·중첩·finite mixing·과거 구간 재사용을 주의합니다. [완료 결과](phase9-results.md)와 [현재 workflow](prospective-workflow.md)를 참고합니다.
