# Phase18 — Symmetry / Reflection / H16 방법

## 연구 질문과 경계

고정 중심23의 reflection이 동일 제약의 random Lotto보다 강한 동시 출현·lag 관계·
co-movement·anti-symmetry를 가지는가를 검증한다. 역사 자료는 bonus를 제외한1–1245회다.
실제1246은 fetch/import하거나 설계·선택·평가에 쓰지 않는다. H17 final ensemble은 구현하지 않는다.

primary transform은 mirror(n)=46−n이다. 1↔45,…,22↔24의22쌍과 self-reflected23을 구분한다.
입력은 exact integer1–45이며 wrap/clip은 없다. dynamic center 탐색은 하지 않는다.

## Same-draw symmetry와 side balance

draw의 complete mirror pair 수를 P,23 포함 여부를 C라 두면 paired numbers=2P다.
primary draw symmetry=2P/(6−C)이며23 자체를 matched pair로 세지 않는다.
Jaccard(A,M(A))=(2P+C)/(12−2P−C)는 self point를 포함한 별도 set similarity다.
below23/above23 counts와 absolute imbalance는 side balance다. balance와 mirror symmetry를 동일시하지 않는다.

정확한 IID joint distribution은 s=6−2P−C에 대해
Pr(P,C)=choose(22,P)×choose(22−P,s)×2^s/choose(45,6)다.
따라서 E[P]=1/3, E[paired numbers]=2/3, Pr(C=1)=6/45다.
left/right/center 분포는 choose(22,left)choose(22,right)/choose(45,6),left+right+C=6이다.
한 draw 안의 여러 pair를 독립 표본으로 취급하지 않는다.

## Lag·activity·방향성

lag={0,1,2,3,4,8,13,26,52}다. source draw t와 future t+lag를 정렬한다.
lag0은 같은 draw에서 source가 이미 포함되어 있으므로 nontrivial target의 IID 조건부 기대율은5/44다.
양의 lag는6/45다. center23은 별도 reference table에 저장하며 lag0의 당연한 hit율1은 primary에서 제외한다.

pooled relation은44 non-center source의 event/hit를 합친다. pair-specific 관계는
1→45,45→1,2→44,44→2,… 순서로44방향을 유지한다.
pair risk difference는 hit/source−baseline이다. 양의 lag의 baseline은 정렬된 future target의
번호별 출현율이며 lag0은5/44다. source support20 미만은 primary pair 후보에서 제외한다.
directional asymmetry는 두 조건부 hit율의 절대 차이다. lag0 asymmetry도 reference로 검색하지만,
source marginal 차이만으로 생길 수 있으므로 directional information flow라고 부르지 않는다.

working binomial z는 raw 진단값이며 p-value가 아니다. within-draw/lag 공유에 따른 의존성은
complete-history null로 처리한다. pooled95% 구간은 draw 단위 event/hit를 함께 resample하는
circular block52 bootstrap1000개(seed180077)다. 이 구간은 post-selection/다중 lag 보정 구간이 아니다.

activity W={10,26,52}는 completed anchor를 포함한 rolling appearance rate다.
OwnActivity,MirrorActivity,Difference=Mirror−Own,Sum=Mirror+Own을 제공한다.
Pearson co-movement는22쌍×3W에서 lag0 한 방향,양의8lags 양 방향을 계산한다.
정렬된 rate points26개 미만 또는 상수 series는 undefined로 제외한다.
겹치는 rate window는 강한 autocorrelation을 스스로 만들므로 null도 원시 draw에서 rate를 재구성한다.

## Regime와 secondary shift

regime W={26,52,104},endpoints=W,W+26,…와 최종 cutoff다.
mean pair 수,mean draw symmetry,mean absolute side imbalance,mean binary mirror correlation을 기록한다.
마지막 지표는 해당 window에서 양쪽이 variable인 pair12개 이상일 때만 정의한다.
높은 imbalance regime를 높은 mirror symmetry라고 해석하지 않는다.

secondary T_k(n)=46−n+k,k={−4,−2,0,2,4}를 별도 family로 검색한다.
범위 밖 target은 버리고 cyclic wrap/clip하지 않는다. primary와 같은 source population을 위해
source23과 각 transform의 fixed point를 제외한다. 다른 source가 target23으로 매핑되는 것은 허용한다.
유효 source/target labels,event/hit/aligned-draw counts를45개 shift×lag table에 저장한다.
이 작은 사전 shift set 이외의 center/shift는 탐색하지 않으며 shifted predictor는 만들지 않는다.

## Exact complete-search 공간

| Family | 후보 | 전체1245 | 개발900 |
|---|---|---:|---:|
| same_draw |mean pairs/mean symmetry/mean Jaccard/fraction pairs≥2|4|4|
| pooled |9lags의 pooled risk|9|9|
| pair |44×9 directional risk +22×3×17 positive activity correlations|1518|1518|
| asymmetry |22pairs×9lags|198|198|
| regime |4metrics×rolling windows|560|404|
| anti |396 negative pair risks+1122 negative activity correlations+9 negative pooled risks+mean imbalance|1528|1528|
| shift |5shifts×9lags|45|45|
| 전체 |7 families|3862|3706|

full rolling windows는140개,개발은101개다. shift0 pooled9개는 primary pooled의 reference를
포함하는 의도된 중복이다. positive/negative orientations도 구분해 검색한다.
이들을 독립 검정이라고 가정하지 않으며 Bonferroni는 이러한 의존성에서도 보수적으로 적용한다.
candidate key/eligible count/undefined mask를 저장한다.

## Calibration·null·보정

독립 IID32pilot을 길이1245와900에 각각 만든다(seed181001).
cell별 oriented mean/std를 고정하고 유효 pilot≥24, std>1e−12인 cell만 쓴다.
z=(oriented value−pilot mean)/pilot std이며 실제나 본 null의 매력적인 후보에 맞춰 fit하지 않는다.

main seed180042로 IID199와 기존 Curveball fixed-margin199를 scope별로 새로 만든다.
개발 fixed margins는1–900 자체의 row/column margins만 사용한다.
각 surrogate는 자체45series,same-draw,pairs,lags,rate windows,regimes,secondary shifts를 재구성하고
모든 후보를 검색한 뒤7개 family의 자체 최대 z를 저장한다.
selected real pair 한 곳에만 null을 적용하지 않는다. raw vector와 pilot도 보존한다.
global empirical p=(1+exceedances)/(199+1), corrected p=min(1,7p)다.
secondary를 포함한7family 보정은 primary-only 보정보다 보수적이다.
최소 global p=.005,보정 최소=.035이며 finite Monte Carlo/pilot 추정의 불확실성이 남는다.
Curveball20×N trades는 정확한 margins를 보존하지만 완전한 균등 mixing의 증명은 아니다.

## MirrorModel과 개발 선택

descriptive/null 분석 완료 뒤 역사 비교용 MirrorModel을 구현한다.
corrected 구조 근거가 없다고 해서 이 실험을 예측 우위의 증거로 포장하지 않는다.
MirrorPairModel은 개발에서 corrected pair relation과 시대별 support가 있어야 검토하며,
이번 개발의 pair family가 양 null 모두 보정 p=1이므로 만들지 않는다.

target T에서는 N=T−1까지의 completed prefix만 입력한다.
training source rate z_j(u)는 mirror(j)의 W-draw mean이며 source endpoint u,
response y_j(u+lag)는 completed future appearance다. 마지막 training response는 N이다.
query source endpoint는 T−lag이며 반드시 N 이하이다.

각 번호별 training source/target mean을 빼 own frequency 수준을 제거한다.
C_j=Σ(z_j−mean z_j)(y_j−mean y_j), V_j=Σ(z_j−mean z_j)²라 두고
source binary support≥20인 non-center 번호 집합 S에서

beta=clip(Σ(S)C_j/[Σ(S)V_j+shrinkage×|S|×p(1−p)/W],−1,1),p=6/45.

score(j)=p+beta×s_j/(s_j+shrinkage)×[query mirror activity(j)−training source mean(j)]다.
support 미달은 contribution0이며 score(23)=p로 고정한다.
이는 finite ranking score이며 calibrated probability가 아니다. clip은 beta에 적용한다.
Source-support attenuation이 번호별로 달라 shrinkage는 단순한 공통 score rescaling이 아니다.
Gap/Graph/MI/기존 ensemble feature는 넣지 않는다.

개발 target401–900에서 W{10,26,52}×positive lags8개×shrinkage{50,200}=48configs를 비교한다.
평균Top6가 selection metric이며 동률은 사전 grid 순서다. support20·aggregation·normalization은 고정이다.
개발 prefix hash와 설정 JSON/hash를 동결한 후901–1245에서 평가한다.
score마다 전체 available prefix의 계수를 다시 구하고 cache key도 prefix bytes/shape/W/lag를 포함한다.
outer cadence fit과 실제 score fit cutoff를 별도 기록한다. 기존 prefix를 바꾸거나 future row를 주면 거부한다.
모든 ranking은45개이며 score 동률은 작은 번호 우선이다.

## 평가·다양성·prospective

RandomModel(seed42),Frequency26,MirrorModel을 causal engine에서 비교한다.
GapLogistic은 Phase15의 cadence26/13 frozen output을 manifest hash·source·ranking metrics로 검증해 읽는다.
Gap을 새로 fit하지 않는다. diversity용 Graph/GapShape/MI도 직접 저장된 역사 output만 사용한다.
Top6평균/0–6분포/Recall6·10·15/mean winning rank/Top8·10·12·15≥5/각 pool all-six를 저장한다.
starts901/1001/1101에서2000 paired circular block-bootstrap,main block=cadence와 sensitivity block52를 쓴다.
이 구간들은 겹치며 독립 반복 실험이 아니다. 여러 starts/metrics/blocks의 CI는 simultaneous correction을 하지 않은 진단이다.

low correlation은 prediction benefit을 보장하지 않는다. ENSEMBLE CANDIDATE는 약한 양의 점추정치와
다른 순위를 탐색적으로 보존하는 분류이며 H16 PROMISING/통계적 예측 우위와 구분한다.
최근 성능·인접 W/lag 민감도를 보고하지만 더 좋은 later 설정으로 바꾸지 않는다.
H16 PROMISING은 corrected 구조와 robust predictive benefit 모두 필요하다.

실제 prospective archive가 부재하므로 어떤1247 snapshot도 발행하지 않는다.
역사 실험 모델의 존재와 prospective에 정당화된 모델의 존재를 구분한다.
이번에는 후자가 없어 draw1247_phase18_symmetry capability를 만들지 않는다.
전체 상태는 PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION이다.

## 재현

```powershell
$env:PYTHONPATH='.;.deps/docs-checks'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
python main.py symmetry calibrate --pilots 32
python main.py symmetry benchmark
python main.py symmetry analyze --surrogates 199 --workers 4
python main.py symmetry diagnostics
python main.py symmetry select
python main.py symmetry compare --cadence 26
python main.py symmetry compare --cadence 13
python main.py symmetry sensitivity
python main.py symmetry model-example
python main.py symmetry plots
python -m pytest -q -rs
```

`details`는 초기 진단과 분리해 추가 진단만 실행할 때 사용하며 기존 evidence는 덮어쓰지 않는다.
그림은 inspection aid다. 결과·검증·파일 목록은 [Phase18 결과](phase18-results.md)를 참조한다.
