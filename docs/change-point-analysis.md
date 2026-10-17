# Phase19 — H18 Change-point / piecewise-stationary regimes

분석 범위는 main number의 draws **1–1245**이다. bonus와 실제1246은 사용하지 않는다. H17 Weak-signal ensemble은 BACKLOG로 남기며 이 Phase에서는 구현하지 않는다. 관측된 경계를 물리적 추첨 기계 변화로 해석하지 않는다.

## 사전 고정 표현과 비용

|표현|관측값|비용·정규화|
|---|---|---|
|개별 번호45개|draw별 Bernoulli indicator|−2 maximum Bernoulli loglikelihood|
|A|draw×45 binary|45개 Bernoulli 비용 합|
|B13/B26/B52|겹치지 않는13/26/52draw block의45개 appearance rate|IID p=6/45, sd=sqrt(p(1−p)/B)로 고정 표준화한 Gaussian SSE|
|C|sum,range,std,spacing mean,spacing std,consecutive-pair count,odd count|해당 fitting prefix의 mean/std로 표준화한 Gaussian SSE|

std는 population deviation(ddof=0)이다. C의 상수 열은 scale1을 사용하며 수치상 상수도 처리한다. B는 완성된 block만 segmentation하고 버린 tail 길이를 기록한다. A의 각 row 합은6이므로 composite Bernoulli likelihood는 독립 발생 generative model이 아니다. 유의성은 유효한 Lotto null에서만 보정한다.

## Segmentation

NumPy exact dynamic programming으로 `sum(segment cost)+penalty×CP count`를 최소화한다. A/C 및 개별 번호의 경계 후보는 **0,13,26,…,N**이며 마지막 N은 항상 포함한다. 이 grid 안의 optimum이지 매 draw 경계의 optimum을 주장하지 않는다. B의 후보는 완성 block 끝이다.

최소 segment 길이는 draw 단위 **26/52/104**, penalty multiplier는 **1/2**이다. penalty는 `multiplier×dimension×log(observation count)`이다. 개별 번호의 dimension1, A/B의45, C의7이며 B의 observation count는 block 수이다. B의 실제 최소 support는 `ceil(minimum/B)×B`이다. B52의 minimum26/52 설정은 중복되며 제거하거나 사후 유리한 설정만 남기지 않는다. 동률은 적은 CP 수, 이른 경계 순으로 결정한다.

Penalized detected CP와 penalty를 무시한 **best-single-split proposal**은 명확히 구분한다. proposal은 비용 개선이1e−10을 넘을 때만 존재한다. 늘 split을 강제하면 생기는 최적 분할을 실제 regime 검출로 부르지 않는다. CUSUM은 각 prefix에서 중심화/표준화하고 양쪽 최소26row를 요구한다. 상수 열은 score0/location없음이다.

## 전체 검색과 null

50개 unit(45번호+A/B13/B26/B52/C)×6개 penalty/minimum=**300 fits/prefix**이다. Full stability prefix는800/900/1000/1100/1245, development는500/600/700/800/900이다. 모든 surrogate에서 다섯 prefix와 모든 표현을 다시 만든다.

|family|고정 statistic cell 수|정의|
|---|---:|---|
|single_number|585|270 detected adjacent rate effects+270 one-split gains+45 CUSUM|
|global_shift|68|30 detected adjacent L1+30 proposal gains+7 shape CUSUM+1 number-vector CUSUM norm|
|concentration|24|6configs×tolerance13/26×detected/proposal의 최대 distinct-number 경계 집중도|
|concordance|360|6boundary group의15쌍×6configs×2tolerances×2kinds,one-to-one F1|
|stability|1200|50units×6configs×2tolerances×2kinds|
|합계|**2237**|pilot에서 분산이 있는 cell만 standardized search에 사용|

경계 없음끼리의 concordance는0이다. Stability는 full candidate보다 minimum만큼 이후까지 관측한 과거 prefix가2개 이상이고 그중 적어도2개가 tolerance 안의 경계를 재검출할 때만 양수이다. 값은 `matched/eligible × median(local gain/penalty)`이다. Full과 matching prefix의 gain을 사용한다. proposal 안정성과 detected 안정성을 분리한다. 내부 DP state/허용 interval transition 수, 표현별 endpoint 수는 artifact의 `space.prefix_inventory`에 별도 저장한다.

통계마다 단위가 다르므로 cutoff별 독립 IID pilot32개(seed191001)의 cell별 평균/표본std를 고정한다. finite pilot support≥24, std>1e−12인 cell을 eligible로 하며 상수/미정의 mask를 보존한다. Main null을 이 보정에 재사용하지 않는다. 실제 및 각 null은 같은 eligible cell 안에서 **자기 자신의 family global maximum z**를 선택한다.

주 null은 IID199개와 기존 constrained/Curveball fixed-margin199개(seed190042)이다. Development fixed-margin은 full history를 잘라 만들지 않고 **1–900의 margin**으로 독립 생성한다. Empirical p=`(1+null maxima≥real maxima)/(199+1)`, 다섯 family Bonferroni=`min(1,5p)`이다. 두 null에서 모두 unusual해야 강한 구조 근거로 해석한다. 소규모 pilot의 z는 순위 표준화 도구이며 정규분포 p-value로 사용하지 않는다. Calibration/noise의 tail 불안정성과 p resolution.005를 공개한다.

## Causal 예측

개발 target401–900만으로 표현5×minimum3×multiplier2×shrinkage2(26/104)=60개 후보를 Top6 평균 기준으로 선택한다. 동률은 선언 순서를 따른다. fixed Frequency26/52/104 중 비교 대상도 개발에서만 선택한다. 설정과 개발 matrix hash를 동결한 뒤901–1245를 평가한다.

각 target T는 **draws<T만 새로 segmentation**한다. 마지막 경계 b 이후 `b+1..T−1`의 rate를 prefix 전체 rate로 shrink한다: `(segment count+alpha×long-term rate)/(segment length+alpha)`. CP가 없으면 b=0이고 전체 frequency가 된다. B segmentation의 미완성 tail도 예측 시 이미 완료된 draw이므로 current segment rate에 포함한다. Cache key는 정확한 prefix bytes/shape/config이며 미래 값을 재사용하지 않는다.

Outer cadence26/13에 관계없이 Regime와 fixed baseline은 target별 현재 prefix에서 계산한다. Gap Logistic은 검증된 기존 frozen historical predictions를 읽는다. 새 Phase19에서 Graph/GapShape/Mirror/Gap을 재학습하지 않는다. 개발 Regime 평균이.8과 best fixed를 넘고 개발 전후반 모두.8을 넘을 때만 secondary Gap+Regime equal-rank comparison을 허용한다. 이는 H17 최종 ensemble이 아니다.

모든 target에 cutoff,lastCP,current segment length,raw45rates,shrunk45rates를 export하고 raw rates가 해당 prefix slice의 평균과 같은지 즉시 검증한다. 여러 historical start와 early/middle/recent,인접 설정 민감도를 보고한다. Paired circular block bootstrap2000회,block=cadence 및52를 Random/best-development-fixed/Gap 대비 계산한다. 다양성은 number-coordinate Spearman과Top6/10/15 overlap으로 측정한다.

## 판단·출판

H18 PROMISING은 corrected structural evidence와 causal later predictive robustness가 함께 있을 때만 가능하다. 검출된 regime의 그림,proposal,frequency와의 동률만으로는 충분하지 않다. 예측 정당성이 없으면 draw1247_phase19_changepoint capability를 만들지 않는다. Archive 부재는 historical 연구를 막지 않지만 prospective publication은 금지한다: `PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION`.

실행 및 수치 결과는 [Phase19 결과](change-point-results.md), local artifact는 `reports/change_point/`에 기록한다.

## 재현 명령

기존 evidence를 덮어쓰지 않는 guard가 있으므로 재현은 `--reports-dir reports/change_point/새이름`을 모든 명령에 동일하게 지정한다. 아래는 canonical 최초 실행 순서이며 collect/import/publication 명령을 포함하지 않는다. 기존 NumPy/SciPy/pandas/matplotlib/pytest 환경을 사용한다. 이 laptop의 실행은 `PYTHONPATH=.;.deps/docs-checks`와 OPENBLAS/MKL/OMP thread1을 적용했다.

```powershell
python main.py change-point calibrate
python main.py change-point benchmark
python main.py change-point analyze --surrogates 199 --workers 4
python main.py change-point select
python main.py change-point compare --cadence 26
python main.py change-point compare --cadence 13
python main.py change-point sensitivity
python main.py change-point diagnostics
python main.py change-point plots
python -m pytest -q -rs
```
