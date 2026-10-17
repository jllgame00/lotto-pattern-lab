# Phase 23 — Topological Data Analysis 방법

Canonical H22. 실제 자료는 본번호만 있는1–1245회이며1246회를 가져오거나 참조하지 않는다.
[실행 전 고정한 계획](superpowers/plans/2026-10-18-phase23.md) · [결과·검증](topology-results.md).
질문은 Lotto history의 cluster/연결 구조가 같은 Lotto 제약을 가진 random point cloud보다 persistent한지이다.
Persistence 자체를 dynamical attractor나 번호 예측력으로 해석하지 않는다.

## 의존성 및 구현 범위

기존 로컬 환경에 ripser, persim, gudhi가 모두 없다. 설치·네트워크 의존성 작업 없이 정확한 H0만 구현한다.
**H1_DEFERRED_DEPENDENCY_LIMITATION**이며 loop의 존재·부재를 판정하지 않는다.
Bottleneck/Wasserstein diagram distance도 구현하지 않는다. 아래 recurrence는 diagram distance가 아닌 summary vector 거리다.

H0의 Vietoris–Rips filtration은 거리 이하의 edge를 추가하면서 connected component의 합병을 추적한다.
Radius는0부터 해당 cloud의 최대 pairwise distance까지로 정의하며,edge length를 반으로 나누지 않는다.
이는 [GUDHI의 Vietoris–Rips 정의](https://gudhi.inria.fr/python/latest/rips_complex_user.html#definition)와 같은 edge-threshold convention이다.
H0의 finite death는 완전 metric graph의 MST edge weight와 같다. Dense Prim O(n²)으로 이를 직접 계산한다.
Duplicate point 사이의0 edge도 보존하고 tie는 고정 point 순서의 index로 결정한다.
각 n-point cloud에 birth0인 finite bar n−1개와 별도의 infinite component1개를 기록한다.
Infinite bar는 모든 finite summary에서 제외한다. MST tie의 특정 edge는 유일한 feature attribution이 아니다.

## 고정한 다섯 cloud/metric

| Config | Point | Distance / scaling |
|---|---|---|
| A_jaccard | draw별45 binary,행합6 | 1−intersection/union |
| A_hamming | 같은 draw binary | 서로 다른 좌표 수/45 |
| B_euclidean | sum,range,std,spacing mean,spacing std,consecutive-pair count,odd count | 해당 interval의 population mean/std로 표준화한 Euclidean |
| C26_euclidean | 서로 겹치지 않는26회 block의45번호 appearance rate | Euclidean |
| C52_euclidean | 서로 겹치지 않는52회 block의45번호 appearance rate | Euclidean |

A의 두 metric은 overlap의 단조변환이므로 독립 evidence가 아니다. B는 기존 frozen shape7을 재사용하며
spacing mean=range/5라는 중복도 보존한다. 상수 coordinate는0으로 만들고 추가 PCA/normalization/metric은 검색하지 않는다.
B의 scaling은 해당 interval 안에서만 추정하며 미래 suffix를 쓰지 않는다.

C는 interval 오른쪽 끝에 맞춘 complete block만 point로 삼고 왼쪽 incomplete block은 버린다.
Point stride=26/52로 cloud 내부의 관측 공유가 없으며 각 rate vector의 합은6이다.
Dense overlapping activity나 W10/cosine sensitivity는 추가하지 않았다.
서로 다른 rolling cloud 사이에는 관측 공유가 있으므로 독립 반복실험으로 취급하지 않고 null에도 같은 interval을 적용한다.

## Rolling 및 sample-size 제어

Whole와 W={208,416,624},endpoint stride104,각 W의 마지막1245/900 endpoint도 포함한다.
Full은27개 rolling fit+whole,development는18개+whole이다. Landmark나 point subsampling은 없다.

| Interval | A/B points | C26 points | C52 points |
|---|---:|---:|---:|
| whole1245 | 1245 | 47 | 23 |
| whole900 | 900 | 34 | 17 |
| rolling208 | 208 | 8 | 4 |
| rolling416 | 416 | 16 | 8 |
| rolling624 | 624 | 24 | 12 |

Real과 모든 surrogate는 각 config/interval cell에서 point 수가 정확히 같다.
Raw whole persistence와208-point persistence를 직접 비교하지 않는다. Family search는 cell별 독립 pilot의 center/scale로 비교한다.
C52/W208은4points뿐이므로 해석력이 약하다. 더 유리한 결과를 위해 overlap을 되살리거나 sample 수를 바꾸지 않는다.

각 cloud의 median pairwise distance,median nearest-neighbor distance,distance variance,NN/median,
distance CV,중복·등거리 여부를 저장한다. 여기의 CV는 std(distance)/median(distance)인 descriptive normalized spread다.
통상적인 std/mean CV와 구분한다. CV<.1은 descriptive concentration 표시일 뿐 검정 family가 아니다.
Median0이면 비율은 미정이며 high-dimensional 등거리 구조에 topological 의미를 강제하지 않는다.

## Primary summaries와 완전 null 검색

Finite lifetimes d에 대해 네 family만 사용한다.

1. `h0_longest`: max(d).
2. `h0_total`: sum(d).
3. `h0_entropy`: −sum(p log p),p=d/sum(d);0 bar는 entropy weight0.
4. `h0_tail`: 큰 ceil(.1×(n−1))개 lifetime의 합/전체 합.

전체 lifetime이0이면 entropy와 tail은0이다. 별도 persistence threshold나 rolling family를 추가하지 않는다.
Full140cloud×4=**560cells**(family당140),development95×4=**380cells**(family당95).

각 cutoff별 independent IID32pilots,seed231001로 cell의 mean/std를 고정한다.
Finite≥24/32,std>1e−12인 cell만 검정한다. Constant/tied cell은 제외하고 개수를 보고한다.
세 family는 상방 z,entropy는 |z|로 양방향 anomaly를 검정한다.
Pilot 크기는 작으며 z를 Gaussian p로 바꾸지 않는다.

Main seed230042,**199 IID+199 fixed-margin** histories를 각각 full/dev에서 생성한다.
Child seed는 SeedSequence([seed,nullcode,replicate,cutoff])로 고정한다.
Fixed-margin은 기존 Curveball로 행합6과 해당 실제 prefix의 번호별 총빈도를 보존한다(row당20trades).
유한 trade 횟수의 mixing 한계는 남는다.
모든 surrogate가 자체 binary/cloud/scaler/distance/MST/모든 rolling cell을 새로 만들고 자신의 family global maximum을 찾는다.
두 scope의 key/point-count inventory 일치를 확인한다.

Empirical p=(1+null maximum≥real maximum 횟수)/200,**Bonferroni4**를 각 scope/각 null에 적용한다.
최소 raw p=.005,보정 p=.020이다. 두 null의 같은 family가 모두 보정 p≤.05여야 gate를 통과한다.
Cell별 observed−null median과 percentile도 저장하지만 local percentile을 global 검정 근거로 올리지 않는다.

## 시간 변화·기존 결과와의 관계

Rolling feature=[longest,total,entropy,tail]. 같은 config와 같은 W의 시점만 모아 표준화하고
endpoint index lag={1,2,4}의 Euclidean summary 거리를 descriptive recurrence로 저장한다.
최종 irregular endpoint와 rolling overlap도 real/null에 같으며 작은 거리를 유의한 재귀로 부르지 않는다.

Manifest hash로 검증한 Phase22 `interval_summary.csv`에서 같은 W/endpoint의 largest eigenvalue·effective rank와
B-shape H0 longest의 Spearman을 W별로 계산한다.
Phase14 `graph_rows.csv`가 있으면 같은 endpoint의 Graph W104 concentration과 topology W208을 비교한다.
이 Graph 비교는 interval 길이가 서로 다르다는 한계가 있다. Endpoint1244와1245를 같게 취급하지 않는다.
Graph/RMT를 refit·retune하지 않으며 cross-method correlation은 독립적인 검정 evidence가 아니다.
A의 한 MST merge edge에 관련된 draw/번호는 inspection만 제공한다. 유일한 persistent number group은 식별하지 않는다.

## Development gate 및 prospective

설정은 개발1–900에서만 고른다.901–1245는 이후 historical 진단이며 이전 연구에서 이미 본 구간이므로 pristine holdout은 아니다.
개발 corrected gate 실패면 **PREDICTIVE_MODEL_NOT_JUSTIFIED**로 종료한다.
구조가 통과해도 번호 outcome으로의 causal mapping은 별도다. 사전 계획의 rolling regime/mapping gate까지 통과해야 모델을 만든다.
Whole-only winner는 rolling regime predictor의 근거가 아니다.
모델이 없으면 Random/Frequency26/Gap Logistic walk-forward,paired uncertainty,후보 rank correlation,1247 capability를 만들지 않는다.
H17은 BACKLOG로 남는다.

Source loader는 정확한 canonical1–1245만 허용한다.1246 target은 거부한다.
Archive 부재 상태는 **PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**이며 실제 publication command가 없다.

## 재현·감사

`python main.py topology {calibrate,benchmark,analyze,select,diagnostics,audit}`를 순서대로 사용한다.
분석199/null,workers3,pilots32가 canonical 설정이다. 기존 완성·부분 결과는 덮어쓰지 않는다.
양 scope의 pilot count/seed와 calibration 파일 hash를 검증하고 selection 전에 input hash와 null inventory를 확인한다.
감사는64pilots 전부와 대표 main8histories를 seed 재생하고,저장된796null vectors의 own-max/p 계산을 모두 재검산한다.
실제 full/dev의235cloud는 독립 shape/scaling,SciPy distance,Kruskal로 Prim H0를 검증한다.
398개 main history 전부를 재생한 것은 아니다. Canonical CSV·이전 artifact hash·HEAD·변경 파일도 확인한다.
