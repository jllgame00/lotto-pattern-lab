# Weak-signal 후보 원장

약한 역사 점추정치와 다양성을 보존하는 연구용 원장이다. **Validated ensemble이나 미래 예측 우위의 판정이 아니다.** GraphStructureModel·GapShapeModel·MirrorModel의 ENSEMBLE CANDIDATE는 탐색적 분류이며, Gap Logistic은 비교 baseline, MI는 NOT CURRENTLY JUSTIFIED로 유지한다. H17 최종 ensemble은 BACKLOG다.

범위·수치·판정의 canonical 기록은 [JSON](weak-signal-candidates.json), 가설 전체는 [증거 종합](research-evidence-synthesis.md)에 있다. 문서에서 전사한 정밀도만 보존한다. null이나 diversity가 다른 것은 예측력이 있다는 뜻이 아니다. 주요 paired CI는 명목 95% circular block-bootstrap 구간이며 모델·지표·시작점 전체의 동시구간이 아니다. 동일 역사 구간의 비교와 sensitivity를 독립 반복으로 세지 않는다.

| 모델 | 출처 Phase | 역사 평가 범위 | 평균 Top6 | 후보 판정 |
|---|---|---|---:|---|
| Gap Logistic | 3–4; 비교 재사용 Phase11–20 | 초기 primary601–1244(644targets), robustness starts401/501/601/701/801; 후속901–1245(345targets) | 0.849379 | BASELINE / 우위 미확립 |
| GraphStructureModel | 14 / H12 | 구조1–1245; 개발401–900(500targets); 이후901–1245(345targets) | 0.8580 | ENSEMBLE CANDIDATE (탐색적) |
| GapShapeModel | 15 / H13 | 구조1–1245; 개발401–900(500targets); 이후901–1245(345targets) | 0.8377 | ENSEMBLE CANDIDATE (탐색적) |
| MirrorModel | 18 / H16 | 구조1–1245; 개발401–900(500targets); 이후901–1245(345targets) | 0.826087 | ENSEMBLE CANDIDATE (탐색적) |
| MutualInformationModel (MI) | 13 / H11 | 구조1–1245; 개발401–900(500targets); 이후901–1245(345targets) | 0.8435 | NOT CURRENTLY JUSTIFIED |

## Gap Logistic

**BASELINE / 우위 미확립** — 반복 비교용으로 보존하지만 validated signal 또는 신규 ensemble 채택 판정은 아니다.

출처: [docs/predictive-experiments.md](../docs/predictive-experiments.md) · [docs/gap-prize-research.md](../docs/gap-prize-research.md) · [docs/regime-research.md](../docs/regime-research.md) · [docs/phase15-results.md](../docs/phase15-results.md) · [docs/phase18-results.md](../docs/phase18-results.md).

역사 범위: 초기 primary601–1244(644targets), robustness starts401/501/601/701/801; 후속901–1245(345targets). 평균 Top6=0.849379. 대표값은 Phase3 primary다. 후속 frozen Gap26=.834783, Gap13=.831884는 별도 값이다. Phase6/10 Gap26=.823188/.8232는 fit calendar가 다르다.

동결 설정: Logistic C=1,seed42,SciPy L-BFGS-B; features=current_gap,has_appeared,mean_gap,median_gap,gap_std,gap_ratio; primary start601/end1244/cadence26,bootstrap2000/block26. exact 초기 config=reports/prize_research/experiment.json. 후속 Gap는 해당 Phase frozen predictions를 기준선으로 사용.

| Paired 비교 | 범위 / 방법 | 차이 | 95% interval |
|---|---|---:|---|
| RandomModel | 601–1244; Phase3 prize robustness block26/2000 | +0.051242 | [-0.032609, +0.133579] |
| RandomModel | 601–1244; 초기 prediction 비교의 별도 bootstrap stream | +0.051242 | [-0.035714, +0.139790] |

강건성·민감도: starts401/501/601/701/801 평균=.843602/.831989/.849379/.845588/.853604이며 모든 paired CI가0을 포함한다. primary early/middle/recent=.809302/.869767/.869159, Random 차이=-.046512/+.097674/+.102804. coefficient 부호 안정성은 예측 우위 증거가 아니다. 주기 추가·hazard/Bayesian/HMM의 안정적 개선 미확립.

보정-null 근거: 초기 Random upper-tail=.055972, learned-specification Bonferroni=.447776. 별도 구조-null corrected p가 아니다. 주요 paired 구간에서 예측 우위 미확립.

순위 다양성: 후속 상대 순위 기준: Graph 대비 Spearman=.0611,GapShape=-.0357,Mirror=.007219,MI=-.2095(각345targets 번호 좌표 평균). 상관을 결합해 효과를 계산하지 않는다.

명시적 미확인 값: 초기 Phase3 config·ranking audit·비교 출력은 존재한다. 후속 Phase15 Gap frozen CSV/manifest가 없어 byte/hash를 현재 재검증하지 못했다.

정확한 설정·출력 경로:

- [reports/prize_research/experiment.json](../reports/prize_research/experiment.json) — 초기 exact 모델·seed·cadence 설정
- [reports/prize_research/ranking_audit.csv](../reports/prize_research/ranking_audit.csv) — 초기 target별 예측 audit
- [reports/prize_research/ranking_comparisons.csv](../reports/prize_research/ranking_comparisons.csv) — 초기 paired 순위 비교
- [reports/prize_research/comparison.csv](../reports/prize_research/comparison.csv) — 초기 성능
- [reports/prize_research/gap_vs_heuristics.csv](../reports/prize_research/gap_vs_heuristics.csv) — Gap robustness·heuristic 비교
- `reports/transformed_space/walk_forward_26/predictions.csv` — HISTORICAL_UNAVAILABLE — 후속45score/rank·target·cutoff
- `reports/transformed_space/run_manifest.json` — HISTORICAL_UNAVAILABLE — 과거 byte/hash inventory

## GraphStructureModel

**ENSEMBLE CANDIDATE (탐색적)** — 약한 양의 역사 점추정치와 낮은 순위 상관을 보존한다. 주요 CI·W104 민감도로 검증된 예측 신호는 아니다.

출처: [docs/phase14-results.md](../docs/phase14-results.md) · [docs/graph-hypergraph-analysis.md](../docs/graph-hypergraph-analysis.md).

역사 범위: 구조1–1245; 개발401–900(500targets); 이후901–1245(345targets). 평균 Top6=0.8580. 원문 표4자리 정밀도. 개발=.884; Gap=.8348,Random=.7681,Frequency26=.7739.

동결 설정: W52; neighbor/community 동일 평균; spectral K3; graph threshold2; 매 target prefix<T에서 rolling 재fit. 개발30configs에서 Top6 선택,동률 선언순서. Phase14의 Graph/Hypergraph 동결 JSON SHA-256=a9712639a2cc76fc182f26a6b8767fdda32a7b218e1f362ee5395977e0f0390e(문서 전사,실제 파일 미검증).

| Paired 비교 | 범위 / 방법 | 차이 | 95% interval |
|---|---|---:|---|
| Random | 901–1245; circular block26 bootstrap2000 | +0.089900 | [-0.029100, +0.205800] |
| Frequency26 | 901–1245; circular block26 bootstrap2000 | +0.084100 | [-0.058000, +0.211600] |
| Gap | 901–1245; circular block26 bootstrap2000 | +0.023200 | [-0.092800, +0.127500] |
| matched Frequency52 | 901–1245; circular block26 bootstrap2000 | +0.127500 | [+0.002900, +0.243500] |

강건성·민감도: early/middle/recent=.8522/.8435/.8783; starts1001/1101=.8653/.8621. start1101 Gap 차이=-.0207 CI[-.2000,.1586]. W26=.8348,W52=.8580,W104=.7710; W52/K2=.8667. Gap13 대비+.0261[-.0928,.1420]; Gap 대비 block52/104 CI[-.1043,.1362]/[-.1014,.1276]. matched Frequency52만 약한 양의 CI,주요 기준선 CI는0 포함.

보정-null 근거: 135graphs·2,057,700primary cells의 IID199/fixed199 own maxima. community stability corrected p=.10/.05(경계); edge/triple/persistence/frequency-controlled successor corrected p=1/1. 빈도 이상의 successor 정보 미확립.

순위 다양성: Gap Spearman=.0611,Top6/10/15 overlap=1.0435/2.7391/5.5072; frozen MI Spearman=-.0062,overlap=.7420/2.0986/4.7652. 기존 기준선 refit 없음.

명시적 미확인 값: 해당 과거 출력 CSV·selected_configuration·manifest는 현재 checkout에 없다. 문서에 없는 더 정밀한 수치·hash는 null(미확인)이며 새로 추정하지 않았다.

정확한 설정·출력 경로:

- `reports/graph_hypergraph/selected_configuration.json` — HISTORICAL_UNAVAILABLE — 개발 선택 동결 설정
- `reports/graph_hypergraph/run_manifest.json` — HISTORICAL_UNAVAILABLE — 과거 byte/hash inventory
- `reports/graph_hypergraph/global_null_comparison.csv` — HISTORICAL_UNAVAILABLE — complete-search null 비교
- `reports/graph_hypergraph/walk_forward_26/predictions.csv` — HISTORICAL_UNAVAILABLE — 후속45score/rank·target·cutoff
- `reports/graph_hypergraph/walk_forward_26/summary.csv` — HISTORICAL_UNAVAILABLE — 성능·ranking 지표
- `reports/graph_hypergraph/walk_forward_26/paired.csv` — HISTORICAL_UNAVAILABLE — paired 차이·명목95% 구간
- `reports/graph_hypergraph/walk_forward_26/rank_diversity.csv` — HISTORICAL_UNAVAILABLE — 번호 좌표 순위 상관·TopK overlap
- [src/graph_hypergraph_cli.py](../src/graph_hypergraph_cli.py) — 정확한 출력 이름·protocol 구현

## GapShapeModel

**ENSEMBLE CANDIDATE (탐색적)** — 약한 양의 점추정치와 다양성 보존용. 주요 paired CI가0을 포함하고 K에 민감해 최종 채택 근거가 아니다.

출처: [docs/phase15-results.md](../docs/phase15-results.md) · [docs/transformed-space-analysis.md](../docs/transformed-space-analysis.md).

역사 범위: 구조1–1245; 개발401–900(500targets); 이후901–1245(345targets). 평균 Top6=0.8377. 원문 표4자리. 개발=.836(절반 .808/.864); Gap=.8348.

동결 설정: K25,normalized-gap Euclidean,exclusion26,Gaussian sigma1; 매 target prefix<T에서 neighbor/transition 재계산. selection SHA256=f6cac03e51aa8036824301d4d07a559900fb18a3674f2a2826b8c99eacfc3eb3(문서 전사,실제 파일 미검증).

| Paired 비교 | 범위 / 방법 | 차이 | 95% interval |
|---|---|---:|---|
| Random | 901–1245; circular block26 bootstrap2000 | +0.069600 | [-0.040600, +0.176800] |
| Gap | 901–1245; circular block26 bootstrap2000 | +0.002900 | [-0.101400, +0.115900] |

강건성·민감도: early/middle/recent=.8000/.8783/.8348; starts1001/1101=.8735/.8621. Gap 대비 start1001 +.0082[-.1143,.1429],start1101 -.0207[-.1862,.1241]. K25/sigma2=.8261이나 K10/sigma1=.7478,K10/sigma2=.7797로 K에 민감. cadence13 Gap 대비+.0058[-.1101,.1275],block52 Gap CI[-.0812,.0928]. 이후 최고 설정으로 교체하지 않음.

보정-null 근거: 다섯family·1793cells complete search IID199/fixed199. Gap-shape corrected p=1/1; 다섯family 최소 corrected p는 modular temporal 1/.95. K10/K25 successor normalized-shape MSEgain은 음수이며 number ranking과 target이 다르다.

순위 다양성: Gap Spearman=-.0357,Top6/10/15 overlap=.6609/1.9971/4.7565; frozen Graph Spearman=.0024,overlap=.7855/2.2290/5.0464. Graph refit/reselect 없음.

명시적 미확인 값: 해당 과거 출력 CSV·selected_configuration·manifest는 현재 checkout에 없다. 문서에 없는 더 정밀한 수치·hash는 null(미확인)이며 새로 추정하지 않았다.

정확한 설정·출력 경로:

- `reports/transformed_space/selected_configuration.json` — HISTORICAL_UNAVAILABLE — 개발 선택 동결 설정
- `reports/transformed_space/run_manifest.json` — HISTORICAL_UNAVAILABLE — 과거 byte/hash inventory
- `reports/transformed_space/global_null_comparison.csv` — HISTORICAL_UNAVAILABLE — complete-search null 비교
- `reports/transformed_space/walk_forward_26/predictions.csv` — HISTORICAL_UNAVAILABLE — 후속45score/rank·target·cutoff
- `reports/transformed_space/walk_forward_26/summary.csv` — HISTORICAL_UNAVAILABLE — 성능·ranking 지표
- `reports/transformed_space/walk_forward_26/paired.csv` — HISTORICAL_UNAVAILABLE — paired 차이·명목95% 구간
- `reports/transformed_space/walk_forward_26/rank_diversity.csv` — HISTORICAL_UNAVAILABLE — 번호 좌표 순위 상관·TopK overlap
- [src/transformed_cli.py](../src/transformed_cli.py) — 정확한 출력 이름·protocol 구현

## MirrorModel

**ENSEMBLE CANDIDATE (탐색적)** — 낮은 Gap/Graph 상관과 약한 점추정치 보존용. 주요 CI는0 포함,최근 평균은.8 미만이며 corrected 구조 근거가 없다.

출처: [docs/phase18-results.md](../docs/phase18-results.md) · [docs/symmetry-analysis.md](../docs/symmetry-analysis.md).

역사 범위: 구조1–1245; 개발401–900(500targets); 이후901–1245(345targets). 평균 Top6=0.826087. 개발=.896(절반 .948/.844). Gap26=.834783,Random=.768116,Frequency26=.773913.

동결 설정: window10,lag1,shrinkage200,support20,pooled linear ridge; 각 available-prefix 재fit; mirror(n)=46-n,center23 중립6/45. 48configs 개발Top6 선택. selection SHA256=6476edcd3f8e989c89a93aa76dc1c83c81f62ead1c4047348f0f0a7c7c00b1a9(문서 전사).

| Paired 비교 | 범위 / 방법 | 차이 | 95% interval |
|---|---|---:|---|
| Random | 901–1245; circular block26 bootstrap2000 | +0.057971 | [-0.026087, +0.142029] |
| Frequency26 | 901–1245; circular block26 bootstrap2000 | +0.052174 | [-0.055072, +0.162319] |
| Gap | 901–1245; circular block26 bootstrap2000 | -0.008696 | [-0.110145, +0.089855] |

강건성·민감도: early/middle/recent=.834783/.852174/.791304; starts1001/1101=.804082/.793103. W10/lag2=.820290,W26/lag1=.886957,W26/lag2=.881159(재선택 없음). block13 Random CI[-.037681,.159420],Gap[-.107246,.098551]. block52 Random CI[.005797,.104348]만 양수이나 Frequency[-.037681,.139203],Gap[-.095652,.072464]는0 포함. 유리한 구간 하나를 독립 확인으로 선택하지 않음.

보정-null 근거: 3862cells·일곱family IID199/fixed199 complete search corrected p 모두1. strongest pair13→33 lag8 global p=.225/.160,pooled lag8=.595/.640. 보정 후 구조 근거 없음; PairModel·secondary-shift predictor 미구현.

순위 다양성: Gap Spearman=.007219,Top6/10/15 overlap=.739130/2.000000/5.043478; Graph=.024548,.947826/2.394203/5.150725; GapShape=-.005878,.739130/2.205797/5.008696; MI=-.002914,.742029/2.231884/5.020290. 기존 모델 frozen 출력만 비교.

명시적 미확인 값: 해당 과거 출력 CSV·selected_configuration·manifest는 현재 checkout에 없다. 문서에 없는 더 정밀한 수치·hash는 null(미확인)이며 새로 추정하지 않았다.

정확한 설정·출력 경로:

- `reports/symmetry/selected_configuration.json` — HISTORICAL_UNAVAILABLE — 개발 선택 동결 설정
- `reports/symmetry/run_manifest.json` — HISTORICAL_UNAVAILABLE — 과거 byte/hash inventory
- `reports/symmetry/global_null_comparison.csv` — HISTORICAL_UNAVAILABLE — complete-search null 비교
- `reports/symmetry/walk_forward_26/predictions.csv` — HISTORICAL_UNAVAILABLE — 후속45score/rank·target·cutoff
- `reports/symmetry/walk_forward_26/summary.csv` — HISTORICAL_UNAVAILABLE — 성능·ranking 지표
- `reports/symmetry/walk_forward_26/paired.csv` — HISTORICAL_UNAVAILABLE — paired 차이·명목95% 구간
- `reports/symmetry/walk_forward_26/rank_diversity.csv` — HISTORICAL_UNAVAILABLE — 번호 좌표 순위 상관·TopK overlap
- [src/symmetry_cli.py](../src/symmetry_cli.py) — 정확한 출력 이름·protocol 구현

## MutualInformationModel (MI)

**NOT CURRENTLY JUSTIFIED** — 관심 있는 양의 점추정치지만 paired·시간 안정성·parameter 민감도 조건을 충족하지 못해 후보로 승격하지 않는다.

출처: [docs/phase13-results.md](../docs/phase13-results.md) · [docs/information-flow-analysis.md](../docs/information-flow-analysis.md).

역사 범위: 구조1–1245; 개발401–900(500targets); 이후901–1245(345targets). 평균 Top6=0.8435. 원문 표4자리. 개발=.826(절반 .864/.788); Gap=.8348,Random=.7681.

동결 설정: lag1,incoming3; context support20,shrinkage20,positive corrected information weighting,trailing624; pair/state를 매 target prefix<T에서 재선택. MI14개 개발configs. selection SHA256=b3a126bd5ecb1ea374d9ef90d91e667d0fe054d69196ca75205ff11c7a0d5e30(문서 전사).

| Paired 비교 | 범위 / 방법 | 차이 | 95% interval |
|---|---|---:|---|
| Random | 901–1245; circular block26 bootstrap2000 | +0.075400 | [-0.034900, +0.188400] |
| Gap | 901–1245; circular block26 bootstrap2000 | +0.008700 | [-0.087000, +0.113000] |

강건성·민감도: early/middle/recent=.6783/.9652/.8870; starts1001/1101=.8980/.9241; cadence13도=.8435. lag1/K5=.8290,lag2/K3=.8174,lag3/K3=.8029,lag8/K3=.7188로 lag 의존. 개발 절반 승자 lag3→lag13로 불안정. 이후 상승·early 부진을 함께 보존하며 재선택 없음.

보정-null 근거: 166,320primary cells·다섯family IID199/fixed199 own-max. 최고 MI2→33 lag13 corrected p=.225/.175; CMI=.725/.600; TE/asymmetry=1/1; stableTE=.575/.550. source-only shift local 결과와 전체 보정 결과를 결합하지 않음.

순위 다양성: Gap Spearman=-.2095,Top6/10/15 overlap=.4783/1.5246/3.1623. 높은 차별성 자체는 개선 증거가 아니다.

명시적 미확인 값: 해당 과거 출력 CSV·selected_configuration·manifest는 현재 checkout에 없다. 문서에 없는 더 정밀한 수치·hash는 null(미확인)이며 새로 추정하지 않았다.

정확한 설정·출력 경로:

- `reports/information_flow/selected_configuration.json` — HISTORICAL_UNAVAILABLE — 개발 선택 동결 설정
- `reports/information_flow/run_manifest.json` — HISTORICAL_UNAVAILABLE — 과거 byte/hash inventory
- `reports/information_flow/global_null_comparison.csv` — HISTORICAL_UNAVAILABLE — complete-search null 비교
- `reports/information_flow/walk_forward_26/predictions.csv` — HISTORICAL_UNAVAILABLE — 후속45score/rank·target·cutoff
- `reports/information_flow/walk_forward_26/summary.csv` — HISTORICAL_UNAVAILABLE — 성능·ranking 지표
- `reports/information_flow/walk_forward_26/paired.csv` — HISTORICAL_UNAVAILABLE — paired 차이·명목95% 구간
- `reports/information_flow/walk_forward_26/rank_diversity.csv` — HISTORICAL_UNAVAILABLE — 번호 좌표 순위 상관·TopK overlap
- [src/information_cli.py](../src/information_cli.py) — 정확한 출력 이름·protocol 구현

HISTORICAL_UNAVAILABLE은 현재 checkout에 파일이 없다는 뜻이다. 원문 결과는 존재하지만 해당 CSV·동결 설정·manifest의 byte/hash를 이번 원장 작업에서 재검증하지 못했다. AVAILABLE은 현재 파일 존재만 확인한 상태이며 자동으로 과거 전체 산출물의 무결성을 보증하지 않는다. 후보를 재학습하거나 더 좋은 사후 설정으로 교체하지 않았고 실제1246 결과를 사용하지 않았다.

생성·검증: `python -m src.analysis.evidence_ledger --check`.
