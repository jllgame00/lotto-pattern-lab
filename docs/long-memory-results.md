# Phase21 / H20 — Long-memory / fractal scaling / DFA 결과

## 최종 과학적 결정

**H20: TESTED / INCONCLUSIVE.** 1–1245회에서 long-range dependence가 corrected null testing을 통과하지 못했다. DFA curve의 persistence/anti-persistence, 높은 R², crossover 또는 rolling 극단값만으로 장기 기억을 선언하지 않는다. 무작위성을 증명했다는 뜻도 아니다.

**PREDICTIVE_MODEL_NOT_JUSTIFIED.** LongMemoryModel/ScaleStateModel은 만들지 않았다. RandomModel/Frequency26/Gap Logistic 비교, paired predictive uncertainty,rank diversity도 실행하지 않았다. 정당화되지 않은 predictor의 성능을 억지로 보고하지 않는다. Ensemble 후보는 **NOT CURRENTLY JUSTIFIED**, H17은 BACKLOG다.

방법은 [Phase21 분석](long-memory-analysis.md), 중단 전 고정 규칙과 재개 이력은 [실행 계획](superpowers/plans/2026-10-18-phase21.md)에 있다. H21 Random Matrix Theory와 이후 Phase는 시작하지 않았다.

## 재개 당시 상태와 완료 범위

|분류|재개 시 확인한 내용|재개에서 수행한 일|
|---|---|---|
|COMPLETE|사전 고정 계획,수학 DFA/R/S/crossover,55개 표현,aggregation/spectrum/rolling 구현과 수치 테스트|기존 올바른 모듈을 보존하고 실제 재실행으로 확인|
|PARTIALLY COMPLETE|CLI/complete-search 통합; 최초 Phase21 테스트65 passed/4 failed|미지원 rolling window 호출 및 빈 archive guard 수정; crossover 미지원 N312 테스트 fixture를N416으로 수정|
|IMPLEMENTED BUT NOT VERIFIED|pilot/null/development gate/diagnostics 코드|고정32pilot×2scope,199IID+199fixed×2scope,개발 decision,bootstrap/10plots를 실제 실행하고 검증|
|NOT STARTED|실제 산출물,한국어 방법/결과,최종 audit/manifest|모든 산출물·문서·hash manifest와 무결성 검사 완료|

재개 시 Phase21 reports/plots/partial manifest는 없었다. 기존 uncommitted 파일은 삭제하거나 초기화하지 않았다. 독립 reviewer는 수학과 complete-search의 critical 오류를 찾지 않았지만 predictive gate가 다른 family의 유의성과 무관한 series 안정성을 결합할 수 있음을 지적했다. Synthetic 반례를 실패 테스트로 확인한 뒤 saved family winner와 선택 series/방향의 연결을 요구했다. 이는 수치 검색/null 통계를 바꾸지 않는다. 실제 데이터에서는 passing family가0개이므로 과학적 결론에도 영향이 없다.

## 실제 검색 범위와 유한 크기

DFA1 primary,사전 scales **8,13,21,34,52,78,104,156,208,312**다. 서로 다른 forward segment4개 이상 조건 때문에 전체1245/개발900에서 사용한 scale은 **8,13,21,34,52,78,104,156,208**이다.312는 최소1248회가 필요하므로 미지원이며 미래 자료를 추가하지 않았다. DFA2는 secondary sensitivity만 사용했다.

|scope|series|선언 cells|eligible cells|rolling fits|rolling cells|
|---|---:|---:|---:|---:|---:|
|전체1–1245|55|3200|3145|49|2695|
|개발1–900|55|2210|2155|31|1705|

Series는 번호45,whole-draw scalar5,band count5개다. 각 scope의55개 제외 cells는 crossover boundary156이다. 양쪽2scale 조건에서156 위에는208만 있으므로 검정하지 않는다. Boundary52/104는 지원된다. 전체 null 각각이 같은 지원/비지원 구조와 검색 자유도를 가졌다.

Pilot seed211001,각 scope32IID; main seed210042,IID199/fixed199,worker3이다. 각 main surrogate는 전체와 개발을 별도로 생성해 총796개 scope-search를 수행했다. Fixed margins는 해당 scope의 row합6/번호별 총빈도를 보존했다. 본 실험 runtime은 **446.862912초**였다. Benchmark serial 예상1997.917초는 추정치이며 실제3worker runtime과 구분한다.

## 강한 개별 예시와 null 중심화

|진단|series/구간|관측값|
|---|---|---|
|최대 persistent DFA1|number22|alpha=.605785500,R²=.991140042,curvature=.057512408|
|최대 anti-persistent DFA1|number35|alpha=.406336383,R²=.987142797,curvature=−.048961131|
|최대 crossover improvement|number16,boundary52|SSE 감소=.929145624,short alpha=.531966397,long alpha=.349626264|
|aggregation global standardized winner|number13|slope=−1.135405052,R²=.994295093,절대편차=.135405052,z=2.986724005|
|raw aggregation 최대편차|number22|slope=−.857862389,R²=.994084599,절대편차=.142137611,z=1.385144114|
|rolling global standardized winner|number38,W624,157–780|alpha=.650860263,z=5.251500644|
|raw rolling 최대편차|number31,W312,885–1196|alpha=.272580972,절대편차=.227419028|
|raw whole-system 최대편차|odd_count|alpha=.437709459,R²=.994448009|
|whole-system global standardized winner|band19–27|alpha 절대편차=.044605132,z=1.308542730|

Raw 최대편차와 cell별 pilot 표준화 뒤 winner는 다를 수 있다. p값은 후자의 family maximum에 대응하며 특정 raw curve를 고정한 local p값이 아니다. 높은 crossover 개선도 동일한 최대 개선을 찾는 null에서는 흔했다.

Number22의 유한 표본 alpha 중앙값은 IID=.501204299,fixed=.501742472이며 centered alpha는+.104581201/+.104043027이었다. Number35는 IID=.502173999,fixed=.500741629에서 centered−.095837615/−.094405246이었다. Number35의 matching-cell percentile이0이어도55series/여러family 검색의 global evidence가 아니다. 55열 전체의 보정표를 `finite_sample_alpha_calibration.csv`에 보존했다.

## 전체1–1245 global-max 검정

두 null 각각199회이며 p=(1+exceedances)/200,primary Bonferroni6이다.

|primary family|real z max|IID global p|IID corrected p|fixed global p|fixed corrected p|
|---|---:|---:|---:|---:|---:|
|persistent|3.109765|.110|.660|.110|.660|
|anti_persistent|2.551720|.405|1|.355|1|
|crossover|2.820419|.435|1|.415|1|
|aggregation|2.986724|.660|1|.645|1|
|rolling|5.251501|.495|1|.490|1|
|whole_system|1.308543|.690|1|.740|1|

Secondary3family는 별도 Bonferroni3이다. R/S global p=.775/.820,spectral=.755/.780,DFA2=.900/.885 (IID/fixed)이며 전체 corrected p는 모두1이었다. Number22의 R/S=.615471874와 spectral beta=.508943415도 보조 진단이다. 후자의 R²=.168747348,고정 저주파46bins로 안정된 power-law를 주장할 근거가 아니다. DFA2 alpha는 number22=.566114515,number35=.438052482로 DFA1에서 이동했지만 별도 null 검정도 통과하지 못했다.

## 개발 gate,시간 안정성,bootstrap

|개발 primary family|IID global / corrected p|fixed global / corrected p|
|---|---:|---:|
|persistent|.190 / 1|.110 / .660|
|anti_persistent|.870 / 1|.905 / 1|
|crossover|.775 / 1|.820 / 1|
|aggregation|.655 / 1|.665 / 1|
|rolling|.615 / 1|.620 / 1|
|whole_system|.790 / 1|.830 / 1|

개발 선택 series는number22지만 passing/linked family는 모두없다. 개발 alpha=.631167138,세 개발 구간1–300/301–600/601–900은.528638439/.538647765/.469236551로 방향도 유지되지 않았다. 개발 decision의 SHA-256은 `57cb7a146d04e9f55ff145be15c9c637e7f9d390e9bc339f549628e5b95a5fe0`이다.

전체의 별도 기술적 세 구간1–415/416–830/831–1245에서 number22 alpha는.534678821/.497981941/.492916485,number35는.512046648/.451116712/.413223692였다. Whole-sample의 높은 alpha를 모든 시대에 유지되는 장기 의존성으로 해석할 수 없다. Rolling W312/416/624,stride52의55열 모두를 기록했고,그2695cells의 전체 최대값도 양 null의 중앙값 부근이었다.

선택 series의199회 circular moving-block bootstrap(seed211999)95%구간은 다음과 같다.

|series|block26|block52|
|---|---|---|
|number22|[.472429,.613163]|[.485766,.621252]|
|number35|[.381604,.519092]|[.392766,.525086]|
|odd_count|[.390988,.509516]|[.383186,.504081]|

이 구간은 선택 이후의 descriptive finite-block CI이며 asymptotic H 또는 탐색 전체에 대한 신뢰구간이 아니다. 선택된 curve/CI만으로 global null 결론을 뒤집지 않는다.

## 산출물과 검증

최종 전체 suite는 **1083 passed,1 skipped,0 failed**,223.07초였고 Phase21 tests는71개다. Skip은 기존 `tests/test_predictive_models.py:52`의 optional LightGBM/XGBoost 미설치다. Gate 수정 전 전체 suite의1081 passed/1 skipped 로그도 덮어쓰지 않고 별도로 남겼다. 최종 suite는 gate 수정과71개 Phase21 tests를 모두 포함한다.

`reports/long_memory/`에는 scope별 calibration/raw metrics/398null vectors/own maxima/36개 비교행,개발 결정,55series calibration,bootstrap,temporal/rolling/DFA2/R/S/spectral CSV와10plots가 있다. `audit_result.json`은64pilot를 모두 exact replay하고 IID/fixed 첫/마지막 replicate×두scope의8개 complete-search raw vector를 seed로 재생성했음을 기록한다. 모든796개 저장 null vector는 별도로 standardization→own family maximum→global p→correction을 재계산했다.398개 원래 history 모두를 재생성했다는 주장은 하지 않는다. 실제55열 DFA는 별도 direct least-squares 구현과 비교했다. Bootstrap199×두block 및 matched seed211234 curve도 exact replay했다.

이 checkout의 canonical CSV raw-byte SHA-256은 `3b7bb1e0a37c28ae4b4a97e098180d8407008ec007698c191ed6cf279db8225b`로 재개 전후 불변이다. 이전 Phase 문서의 당시 해시 기록을 소급 수정하지 않는다. 재개 전 자료와 기존 reports550개 파일의 hash,HEAD를 별도로 보호했다. 기존 prospective archive 자체는 없는 상태여서 해당 원본의 byte 비교가 가능하다고 주장하지 않는다. 최종 전체 테스트/산출물 hash/정확한 변경 목록은 같은 디렉터리의 test_result/manifest에 기록한다.

**Prospective capability: NOT CREATED — NO JUSTIFIED PREDICTIVE MODEL.**

**PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**

정확한 변경 파일은18개다. 아래에는 재개 전 uncommitted Phase21 파일도 포함한다. Ignore된 local 산출물 전체는 `reports/long_memory/manifest.json`에 별도 hash inventory로 기록한다.

```text
.gitignore
README.md
docs/README.md
docs/research-ideas.md
docs/long-memory-analysis.md
docs/long-memory-results.md
docs/superpowers/plans/2026-10-18-phase21.md
src/cli.py
src/analysis/long_memory.py
src/analysis/long_memory_diagnostics.py
src/analysis/long_memory_search.py
src/analysis/long_memory_series.py
src/long_memory_cli.py
tests/test_long_memory.py
tests/test_long_memory_cli.py
tests/test_long_memory_diagnostics.py
tests/test_long_memory_search.py
tests/test_long_memory_series.py
```

실제1246 fetch/import/use/evaluation 없음,canonical 수정 없음,과거 prospective evidence 수정 없음,1247 publication 없음,commit/push 없음. Phase21에서 종료한다.
