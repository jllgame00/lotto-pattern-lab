# Phase 13 — H11 Mutual Information / Transfer Entropy 방법

질문은 “한 번호의 과거가 다른 번호의 미래 uncertainty를 줄이며, target 자신의 과거를 넘어서는가?”이다.
MI의 dependence, 조건부 predictive information, 인과관계는 구분한다. 정보량이 양수인 것만으로
전달·예측 우위·causal effect를 선언하지 않는다.
[사전 실행 계획](superpowers/plans/2026-10-18-phase13.md)을 결과 계산 전에 기록했다.

## 입력과 시간 정렬

canonical history1–1245회 본번호의45개 binary series만 사용한다. bonus는 제외한다.
각 행의 active6개 제약을 검증하고1246행을 포함한 matrix를 거부한다.
strict CSV reader는 header+1245행까지만 읽고 byte길이로 unknown suffix를 거부한다.
fetch/import·외부 회차 조회 경로가 없다.

lag는 **1,2,3,4,8,13,26**이다. MI는 X_i(t−lag)와 X_j(t)를 비교한다.
양 변수에 대한 MI 대칭성과 time-delayed source/target 교환은 다르므로 directed pair로 검색한다.
동일 번호의 self-lag MI는 별도 reference이며 primary cross maximum에 포함하지 않는다.

TE의 target history k와 source history l은 각각 **1 또는2**다.
source code S_i(t)=Σ(r=0..l−1)2^r X_i(t−lag−r),
target code Z_j(t)=Σ(r=0..k−1)2^r X_j(t−1−r), future는 Y_j(t)=X_j(t)다.
가장 최근 bit가 least significant bit이며 첫 유효 t=max(lag+l−1,k)다.
여기서 t는0-based array index다. 불완전 이력, wrap, 미래 state는 사용하지 않는다.
CMI는 k=l=1의 TE와 같으며 독립적인 반복 확인이 아니다.

## Auditable discrete estimator

모든 정보량은 bits다. MI=Σp(x,y)log2[p(x,y)/(p(x)p(y))],
TE=I(S;Y|Z)=H(S,Z)+H(Y,Z)−H(Z)−H(S,Y,Z)다.
45×45 pair의 one-hot joint count를 NumPy matrix product로 한꺼번에 계산한다.
MI count array는[source,target,sourcebit,futurebit], TE는[source,target,sourcehistory,targetpast,future]다.
제로 cell을 버리거나 pseudocount로 raw 정보량을 인위적으로 높이지 않는다.
joint/marginal counts와 raw/corrected 값·support·occupied states를 저장한다.

occupied-state Miller–Madow entropy 보정 H_MM=H_plugin+(q−1)/(2Nln2)를 각 entropy 항에 적용한다.
MI correction=(q_X+q_Y−q_XY−1)/(2Nln2),
CMI correction=(q_XZ+q_YZ−q_Z−q_XYZ)/(2Nln2)다.
corrected 값의 음수도 보존한다. sparse regime에서 이 근사는 완전한 bias 제거가 아니며 p-value도 아니다.
primary MI/CMI/TE maximum은 raw 값이며 finite-sample bias를 같은 전체 null 탐색으로 제어한다.
양의 Miller–Madow 값만 사용하는 모델 weight는 별도의 training 휴리스틱이다.

support는 정렬 표본N>=300, target future의0/1 각각>=20이다.
MI는 source0/1 각각>=20도 요구한다. TE는 가능한 모든 source history 및 target history marginal state가
각각>=8일 때만 eligible이다. occupied joint cell 중 하나라도<5 또는 occupied fraction<0.8이면
sparse flag를 붙인다. sparse flag와 eligibility는 별개이며, 경고를 숨기려고 state를 합치지 않는다.
rolling에서도 동일 filter를 적용해 충분하지 않은 설정은 계산값을 evidence/그림 선으로 쓰지 않는다.

## 사전 탐색 공간과 primary families

| 항목 | 후보 수 |
|---|---:|
| directed cross pairs | 45×44=1,980 |
| unordered asymmetry pairs | 990 |
| lag | 7 |
| k/l history | 4 |
| cross MI | 13,860 |
| self MI reference | 315 |
| CMI (k=l=1) | 13,860 |
| TE | 55,440 |
| absolute directional asymmetry | 27,720 |
| temporally stable TE | 55,440 |
| primary family별 후보 cell 합계 | 166,320 |

CMI는 TE의 부분집합이고 각 family 후보는 독립 검정 개수가 아니다.
행렬 연산은 diagonal을 함께 산출하지만 TE diagonal은 evidence에서 제외한다.
MI self reference315개는 primary합계 밖에 보존한다.

다섯 primary family:

1. 모든 cross number/lag 중 최대 raw MI.
2. 모든 cross number/lag 중 최대 raw CMI(k=l=1).
3. 모든 cross number/lag/k/l 중 최대 raw TE.
4. 같은 lag/k/l의 |TE(i→j)−TE(j→i)| 최대. 두 방향 모두 eligible이어야 한다.
5. early1–415, middle416–830, recent831–1245에서 같은 pair/config의
   correctedTE 최솟값을0 이상으로 자른 stability score의 최대.
   세 구간 모두 두 방향 support를 통과하고 forward rawTE>reverse rawTE일 때만 후보다.

stable family의 세 era는 추가166,320개 cross TE 평가를 포함한다.
support/방향 filter 통과 개수는 history마다 다르며 실제·null의 eligible count도 따로 기록한다.
surrogate에 같은 후보 전체를 탐색할 권리를 준다.

## Bias와 두 종류의 temporal randomization

primary global null은 기존 **IID Lotto199회 + fixed-margin199회**, seed130042다.
fixed-margin은 기존 Curveball row당20 trades로 row6개·각 번호의 전체 빈도를 보존한다.
유한 mixing의 한계는 남는다. 각 surrogate에서45개 series·MI/TE·세 era·support filtering을 새로 만들고
자신의 최고 pair/lag/history 및 비대칭/안정성을 고른다. 실제 최고 위치를 null에 고정하지 않는다.
global p=(1+exceedance)/(199+1), family5 Bonferroni p=min(1,5p)다.
두 null을 모두 보고하며 유리한 것만 선택하지 않는다.

보조적으로 **source column별 circular shift19회**, seed130043, offset53..N−53을 사용한다.
source series의 자기 시간 구조와 전체 marginal 빈도는 유지하고 target 및 targetpast는 그대로 둔다.
잘린 alignment 구간의 count는 달라질 수 있어 같은 support filter를 다시 적용한다.
모든 tested MI/TE relation의 null 분포·평균·std·q95·raw-minus-null-mean·unadjusted local p를 저장한다.
eligible shift 수가 다르면 실제 분모를 기록한다.

source-only shift는 행당6개 조건을 보존하지 않으므로 **유효 Lotto history null이 아니다**.
이는 source/target 관계의 temporal randomization bias 진단이다.
선택된 pair의 local p는 global evidence가 아니며 최소 간격0.05로 정밀도도 제한된다.
primary 결론은 두 valid-history complete-search maximum의 family 보정을 기준으로 한다.
국소 분포는 NPZ 및 MI/TE bias CSV로 보존한다.

## 시간적 안정성과 핵심 조건부 질문

모든 primary leader에 대해 early/middle/recent 및416회 rolling windows(step104, 마지막1245 포함)에서
같은 pair/lag/k/l를 평가한다. forward/reverse, corrected, support, occupied/sparse를 기록한다.
이것은 선택된 관계의 descriptive 진단이며, primary stable-family global 검정과 구분한다.

유연한 empirical conditional table에서 target-history MLE logloss와 source-added MLE logloss의
in-sample 차이는 TE와 직접 연결되며 그 자체는 미래 성능이 아니다.
실제 source 추가 예측 근거는 별도 **이후** TargetHistoryBaseline 대비 logloss로 확인한다.
동시출현 제약, common input, 관측하지 않은 conditioning variable이 있으므로 bivariate TE가
물리적 causal influence를 식별했다고 주장하지 않는다.

## Causal MI / TE 모델

개발 target401–900, 이후901–1245. 이전 Phase에서도 사용한 역사이므로 pristine holdout이 아니다.
전체 descriptive/null 결과를 모델 설정 선택에 전달하지 않는다.
입력은 매 target T 직전의 정확한1..T−1 prefix이며 정보량·edge 선택·rate fit은 trailing624회에서 새로 한다.
cache key는 해당 prefix bytes·shape·lag/k/l이며 incoming3/5 간 같은 training table만 공유한다.
full-history 정보량/edge cache는 예측에 들어가지 않는다.

MutualInformationModel은 eligible cross incoming edge 중 양의 Miller–Madow 값과 현재 source state context support>=20을
만족하는 source를 고른다. 최대K=3/5, tie는 source번호 오름차순이다.
P(Y=1|current source)를 overall target rate로 prior20 shrink하고 positive corrected MI로 정규화 가중 평균한다.
없으면 같은 lag alignment의 overall target rate로 fallback한다.

TransferEntropyModel은 같은 support/topK 규칙을 적용하되 context가 source history와 current target history의 조합이다.
target-own conditional P(Y|Z)는 prior20으로 overall target rate에 shrink한다.
source-added P(Y|S,Z)는 prior20으로 이 target-own baseline에 다시 shrink한다.
각 edge의 baseline 대비 차이를 positive correctedTE로 평균한다. edge가 없으면 target-own baseline이다.
one sparse edge가 지배하지 않도록 최소 context20과 shrinkage20을 고정했다.
각 score는[1e−6,1−1e−6]로 제한하며, 합이6이어야 하거나 calibrated Lotto probability라는 주장은 하지 않는다.

MI 후보14=lag7×K2, TE 후보56=lag7×k/l4×K2다.
context support20, shrinkage20, positiveMM weighting은 사전 고정했으며 이후에서 조정하지 않는다.
개발500개 목표 Top6 평균, tie선언순서로 설정을 선택한다.
이후 평가 전에 exclusive configuration JSON/hash를 만들고 평가 전후 byte 불변성을 검사한다.
모든 번호의 순위를 내며 Top6 tie는 기존 번호 오름차순 규칙이다.

## Walk-forward와 정보 차별성

RandomModel·Frequency26·기존 Gap Logistic·MI·TE 및 **TargetHistoryBaseline**을 같은345개 목표에서 비교한다.
target-only baseline은 선택된 TE의 lag/k/l·training prefix·alignment·shrinkage와 정확히 같고 source만 제거한다.
각 회차45개 번호의 평균 binary logloss로 TE−target-only 차이를 구한다. 이때 bootstrap 단위는45개 번호가 아닌 **회차**다.

평균Top6, hit0–6분포, Recall@6/10/15, 평균 당첨번호 순위,
Top8/10/12/15>=5 및 Top6/8/10/12/15 all-six 사건을 저장한다.
Random·Gap 대비 paired circular block bootstrap2,000회, block26/13의 명목95% 구간을 보고한다.
모든 모델/metric/기간에 대한 동시 신뢰구간이 아니다. 희귀 사건의0 퇴화 구간은 확률0의 증명이 아니다.

Gap fit cadence26 및13을 비교하며 정보 모델은 매 target 재계산한다.
공통 evaluator의 cadence prefix검증 fit은 `outer_fit_cutoff`에 보존한다.
정보 모델과 target-history ablation의 실제 `training_cutoff` 및 `information_training_cutoff`는
모두 `feature_cutoff=T−1`이며, Gap의 `training_cutoff`는 실제 cadence fit cutoff다.
early901–1015/middle1016–1130/recent1131–1245 및 시작1001/1101의 같은 고정 예측열 subset을 보고한다.
사전70개 후보의 later sensitivity는 진단용이며 이후 점수로 동결 설정을 바꾸지 않는다.
Gap과 번호 좌표를 정렬한 Spearman 및 Top6/10/15 overlap을 계산한다.
낮은 상관만으로 ensemble 후보 자격을 주지 않는다. final ensemble은 만들지 않는다.

## 시각화와 prospective

heatmap·lag profile·temporal stability·두 global null·training-only directed edge inspection·역사 ranking을 저장한다.
edge 그림은 frozen TE 설정과 training<=900 자료만 쓰고 correctedTE 상위10개를 원 위에 표시한다.
유의한 edge의 증거가 아니며 community/centrality/hypergraph 분석을 하지 않는다.
예측 예시는 역사 target1245이며 <=1244로 재계산한 score가 실제 저장 예측과 일치해야 한다.

`draw1247_phase13_informationflow` 준비 gate는 설정 로딩 및 이전 archive의 원본 inventory·phase verifier 검증까지다.
archive가 없으면 **PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**으로 거부한다.
1246 target은 거부한다. 이 단계는1246 import/refit나 실제1247 snapshot 발행을 하지 않는다.

```powershell
python main.py information-flow benchmark
python main.py information-flow analyze --surrogates 199 --workers 4
python main.py information-flow select
python main.py information-flow compare --cadence 26
python main.py information-flow compare --cadence 13
python main.py information-flow sensitivity
python main.py information-flow plots
python main.py information-flow prepare-freeze
```

기존 `.deps/docs-checks`를 PYTHONPATH에 사용하고 BLAS thread1로 제한했다. 새 패키지를 설치하지 않는다.
binary series, joint tables, raw/corrected/support arrays 및 source-shift 분포를 cache/artifact로 저장한다.
surrogate representations는 history마다 한 번 만들고 계산 중 재사용하며 hash를 보존한다.

TE의 정의와 time-delayed MI와의 구분은 [Schreiber (2000), 원 논문](https://arxiv.org/abs/nlin/0001042),
유한 표본 bias 및 entropy 보정의 한계는 [Paninski (2003), 원 논문](https://www.cns.nyu.edu/pub/lcv/paninski-infoEst-2003.pdf)을 참고했다.
이 문헌은 Lotto 예측 가능성의 근거가 아니며, 판정은 현재 complete-search null 및 causal 이후 평가에 따른다.
