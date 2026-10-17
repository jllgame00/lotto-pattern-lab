# 데이터와 provenance

## 데이터 범위와 schema

canonical 파일은 [lotto_history.csv](../data/raw/lotto_history.csv)입니다.
1–1245회, 2002-12-07–2026-10-10의 연속 1,245개 회차를 저장합니다.

`draw_no, draw_date, num1, num2, num3, num4, num5, num6, bonus` 형식이며,
본번호는 회차 안에서 오름차순, 회차도 오름차순입니다.
year·month·iso_week·weekday(Monday=0)는 loading 시 파생합니다.
본번호 여섯 개로 45차원 binary series를 만들고 주요 예측 target에서 bonus를 제외합니다.

## 출처와 한계

공식 collector는 Donghaeng 결과 사이트와 웹 endpoint를 대상으로 구현했습니다.
다음 주소는 당시 provenance 설명이며 이번 문서 작업에서 접속·검증하지 않았습니다.

- 공식 결과 사이트: `https://www.dhlottery.co.kr/lt645/result`
- 웹 endpoint: `https://www.dhlottery.co.kr/lt645/selectPstLt645InfoNew.do?srchDir=center&srchLtEpsd=1`
- 과거 경로 `common.do?method=getLottoNumber&drwNo=...`는 재설계 후 가용성을 가정하지 않습니다.

응답은 `data.list` batch, 회차 `ltEpsd`, 날짜 `ltRflYmd`,
본번호 `tm1WnNo`–`tm6WnNo`, bonus `bnsWnNo`를 기대합니다.
문서화되지 않은 웹 endpoint이며 보장된 public API가 아닙니다.

구현 당시 제한 환경에서 Python HTTP 연결이 WinError 10061로 실패했습니다.
공식 live JSON adapter는 schema/error handling 테스트를 갖췄지만 end-to-end 검증을
완료하지 못했습니다. 실패를 “전체 자료 수집 완료”로 처리하지 않습니다.

당시 GitHub connector로 받은 공개 snapshot을 명시적으로 import했습니다.

- 1–1156회: `hyomuel/Lotto/data.json`
- 1157–1245회: `johyunchol/lottogo-python/src/constant/draw_no/{draw_no}.json`
- 1·500·1156회는 두 mirror에서 대조해 일치했습니다. 전수 공식 검증은 아닙니다.

[sources.json](../data/raw/sources.json)은 범위·URL·retrieval·snapshot hash를,
[metadata](../data/raw/lotto_history.metadata.json)는 import event·input hash·canonical hash·
missing/error diagnostics를 보존합니다. 원래 정규화 snapshot의 기록 위치는
`data/raw/snapshots/`이며 Git-ignored이고 현재 체크아웃에는 없습니다.
moving branch URL과 정규화 추출물의 hash는 원본 upstream JSON bytes의 보증이 아닙니다.
자동 mirror fallback은 없습니다.

## 검증·쓰기 규칙

null·fractional·boolean 숫자, 본번호 중복, 1–45 범위 이탈, 본번호와 같은 bonus,
중복 회차, 2002-12-07부터의 주간 calendar와 맞지 않는 날짜를 거부합니다.
회차 누락을 zero appearance로 바꾸지 않습니다. 분석·backtest는 불완전 history를 거부합니다.

import는 같은 회차의 동일 row를 합치고 충돌 결과는 중단합니다. invalid 값을 고치지 않습니다.
collector는 기존 회차를 건너뛰고 제한된 retry·timeout·간격으로 missing draw를 요청하며,
실패 시 성공한 partial progress와 missing/error JSON, exit code 1을 남깁니다.
CSV는 같은 directory 임시 파일 후 atomic replacement로 저장합니다.
동시 writer는 지원하지 않습니다. completeness는 저장된 endpoint까지의 확인이며
최신성이나 공식 원본 일치를 보증하지 않습니다.

## Research seal과 재현

초기 전체 자료 분석과 이후 seal 적용 연구를 구분합니다.
기존 predictive / prize / regime 연구는 1244회까지의 bounded prefix를 사용합니다.
Phase 6–10 전용 offline 연구는 1245회까지 허용합니다.
과거 Phase에서 이미 본 구간을 새 pristine holdout으로 부르지 않습니다.

수집·import·새 결과 평가를 이번 작업에서는 수행하지 않았습니다.
실행 가능한 import 명령의 존재와 연구 seal에 따른 실행 허용은 별개입니다.

## SHA-256 범위

이번 문서 정리 전 CSV의 **실제 바이트** SHA-256:

`3b7bb1e0a37c28ae4b4a97e098180d8407008ec007698c191ed6cf279db8225b`

과거 metadata·연구 문서의 canonical SHA-256:

`b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e`

현재 파일의 CRLF를 LF로 정규화하여 읽기 전용으로 계산하면 두 번째 값과 일치합니다.
현재 바이트 hash는 metadata의 `input_sha256`와 일치합니다.
기존 hash gate를 수정하거나 실제 CSV 개행·metadata·과거 기록을 다시 쓰지 않습니다.
byte integrity와 개행 정규화 후 내용 일치는 서로 다른 검증 범위입니다.
