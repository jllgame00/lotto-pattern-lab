# Phase 14 — H12 Dynamic Graph / Hypergraph 방법

질문은 “개별 번호보다 번호 사이의 관계망에 반복 가능하고 예측에 유용한 구조가 있는가?”이다.
pair graph와 six-number hyperedge를 분리한다. raw co-occurrence·빈도·관계 정보를 구분하며,
그림·큰 lift·선택된 community만으로 구조나 예측 근거를 선언하지 않는다.
[사전 실행 계획](superpowers/plans/2026-10-18-phase14.md)에 범위와 선택 규칙을 기록했다.

## 데이터·cutoff

canonical 본번호1–1245회 binary matrix45개, 각 row6개만 사용한다. bonus 제외.
strict reader는 header+1245행까지만 읽고 unknown byte suffix를 파싱 전에 거부한다.
supplied cutoff는 입력 prefix 길이와 정확히 같아야 하며, 미래 row를 조용히 slice하지 않는다.
1246 fetch/import 또는 해당 결과를 이용하는 경로가 없다.

primary 구조 분석은 고정45개 끝점 **104,130,...,1222,1244**와W=**26,52,104**를 교차한다.
135개 graph/hypergraph다. 이는 계산량을 제한하는 사전 staging이며 모든 실제/null에 동일하다.
W26/52 초기 구간을 추가로 검색하거나 결과에 맞춰 끝점을 옮기지 않는다.
최초 공통 끝점은 최대 window104가 완전해지는 시점이다.
successor는 endpoint+1, 마지막1245까지다. 끝점1245에서1246을 label로 쓰지 않는다.
cumulative1–1245 및 마지막 descriptive window는 reference이며 primary 검색과 구분한다.
모델은 이 구조 분석 grid와 달리 매 target의 training prefix에서 다시 계산한다.

## Graph와 정확한 기대값

A_ij는window에서 i,j가 함께 출현한 횟수, A_ii=0이다.
여섯 본번호 한 draw는정확히C(6,2)=15개의 unordered pair를 만든다.
따라서 upper adjacency sum=15W, node strength=sum_j A_ij=**5×own count**다.
weighted degree/strength를 새로운 frequency-independent signal로 해석하지 않는다.

IID에서 individual pair probability=C(6,2)/C(45,2)=**1/66**,
expected edge count=W/66, expected node strength=**2W/3**다.
upper edge share HHI=sum A_ij²/(15W)²의 기대값은
**1/990+(1−1/66)/(15W)**다. 이는 squared count의 기대값 합으로 직접 계산하며 edge 독립을 가정하지 않는다.
edge primary score=(count−W/66)/sqrt[W(1/66)(1−1/66)]다.
이 z는 global 탐색 통계이지 local normal-theory p-value가 아니다.

B_ij=1[A_ij>=**2**], diag0의 threshold를 사전 고정했다.
degree, density, common-neighbor B², local clustering,
triangle=tr(B³)/6, wedge=sum_i C(degree_i,2), transitivity=3triangle/wedge를 노출한다.
degree<2의 local clustering은0이며 평균은45개 node 전체다.
단일 draw가clique6와triangle20개를 만드는 제약은 arbitrary independent-edge graph null로 보정할 수 없다.
실제 Lotto history를 생성하는 두 null을 사용한다.

## 순수 관계 feature와 빈도 control

window count f에 대해 finite-universe marginal expectation을
E_ij=(45/44)(5/6) f_i f_j/W로 두고 diag0, R=A−E로 정의한다.
이는 IID 동일 marginal에서 pair expectation과 맞는 단순 reference이며 fixed-margin conditional expectation의 정확한 해라고 주장하지 않는다.

compact 관계 feature는 다음 세 가지다.

- **neighbor:** 직전 draw의 다른 active node에 대한 R_ij/sqrt[(f_i+5)(f_j+5)] 평균. self 제외.
- **community:** 자신의 community 내부 residual edge합/(5f_i+5).
- **clustering:** threshold2의 local clustering.

각 feature를 같은 training window의45개 node에서 intercept+own count에OLS 회귀한 잔차로 바꾸고
population std로 표준화한다. 잔차 variance가 사실상0이면0을 반환한다.
따라서 strength의 회귀잔차는 정확히0이다.
이 절차는 **선형** frequency 성분을 제거하며 frequency와 완전히 독립적인 정보가 되었다는 뜻은 아니다.
이후 matched-window frequency control과 valid-history null 검정을 추가한다.

## Community와 graph dynamics

한 종류의 normalized **weighted spectral clustering**, K=**2,3**만 사용한다.
D^−1/2 A D^−1/2의 leading eigenvectors를 row-normalize하고
deterministic farthest-point initialization 및 kmeans로 분할한다.
community label은 최소 번호 순으로 canonicalize하며 isolate는−1이다.
binary threshold는 clustering/motif에만 사용하고 spectral partition은 weighted A를 쓴다.

community stability는 공통 nonisolate>=20인 두 partition의 **adjusted Rand index**다.
primary 비교는 같은W에서 **끝점 차이>=W**인 non-overlap window pair만 허용한다.
raw cosine/correlation/Frobenius/threshold-Jaccard와 adjacent partition ARI도 descriptive로 노출한다.
큰W의 adjacent window는 자료 대부분을 공유하므로 높은 유사성을 독립적 지속성으로 해석하지 않는다.

primary graph-state persistence는 R의990개 upper edge vector cosine이다.
같은W의 모든 허용 non-overlap pair 중 최대를 고른다.
community count·두 window·graph state 선택은 null에도 동일하게 허용한다.

## Hypergraph와 고차 subset

각 draw를 정렬한 unordered six-number hyperedge로 보존한다.
pair990개, tripleC(45,3)=**14,190개**의 고정 ID를 부여한다.
한 draw에는pair15개와triple20개가 있고 전체triple node participation은 **10×own count**다.
모든 triple 참여량 합을 새로운 signal로 사용하지 않는다.

subset size q의 IID probability=C(6,q)/C(45,q), expected=W×probability다.
count/lift/support, normalized binomial z, actual occurrence draw와 recurrence interval,
최근 window와 겹치지 않는 prior history의 rate/trend를 노출한다.
주 검정은 **triple count>=3**의 최고 normalized count다.
quadruple은 W104에서도 expected=104×15/148995≈0.01047로 매우 희소하므로 이번 범위에서 제외한다.
support 조건을 통과한 큰 lift도 전체 null 최대값 비교가 필요하다.

hypergraph continuation은 직전 draw의15개 pair 중 candidate 자신이 포함되지 않은 pair를 문맥으로 쓴다.
pair와 triple count가 support2 또는3 이상인 문맥에서
conditional P(j|ab)=(count_abj+alpha×ownrate_j)/(count_ab+alpha),
weight=count_ab/(count_ab+alpha)로 두고 weight×(conditional−ownrate)의 평균을 구한다.
문맥이 없으면 raw deviation0이다. 이후 위의 own-frequency OLS 제거·표준화를 적용한다.
shrinkage alpha5/10의 작은 사전 후보만 사용하며 enormous raw lift를 직접 score로 쓰지 않는다.

hyperedge overlap/Jaccard는 set 크기6에 대해 intersection과intersection/(12−intersection)이다.
IID expected overlap은0.8이다. 최근26개 draw와 최소26회 떨어진 옛 hyperedge의 유사 예시를 저장한다.
이 set 진단은 descriptive이며 Phase11 delay-state 모델을 복제하거나 새 inference family로 해석하지 않는다.

## Successor 진단

각 W에서 neighbor/clustering/communityK2/communityK3/hyperSupport2/hyperSupport3의6개 feature를
45개 고정 끝점에서 계산한다. 총18개 pooled relation이다.
모든 feature가 완성된 뒤 next-draw label을 읽는다.
outcome도 endpoint별 intercept+own count로 회귀한 잔차를 쓰고,
feature residual과 outcome residual의 pooled Pearson correlation을 구한다.
positive maximum이 primary successor statistic이다.
각 feature의Top6 실제 hit·own cumulative rate 기대hit·같은W recent-frequency 기대hit도 기록한다.

45node×45endpoint를 독립 Bernoulli 관측처럼 p-test하지 않는다.
동일 history의 graph·subset·partition·outcome 의존성을 모두 보존한 complete-search null로 보정한다.
linear own-frequency를 넘어선 관계를 묻는 진단이며 모든 가능한 nonlinear frequency confounding을 제거하지는 않는다.

## 전체 검색과 null

| 범위 | history 하나의 후보 수 |
|---|---:|
| rolling graph | 135 |
| pair/window/endpoint | 133,650 |
| triple/window/endpoint | 1,915,650 |
| weighted partition | 270 |
| non-overlap community stability | 5,588 |
| non-overlap graph persistence | 2,794 |
| pooled successor relation | 18 |

다섯 primary family는 normalized edge / community stability / supported triple /
frequency-residual persistence / frequency-controlled successor다.
primary 후보 cell합계는 **2,057,700**이며 개별 cell이 독립 검정이라는 뜻은 아니다.

IID199회와 fixed-margin199회, seed140042를 사용한다.
기존 Curveball row당20 trades는 row6개와 전체 번호 빈도를 정확히 보존하며 유한 mixing 한계는 남는다.
각 null history에서 graph·hypergraph·community·persistence·successor를 모두 재구축하고 자체 최고 구조를 고른다.
실제 최고 번호쌍/triple/community를 null에 고정하지 않는다.
global empirical p=(1+exceedances)/(199+1), family5 Bonferroni p=min(1,5p)다.
서로 다른 두 null 중 유리한 것만 선택하지 않는다.

## 개발 모델과 이후 평가

개발 target401–900, 이후901–1245. 과거 Phase에서도 사용한 역사이므로 pristine holdout이 아니다.
GraphStructureModel은 W3개에서 neighbor/clustering 각3개,
community 및 equal neighbor+community 각각W3×K2의 **18개** 후보를 갖는다.
HypergraphModel은 W3×support2×shrinkage2의 **12개** 후보다.
threshold2 및 frequency regression 방식은 사전 고정하며 이후 결과로 바꾸지 않는다.
score는 위 pure relational residual이며 probability calibration을 주장하지 않는다.
모든 target에서 정확한 prefix<T만 받고 graph/partition/normalization/subset 선택을 다시 한다.
cache key는 training bytes·shape·W·사전 feature/support/shrinkage다.
full-history graph/partition을 예측에 재사용하지 않는다.

개발 Top6 평균, tie 선언 순서로 선택하고 이후 전에 exclusive JSON/hash로 동결한다.
equal-rank consensus는 두 parent가 각각 개발평균0.8과Frequency26을 넘고,
combination이 두 parent보다 개발전체 및 두개발절반에서 모두 엄격히 좋을 때만 허용한다.
광범위 weight 탐색이나 final H17 ensemble은 만들지 않는다.

이후 Random·Frequency26·Gap Logistic·Graph·Hypergraph와 선택W에 맞춘 두 own-frequency control을 비교한다.
Gap fit cadence26/13과 달리 structural model은 매 target refit이다.
`outer_fit_cutoff`는 cadence anchor를 보존하고 structural model의 `training_cutoff` 및
`structural_training_cutoff`는 실제T−1을 기록한다.
평균Top6/hit0–6/Recall6·10·15/meanwinningrank,
Top8/10/12/15>=5 및Top6/8/10/12/15all-six를 저장한다.
paired circular block-bootstrap2000회, block26/13, references는 **Random·Frequency26·Gap** 세 가지다.
선택W의 matched-frequency 대비 구간도 추가한다. overlappingW104의긴memory를고려해block52/104 sensitivity도모두저장한다.
여러모델/metric/기간 전체의 동시구간은 아니다.
희귀사건 구간0퇴화는 사건확률0의 증명이 아니다.

early901–1015/middle1016–1130/recent1131–1245와 시작1001/1101의 같은 고정예측열 subset을 보고한다.
사전30개 후보의 later sensitivity는진단용이며 이후 점수로설정을교체하지않는다.
Gap과번호좌표정렬Spearman·Top6/10/15overlap을계산한다.
Phase13MI의기존예측CSV가있어추가비교하지만MI를refit/retune하지않는다.

## 산출물과 prospective

cumulative/recent adjacency, strongestedges/community/stability/triples,
두globalnull, 역사ranking과frequencyvsrelation그림을저장한다. 그림은증거자체가아니다.
binary·hyperedges·subsetIDs·135개adjacency/triplecounts·feature/partitioncache를보존한다.
surrogate별표현은계산중재사용하고hash및전체maxima를저장한다.

`draw1247_phase14_graph`는동결설정·원본archive검증준비gate다.
archive없으면 **PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**으로거부한다.
1246target은항상거부하며1246import/refit와실제1247publication은수행하지않는다.

```powershell
python main.py graph-hypergraph benchmark
python main.py graph-hypergraph analyze --surrogates 199 --workers 4
python main.py graph-hypergraph select
python main.py graph-hypergraph compare --cadence 26
python main.py graph-hypergraph compare --cadence 13
python main.py graph-hypergraph sensitivity
python main.py graph-hypergraph plots
python main.py graph-hypergraph prepare-freeze
```

기존`.deps/docs-checks`를PYTHONPATH로사용하고BLASthread1로제한했다. 새network dependency를설치하지않았다.
weighted spectral방법은 [von Luxburg(2007), 원 논문](https://arxiv.org/abs/0711.0189),
partition 비교는 [Hubert & Arabie(1985), 원 논문](https://doi.org/10.1007/BF01908075)을참고했다.
Lotto에서의판정은이문헌이아닌현재valid-historynull과causal이후평가를기준으로한다.
