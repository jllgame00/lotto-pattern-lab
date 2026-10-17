# Phase 13 결과 — H11 Mutual Information / Transfer Entropy

**H11: TESTED / INCONCLUSIVE.** MI·TE 모델 모두 **NOT CURRENTLY JUSTIFIED**.

동일한 전체 pair/lag/history 검색을 허용한 IID199회·fixed-margin199회의 최대값과 비교했을 때
MI·CMI·TE·방향 비대칭·시간 안정성 중 **보정 후 유의한 family는 없었다**.
MI 모델의 이후 Top6 점추정치는 Gap보다 조금 높지만 신뢰구간과 시간적 강건성은 부족했다.
TE는 target 자신의 과거만 쓰는 baseline보다 이후 logloss가 나빴다.
따라서 dependence를 발견했다거나 directional predictive information이 확인됐다고 결론 내리지 않는다.
표본/희소성의 한계가 있어 모든 가능한 정보 관계를 부정하는 결과도 아니다.

## 시작 상태와 범위

- Git root: `C:/Users/Samsung/OneDrive/Desktop/university/personal/lotto-pattern-lab`.
- 시작 branch `main`, SHA **`45a9a04c53dbf08d88b99db6e81a95d634c7058c`**.
- `git rev-parse --show-toplevel`, branch, `git status --short` 및 지정 README3개·CSV를 먼저 확인했다.
  작업 트리는 clean이며 Phase12 완료 파일은 이전 manifest hash와 일치했다.
- canonical 본번호 **1–1245회만** 사용했다. bonus 제외, row당6개 active binary45개다.
- CSV SHA-256: `3b7bb1e0a37c28ae4b4a97e098180d8407008ec007698c191ed6cf279db8225b`.
- **1246은 fetch/import/파싱/특징·pair·parameter·model 선택/검증/튜닝에 사용하지 않았다.**
- [방법·수식·support](information-flow-analysis.md) · [사전 실행 계획](superpowers/plans/2026-10-18-phase13.md).

## 정확한 탐색 공간

lag={1,2,3,4,8,13,26}, target history k={1,2}, source history l={1,2}.
source는 t−lag,t−lag−1, targetpast는 t−1,t−2 중 지정한 길이를 사용한다.
MI/TE는 bits이며 원시 joint/marginal count, occupied states, sparse flag, raw 및 Miller–Madow corrected 값을 보존했다.
corrected 음수도 보존하며 보정값을 p-value로 해석하지 않는다.

| 항목 | 후보 cell |
|---|---:|
| directed cross pair | 1,980 |
| MI cross pair×lag | 13,860 |
| self-lag MI reference | 315 |
| CMI cross pair×lag | 13,860 |
| TE pair×lag×k/l | 55,440 |
| unordered directional asymmetry | 27,720 |
| stable TE relation/config | 55,440 |
| 다섯 primary family 후보 합계 | **166,320** |
| stability용 세 era의 추가 TE 평가 | 166,320 |

CMI는 TE(k=l=1)와 동일한 양이므로 고유/독립 검정처럼 세지 않는다.
행렬 내부 diagonal 계산 중 self MI315개는 reference로만 남기고 TE diagonal은 evidence에서 제외했다.
실제 전체 history는 MI/CMI/TE/asymmetry의 모든 후보가 support를 통과했고,
stable family는55,440개 중 **1,790개**가 세 era support·방향 조건을 통과했다.
기본 support는 정렬N>=300, future0/1각각>=20, MI source0/1각각>=20,
TE 모든 source/target history marginal state 각각>=8이다.

## 가장 강한 관계와 small-sample 진단

| family | 가장 강한 실제 관계 | 표본 | raw/score bits |
|---|---|---:|---:|
| MI | **2→33, lag13** | 1,232 | **0.0132759** |
| CMI | **2→33, lag13, k1/l1** | 1,232 | **0.0134154** |
| TE | **13→24, lag4, k2/l2** | 1,240 | **0.0221175** |
| directional asymmetry | **2↔33, lag13, k2/l1** | 1,232 | **0.0183982** |
| stable TE | **3→26, lag4, k2/l2** | era별410 | **0.0187644** |

최고 TE의 reverse24→13은0.0107989, 차이는0.0113185였다.
최고 asymmetry 설정은2→33=0.0195224,33→2=0.00112415로 차이0.0183982다.
self reference 최고는 번호5, lag8, MI0.007191이다. self reference의 국소 p를 primary global 증거로 쓰지 않았다.

source-only circular shift19회(seed130043)에서 최고 MI의 null평균은0.000692,
raw−null평균=0.012584, unadjusted local p=0.05였다.
최고 TE의 null평균은0.007290, raw−null평균=0.014828, local p=0.05였다.
하지만 이러한 선택된 local p는 전체 탐색과 family 보정 결과를 대체하지 않는다.
각 shift는 번호별 전체 빈도와 source 시간 구조를 보존하고 target/targetpast는 그대로 두지만,
row당6개 제약은 깨지므로 **valid Lotto history null과 구분**했다.
모든 relation의19회 분포·eligible replicate수·bias 진단을 NPZ/CSV에 저장했다.

전체 MI table의 sparse flag 비율은0%, TE는 **94.22%**였다.
모든 가능한 history state가 marginal support를 통과하더라도 joint state가 희소할 수 있다.
특히 큰 rawTE의 상당 부분은 sample/state-space bias일 수 있으며 Miller–Madow만으로 해결했다고 주장하지 않는다.

## IID / fixed-margin global maximum

각 history는45개 binary series와 모든 pair/lag/history/era/support filter를 새로 계산하고 자체 maximum을 선택했다.
실제 pair를 null에 고정하지 않았다. fixed-margin은 기존 Curveball row당20 trades로 row6개·전체 번호 빈도를 보존한다.
유한 mixing 한계는 남는다. seed130042, IID199 + fixed-margin199회, workers4다.

benchmark2+2회는0.545/0.561/1.081/1.099초, 순차398회 예상327.00초였다.
global검정 **165.69초**, 보조 source-shift 포함 전체 **179.89초**였다. 결과에 따른 축소는 없었다.

| family | IID global p | fixed-margin global p | IID / fixed family 보정 p |
|---|---:|---:|---:|
| MI | 0.045 | 0.035 | **0.225 / 0.175** |
| CMI | 0.145 | 0.120 | **0.725 / 0.600** |
| TE | 0.520 | 0.575 | **1.000 / 1.000** |
| asymmetry | 0.305 | 0.275 | **1.000 / 1.000** |
| stable TE | 0.115 | 0.110 | **0.575 / 0.550** |

empirical p=(1+exceedances)/200, family5 Bonferroni다. 번호1,980쌍 선택도 global maximum에 이미 포함된다.
두 null 중 유리한 것만 고르지 않았다. **보정을 통과한 directional information은 없다.**

## 시간적 안정성과 조건부 uncertainty

고정 era는1–415/416–830/831–1245다. 같은 pair/config의 rawTE:

| 관계 | early | middle | recent | 해석 |
|---|---:|---:|---:|---|
| MI2→33, lag13 | 0.01637 | 0.01346 | 0.00947 | MI값, 점차 감소 |
| CMI2→33, lag13,k1/l1 | 0.01669 | 0.01576 | 0.01244 | 모두support통과, sparse |
| TE13→24, lag4,k2/l2 | 0.04192 | 0.03206 | 0.02552 | early/recent는support미달이라 evidence에서 제외 |
| stable leader3→26, lag4,k2/l2 | 0.02580 | 0.02763 | 0.03335 | 세 erasupport·방향통과, global보정불통과 |

stable leader의 correctedTE는0.018764/0.018828/0.022789였다.
최솟값을 골라도 null에 같은 선택 자유도를 주면 특이하지 않았다.
416회 rolling(step104)의 forward/reverse·corrected·support도 저장했고 부족한 window는 그림에서 제외했다.

최고 TE13→24의 target-history conditional entropy는 **0.568648bits**,
source까지 추가한 empirical conditional entropy는 **0.546530bits**, 차이는0.022117bits다.
이는 같은 표본의 더 유연한 table에서 얻은 감소이며 미래 성능이 아니다.
CMI2→33도0.585110→0.571695bits지만 full null correction을 통과하지 않았다.
CMI와 TE의 중복 또는 same-realization 시간 진단을 독립 확인으로 해석하지 않았다.

## 개발 선택·동결

개발 target401–900회500개에서 MI14개·TE56개 사전 후보를 비교했다.
context support20, shrinkage20, positive corrected information weighting, trailing624를 사전 고정했다.
같은 training table의 K3/K5 cache만 공유하고 모든 목표에서 prefix에 맞춰 pair를 새로 선택했다.
full-history descriptive pair를 모델에 고정하지 않았다.

| 모델 | 동결 설정 | 개발Top6 | 개발401–650 | 개발651–900 |
|---|---|---:|---:|---:|
| MutualInformationModel | **lag1, incoming3** | **0.826** | 0.864 | 0.788 |
| TransferEntropyModel | **lag3,k2,l1,incoming3** | **0.846** | 0.896 | 0.796 |

개발 실행192.19초. configuration SHA-256:
`b3a126bd5ecb1ea374d9ef90d91e667d0fe054d69196ca75205ff11c7a0d5e30`.
이후 평가 전에 exclusive 생성했고 모든 이후 실행에서 이 설정을 유지했다.
개발 절반별 승자는 MI lag3→lag13, TE lag3/k1/l1→lag2/k2/l2로 바뀌어 선택 안정성도 제한적이다.

## 이후 walk-forward 901–1245

같은345개 목표. 각 target T는1..T−1만 받으며 정보량·정규화·pair/state 선택은 trailing624에서 매 목표 다시 한다.
Gap fit cadence26 및13을 비교했다. `outer_fit_cutoff`는 cadence anchor,
MI/TE/target-only의 실제 `training_cutoff`와 `information_training_cutoff`는 모두T−1로 저장했다.
이 역사 구간은 이전 Phase에서 사용했으므로 pristine holdout/prospective가 아니다.

| 모델 | 평균Top6 | Recall@6 | Recall@10 | Recall@15 | 평균당첨순위 |
|---|---:|---:|---:|---:|---:|
| Random | 0.7681 | 0.1280 | 0.2198 | 0.3367 | 22.9585 |
| Frequency26 | 0.7739 | 0.1290 | 0.2072 | 0.3145 | 23.3362 |
| Gap Logistic | 0.8348 | 0.1391 | 0.2169 | 0.3309 | 23.0343 |
| MI | **0.8435** | 0.1406 | 0.2184 | 0.3353 | 23.2261 |
| TE | **0.7797** | 0.1300 | 0.2169 | 0.3208 | 23.2184 |
| TargetHistoryBaseline | 0.7797 | 0.1300 | 0.2203 | 0.3271 | 23.1541 |

| 모델 | hits0 | hits1 | hits2 | hits3 | hits4 | hits5 | hits6 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Random | 149 | 135 | 53 | 8 | 0 | 0 | 0 |
| Frequency26 | 142 | 144 | 54 | 5 | 0 | 0 | 0 |
| Gap | 141 | 135 | 55 | 13 | 1 | 0 | 0 |
| MI | 134 | 140 | 62 | 9 | 0 | 0 | 0 |
| TE | 140 | 150 | 46 | 9 | 0 | 0 | 0 |
| TargetHistory | 145 | 142 | 49 | 7 | 2 | 0 | 0 |

Top8/10/12/15>=5 회수: Random0/0/0/0, Frequency0/0/0/4, Gap0/1/1/4,
MI0/1/3/4, TE0/0/1/2, TargetHistory0/0/1/4.
TE는 **1118회 Top15 pool에 all-six 1회**, 그 목표의 Top6 적중은2개였다.
다른 모델 및 TE의Top6/8/10/12 all-six는0회다. pool사건을 실제 six-number ticket 적중과 혼동하지 않는다.
희귀 사건의 퇴화 bootstrap 구간은 실제 사건확률0의 증거가 아니다.

paired circular block-bootstrap2,000회, block26, 평균Top6 차이와95% 구간:

| 모델 | 대비 Random | 대비 Gap |
|---|---|---|
| MI | +0.0754 [−0.0349,+0.1884] | +0.0087 [−0.0870,+0.1130] |
| TE | +0.0116 [−0.1014,+0.1188] | −0.0551 [−0.1623,+0.0464] |

다른 recall/rank/pool metric 구간은 paired.csv에 저장했다. 명목 구간이며 여러 모델·metric 전체의 동시 구간이 아니다.
cadence26 실행93.71초, cadence13 실행95.44초였다.

## Source 추가의 이후 예측 정보

TE와 같은 lag3/k2/l1, 같은 training/alignment/shrinkage의 TargetHistoryBaseline을 직접 비교했다.
45개 binary loss를 회차별 평균하여 회차 단위 block-bootstrap했다.

- TE mean logloss **0.395852** 대 target-only **0.394866** (natural-log units).
- TE−target-only **+0.000986**,95% **[+0.000553,+0.001409]**.
- 시작1001/1101도 차이+0.000720/+0.000751이며 구간이 각각[+0.000261,+0.001218]/[+0.000182,+0.001368]였다.

작은 차이지만 방향은 source 추가의 개선이 아니라 **악화**다.
따라서 높은 training TE나 target-history 대비 empirical entropy 감소가 실제 future uncertainty 감소로 이어졌다는 근거는 없다.
이 부정적 결과는 현재 estimator/model/range에 대한 것으로 모든 가능한 정보 모델의 불가능성을 증명하지 않는다.

## Robustness와 ensemble 후보

| 모델 | early901–1015 | middle1016–1130 | recent1131–1245 | 시작1001 | 시작1101 | cadence13 전체 |
|---|---:|---:|---:|---:|---:|---:|
| Gap | 0.7565 | 0.9130 | 0.8348 | 0.8653 | 0.8828 | 0.8319 |
| MI | 0.6783 | 0.9652 | 0.8870 | 0.8980 | 0.9241 | 0.8435 |
| TE | 0.6870 | 0.8609 | 0.7913 | 0.8245 | 0.8000 | 0.7797 |

multiple start는 같은 고정 예측열의 subset이다. 시작점을 바꿔 개발을 재선택하지 않았다.
MI의 later두구간 상승은 있으나 early가 약하고 paired 구간은0을 포함한다.
MI lag1/K5는0.8290,lag2/K3는0.8174,lag3/K3는0.8029,lag8/K3는0.7188로 lag 의존성도 있다.
TE lag3에서 k/l/K를 바꾼 사전 후보들은0.7014–0.7797이었다.
TE 전체 later sensitivity 최고는 lag13/k2/l2/K5의0.8406이지만, 이후를 보고 이 설정으로 갈아타지 않았다.
모든70개 후보별 이후 예측을 저장했으며 최종 설정은 그대로다.

| 모델 | Gap과 Spearman | Top6 overlap | Top10 overlap | Top15 overlap | 분류 |
|---|---:|---:|---:|---:|---|
| MI | **−0.2095** | 0.4783 | 1.5246 | 3.1623 | **NOT CURRENTLY JUSTIFIED** |
| TE | **−0.1663** | 0.7739 | 1.7130 | 3.6812 | **NOT CURRENTLY JUSTIFIED** |

정보 차별성과 MI의 약한 양의 점추정치는 탐색용으로 보존할 가치가 있지만,
시간적·paired 불확실성 조건을 함께 만족하지 못해 현재 ensemble 후보로 승격하지 않는다.
최종 ensemble은 만들지 않았다.

## 그림·산출물·검증

`reports/information_flow/plots/`에 **10개 PNG**를 저장하고 TE heatmap·fixed-margin 비교·edge그림을 직접 확인했다.

```text
mi_matrix.png
te_directed_matrix.png
te_asymmetry.png
strongest_pair_lag_profile.png
strongest_pair_temporal_stability.png
real_vs_iid.png
real_vs_fixed_margins.png
information_flow_inspection.png
model_ranking_example.png
source_added_logloss.png
```

network는 training<=900에서 frozen TE 설정의 corrected정보량 상위10개를 배치한 inspection 그림이다.
검정으로 확정된 edge/network가 아니며 community·centrality·hypergraph를 분석하지 않았다.
역사 target1245 예측은 <=1244 입력으로 재계산한 score와 저장 예측이 정확히 일치했다.

binary NPY, 전체 joint/raw/corrected/support NPZ, MI/TE search CSV,
source-shift 분포와 bias CSV, null maxima/progress/comparison, 전체 개발·later sensitivity,
동결 설정, 시대별/rolling/조건부 entropy 진단, training edge와 역사 ranking 설명,
두 cadence의 predictions/summary/paired/rank diversity/logloss/protocol을 저장했다.
Git-ignore된 로컬 산출물49개(manifest자체 제외)의 정확한 목록·크기·SHA-256은 `reports/information_flow/run_manifest.json`에 기록했다.
최종audit에서 저장joint table의maxima, 모든null p값, 실제예측의cutoff·순위·적중지표와 파일hash가 통과했다.

전체 테스트 `python -m pytest -q -rs`: **447 passed,1 skipped**,148.38초.
skip은 기존 `tests/test_predictive_models.py:52`의 optional LightGBM/XGBoost 미설치다.
새 Phase13 테스트61개는 모두 통과했다. known MI/CMI, planted direction, sparse/정확한 support 경계,
global-max/parity/determinism, 실제901/1245 table 입력, walk-forward cutoff, 개발전용 선택,
future suffix 및 archive block을 검증했다.
독립 리뷰의 fit provenance 지적은 effective cutoff/outer anchor 분리와 회귀 테스트로 반영했다.
Frequency는 지표로 비교하고 사용자 지정대로 paired reference는 Random·Gap 두 개다.

## Prospective와 변경 파일

**PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**.

`draw1247_phase13_informationflow`의 frozen설정·원본 archive 검증 준비 gate는 구현했다.
실제 CLI가 archive 부재 시 위 상태로 거부하는 것을 확인했다.
archive가 있어도 원본 inventory와 기존 phase별 verifier를 요구한다.
준비 gate는 실제1246 import/refit 또는1247 발행을 수행하지 않으며 완전한 publication 준비 완료를 주장하지 않는다.
**1246·1247 prospective snapshot을 발행하지 않았고 부재한 archive/옛 예측/hash를 재구성하지 않았다.**
원본 CSV·기존 Phase12 전용 파일·HEAD 불변과 `git diff --check` 통과를 확인했고 commit/push는 하지 않았다.
Phase13에서 멈추고 full Graph/Hypergraph, modular, entropy/compression, tensor, symmetry/reflection, final ensemble을 구현하지 않았다.

기존 수정5개:

```text
.gitignore
README.md
docs/README.md
docs/research-ideas.md
src/cli.py
```

새 파일14개:

```text
docs/information-flow-analysis.md
docs/phase13-results.md
docs/superpowers/plans/2026-10-18-phase13.md
src/analysis/information.py
src/analysis/information_plots.py
src/analysis/information_search.py
src/backtest/information_flow.py
src/information_cli.py
src/models/information_flow.py
src/phase13_freeze.py
tests/test_information.py
tests/test_information_models.py
tests/test_information_pipeline.py
tests/test_information_search.py
```

총19개 source/document/test 파일이다. 생성된 로컬 보고서·그림·검증 script는 위 run manifest의 목록을 기준으로 한다.
