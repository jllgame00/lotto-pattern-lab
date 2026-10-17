# Phase20 — H19 Point process / Hawkes-like influence / renewal

## 범위와 해석

Main numbers draws1–1245만 사용한다. Bonus·실제1246·외부 자료는 feature/선택/평가에 쓰지 않는다. 각 row의 활성 번호는 정확히6개이므로45개 process는 서로 독립이 아니다. 아래 Bernoulli/logistic likelihood는 **pseudo-likelihood**이며 실제 추첨의 joint generative model이 아니다. Signed coefficient는 고전적 nonnegative Hawkes와 구분해 discrete Hawkes-like influence라고 부른다. 방향성은 시간 순서에 따른 예측 관계이며 인과적 개입 효과를 뜻하지 않는다.

시작은 clean main `35f97c295832ee8da92ddcdcff6479ec706910d2`이다. Phase19 manifest의22files 및 CSV hash를 확인했다. H1–H18 번호를 보존하고 H19를 추가한다. H17 ensemble과 H20–H25 구현은 하지 않는다.

## Event / renewal

번호별 event draw는1-based index,interarrival은 연속 event index의 차이다. Gap은 target 직전 연속 미출현 수로 직전 draw에 출현하면0이다. 첫 own event 이전은 left-censored로 제외한다. Relative gap은 현재 gap을 **이전에 완료된 own interarrival의 평균**으로 나눈다. 두 prior event가 없으면 미정의이다. Recent counts W10/26/52는 해당 completed draw까지의 요약이며 같은 row outcome 예측에 그대로 사용하지 않는다.

|표현|고정 정의|state 수|
|---|---|---:|
|clipped|`min(gap,26)`|27|
|coarse|edges1/3/7/13/26,오른쪽 bin|6|
|relative|gap/causal mean interarrival,edges.5/1/2/3|5|

Target별 baseline은 uncensored own rows에서 `(wins+2)/(rows+15)`이다. Hazard는 `(state hits+alpha×baseline)/(state support+alpha)`이며 구조 분석 alpha26,minimum support20이다. 모델은 alpha26/104를 개발에서 고르며 support 미달/미정의 state는 baseline으로 fallback한다. Raw hazard와 shrink된 hazard,baseline과 IID6/45를 따로 표시한다. Marginal Jeffreys interval은 탐색 보조이며 draw/번호 의존성을 무시한 유의성 검정으로 사용하지 않는다.

기존 `GapHazardModel`도 training-only gap bin의 pooled hazard를 Beta prior로 smoothing했다. 이 Phase의 renewal 해석 자체가 새로운 정보는 아니다. 번호별 baseline/left-censor 처리/relative causal mean과 event-centric global null을 명확히 하고 cross-number impulse를 별도로 검증하는 것이 추가 범위다. 이전 모델은8bin pooled table·prior strength75였고,본 renewal은6/27/5states·번호별 shrinkage다. 기존 seal을 고쳐 이전 모델을 재실행하지 않는다. 바로 읽을 frozen historical output이 없으면 수치 비교 불가를 명시한다.

## Self / cross effect와 kernel

Lag는 **1/2/3/4/8/13/26**이며 lag0은 없다. Matrix axis는 source_i, target_j이다. `X_i(t−lag)=1` event support와 target hits를 세고 aligned target baseline `(target wins+2)/(aligned rows+15)`을 사용한다. Minimum source support30,alpha26으로 conditional rate를 shrink한다.

`effect=conditional−baseline`, `score=effect×sqrt(support/(baseline×(1−baseline)))`이다. Raw rate,lift,log-odds difference,support를 함께 보존한다. Positive와 negative score의 positive part를 별도 family로 검색한다. Source가 없으면 conditional은 baseline이고 cell은 미지원 처리한다.

Kernel은 exp2/exp8/finite의 세 종류만 쓴다. Exponential weight는 `exp(−(lag−1)/tau)`이며 tau2/8로 고정한다. 구조 통계는 lag excess=`effect×support`의 weighted projection을 `sqrt(sum(weight²×support×baseline×(1−baseline)))`로 나눈 값의 제곱이다. Finite kernel은7개 standardized signed score 제곱의 평균이다. 세 kernel 모두7lag에 support를 요구한다. Independent-lag variance는 calibration용 근사이며 실제 lag의 의존성은 Lotto null이 보정한다. Exp amplitude는 effect의 해당 basis 최소제곱 투영,finite amplitude는 RMS effect이다.

## Complete search / null

|family|고정 cell 수|
|---|---:|
|renewal hazard deviation|45×(27+6+5)=1710|
|self excitation|45×7=315|
|self inhibition|45×7=315|
|cross excitation|45×44×7=13860|
|cross inhibition|45×44×7=13860|
|kernel structure|45×45×3=6075|
|합계|**36135**|

Cell의 고유 key는 family/종류/source/target/lag/state/kernel을 포함한다. Positive와 negative에서 동일 pair를 검색하더라도 다른 family identity를 갖는다. 개발 cutoff900과 full1245에 각각 독립 IID pilot32개(seed201001)로 cell mean/std를 고정한다. Finite pilot support≥24와 std>1e−12를 만족하는 cell만 검색한다. Main null을 pilot에 재사용하지 않는다. Sparse 미정의 값은 rawNaN과 mask로 보존한다.

Main은 IID199 + 기존 constrained fixed-margin199(seed200042),각각 full/development를 별도 생성한다. 개발 fixed-margin은1–900 margin으로 생성하며1245의 margin을 잘라 쓰지 않는다. 매 surrogate에서 event/gap/renewal/모든self·orderedcross pair·7lag·3kernel을 다시 계산하고 자체 strongest cell을 고른다. Family maximum을 null family maximum과 비교한다. p=`(1+exceedances)/(199+1)`,six-family Bonferroni=`min(1,6p)`이다. z를 Gaussian p-value로 해석하지 않는다.

## Predictive model / 개발 동결

모델은 원본 prefix를 immutable bytes로 고정한다. Outer fit 이후 edges/baseline/scaler/coefficients를 재선택하지 않고 source event state만 target<T까지 업데이트한다. Target은1245 이하,입력 길이는 정확히T−1이고 이전 fit prefix가 변경되면 거부한다.

Renewal6configs는 scheme3×alpha26/104이다. Hawkes24configs는 kernel3×incoming1/3×alpha26/104×ridge1/10이다. Signed24개는 같은 grid의 별도 class다. incoming source는 own number를 제외하며 supported conditional effects에서 training-only로 고른다. Positive 모델은 positive effect와 nonnegative impulse만 허용한다. Signed는 음의 효과도 별도 weight로 허용한다. 각 amplitude의 절대값≤1,합≤1로 정규화하고 incoming 수로 평균해 작은 edge 집합을 보수적으로 감쇠한다. Input feature도±3으로 제한한다.

Pooled logistic은 번호별 fitted baseline logit offset에 own event convolution과 incoming convolution이라는 **두 개**의 pooled coefficient만 적합한다. 마지막416개 training outcomes(t≥26)를 사용하며 모든 convolution은 t−lag event만 읽는다. Training feature 평균으로 중심화하고 fitted baseline Bernoulli sd(floor.05)로 scale한다. Finite self kernel은7lag uniform,finite cross weight는 fitted lag effect에서 나온다. Objective는 sum Bernoulli NLL+.5ridge×coefficient²이다. Positive coefficient bounds는0..3,Signed의 self coefficient는−3..3이며 signed incoming weight의 방향과 구분한다. Centering 때문에 event가 없을 때 fitted mean보다 낮은 기여가 있을 수 있지만 positive 모델의 event impulse derivative는 nonnegative다.

같은 own feature/offset/ridge로 self-only coefficient를 **독립 적합**한다. Full model coefficient를 단순히0으로 지우는 ablation이 아니다. 이 nested baseline과 cross-added model의 이후 logloss를 비교한다. 각 draw의45개 Bernoulli loss 평균을 사용하며 joint draw probability라고 부르지 않는다.

개발 target401–900,cadence26에서54개 설정을 비교하고 **평균 per-number logloss 최소**,동률은 선언 순서로 선택한다. Top6는 별도로 보고하며 이후 성능으로 재선택하지 않는다. Hawkes는 development screening 후 explicit experimental falsification 비교로 남긴다. Development-positive flag는 두 개발 반구간에서 nestedself보다 logloss가 작고 Top6≥Renewal일 때만 참이다. Signed는 두 개발 반구간에서 positive 모델 및 자체self baseline보다 logloss가 작고 Top6≥positive일 때만 이후 비교에 포함한다. 통과하지 않은 predictor는 prospective 근거가 아니다.

이후 target901–1245,cadence26/13을 비교한다. Random/Frequency26/검증된 frozen Gap/Renewal/Hawkes(+allowed Signed)가 대상이다. Random의 probability reference는6/45이며 random ranking score를 확률로 해석하지 않는다. Gap rank score가 확률이 아니면 logloss를 계산하지 않는다. 이전 Graph/GapShape/Mirror는 hash 확인한 frozen CSV의 rank 다양성만 계산하며 재fit/재선택하지 않는다.

Rank metric/0–6 hit distribution/Top8/10/12/15 >=5와all-six pool events를 export한다. Draw 단위 paired circular block bootstrap2000회(seed200042),blocks=cadence/52,starts901/1001/1101을 사용한다. Conditional logloss도 같은 draw 단위로 bootstrap한다. Era/rolling 분석은 full strongest relation을 고정하고,각 era의 best lag 변화는 기술적으로만 별도 기록한다.

### Support와 수치 안정성 검증

예측 source를 선택할 때도 structural kernel과 같이 **7개 lag 모두 support≥30**을 요구한다. 일부 lag만 지원된 source의 다른 lag가 convolution에 기여하지 않도록 검증한다.

Bounded logistic solver는 동일한 sum likelihood와 ridge를 row 수로 함께 나눈 목적함수를 최적화한다. 합계 loss가 약7300일 때 optimum의 작은 개선이 한 floating-point ULP보다 작아지는 line-search 문제를 피하기 위한 수치 스케일링이며 정규화 강도나 statistical model을 바꾸지 않는다. Primary L-BFGS-B 후 finite/feasible/success,baseline보다 나쁘지 않은 원래 목적함수,box-constrained projected KKT/row≤1e−8을 검증한다. 실패하면 같은 목적함수의 SLSQP fallback을 검증하며 두 solver 모두 실패하면 명시적으로 중단한다. 원래 목적함수와 수렴 진단을 보존한다.

## Graph 연결과 종료 gate

Lagged directional influence와 Phase14 same-draw co-occurrence는 다른 관계다. 기존 matrix가 frozen artifact에 있으면 hash 검증 후 undirected pair co-occurrence 대 directional influence 양방향 평균의 Spearman 및 top45 edge overlap을 기술적으로 계산한다. 새 Graph fit이나 community 재선택은 하지 않는다.

H19 PROMISING은 corrected event structure와 causal predictive improvement/robustness가 모두 필요하다. Development/later 근거가 없으면 ensemble candidate는 NOT CURRENTLY JUSTIFIED,Phase20 prospective infrastructure는 생성하지 않는다. Archive가 없으면 발행하지 않으며 `PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION`이다. 상세 결과는 [Phase20 결과](point-process-results.md)에 기록한다.

## 재현 명령

기존 evidence 덮어쓰기 guard가 있으므로 별도 재현은 모든 명령에 같은 `--reports-dir reports/point_process/새이름`을 지정한다. 기존 NumPy/SciPy/pandas/matplotlib/pytest를 사용하며 새 설치나 collection은 하지 않는다. 이 laptop은 PYTHONPATH=.;.deps/docs-checks,OPENBLAS/MKL/OMP thread1로 실행했다.

```powershell
python main.py point-process calibrate
python main.py point-process benchmark
python main.py point-process analyze --surrogates 199 --workers 4
python main.py point-process select
python main.py point-process compare --cadence 26
python main.py point-process compare --cadence 13
python main.py point-process diagnostics
python main.py point-process plots
python -m pytest -q -rs
```
