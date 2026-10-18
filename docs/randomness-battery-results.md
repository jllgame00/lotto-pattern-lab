# Phase26 / H25 — Integrated randomness battery 결과

**H25 = TESTED / INCONCLUSIVE.** 사전 고정한 battery에서 실제1–1245 history를 IID Lotto와 구별할 보정된 omnibus 증거를 얻지 못했다. 번호별 장기 빈도를 조건으로 한 fixed-margin track에서도 추가 시간·관계 구조의 증거를 얻지 못했다. 이는 무작위성의 증명이나 예측 불가능성의 증명이 아니다. [방법·정확한 통계 정의](randomness-battery-analysis.md), [실행 계획](superpowers/plans/2026-10-18-phase26.md)을 함께 보존한다.

## 작업 경계·출발 상태

- Git root: `D:/univ/personal/lotto-pattern-lab` (예상 경로와 정확히 일치).
- Branch: `main`; 시작 SHA: `9b890c4799ecef4b4cbca0dcb8b211fe34fdfc3c`.
- 시작 `git status --short`: 빈 출력. Phase25/H24 완료, 필수 README·docs·원본 CSV·src·tests 확인. 관련 없는 source/data 변경은 없었다.
- Canonical CSV SHA-256: `b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e`.
- 연구 입력은 정확히1–1245회. 실제1246 자료는 사용·수집·import하지 않았다. Guard regression test의 가짜 미래 회차 표식은 실제 추첨 자료가 아니다.
- **PROSPECTIVE_ARCHIVE_STATUS = VERIFIED**. 기존30files 전체 SHA-256 inventory와 기존 integrity record의12targets를 시작·끝 검증했다. 불일치0, 원본 byte 변경0. Hash를 재생성하여 기존 integrity record를 덮어쓰지 않았다.
- 새 predictor, ranking, ensemble,1247prediction, prospective capability/publication은 만들지 않았다. Commit/push 없음. H17은 **BACKLOG / NEXT PHASE**이며 구현하지 않았다.

## Battery·검색 크기

표현: 번호별 binary45/time, draw binary45, sorted6, adjacent gaps5, frozen shape7(sum/range/std/spacing mean/spacing std/consecutive pairs/odd count), five-band occupancy(1–9/10–18/19–27/28–36/37–45).

9families는 marginal, serial, run_gap, overlap, shape_distribution, shape_temporal, relational, spacing, spectral_entropy다. Track A는 **2200units/9families**, Track B는 **2147units/8families**다. B는 marginal51개와 margin에 고정되는 sum/odd 평균2개를 제외한다. 정확한 family별 unit 수는 [방법 inventory](randomness-battery-analysis.md#고정-표현과-inventory)에 있다.

Serial/overlap lags={1,2,3,4,8,13,26}; shape temporal lags={1,2,4,8,13,26}. 990pair는 개별 unit이고,14190triple 검색은 하나의 supported-triple maximum unit에 포함된다. Triple 후보까지 펼치면 A16389/B16336candidate-cells다. 모든 surrogate가 자신의 support와 strongest triple을 검색한다. Full 실제 적격 triple425개, strongest=(1,3,27),count8,expected1.754757이다. Era는 같은 expected≥1 rule 때문에 triple maximum=0이며 support를 사후 완화하지 않았다.

**IID199 + fixed-margin199**를 full과 각 era에서 독립 생성했다. 총398full histories+1194era histories=1592vectors, surrogate raw scalar cells=3,460,212다. 실제8vectors의17,388cells를 합치면3,477,600cells다. 독립 synthetic shape reference65536draws는 별도 고정 보조분포다. Seed260042, shape-reference seed260001; 정확한 child seeds·inventory hashes는 `null_progress.jsonl`에 있다. Main 실행203.54초, workers1.

## Full-history omnibus

각 score의 empirical p는199개 matching surrogate meta-score와 비교한 `(1+tail count)/200`이다. 모든 점수는 peer-only leave-self-out normalization을 사용한다. Real+null200행 각각에서 자기 자신을 제외한199행을 reference로 썼다. 양 track의 세 primary score를 전부 보고하며 유리한 결과를 선택하지 않았다.

| Track | Omnibus | 실제 score | Null median | Global empirical p | Track3 보정 | 전체6 보정 |
|---|---|---:|---:|---:|---:|---:|
| A / IID | FamilyMax | 8.424155 | 10.423328 | .775 | 1 | 1 |
| A / IID | SumOfAnomalies | .200457 | .200200 | .500 | 1 | 1 |
| A / IID | HigherCriticism | 0 | .459729 | 1.000 | 1 | 1 |
| B / fixed-margin | FamilyMax | 9.301101 | 10.061305 | .615 | 1 | 1 |
| B / fixed-margin | SumOfAnomalies | .228587 | .206775 | .275 | .825 | 1 |
| B / fixed-margin | HigherCriticism | 1.422183 | .467874 | .300 | .900 | 1 |

**Track A:** 단일 최대 편차와 diffuse 누적 모두 corrected evidence가 없다. **Track B:** marginal conditioning 후에도 시간·관계 구조를 구별할 corrected evidence가 없다. Fixed-margin Sum/HC가 null median보다 크지만 raw p=.275/.300이며, 이를 positive finding으로 승격하지 않는다. IID HC=0은 p≤.5의 weighted CDF excess가 양수가 없다는 뜻이다.

Sum은 equal-family 가중 `clip(z−1,0,4)` 합계다. HC도 equal-family weighting이며 p≤.5에서 양의 최대값이다. Kish factor는 A585.972834/B517.647106이고 독립 검정 수가 아니다. HC significance에 asymptotic independence 이론을 쓰지 않았다. Unit 사이의 중복·의존은 matching null의 전체 battery 계산으로 보존한다.

## Family별 maxima와 strongest unit

| Family | IID own-max p | Fixed-margin own-max p |
|---|---:|---:|
| marginal | .540 | 제외 |
| serial | .685 | .510 |
| run_gap | .180 | .515 |
| overlap | .490 | .335 |
| shape_distribution | .465 | .270 |
| shape_temporal | .620 | .400 |
| relational | .105 | .900 |
| spacing | .335 | .310 |
| spectral_entropy | .250 | .375 |

각 family를 내부 전체 검색의 own maximum과 비교한 값이다. 9/8family 보정값은 전부≥.945/1이다. 전체 battery의 maximum은 위 omnibus에서 다시 교정했다.

Full-history 최대 oriented z는 IID에서 **number5 lag1 transition G=7.472088**,z=8.424155,unit p=.020이다. Fixed-margin에서는 **number5 2-bit word G=7.477906**,z=9.301101,unit p=.015다. 둘은 상당히 중복되는 국소 진단이다. number5 block2 entropy deficit의 unit p=.010도 있으나 maximum z와는 다른 순위이고 독립 증거가 아니다. Strongest z의 전체검색 p는 .775/.615다. 국소 p를 구조 발견으로 해석하지 않는다. 모든 key/value/z/p는 `units_{track}_full.csv`에 보존했다.

## 시간 구간 robustness

동일 frozen battery를 early1–415/middle416–830/recent831–1245에 적용했다. 아래 값은 **global raw p / era scan18 보정 p**다. Full-history의6보정과 시대별18보정을 혼동하지 않는다.

| Era | IID FamilyMax | IID Sum | IID HC | Fixed FamilyMax | Fixed Sum | Fixed HC |
|---|---|---|---|---|---|---|
| Early | .005/.090 | .545/1 | 1/1 | .015/.270 | .230/1 | .495/1 |
| Middle | .175/1 | .745/1 | 1/1 | .450/1 | .740/1 | 1/1 |
| Recent | .040/.720 | .510/1 | 1/1 | .035/.630 | .550/1 | .380/1 |

Early maximum은 number40 gap GOF(z44.14/44.36), recent는 number18 gap GOF(z26.14/24.07)다. Middle의 최대는 IID number2 transition G, fixed number21 word2 G다. 동일 번호/통계가 세 era에서 반복되는 증거가 아니며 diffuse score도 반복적으로 유의하지 않았다. Robust z가 큰 값이어도 heavy-tailed gap GOF의 Gaussian p로 바꾸지 않았다.

199null의 p 해상도=.005로 era18보정의 최소값=.09다. 따라서 이 실행은 era-level .05 rejection을 확인할 해상도가 없다. 이 한계를 숨기거나 era 검색 수를 줄이지 않았다. Era 결과로 full battery 설정/가중치/판정을 변경하지 않았다.

## Leave-one-family-out

각 family를 제거할 때 real 및 모든 matching null score를 새 가중치로 다시 계산했다.

| Track | FamilyMax raw p 범위 | Sum raw p 범위 | HC raw p 범위 |
|---|---|---|---|
| IID | .510–.775 | .425–.610 | .575–1 |
| Fixed-margin | .560–.615 | .240–.385 | .260–.435 |

어떤 family를 빼도 유의한 omnibus는 나타나지 않았다. IID Sum 최소=.425(marginal 또는 shape_distribution 제외), fixed Sum 최소=.240(spectral_entropy 제외)다. Leave-out scan27/24보정은 전부1이다. 원래 없던 aggregate evidence가 특정 한 family 때문에 가려져 있었다는 근거도 없다. 삭제 결과를 고른 새 주 검정을 만들지 않았다.

## 증거 종합·H17 입력 원장

- [연구 증거 종합](research-evidence-synthesis.md): H1–H25 상태·Phase·보정 null 근거·예측 결과·후보 상태. H7 DEFERRED/H17 BACKLOG도 미실행으로 명시한다. 이전 Phase의 p-value를 수학적으로 결합하지 않았다.
- [Human-readable 후보 원장](weak-signal-candidates.md), [machine-readable JSON](weak-signal-candidates.json): 정확한 configuration, 평가 범위, paired CI, 시간/parameter sensitivity, null 근거, rank diversity, 원문·출력 경로 및 현재 파일 가용성을 기록한다.

| 모델 | 기록된 later 평균 Top6 | 범위 | 현재 분류 |
|---|---:|---|---|
| Gap Logistic | .849379 | 601–1244 | BASELINE / 우위 미확립 |
| GraphStructureModel | .8580 | 901–1245 | ENSEMBLE CANDIDATE, 탐색적 |
| GapShape | .8377 | 901–1245 | ENSEMBLE CANDIDATE, 탐색적 |
| Mirror | .826087 | 901–1245 | ENSEMBLE CANDIDATE, 탐색적 |
| MI | .8435 | 901–1245 | NOT CURRENTLY JUSTIFIED |

Gap의 후속901–1245 cadence 비교값은 .834783으로 다른 fit calendar다. 표의 초기 Gap와 다른 모델의 수치를 직접 같은 실험처럼 비교하지 않는다. 주요 후보의 Random/Gap paired95% intervals는0을 포함한다. Graph의 matched Frequency52 비교 하나는 양수지만 모든 baseline·robustness에 대한 확립된 우위가 아니다. MI의 높은 점추정치나 낮은 rank correlation만으로 후보를 승격하지 않았다.

Graph/GapShape/Mirror/MI의 해당 과거 report CSV/config/manifest는 현재 checkout에 없어 **HISTORICAL_UNAVAILABLE**로 표시했다. 문서의 수치·hash는 전사이며 실제 byte를 재검증했다고 주장하지 않는다. 과거 출력을 복원·재학습·재선택하지 않았다. H25가 후보를 새로 추가하지 않았고 H17 구현도 하지 않았다.

## 검증·Windows 실패 조사

H25 및 ledger 새 테스트 **30 passed**. 전체 suite: **1256 passed,4 failed,2 skipped (104.48s)**. Full suite가 green이라고 주장하지 않는다. 시작 시 아래 네 테스트만 실행해 같은4개의 `PermissionError: [WinError 5]`를 재현했다. Failure는 Windows `multiprocessing.connection.Pipe`의 `_winapi.CreateFile`에서 worker channel 생성 중 발생하며 기존 parallel tests의 통계 assertion까지 도달하지 못한다.

- `tests/test_complexity_search.py::test_independent_calibration_complete_null_determinism`
- `tests/test_random_matrix_search.py::test_worker_count_does_not_change_seeded_results`
- `tests/test_recurrence_pipeline.py::test_parallel_null_same_as_serial`
- `tests/test_topology_search.py::test_parallel_seeds_equal_serial_searches`

이전 연구의 source/data/tests를 고쳐 숨기거나 skip하지 않았다. H25 main은 deterministic serial 실행이라 이 named-pipe 경로를 사용하지 않으며199+199가 완료됐다. 환경 권한/간헐성을 넘어서 근본 원인을 확정했다고 주장하지 않는다. Baseline/full log는 `windows_baseline_tests.log`/`full_tests.log`에 보존했다.

`audit_result.json`: 모든1592개 saved full/era raw vectors에서 inventory parity, normalization·unit p·meta-score·omnibus p, family maxima와 leave-out 계산이 일치했다. 각 pool 대표3행은 독립 peer/rank/HC 계산과 대조했고,16representative histories를 seed부터 재생성했다. 보호된 기존420tracked files와 HEAD가 시작 hash와 같고 prospective30files가 동일하다. 모든1592histories를 seed부터 재생성한 것은 아니다.

통계/제약/Track분리/lag/run/gap/overlap/pair/triple/opportunity/entropy, 방향·rank·자기제외·동일 reference 크기, diffuse HC synthetic/null grid, correction·era·family-drop, deterministic rebuilding, ledger generation, archive read-only/failure guard, 미래 회차 거절과 prediction command 부재를 검증했다. Scientific code의 독립 review 후 archive failure guard를 보완하고 regression test를 통과했다.

## 산출물

`reports/randomness_battery/`는 Git-ignored 연구 출력이다. Raw null NPZ,200행 raw/z/p/center/scale/meta arrays, unit CSV, inventory/seeds,24omnibus rows,68family rows,51leave-out rows,HC curve,era robustness,audit와 시작 기록을 저장했다. `output_inventory.json`은 자기 자신을 제외한 산출물 SHA-256 inventory다. 별도 `final_summary.json`에 상태·검증·변경 목록을 보존한다.

`reports/randomness_battery/plots/`의 다음10개 PNG를 렌더링 후 contact sheet로 모두 시각 검사했다.

1. `01_family_overview.png`
2. `02_iid_family_maxima.png`
3. `03_fixed_margins_family_maxima.png`
4. `04_unit_anomalies.png`
5. `05_higher_criticism.png`
6. `06_sum_anomalies.png`
7. `07_omnibus_comparison.png`
8. `08_era_robustness.png`
9. `09_leave_family_out.png`
10. `10_evidence_map.png`

Plots는 inspection aids다. Evidence map의 null 구조/예측 우위/후보 bookkeeping은 다른 열이며 이전 p 결합을 뜻하지 않는다.

## 정확한 변경 파일 목록

기존 tracked 파일 수정5개:

- `.gitignore`
- `README.md`
- `docs/README.md`
- `docs/research-ideas.md`
- `src/cli.py`

신규 파일20개:

- `docs/randomness-battery-analysis.md`
- `docs/randomness-battery-results.md`
- `docs/research-evidence-synthesis.md`
- `docs/weak-signal-candidates.json`
- `docs/weak-signal-candidates.md`
- `docs/superpowers/plans/2026-10-18-phase26.md`
- `src/analysis/evidence_ledger.py`
- `src/analysis/randomness_battery.py`
- `src/analysis/randomness_diagnostics.py`
- `src/analysis/randomness_null.py`
- `src/analysis/randomness_omnibus.py`
- `src/analysis/randomness_statistics.py`
- `src/randomness_cli.py`
- `tests/test_evidence_ledger.py`
- `tests/test_randomness_battery.py`
- `tests/test_randomness_cli.py`
- `tests/test_randomness_diagnostics.py`
- `tests/test_randomness_null.py`
- `tests/test_randomness_omnibus.py`
- `tests/test_randomness_statistics.py`

생성된 ignored report 파일은 위 source 변경 목록과 구분하여 `output_inventory.json`에 파일별 기록한다. 원본 source/data 및 과거 prospective artifacts는 변경하지 않았다. H25에서 종료하며 H17을 자동 시작하지 않는다.
