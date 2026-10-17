# Phase 11 — H9 Delay Embedding / Recurrence Geometry

시작 상태: **IN PROGRESS**. 완료 결과는 [Phase 11 결과](phase11-results.md)에 기록한다.
중심 질문: **비슷한 과거 상태가 비슷한 미래 결과로 이어지는가?**

## 연구 경계와 구현 계획

기준: `27e545bd138627e671abd642c4149bb96022ed45`, main, 깨끗한 작업 트리.
연구 입력은 영구적으로 1–1245회만 허용한다. 알려진 1246회는 수집·열람·검증·선택에 사용하지 않는다.
H9는 기존 로드맵의 계보를 유지한다. Takens 정리나 결정론적 동역학을 가정하지 않는다.
이후 구간도 앞선 Phase에서 사용된 역사이므로 pristine holdout은 아니다.

1. 인과적 관측·embedding·distance·원자료 구간 제외를 구현하고 누출 방지 테스트.
2. recurrence 두 정의, RQA, successor 진단과 전체 surrogate parity를 구현·검증.
3. 개발 선택과 세 analog 모델, 기존 baseline을 같은 walk-forward 목표에서 비교.
4. 고정 개수 benchmark 후 null 실행, 그림·한국어 결과 기록.
5. 설정 동결 및 archive 복원 전 publication 차단 기능, 전체 테스트·변경 검토.
외부 checkout, commit, push는 하지 않는다.

## 사전 고정 설계

- A: 본번호 45차원 binary, bonus 제외. Hamming/Jaccard.
- B: sum, mean, population std, min, max, range, adjacent-spacing mean/std/min/max,
  consecutive-pair count, odd count, low count(1–22)의 13차원. high=6−low이므로 중복 제외.
  standardized Euclidean / cosine(원래 비음수 shape 좌표).
- C: W=10/26/52의 45차원 전체 번호 출현율. standardized Euclidean / cosine(원래 출현율).
- m=2/3/4, τ=1/2/4/8/13/26. 총 180개 설정. 차원 A/C=90/135/180, B=26/39/52.
- Euclidean scaler: 각 fit 시점 이하의 완성된 관측에서 평균·표준편차를 추정;
  구조 검정 scaler는 1–400회로 고정. cosine은 centering하지 않으며 영벡터 거리는
  둘 다 영이면 0, 한쪽만 영이면 1.
- S_t=[O_t,O_(t−τ),…,O_(t−(m−1)τ)]. 불완전한 상태는 만들지 않는다.
- 길이 L trajectory의 원자료 보수적 구간 I_t=[t−h,t], h=(m−1)τ+W−1+L−1,
  A/B는 W=1. 끝점 i<j의 쌍은 i+1<j−h일 때만 유효하다.
  따라서 |i−j|>h+1. 실제 사용 좌표 사이 빈 구간까지 제외하는 보수적인 Theiler 규칙이다.
  analog j는 j+1<T이고 j+1<T−1−h. successor가 현재 상태의 원자료와도 겹치지 않는다.
- 구조 검정은 **661–899회 끝점(239개)**의 연속 구간, successor는 최대 900회.
  전체 1–900을 입력으로 표현을 재계산한다. 이는 계산량을 제한하기 위한 고정 구간이며
  데이터 결과에 따른 선별은 없다. rolling과 이후 역사 그림은 선택된 설정의 설명 진단이다.
- recurrence: eligible 쌍에서 k=10 directed nearest graph의 union 대칭화;
  별도로 eligible unordered 쌍의 정확한 하위 10% 거리 edge. 경계 동률은 시간 인덱스 순서.
  고정 density의 RR은 검정 증거가 아니다. diagonal/vertical 최소 길이=2.
- 다섯 family: DET, Lmax, laminarity, recurrence-time CV, −Spearman(distance, successor overlap).
  전체 180×2×5=1,800 cell; successor 통계는 recurrence 정의에 독립적이므로 중복은 1회 계산.
  각 surrogate는 모든 설정·family를 다시 계산하고 자체 최대값을 낸다.
  (1+초과 개수)/(B+1), family 5개 Bonferroni; 두 null 모두 통과해야 구조 증거로 해석.
- successor: 모든 유효 쌍의 overlap/Jaccard, distance decile, Spearman, 이전 nearest와 ordinary pair 비교.
  쌍들이 독립이 아니므로 분석적 Spearman p-value는 쓰지 않고 전체 surrogate 최대값으로 검정한다.
- 개발 목표 401–900, 이후 목표 901–1245. scaler refit cadence=26; sensitivity=13.
  각 모델별 평균 Top6 hits 최대, 동률은 선언 순서. nearest=180개;
  analog=180×K(5/10/20/40)×weight(uniform/inverse)=1,440개;
  continuation=동일 설정×L(2/3)=2,880개. inverse weight=1/(distance+1e−6).
  RQA recurrence 정의는 구조 설명용으로 개발 구간 DET 최대 설정을 기록하며 예측 가중치에 사용하지 않는다.
- 개발 안정성은 401–800, 501–900의 동일 후보 선택. 이후 결과로 설정을 바꾸지 않는다.
- 이후 시작 901/1001/1101, 시대 901–1015/1016–1130/1131–1245.
  RandomModel, Frequency26, GapLogistic과 같은 목표에서 비교.
  paired circular block-bootstrap 길이26, 2,000회; sensitivity 길이13.
- IID와 기존 fixed-margin swap surrogate 각 199회 목표. 두 개씩 benchmark 후 실행시간 추정.
  모든 null은 위의 동일한 고정 구조 구간과 전체 설정 탐색을 사용한다.
- 수치 동률 순위는 기존 프로젝트 규칙(번호 오름차순); 의미 있는 점수 차이로 해석하지 않는다.

## Prospective 경계

기존 `reports/prospective/` 부재는 역사 연구를 막지 않는다. 옛 artifact·hash는 재구성하지 않는다.
연구 설정을 동결한 뒤 별도 명시적 절차에서만 검증된 1246회를 훈련에 추가할 수 있다.
1247 publication은 복원된 archive와 원래 integrity evidence 확인이 선행되어야 한다.
이 실행의 상태는 archive가 없으면 **PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**이다.

## 실행과 검증 기록

구현은 기존 `src/analysis`, `src/models`, `src/backtest` 및 main CLI 구조를 따른다.
`executing-plans` 방식으로 이 checkout에서 직접 구현했다. 별도 worktree·복사본은 만들지 않았다.
설계·TDD·완료 검증 스킬을 적용했고, `requesting-code-review`에 따른 독립 읽기 검토를 수행했다.

- 초기 수학 테스트 11개, 모델·null 테스트를 포함한 19개가 순차적으로 통과했다.
- 개발 탐색 첫 실행은 전체 계산 후 안정성 요약에서 `window` 필드 충돌로 저장에 실패했다.
  기간 이름을 `period`로 분리하고 재현 테스트를 추가했다. 동일 후보·목표·선택 규칙으로 재실행했다.
  거리의 이웃 정렬을 K/weight 간 재사용하여 계산량만 줄였다. 결과를 보고 search를 바꾸지 않았다.
- 독립 검토의 세 지적을 재현 테스트 후 수정했다: 부분 archive readiness,
  거부된 재실행의 보고서 덮어쓰기, analog 예시의 scaler cutoff 불일치.
- 일반 CSV loader 대신 기존 strict prefix reader를 재사용했다. header+1245행 이후 suffix가 있으면
  그 행을 파싱하기 전에 파일 크기 검사로 거부한다.
- 구조 null은 각 199회, 총 398회 전부 실행했다. 고정 benchmark 2+2회는 별도 seed이며 추론에 섞지 않는다.
- raw distance·NN distance 분포는 `real_search.csv`의 모든 설정에 저장한다.
  recurrence-time은 같은 행의 연속 recurrence 열 좌표 차이이며, 경계·제외대역에 따른 검열을
  별도로 보정하지 않는다. 동일 조건 null이 비교 기준이다. diagonal/vertical 길이 단위는 회차이다.
- kNN union과 fixed-density 모두 시간 이웃의 중첩으로 line persistence가 나타날 수 있다.
  Theiler로 가까운 쌍을 제외해도 rolling 관측 자체의 지속성은 남으므로 반드시 전체 surrogate와 비교한다.

## 재실행 명령

```powershell
python main.py recurrence benchmark
python main.py recurrence analyze --surrogates 199 --workers 4
python main.py recurrence select
python main.py recurrence compare --cadence 26
python main.py recurrence compare --cadence 13
python main.py recurrence plots
python main.py recurrence prepare-freeze
python -m pytest -q
```

기존 null/선택 증거가 있으면 새 탐색은 거부한다. 새 연구 출력은 `--reports-dir reports/recurrence/<새 실행>`으로 분리한다.
마지막 prepare-freeze는 현재 archive 부재로 거부되는 것이 정상이다. 실제 snapshot 발행 명령은 제공하지 않는다.
복원 후에는 원래 protected inventory에 Phase 5–10 registry·snapshot·manifest·integrity·reservation이
포함되어야 하며 기존 phase별 verifier로 검증한다. 준비 기능은 설정 고정과 복원 검증 gate까지이다.
검증된 1246회의 명시적 import, 별도 prospective scope에서의 refit, 결과 미공개 확인과 publication은
후속 명시적 단계에 남긴다. 연구용 API의 1245 cutoff는 그때도 완화하지 않는다.
