# Phase16 H14 — Entropy / Compression / Algorithmic Randomness 방법

질문은 실제 Lotto가 동일한 제약과 길이의 random history보다 낮은 complexity 또는 더 큰 compressibility를 보이는가이다.
별도로 같은 draw의 순서만 섞었을 때 chronological ordering의 추가 구조가 사라지는지도 묻는다.
**Kolmogorov complexity 자체는 계산 불가능하다.** 아래 통계와 compressor는 encoding·표본 길이에 따르는 실용적 proxy이며
true Kolmogorov complexity를 측정하거나 randomness를 증명하는 도구가 아니다.
[사전 설계·실행 계획](superpowers/plans/2026-10-18-phase16.md)에 전체 범위를 기록했다.

## 데이터와 사전 표현

본번호1–1245회, bonus제외, 매 row45bit 중6개 active만 사용한다.
strict reader는 canonical header+1245행 이후 unknown suffix를 파싱 전에 거부한다.
cutoff는 실제 입력 prefix 길이와 정확히 같아야 한다.1246 fetch/import/design/tuning/evaluation은 없다.

53개 표현의 serialization을 고정했다. alternative encoding을 성능으로 고르지 않는다.

| 표현 | 개수 | symbol/bytes |
|---|---:|---|
| 번호별 binary |45|uint8 0/1, N bytes|
| 전체 binary stream |1|draw-major, 각 draw에서1..45 순,45N bytes|
| block-aware packed draw |1|np.packbits big bitorder, draw당6bytes; 마지막3padding bit는0|
| 정렬 본번호 sequence |1|uint8, draw당6symbols|
| adjacent-gap sequence |1|uint8, draw당5symbols|
| sum |1|little-endian uint16, draw당1symbol/2bytes|
| range |1|uint8, draw당1byte|
| population std |1|little-endian float64, draw당8bytes|
| spacing population std |1|little-endian float64, draw당8bytes|

packed block의6byte 경계와 full_binary의45symbol 경계를 metadata에 보존한다.
정렬·gap·six-of-45·padding이 만드는 내재적 압축 가능성은 동일한 encoding을 거친 valid Lotto null과 비교한다.
float64 encoding의 byte 패턴을 순수한 시간 정보처럼 해석하지 않는다.

## Shannon·conditional entropy

binary46개에 overlapping block length **L={1,2,3,4,5}**, 총230개를 사용한다.
plugin Shannon entropy H_L(bits/block), H_L/L(per-symbol 및 binary normalized),
sample수·occupied block·원시 counts를 노출한다. samples>=10×2^L만 primary에 사용한다.
binary1의 IID reference는 H(6/45)다. 각 번호의 경험 빈도가 달라질 수 있다.

packed byte·sorted number·gap·sum·range5개에는 단일-symbol entropy를 사용한다.
고정 alphabet 최대는256/45/44/235/40, normalized H/log2(q)다.
최소 samples>=max(10,q)를 요구한다. 이론적 최대가 실제 제약 아래 달성 가능하다고 가정하지 않는다.

binary46개의 history **h={1,2}**에 대해 같은 aligned future 표본에서 Hfuture와 Hfuture|context를 계산한다.
reduction=Hfuture−Hfuture|context가 주 지표다. 원시92개 contingency table의
모든2^h context와 future0/1 각 marginal에 최소5개 support를 요구한다.
sparse라도 raw entropy는 보고하며 primary oriented value는NaN으로 제외한다.
finite-sample plugin bias와 overlapping block 의존성은 동일 estimator·길이의 complete-history null로 보정한다.
원시 reduction>0을 미래 정보의 증명으로 취급하지 않는다.

## Permutation Entropy·Sample Entropy

sum/range/std/spacing_std의 scalar4개에만 적용한다. binary ordinal pattern을 별도 검색하지 않는다.

- Permutation Entropy: **m={3,4,5}, delay={1,2,4,8}**, 총48개.
  동점은 stable argsort의 원래 시간 index 순서로 해소하고 tie_fraction을 보고한다.
  entropy/log2(m!), 최소5×m! embeddings를 요구한다.
- Sample Entropy: **m={2,3}, r={.15,.20,.25}×population std**, 총24개.
  m과m+1 모두 공통 N−m starting templates를 사용한다. Chebyshev거리<=r,
  distinct unordered pair만 세며 self match는 없다. B=m matches,A=m+1 matches,
  값은−ln(A/B) nats다. SciPy cKDTree를 사용한다.
  A>=10,B>=20,std>0에서만 primary로 사용한다. zero-match는None/NaN이며 infinity를 근거로 삼지 않는다.
  constant series는 raw0이지만 degenerate·ineligible로 명시한다.

Approximate Entropy는 중복·self-match 편향과 비용을 늘리지 않기 위해 이번 secondary에서도 생략했다.
이 선택은 real 결과를 보기 전에 고정했다.

## Lempel–Ziv와 compressor

**LZ78**의 transparent dictionary/trie parsing을 사용한다.
root부터 symbol을 읽다가 처음 보지 못한 phrase를 등록하면 count를1 올리고 root로 돌아간다.
끝에 미완료 suffix가 남으면1phrase를 더 센다. expected O(N)이다.
고정 alphabet q에 대해 **c×log_q(N)/N**으로 길이를 정규화한다.
number45/full_binary/packed/sorted/gap의49개 discrete 표현을 평가한다.
constant·periodic·IID synthetic에서 순서와 수치 동작을 검증했다.
유한 표본 normalized 값은1보다 클 수도 있고 entropy rate 또는 Kolmogorov complexity와 같지 않다.

53개 표현 모두에 **zlib level9, bz2 level9, lzma FORMAT_XZ preset0**를 적용한다.
총159개 cell이며 preset·encoding을 추가로 최적화하지 않는다.
raw/compressed bytes, compressed/raw ratio, bits per original symbol을 기록한다.
header/frame overhead가 포함되므로 짧은 stream의 absolute ratio를 단독 해석하지 않는다.
같은 representation·길이·serializer·compressor에 대한 real/null만 비교한다.

## Rolling과 chronological-order family

rolling **W={104,208,416}**, 끝점은 각W부터104회 간격 및 마지막 N−1이다.
1–1245에서 각각12/11/9개, 총32개 window다. 다음 draw label은 최대1245다.
window마다 compact138개만 계산한다:
번호45개 L3 entropy, h1 reduction, LZ78; packed zlib; sum PE(m3,tau1), sum SampEn(m2,r.2).
rolling 선택도 whole-history와 같은 primary family의 global maximum에 포함한다.

별도 chronological-order family는 whole-history의 order-sensitive161개를 사용한다.
binary46 L3 entropy,46 h2 reduction,49 LZ78,global4representation×3compressor12,
scalar4 PE(m3,tau1),scalar4 SampEn(m2,r.2)다.
각 history의 exact draw를3번 섞고 이 subset을 다시 계산한다.
entropy/ordinal/LZ/ratio는 음수, conditional reduction은 양수로 방향을 맞춘 뒤
**chronological oriented value−3shuffle oriented mean**을 원시 order advantage로 정의한다.
reference3개 모두 support를 통과해야 한다. seed는 binary history hash로부터 결정하므로 모든 history에 같은 규칙을 적용한다.

이 inner3개는 값의 paired reference이며 별도의199개 outer draw-shuffle 검정을 대체하지 않는다.
outer shuffle은 정확한 draw contents·marginals·within-draw relations를 유지하고 순서만 파괴한다.
outer history도 다시 자신의 inner3개 및 전체 검색을 수행한다.

## 정확한 primary 공간과 independent calibration

| Family | Whole/rolling 포함1–1245 cell수 |
|---|---:|
| Shannon deficit |1675|
| Conditional reduction |1532|
| Permutation/Sample Entropy deficit |136|
| LZ78 deficit |1489|
| Compression advantage |191|
| Paired chronological-order advantage |161|
| **합계** |**5184**|

whole607 + rolling4416 + chronological161이다. 개발1–900은 동일 규칙의23개 rolling window로 **3942개**다.
이 개수는 독립 검정 개수가 아니며 sparse/support filtering 이전 값이다.

서로 다른 지표의 단위를 그대로 비교하지 않는다.
real과 main null에 포함되지 않는 **독립 IID32개 pilot**를 scope별로 생성한다(seed160001).
cell별 oriented 평균·sample std를 고정하고 z=(oriented−pilotmean)/pilotstd로 변환한다.
최소24/32 finite 및std>1e−12만 calibrated search에 사용한다.
동일한 frozen scale/mask를 real과 모든 main null에 적용한다. 이 z를 normal-theory p-value로 해석하지 않는다.
32개 scale의 추정 불확실성과 sparse filter도 동일 null global-max에 반영된다.
pilot values·counts·mask·hash를 보존한다.

## 세 null과 full/development 분리

seed160042, **IID199 + fixed-margin199 + exact-draw shuffle199**를 완주한다.
각 history에서 모든53표현·parameter·rolling·inner3shuffle를 재계산하고 자신의 strongest cell을 고른다.
원래 선택된 번호/window/compressor를 null에 고정하지 않는다.
global empirical p=(1+exceed)/(199+1), 여섯family Bonferroni=min(1,6p)다.
각 null에 대한18개 family 결과를 숨기지 않고 모두 보고한다.

full1–1245와 development1–900을 별도 calibration·검색으로 수행한다.
특히 fixed-margin 개발 null은 **실제 x[:900]에서 별도로 생성**하며
1245전체 margin을 보존한 history의 prefix를 개발 null로 쓰지 않는다.
이로써 representation/metric/model 채택 선택에>900의 빈도가 들어오지 않는다.
기존 Curveball20rowtrades의 유한 mixing 한계는 남는다.
outer shuffle199개의 조건부 검정은 chronological ordering 자체의 추가 정보를 묻는다.

## Regime·predictor 채택

strongest rolling metric은 development calibrated z에서만 고른다.
선택W와 metric·parameter를 고정한 뒤 매 draw endpoint의 완료된 prefix로 계산한다.
현재 값을 제외한 이전 최소104개 finite metric의1/3,2/3 quantile로
LOW/NORMAL/HIGH complexity를 정한다(같은 quantile이면NORMAL).
higher oriented value가LOW complexity다.
다음 draw의 최근6개와 overlap, own training-frequency expected overlap, next sum/range를 descriptive로 기록한다.
전 기간 결과로 threshold를 미리 학습하지 않는다.

ComplexityStateModel은 다음 development-only gate를 모두 통과할 때만 구현한다.

1. temporal-capable family에서 IID/fixed의 보정 p<=.05를 함께 충족하거나,
   chronological family의 draw-shuffle 보정 p<=.05.
2. 개발 target501–900의 LOW finite 결과>=30개.
3. 양 개발절반501–700/701–900에서 LOW의 overlap−own-frequency expectation 평균이 각각>.05.

실패하면 모델을 만들지 않고 later predictive evaluation·ensemble correlation·prospective capability를 생략한다.
이 경우 Random/Gap 예측 비교를 만들어내지 않으며 descriptive regime outcome을 예측 성능처럼 제시하지 않는다.
CompressionAnalogModel은 causal continuation의 추가 정의·encoding 선택 없이 정당화할 수 없어 사전 범위에서 DEFERRED다.
C(45,6) brute force는 하지 않는다.

## 실행과 prospective

```powershell
python main.py complexity calibrate
python main.py complexity benchmark
python main.py complexity analyze --surrogates 199 --workers 4
python main.py complexity regimes
python main.py complexity plots
python -m pytest -q -rs
```

새 network/package 설치는 없다. 기존 local dependencies를 사용하고 BLAS/MKL/OMP thread는1이다.
모델이 정당화되지 않으면 `draw1247_phase16_complexity`용 의미 없는 publication infrastructure를 만들지 않는다.
어떤 경우에도 archive 복원·검증 전 실제 snapshot publication은 금지다.
상태는 **PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**이며1246을 가져오지 않는다.
