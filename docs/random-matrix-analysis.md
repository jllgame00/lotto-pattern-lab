# Phase22 / H21 — Random Matrix Theory / collective number modes 방법

## 질문과 연구 범위

Phase14가 명시적 pair/hypergraph를 검색했다면 H21은 **45번호 전체 correlation에 Lotto-valid noise보다 강하고 안정적인 collective mode가 있는가**를 묻는다. 구조 검정과 예측 근거는 별개다. 실제 본번호1–1245회만 사용하고 bonus와 실제1246은 제외한다. strict reader는 header+1245행 이후 unknown suffix를 파싱 전에 거부한다. 개발1–900에서 선택하고 이후901–1245는 gate 통과 시에만 평가한다. 이전 Phase가 사용한 이후 역사는 pristine holdout이 아니다.

[실행 전 고정 계획](superpowers/plans/2026-10-18-phase22.md)에 window/rank/lag/family와 gate를 기록했다. 추가 normalization,lagged rolling,임의r,non-Hermitian eigenvalue 검색은 하지 않는다.

## Primary correlation과 구조적 zero mode

각 draw는45열 binary이고 row합은6이다. Interval 내부 sample mean으로 center하고 sample std(ddof1)로 standardize한다. Primary는 ZᵀZ/(N−1) correlation45×45,secondary는 centered XᵀX/(N−1) covariance뿐이다.

Centered binary의 row합0은 covariance·ones=0을 뜻한다. 표준화 뒤에는 **correlation·sample_std=0**이며 일반적으로 correlation·ones는0이 아니다. 따라서45차원 matrix를 저장하되 active coordinate에서 covariance의1 또는 correlation의sample_std에 수직인 orthonormal basis로 제한해 고유분해한다. 구조적 zero mode를 scientific ranking에서 제거하며 나머지 eigenvalue를 바꾸지 않는다. Active45개이면 비자명 spectrum은44개다. Inactive column의 row/column/loading은0으로 embed하고 별도 zero들을 outlier로 세지 않는다. Inactive로44번째 mode가 없으면 해당 검색 cell을NaN으로 남긴다. 추가 genuine rank deficiency는 숨기지 않는다.

균일 IID Lotto의 population correlation은 대각1,비대각−1/44이므로 비자명 reference eigenvalue는45/44이다. 관측 sample의 약한 음의 상관과 zero mode를 숨은 구조로 해석하지 않는다. 실제 유의성은 이 이론값 대신 동일한 Lotto surrogate로 판단한다.

Eigenvalue는 내림차순이다.44개의 ordered spectrum,largest/smallest,오름차순 인접 spacing,cumulative explained variance,entropy=−Σp log p,effective rank=exp(entropy)를 기록한다. p는 eigenvalue/trace다. 고유분해의 대칭행렬 API 성질은 [NumPy 공식 문서](https://numpy.org/doc/stable/reference/generated/numpy.linalg.eigh.html)를 참고하며 코드에서는 descending으로 뒤집는다.

## MP는 설명용 reference

[Marchenko–Pastur 원 논문](https://www.mathnet.ru/links/4b7f424ea76d5b28bcc927c357d7aa85/sm4101_eng.pdf)의 independent-entry asymptotic 결과는 Lotto의 유한 binary/row-sum/margin 조건을 그대로 충족하지 않는다. 그림에는 effective q=(active−1)/(N−1),variance scale=trace/(active−1)의 approximate bulk σ²(1±√q)²와 density를 그린다. 이 적용은 설명용 근사이며 MP 경계 crossing은 유의성이나 predictor gate가 아니다.

## Localization,sign,degeneracy

각 unit eigenvector에 IPR=Σvᵢ⁴,PR=1/IPR를 계산한다. 균일 magnitude의 IPR reference는1/45다. Loading 상위 번호는 inspection용이며 부호를 번호 간 의미 관계로 해석하지 않는다. 출력 sign은 최대 absolute loading의 첫 index가 양수가 되도록 고정한다.

Direct 비교 helper는 isolated mode의 sign과 relative adjacent gap<=.05의 near-degenerate block을 Procrustes 정렬한다. 검정의 stability는 고정 leading r={1,2,3,5}의 principal angles와 projector overlap을 사용한다. Overlap=tr(P₁P₂)/r,projection distance=√(2r−2tr(P₁P₂))다. [SciPy 공식 principal-angle 정의](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.subspace_angles.html)와 일치하는 SVD geometry다.

**한계:** 선택한 span 내부 회전과 sign flip은 projector에 영향을 주지 않지만,degenerate block이 r/r+1 경계를 가로지르면 fixed-r subspace도 회전할 수 있다. 이것만으로 temporal instability를 선언하지 않는다. 개별 mode IPR도 degenerate basis에 의존하므로 특정 번호 집단의 고유하고 안정된 factor를 뜻하지 않는다. 실제/각 null에 동일한 deterministic solver와 고정r를 적용하며 임의 cluster dimension을 추가 검색하지 않는다.

## Rolling,era,recurrence

W={104,208,416,624},stride104,모든 complete endpoint와 마지막N을 포함한다. Nwindow>=2×effective dimension을 요구하며W104도44차원 대비2.36배 sample로 지원된다. 각 window 내부에서 mean/std/constraint를 다시 적합한다. Whole-history scaler를 rolling에 빌려주지 않는다.

같은 W의 endpoint index k={1,2,4} 차이를 비교한다. k1은 adjacent stability,k2/4는 bounded spectral recurrence다. 마지막 irregular endpoint도 포함하며 실제 start/end를 저장한다. Full은39rolling fits,dev는27개다. Full의 세 nonoverlap era는1–415/416–830/831–1245,dev는1–300/301–600/601–900이다. 모든 era pair 및 r별 세 pair overlap 최솟값을 같은 stability family에 포함한다. Overlapping rolling의 높은 overlap은 그 자체로 구조가 아니며 null도 같은 중복을 가진다.

## Lagged secondary SVD

L={1,2,4,8,13},full interval에서만 분석한다. X(t),X(t+L)의 양쪽 mean/std를 각각 다시 추정한다. C=ZleftᵀZright/(N−L−1)이며 일반적으로 비대칭이다. 양쪽 구조 방향도 다르므로 각각 제거한 후 SVD를 계산한다.

Largest singular value,top-r squared singular concentration(Σ₁ʳs²/Σs²),leading5left/right singular vector IPR를 보고한다. Lag당15cells×5=75cells다. Secondary lag 결과를 contemporaneous eigenvalue 발견으로 승격하지 않는다.

## Null와 정확한 검색 공간

각 cutoff1245/900의 IID32pilot(seed221001)을 별도로 생성해 cell별 oriented mean/std를 고정한다. Finite>=24/32,std>1e−12만 eligible다. Main seed220042로 **IID199+fixed-margin199**를 수행한다. Child seed는(seed,null code,replicate,cutoff)에서 결정하며 개발 fixed null은 실제1–900의 margin에서 독립 생성한다. Curveball은 기존 row당20trades이며 finite mixing surrogate다. Exact margins 보존과 uniform stationary sampling의 증명을 혼동하지 않는다.

각 surrogate는 binary45,구조 방향,correlation/covariance,whole/rolling/era/r/k/lag/SVD를 모두 새로 계산하고 **자기 family maximum**을 찾는다. 실제 eigenvectors나 selected mode를 null에 고정하지 않는다.

|family|통계|full cells|dev cells|
|---|---|---:|---:|
|largest|whole+rolling λ1|40|28|
|smallest|whole+rolling −λ44|40|28|
|localization|whole+rolling 모든44mode IPR|1760|1232|
|concentration|rolling top-r eigenvalue sum/trace|156|108|
|stability|rolling/era pair overlap 및 era-min|372|228|
|lagged_secondary|full lagged SVD75cells|75|75|
|합계||2443|1699|

Largest/작은 mode anomaly/localization/rolling concentration/stability의 다섯 family가 contemporaneous primary다. Lag는 secondary이나 **여섯 family 전체 Bonferroni6**에 포함한다. Empirical global p=(1+exceedances)/200,corrected=min(1,6p),최소가능값.03이다. Family 내부 모든 search cell은 global-max에 포함한다. Covariance는 동일 intervals/null spectra를 저장하지만 추가 primary family를 만들지 않는다.

Cell별 observed−IID/fixed median 및 empirical percentile을 별도 표에 저장한다. Local percentile과 pointwise95% spectrum envelope는 global evidence가 아니다. Pilot 표준화는 유한 표본/scale 차이를 줄이는 데 사용하고 이론적 Gaussian MP z값을 강제하지 않는다.

## Frozen Graph 비교

Phase14 manifest의 structural_cache.npz SHA-256을 확인한 뒤 **저장된** W104 adjacency/community만 읽는다. 정확히 일치하는 endpoint104/208/312/416/520/624/728/832/936/1040/1144의11개 window를 비교한다. Graph의1244와 RMT1245를 같은 endpoint로 간주하지 않는다.

Leading |loading| 대 node strength Spearman/top6 overlap,leading5projector의 node leverage mass 대 저장K2/K3 community size를 기록한다. Graph strength=5×frequency이므로 그 상관은 marginal activity와의 관계일 수 있다. 공동 역사에 대한 설명이며 독립 predictive evidence가 아니다. Missing/hash mismatch는 명시적으로 skip하고 Graph를 refit/retune하지 않는다.

## 개발 gate와 조건부 예측

예측 전에 **동일 whole leading-eigenvalue cell**이 개발 largest-family global null maxima 대비 두 null에서 모두 corrected p<=.05이어야 한다. 추가로 **동일 r의 세 nonoverlap-era overlap 최솟값 cell**이 stability-family global null maxima 대비 두 null에서 모두 corrected p<=.05이어야 한다. Rolling winner의 유의성으로 이 필수 cell을 대체할 수 없다.

실패하면 **PREDICTIVE_MODEL_NOT_JUSTIFIED**,ensemble NOT CURRENTLY JUSTIFIED다. SpectralFactorModel/ResidualModel,Random/Frequency26/Gap 비교,paired predictive bootstrap,rank diversity와draw1247_phase22_rmt를 만들지 않는다. 통과 시에만 계획의 작은 causal linear factor forecast를 개발에서 선택/동결하고 이후901–1245를 별도 평가한다. MP outlier만으로 gate를 열지 않는다.

## 실행과 보존

```powershell
$env:PYTHONPATH=(Join-Path (Get-Location) '.deps/docs-checks')
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
python main.py random-matrix calibrate
python main.py random-matrix benchmark
python main.py random-matrix analyze --surrogates 199 --workers 3
python main.py random-matrix select
python main.py random-matrix diagnostics
python main.py random-matrix audit
python -m pytest -q -rs --junitxml=reports/random_matrix/pytest.xml
```

설치나 데이터 fetch 없이 기존 local environment를 사용한다. Output은 `reports/random_matrix/` 아래다. Complete/partial analysis-owned output을 미리 확인해 기존 파일을 덮어쓰지 않는다. 시작 tracked/source/data/prior reports hashes와 HEAD를 보호하고 모든 새 산출물/정확한 변경 파일을 manifest에 기록한다. Full suite/독립 review/seed replay/raw→max→p 감사 후 [결과](random-matrix-results.md)를 갱신한다.

과거 prospective archive 부재 시 **PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**이다.1246을 가져오거나1247 snapshot을 발행하지 않는다. H17은 BACKLOG,H22–H25는 미시작이며 Phase22에서 종료한다.
