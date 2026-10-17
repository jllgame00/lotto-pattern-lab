# Lotto Pattern Lab 문서

## 연구 개요

- [프로젝트 소개와 Phase 지도](../README.md)
- [Canonical H1–H17 연구 가설 노트](research-ideas.md)
- [현재 prospective workflow](prospective-workflow.md)
- [데이터·출처·검증·해시 범위](data-provenance.md)
- [문서 전체 inventory와 보존·검증 기록](documentation-audit.md)

현재 방법·결과는 한국어 설명을 기준으로 읽습니다. 기술 명칭·수식·CLI는 원래 표기를
유지합니다. Phase는 실행 순서이며 H번호와 다릅니다. 표·수치와 원본 동결 기록은 보존합니다.
일부 상세 연구 출력과 동결 원본은 이 체크아웃에 없습니다. 경로 표기는 파일 존재 보증이 아닙니다.

## Phase 1–5

| Phase | 내용 | 방법·결과 |
|---|---|---|
| 1 | 데이터 검증·기초 통계·Random baseline | [기초 분석](foundation-analysis.md) |
| 2 | 개별 번호 시간 구조, H1 | [시간 분석](temporal-analysis.md) |
| 3 | Causal ranking·Gap robustness·prize-aware, H2 | [예측 실험](predictive-experiments.md) · [Gap / prize](gap-prize-research.md) |
| 4 | Hazard·Bayesian·HMM·고정 ensemble 실험, H2 | [Regime 연구](regime-research.md) |
| 5 | Prospective freeze·별도 평가 체계 | [현재 workflow](prospective-workflow.md) · [당시 원본 기록](prospective-experiment.md) |

## Phase 6 — 2D Translation

H3: TESTED / INCONCLUSIVE.
[방법](spatiotemporal-analysis.md) · [결과](phase6-results.md) ·
[당시 protocol](superpowers/plans/2026-10-17-phase6.md)

## Phase 7 — Gap-conditioned 3D

H4: TESTED / INCONCLUSIVE.
[방법](gap3d-analysis.md) · [결과](phase7-results.md) ·
[당시 protocol](superpowers/plans/2026-10-17-phase7.md)

## Phase 8 — Recent-frequency 3D

H5: TESTED / INCONCLUSIVE.
[방법](frequency3d-analysis.md) · [결과](phase8-results.md) ·
[당시 protocol](superpowers/plans/2026-10-17-phase8.md)

## Phase 9 — Gap × frequency interaction

H6: TESTED / INCONCLUSIVE.
[방법](joint-state-analysis.md) · [결과](phase9-results.md) ·
[당시 protocol](superpowers/plans/2026-10-17-phase9.md)

## Phase 10 — Number-space

H8: TESTED / INCONCLUSIVE. 과거 protocol의 H9는 현재 H8에 해당합니다.
[방법](number-space-analysis.md) · [결과](phase10-results.md) ·
[당시 protocol](superpowers/plans/2026-10-17-phase10.md)

## Phase 11 — Delay / Recurrence

H9: TESTED / INCONCLUSIVE. 연구 cutoff는 영구적으로 1245회입니다.
“비슷한 과거 상태가 비슷한 미래 결과로 이어지는가?”를 질문으로 삼습니다.
[Phase 11 방법론](recurrence-analysis.md) · [결과·동결 설정·검증](phase11-results.md) · [H9 가설](research-ideas.md#h9--delay-embedding--recurrence-geometry)
199+199 전체 surrogate 탐색과 이후 평가에서 안정적인 개선을 확인하지 못했습니다.
1247 발행은 PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION입니다.

## Phase 12 — Wavelet / SSA Multiscale Structure

H10: TESTED / INCONCLUSIVE. 1–1245회만 사용한199+199 전체 surrogate 탐색에서
번호5의 SSA 안정성 보정 p=0.03이 남았지만 이후 예측 우위는 확보하지 못했습니다.
Wavelet·SSA 모델은 모두 NOT CURRENTLY JUSTIFIED입니다.
[방법](multiscale-analysis.md) · [결과·동결 설정·검증](phase12-results.md) · [실행 계획](superpowers/plans/2026-10-17-phase12.md)
1247 발행은 PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION입니다.

## Phase 13 — Mutual Information / Transfer Entropy

H11: TESTED / INCONCLUSIVE. 1–1245회45개 binary series의199+199 전체 surrogate 탐색에서
다섯 information family 모두 보정을 통과하지 못했습니다. MI의 이후 작은 상승은 불확실하며,
TE는 target-history baseline 대비 이후 logloss가 나빴습니다. 두 모델은 NOT CURRENTLY JUSTIFIED입니다.
[방법](information-flow-analysis.md) · [결과·동결 설정·검증](phase13-results.md) · [실행 계획](superpowers/plans/2026-10-18-phase13.md)
1247 발행은 PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION입니다.

## Phase 14 — Dynamic Graph / Hypergraph

H12: TESTED / INCONCLUSIVE. 1–1245회만 사용한199+199 전체 검색에서 community 안정성은
보정 p=0.10(IID),0.05(fixed-margin)로 두 null에서 일관된 근거를 확보하지 못했습니다.
빈도를 제거한 successor 진단도 유의하지 않았습니다.
Graph는 낮은 rank 상관과 약한 양의 성능을 보존하는 탐색적 ENSEMBLE CANDIDATE이며,
Hypergraph는 NOT CURRENTLY JUSTIFIED입니다. 예측 우위를 확립한 판정은 아닙니다.
[방법](graph-hypergraph-analysis.md) · [결과·설정·검증](phase14-results.md) · [실행 계획](superpowers/plans/2026-10-18-phase14.md)
1247 발행은 PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION입니다.

## Phase 15 — Modular / Difference-Space Transforms

H13: TESTED / INCONCLUSIVE. moduli2–7·lag7개의199+199 전체 null 검색에서
다섯 family 모두 보정 후 유의하지 않았습니다. 이후 Modular/Difference의 근거는 부족하며,
GapShape는 약한 양의 점추정치와 낮은 순위 상관을 보존하는 탐색적 ENSEMBLE CANDIDATE입니다.
주요 paired 구간은0을 포함하고 K 민감도가 있습니다.
[방법](transformed-space-analysis.md) · [결과·설정·검증](phase15-results.md) · [실행 계획](superpowers/plans/2026-10-18-phase15.md)
1247 발행은 PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION입니다.

## Phase 16 — Entropy / Compression / Algorithmic Randomness

H14: TESTED / INCONCLUSIVE.53개 표현·5184개 후보의 IID199/fixed199/draw-shuffle199 전체 검색에서
여섯 family 모두 보정 p=1이었습니다. 실제의 낮은 complexity와 chronological ordering의 추가 구조는 입증되지 않았습니다.
개발 gate가 실패해 예측 모델·rank correlation·prospective capability를 만들지 않았습니다.
[방법](complexity-analysis.md) · [결과·결정·검증](phase16-results.md) · [실행 계획](superpowers/plans/2026-10-18-phase16.md)
기존 prospective archive는 PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION입니다.

## Phase 17 — Tensor Decomposition

H15: TESTED / INCONCLUSIVE. causal Tensor A/B/C·36 Tucker 조합·165 statistic cell을
IID199/fixed-margin199에서 완전히 검색했습니다. 모든 family는 보정 후 유의하지 않았고 최소 보정 p=.400이었습니다.
개발 gate 실패로 PREDICTIVE_MODEL_NOT_JUSTIFIED이며 예측/Phase17 prospective 기능은 만들지 않았습니다.
[방법](tensor-analysis.md) · [결과·결정·검증](phase17-results.md) · [실행 계획](superpowers/plans/2026-10-18-phase17.md)
기존 prospective archive는 PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION입니다.

## Phase 18 — Symmetry / Reflection

H16: TESTED / INCONCLUSIVE. 중심23·22pairs·9lags·제한된 shift를 IID199/fixed199에서
동일하게 검색했으며 전체3862개 후보의 일곱 family 보정 p는 모두1이었습니다.
MirrorModel 이후Top6=.8261,Gap=.8348이며 주요 paired 구간은0을 포함했습니다.
낮은 Gap/Graph 순위 상관의 탐색적 ENSEMBLE CANDIDATE로 보존하되 예측 우위를 주장하지 않습니다.
PairModel/Phase18 prospective 기능/H17 ensemble은 만들지 않았습니다.
[방법](symmetry-analysis.md) · [결과·결정·검증](phase18-results.md) · [실행 계획](superpowers/plans/2026-10-18-phase18.md)
기존 prospective archive는 PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION입니다.

## 향후 연구 가설

[가설 노트](research-ideas.md)의 H7은 DEFERRED,
H17은 BACKLOG입니다. validated ensemble 연구는 별도로 남아 있습니다.

## Historical protocol archive

아래 문서는 당시 실험 시작 전에 작성된 historical protocol이며,
현재 결과/상태는 최신 result 문서를 참고합니다.
실행 후 보충된 메모도 있으므로 모든 문장을 사전 등록으로 간주하지 않습니다.
원래 의사결정·H번호·당시 시점의 표현과 해시를 보존하기 위해 파일을 수정하지 않았습니다.

| 범위 | 원본 |
|---|---|
| 초기 설계 | [first-pass design](superpowers/specs/2026-10-17-first-pass-design.md) · [first-pass plan](superpowers/plans/2026-10-17-first-pass.md) |
| 시간 분석 | [temporal design](superpowers/specs/2026-10-17-temporal-design.md) · [temporal plan](superpowers/plans/2026-10-17-temporal.md) |
| 예측 비교 | [prediction](superpowers/plans/2026-10-17-prediction.md) |
| Gap / prize | [prize research](superpowers/plans/2026-10-17-prize-research.md) |
| Regime | [regime research](superpowers/plans/2026-10-17-regime-research.md) |
| Phase 5 | [prospective freeze](superpowers/plans/2026-10-17-prospective-freeze.md) |
| Phase 6 | [2D](superpowers/plans/2026-10-17-phase6.md) |
| Phase 7 | [Gap 3D](superpowers/plans/2026-10-17-phase7.md) |
| Phase 8 | [Frequency 3D](superpowers/plans/2026-10-17-phase8.md) |
| Phase 9 | [Joint state](superpowers/plans/2026-10-17-phase9.md) |
| Phase 10 | [Number-space](superpowers/plans/2026-10-17-phase10.md) |

[기존 실행 메모](progress.md)는 개발 내부의 역사 기록입니다.
과거 테스트 수·완료 시점·“다음 단계” 문구를 현재 상태로 해석하지 않습니다.

## Frozen prospective evidence

다음은 순위·티켓·해시를 담은 당시 기록입니다. 링크만 제공하며 원본을 수정하지 않습니다.
draw 1246은 현재 외부에 알려졌고 새 prospective 대상이 아닙니다.
아래 FROZEN_UNEVALUATED는 각 원본 기록의 상태를 보존한 것입니다.

- [Phase 5 원본 protocol·동결 기록](prospective-experiment.md)
- [Phase 6 원본 동결 구역](phase6-results.md#frozen-experiment-record)
- [Phase 7 원본 prospective 기록](phase7-prospective.md)
- [Phase 8 원본 prospective 기록](phase8-prospective.md)
- [Phase 9 원본 prospective 기록](phase9-prospective.md)
- [Phase 10 원본 prospective 기록](phase10-prospective.md)

원본 위치는 `reports/prospective/`이나 **이 체크아웃에는 해당 디렉터리가 없습니다**.
원본 기록에 남은 D: 절대 경로·누락된 출력 링크는 역사 증거의 일부로 그대로 보존했습니다.
현재 안내는 위의 존재하는 문서 링크를 사용합니다. 실제 동결 파일의 byte-for-byte 비교는
원본이 제공되지 않아 수행할 수 없습니다. 이번에 보존한 문서의 SHA-256은
[문서 감사 기록](documentation-audit.md)에 있습니다.
