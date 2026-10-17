# Phase21 / H20 — Long-memory / fractal scaling / DFA 방법

## 범위와 사전 고정

본번호 1–1245회만 사용하며 bonus는 제외한다. 기존 strict reader는 header+1245행만 읽고 파일 길이가 다르면 미래 행을 파싱하기 전에 거부한다. 실제1246 fetch/import/use/evaluation은 없다. 개발은1–900이며 이후901–1245는 이전 연구에서도 사용한 역사 구간으로 pristine holdout이 아니다.

[중단 전 계획](superpowers/plans/2026-10-18-phase21.md)의 grid와 여섯 primary family를 유지한다. 재개를 이유로 hypothesis, window, crossover 또는 통계 family를 늘리지 않는다.

## 표현과 추정

55열은 centered binary 번호45개, draw 전체의 sum/range/std/spacing_std/odd_count 5개,9개 번호씩 묶은 band count5개다. 모든 표현은 해당 완료 draw만 사용한다. 번호열의 합과 band count의 합은 draw당 고정이므로 45열 합계의 DFA를 별도 hypothesis로 만들지 않는다.

DFA1이 primary다. 각 열을 demean하고 누적합 profile을 만든 뒤 각 scale의 선형 추세를 제거한다. 시작/끝 양방향의 nonoverlap partition에서 residual squares를 모아 RMS F(s)를 구하고 log F(s) 대 log s의 전체 slope alpha, R², 이차 곡률을 기록한다. 역방향 partition을 독립 표본 수 두 배로 세지 않는다. RMS0은 exponent 미정의로 남긴다.

사전 선언 scales는 **8,13,21,34,52,78,104,156,208,312**이다. 한 방향에서 서로 다른 complete segment가4개 이상인 scale만 쓴다. 따라서 N1245와 N900의 실제 적합은 **8–208의9개 scale**이며312는1248회가 필요해 미지원이다. 이를 위해 미래 draw를 읽거나 support 기준을 완화하지 않는다. W312/416/624의 실제 scale은 각각8–78/104/156이다. DFA2는 동일 grid의 secondary sensitivity만 제공한다.

R/S는 같은 지원 scale에서 segment 누적편차의 range/표준편차를 평균해 slope를 구하는 reference다. 유한 크기 binary 자료의 편향 때문에 alpha>.5 또는 R/S>.5만으로 persistence를 선언하지 않는다. Synthetic white/AR(1)/difference 검사는 유한 scale 반응의 sanity check이며 AR(1)을 진짜 장기 의존성 생성기로 해석하지 않는다.

한정된 crossover 분석은 boundary52/104/156의 continuous hinge log-log fit이다. 양쪽에 엄격히2개 이상 scale이 있어야 하며 경계와 같은 scale은 양쪽 support에 세지 않는다. 통계는 (linear SSE−hinge SSE)/linear SSE다. 한 curve의 개선은 구조 증거가 아니며 최대 개선 검색을 null에서도 수행한다.

Aggregation은 disjoint block1/2/4/8/13/26/52 평균의 variance(ddof1)를 log block size에 회귀한다. 각 크기 최소4개 block, 불완전 tail 제외. IID reference slope−1로부터의 절대편차를 쓴다. Spectral beta는 demeaned periodogram의 Fourier index2..floor(N/26), 즉 period>=26의 고정 저주파 band에서 minus log-power slope다. Secondary이며 sparse/noisy periodogram의 slope를 별도 발견으로 승격하지 않는다.

Rolling은 W312/416/624,stride52,각 window가 완성된 endpoint와 마지막 cutoff를 포함한다. window마다 mean/profile/detrending을 새로 계산한다. Overlap이 큰 창의 개별 극단값을 독립 evidence로 세지 않는다.

## 동일 탐색 null과 보정

N1245/N900 각각 독립 IID pilot32개(seed211001)로 cell별 oriented mean/std를 먼저 고정한다. 유한 pilot 중75% 이상 지원되고 std>1e−12인 cell만 활성화한다. Pilot은 본199개 null에 포함하지 않는다.

본 실험은 **IID199 + fixed-margin199**, seed210042다. IID는 매 draw6-from45이며 fixed-margin은 기존 Curveball(행당20 trades)로 각 row합6과 각 번호의 총빈도를 보존한다. Fixed-margin은 finite mixing surrogate이며 독립성/완전 uniform mixing의 증명은 아니다. 개발 fixed null은1–900에서 별도로 생성하고 전체 null prefix를 잘라 쓰지 않는다.

모든 surrogate는 표현55개, 모든 scale/경계/rolling fit, secondary까지 동일 complete search를 새로 수행한다. 각 cell을 pilot mean/std로 표준화한 뒤 **각 surrogate 자신의 family 최대값**과 실제 최대값을 비교한다. Empirical p=(1+exceedances)/200이며 양 null을 따로 보고한다.

Primary는 persistent alpha,anti-persistent −alpha,crossover improvement,aggregation |slope+1|,rolling |alpha−.5|,whole-system(shape/band) |alpha−.5|의6개다. Family 간 Bonferroni6을 적용한다. 번호와 band 등은 이미 family 내부 global-max에 포함된다. R/S/spectral/DFA2의3개 secondary family는 별도의 global-max와 Bonferroni3으로 보고하며 primary 발견으로 전용하지 않는다. 가장 작은 가능한 primary corrected p는.03이다.

Cell별 보정은 유한 표본 null 중심화이며 이론적 alpha=.5를 검정의 중심으로 강제하지 않는다. 55개 whole-curve alpha의 IID/fixed median,centered alpha,percentile을 별도 CSV로 저장한다. Percentile은 p값이 아니다.

## 개발 gate와 기술적 진단

동일 primary family가 개발1–900의 두 null에서 모두 corrected p<=.05이어야 predictor 설계를 검토한다. 추가로 개발에서 선택한 series는 해당 passing family의 저장된 winner와 일치하고1–300/301–600/601–900의 같은 방향 및 R²>=.9를 만족해야 한다. Persistent/anti-persistent는 그 family의 방향도 일치해야 한다. 다른 series의 유의성과 선택 series의 안정성을 합칠 수 없다. 실제 모델 설계/검증은 gate 통과 뒤에만 가능하다. 실패하면 **PREDICTIVE_MODEL_NOT_JUSTIFIED**, ensemble NOT CURRENTLY JUSTIFIED이며 LongMemoryModel/ScaleStateModel,비교 backtest,prospective capability를 만들지 않는다.

기술적 설명을 위해 raw number alpha 최대/최소와 shape/band 최대편차 curve,전체/세 구간/rolling을 기록한다. 선택 series의 circular moving-block bootstrap은 block26/52,199replicates,seed211999다. 이는 선택에 조건부인 유한 block CI이며 전체 탐색 보정이나 asymptotic H의 신뢰구간이 아니다. 열을 공동으로 resample하고 DFA를 다시 적합한다. Matched IID/fixed curve의 seed211234도 그림 설명용이며 추론은199개 global-max에 의존한다.

## 실행과 산출물

```powershell
$env:PYTHONPATH=(Join-Path (Get-Location) '.deps/docs-checks')
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
python main.py long-memory calibrate
python main.py long-memory benchmark
python main.py long-memory analyze --surrogates 199 --workers 3
python main.py long-memory select
python main.py long-memory diagnostics
python -m pytest -q -rs --junitxml=reports/long_memory/pytest.xml
```

현재 환경은 기존 local dependencies를 이용하며 설치나 원격 자료 접근은 없다. 결과는 gitignore된 `reports/long_memory/`에만 쓴다. Null raw metrics,scope별 search inventory/real metrics,자기 최대값,보정표,개발 decision hash,bootstrap/temporal/rolling/secondary CSV와10개 PNG를 보존한다. 기존 evidence가 있으면 CLI는 덮어쓰기를 거부한다. Interrupted partial evidence를 자동으로 complete라고 인정하지 않는다. `metric_vector`는 짧은 진단 입력312부터 허용하지만 모든 family를 요구하는 `complete_search`는 crossover 지원 때문에416회 이상이 필요하다. 실제 역사 실행은900/1245만 사용한다.

과거 prospective archive가 없는 동안 **PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**이다. Negative guard만 있으며1247 publication 명령은 없다. H17은 BACKLOG,H21–H25는 시작하지 않는다. 최종 수치는 [결과](long-memory-results.md)를 참고한다.
