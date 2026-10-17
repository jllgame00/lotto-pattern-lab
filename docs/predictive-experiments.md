# Phase 3 — Causal ranking 예측 실험

## 결론과 현재 경계

Phase 3 역사 결과입니다. 이후 fixed research seal은 CLI를1..1244회로 제한하고 canonical current prediction을 막습니다. 현재 protocol·한계는 [Gap / prize](gap-prize-research.md)를 참고합니다. H2는 TESTED / INCONCLUSIVE입니다.

chronological ranking 탐색이며 fitted score는 Lotto 예측 가능성의 증거가 아닙니다. hyperparameter search·마지막 draw 최적화·neural network·HMM·web frontend는 추가하지 않았습니다.

## CLI

```powershell
python main.py compare-models --ablations --tickets 20
python main.py predict-current --model logistic
python main.py explain-number 17 --neighbors 10
python -m pytest -q
```

optional tree backend는 package access가 있을 때 `python -m pip install -r requirements-ml.txt`입니다. LightGBM을 쓸 수 없으면 XGBoost를 명시 설치하며 둘 다 있으면 LightGBM 우선입니다. missing library는 console/metadata에 기록하고 zero performance나 다른 classifier로 대체하지 않습니다. SciPy logistic·similarity는 core requirements만 필요합니다.

당시 scikit-learn·LightGBM·XGBoost가 없었고 pip index가 비활성화되어 PyPI HTTPS도 WinError10061로 실패했습니다. 환경 제한을 해제하지 않았습니다. Random Forest·boosting은 평가하지 못했고 integration test는 명시 skip했습니다. 이 검증 한계는 유지합니다.

## 데이터 및 사전 평가 protocol

feature history104 draws, 첫 supervised target 105입니다. evaluation601..penultimate1244이며1245는 comparison에서 제외했습니다. 매26 targets마다 `target_draw < current_target`의 모든 label로 refit하고 그 사이 current feature만 갱신합니다. `--start`, `--end`, `--cadence`, `--seed`는 명시하며 random row split은 없습니다.

target 601은 label·feature cutoff600입니다. 602..626은 fit/scaler/neighbors600을 유지하고 feature는 직전 draw까지 갱신합니다. 627은626까지 refit합니다. 모든 모델에 같은 feature를 주고 `score_rows`에 target outcome을 넘기지 않습니다. 기존 stateless RandomModel engine은 그대로입니다.

당시 `predict-current`는 reserved draw까지 포함한 모든 labeled opportunity로 다음 scheduled draw를 기술했습니다. 다음 결과로 평가·tune한 것이 아니며 default는 fixed Logistic, 역사 winner가 아닙니다. 현재 seal 때문에 canonical 실행은 차단됩니다. 1246회는 현재 알려진 결과로 새 prospective 대상이 아닙니다.

## 데이터 표현과 핵심 feature

`src.analysis.features.build_features`는 source 검증 후 target/number별 row를 만듭니다. 본번호만 positive이며 label join 전에 feature를 계산합니다. prefix invariance·target poisoning을 테스트하고 retrospective calendar/regime table을 입력에 합치지 않습니다.

full set은31 predictor columns입니다. categorical identity, frequency12개(count/rate 5/10/26/52/104·10-to-104 ratio·직전 두 출현), gap 6개(current·ever-appeared·completed mean/median/population std·current/mean), periodicity/regime8개, cyclic calendar4개입니다. count/rate는 scaled redundancy이며 독립 근거가 아닙니다. interaction·hyperparameter search는 없습니다.

periodicity는 trailing104와 Phase 2 guard만 사용하고 unsupported는 missing입니다. 최소52 earlier supported scores의90th percentile 초과가 세 번 연속일 때 strong regime입니다. age는 세 번째 endpoint에서 zero부터 시작하며 과거 start로 소급하지 않습니다. time-since는 최초 confirmed 전에는 missing, confirmed 중 zero, 이후 draw 수입니다. `strong_regime=0`에는 history 부족도 포함됩니다. causal descriptor이며 recurrence prediction이 아닙니다.

gap std는 completed gap 두 개가 필요합니다. never-seen current gap은 absence lower bound이며 `has_appeared=0`으로 구분합니다. training-only median imputation, 전부 missing이면 zero, 이후 training population z-score입니다. vocabulary1..45는45 one-hot으로 바꾸고 ordinal slope를 쓰지 않습니다. month/ISO week는 sine/cosine, raw 값은 export에 남깁니다.

metadata는 target number/date·cutoff·month/week·`appeared_next`이며 feature group은 label·draw ID를 제외합니다. 31 raw predictor는 identity encoding 후75 columns입니다. calendar-only pooled score는 target의45번호가 동률이라 deterministic tie의 고정 ticket이며 번호별 seasonal effect를 학습한 것이 아닙니다.

## 계산 방법 — 모델

- Similarity: 같은 번호만 비교하며 training median/scale·Euclidean30 neighbors를 사용합니다. feature subset·K·Euclidean/Manhattan·uniform/distance 설정이 있습니다. `1/(1+d)` weight 합을 neighbor 수로 맞추며 score는 `(weighted appearances + 2)/(neighbor count + 15)`, prior mean6/45입니다. neighbor target/date·cutoff·distance·outcome을 설명하고 refit 사이 새 outcome은 neighbor에 넣지 않습니다.
- Pooled Logistic: SciPy L-BFGS로 mean binary log loss + `||w||²/(2*C*n)`, C=1, unpenalized intercept, no class weighting입니다. convergence failure는 error이며 signed standardized coefficient는 causal importance가 아닙니다.
- Random Forest: sklearn100 trees·depth4·min leaf50·sqrt feature·one thread·fixed seed입니다.
- Boosting: LightGBM100 trees·rate .03·7 leaves·depth3·min leaf100·L2=1·one thread·deterministic입니다. 명시 XGBoost fallback은100 trees·.03·depth3·min child weight15·L2=1·histogram·one thread·fixed seed입니다.

의존성이 있으면 cutoff마다 tree importance를 export합니다. SHAP·cross-number similarity는 추가하지 않았습니다.

## 평가 지표와 불확실성

45번호를 ranking합니다. predictive model의 Top6 tie는 작은 번호 우선, RandomModel은 seeded uniform ticket과 ticket 안/밖 random order입니다. uniform score와 sampled ranking을 모두 기록하며 Random ranking에 deterministic tie를 쓰지 않습니다.

mean hits·0..6 histogram·3+/4+/5+ rate·best·winning mean rank·Recall@6/10/15입니다. uniform expectation은 hit0.8, rank23, Recall@k=k/45입니다.

weighted ticket은 별도 stream입니다. nonnegative score 정규화 후0.1% uniform mixture로 sparse score에서도 여섯 개를 고르고 target/ticket seed로 without replacement sampling합니다. deterministic ranking metric을 대체하지 않습니다. score는 externally calibrated probability가 아니고 sampling도 calibration이 아닙니다.

같은 target 수의 exact hypergeometric hit로 random2,000 runs를 만듭니다. target별 seeded RandomModel과 paired 비교하며 mean-hit·difference는 block26의 circular moving-block bootstrap 2,000회입니다. early/middle/recent도 보고합니다. interval은 familywise 보정 전 기술값이고 random tail에는 learned specification별 Bonferroni도 표시합니다. random policy reference이지 learned predictability의 일반 증명은 아닙니다. 작은 차이·좋은 한 block은 충분하지 않습니다.

일곱 feature ablation은 같은 protocol·fixed Logistic입니다. `ablation_differences.csv`는 frequency+gap+periodicity 대 frequency+gap의 mean-hit paired interval·ranking 차이를 저장합니다. 사전 incremental 비교이며 best group을 후속 tuning·latest draw에 선택하지 않습니다.

## 출력 파일

default는 `reports/prediction/`, override는 `--reports-dir`입니다.

- `features.csv`: supervised 전체, `feature_sample.csv`: 첫10 targets입니다.
- `comparison.csv`: ranking/uncertainty, `time_blocks.csv`: 시기 안정성입니다.
- `prediction_audit.csv`: model/target별45 scores·ranking·Top6·actual·hits·feature/fit cutoff·seed/config입니다. `--no-audit`는 상세 score/outcome/config를 생략하되 target metric은 유지합니다.
- `feature_importance.csv`: cutoff별 signed coefficient/tree importance입니다.
- `ablation_differences.csv`: incremental periodicity입니다.
- `experiment.json`: protocol·source hash·availability·versions·dimensions·runtime·bootstrap/simulation·주의사항입니다.

canonical/provenance 경로는 report overwrite에서 보호합니다. report는 로컬 Git-ignored 산출물이며 당시 commit/push는 없었습니다.

## 주요 결과 — 최초 실행 (2026-10-17)

명령은 `python main.py compare-models --ablations --tickets 20`입니다. source1,245 draws, 2002-12-07–2026-10-10, SHA256 `b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e`를 유지했습니다. 51,345 supervised rows·37 total columns(31 predictors), 601..1244의644 targets·specification별25 expanding fits입니다. 1245는 평가하지 않았고 configuration tuning도 없었습니다.

| Model/group | Mean hits | Recall@6 | Recall@10 | Recall@15 | Mean winning rank |
|---|---:|---:|---:|---:|---:|
| RandomModel | .798137 | .133023 | .224120 | .338768 | 22.933230 |
| Same-number similarity, full | .777950 | .129658 | .219462 | .329451 | 23.310300 |
| Logistic, frequency | .781056 | .130176 | .214803 | .330745 | 23.253623 |
| Logistic, gap | .849379 | .141563 | .228261 | .340839 | 22.754917 |
| Logistic, periodicity | .824534 | .137422 | .228261 | .346791 | 22.552277 |
| Logistic, calendar | .767081 | .127847 | .213251 | .333333 | 23.042961 |
| Logistic, frequency + gap | .781056 | .130176 | .222826 | .327122 | 23.024845 |
| Logistic, frequency + gap + periodicity | .796584 | .132764 | .227484 | .336957 | 22.671066 |
| Logistic, full | .796584 | .132764 | .221532 | .329451 | 22.981884 |

Random Forest·두 boosting package는 사용 불가로 평가하지 않았습니다. Logistic 수치는 위 SciPy 구현입니다.

모든 learned specification의 Random 대비 paired95% hit interval은 zero를 포함합니다. gap-only 최대 평균의 차이는 +.051242, interval[-.035714,.139790], upper-tail .055972·Bonferroni .447776입니다. 예측 우위가 확립되지 않았습니다. gap의 early/middle/recent 차이는 -.046512,+.097674,+.102804, similarity는 -.139535,+.060465,+.018692, full Logistic은 -.088372,+.088372,-.004673입니다. 안정적 우위가 아닙니다.

사전 periodicity increment는 +.015528 hit, paired95%[-.054348,.090062]입니다. block 차이는 +.013953,+.074419,-.042056입니다. mean winning rank는 .353778 개선(낮을수록 좋음)했지만 interval[-.711704,.002899]도 zero를 포함합니다. Recall@6/10/15 incremental interval도 모두 zero를 포함합니다. 여러 metric의 uncorrected interval이며 신뢰할 incremental value는 확립되지 않았습니다.

random2,000 runs 평균은 .799244(theory .8),644-ticket run의95% range[.737578,.860248]입니다. 전체 histogram·3+/4+/5+는 comparison.csv에 있습니다. 아홉 specification의 best deterministic은 four hits, five/six-hit ticket은 없었습니다.

runtime은 **163.349 seconds**, feature47.380s·similarity35.562s·full Logistic29.911s, 나머지 ablation4.2..11.4s입니다. 이전 diagnostic-heavy 시도는 결과 전에 취소했습니다. scoring에서 불필요한 neighbor explanation을 제거해 score·protocol은 유지했습니다. 이후 ranking bootstrap column도 저장 audit로 계산했고 refit·새 selection은 없었습니다.

model-target audit5,796 rows·coefficient3,725·time-block27·별도 weighted tickets115,920개를 저장했습니다. 당시 독립 artifact 확인으로 outcome/hit·45 scores/ranks·six unique choices·26-draw fit cutoff를 재구성했고 reserved draw를 유지했습니다.

당시 `predict-current --model logistic`은 cutoff1245·scheduled1246으로55.17s에 실행했습니다. 권장·검증 ticket이 아닌 실험 출력입니다. `explain-number 17 --neighbors 5`도 확인했으며 source data는 바꾸지 않았습니다. 현재는 위 seal과 [prospective workflow](prospective-workflow.md)를 따릅니다.

## 해석·한계·다음 단계

초기 optional backend 검증 한계와 historical selection/multiplicity를 유지합니다. 수익성의 근거가 아닙니다. 이후 완료된 robustness·pool·prize 비교는 [Gap / prize](gap-prize-research.md), regime은 [Phase 4](regime-research.md)에 있습니다.
