# Prospective experiment 운영 안내

## 목적과 현재 시점

prospective freeze는 결과를 보기 전에 예측·설정·티켓을 고정하여 hindsight와
cherry-picking을 막는 절차입니다. 동결 자체는 예측력의 증거가 아닙니다.

draw 1246은 현재 외부에 알려져 있습니다. Phase 5–10의 draw-1246 실험은 결과가
알려지기 전에 만든 역사 기록으로 보존합니다. 원본에 “미래”나 “unknown”이 남아 있어도
현재의 새 실험 대상이라는 뜻이 아닙니다. 결과를 자동으로 가져오거나 평가하지 않습니다.

## 절차

research → development → configuration freeze → dataset hash → Git SHA
→ score/ranking freeze → ticket freeze → SHA-256 → FROZEN_UNEVALUATED
→ 이후 명시적 결과 입력과 별도 평가

1. Development history에서만 설정·weight를 선택하고 평가 범위를 분리합니다.
2. 허용된 데이터 cutoff·파일 해시 범위·Git SHA와 dirty 상태·구현 버전을 기록합니다.
3. 모든 번호의 score/ranking·tie 규칙·TopK·직접 Top6를 보존합니다.
4. 사전 선언한 seed·pool·예산의 티켓을 고정합니다. 예산 간 nested portfolio도 기록합니다.
5. snapshot JSON·manifest·integrity·registry를 검증하고 기존 파일을 덮어쓰지 않습니다.
6. 상태를 FROZEN_UNEVALUATED로 남깁니다.
7. 이후 승인된 명시적 결과 입력으로 별도 evaluation 파일을 만듭니다. 원본을 수정하지 않습니다.

로컬 timestamp와 SHA-256은 외부의 신뢰할 timestamp 인증을 대신하지 않습니다.
현재 소스가 변경되어도 당시 source archive·configuration을 기준으로 기록을 해석합니다.

## 보호 대상

`reports/prospective/**`, frozen manifests, snapshot JSON, integrity/hash records,
registry·reservation, 등록된 ranking·ticket evidence와 hashed Markdown은 immutable입니다.
영문·옛 H번호·옛 절대 경로도 소급 수정하지 않습니다.

문서 정리에서는 [기존 prospective 원본 목록](README.md#frozen-prospective-evidence)에
링크만 제공합니다. Phase 6 결과 문서 안의 frozen experiment record 구역도 그대로 둡니다.

## CLI와 평가 범위

기존 명령은 `freeze-next`, `freeze-2d`, `freeze-gap3d`,
`freeze-frequency3d`, `freeze-joint`, `freeze-number-space`입니다.
이름의 존재가 알려진 target의 재생성을 허용하지 않습니다. 중복 생성은 금지합니다.
Phase별 publisher·registry와 verifier를 혼용하지 않습니다.

Phase 5 평가 인터페이스는 다음과 같습니다. 여기서는 사용법만 기록하며 실행하지 않습니다.

```powershell
python main.py evaluate-freeze <snapshot.json> <result.json> --output <new-evaluation.json>
```

이 명령을 다른 Phase의 evaluator로 재사용한다고 가정해서는 안 됩니다.
당시 세부 protocol은 [Phase 5 원본](prospective-experiment.md)과 각 Phase 방법을 참고합니다.

## 향후 Phase 11과 draw 1247

H9 / Phase 11은 BACKLOG이며 이 저장소에서 실행되지 않았습니다.
역사 연구·선택·null 비교·평가는 1–1245회만 사용합니다.
1246회는 Phase 11 validation evidence로 쓸 수 없습니다.

방법·설정·결과를 모두 확정한 뒤에만 검증된 1246회를 추가 training observation으로
도입할 수 있습니다. 그 이후 방법·parameter·model 선택을 바꾸지 않습니다.
진정한 다음 prospective target은 1247회입니다.
검증된 1246회 import가 없으면 freeze를 실행하지 않습니다.

이 문서 정리는 Phase 11 모델이나 draw-1247 freeze capability를 구현하지 않습니다.

## 현재 파일 가용성과 검증 한계

이 체크아웃에는 `reports/prospective/`와 실제 동결 snapshot·manifest·integrity·registry가
없습니다. 과거 문서에 기록된 해시를 그대로 보존했지만 원본 파일과 대조하지 못했습니다.
과거 문서의 “검증 완료”는 당시 실행의 보고이며 이번 실행의 재검증 결과가 아닙니다.
[Inventory와 검증 기록](documentation-audit.md)을 참고하세요.
