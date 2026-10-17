# Phase 10 — Number-space 방법

## 목적과 연구 가설

연속 상태 차원을 추가하지 않고 표현을 바꾸는 가설입니다. 번호 label의 수치적 인접성에 물리적·인과적 의미를 가정하지 않습니다. [당시 protocol](superpowers/plans/2026-10-17-phase10.md)에 window·width·kernel·search·selection·ticket rule을 고정했습니다. 현재 H8는 TESTED / INCONCLUSIVE이며 옛 H9 표기는 archive에서 보존합니다.

## 데이터 표현과 핵심 정의

target T는 완료 draw<T만 사용합니다. full windows 10/26/52, row별 unique6 본번호이며 bonus는 제외합니다. width 3/5/7/9의 valid start는 각각43/41/39/37개입니다. time·number axis는 wrap하지 않습니다. range table에는 마지막 포함 draw와 next target index를 남깁니다. 당시 index1246은 결과를 읽거나 label하지 않고 기록할 수 있었습니다.

Range density=count/(W*width), expected p=6/45입니다. draw별 range count의 hypergeometric variance는 6*(width/45)*(1-width/45)*39/44이며 W배합니다. raw z는 기술값이며 local 유의성 주장이 아닙니다.

primary kernel은 none[1], triangular1[.5,1,.5], triangular2[.25,.5,1,.5,.25], Gaussian2[exp(-2),exp(-.5),1,exp(-.5),exp(-2)]입니다. descriptive box radii1..4로 multiscale 진단합니다. finite boundary에서 남은 weight를 renormalize합니다. neighbor-only는 normalization 전에 center를 제거하고 none에는 해당 variant가 없습니다. normalized weight a에서 IID smoothed mean variance는 p*(1-p)*(45*sum(a*a)-1)/(44*W)로 같은 draw의 negative covariance를 반영합니다. constant input은 1/45 경계에서도 일정하며 45→1 spillover는 없습니다.

## 계산 방법 — Zone·motion·spacing

서로 다른 positive-z Top3 range를 겹침의 transitive grouping으로 묶습니다. 겹친 세 window는 독립 발견 세 개가 아닙니다. strongest range 동률은 작은 start 우선입니다. persistence는 identical range의 longest run, movement는 absolute step<=4의 same-direction nonzero center-step longest run입니다. exact +/-1..4 반복·mean absolute movement·interval Jaccard도 보고합니다. rolling overlap이 persistence를 기계적으로 만들므로 null에도 같은 overlap/tie 규칙을 씁니다.

draw별 sorted numbers·다섯 spacings·min/max/mean/median/variance·consecutive pair·range·mean point nearest-neighbor distance·small gaps<=2·large gaps>=10·threshold2/4 cluster 수·다섯9-number region 수를 export합니다. 17개 metric은 상관·중복이 있어 독립 근거17개가 아닙니다. ordered spacing motif는 합<=44인 positive5-tuples 전체 C(44,5)=1,086,008개이며 임의 motif를 미리 고르지 않습니다.

## Null / surrogate 설계와 Global search correction

1245까지의 모든 valid rolling endpoint를 탐색합니다. range584,000 cells, number/kernel/signal2,463,750 cells, strongest-zone14,600 endpoint records, zone/movement144 metrics, spacing-window 83,215 cells, motifs1,086,008개입니다. range12·primary kernel 12·kernel/signal45 settings는 같은 cells의 설명이지 추가 검정이 아닙니다. computational opportunities이며 독립 가설 수가 아닙니다.

여섯 global family는 maximum range z·neighborhood z·zone persistence·directional movement·maximum absolute rolling spacing/clustering z·motif repeat count입니다. clustering windows 1/10/26/52입니다. real history와 별개인 50,000 IID draws, seed 1010의 deterministic50 batches로 reference mean/SD를 구합니다.

199 IID와 199 fixed-margin curveball, seed 100042입니다. latter는 20*T trades로 exact row/column sums를 유지하고 mixing은 근사입니다. 매 surrogate가 count·zone·smoothing·spacing을 다시 계산해 같은 탐색을 합니다. p=(1+exceedances)/(B+1), null별 Bonferroni6이며 두 null 모두 통과해야 합니다. raw resolution0.005, adjusted0.030입니다. local z는 complete-search calibration을 대신하지 않습니다.

## Leakage 방지와 development 선택

RangeDensityModel은 선택된 W,width를 쓰며 interval rate를 prior 26 draws로 p에 shrink합니다. candidate를 포함하는 interval의 p 초과 positive excess를 평균한 뒤 p를 더합니다. overlap 평균은 내부 range boundary를 완화하고 edge membership 수를 조정합니다. ranking support이며 calibrated predictive probability가 아닙니다.

NeighborhoodModel은 causal recent rate에 고정 kernel을 적용합니다. 후보는3 windows ×4 primary kernels이며 neighbor-only는 별도 ablation입니다. none은 own-number control입니다. GapNeighborhoodModel은 기존 Gap Logistic과 선택 neighborhood의 percentile rank를 gap weights .25/.5/.75 중 하나로 평균하며 equal score는 average rank를 받습니다.

development 401..900의 mean Top6만 최대화하고 tie는 선언 순서입니다. later scoring 전에 SHA256으로 selection을 저장합니다. cadence 13은 cadence 26 selection을 재사용하며 재선택하지 않습니다. development hash로 다른 prefix 재사용을 막습니다. full401..1245는 selection optimism이 포함된 탐색 결과이며 primary는901..1245입니다. latter는 선택에서 제외했어도 pristine holdout이 아닙니다. start slice는401의 refit calendar를 유지합니다.

## 평가 지표

동일 target sets를 쓰며 Random/GapLogistic은 변경하지 않습니다. score/rank/cutoff/seed를 audit합니다. paired circular26-draw bootstrap 2000, seed 42로 Random·raw FrequencyW26·Gap Logistic과 비교합니다. interval은 model-search 보정 전 탐색치입니다. exact hypergeometric pool expectation·full0..6 분포도 export합니다.

## Candidate-pool / prize-aware 평가

unique nested1/5/10/20 tickets, seed 42+target, model별 Top15 pool입니다. rawFrequencyW26·Gap Logistic·선택 neighborhood/range/combination weighted·range-aware coverage·uniform45를 비교합니다. coverage는 slot마다 fixed64 weighted proposals 중 new five-subset coverage·uncovered-zone representation·new-pair coverage·seeded priority의 lexicographic 순서로 선택합니다. zone 밖은 별도 category입니다. 2+2 quota·target·bonus는 생성에 쓰지 않으며 모든 portfolio 후 actual/bonus를 읽고 prizes1/2/3를 별도 집계합니다.

Uniform45는 Top15보다 넓은 번호 coverage를 탐색하는 동일 예산 실용 비교입니다. exact uniform portfolio law를 겹치는 임의 range portfolio에 적용하지 않습니다. paired uncertainty·rare-event marginal interval을 함께 봅니다. uniform과 weighted control 모두에 robust historical superiority가 없으면 range-aware prospective allocation은 보류합니다.

## Prospective experiment

publisher는 자기 phase10 namespace/registry만 씁니다. 독립 선택한 세 score track의45 score·rank/tie/Top6/8/10/12/15·direct Top6·seed 42·Top12 weighted/coverage portfolio를 보존합니다. archived causal count·frozen gap feature/scaler/coefficient로 score를 재계산하고 ranking/ticket consistency를 검증합니다. selection/configuration/source/environment/dataset/prior hash를 보관합니다. permanent reservation 전 serialization/validation, exclusive creation, regeneration 거부를 적용했습니다. 당시 이전25파일을 전후 검사했고 미래 결과를 가져오거나 평가하지 않았습니다.

## 출력 파일과 CLI

`reports/number_space/`에 저장합니다. `python main.py analyze-number-space --surrogates 199`, `python main.py compare-number-space`, `--cadence 13` sensitivity가 있습니다. 당시 publisher는 `freeze-number-space`입니다.

## 한계와 현재 결과

번호 인접성·overlap·finite mixing·selection optimism이 한계입니다. [완료 결과](phase10-results.md)와 [현재 workflow](prospective-workflow.md)를 참고합니다. [당시 prospective 원본](phase10-prospective.md)은 수정하지 않습니다.
