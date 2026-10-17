# Phase15 H13 — Modular / Difference-Space 방법

절대 번호 대신 residue·absolute distance·normalized spacing으로 표현했을 때
반복 가능한 구조와 다음 회차 정보가 있는지 각각 검증한다.
[사전 계획](superpowers/plans/2026-10-18-phase15.md)에 검색·모델·선택 규칙을 고정했다.
새 표현이 자체적으로 정보를 추가하거나 random Lotto를 예측 가능하게 만든다고 가정하지 않는다.

## 범위와 causal timing

canonical 본번호1–1245회만 사용한다. bonus제외,45열 binary matrix의 각 row6개다.
strict reader는 header+1245행 뒤 unknown suffix를 파싱 전에 거부한다.
cutoff는 제공된 prefix 길이와 정확히 같아야 한다. 미래가 포함된 배열을 조용히 slice하지 않는다.
모델 target T의 입력은 정확히1..T−1이며 T<=1245다.
1246 fetch/import 및 설계·선택·튜닝·평가에 사용하는 경로가 없다.

## Modular representation

modulus **k={2,3,4,5,6,7}**, lag **{1,2,3,4,8,13,26}**를 사용한다.
residue는 n%k, 열은0..k−1이다. mod2는 parity reference로 함께 계산한다.
H[t,r]는 draw별 residue histogram이며 합6이다.
occupied classes, HHI=sum(H/6)², entropy=−sum(H/6)log2(H/6),
repeats=6−occupied, repeatedclasses=count(H>=2), finite-population imbalance를 노출한다.
이 entropy는 H13 표현 요약이며 H14 entropy/compression 연구는 하지 않는다.

1..45에서 residue class 크기 c_r는 균등하지 않을 수 있다.
p_r=c_r/45, IID 기대histogram=6p,
covariance=6×39/44×[diag(p)−ppᵀ]로 without-replacement 제약을 반영한다.

주 family1은 residue별 전체 기간 총량의 |z| 최대다.
z_r=(sum_t H[t,r]−N6p_r)/sqrt(N×cov_rr), 총27개 residue cell이다.
이는 정적 marginal 진단으로, fixed-margin에서는 각 번호 총량이 고정되어 residue 총량도 고정된다.
fixed-margin에서 새 시간 구조를 검증하는 통계로 해석하지 않는다.

주 family2는 k×lag×세 feature의126개 absolute correlation 최대다.
feature는 histogram(각 residue열을 segment별 중심화한 뒤 pooled Pearson), HHI, entropy다.
histogram[:-lag]와histogram[lag:]를 정렬하며 temporal wrap은 없다.

## Modular successor와 모델

각 k/lag/r에서 source histogram count a∈{0..6}에 따른 future의 **같은 residue** count를 비교한다.
cross-residue pattern grammar는 추가하지 않는다.
C[r,a]=source state 표본수, S[r,a]=그 표본의 futurecount 합,
conditional mean=S/C, baseline=전체 aligned future 평균, v=그 population variance다.
주 family3의 점수는
|conditional−baseline|/sqrt[v×(1/C−1/M)]이다.
support>=20, C<M, v>0만 허용한다. 최대 가능한1323개 cell 중 실제 eligible 수를 별도로 기록한다.
공유 표본 baseline의 분모 보정을 포함하되 이 z의 normal-theory p-value는 사용하지 않는다.
희소한/부재한 state는 mask와NaN으로 원시 table에 남긴다.

**ModularResidueModel**은 single k/lag42개 후보 중 개발에서 선택한다.
현재 source draw T−lag의 각 residue count state를 읽고,
conditional expected futurecount=(S+50×baseline)/(C+50)으로 shrink한다.
support20미만이면 baseline이다. number score는 그 residue의 expectedcount/c_r다.
modulus 여러 개를 broad subset 검색하거나 임의 weight로 합치지 않는다.
독립 conditional estimates의 합이 반드시6인 것은 아니므로 calibrated probability라고 주장하지 않는다.
같은 residue의 번호는 동점이며 Top6 tie는 작은 번호 우선으로 고정한다.

## Difference·spacing 표현과 기대값

정렬한 x1<...<x6에서 adjacent gaps5개, pairwise absolute differences15개,
anchored shape=[0,x2−x1,...,x6−x1], normalized gaps=gaps/(x6−x1)를 계산한다.
번호축은1..45의 유한 축이며 cyclic wrap은 없다.
spacing entropy는 normalized gaps의 Shannon 요약이다.

within-draw distance d=1..44에는45−d개의 가능한 unordered pair가 있다.
draw당 paircount 기대=(45−d)/66,
adjacent-gap count 기대=5×C(45−d,5)/C(45,6)이며 합은 각각15와5다.
따라서 raw 작은 distance 빈도가 높은 것을 구조로 해석하지 않는다.

## Temporal absolute-distance relation

source=X[:-lag], future=X[lag:]의 crosscount matrix에서 |i−j|=d를 합한다.
source draw마다 candidate m에 대해 a_m=#source numbers atdistance d를 계산한다.
opportunity=sum_{draw,m}a_m, IID mean=(6/45)×opportunity다.
future6개 without replacement에 대한 row별 conditional variance는
6×39/44×[mean_m(a_m²)−mean_m(a_m)²]이며 이를 row에 걸쳐 합한다.
주 family4는 lag7×distance44=308개 |(observed−expected)/sqrt(variance)| 최대다.
d0는 self-number reference로 저장하지만 primary 선택에서 제외한다.
source/future가 여러 lag에서 겹치므로 이 conditional normalization을 독립 p-test로 해석하지 않는다.
complete Lotto-history null이 실제 의존성과 번호 빈도를 보정한다.

**DifferenceRelationModel**은 lag7×observed support{20,40}=14개 후보다.
rate_d=(observed_d+100×6/45)/(opportunity_d+100), weight_d=rate_d/(6/45)−1이다.
support미달 및d0의 weight는0이다. 학습은 모든 training distance에서 수행하며 특정 distance를 hardcode하지 않는다.
현재 T−lag source6개에 대한 candidate m의 mean weight에서
(1/45)sum_{n=1..45}weight_|m−n|을 빼서 finite-axis source expectation을 제거한다.
이 경계 보정은 미래 번호를 쓰지 않는다. 각 source·distance·weight·boundaryterm을 진단에 저장한다.

## Gap-shape 진단과 optional 모델

normalized gap5의 Euclidean distance만 사용한다. exact match만 찾지 않는다.
주 family5는 일곱 lag의 |pooled centered gap correlation|×sqrt(N−lag)와
K={10,25}의 causal neighbor successor MSEgain paired-t 중 최대, 총9개다.
서로 다른 점수의 최대도 동일하게 검색한 null maximum으로 보정하며 raw paired-t를 p-value로 쓰지 않는다.

neighbor query끝점104,130,...,1222,1244의45개다. query index q=end−1에서 과거 후보j<=q−26,
후보 successor j+1<q만 허용한다. 현재/가까운 query와 그 successor를 학습 neighbor로 넣지 않는다.
query의 다음 normalized shape를 nearestK의 successor 평균으로 예측하고
동일한 eligible 과거 successor 전체 평균과 MSE를 비교한다.
nearest/all 거리와 실제 successor를 노출하나 Phase11 recurrence framework를 재구현하지 않는다.

**GapShapeModel** 개발 후보는 K10/25×Gaussian sigma1/2의4개다.
과거 유사 shape의 실제 successor sorted positions마다1..45 안에서 normalize한 Gaussian을 놓고 평균한다.
개발 평균>.8 및Frequency26 초과, 양 개발절반 평균>.8을 모두 만족할 때만 이후 평가에 포함한다.
실패하면 development/descriptive 단계에 남긴다.

## Global null·개발 선택·평가

다섯 family의 사전 후보 합계는 **1793=27+126+1323+308+9**다.
지원 조건 이전 upper bound이며 독립 검정 개수가 아니다.
IID199개·fixed-margin199개에서 표현·모든 modulus·lag·distance·state support·shape neighbor를 다시 구축한다.
각 history가 자체 최고 후보를 고른다. real leader를 null에 고정하지 않는다.
기존 Curveball20rowtrades는 row6개/전체 번호 총량을 보존하며 유한 mixing 한계는 남는다.
seed150042, globalp=(1+exceed)/(199+1), 다섯family Bonferroni=min(1,5p)다.

개발 target401–900, 이후901–1245다. 이전 연구에서도 쓴 역사이므로 pristine holdout은 아니다.
main56개+shape4개=60개 후보를 development 평균Top6, tie선언순서로 고른다.
exact1..900 matrix hash·모든 선택·version을 JSON/hash로 동결한다.
ModularDifferenceConsensus는 두 main이각각>.8및Frequency26을 넘고,
equal-rank 조합이 두 parent보다 개발전체와 양절반에서 모두 엄격히 좋은 경우에만 허용한다.
최종 H17 ensemble과 arbitrary weight 최적화는 없다.

모든 target에서 실제 prefix<T로 모델의 transition/distance/shape/normalization을 다시 계산한다.
cache key는 prefix bytes·shape·고정 parameter다.
Gap cadence26/13과 별개로 actual transformed cutoff=T−1을 기록하며 outer fit anchor를 따로 보존한다.
Random/Frequency26/Gap/main/허용optional의 Top6·hit0..6·Recall6/10/15·winning rank·pool>=5·all-six를 저장한다.
paired circular bootstrap2000회, block26/13 및52 sensitivity, Random/Gap 두 reference를 사용한다.
start901/1001/1101과 세 era를 같은 예측열로 비교한다. later sensitivity는 재선택에 쓰지 않는다.
Gap과 frozen Phase14Graph CSV의 번호 좌표 Spearman/Top6/10/15 overlap을 계산하며 Graph를 refit하지 않는다.

## Prospective와 실행

`draw1247_phase15_transformedspace`는 frozen설정·원본archive검증 준비 gate다.
archive 부재 시 **PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**으로 거부한다.
1246target은 금지이며 import/refit/실제 snapshot publication은 수행하지 않는다.

```powershell
python main.py transformed-space benchmark
python main.py transformed-space analyze --surrogates 199 --workers 4
python main.py transformed-space select
python main.py transformed-space compare --cadence 26
python main.py transformed-space compare --cadence 13
python main.py transformed-space sensitivity
python main.py transformed-space plots
python main.py transformed-space prepare-freeze
```

기존`.deps/docs-checks`를 PYTHONPATH에 사용하고 BLAS/MKL/OMP thread를1로 제한했다.
새 패키지 설치나 draw data network 수집은 하지 않았다.
