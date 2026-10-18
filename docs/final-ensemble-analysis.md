# Phase27 / H17 — Final validated weak-signal ensemble 방법

기존 후보의 순위만 조합한다. 새 가설·feature family·underlying predictor는 추가하지 않는다. 역사 상한은 **1245회**이며 실제1246 자료를 수집하거나 읽지 않았다. 초기 root는 `D:/univ/personal/lotto-pattern-lab`, branch는 `main`, clean SHA는 `01d2eb7ef04c20a8052ab577a405811df418d7dc`다.

## 사전 설계와 provenance

[사전 계획](superpowers/plans/2026-10-18-phase27.md)과 [immutable protocol](../reports/final_ensemble/protocol.json)을 replay·선택 전에 고정했다. 기존 Phase3/4·13·14·15·18 원문 및 canonical ledger를 감사했다. 당시 ledger 전체는 [provenance_before.json](../reports/final_ensemble/provenance_before.json)에 보존한다. 원문의 paired uncertainty·sensitivity·null evidence·정확한 과거 산출물 경로는 [후보 원장](weak-signal-candidates.md)의 기존 항목을 유지한다.

| 후보 | 출처 | 정확한 기존 설정 | 사전 포함 판단 |
|---|---|---|---|
| Gap Logistic | Phase3–4, 후속 비교 baseline | GAP6: current_gap/has_appeared/mean_gap/median_gap/gap_std/gap_ratio, Logistic C=1, seed42, expanding labels105..fit cutoff, cadence26 anchor901 | 여러 시작점의 약한 양의 점추정·재현 가능한 baseline; 주요 CI는0 포함 |
| GraphStructureModel | Phase14/H12 | W52, neighbor_community, communities3, graph threshold2 | 기존 exploratory ENSEMBLE CANDIDATE; 세 구간 Top6 방향 양호. W104 저하와 주요 paired CI0 포함을 그대로 인정 |
| GapShapeModel | Phase15/H13 | K25, sigma1, exclusion26 | 기존 exploratory ENSEMBLE CANDIDATE; 세 구간 방향 양호. K10 민감도·보정 null 근거 부재 인정 |
| MirrorModel | Phase18/H16 | W10, lag1, shrinkage200, support20 | 기존 exploratory ENSEMBLE CANDIDATE; 다른 순위 제공. 최근 약화와 W/lag 민감도 인정 |
| MutualInformationModel | Phase13/H11 | lag1, incoming3, training window624, context support20, shrinkage20 | **AUDIT_ONLY**. 기존 NOT CURRENTLY JUSTIFIED, 개발 절반 선택 불안정·early 부진. 높은 전체 점추정으로 재승격하지 않음 |

Graph/GapShape에 서로 다른 사후 sensitivity cutoff를 만들지 않았다. 네 모델은 **연구 조합에 포함할 후보**이며 검증된 예측 신호로 승격한 것이 아니다. 새로 포함할 다른 사전 승격 후보는 없었다. MI는 비교·다양성 감사에만 남긴다. Frequency26와 기존 seed42/stream10 RandomModel은 기준선이다.

원래 Graph/GapShape/Mirror/MI prediction/config CSV 일부가 checkout에 없었다. 문서에서 bytes를 복원하지 않고 기존 source와 동결 설정으로 **새 causal replay**를 만들었다. [predictions_26.csv](../reports/final_ensemble/predictions_26.csv)는 각 모델345targets, 총2415rows다. 7개 모두 원문 hit0..6 분포와 정확히 일치했다. 이것은 재현 근거지만 사라진 원본 bytes/hash 검증은 아니다. 후보 누출·재현 실패 시 선택을 차단하도록 했다. 원본 결과는 ledger에 별도로 보존한다.

## 공통 domain과 시간 분리

공통 평가 domain은 **901–1245, 345targets**다. 모든 후보가 이를 덮으므로 범위 부족으로 제외한 모델은 없다. 원래 base hyperparameter 선택은401–900이므로 이를 다시 H17 개발로 사용하지 않는다.

| 구간 | 대상 | 수 |
|---|---|---:|
| DEVELOPMENT | 901–1015 | 115 |
| VALIDATION | 1016–1130 | 115 |
| FINAL HISTORICAL TEST | 1131–1245 | 115 |

이 구간은 이전 Phase와 후보 적격 판단에서 이미 연구되었다. **Retrospective evidence이며 pristine holdout이 아니다.** 내부 선택 chronology를 지켜도 과거 연구 전체의 선택 편향은 사라지지 않는다. 115회 final의 effective blocks도 적다.

각T에서 source는 draw<T만 사용한다. Gap fit은901,927,…에서 직전까지의 labels로 수행한다. `include_current=False`로 실제1246뿐 아니라1246 feature row도 생성하지 않는다. 후보별 원래 tie rule을 보존한다. 비무작위 동점은 작은 번호, Random은 원래 seeded permutation이다.

## 조합·선택·validation

번호별 rank r을 `(r−1)/44`로 바꾸고 convex 평균 후 재순위화한다. 평균은12decimal precision으로 numerical ties를 정리하고 작은 번호 우선이다. Raw-score calibration, 원래 handcrafted features 추가, stacking은 하지 않는다. Stacking은 optional이며 이 표본에서 과적합 위험이 커 생략했다.

Primary objective는 **실제 조합 순위의 mean winning-number rank(MWR) 최소화**다. Top6는 secondary다. 동률은 높은 Top6, 적은 component 수, 사전 ID순이다.

- Equal-all4 기준선.
- Equal subsets: 6pairs+4triples+all4=11. 일반 선택과 diversity-aware 선택이 같은11개를 사용한다.
- Diversity objective: normalized MWR + `.02 × development 평균 positive Spearman`. 계수 하나만 사용한다.
- Weighted family: pair당50/50,60/40 양방향,70/30 양방향=30; triple당equal 및50/25/25 permutations=16; all4equal1. **47unique configurations**이며 중복된 equal 비교를 새 독립 검정으로 세지 않는다.

Development에서 primary weighted winner와 best single identity를 고정한다. Validation은 winner가 Gap·best single·equal-all보다 MWR가 엄격히 낮고 Top6가 각각 이상인지 확인한다. 자신과 비교하는 경우만 제외한다. **실패하면 equal-all4 audit baseline**으로 돌아가며 validation runner-up을 선택하지 않는다. 일반·diversity subset도 진단하지만 primary를 대체하지 않는다. Gate 실패 후 final이 좋아도 승격하지 않는다.

Protocol → development → validation → final-start hash chain을 보존한다. Final 모델선택 평가는 한 번만 실행했고 재실행은0회다. 이후 frozen rankings로 robustness·placebo·portfolio를 계산하며 선택을 변경하지 않는다.

## 불확실성·robustness·placebo

Final에서 Random·Gap·development-best single과 paired circular block-bootstrap2000(seed270042)을 수행한다. Block26 primary,13/52 sensitivity다. Top6 improvement는 ensemble−reference, MWR improvement는 reference−ensemble다. 명목95%와 **각 비교98.333% Bonferroni 구간**을 함께 기록한다. 후자는 metric별3references에 대해95% family-wise coverage를 목표로 한다. Top6와MWR를 합친6개 비교나 이전 연구 전체의 correction은 아니다.

동결 weights로 세 구간, final starts1131/1170/1208, Gap cadence13을 비교한다. Leave-one-component-out은 남은 weights를 재정규화하고 Top6/MWR 변화 및 fullensemble와 Spearman을 보고한다. 결과로 실제 동결 조합을 수정하지 않는다.

Random-weight199(seed270101): 원래47cell과 동일 support/예산을 사용하되46개 weights는 Dirichlet(1), equal-all은 유지한다. Random-candidate199(seed270202): target마다 네 모델에 같은 번호-label permutation을 적용하여 순위분포·모델간 diversity를 보존하고 winner alignment를 제거한다. 둘 다 동일 development selection/validation gate/fallback을 수행하며 gate실패도 분모에 포함한다. Final은 placebo 선택에 쓰지 않는다.

이는 selection diagnostics다. Fixed grid와 random grid가 exchangeable하지 않으므로 tail fractions를 calibrated frequentist p-value로 부르지 않는다. 실제 gate실패 시 promoted gain=0, promotion tail inference는 생략한다. Raw fallback gain은 따로 기술한다. 전체 과거 model discovery의 null calibration은 아니다.

## Portfolio와 freeze

기존 portfolio primitive만 사용한다. Top12 pool의924조합, rank score `(46−r)/45`, weighted/coverage, 20unique tickets의 prefix로 예산1/5/10/20을 맞춘다. Selected ensemble weighted/coverage, Gap weighted, best single weighted, uniform random을 비교한다. Seed270500+replicate+target,10replicates를 공유한다. Mean best main matches,≥4/≥5,5+bonus의2nd-equivalent,5/no-bonus의3rd-equivalent를 보고한다. Seed replicate를 추가 독립 draw로 세지 않는다. 희귀 당첨은 기술적 결과다.

해석 예시는 결과와 무관하게1131/1188/1245로 고정했다. [interpretability.csv](../reports/final_ensemble/interpretability.csv)에 각 번호의 component rank·contribution·disagreement·winner flag를 담았다. 인과적 이야기를 붙이지 않는다.

Validation·final·paired uncertainty·robustness·placebo 조건을 모두 만족해야 HISTORICAL_ENSEMBLE_ADVANTAGE다. 낮은 수준의 candidate도 validation과 final 방향을 요구한다. 그 외는 NO_ENSEMBLE_ADVANTAGE_ESTABLISHED다. Negative 결과의 configuration-only freeze는 감사용이며 **READY_FOR_1247=false**다. 실제1246 import/refit 또는1247 번호 생성은 이 Phase에서 하지 않는다.

Old prospective archive30files/12recorded hashes 및435개 기존 보호파일을 시작·종료 때 비교한다. 새 산출물은 `reports/final_ensemble/`에만 저장하며 old archive를 수정하지 않는다. 실행 명령과 최종 검증은 [결과](final-ensemble-results.md)에 있다.
