# Lotto Pattern Lab

## 프로젝트 소개

“로또 과거 데이터에 우리가 놓친 패턴이 있을까?”라는 질문에서 시작한
Korean Lotto 6/45 연구 프로젝트입니다. 로또가 예측 가능하다고 가정하지 않습니다.
무작위성이 강한 이산 데이터에서 눈에 띄는 구조와 실제 예측 근거를 구분합니다.

가설 → historical analysis → null / surrogate → global-max correction
→ walk-forward → prospective freeze → 이후 명시적 결과 비교

로컬 Python CLI 프로젝트이며 웹 앱은 없습니다.
전체 문서는 [문서 색인](docs/README.md), 가설별 결정은
[연구 가설 노트](docs/research-ideas.md)에서 찾을 수 있습니다.

## 핵심 연구 질문

- 개별 번호 자체에 반복 구조가 있는가?
- 번호축을 따라 이동하는 구조가 있는가?
- 특정 상태에서만 구조가 드러나는가?
- 주변 숫자 공간에 activity가 존재하는가?
- hand-crafted state 대신 hidden state를 표현하면 recurrence가 드러나는가?
- symmetry / reflection transform에서 구조가 보이는가?
- 서로 다른 약한 signal을 조합하면 더 강한 signal이 되는가?

## 연구 원칙

### No future leakage

대상 회차 T의 입력은 완료된 1–T−1회뿐입니다.
특징 계산, scaling, 상태 경계와 규칙 선택도 training history 안에서 수행합니다.

### Pattern != prediction

전체 과거에서 발견한 구조는 탐색 결과입니다.
아직 보지 않은 결과를 더 잘 예측하는지는 별도로 검증합니다.

### Search the null equally hard

실제 자료에서 시도한 표현과 parameter 탐색을 각 surrogate에도 동일하게 적용합니다.
surrogate도 자신의 최적 패턴을 찾을 수 있어야 합니다.

### Global-max comparison

선택된 local peak를 고정된 한 번의 검정처럼 해석하지 않습니다.
동일한 전체 탐색의 null maximum과 비교하고 statistic family 보정도 보고합니다.

### Development / evaluation separation

설정 선택과 이후 평가를 분리합니다. 앞선 Phase에서 이미 사용한 역사 구간은
새 Phase의 later period여도 pristine holdout이라고 부르지 않습니다.

### Prospective freeze

설정·데이터 해시·Git SHA·점수와 순위·티켓·seed를 결과 확인 전에 동결합니다.
이후 결과 평가는 별도 파일에 기록합니다.

### Negative results are results

불확실하거나 부정적인 결과도 보존합니다.
복잡한 모델이라는 이유로 예측력이 좋아졌다고 간주하지 않습니다.

## 데이터

canonical history는 **1–1245회**, **2002-12-07–2026-10-10**입니다.
파일은 `data/raw/lotto_history.csv`이며 본번호 여섯 개와 bonus를 저장합니다.
주요 예측 대상과 binary matrix에서는 bonus를 제외합니다.

공개 GitHub mirror를 명시적으로 import한 자료입니다. schema 검증과 일부 대조를
수행했지만 모든 회차의 공식 원본 대조를 완료한 자료는 아닙니다.
출처·검증 규칙·해시 범위는 [데이터와 provenance](docs/data-provenance.md)를 참고하세요.

기존 연구 명령은 1244회까지의 seal을 유지하며, 전용 Phase 6–10 명령은
로컬 1245회까지 허용합니다. 1245회는 새로운 미사용 holdout이 아닙니다.

## 현재까지의 핵심 결론

- Random baseline은 이론적 기대값인 티켓당 평균 **0.8개** 근처에서 작동했습니다.
- 개별 번호의 시간적 패턴과 periodicity / regime 모델은 신뢰할 예측 우위를 확립하지 못했습니다.
- 2D translation은 global null correction을 통과하지 못했습니다.
- Gap-conditioned 3D, recent-frequency-conditioned 3D와 gap × frequency interaction도
  **TESTED / INCONCLUSIVE**입니다.
- Number-space neighborhood / range-density도 **TESTED / INCONCLUSIVE**입니다.
  선택된 neighborhood 설정은 smoothing이 없는 own-number control이었습니다.
- Gap Logistic은 여러 역사 비교에서 약하게 양의 점추정치를 보였지만,
  신뢰할 예측 우위를 확립하지 못했습니다.
- 모델 복잡성의 증가는 성능 향상을 보장하지 않았습니다.

수치·신뢰구간·검정 수·runtime은 아래 Phase 문서에 보존합니다.

## 연구 가설 로드맵

| ID | 가설 | 상태 |
|---|---|---|
| H1 | 개별 번호의 시간적 패턴 | TESTED / INCONCLUSIVE |
| H2 | Gap / periodicity / regime | TESTED / INCONCLUSIVE |
| H3 | 2D translational number patterns | TESTED / INCONCLUSIVE |
| H4 | Gap-conditioned 3D | TESTED / INCONCLUSIVE |
| H5 | Recent-frequency-conditioned 3D | TESTED / INCONCLUSIVE |
| H6 | Gap × frequency interaction | TESTED / INCONCLUSIVE |
| H7 | Full continuous 4D geometry | DEFERRED |
| H8 | Spatial neighborhood / range-density | TESTED / INCONCLUSIVE |
| H9 | Delay embedding / recurrence geometry | TESTED / INCONCLUSIVE |
| H10 | Wavelet / SSA multiscale structure | TESTED / INCONCLUSIVE |
| H11 | Mutual information / Transfer Entropy | TESTED / INCONCLUSIVE |
| H12 | Dynamic graph / Hypergraph | TESTED / INCONCLUSIVE |
| H13 | Modular / difference-space transforms | TESTED / INCONCLUSIVE |
| H14 | Entropy / compression / algorithmic randomness | TESTED / INCONCLUSIVE |
| H15 | Tensor decomposition | TESTED / INCONCLUSIVE |
| H16 | Symmetry / reflection structure | BACKLOG |
| H17 | Validated weak-signal ensemble | BACKLOG |

Phase와 H번호는 서로 다른 분류입니다. 옛 계획·동결 증거의 H번호는 보존합니다.
대응 관계는 [번호 이관 안내](docs/research-ideas.md#번호-이관-안내)에 설명합니다.

## Phase별 요약

### Phase 1 — 데이터·기초 분석·Random baseline

수집/import·검증·binary series·frequency/gap 통계와 RandomModel backtest를 만들었습니다.
초기 Random 결과는 평가 pipeline 점검이며 예측 우위의 근거가 아닙니다.
[방법과 초기 결과](docs/foundation-analysis.md)

### Phase 2 — 개별 번호의 시간적 패턴

calendar·rolling 통계, ACF·spectrum, periodicity score와 regime 진단을 조사했습니다.
탐색에서 보이는 구조를 신뢰할 예측 근거로 확립하지 못했습니다.
[방법과 결과](docs/temporal-analysis.md)

### Phase 3 — Causal ranking·Gap robustness·prize-aware 비교

Similarity·Logistic·feature ablation과 gap-only·candidate pool·동일 예산 티켓을 비교했습니다.
Gap 계열의 약한 점추정치는 있으나 안정적인 예측 우위는 확립되지 않았습니다.
[예측 실험](docs/predictive-experiments.md) · [Gap / prize 연구](docs/gap-prize-research.md)

### Phase 4 — Hazard·Bayesian·HMM·고정 ensemble 실험

hazard·Bayesian·Bernoulli HMM과 development에서 고정한 조합을 비교했습니다.
복잡한 regime 모델의 안정적 개선 근거는 부족했습니다.
[방법과 결과](docs/regime-research.md)

### Phase 5 — Prospective freeze 체계

여섯 track의 전체 순위·동일 예산 portfolio·manifest·registry·SHA-256을 동결했습니다.
결과 평가는 명시적 로컬 입력으로 분리합니다.
[현재 workflow](docs/prospective-workflow.md) · [당시 원본](docs/prospective-experiment.md)

### Phase 6 — 2D Translation

draw × number 공간의 shift·chain·Hough·FFT를 동일한 전체 null 탐색과 비교했습니다.
보정 후 유의한 구조와 안정적인 walk-forward 우위를 확립하지 못했습니다.
[방법](docs/spatiotemporal-analysis.md) · [결과](docs/phase6-results.md)

### Phase 7 — Gap-conditioned 3D

causal current gap 상태별 translation과 trajectory를 조사했습니다.
상태 조건 추가로 신뢰할 예측 개선이 나타났다고 결론 내릴 수 없습니다.
[방법](docs/gap3d-analysis.md) · [결과](docs/phase7-results.md)

### Phase 8 — Recent-frequency-conditioned 3D

W10/W26/W52 frequency 상태별 구조를 조사하고 각 surrogate의 상태를 다시 계산했습니다.
전체 탐색 보정과 walk-forward에서 신뢰할 우위를 확립하지 못했습니다.
[방법](docs/frequency3d-analysis.md) · [결과](docs/phase8-results.md)

### Phase 9 — Gap × frequency interaction

gap과 W26 frequency의 아홉 joint state를 단일 상태 parent와 비교했습니다.
두 parent와 비기하학 baseline을 넘어선다는 근거는 부족했습니다.
[방법](docs/joint-state-analysis.md) · [결과](docs/phase9-results.md)

### Phase 10 — Number-space

range-density·neighborhood smoothing·spacing·hot-zone 이동을 조사했습니다.
H8은 TESTED / INCONCLUSIVE이며 neighbor 기여를 입증하지 못했습니다.
[방법](docs/number-space-analysis.md) · [결과](docs/phase10-results.md)

### Phase 11 — Delay Embedding / Recurrence Geometry

“비슷한 과거 상태가 비슷한 미래 결과로 이어지는가?”를 1–1245회만으로 검증했습니다.
199 IID + 199 fixed-margin 전체 탐색과 이후 walk-forward에서 안정적인 개선을 확인하지 못했습니다.
H9는 **TESTED / INCONCLUSIVE**, ensemble 후보는 **NOT CURRENTLY JUSTIFIED**입니다.
[방법](docs/recurrence-analysis.md) · [결과·동결 설정](docs/phase11-results.md)

### Phase 12 — Wavelet / SSA Multiscale Structure

특정 시기·scale에만 나타나는 반복 구조를 1–1245회와199 IID +199 fixed-margin 전체 탐색으로 비교했습니다.
번호5의 SSA window 안정성은 두 null 모두 family 보정 p=0.03이었지만, 이후 예측 우위와 강건성은 확보하지 못했습니다.
H10은 **TESTED / INCONCLUSIVE**, Wavelet·SSA ensemble 후보는 **NOT CURRENTLY JUSTIFIED**입니다.
[방법](docs/multiscale-analysis.md) · [결과·동결 설정·검증](docs/phase12-results.md)

### Phase 13 — Mutual Information / Transfer Entropy

45개 binary series의 모든 pair·lag·작은 history 설정을199 IID +199 fixed-margin 전체 탐색으로 비교했습니다.
MI·CMI·TE·방향 비대칭·시간 안정성 모두 family 보정을 통과하지 못했습니다.
MI의 이후 약한 상승은 불확실하며, source를 추가한 TE logloss는 target-history baseline보다 나빴습니다.
H11은 **TESTED / INCONCLUSIVE**, MI·TE ensemble 후보는 **NOT CURRENTLY JUSTIFIED**입니다.
[방법](docs/information-flow-analysis.md) · [결과·동결 설정·검증](docs/phase13-results.md)

### Phase 14 — Dynamic Graph / Hypergraph Structure

W26/52/104의 graph·triple·community·successor를199 IID +199 fixed-margin 전체 검색과 비교했습니다.
community 안정성의 보정 p는0.10/0.05로 두 null에서 일관된 근거를 확보하지 못했습니다.
이후 Top6 평균은 Graph0.858, Hypergraph0.817, Gap0.835이며 Random·Frequency26·Gap 대비 구간은0을 포함했습니다.
H12는 **TESTED / INCONCLUSIVE**입니다. Graph는 낮은 rank 상관과 약한 양의 성능을 보존하는
탐색적 **ENSEMBLE CANDIDATE**, Hypergraph는 **NOT CURRENTLY JUSTIFIED**입니다. 최종 ensemble은 만들지 않았습니다.
[방법](docs/graph-hypergraph-analysis.md) · [결과·동결 설정·검증](docs/phase14-results.md)

### Phase 15 — Modular / Difference-Space Transforms

moduli2–7과 lag1/2/3/4/8/13/26의 residue·absolute distance·gap shape를199 IID +199 fixed-margin 전체 검색과 비교했습니다.
다섯 family 모두 보정 후 유의하지 않았습니다. 이후 평균Top6는 Modular0.786, Difference0.777,
GapShape0.838, Gap Logistic0.835이며 주요 paired 구간은0을 포함했습니다.
H13은 **TESTED / INCONCLUSIVE**입니다. Modular·Difference는 **NOT CURRENTLY JUSTIFIED**,
GapShape는 K 민감도를 남긴 탐색적 **ENSEMBLE CANDIDATE**입니다. 최종 ensemble은 만들지 않았습니다.
[방법](docs/transformed-space-analysis.md) · [결과·동결 설정·검증](docs/phase15-results.md)

### Phase 16 — Entropy / Compression / Algorithmic Randomness

53개 고정 표현의 entropy·LZ78·세 compressor를 IID199/fixed-margin199/draw-order shuffle199와 비교했습니다.
전체·개발을 분리해 전체5184개 후보를 똑같이 검색했으며 전체 역사 여섯 family 보정 p는 모두1이었습니다.
실제가 더 낮은 complexity를 가지거나 chronological ordering에 hidden temporal structure가 있다는 근거는 없었습니다.
H14는 **TESTED / INCONCLUSIVE**이며, 개발 gate가 실패해 predictor·ensemble 후보·H14 prospective 기능은 만들지 않았습니다.
[방법](docs/complexity-analysis.md) · [결과·결정·검증](docs/phase16-results.md)

### Phase 17 — Tensor Decomposition

causal Tensor A/B/C와36개 Tucker rank 조합,165개 statistic cell을 IID199/fixed-margin199에서 동일하게 검색했습니다.
다섯 family는 모두 보정 후 유의하지 않았으며, 가장 작은 보정 p는0.400이었습니다.
low-rank factor나 smooth temporal trajectory가 random history보다 특별하다는 근거를 확보하지 못했습니다.
H15는 **TESTED / INCONCLUSIVE**입니다. 개발 gate 실패로 TensorFactorModel은
**PREDICTIVE_MODEL_NOT_JUSTIFIED**이며 예측·ensemble 후보·Phase17 prospective 기능을 만들지 않았습니다.
[방법](docs/tensor-analysis.md) · [결과·결정·검증](docs/phase17-results.md)

## Prospective experiments

여러 draw-1246 실험은 결과가 알려지기 전에 동결된 역사적 증거입니다.
**1246회 결과는 현재 외부에 알려져 있으며 새로운 prospective 대상이 아닙니다.**
원본의 FROZEN_UNEVALUATED는 당시 동결 상태로 보존하고 결과를 자동 평가하지 않습니다.

Phase 11–15의 역사 연구와 설정은 고정했으며 다음 prospective 대상은 **1247회**입니다.
Phase16–17은 정당화된 predictor가 없어 별도 prospective capability를 생성하지 않았습니다.
기존 archive가 없어 **PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION** 상태입니다.
1247 준비 gate만 구현했고 1246회 import·새 prospective snapshot 발행은 수행하지 않았습니다.

[Workflow와 보호 규칙](docs/prospective-workflow.md) ·
[동결 기록 색인](docs/README.md#frozen-prospective-evidence)

이 체크아웃에는 `reports/prospective/` 원본 파일이 없습니다.
과거 해시 기록 보존과 실제 파일의 무결성 재검증을 구분해야 합니다.

## 실행 방법

아래는 존재하는 명령의 사용 예입니다. 분석·freeze 명령은 출력 파일을 만듭니다.
Phase 11–16 명령은 연구 입력을 1–1245회로 제한하며 데이터 수집을 수행하지 않습니다.

### 환경 설정

Python 3.11 이상이 필요합니다. optional ML 의존성은 별도입니다.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py --help
```

### 데이터 검증

```powershell
python main.py validate
```

다른 CSV는 subcommand **앞에** `--data path/to/history.csv`로 지정합니다.
검증 성공은 공식 원본 대조나 최신 회차 확보를 의미하지 않습니다.

### 기본 분석

```powershell
python main.py inspect 17
python main.py analyze-all --permutations 4999 --seed 42
python main.py export-series
```

### Backtesting

```powershell
python main.py backtest --mode walk-forward --min-train 299 --seed 42 --report reports/random_walk_forward
python main.py backtest --mode checkpoints --checkpoints 100 --tickets 5 --repeats 10 --seed 42 --report reports/random_checkpoints
python main.py compare-models --ablations
python main.py prize-eval
python -m pytest -q
```

### Phase analyses

```powershell
python main.py hazard-analysis
python main.py compare-regime-models
python main.py analyze-2d --surrogates 199
python main.py compare-2d
python main.py analyze-gap3d --surrogates 199
python main.py compare-gap3d
python main.py analyze-frequency3d --surrogates 199
python main.py compare-frequency3d
python main.py analyze-joint --surrogates 199
python main.py compare-joint
python main.py analyze-number-space --surrogates 199
python main.py compare-number-space
python main.py recurrence --help
python main.py multiscale --help
python main.py information-flow --help
python main.py graph-hypergraph --help
python main.py transformed-space --help
python main.py complexity --help
```

### Prospective workflow

기존 CLI의 사용법은 help로 확인할 수 있습니다.
`python main.py recurrence prepare-freeze`는 archive 복원 검증용 준비 기능이며 실제 snapshot을 발행하지 않습니다.
이미 알려진 1246회를 새 prospective 실험으로 생성해서는 안 됩니다.

```powershell
python main.py freeze-next --help
python main.py freeze-2d --help
python main.py freeze-gap3d --help
python main.py freeze-frequency3d --help
python main.py freeze-joint --help
python main.py freeze-number-space --help
python main.py evaluate-freeze --help
```

## 프로젝트 구조

```text
data/raw/           canonical CSV, metadata, sources
data/processed/     파생 데이터 출력 위치
src/collect/        수집·import·검증
src/analysis/       표현·특징·탐색 분석
src/models/         ranking 및 예측 모델
src/backtest/       walk-forward·평가·portfolio
src/*_cli.py        Phase별 CLI
src/phase*_*.py     Phase별 동결·artifact 검증
tests/              오프라인·누출 방지·무결성 테스트
reports/            분석 출력; 현재는 일부 초기 보고서만 포함
docs/               방법·결과·가설·역사 protocol
main.py             CLI 진입점
requirements.txt    기본 의존성
requirements-ml.txt optional ML 의존성
```

## 데이터 출처 및 provenance

공식 사이트 adapter는 구현 당시 제한 환경에서 연결에 실패하여 end-to-end 검증을
완료하지 못했습니다. mirror import는 자동 fallback이 아닌 명시적 작업이었습니다.
상세 출처는 [provenance 안내](docs/data-provenance.md), 원본 기록은
[sources.json](data/raw/sources.json)과 [metadata](data/raw/lotto_history.metadata.json)에 있습니다.

## 해석상의 주의사항

수익성 있는 전략은 확립되지 않았습니다. 역사적 prize-equivalent 결과는 실제 구매나
예측력의 증명이 아닙니다. Candidate pool에 당첨번호가 포함되는 사건과 실제 티켓 당첨도
구분합니다. 탐색적 구조와 예측 증거는 별개이며 prospective freeze는 hindsight와
cherry-picking을 막기 위한 절차입니다.
