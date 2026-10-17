# 문서 정리 inventory와 검증 기록

## 범위와 작업 경로

검증한 Git root는 `C:/Users/Samsung/OneDrive/Desktop/university/personal/lotto-pattern-lab`입니다.
`git rev-parse --show-toplevel`이 정확히 일치했고 README·가설 노트·canonical CSV·src/·tests/가 있었습니다.
시작 시 Git working tree는 깨끗했습니다. 다른 directory에 프로젝트를 만들지 않았습니다.

기존 Markdown은 **35개**였습니다. repository 파일·hidden/ignored 파일까지 확인했으며
Git 내부와 이후 설치한 third-party test dependency 문서는 프로젝트 문서에서 제외합니다.
기존 16개를 재작성하고 19개를 원본 보존했습니다. 새 문서 5개를 더해 프로젝트 Markdown은 **40개**입니다.
Phase 11은 실행하지 않았습니다.

## 분류 기준

A root overview, B documentation index, C hypothesis notebook, D Phase result,
E methodology, F historical protocol / preregistration, G prospective workflow,
H immutable frozen evidence, I development/internal notes, J obsolete/duplicate입니다.

기존 문서의 주 분류는 A 1개·C 1개·D 5개·E 9개·F 13개·H 5개·I 1개입니다.
Phase 6 결과 문서의 frozen record 구역은 D와 별도로 H 보호를 적용합니다.
B·G는 새 문서로 추가했습니다. J 성격의 중복 README 본문은 각 전문 문서로 합치고,
역사 문서를 obsolete로 삭제하지 않았습니다.

## 발견한 모든 기존 Markdown

아래 SHA-256은 **수정 전 실제 바이트**를 기록한 감사 자료입니다.
순위·티켓·당시 hash 값을 대체하거나 frozen registry에 새로 등록하는 기록이 아닙니다.

| 파일 | 분류 | 처리 | 수정 전 SHA-256 |
|---|---|---|---|
| [README.md](../README.md) | A — Root overview | 한국어 재작성 | `b1ed891dcd0bd8ab8b89b5e881cf36b04ccb4a9b90091b25f3a3e8ab0396ec5a` |
| [docs/frequency3d-analysis.md](frequency3d-analysis.md) | E — 방법·초기 결과 | 한국어 재작성 | `8d1114e64ef9647c4d0435baa4eda23477c486367f8bc1da74409407bac0c17e` |
| [docs/gap-prize-research.md](gap-prize-research.md) | E — 방법·초기 결과 | 한국어 재작성 | `abcf1655de158fb26aa383bbd5773ca5a7b3fc5afd78e9314c09343619738e4b` |
| [docs/gap3d-analysis.md](gap3d-analysis.md) | E — 방법·초기 결과 | 한국어 재작성 | `ede5567a785fe0347b0195f6391b15822910f2d7c5cdfb048d01b3d0f8003ae4` |
| [docs/joint-state-analysis.md](joint-state-analysis.md) | E — 방법·초기 결과 | 한국어 재작성 | `536b5bb5698b1dc84f2cc4f789f69182519849bcf946af33eb0f79da9700c655` |
| [docs/number-space-analysis.md](number-space-analysis.md) | E — 방법·초기 결과 | 한국어 재작성 | `b18a6468f0486c47a28d1e5838858091fa0746a2f248c427a18ad1411ed53a5e` |
| [docs/phase10-prospective.md](phase10-prospective.md) | H — Frozen evidence / 당시 동결 기록 | 원본 보존 | `f86dc73d3c215a7a5cae2d281ae60f33cfa33c090935440902f528d6680a3d96` |
| [docs/phase10-results.md](phase10-results.md) | D — Phase 결과 | 한국어 재작성 | `acc504ca3b40f47ec2a1949915b96869328a311f79932c8d93f9cd62aa54f4ca` |
| [docs/phase6-results.md](phase6-results.md) | D + H — Phase 결과·동결 구역 | 한국어 재작성 | `325c6b6170b0bb3f1c175998189330acb14e3fefc2fec95b88dd5a6a3a642786` |
| [docs/phase7-prospective.md](phase7-prospective.md) | H — Frozen evidence / 당시 동결 기록 | 원본 보존 | `9c3443b74ed9b8b68c6bcc19859f1695970457c427372f66b88d560bdd91a1da` |
| [docs/phase7-results.md](phase7-results.md) | D — Phase 결과 | 한국어 재작성 | `ec299aea3c3c19ed8d6f1f23ca756131f6ee62649ffd222e834c7db959ff502b` |
| [docs/phase8-prospective.md](phase8-prospective.md) | H — Frozen evidence / 당시 동결 기록 | 원본 보존 | `a9c3d1c626af48081b67d7f3f5ef731d9fbd516e18dfa29a19f684322ac45b5e` |
| [docs/phase8-results.md](phase8-results.md) | D — Phase 결과 | 한국어 재작성 | `02716e646c856ba22380fac81885a3491ff5e19424ebf3e504ac049aba525117` |
| [docs/phase9-prospective.md](phase9-prospective.md) | H — Frozen evidence / 당시 동결 기록 | 원본 보존 | `305fa71594f5936a3da0701353d7e7c37a42f7faaaf9b0978a59f2e09d8f89af` |
| [docs/phase9-results.md](phase9-results.md) | D — Phase 결과 | 한국어 재작성 | `921f98080d42af1bcd4422de40b1c1a39880340d34ff0328bd35b45a782e57b3` |
| [docs/predictive-experiments.md](predictive-experiments.md) | E — 방법·초기 결과 | 한국어 재작성 | `cab1cfbd81eacf866a58e3c15d832e40fbb2f26b16a19b54ff70a48bb2bbdee9` |
| [docs/progress.md](progress.md) | I — Development/internal history | 원본 보존 | `fe6eaab2c53395d77f0f697f6966b7ace2798d6140389cd8d95169451ec10a08` |
| [docs/prospective-experiment.md](prospective-experiment.md) | H — Frozen evidence / 당시 동결 기록 | 원본 보존 | `f9f4aa4b830a665d8b2be3550444c3b95783ec8705b09f964f3a411bcd810143` |
| [docs/regime-research.md](regime-research.md) | E — 방법·초기 결과 | 한국어 재작성 | `e5482a8a1de30bd1215d99f60c38ba609a1f4f30c0ef2198b6f39d4b1492c5d1` |
| [docs/research-ideas.md](research-ideas.md) | C — Hypothesis notebook | 한국어 재작성 | `f035ac53d610a71d0cf2f51e8864786801c70c46424574aaa68e7d8710b4b7a0` |
| [docs/spatiotemporal-analysis.md](spatiotemporal-analysis.md) | E — 방법·초기 결과 | 한국어 재작성 | `2b93425391489b2112510568dba0385bfa4a06e6c23553de17e614084dccb76f` |
| [docs/superpowers/plans/2026-10-17-first-pass.md](superpowers/plans/2026-10-17-first-pass.md) | F — Historical protocol / 설계·계획 | 원본 보존 | `186842939596335a72a1f5ba7e2f9faba0fe26202a5c20504093c287bdc88441` |
| [docs/superpowers/plans/2026-10-17-phase10.md](superpowers/plans/2026-10-17-phase10.md) | F — Historical protocol / 설계·계획 | 원본 보존 | `bbd308af1c4f4eda533f1e228c4a86fcdd760a6dca2219553efd0db5e33bc942` |
| [docs/superpowers/plans/2026-10-17-phase6.md](superpowers/plans/2026-10-17-phase6.md) | F — Historical protocol / 설계·계획 | 원본 보존 | `269e6424f1716dc24fcd01db06464f846516f7457d2ef4845183dc831e4549f6` |
| [docs/superpowers/plans/2026-10-17-phase7.md](superpowers/plans/2026-10-17-phase7.md) | F — Historical protocol / 설계·계획 | 원본 보존 | `61885ec3d8069d05eec5c0b15a82a89b3857385b25ba1d709651ed161074238b` |
| [docs/superpowers/plans/2026-10-17-phase8.md](superpowers/plans/2026-10-17-phase8.md) | F — Historical protocol / 설계·계획 | 원본 보존 | `cafa761f7a072fdaa010dd4d1f5ed0d663b4db1d9e491343275fa7b7843af004` |
| [docs/superpowers/plans/2026-10-17-phase9.md](superpowers/plans/2026-10-17-phase9.md) | F — Historical protocol / 설계·계획 | 원본 보존 | `8faed826de8dde9430715dca857bb98c28c9d84d7008d46e3b66b8047979c21e` |
| [docs/superpowers/plans/2026-10-17-prediction.md](superpowers/plans/2026-10-17-prediction.md) | F — Historical protocol / 설계·계획 | 원본 보존 | `16393bef4fae91786198119c743d46f2927300f17c0a761bbc8228476f8a082d` |
| [docs/superpowers/plans/2026-10-17-prize-research.md](superpowers/plans/2026-10-17-prize-research.md) | F — Historical protocol / 설계·계획 | 원본 보존 | `eace69fc606e8aa2e4c852f2fd653ed31125bf1cc1aa457d43e2e68637f5c3c6` |
| [docs/superpowers/plans/2026-10-17-prospective-freeze.md](superpowers/plans/2026-10-17-prospective-freeze.md) | F — Historical protocol / 설계·계획 | 원본 보존 | `63353afe8787af64b621e2af0f8c7b6d38c2061addd7db143c513f7aa8b97f2b` |
| [docs/superpowers/plans/2026-10-17-regime-research.md](superpowers/plans/2026-10-17-regime-research.md) | F — Historical protocol / 설계·계획 | 원본 보존 | `dfc1a202821dbdb30d95f3da8a81da1ab32f2ed92fa5b7eb3fb0a53f044c544b` |
| [docs/superpowers/plans/2026-10-17-temporal.md](superpowers/plans/2026-10-17-temporal.md) | F — Historical protocol / 설계·계획 | 원본 보존 | `80991b3cf04ba44f9388d32f6ac76428a63b9f0b7c79624ea8025965dfba2210` |
| [docs/superpowers/specs/2026-10-17-first-pass-design.md](superpowers/specs/2026-10-17-first-pass-design.md) | F — Historical protocol / 설계·계획 | 원본 보존 | `2272e03af46dd30d3c44a52005f857518e49891fc53fa779bdca589e0561bc35` |
| [docs/superpowers/specs/2026-10-17-temporal-design.md](superpowers/specs/2026-10-17-temporal-design.md) | F — Historical protocol / 설계·계획 | 원본 보존 | `0caa061e980a96c2aae10eef016689f006a8385ee0e52498fc5821d23eb6b583` |
| [docs/temporal-analysis.md](temporal-analysis.md) | E — 방법·초기 결과 | 한국어 재작성 | `11536fd73c72ad33a1eb5d1e27f0d47fb8b5104c1dc5f0c0d184fb93e5d90e7d` |

## 새 문서

| 파일 | 분류·역할 |
|---|---|
| [README.md](README.md) | B — 전체 문서 색인, Phase 순서와 historical/frozen archive |
| [foundation-analysis.md](foundation-analysis.md) | E + D — README에서 옮긴 Phase 1 정의·초기 Random 결과 |
| [data-provenance.md](data-provenance.md) | E — source·schema·seal·검증·hash 범위 |
| [prospective-workflow.md](prospective-workflow.md) | G — 현재 시점의 한국어 설명 |
| [documentation-audit.md](documentation-audit.md) | I — 전체 inventory·검증·한계 |

## README와 색인의 구조

README는 프로젝트 소개·질문·연구 원칙·데이터·현재 결론·단일 H1–H17 table·
Phase 1–10의 시간순 요약·prospective·실행 방법·실제 구조·provenance·해석 주의로 구성합니다.
초기 Random 수치는 foundation-analysis.md로, source 세부 설명은 data-provenance.md로 옮겼습니다.
자세한 연구 결과를 README에 반복하지 않습니다.

docs/README.md는 연구 개요, Phase 1–5, 각 Phase 6–10, 미실행 Phase 11,
향후 가설, historical protocol archive, frozen evidence를 연결합니다.
모든 프로젝트 Markdown은 색인 또는 이 inventory에서 찾을 수 있습니다.

## 수정한 모순과 현재 상태

- 옛 H9 spatial neighborhood를 현재 H8로 고쳤습니다. H8는 TESTED / INCONCLUSIVE입니다.
- 옛 H8 delay / recurrence / tensor 묶음은 H9·H15 등으로 구분합니다.
- H9 / Phase 11은 BACKLOG이며 이 저장소에서 실행하지 않았습니다.
- H1–H6·H8는 TESTED / INCONCLUSIVE, H7은 DEFERRED, H9–H17은 BACKLOG입니다.
- README 끝의 중복 H9 BACKLOG 구역과 number-space 완료 상태의 모순을 없앴습니다.
- Phase 10→9→8→7로 뒤섞인 설명을 Phase 1→10으로 정리했습니다.
- Phase 6의 “H4 remains planned”는 당시 상황임을 밝히고 현재 Phase 7 완료 결과로 연결합니다.
- 현재 개요에서 1246회를 unknown future로 부르지 않습니다. 당시 동결 상태는 원본 그대로입니다.
- Phase 4의 실험 ensemble을 최종 H17 validated ensemble 완료로 해석하지 않습니다.
- 실제 CSV byte hash와 과거 LF canonical hash를 구분하고 기존 기록을 소급 변경하지 않습니다.

Canonical 이름·상태의 전문은 [가설 노트](research-ideas.md)에 있습니다.
수치·formula·technical identifiers·CLI·기술 table은 기존 보고값을 보존합니다.
각 Phase의 test count/runtime은 **당시 실행 기록**이며 아래 이번 테스트와 구분합니다.

## 실제 prospective 파일 inventory

작업 전 `reports/prospective/`는 **존재하지 않았습니다**.
실제 snapshot JSON·manifest·integrity JSON·reservation·registry와
`prior_prospective_hashes.json`도 이 체크아웃에 없습니다.
따라서 실제 prospective artifact inventory는 **0개**이며,
과거 문서가 보고한 파일 수와 현재 가용성을 혼동하지 않습니다.

실제 원본이 없으므로 Phase 5–10 frozen artifact 전체의 원본 hash 일치를
이번에 재검증했다고 주장할 수 없습니다. 누락을 mismatch나 성공으로 처리하지 않았습니다.
실제 prospective 생성·재생성·평가 작업은 하지 않았습니다.

등록 ranking·ticket·hash를 담은 다음 문서는 원문 전체를 byte-for-byte 보존했습니다.

| 보존 문서 | 수정 전·후 SHA-256 | 대조 |
|---|---|---|
| [prospective-experiment.md](prospective-experiment.md) | `f9f4aa4b830a665d8b2be3550444c3b95783ec8705b09f964f3a411bcd810143` | 동일 |
| [phase7-prospective.md](phase7-prospective.md) | `9c3443b74ed9b8b68c6bcc19859f1695970457c427372f66b88d560bdd91a1da` | 동일 |
| [phase8-prospective.md](phase8-prospective.md) | `a9c3d1c626af48081b67d7f3f5ef731d9fbd516e18dfa29a19f684322ac45b5e` | 동일 |
| [phase9-prospective.md](phase9-prospective.md) | `305fa71594f5936a3da0701353d7e7c37a42f7faaaf9b0978a59f2e09d8f89af` | 동일 |
| [phase10-prospective.md](phase10-prospective.md) | `f86dc73d3c215a7a5cae2d281ae60f33cfa33c090935440902f528d6680a3d96` | 동일 |

Phase 6 결과의 `## Frozen experiment record`부터 EOF까지도 원래 바이트를 보존했습니다.
그 구역의 수정 전·후 SHA-256은
`cdbf839a5c78477825b62ac95a29ad87d7f0d2c029ec357b4d8be2abc4692de5`입니다.
역사 protocol 13개와 progress.md도 전체 바이트가 같습니다.
원본 영문·legacy H번호·과거 timestamp·ticket·ranking·hash·옛 D: 링크는 수정하지 않았습니다.

## 현존 JSON의 hash record inventory

파일 이름뿐 아니라 현존 JSON의 nested field에 저장된 SHA-256 문자열도 확인했습니다.
count에는 같은 값의 여러 field가 포함되며 독립 artifact 개수가 아닙니다.
다음 파일 전체는 수정 전·후 바이트가 같습니다.

| 기록 파일 | SHA-256 값이 든 field 수 | 전후 대조 |
|---|---:|---|
| [reports/random_checkpoints.json](../reports/random_checkpoints.json) | 5 | 원본 byte hash 동일 |
| [reports/random_walk_forward.json](../reports/random_walk_forward.json) | 5 | 원본 byte hash 동일 |
| [reports/temporal_analysis.json](../reports/temporal_analysis.json) | 2 | 원본 byte hash 동일 |
| [reports/number_17/temporal_analysis.json](../reports/number_17/temporal_analysis.json) | 2 | 원본 byte hash 동일 |
| [reports/number_34/temporal_analysis.json](../reports/number_34/temporal_analysis.json) | 2 | 원본 byte hash 동일 |
| [reports/number_7/temporal_analysis.json](../reports/number_7/temporal_analysis.json) | 2 | 원본 byte hash 동일 |
| [data/raw/lotto_history.metadata.json](../data/raw/lotto_history.metadata.json) | 6 | 원본 byte hash 동일 |
| [data/raw/sources.json](../data/raw/sources.json) | 92 | 원본 byte hash 동일 |

sources.json의 92 fields는 canonical 1개와 normalized source snapshot 91개입니다.
metadata는 import/event의 canonical/input hash를 보존합니다.
이 snapshot의 원본 추출물은 현재 체크아웃에 없으므로 값 보존과 원본 대조는 구분합니다.
Markdown에 적힌 당시 freeze/hash 기록은 위 H 문서·Phase 6 구역·historical protocol과
각 Phase report에서 보존합니다. 실제 frozen integrity record를 새로 만들지 않았습니다.

## 데이터 SHA-256 전후

| 범위 | 수정 전 | 수정 후 |
|---|---|---|
| 실제 CSV bytes | `3b7bb1e0a37c28ae4b4a97e098180d8407008ec007698c191ed6cf279db8225b` | 동일 |
| CRLF→LF 읽기 전용 정규화 | `b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e` | 동일 |

dataset·sources.json·metadata를 고치지 않았고 새 회차를 가져오지 않았습니다.
전체 기존 파일 218개의 baseline hash를 메모리에 기록하고 전후 대조했습니다.
변경된 기존 파일은 Markdown 16개뿐입니다. 코드·데이터·기존 reports의 hash는 모두 같습니다.

## 링크와 Markdown 검증

현재 안내의 relative link·anchor를 검사했고 오류는 **0개**입니다. 누락된 산출물을 새로 만들거나
immutable 문서의 경로를 바꾸어 링크를 고치지 않습니다.
동결 증거에는 원래부터 해소할 수 없는 링크 **20개**가 있습니다.
Phase 6·7·8은 각 4개의 누락 원본 상대 링크, Phase 9·10은 각 4개의 legacy D: 링크입니다.
이를 원본 그대로 남기고 현재 색인에서 존재하는 보존 문서로 연결했습니다.

방법·결과의 numeric table rows는 원본과 동일합니다. prose의 숫자 literal과 40/64자리
hash도 대조하고, 초기 README의 결과 table은 foundation-analysis.md로 옮겼습니다.
문서별 H1 하나, fence·표·hierarchy와 현재 canonical 상태를 검사합니다.
보존 archive의 옛 표현은 현재 상태 충돌 검사에서 별도 분류합니다.
최종 검사에서 기존 숫자 literal·hash 누락, table 차이, H1·fence 오류는 모두 0개였습니다.
README는 303줄이며 H1–H17 table이 가설 노트와 일치합니다. `git diff --check`도 통과했습니다.

## 이번 전체 테스트

`python -m pytest -q`: **290 passed, 1 skipped in 86.31s**.

기본 Python에 pandas·pytest가 없어 저장소 안 `.deps/docs-checks`에 test dependency를
설치했습니다. 설치에 network 승인이 필요했고 Windows ACL 때문에 전체 테스트도
승인된 sandbox 밖 실행을 사용했습니다. package/TEMP/TMP/MPLCONFIGDIR은 저장소 안으로 지정했습니다.
새 Lotto data를 가져오거나 실제 결과를 평가한 것이 아닙니다.
추가한 환경은 Git-ignored이며 source·requirements·pytest 설정은 바꾸지 않았습니다.

과거 문서의 289 passed / 2 skips 등은 그대로 보존합니다.
이번 환경의 test outcome과 당시 기록을 소급 맞추지 않습니다.

## 정확한 변경 파일 목록

기존 파일 재작성:

- `README.md`
- `docs/frequency3d-analysis.md`
- `docs/gap-prize-research.md`
- `docs/gap3d-analysis.md`
- `docs/joint-state-analysis.md`
- `docs/number-space-analysis.md`
- `docs/phase10-results.md`
- `docs/phase6-results.md`
- `docs/phase7-results.md`
- `docs/phase8-results.md`
- `docs/phase9-results.md`
- `docs/predictive-experiments.md`
- `docs/regime-research.md`
- `docs/research-ideas.md`
- `docs/spatiotemporal-analysis.md`
- `docs/temporal-analysis.md`

새 파일:

- `docs/README.md`
- `docs/data-provenance.md`
- `docs/foundation-analysis.md`
- `docs/prospective-workflow.md`
- `docs/documentation-audit.md`

코드·모델 동작·canonical Lotto data·동결 순위/티켓·기존 integrity record는 수정하지 않았습니다.
commit·push를 하지 않았으며 Phase 11 구현이나 실험을 시작하지 않고 문서 정리에서 멈춥니다.
