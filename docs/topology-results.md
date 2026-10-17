# Phase 23 — H22 Topological Data Analysis 결과

**H22: TESTED / INCONCLUSIVE.** 검정한 H0 persistence는 corrected null evidence를 확보하지 못했다.
H1은 dependency 한계로 유보했으므로 전체 topology나 loop의 부재를 입증한 것은 아니다.
**PREDICTIVE_MODEL_NOT_JUSTIFIED / NOT CURRENTLY JUSTIFIED**다.
[방법](topology-analysis.md) · [사전 계획·review 보완](superpowers/plans/2026-10-18-phase23.md).

## 시작 상태와 범위

Git root는 `C:/Users/Samsung/OneDrive/Desktop/university/personal/lotto-pattern-lab`,branch는 main,
시작 SHA는 `36d10345c56e380e78cc16c7a484ea521fae3478`이었다. 시작 working tree는 clean이었다.
Phase22/H21 완료 상태와63artifact hashes를 확인한 뒤 시작했다.
README,docs/README,research-ideas,canonical CSV를 확인했고 무관한 source/data 변경은 없었다.
실제 본번호 자료는 정확히 **1–1245회**다. 개발1–900,이후901–1245로 구분한다.

## 구현한 범위와 검색공간

ripser/persim/gudhi는 모두 미설치다. 설치를 시도하지 않고 exact MST H0를 구현했다.
**H1_DEFERRED_DEPENDENCY_LIMITATION**이며 H1 loop가 없다는 결론은 아니다.
Persistence-diagram bottleneck/Wasserstein distance도 미구현이다.

Binary45의 Jaccard/Hamming,local-standardized frozen shape7의 Euclidean,
disjoint26/52draw activity rates의 Euclidean으로5configs를 고정했다.
Whole와 W208/416/624,stride104,마지막 endpoint도 포함한다.
Full은140cloud/560cells 중534eligible,development는95cloud/380cells 중362eligible다.
제외된26/18cells는 pilot 분산이 없거나 매우 작은 cell이며 선택적으로 real peak를 제외한 것이 아니다.
네 family는 H0 longest,total,entropy anomaly,top10% tail concentration이다.

Whole의 A/B point 수는1245,C26은47,C52는23이다. Rolling208/416/624에서 A/B는각 W,
C26은8/16/24,C52는4/8/12다. 같은 cell의 real/null point 수는 모두 같다.
Raw whole persistence를208-point persistence와 직접 비교하지 않는다.
H0는 finite n−1bars와 별도의 infinite component1개이며0 lifetime도 보존한다.

독립 pilot는 cutoff별 IID32,seed231001이다. Main seed230042에서 IID199/fixed199를 각각full/dev로 검색했다.
모든 surrogate가 자체 cloud/scaling/MST와 모든 rolling cell을 새로 만들고 자신의 global maximum을 찾았다.
Entropy만 양방향 |z|,나머지는 upper z이며 empirical global p에 Bonferroni4를 적용한다.
Benchmark는4개 complete full+development search의3.137/4.258/4.587/4.871초를 기록했고,
398histories의 serial 예상1676.911초가 실용적이어서199+199를 유지했다(workers3).
실제 full+development main experiment runtime은953.232초였다.

## Whole cloud와 거리 집중

| Cloud | Points | H0 longest | H0 total | Entropy | Tail |
|---|---:|---:|---:|---:|---:|
| A/Jaccard | 1245 | .666666667 | 671.000000000 | 7.115170760 | .124192747 |
| A/Hamming | 1245 | .133333333 | 123.911111111 | 7.105102316 | .134505022 |
| B/shape Euclidean | 1245 | 2.259718474 | 813.102379156 | 7.036863577 | .190886412 |
| C26/Euclidean | 47 | .583298111 | 23.466001963 | 3.825794152 | .122647071 |
| C52/Euclidean | 23 | .432585457 | 8.170809563 | 3.087989659 | .154111432 |

다른 단위/point 수의 위 raw summary는 서로 직접 비교하지 않는다.

| Cloud | Median pairwise | Median nearest | Distance variance | NN/median | Distance CV |
|---|---:|---:|---:|---:|---:|
| A/Jaccard | .909090909 | .500000000 | .006470781 | .550000000 | .088485280 |
| A/Hamming | .222222222 | .088888889 | .001213674 | .400000000 | .156770201 |
| B/shape Euclidean | 3.282711971 | .526887655 | 1.912694769 | .160503772 | .421298639 |
| C26/Euclidean | .631987566 | .507342537 | .004287691 | .802772972 | .103610364 |
| C52/Euclidean | .442725555 | .357712985 | .002520730 | .807979077 | .113404048 |

여기서 CV=distance std/median이다. Whole Jaccard는 CV<.1의 concentrated distance이지만 정확한 equidistant/duplicate cloud는 아니다.
Activity cloud의 NN/median도 약.80으로 높은 차원의 거리 집중을 보여준다. 이를 manifold 증거로 해석하지 않는다.
모든140cloud의 상세 진단은 `cloud_summary.csv`에 있다.

## Full global-max 결과

아래 raw값은 각 family의 pilot-standardized global winner다. Metric 단위가 다르므로 raw값 크기로 config를 서로 순위화하지 않는다.
Entropy의 z는 |z|이며 다른 세 family는 상방 z다.

| Family | Winner / interval / points | Raw | Global score | IID global / corrected | Fixed global / corrected |
|---|---|---:|---:|---:|---:|
| H0 longest | C52,W208,313–520,4 | .526656305 | 4.083085729 | .215 / .860 | .205 / .820 |
| H0 total | C52,W208,313–520,4 | 1.440887775 | 3.208623653 | .185 / .740 | .160 / .640 |
| H0 entropy anomaly | C26,W416,313–728,16 | 2.703041762 | 2.939753852 | .645 / 1 | .640 / 1 |
| H0 tail | C52,W416,830–1245,8 | .168191235 | 2.448300229 | .730 / 1 | .800 / 1 |

가장 강한 longest/total 결과도4-point activity cloud의3개 finite merge에서 나왔다.
Local z가 커 보이지만 surrogate가 자신의 모든 cell을 검색하면 더 큰 apparent structure가 자주 나온다.
Whole/rolling을 포함한 어떤 family도 두 null 중 하나에서도 Bonferroni4를 통과하지 못했다.

| Winner family | Observed−IID cell median | IID cell percentile | Observed−fixed cell median | Fixed cell percentile |
|---|---:|---:|---:|---:|
| Longest | +.086443877 | 100.000% | +.083930750 | 100.000% |
| Total | +.190401472 | 97.990% | +.184820631 | 99.497% |
| Entropy | −.002822648 | 4.523% | −.002672400 | 2.010% |
| Tail | +.012735764 | 91.960% | +.013228883 | 98.492% |

위 percentile은 선택된 동일 cell의 raw 통계 진단이며 local p나 corrected p가 아니다.
Longest의 local100%조차 complete-search global p≈.21과 양립한다.
Full family maximum의 null median(IID/fixed)은 longest3.202809269/2.836511176,total2.549761780/2.594466550,
entropy3.425648338/3.266885717,tail2.930972330/3.078983651이다.

## Rolling topology와 frozen Graph/RMT 비교

Whole보다 더 강한 raw persistence를 찾았다는 주장을 하지 않고 동일 cell의 finite-sample calibration을 사용했다.
Full의 네 winner 모두 rolling에 있었지만 모두 corrected gate를 실패했다.
같은 config/W의4summary feature trajectory와 lag1/2/4 recurrence만 descriptive로 저장했다.
가장 가까운 standardized feature pair는 A/Jaccard,W208,endpoint1144→1245,distance.255944048이었다.
101회 차이의 overlapping window이며 유의한 regime recurrence의 근거가 아니다.

Manifest hash를 확인한 기존 Graph/RMT outputs만 읽었고 refit하지 않았다.
Topology B/shape H0 longest와 RMT의 같은 W/endpoint를 비교했다.

| Frozen reference | Topology W | Matched endpoints | Spearman |
|---|---:|---:|---:|
| RMT largest eigenvalue | 208 | 11 | +.009090909 |
| RMT effective rank | 208 | 11 | −.054545455 |
| RMT largest eigenvalue | 416 | 9 | −.766666667 |
| RMT effective rank | 416 | 9 | +.266666667 |
| RMT largest eigenvalue | 624 | 7 | +.428571429 |
| RMT effective rank | 624 | 7 | +.321428571 |
| Graph W104 concentration | 208 | 10 | +.376901437 |

W416의 음의 eigenvalue 상관은 있지만 다른 W에서 같은 관계가 재현되지 않는다.
낮은 effective rank와 강한 H0 persistence의 일관된 대응도 확보하지 못했다.
Graph는 같은 endpoint라도 W104 대 W208로 span이 다르다. 이 상관들은 같은 history의 descriptive 관계이고
독립 검정 evidence나 예측 ranking correlation이 아니다.
Draw-set MST edge attribution도 tie와 point=draw라는 한계 때문에 유일한 persistent number group으로 해석하지 않는다.

## 개발 결정과 예측 생략

| Development family | IID global / corrected | Fixed global / corrected |
|---|---:|---:|
| H0 longest | .375 / 1 | .420 / 1 |
| H0 total | .190 / .760 | .225 / .900 |
| H0 entropy anomaly | .545 / 1 | .540 / 1 |
| H0 tail | .455 / 1 | .385 / 1 |

Passing family는 없고 selected_cell=null이다. 이후901–1245를 설정 선택에 쓰지 않았다.
구조 gate 실패로 causal regime/outcome mapping을 fit하지 않았고 TopologyStateModel을 만들지 않았다.
Random/Frequency26/Gap Logistic의 새 predictive comparison,paired bootstrap,후보 모델들과의 predictive rank 상관은 해당하지 않는다.
**PREDICTIVE_MODEL_NOT_JUSTIFIED**,ensemble은 **NOT CURRENTLY JUSTIFIED**이며 H17은 deferred/BACKLOG다.
`draw1247_phase23_topology` 준비 기능도 만들지 않았다. Prospective 관련 코드는 target/archive를 거부하는 negative guard뿐이다.
개발 결정 SHA256은 `0a7fdca9778238dfd433372585e993a54414cc601245fc105f2eb5a846a5e0fb`이다.

## 검증 방식과 산출물

최종 전체suite는 **1189 passed,1 skipped,0 failed**,369.85초였다.
Skip은 기존 `tests/test_predictive_models.py:52`의 optional LightGBM/XGBoost 미설치다.
Review 수정 이전의 별도 full run도1183passed/1skipped였으며,최종 suite는 추가6개 회귀까지 한 번에 포함한다.

Known synthetic clusters,duplicate zero edges,ties,independent SciPy MST,local-only scaling,
disjoint activity,point-count parity,own-null maximum,entropy direction,deterministic worker seeds,
source/target1246 거부,archive 부재,partial-output 보존과 개발-only gate를 테스트한다.
독립 read-only review에서 발견한 양 cutoff calibration count/seed 검증 누락은6개 RED 회귀로 재현했다.
Both-scope guard와 source hash guard로 수정한 후 신규Phase23 **56tests**가 통과했고 재검토에서도 추가 finding은 없었다.
현재 calibration 파일은 원래 올바르므로 numerical search를 재시작하지 않았다.

독립 감사는64pilots 전부의 raw/mean/std/eligible를 exact seed replay했다.
실제 full140+development95=235cloud는 별도의 shape/scaling,SciPy distance,Kruskal로 모든 finite deaths와 summary를 확인했다.
796개 저장 null vector의 independent standardization→own maximum→global p→Bonferroni4를 모두 검산했다.
두 null의 첫/마지막 replicate×두 scope인8개 main history도 exact replay했다.
모든 null의 point-count inventory,행합6,고정마진 보존을 확인했고 이전670artifact hashes와HEAD도 불변이었다.
398개 main history를 전부 두 번 생성한 것은 아니다. 상세 evidence는 `audit_result.json`이다.

Canonical raw-byte SHA256은 `3b7bb1e0a37c28ae4b4a97e098180d8407008ec007698c191ed6cf279db8225b`로 불변이다.
이전 문서·numerical history·prospective 기록은 보존했다. 원래 prospective archive가 없으므로 그 원본 byte 검증을 주장하지 않는다.

정확한 source 변경과 artifact hash는 로컬 `reports/topology/manifest.json`에 기록한다.
수치 원본은 `global_null_comparison.csv`,`full_metrics.csv`,`development_metrics.csv`,
`null_metrics_full.npz`,`null_metrics_development.npz`,`finite_sample_calibration.csv`다.
Cloud summaries/bars/MST edges,거리 진단,동일 point 수 state trajectory/recurrence,고정 Graph/RMT 비교도 저장한다.
`reports/topology/plots/`에는 distance concentration,H0 barcode,H0 diagram,real-vs-IID global maxima,
real-vs-fixed global maxima,matched summary distributions,rolling H0,state trajectory,Graph/RMT comparison의9개 PNG가 있다.
H1/predictive ranking plot은 해당 구현·모델이 없어 만들지 않았다. 그림은 inspection aid이며 검정을 대신하지 않는다.
`reports/topology/`는 기존 연구 산출물과 같은 방식으로 gitignore되며 source/test/docs는 그대로 uncommitted로 남긴다.

Git 변경 파일은18개다.

```text
.gitignore
README.md
docs/README.md
docs/research-ideas.md
docs/topology-analysis.md
docs/topology-results.md
docs/superpowers/plans/2026-10-18-phase23.md
src/cli.py
src/topology_cli.py
src/analysis/topology.py
src/analysis/topology_search.py
src/analysis/topology_diagnostics.py
src/analysis/topology_audit.py
tests/test_topology.py
tests/test_topology_search.py
tests/test_topology_cli.py
tests/test_topology_diagnostics.py
tests/test_topology_audit.py
```

실제1246 fetch/import/use/evaluation,canonical CSV 수정,과거 prospective evidence 수정은 하지 않았다.
기존 archive는 없으며 **PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**이다.
실제1247 snapshot 발행,commit/push,후속H23/H24/H25/H17 구현 없이 Phase23에서 종료한다.
