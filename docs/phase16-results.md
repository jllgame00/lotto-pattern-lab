# Phase16 결과 — H14 Entropy / Compression / Algorithmic Randomness

**H14: TESTED / INCONCLUSIVE.** 예측 모델과 ensemble 후보는 **NOT CURRENTLY JUSTIFIED**다.

실제 자료가 project null보다 덜 복잡하거나 더 압축된다는 증거가 없었고,
정확히 같은 draw의 chronological ordering에도 보정 후 추가 구조가 없었다.
따라서 **entropy/compression은 hidden temporal structure의 근거를 제공하지 못했다.**
이는 true randomness의 증명이나 모든 가능한 구조의 영구 부정이 아니다.
개발 gate가 실패하여 예측 모델·미래 snapshot infrastructure를 만들지 않았다.

## 시작 상태·자료 보호

- Git root: `C:/Users/Samsung/OneDrive/Desktop/university/personal/lotto-pattern-lab`.
- branch `main`, 시작 SHA **`2d01a396286ae02f52c0bcee11b880da6de4df3e`**.
- 지정 root·branch·`git status --short`, README3개 및 CSV를 먼저 확인했다. 시작 상태는 clean이며 Phase15/H13 완료 상태였다.
- Phase15 manifest21개 source/document/test hash가 일치했다.
- canonical **1–1245회 본번호만**, bonus 제외,45개 binary series·회차당6개 active를 사용했다.
- CSV SHA-256: `3b7bb1e0a37c28ae4b4a97e098180d8407008ec007698c191ed6cf279db8225b`.
- **실제1246 fetch/import/파싱·representation/parameter/model 선택·튜닝·역사 평가에 사용하지 않았다.**
- [방법·수식·support](complexity-analysis.md) · [사전 설계·실행 계획](superpowers/plans/2026-10-18-phase16.md).

Kolmogorov complexity 자체는 계산 불가능하다. 이 연구는 practical complexity/compression proxy를 비교했으며
true Kolmogorov complexity를 측정하거나 Lotto의 randomness를 증명하지 않았다.

## 표현·parameter·정확한 검색 규모

53개 deterministic 표현만 사용했다.

- 번호별45개 binary(uint8), draw-major 전체 binary stream(45Nbytes).
- block-aware packed draw(회차당6bytes, 마지막3padding bit0).
- 정렬 본번호6N uint8, adjacent gaps5N uint8.
- 기존 shape scalar sum(uint16 little-endian), range(uint8), population std와 spacing std(float64 little-endian).

실제와 각 surrogate의 representation별 raw byte 길이는 같다.
정렬·padding·binary sparsity·six-of-45 구조가 원래 만드는 압축 가능성은 valid Lotto null에도 동일하게 존재한다.

| Estimator | 고정 범위 |
|---|---|
| Shannon | binary46개 L1–5 overlapping blocks; 기타 discrete5개 symbol entropy |
| Conditional entropy reduction | binary46개 history1/2; 모든 context·future marginal support>=5 |
| Permutation Entropy | scalar4개 m3/4/5 × delay1/2/4/8, stable chronological ties, normalized by log2(m!) |
| Sample Entropy | scalar4개 m2/3 × r .15/.20/.25×population std, 공통N−m starts, self제외 Chebyshev pairs |
| Lempel–Ziv | discrete49개 LZ78 trie phrase count, c×log_q(N)/N |
| Compression | 53개 × zlib9/bz2-9/lzma-XZ preset0 |
| Rolling | W104/208/416, endpoint104간격 및 마지막1244, compact138개/window |

Sample Entropy는 A>=10,B>=20,std>0을 primary support로 요구했다.
zero-match는None/NaN, constant raw0은 degenerate/ineligible로 기록했다.
Approximate Entropy는 중복 진단과 self-match 편향·비용을 늘리지 않기 위해 생략했다.
LZ78은 새 phrase를 등록하고 root로 복귀하며 마지막 suffix가 남으면1phrase를 더 센다.
유한 표본 normalized LZ가1을 넘을 수 있고 true entropy rate와 같지는 않다.

| Primary family | 전체1–1245 후보 cell | 개발1–900 후보 cell |
|---|---:|---:|
| Shannon deficit |1675|1270|
| Conditional reduction |1532|1127|
| Permutation/Sample deficit |136|118|
| LZ78 deficit |1489|1084|
| Compression advantage |191|182|
| Chronological-order advantage |161|161|
| **합계** |**5184**|**3942**|

전체는 whole607+rolling4416+chronological161, 개발은 whole607+rolling3174+chronological161이다.
rolling32개(12/11/9)와23개(9/8/6)를 각각 전부 검색했다.
위 숫자는 독립 검정 개수가 아니며 support/calibration filtering 이전 upper bound다.

## Independent calibration와 세 종류 null

서로 다른 단위의 raw minimum을 직접 비교하지 않았다.
main null과 별개인 IID32개 pilot를 **각 scope마다** 생성하여 oriented mean/std를 고정했다(seed160001).
24/32 finite·std>1e−12인 cell만 동일한 frozen scale로 real과 모든 main null에 적용했다.
높은 z는 더 낮은 complexity 방향이며 normal-theory p-value가 아니다.
전체 calibration5170개 중 real5169개, 개발 calibration3931개 중 real3931개가 finite였다.
전체 binary L1의 고정6/45 zero variance, 희소 Sample Entropy 등이 적절히 제외됐다.

각 scope에서 **IID199 + fixed-margin199 + exact-draw-order shuffle199**,597개를 검색했다.
따라서 두 scope의 main complete search는1194회다. pilot64개는 이199회에 포함하지 않았다.
각 history에서 모든 표현·parameter·rolling 및 inner3shuffle를 재구축하고 자체 최고 cell을 골랐다.
개발 fixed-margin은 정확히 실제1..900에서 별도로 생성하여>900 margin을 쓰지 않았다.

chronological family는 order-sensitive161개에 대해
oriented chronological value−동일 draw의 inner3shuffle mean을 사용했다.
entropy/LZ/ratio는 음수, conditional reduction은 양수로 방향을 맞췄다.
이는 별도199개 outer draw-shuffle 검정을 대체하지 않는다.
outer shuffle도 자체 inner3 및 전체 검색을 수행했다.
고정된 local 번호/window만 null에 검정하는 비교는 없었다.

## 가장 강한 raw/local 구조

| Family | 선택된 실제 구조 | raw/local 값 | Calibrated global-search z |
|---|---|---:|---:|
| Shannon | 번호9, W416,417–832회,L3 | H3/3=.425265 |3.681476|
| Conditional | 번호10,W104,729–832회,h1 | reduction=.076175bits |8.289654|
| Ordinal | sum,W104,521–624회,PE m3/delay1 | normalized .971888 |2.915170|
| LZ78 | 번호9,W416,417–832회 | normalized1.087555 |3.515176|
| Compression | 번호9 whole,bz2 |165/1245bytes=.132530 |3.121195|
| Chronological | 번호5 whole,L3 | normalized entropy advantage .003384 |2.918653|

번호9 bz2는 header를 포함해1.06024bits/original binary symbol이다.
ratio가 작다는 사실만으로 hidden structure라고 주장하지 않는다.
conditional8.29라는 큰 z도 Gaussian significance가 아니며 동일한 전체 null 최대값과 비교해야 한다.
raw count/support·원래 entropy·LZ phrase·compressed bytes는 `leading_cell_diagnostics.json`과 metric CSV에 보존했다.

## 전체 역사 global-max 검정

| Family | IID global p | IID 보정 p | Fixed global p | Fixed 보정 p |
|---|---:|---:|---:|---:|
| Shannon |.730|1.00|.690|1.00|
| Conditional |.830|1.00|.840|1.00|
| Permutation/Sample |.660|1.00|.730|1.00|
| LZ78 |.805|1.00|.815|1.00|
| Compression |.325|1.00|.400|1.00|
| Chronological |.750|1.00|.800|1.00|

global p=(1+exceed)/(199+1), 해상도 .005, 여섯family Bonferroni=min(1,6p)다.
각 null/scope별 보정이며 모든 history·metric이 독립이라는 뜻은 아니다.
**실제가 IID나 fixed-margin보다 측정 가능하게 덜 복잡하거나 더 압축된다는 근거는 없었다.**
finite mixing·32pilot scale·유한 표본 support의 한계는 남는다.

## Chronological ordering vs 같은 draw의 무작위 순서

| Family | Outer draw-shuffle global p | 6-family 보정 p |
|---|---:|---:|
| Shannon |.760|1.00|
| Conditional |.815|1.00|
| Permutation/Sample |.685|1.00|
| LZ78 |.865|1.00|
| Compression |.380|1.00|
| Chronological paired advantage |.765|1.00|

동일 draw를199번 다른 순서로 재배치했을 때도 실제 순서가 특별히 낮은 complexity를 보이지 않았다.
선택된 번호5 L3 entropy의 inner3 대비 작은 advantage .003384도 global 보정을 통과하지 못했다.
whole·rolling·parameter·번호 선택을 모두 다시 허용한 결과다.
per-number L1 entropy처럼 순서와 무관한 marginal 지표는 shuffle에서 불변임을 구분했다.
per-number L1 entropy는 빈도의 함수이며 자체로 시간 정보를 보이는 지표가 아니다.

## Rolling low-complexity와 causal regime

whole+rolling을 포함한 전체 family의 IID/fixed/shuffle 보정 p는 모두1이었다.
따라서 local low-complexity window가 random보다 unusual하다는 근거는 없었다.
번호9의417–832회 L3 entropy/LZ가 낮게 보이고 번호10의729–832회 conditional reduction이 커 보였지만,
동일하게 검색한 null도 더 큰 apparent deficit을 빈번하게 찾았다.
예를 들어 번호10의h1 jointcounts는[[61,21],[21,0]], source support82/21, sample103개였다.
원시 next entropy .729627에서 conditional .653453으로 줄어도 full global p=.83/.84/.815였다.

regime용 metric 선택은 **개발1–900에서만** 했다.
선택은 번호36, W208, h1 conditional-entropy reduction, discovery endpoint832(625–832회), z=8.924237이었다.
그 뒤 매 endpoint의 prefix에서 계산하고 이전104개 이상 완료 metric의1/3·2/3 quantile로 분류했다.
현재·미래 metric을 threshold fit에 넣지 않았다. higher oriented value는LOW complexity다.

| 구간 | 상태 | 표본 | 실제 next overlap | Own-frequency 기대 | 차이 |
|---|---|---:|---:|---:|---:|
| 개발 전체 diagnostic |HIGH|128|.7656|.8111|−.0455|
| 개발 전체 diagnostic |NORMAL|116|.9310|.8093|+.1217|
| 개발 전체 diagnostic |LOW|344|.8488|.8086|+.0402|
| 이후901–1245 |HIGH|62|.7903|.8024|−.0121|
| 이후901–1245 |NORMAL|188|.7766|.8047|−.0281|
| 이후901–1245 |LOW|95|.7368|.8026|−.0657|

개발 diagnostic은target209–900이며 초기104개 metric은UNKNOWN이라 위 상태 표에서 제외했다.
모델 gate는 그중 **target501–900만** 사용했다.
LOW 구간은target660–937의278회,545–611의67회 등으로 이어졌다.
이 run length는 중첩 W208 metric과 적응 quantile의 descriptive 결과다.
그 길이를 별도로 null-calibrated한 검정으로 주장하지 않는다.
rolling global search 자체는 같은32window/parameter 공간으로 모든 null에 적용했다.
W208 안의 관측들이 크게 겹치므로 daily state/outcome을 독립 표본으로 p-test하지 않았다.

## 개발 gate·모델·예측 평가 결정

개발 전용 전체 검색에서도 corrected structure가 없었다.

| 개발 family | IID 보정 p | Fixed 보정 p | Shuffle 보정 p |
|---|---:|---:|---:|
| Shannon |1.00|1.00|1.00|
| Conditional |1.00|1.00|1.00|
| Ordinal |1.00|1.00|1.00|
| LZ78 |.75|.84|.93|
| Compression |1.00|1.00|1.00|
| Chronological |1.00|1.00|1.00|

개발 gate의 LOW support는311개로 최소30을 넘었지만,
LOW의 overlap−own-frequency 기대는 양 개발절반501–700/701–900에서+.049707/+.065822였다.
첫 절반이 사전>.05 조건을 통과하지 못했고, 더 본질적으로 **corrected development temporal structure 조건이 실패**했다.
이후 결과를 보고 cutoff나 gate를 바꾸지 않았다.

고정한 descriptive 설정/결정 SHA-256:
**`376dc33f17b91b24b9617e7ad4422cbab5bd8c6d4789037a0c26f37ceca5182a`**.

- **ComplexityStateModel: 정당화되지 않아 구현하지 않았다.**
- **CompressionAnalogModel: DEFERRED.** causal continuation과 추가 encoding/ticket 선택의 검증 없이 단순 compressor로 만들 수 없다.
  C(45,6) brute force도 하지 않았다.
- **Predictive walk-forward·Top6/Recall/pool·paired bootstrap vs Random/Gap: 생략.** 방어 가능한 모델이 없어 성능을 만들어내지 않았다.
- **Gap/Graph/GapShape rank correlation: 해당 없음.** 새로운 ranking predictor가 없으므로 상관을 계산하지 않았다.
  기존 Graph/GapShape를 refit/reselect하지 않았고 저장 예측 hash를 보존했다.
- **ENSEMBLE CANDIDATE: 아님 — NOT CURRENTLY JUSTIFIED.** proxy의 낮은 entropy만으로 component를 만들지 않았다.

위 regime table은 descriptive outcome 진단이며 모델의 out-of-sample 성능 표가 아니다.
이후901–1245에서도 LOW의 overlap 차이는 음수였지만 이를 별도의 tuned predictive model 결과라고 부르지 않는다.
H14의 meaningful corrected structure와 predictive promise를 모두 주장하지 않는다.

## 실행·그림·테스트·감사

2+2+2 benchmark의 전체·개발 scope 포함 순차597회 예상은1520.79초였다.
실제 workers4의597회×두 scope main검색은 **736.60초**였다.
결과를 본 뒤 null 횟수나 parameter/rolling 검색을 축소하지 않았다.
새 package나 network draw-data 수집 없이 기존 local dependencies와 Python stdlib compressor를 사용했다.

`reports/complexity/plots/`에10개 PNG를 저장했다.

```text
per_number_shannon.png
real_vs_surrogate_entropy.png
lz_complexity_comparison.png
compression_ratio_comparison.png
chronological_vs_shuffled.png
rolling_complexity.png
strongest_low_complexity_region.png
global_max_statistics.png
permutation_sample_entropy.png
descriptive_regimes.png
```

마지막 그림은 **descriptive regime**이며 predictive regime plot이 아니다. 그림 자체는 evidence가 아니다.
두 scope의64pilot/raw vector/mask/hash, 실제 cell measurement/support,
1194개 main complete-search raw vector와 maxima, frozen encoding inventory,
regime·gate·선택·leading count diagnostics를 저장했다.
정확한 로컬 artifact40개(manifest자체 제외)의 목록·크기·SHA-256과 변경source18개의 hash는
[run manifest](../reports/complexity/run_manifest.json)에 기록했다.

전체 `python -m pytest -q -rs`: **625 passed,1 skipped**,262.32초.
skip은 기존 `tests/test_predictive_models.py:52`의 optional LightGBM/XGBoost 미설치다.
새 Phase16 테스트80개는 Shannon/block/conditional known cases, PE ties/periodic/random,
Sample Entropy common starts·self제외·support/zero-match,
LZ78 synthetic ordering·정확한 phrase, serialization·세 compressor reproducibility,
real/null 동일 길이·row shuffle 보존/시간파괴, rolling causal threshold,
independent calibration/global maxima·병렬 determinism, hash inner-shuffle,
정확한 개발 fixed-margin prefix900, 미래suffix 거부·1246/없는archive publication gate를 검증했다.

독립 리뷰는 estimator·encoding·calibration 통계/파일hash·space·causal regime를 확인했다.
critical/important defect는 없었고, 제안된 두 경계 회귀 테스트를 추가해 통과했다.
실제 개발 gate 실패를 확인하여 conditional predictor 구현이 미완료로 남는 경우도 없었다.

## Prospective·정확한 변경 파일·종료

**PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**.

H14의 `draw1247_phase16_complexity` capability 상태는 **NOT_CREATED_NO_JUSTIFIED_MODEL**이다.
모델이 정당화되지 않아 의미 없는 Phase16 freeze/publication CLI나 파일을 만들지 않았다.
이는 전체 연구의 archive 복원 대기 상태와 구분한다. archive가 복원돼도 unsupported H14 모델을 자동 발행하지 않는다.
기존 공용 target1246/archive 차단 회귀 테스트를 확인했고 H14 CLI에는 publication action 자체가 없다.
**어떤 prospective snapshot도 발행하지 않았다.** 부재한 옛 archive·예측·hash를 재구성하지 않았다.

기존 수정5개:

```text
.gitignore
README.md
docs/README.md
docs/research-ideas.md
src/cli.py
```

새 파일13개:

```text
docs/complexity-analysis.md
docs/phase16-results.md
docs/superpowers/plans/2026-10-18-phase16.md
src/analysis/complexity_encoding.py
src/analysis/complexity_plots.py
src/analysis/complexity_regimes.py
src/analysis/complexity_search.py
src/analysis/entropy_complexity.py
src/complexity_cli.py
tests/test_complexity_encoding.py
tests/test_complexity_pipeline.py
tests/test_complexity_search.py
tests/test_entropy_complexity.py
```

ignore된 로컬 보고서·그림·검증 script도 manifest에서 모두 열거한다.
원본CSV·이전Phase 전용source·frozen Graph/GapShape 출력·HEAD 불변과 `git diff --check`를 확인했다.
**draw1246 미사용, prospective publication 없음, commit/push 없음**이다.
Phase16에서 종료하며 Tensor decomposition, Symmetry/Reflection, Final Ensemble은 구현하지 않았다.
