# Phase 14 결과 — H12 Dynamic Graph / Hypergraph Structure

**H12: TESTED / INCONCLUSIVE.** Graph는 탐색적 **ENSEMBLE CANDIDATE**, Hypergraph는 **NOT CURRENTLY JUSTIFIED**.

번호 관계망을 IID199회·fixed-margin199회의 동일한 전체 검색과 비교했다.
community 안정성의 보정 p-value는0.10(IID),0.05(fixed-margin)로 두 null에 걸쳐 일관된 근거가 부족했다.
edge·triple·graph persistence·frequency-controlled successor의 보정 p-value는 모두1이었다.
전체 node strength와 전체 triple 참여량은 각각5×빈도와10×빈도이므로 별도 관계 신호가 아니다.

## 시작 상태·범위

- Git root: `C:/Users/Samsung/OneDrive/Desktop/university/personal/lotto-pattern-lab`.
- branch `main`, 시작 SHA **`219a6e0e9dad9b0e011ea41d06208cd4f9d5ee1b`**.
- 지정한 root·branch·status, README3개와 CSV를 먼저 확인했다. 시작 상태는 clean이며 Phase13 완료 상태였다.
- 이전 Phase13 manifest의 전용 source/document/test hash를 확인했다.
- 본번호 **1–1245회**만 사용했다. bonus 제외,45개 binary series이며 매 draw6개 active다.
- CSV SHA-256: `3b7bb1e0a37c28ae4b4a97e098180d8407008ec007698c191ed6cf279db8225b`.
- **1246 fetch/import/파싱·설계·window/motif/model 선택·튜닝·평가에 사용하지 않았다.**
- [방법·수식](graph-hypergraph-analysis.md) · [사전 실행 계획](superpowers/plans/2026-10-18-phase14.md).

## Graph·Hypergraph 및 정확한 탐색 규모

Graph는 weighted co-occurrence adjacency, diag0이다. unique draw 하나는15개 pair edge를 만든다.
threshold **A>=2**, rolling **W={26,52,104}**, normalized weighted spectral **K={2,3}**를 고정했다.
strength/degree/density/clustering/common-neighbor/triangle/wedge/HHI와 raw cosine/correlation/Frobenius/Jaccard를 노출했다.
primary partition 안정성·graph persistence는 **겹치지 않는 window**끼리만 비교했다.

Hypergraph는 정렬한 unordered6개 본번호 set이다. pair990개와 triple14,190개를 모두 센다.
주 triple 검정은 support>=3이다. quadruple은 W104에서도 IID 기대count≈0.01047이므로 제외했다.
큰 lift만으로 희소 motif를 예측 근거로 삼지 않았다. pair/triple의 count·기대·lift·support·발생회차·간격·최근/과거 rate를 저장했다.

| 검색 범위 | history 하나의 후보 수 |
|---|---:|
| endpoint104,130,...,1222,1244 × W3 | 135 graphs |
| pair × W × endpoint | 133,650 |
| triple × W × endpoint | 1,915,650 |
| weighted partition | 270 |
| non-overlap community stability | 5,588 |
| non-overlap residual graph persistence | 2,794 |
| pooled frequency-controlled successor | 18 |
| 다섯 primary family 후보 합계 | **2,057,700** |

이 수는 서로 독립인 검정의 개수가 아니다.45개 끝점 사용은 계산 전 선언한 staging이며 real/null에 동일하다.
끝점1244의 successor가1245이므로1246 label은 없다. 모델은 이 grid와 달리 매 target에서 graph를 다시 계산했다.
누적1–1245 graph와 마지막 selected-window matrix는 descriptive reference다.

IID individual pair probability=1/66, expected node strength=2W/3,
edge-share HHI 기대=1/990+(1−1/66)/(15W)다.
binomial z는 검색 점수이며 local normal-theory p-value가 아니다.

## 가장 강한 구조와 global null

- **Edge27–31:**235–260회(W26), count5, IID expected0.39394, z=7.394865. 두 번호 own count는7,8이다.
- **Triple2–41–42:**131–156회(W26), count3, expected0.036646, lift81.8654, z=15.490998.
  크게 보이는 lift지만 IID197/199, fixed195/199회가 이 이상의 자체 최고 triple을 찾았다.
- **Community:**W52/K2,651–702회와807–858회, common nonisolates45개, ARI=0.462409.
  구성원과 두 partition은 `strongest_communities.json`에 모두 저장했다.
- **Graph-state persistence:**W26, 끝점494와858의 frequency-residual edge cosine=0.114606.
- **Successor:**W52 neighbor의 pooled residual correlation=0.014943가18개 중 최고였다.

| Family | Real maximum | IID global p | IID 보정 p | Fixed global p | Fixed 보정 p |
|---|---:|---:|---:|---:|---:|
| Edge | 7.394865 | .795 | 1.00 | .845 | 1.00 |
| Community stability | .462409 | .020 | .10 | .010 | .05 |
| Triple | 15.490998 | .990 | 1.00 | .980 | 1.00 |
| Graph persistence | .114606 | .465 | 1.00 | .535 | 1.00 |
| Successor information | .014943 | .955 | 1.00 | .945 | 1.00 |

각 surrogate가 모든 graph·subset·partition·stability·successor를 재구축하여 자신의 최대값을 선택했다.
p=(1+초과수)/(199+1), 다섯 family Bonferroni=min(1,5p)다. 해상도는0.005다.
community의 fixed 보정값은 **정확히0.05 경계**이며 IID에서는0.10이다.
두 null 중 유리한 것만 고르면 안 되므로 robust한 구조 발견으로 분류하지 않는다.
fixed-margin Curveball은 row6개·전체 번호 count를 보존하나 유한 mixing 한계가 있다.

## 빈도를 넘어선 successor 진단과 개발 선택

strength−5×own count는 정확히0이다. 전체 triple node participation−10×own count도0이다.
사용한 관계 score는 residual affinity to recent winners, within-community residual strength, clustering이다.
각 training window의45개 node에서 intercept+own frequency OLS 잔차로 바꾸고 표준화했다.
이는 선형 빈도 성분을 제거하며 모든 nonlinear confounding을 제거한다는 주장이 아니다.
Hypergraph는 직전 draw의 candidate 자신을 제외한 source pair 문맥에서 supported triple conditional rate를
own-rate prior로 shrink하고 같은 frequency regression을 적용했다.

세 window × 여섯 feature의18개 successor 진단은 모두 최고 r가0.014943 이하였고
전체 null 보정 p=1이었다. 따라서 **단순 빈도를 넘어선 successor 정보는 입증되지 않았다.**
Top6의 실제 hit와 own-history/recent-frequency 기대hit도 `successor_rows.csv`에 보존했다.
45node×45끝점을 독립 표본으로 취급한 p-value는 계산하지 않았다.

개발 target **401–900회(500개)**, 이후 **901–1245회(345개)**다.
이후 구간은 앞선 Phase에서도 사용한 역사이므로 pristine holdout이 아니다.

| 모델 | 동결 설정 | 개발 평균 Top6 hits |
|---|---|---:|
| GraphStructureModel | W52, neighbor/community 동일 평균, K3, threshold2 | .884 |
| HypergraphModel | W104, pair/triple support>=2, shrinkage10 | .836 |
| Frequency26 | W26 own frequency | .792 |
| equal-rank 조합 진단 | 개발에서만 계산, **허용 안 됨** | .824 |

Graph18개·Hypergraph12개의 사전 후보만 검색했다.
조합은 두 parent를 이기는 조건을 충족하지 않아 이후 모델에 추가하지 않았다.
동결 JSON의 설정 SHA-256은 **`a9712639a2cc76fc182f26a6b8767fdda32a7b218e1f362ee5395977e0f0390e`**다.
모든 target에서 history<T만으로 adjacency·community·subset·normalization·문맥을 다시 구성했다.
Gap fit cadence26/13 anchor와 실제 구조계산 cutoff(T−1)를 별도 열로 보존했다.

## 이후 평가

주 비교는 Gap cadence26,345개 target 모두의 deterministic Top6다. Random만 고정 seed의 무작위 tie 순위다.

| 모델 | 평균Top6 | Recall@6 | Recall@10 | Recall@15 | Mean winning rank↓ |
|---|---:|---:|---:|---:|---:|
| Random | .7681 | .1280 | .2198 | .3367 | 22.9585 |
| Frequency26 | .7739 | .1290 | .2072 | .3145 | 23.3362 |
| Gap Logistic | .8348 | .1391 | .2169 | .3309 | 23.0343 |
| GraphStructureModel | **.8580** | .1430 | .2338 | .3343 | 22.8024 |
| HypergraphModel | .8174 | .1362 | .2280 | .3454 | 22.7367 |
| Matched Graph Frequency52 | .7304 | .1217 | .2068 | .3242 | 23.5005 |
| Matched Hypergraph Frequency104 | .7507 | .1251 | .2150 | .3232 | 23.4256 |

| 모델 | hits0 | hits1 | hits2 | hits3 | hits4 | hits5 | hits6 | Top8≥5 | Top10≥5 | Top12≥5 | Top15≥5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Random |149|135|53|8|0|0|0|0|0|0|0|
| Frequency26 |142|144|54|5|0|0|0|0|0|0|4|
| Gap |141|135|55|13|1|0|0|0|1|1|4|
| Graph |129|144|64|8|0|0|0|0|0|1|2|
| Hypergraph |121|174|42|8|0|0|0|0|0|0|3|
| Frequency52 |146|150|45|4|0|0|0|0|0|1|4|
| Frequency104 |140|155|46|4|0|0|0|0|0|0|2|

**Top6/8/10/12/15 all-six 사건은 모든 모델에서0회**다. 희귀사건0은 확률0의 증거가 아니다.

paired circular block-bootstrap2000회, block26의 Top6 hit 차이와95% 구간:

| 모델 | 기준선 | 평균 차이 | 95% interval |
|---|---|---:|---|
| Graph | Random | +.0899 | [−.0291,.2058] |
| Graph | Frequency26 | +.0841 | [−.0580,.2116] |
| Graph | Gap | +.0232 | [−.0928,.1275] |
| Graph | matched Frequency52 | +.1275 | [.0029,.2435] |
| Hypergraph | Random | +.0493 | [−.0551,.1565] |
| Hypergraph | Frequency26 | +.0435 | [−.0551,.1391] |
| Hypergraph | Gap | −.0174 | [−.1159,.0870] |
| Hypergraph | matched Frequency104 | +.0667 | [−.0348,.1855] |

Graph의 matched Frequency52 대비 차이는 약하게 양의 구간이지만 **주요 Random/Frequency26/Gap 비교는 모두0을 포함**한다.
이는 여러 모델·지표·시작점 전체를 보정한 동시 신뢰구간이 아니다.
complete-search successor p=1과 함께 보면 빈도를 넘어선 일반적 예측 우위는 확립하지 못했다.

## 강건성·시간 안정성

| 모델 | early901–1015 | middle1016–1130 | recent1131–1245 | start1001 | start1101 |
|---|---:|---:|---:|---:|---:|
| Graph | .8522 | .8435 | .8783 | .8653 | .8621 |
| Hypergraph | .8261 | .8348 | .7913 | .8163 | .7862 |
| Gap | .7565 | .9130 | .8348 | .8653 | .8828 |
| Frequency26 | .6696 | .9043 | .7478 | .8122 | .7586 |
| Random | .7739 | .8261 | .7043 | .7673 | .6966 |

Graph는 세 era 모두0.8보다 높으나 Gap 대비 방향이 일관되지 않다.
start1001에서는 Gap과같고 start1101에서는−.0207이며95% 구간[−.2000,.1586]이다.
Hypergraph는 recent/start1101에서0.8 미만이며 같은104회 빈도 기준선도 이기지 못했다.
여러 시작은 같은 고정 예측열의 subset이며 재선택한 모델이 아니다.

Gap cadence13에서는 Gap 평균 .8319, Graph/Hypergraph 평균은 .8580/.8174로 그대로였다.
Graph−Gap=.0261 [−.0928,.1420], Hypergraph−Gap=−.0145 [−.1188,.1043]로 결론이 바뀌지 않았다.
긴 memory를 고려한 block52/104도 저장했다. Graph−Gap 구간은 각각[−.1043,.1362]/[−.1014,.1276]이며,
Graph−matched Frequency52는 [.0028,.2319]/[.0087,.2232]다. block104의 Graph−Random 하한은정확히0이다.
긴 block에서는 효과적인 독립 block 수가 작다는 한계도 있다.

사전30개 후보의 later sensitivity는 **설정 변경 없이 진단으로만** 계산했다.
Graph의 같은 neighbor/communityK3 규칙은 W26=.8348,W52=.8580,W104=.7710이다.
같은W52의K2=.8667로 K 하나에만 의존하지는 않지만104회로 늘리면 개선이 사라진다.
Hypergraph support2/shrink10은 W26=.7623,W52=.8174,W104=.8174,
W104 shrink5=.8058,support3=.7478이다. 희소 문맥 support 선택에 민감하다.
이후 최고 후보로 교체하거나 consensus를 사후 추가하지 않았다.

역사 전체의 selected 구조도 반복이 안정적이지 않았다.

| 선택된 subset | early1–415 count | middle416–830 | recent831–1245 | era당 IID expected |
|---|---:|---:|---:|---:|
| Edge27–31 |10|6|1|6.2879|
| Triple2–41–42 |3|0|0|.5849|

triple은136,146,149회(간격10,3)에서만 나타났고 이후에는 없었다.
각 era 안에 온전히 들어가는 non-overlap community pair의 최고 ARI는 .1596/.1856/.1713,
평균은 .0051/−.0017/.0018이었다. 전체 최고 .4624는 다른 era를 가로지르는 선택이다.
rolling trace와 adjacent-window raw 유사성은 별도 descriptive artifact이며 중첩 window의 안정성을 독립 지속성으로 해석하지 않는다.

## Rank diversity와 후보 판정

345개 target에서 번호 좌표를 맞춘 Spearman 및 TopK 교집합의 평균이다.

| 모델 | 비교 순위 | Spearman | Top6 overlap | Top10 | Top15 |
|---|---|---:|---:|---:|---:|
| Graph | Gap | .0611 |1.0435|2.7391|5.5072|
| Hypergraph | Gap | .0556 |1.0029|2.5942|5.2029|
| Graph | frozen Phase13MI |−.0062|.7420|2.0986|4.7652|
| Hypergraph | frozen Phase13MI |−.0640|.7942|2.2522|4.8580|

기존 Phase13 prediction CSV만 읽었다. MI refit/tuning은 하지 않았다.

- **GraphStructureModel: ENSEMBLE CANDIDATE — 탐색적 보존용.** 개발 .884에서 이후 .858로 약한 양의 성능이 남고,
  세 era에서 .84 이상이며 Gap과 rank 상관이 낮다. matched Frequency52 비교도 약하게 양의 구간이다.
  그러나 Random/Frequency26/Gap의 주요 구간은0을 포함하고 W104 민감도가 있다.
  이 분류는 미래에 검증할 다양성 후보라는 뜻이며 통계적으로 입증된 예측 신호라는 뜻이 아니다.
- **HypergraphModel: NOT CURRENTLY JUSTIFIED.** 낮은 상관만으로는 충분하지 않다.
  이후 Gap 대비 음의 차이, recent 약화, support 민감도와 불확실한 기준선 비교 때문에 후보 근거가 부족하다.

**H12는 PROMISING 조건을 충족하지 않는다.** 두 null에 걸친 unusual 구조와 강건한 예측 개선을 함께 확인하지 못했다.
표본·희소성 한계를 고려하여 모든 graph 관계를 영구 부정하는 결론도 내리지 않는다.
H17 최종 ensemble은 구현하지 않았다.

## 실행·그림·검증

2+2회 benchmark에서 sequential398회 예상은730.8초였다.
동일 검색을 workers4로199+199회 완주한 실제 시간은 **362.31초**였다. 결과에 따른 null 축소는 없었다.
개발 선택27.63초, 이후 cadence26평가86.61초이며 기존 NumPy/SciPy와 deterministic spectral만 사용했다.
새 package 설치나 network 데이터 수집은 없었다.

`reports/graph_hypergraph/plots/`에 다음10개 PNG를 저장했다.

```text
long_term_cooccurrence.png
recent_window_matrix.png
strongest_normalized_edges.png
community_ordered_matrix.png
graph_stability_through_time.png
strongest_triple_motif.png
real_vs_iid.png
real_vs_fixed_margins.png
model_ranking_example.png
frequency_vs_relational_score.png
```

그림은 evidence 자체가 아니다. 역사 target1245 ranking 예시를 <=1244만으로 재계산한 점수는 저장값과 정확히 일치했다.
binary/6-set/pairID/tripleID,135개 adjacency/triple table/partition/feature,
398개 null progress/maxima/representation hash, 실제 구조·successor·시대별 진단,
개발·later sensitivity·두 cadence의 모든 예측/지표/paired/diversity/protocol을 보존했다.
정확한 로컬 산출물50개(manifest자체 제외)의 목록·크기·SHA-256과 Git-visible source20개의 hash는
[run manifest](../reports/graph_hypergraph/run_manifest.json)에 있다.

전체 `python -m pytest -q -rs`: **488 passed,1 skipped**,129.96초.
skip은 기존 `tests/test_predictive_models.py:52`의 optional LightGBM/XGBoost 미설치다.
새 Phase14 테스트41개가 graph15pair/strength·rolling·유사성·빈도잔차·community/planted relation·triangle·triple·hyperedge,
동일한 null 최대값·재구축·determinism, 실제901/1245 prefix입력과 walk-forward cutoff,
개발전용 선택·순위상관·1246 suffix거부·archive publication 차단을 검증했다.
W104 matched-frequency 지원 누락을 평가 시작 시 발견하고 회귀 테스트를 추가해 Phase14 전용 단순 빈도 control로 수정했다.
개발 설정과 null 결과는 바꾸지 않았으며 두 이후 평가를 수정 후 다시 실행했다.
독립 코드 리뷰는 수식·causality·complete-search·빈도 control과 저장된 두 cadence 지표/cutoff를 확인했고
important/critical finding은 없었다.

## Prospective·변경 파일·종료 범위

**PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**.

`draw1247_phase14_graph`의 동결 설정·기존 archive 검증 **준비 gate는 구현했다**.
기존 verifier와 원본 protected inventory를 요구하며, 실제 CLI에서 archive 부재로 위 상태를 반환하는 것을 확인했다.
1246 target은 항상 거부한다. archive 복원·검증 후 명시적인 import/refit/publication 작업이 더 필요하므로
실제1247 publication 준비 완료를 주장하지 않는다.
**어떤 prospective snapshot도 발행하지 않았으며 부재한 archive·옛 순위·hash를 재구성하지 않았다.**

Git-visible 기존 수정5개:

```text
.gitignore
README.md
docs/README.md
docs/research-ideas.md
src/cli.py
```

새 파일15개:

```text
docs/graph-hypergraph-analysis.md
docs/phase14-results.md
docs/superpowers/plans/2026-10-18-phase14.md
src/analysis/graph_hypergraph_plots.py
src/analysis/graph_hypergraph_search.py
src/analysis/graph_structure.py
src/analysis/hypergraph_structure.py
src/backtest/graph_hypergraph.py
src/graph_hypergraph_cli.py
src/models/graph_hypergraph.py
src/phase14_freeze.py
tests/test_graph_hypergraph_pipeline.py
tests/test_graph_hypergraph_search.py
tests/test_graph_structure.py
tests/test_hypergraph_structure.py
```

추가 생성된 ignore된 보고서·그림·검증 script도 위 manifest에서 모두 열거한다.
canonical CSV·이전 Phase 전용 파일·HEAD 불변과 `git diff --check`를 확인했다.
**1246은 사용하지 않았고 commit/push는 하지 않았다.** Phase14에서 종료한다.
Modular/difference-space, entropy/compression, tensor, symmetry/reflection, 최종 ensemble을 구현하지 않았다.
