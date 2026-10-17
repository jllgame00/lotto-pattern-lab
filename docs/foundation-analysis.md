# Phase 1 — 데이터·기초 분석·Random baseline

## 결론

RandomModel 결과는 이론적 티켓당 평균 0.8개와 양립했습니다.
이는 평가 pipeline 점검이며 예측 우위를 뜻하지 않습니다.

## 가설과 데이터 및 검증 범위

Korean Lotto 6/45의 본번호 여섯 개를 다룹니다. 초기 snapshot은
1–1245회, 2002-12-07–2026-10-10입니다.
출처·검증의 한계는 [provenance](data-provenance.md)를 참고합니다.
이 문서는 README의 기존 기초 방법과 초기 수치를 옮긴 것이며 새 분석을 실행하지 않았습니다.

## 방법

`binary_series(history)`는 draw-indexed, 45-column `uint8` DataFrame을 반환합니다.
각 row는 정확히 six ones이며 bonus는 제외합니다.
출력 위치는 `data/processed/number_series.csv`입니다.

`inspect_number(history, number)`는 전체 빈도·rate·최근 26/52/104 빈도와 실제 분모,
completed appearance interval, mean·median·population variance/std, 연속 출현과
최장/current run·current gap을 보고합니다.

appearance interval은 출현 간 회차 거리로 연속 출현이면 1입니다.
current gap은 마지막 출현 뒤 불출현 수로 endpoint에서 출현하면 0입니다.
한 번도 출현하지 않았으면 current gap은 `None`, 관측 불출현 길이는 lower bound입니다.
출현 두 번 미만이면 completed-gap 통계는 `None`입니다.
censored boundary gap은 completed interval에서 제외합니다.
표본이 작은 completed gap에는 불안정 표시를 합니다.

## Leakage 방지

target N에서 `run_backtest`는 새 unfitted model에 1–N−1회 deep copy만 전달합니다.
extra column을 제거하며 context는 target draw와 training 마지막 날짜에서 계산한
다음 예정일만 포함합니다. 실제 결과는 유효 티켓 생성 후 읽습니다.

모델 인터페이스는 `score_numbers(history, target_draw_context)` 또는
`predict(history, context=None, k=6, seed=None)`입니다.
RandomModel은 동일 score에서 중복 없는 여섯 정수를 uniform sampling합니다.
model factory는 매 ticket마다 새 model을 반환하며 checkpoint·repeat 사이에 재사용하지 않습니다.

이 인터페이스는 security sandbox가 아닙니다. 모델이 전역 full-history 파일·prefitted state·
외부 미래 자료를 읽어서는 안 됩니다. 전체 자료 탐색 export는 예측 입력이 아닙니다.
경계·target/future poisoning·history mutation·새 instance 검증 테스트를 유지합니다.

## Backtesting과 평가 지표

`--min-train 299`는 1–299회로 target 300부터 평가합니다.
walk-forward는 마지막 저장 회차까지, checkpoints는 eligible target을 seed로 중복 없이 뽑습니다.
start/end는 평가 target만 제한하고 training prefix는 바꾸지 않습니다.
tickets·repeats는 같은 결과에 대한 simulation 수를 늘리며 독립 회차 수를 늘리지 않습니다.
seed는 root seed·target·repeat·ticket index에서 정해 부분 구간에서도 재현됩니다.
서로 다른 ticket은 우연히 같을 수 있으나 한 ticket 안의 번호는 중복되지 않습니다.

CSV audit와 JSON에는 평균 적중, 0–6 분포, 3+/4+/5+ rate, best match, repeat별 평균,
configuration·package versions·dataset hash/provenance·약 95% 평균 interval을 저장합니다.
초기 interval은 target별 ticket/repeat 평균을 함께 resample하는 bootstrap입니다.
시계열 의존 오류에는 block bootstrap이 필요하며 rare-event interval·다중비교는 초기 범위 밖입니다.

## 주요 결과와 Null 비교

uniform 기준은 hypergeometric입니다.

```text
P(matches=m) = C(6,m) * C(39,6-m) / C(45,6)
E[matches] = 0.8
```

초기 seed-42 검증 수치는 다음과 같습니다.

| Run | Targets | Tickets | Mean matches | Approx. 95% CI | Best |
|---|---:|---:|---:|---|---:|
| Walk-forward, draws 300–1245 | 946 | 946 | 0.788584 | 0.738901–0.837209 | 4 |
| 100 checkpoints, 5 tickets × 10 repeats | 100 | 5,000 | 0.788800 | 0.767200–0.810205 | 4 |

두 interval은 모두 0.8을 포함합니다.
초기 Random baseline은 이후 모델 간 검증과 구분합니다.
best ticket은 발행 수의 영향을 받으며 skill의 증거가 아닙니다.

## 출력 파일과 CLI

`backtest`, `inspect`, `export-series`, `analyze-all`은
[README 실행 방법](../README.md#실행-방법)에 있습니다.
초기 저장 summary는 `reports/random_walk_forward.json`,
`reports/random_checkpoints.json`입니다.
`--data`는 subcommand 앞에 둡니다. relative output은 cwd 기준이며 default는 project root 기준입니다.

## Prospective experiment

Phase 1은 새 prospective freeze를 만들지 않았습니다.
이후 체계는 [prospective workflow](prospective-workflow.md)를 참고합니다.

## 해석·한계·다음 단계

기초 검증은 데이터 최신성이나 공식 전수 대조를 보장하지 않습니다.
Random simulation의 좋은 개별 티켓과 전체 성능을 혼동하지 않습니다.
다음 실행 단계였던 시간 구조 분석의 완료 결과는 [Phase 2](temporal-analysis.md)에 있습니다.

초기 README에 기록된 전체 테스트 환경은 Python 3.13.1이었습니다.
오프라인 테스트의 임시 경로는 Windows sandbox에서 다시 열 수 있도록 상속 ACL을
사용하고 pytest의 optional cache는 비활성화합니다.
