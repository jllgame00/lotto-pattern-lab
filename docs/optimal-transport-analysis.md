# Phase 24 — H23 Optimal Transport / Wasserstein geometry 방법

## 연구 범위

각 draw를 번호축 1..45의 empirical probability measure로 본다.
숫자 mass의 이동에 random Lotto보다 반복 가능한 geometry가 있는지 검정한다.
Canonical 자료는 **1–1245회**로 영구 고정하고 기존 strict-source byte-length/hash seal을 사용한다.
외부에 알려진 1246회 결과의 수집·import·분석은 하지 않는다.
개발은1–900회, 이후는901–1245회다. 이후 구간은 기존 연구에서 사용했으므로 pristine holdout이 아니다.

실행 전 Git root·branch·clean status·필수 파일·Phase23/H22 완료 상태를 확인한다.
기존 `reports/prospective/`의 모든 파일을 SHA-256 inventory에 기록하고 integrity record를 읽기 전용으로 검증한다.
Phase5의 nested `files`와 Phase6–10의 flat mapping을 모두 처리한다.
기존 파일을 수정·재생성·normalization하지 않으며 종료 audit에서 전체 inventory가 같은지 확인한다.

## Exact 1D OT

정렬한 draw 좌표를 x₁<…<x₆라 하면 μ=(1/6)Σδ[xᵢ]다.
두 equal-mass measure의 optimal monotone coupling은 같은 순서의 좌표끼리 연결한다.

`W1(A,B) = mean(abs(B_sorted - A_sorted))`

`W2(A,B) = sqrt(mean((B_sorted - A_sorted)^2))`

Primary는 W1, secondary는 W2다. Sinkhorn·entropic regularization·추가 optimizer가 필요 없다.
Signed transport vector `d_t = sorted(draw_(t+1)) - sorted(draw_t)`는 여섯 order statistics의 이동이다.
특정 실제 공의 정체성을 추적하는 transport map으로 해석하지 않는다.
signed mean·absolute mean·RMS·variance·positive/negative fraction·sign consistency·center-of-mass change를 저장한다.

방향 cosine은 dot/(norm product), normalized dot은 dot/(mean squared norms)다.
후자는 두 vector 크기가 다를 때 cosine보다 작아진다.
Mean-shift sign 및 coordinate sign agreement도 측정한다. Zero vector의 방향 cosine은0으로 정한다.
Magnitude memory는 bounded lag의 Spearman과 이전 W1 quartile별 다음 W1이다.
Acceleration은 `a_t=d_t-d_(t-1)`이고 추가 derivative hierarchy는 만들지 않는다.

## 사전 고정 검색공간

| Family | Cell 수 | 검색 내용 |
|---|---:|---|
| lag_magnitude | 36 | W1/W2 × lag7 × mean/std=28; W1 magnitude memory lag7; 큰/작은 이전 이동의 다음 W1 차이1 |
| direction | 19 | cosine/normalized dot/mean sign/coordinate sign × lag1/2/3/4=16; acceleration absolute/RMS/repeat cosine3 |
| successor | 10 | standardized Euclidean/cosine × pair cosine relation/pair distance relation/nearest distance/next cosine gain/next distance gain |
| rolling_drift | 39 | W3 × step4 × mean/max/adjacent drift-direction cosine=36; historical distribution return3 |
| barycenter | 24 | W3 × W1/W2 evaluation distance × next/recent/unconditional gain/movement |
| geodesic | 4 | W1/W2 midpoint residual × mean/std |
| **합계** | **132** | 개발·전체 구간과 모든 null에서 같은 keys와 전체 검색 |

Draw-distance lag={1,2,3,4,8,13,26}.
Rolling distribution W={26,52,104}, endpoint step={1,4,13,26}.
Barycenter W={10,26,52}. Secondary diagnostics도 위 family에 포함해 보정한다.
실제 자료의 peak를 보고 parameter를 추가하거나 제거하지 않는다.

## Transport successor

`X=distance(d_i,d_j)`, `Y=cosine(d_(i+1),d_(j+1))` 또는 다음 vector의 RMS Euclidean distance다.
유사한 원인 vector 뒤에 유사한 후속 vector가 오는지 Spearman으로 측정한다.
Cosine relation은 `-rho(X,Y_cosine)`, distance relation은 `rho(X,Y_distance)`로 정의한다.
양수는 continuation 방향이며 검정 자체는 양방향 |z|를 사용한다.

원인·후속 event 하나는 underlying draw3개를 사용한다. Pair diagnostic은 index0,3,6,…의 disjoint block 쌍만 쓴다.
Nearest historical diagnostic의 query i는 j<=i−3에서 선택하고 successor j+1을 query successor i+1과 비교한다.
각 query의 같은 admissible historical successor 전체 평균에 대한 cosine gain과 RMS-distance gain을 저장한다.
동률은 가장 오래된 index를 택한다. Euclidean scale은 해당 완성된 분석 scope의 coordinate 표준편차다.
이는 **descriptive development diagnostic**이며 과거 모든 target의 causal predictor 성능으로 부르지 않는다.
실제 predictor가 생기면 target마다 training-only scaling을 다시 해야 한다.

연속 d는 중간 draw를 공유하므로 IID에서도 anti-persistence가 발생한다.
유사 d의 successor도 원인 draw geometry 때문에 닮을 수 있다. Raw correlation/gain 양수만으로 gate를 통과하지 않는다.

## Rolling distribution과 barycenter

Endpoint t의 ν_t^W는 draw[t−W+1..t]의6W appearances를1..45에 누적한 normalized mass다.
Unit-spaced discrete distribution의 exact W1은 `sum_k=1..44 abs(CDF_A(k)-CDF_B(k))`다.
Rolling drift는 t와 t−step의 ν 사이 거리다. Drift-direction cosine은 연속 endpoint의 signed CDF movement를 비교한다.
Historical return은13endpoint 간격으로 query하고 최소26draw 떨어진 이전 distribution까지의 최소 W1이다.
Overlapping rolling window가 만드는 매끄러움은 null에도 정확히 유지한다.

평균 quantile profile은 **squared-W2 objective의 barycenter**이며 실수 좌표를 그대로 보존한다.
W1 barycenter의 quantile은 median이다. 이 둘을 혼동하지 않는다.
요청한 평균 profile과 trivial coordinate-wise sorted-draw mean baseline은 정확히 같은 값이다.
Next draw W1/W2, recent draw 평균거리, causal cumulative sorted-position mean에 대한 next distance 차이,
barycenter movement를 각각 기록하고 IID/fixed-margin으로 검정한다.
Recent training distance가 next distance보다 작다는 사실만으로 예측 집중을 주장하지 않는다.
평균 quantile 표현만으로 별도의 WassersteinBarycenterModel을 보존하지 않는다.

## Geodesic

Midpoint quantile은 `(sorted(draw_(t-1))+sorted(draw_(t+1)))/2`다.
실제 가운데 draw와의 W1/W2 residual을 비교한다. 이는 **DESCRIPTIVE ONLY**이며 미래 draw를 사용한다.
Residual은 acceleration magnitude의 절반과 대수적으로 같아 독립 evidence로 중복 해석하지 않는다.

## Null calibration과 보정

각 scope 길이900/1245에 독립 IID32 pilot(seed241001)을 만들고 cell별 mean/sample std를 동결한다.
Scope별 seed는 SeedSequence([pilot_seed,n,replicate])다. Main history와 real은 pilot 추정에 쓰지 않는다.
|z|를 계산하고 각 family의 모든 cell 중 자체 maximum을 택한다. Zero pilot variance는 eligible에서 제외한다.

Main seed240042에서 IID199 및 기존 Curveball fixed-margin199를 생성한다.
각 scope/null/replicate seed는 SeedSequence([240042,kind_code,replicate,n])다.
Fixed-margin은 row6개·각 번호의 전체 column count를 정확히 보존하고20trades/row를 수행한다.
유한 mixing의 근사 randomization이라는 한계는 남으며 exact uniform fixed-margin sample이라고 주장하지 않는다.
모든 surrogate는 draw measures·거리·vector·lags·rolling distributions·barycenters·geodesic·모든 parameter를 새로 만든다.
개발 fixed-margin은900회 자체 margin을 보존하며 전체 null history의 prefix를 재활용하지 않는다.

`global_p=(1 + count(null_own_max >= real_own_max))/(199+1)`

각 null별 여섯 family에 `corrected_p=min(1,6*global_p)`를 적용한다.
두 null은 평균내거나 유리한 쪽만 선택하지 않고 나란히 보고한다. 최소 p=.005, 최소 corrected p=.03이다.
개발·전체 scope는 별도 보고하며 개발만 모델 gate에 사용한다.

## 모델 gate와 이후 평가

Continuation은 개발 successor family가 두 null 모두 corrected p<=.05이고,
선택 metric의 cosine gain과 distance gain 각각이 IID pilot mean보다 큰 방향의 signed z로도
두 null의 successor-family absolute global maximum을 넘는 corrected p<=.05를 확보해야 한다.
이 방향 검정은 기존 양방향 family maximum을 재사용하므로 추가 검색을 유리하게 허용하지 않는다.
같은 vector metric의 cosine gain과 distance gain이 개발의 세 구간 모두 양수여야 한다.
통과한 경우만 그 metric을 동결하고 training-only predictor·fixed kernel 개발 선택·later walk-forward를 구현한다.
Barycenter는 동일 mean baseline을 넘어서는 별도 정보가 없으면 retain하지 않는다.
Gate 실패 시 모델·walk-forward·Random/Frequency/Gap 비교·rank correlation·prospective capability는 생성하지 않는다.
관찰된 양의 raw successor relation이나 descriptive geodesic을 대신 예측 근거로 쓰지 않는다.

안정성은 early1–415/middle416–830/recent831–1245 및 W208/stride52의 descriptive metric table로 보고한다.
여기서 새 p-value나 best rolling window를 선택하지 않는다.

## 재현·검증

```powershell
python main.py optimal-transport prepare
python main.py optimal-transport calibrate
python main.py optimal-transport analyze --workers 1
python main.py optimal-transport diagnostics
python main.py optimal-transport audit
python -m pytest -q
```

출력은 Git-ignored `reports/optimal_transport/` 안에 둔다. 실행은 기존 evidence 덮어쓰기를 거부한다.
별도 run은 그 아래 새 `--reports-dir`를 사용한다. Parallel worker 실행이 제한되는 환경에서는 workers1을 사용한다.
Audit은64pilot 전체, 대표 main8개 seed replay,796saved raw metric vector 전체의 own-max와 p-value 재계산,
선택 hash·protected artifact hash·archive 전체 byte hash·HEAD 불변을 확인한다.
398main history 전부를 두 번째로 재생성하는 검증은 아니다.
Plots11개는 inspection aid이며 검정 증거를 추가하지 않는다.

H24 Symbolic Dynamics, H25 randomness battery, H17 final ensemble은 구현하지 않는다.
