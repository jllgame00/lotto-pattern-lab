# Phase 11 결과 — H9 Delay Embedding / Recurrence Geometry

**H9: TESTED / INCONCLUSIVE**. **Ensemble: NOT CURRENTLY JUSTIFIED**.

**비슷한 과거 상태가 비슷한 미래 결과로 이어지는가?**
이 실험에서는 이를 뒷받침하는 안정적인 증거를 확인하지 못했다. 높은 DET와 긴 diagonal은
IID·fixed-margin에서도 나타났다. 가장 유리한 successor 관계도 전체 탐색과 family 보정을
통과하지 못했고, 개발 선택 모델은 이후 구간에서 Gap Logistic을 개선하지 못했다.
가능한 모든 hidden state를 부정하는 결과는 아니다.

## 실행 경계

- 저장소: `C:/Users/Samsung/OneDrive/Desktop/university/personal/lotto-pattern-lab`
- 시작 브랜치 `main`, 시작 SHA `27e545bd138627e671abd642c4149bb96022ed45`.
  `docs: reorganize research documentation in Korean` checkpoint, 작업 트리 clean 및 필수 경로 확인 후 시작.
- 역사 연구 cutoff는 **1245**. 1246회는 수집·import·열람·검증·선택·평가 어디에도 사용하지 않았다.
- 원본 CSV SHA-256: `3b7bb1e0a37c28ae4b4a97e098180d8407008ec007698c191ed6cf279db8225b`.
- 구조 검정: 1–900회로 관측 재구축, scaler 1–400회, 상태 끝점 661–899회,
  successor 최대 900회. 사전 고정한 239개 연속 끝점으로 계산량을 제한했다.
- 예측 개발: 401–900회 500개 목표. 이후 평가: 901–1245회 345개 목표.
  이전 Phase가 이미 사용한 역사이므로 pristine holdout 또는 새 prospective 증거라고 부르지 않는다.
- [방법론·제외 규칙·실행 명령](recurrence-analysis.md). 기존 frozen protocol과 원본 prospective 문서는 수정하지 않았다.

## 표현과 탐색 공간

| 표현 | 관측 차원 | metric | embedding 유효 차원 |
|---|---:|---|---|
| A: 여섯 본번호 binary | 45 | Hamming, Jaccard | 90 / 135 / 180 |
| B: deterministic draw shape | 13 | standardized Euclidean, 원래 좌표 cosine | 26 / 39 / 52 |
| C: whole-system rolling rate | 45, W10/26/52 | standardized Euclidean, 원래 좌표 cosine | 90 / 135 / 180 |

m={2,3,4}, τ={1,2,4,8,13,26}. A 36 + B 36 + C 108 = **180 설정**.
recurrence는 k10 directed graph의 union과 정확한 eligible edge 하위 10%의 두 가지다.
다섯 family와 교차한 **1,800 cell** 중 successor는 graph에 독립적이어서 고유 통계는 1,620개다.
고정 density의 RR은 증거로 사용하지 않았다. RQA 최소 diagonal/vertical 길이는 2다.
예측 선택은 nearest 180 + analog 1,440 + continuation 2,880 = **4,500 후보**였다.

예측 T는 S_(T−1)만 사용한다. 길이 L trajectory의 보수적 raw support는
I_t=[t−h,t], h=(m−1)τ+W−1+L−1이며 A/B는 W=1이다.
과거 끝점 j는 **j+1<T−1−h**일 때만 유효하다. 상태뿐 아니라 successor도 현재 raw support와 분리한다.
RQA 쌍은 |i−j|>h+1을 적용한다. 관측 사이 빈 구간도 제외하므로 보수적이다.
불완전한 초기 상태를 축소해 사용하지 않는다. trajectory는 정렬된 L=2/3개 상태 거리의 평균이다.

## Distance concentration

아래는 각 family/metric에서 m·τ·W에 따른 범위다. metric 간 수치 크기를 직접 비교하지 않는다.
각 180개 설정의 median, std, variance, NN q10/median/q90와 ratio는
`reports/recurrence/real_search.csv`에 모두 보존했다.

| 표현/metric | pairwise median 범위 | nearest median / pairwise median |
|---|---:|---:|
| A Hamming | 0.2222–0.2444 | 0.6364–0.8095 |
| A Jaccard | 0.9091–0.9565 | 0.7703–0.8885 |
| B Euclidean | 6.7346–9.8656 | 0.4570–0.6503 |
| B cosine | 0.0191–0.0360 | 0.0520–0.1508 |
| C Euclidean | 13.6928–22.3957 | 0.7760–0.9352 |
| C cosine | 0.1125–0.4007 | 0.6282–0.9059 |

A Jaccard와 일부 C Euclidean은 가까운 상태도 일반적인 상태에 비해 크게 가깝지 않다.
B cosine에서는 가까운 상태를 쉽게 찾지만, sum 등 큰 좌표가 방향을 지배할 수 있다.
어느 경우도 거리 분리 자체가 미래 예측을 보장하지 않는다.

## 전체 null 탐색

IID **199회**, fixed-margin **199회**를 모두 실행했다. fixed-margin은 기존 Curveball
20 trades/row이며 행당 6개와 1–900회의 번호별 빈도를 정확히 보존한다. 유한 mixing의 한계는 남는다.
각 history에서 관측·scaler·embedding·거리·recurrence·RQA·successor를 재계산하고 자체 최대값을 기록했다.
개발의 K/weight 최적화 점수는 이 구조 p-value의 대상이 아니다. 그 모델 선택은 별도 이후 평가로 검증했다.

benchmark 2+2회는 각각 3.417/3.401/3.824/3.733초, 순차 398회 예상 1,430.2초였다.
4개 CPU 프로세스로 본 검정 전체 **740.73초**. seed 110042, benchmark seed 110000.
결과에 따라 surrogate 수나 탐색 범위를 줄이지 않았다. empirical p의 최소 간격은 0.005다.

| family | 가장 강한 실제 raw 통계 | IID global p | fixed-margin global p | IID / fixed 보정 p |
|---|---:|---:|---:|---:|
| DET | 0.98455 | 0.840 | 0.805 | 1.000 / 1.000 |
| Lmax | 51 | 0.435 | 0.470 | 1.000 / 1.000 |
| laminarity | 0.98901 | 0.885 | 0.850 | 1.000 / 1.000 |
| recurrence-time CV | 5.47957 | 0.435 | 0.430 | 1.000 / 1.000 |
| −Spearman(distance, successor overlap) | 0.02407 | 0.080 | 0.085 | 0.400 / 0.425 |

보정은 family 5개의 Bonferroni이며, null 종류를 골라 유리한 결론을 내리지 않는다.
DET 최대: C/W52/m4/τ1/cosine/density.
Lmax 최대: C/W52/m4/τ26/Euclidean/kNN.
laminarity 최대: C/W52/m4/τ1/Euclidean/density.
recurrence-time CV 최대: C/W52/m3/τ8/Euclidean/density.
선 길이·entropy·trapping time·recurrence-time 요약을 포함한 전체 local 결과는 `real_search.csv`에 있다.
선택된 구조의 rolling DET·Lmax·laminarity·recurrence time은 시기에 따라 변하지만,
비교 IID·fixed-margin 그림에서도 비슷한 변화가 나타난다. 그림에 대한 추가 유의성 주장은 하지 않는다.

## 1차 결과: state distance → successor similarity

가장 유리한 local 관계는 **C/W52/m4/τ26/cosine**, 유효 unordered pair **5,886개**였다.
Spearman은 **−0.02407**이며 successor Jaccard는 overlap의 단조변환이므로 rank 관계가 같다.
ordinary pair overlap은 **0.79579**, 이전 nearest pair overlap은 **0.81481**이었다.
Jaccard는 각각 **0.07658 / 0.07772**. 이 차이를 독립 표본 검정으로 과장하지 않는다.
surrogate에도 180개 설정에서 최선의 관계를 찾게 한 결과 family 보정 p=0.400/0.425다.

그림용으로 개발 DET가 최대인 설정에서는 ρ=**+0.00316**, ordinary overlap 0.79835,
nearest overlap 0.87432였다. 가까운→먼 decile 평균 overlap은
0.798 / 0.780 / 0.796 / 0.776 / 0.810 / 0.845 / 0.789 / 0.803 / 0.784 / 0.803이다.
단조 감소가 없으며, nearest 하나의 요약만으로 예측 근거를 선언할 수 없다.
**시험한 표현에서 analog forecasting을 뒷받침하는 재현성 있는 successor 근거는 확보되지 않았다.**

## 개발 선택과 동결

| 모델 | 표현 | m / τ | metric | K / weight / L | 개발 Top6 |
|---|---|---|---|---|---:|
| NearestSuccessorBaseline | B | 2 / 26 | cosine | 1 / uniform / 1 | 0.908 |
| RecurrenceAnalogModel | B | 2 / 13 | standardized Euclidean | 20 / uniform / 1 | 0.924 |
| RecurrenceContinuationModel | C W52 | 4 / 13 | standardized Euclidean | 5 / inverse / 3 | 0.900 |

`reports/recurrence/selected_configuration.json`은 이후 평가 전에 exclusive 생성했다.
canonical selection hash:
`77ea741a84c689a2ca55a6f1f8ab942c30af4a2460995130ca0a082676fde3fa`.
두 평가 protocol 모두 이 hash를 참조하며 평가 전후 byte 동일성을 검사했다.
개발 재실행은 38.30초, 이후 cadence26은 63.90초, cadence13은 51.74초였다.

## 이후 walk-forward: 901–1245

모든 모델이 같은 345개 목표를 사용한다. 현재 관측과 analog 풀은 매 회차 갱신하고,
Euclidean scaler와 Gap Logistic fit은 26회 cadence로 갱신한다. tie는 기존 번호 오름차순 규칙이다.

| 모델 | 평균 Top6 | Recall@6 | Recall@10 | Recall@15 | 평균 당첨번호 순위 |
|---|---:|---:|---:|---:|---:|
| Random | 0.7681 | 0.1280 | 0.2198 | 0.3367 | 22.9585 |
| Frequency26 | 0.7739 | 0.1290 | 0.2072 | 0.3145 | 23.3362 |
| Gap Logistic | 0.8348 | 0.1391 | 0.2169 | 0.3309 | 23.0343 |
| Nearest successor | 0.7855 | 0.1309 | 0.2135 | 0.3213 | 23.1072 |
| Recurrence analog | 0.7362 | 0.1227 | 0.2058 | 0.3261 | 23.2353 |
| Recurrence continuation | 0.7884 | 0.1314 | 0.2309 | 0.3473 | 22.9024 |

Top6 hits 0/1/2/3/4/5/6 분포:

| 모델 | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Random | 149 | 135 | 53 | 8 | 0 | 0 | 0 |
| Frequency26 | 142 | 144 | 54 | 5 | 0 | 0 | 0 |
| Gap Logistic | 141 | 135 | 55 | 13 | 1 | 0 | 0 |
| Nearest successor | 148 | 130 | 60 | 7 | 0 | 0 | 0 |
| Recurrence analog | 151 | 138 | 52 | 4 | 0 | 0 | 0 |
| Recurrence continuation | 142 | 140 | 57 | 6 | 0 | 0 | 0 |

Top8/10/12/15가 당첨번호 ≥5개를 포함한 횟수:
Random 0/0/0/0, Frequency26 0/0/0/4, Gap Logistic 0/1/1/4,
nearest 0/0/0/1, analog 0/0/0/3, continuation 0/0/1/9.
모든 모델의 Top6/8/10/12/15 all-six 사건은 **0회**였다.
희귀 사건의 bootstrap 구간이 0으로 퇴화할 수 있으며 실제 사건 확률이 0이라는 뜻은 아니다.

paired circular block-bootstrap 2,000회, block26, 평균 Top6 차이와 95% 구간:

| 모델 | 대비 Random | 대비 Gap Logistic |
|---|---|---|
| Nearest | +0.0174 [−0.0899, +0.1247] | −0.0493 [−0.1594, +0.0580] |
| Analog | −0.0319 [−0.1536, +0.0783] | −0.0986 [−0.1884, −0.0058] |
| Continuation | +0.0203 [−0.0812, +0.1217] | −0.0464 [−0.1420, +0.0435] |

이 구간은 명목상 paired uncertainty이며 여러 모델·metric·기간 전체에 대한 동시 신뢰구간은 아니다.
나머지 recall·rank·candidate-pool 차이와 구간은 각 `walk_forward_*/paired.csv`에 저장했다.

## 강건성과 정보 차별성

평균 Top6:

| 모델 | early 901–1015 | middle 1016–1130 | recent 1131–1245 | 시작1001 | 시작1101 | cadence13 전체 |
|---|---:|---:|---:|---:|---:|---:|
| Nearest | 0.7739 | 0.8000 | 0.7826 | 0.7755 | 0.7862 | 0.7855 |
| Analog | 0.7391 | 0.6870 | 0.7826 | 0.7347 | 0.8000 | 0.7362 |
| Continuation | 0.7217 | 0.7478 | 0.8957 | 0.8204 | 0.8897 | 0.7913 |

multiple start는 동일하게 고정된 예측열의 이후 subset이다. start를 바꿔 설정을 재선택하지 않는다.
cadence13 sensitivity는 scaler/Gap fit 빈도를 바꾸고 bootstrap block도 13으로 변경했다.
그때 Random 0.7681, Frequency26 0.7739, Gap Logistic 0.8319였다.
continuation의 최근 상승만으로 안정적인 우위를 주장할 수 없다.

개발 안정성: nearest는 401–800/501–900에서도 B/m2/τ26/cosine을 유지했다.
analog는 두 인접 구간에서 B/m2/τ26/cosine/K5/inverse로 바뀌어 m 외의 설정이 불안정했다.
continuation의 C/W52/m4/τ13/Euclidean은 유지됐지만 early에서는 L2/K10으로 바뀌었다.

Gap Logistic과의 회차별 값의 평균:

| 모델 | 전체 ranking Spearman | tie-aware score rank Spearman | Top6 overlap | Top10 overlap | Top15 overlap |
|---|---:|---:|---:|---:|---:|
| Nearest | −0.0478 | −0.0144 | 0.6261 | 1.8232 | 4.8000 |
| Analog | −0.0560 | −0.0464 | 0.6667 | 1.9971 | 4.6058 |
| Continuation | −0.0433 | −0.0351 | 0.6870 | 1.9130 | 4.6986 |

score는 calibrated probability로 해석하지 않고 scale에 불변인 rank correlation만 비교했다.
상관은 낮지만 reasonably stable positive performance 조건을 만족하지 않아 **NOT CURRENTLY JUSTIFIED**다.
최종 ensemble은 만들지 않았다.

## 그림과 산출물

`reports/recurrence/plots/`에 9개 PNG를 저장하고 null 비교·rolling 그림을 직접 확인했다.

1. `real_recurrence.png`
2. `iid_recurrence.png`
3. `fixed_margin_recurrence.png`
4. `rqa_real_null.png`
5. `nearest_analog_example.png`
6. `state_distance_successor.png`
7. `rolling_recurrence.png`
8. `nearest_distance_history.png`
9. `ranking_example.png`

recurrence 3개 그림은 같은 개발 DET 선택 설정과 같은 끝점 구간을 쓴다.
analog/순위 예시는 **역사 목표 1245회**, 실제 평가와 동일한 fit cutoff **1238회**이다.
개발 선택 구조의 그림은 예측 모델 선택과 구분한다. visual block은 증거가 아니다.

기계 판독 산출물은 benchmark, analysis metadata, real search/maxima, null maxima/progress,
global null comparison, frozen selection, development candidates/stability/runtime,
selected successor diagnostic/deciles, rolling RQA, nearest example/distance history 및
각 cadence의 predictions/summary/paired/gap correlations/protocol이다.
로컬 reports는 기존 프로젝트 관례대로 Git-ignore하며, 이 문서에 핵심 결과와 설정 hash를 보존했다.

## Prospective와 완료 검증

**PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**.

1247회 준비 기능은 frozen configuration 로딩과 원본 archive 검증 gate까지 구현했다.
archive가 없으면 즉시 거부한다. 복원 후에는 원래 inventory에 있는 Phase 5–10 전체 구성과
phase별 verifier를 통과해야 한다. 임의의 몇 개 파일을 복원한 것으로 준비 완료를 표시하지 않는다.
검증된 1246회의 명시적 import/refit와 실제 발행은 후속 단계이며, 이번 실행은 수행하지 않았다.
기존 archive의 byte-integrity를 이 laptop에서 확인했다고 주장하지 않는다.
1246·1247 신규 prospective snapshot을 만들지 않았고 옛 artifact·hash·예측을 재구성하지 않았다.

전체 테스트: **324 passed, 1 skipped**, 87.41초.
명령은 `python -m pytest -q -rs`이며 skip은 기존 optional BoostingModel 테스트의
LightGBM/XGBoost 미설치 때문이다. 새 Phase 11 테스트는 모두 통과했다.
현재 환경에서는 기존 `.deps/docs-checks`를 PYTHONPATH로 지정했고 접근 제한 때문에 승인된 실행 환경을 사용했다.
`git diff --check` 통과, canonical data 변경 없음, HEAD는 시작 SHA 그대로다. commit/push는 하지 않았다.

## 정확한 변경 파일

기존 파일 수정 5개:

- `.gitignore`
- `README.md`
- `docs/README.md`
- `docs/research-ideas.md`
- `src/cli.py`

새 파일 10개:

- `docs/recurrence-analysis.md`
- `docs/phase11-results.md`
- `src/analysis/recurrence.py`
- `src/analysis/recurrence_search.py`
- `src/models/recurrence.py`
- `src/backtest/recurrence.py`
- `src/phase11_freeze.py`
- `src/recurrence_cli.py`
- `tests/test_recurrence.py`
- `tests/test_recurrence_pipeline.py`

Git-ignore된 로컬 생성 파일은 아래와 같다. `reports/recurrence/` 기준 경로이며
최종 `run_manifest.json`에 각 artifact의 실제 SHA-256과 검증 결과를 저장한다.
이 hash들은 새 Phase 11 산출물에 대한 것으로, 부재한 과거 prospective hash를 대신하지 않는다.

```text
analysis_metadata.json
benchmark.json
development_candidates.csv
development_stability.csv
global_null_comparison.csv
nearest_analog_example.json
nearest_distance_history.csv
null_maxima.csv
null_progress.jsonl
real_maxima.json
real_search.csv
rolling_rqa.csv
selected_configuration.json
selected_successor_diagnostic.json
selection_runtime.json
successor_deciles.csv
run_manifest.json
plots/fixed_margin_recurrence.png
plots/iid_recurrence.png
plots/nearest_analog_example.png
plots/nearest_distance_history.png
plots/ranking_example.png
plots/real_recurrence.png
plots/rolling_recurrence.png
plots/rqa_real_null.png
plots/state_distance_successor.png
walk_forward_13/gap_correlations.csv
walk_forward_13/paired.csv
walk_forward_13/predictions.csv
walk_forward_13/protocol.json
walk_forward_13/summary.csv
walk_forward_26/gap_correlations.csv
walk_forward_26/paired.csv
walk_forward_26/predictions.csv
walk_forward_26/protocol.json
walk_forward_26/summary.csv
```

Wavelet/SSA, information/Transfer Entropy, graph/hypergraph, modular, entropy/compression,
tensor, symmetry/reflection, final ensemble은 구현하지 않았다. Phase 11 역사 연구와 검증에서 멈춘다.
