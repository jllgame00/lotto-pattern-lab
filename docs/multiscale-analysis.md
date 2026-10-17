# Phase 12 — H10 Wavelet / SSA 방법

질문은 “전체 기간에 안정된 주기가 없어도 특정 시기·특정 scale에서 반복 구조가 잠깐 나타나는가?”이다.
그림의 인상과 예측 근거를 구분한다. [사전 실행 계획](superpowers/plans/2026-10-17-phase12.md)에 탐색 범위를 기록한 뒤 실행했다.

## 데이터와 선택 경계

연구 입력은 canonical 본번호 **1–1245회**이며 bonus를 제외한다. CSV reader는 header+1245행까지만 읽고
파일 크기가 다르면 unknown suffix로 거부하므로 1246행을 파싱하지 않는다. fetch/import 경로가 없다.
구조 분석은 1–1245회 전체를 사용하며, 모델 개발 함수에는 정확히 1–900회만 전달한다.
개발 목표는 **401–900회**, 이후 평가는 **901–1245회**다. 이전 Phase에서 이미 사용한 역사이므로
pristine holdout·새 prospective 증거라고 부르지 않는다. 구조 분석 결과를 예측 설정 선택의 입력으로 전달하지 않는다.

## 표현

- A: 번호1–45 각각의 본번호 출현 binary series 45개.
- B: sum, mean, range, population std, spacing mean, spacing population std,
  consecutive-pair count, odd count의 8개. 정렬한 여섯 번호의 인접 차이를 spacing으로 정의한다.
- 전체 **53개**. sum/mean 및 range/spacing mean의 정확한 중복도 그대로 유지하며 null에서도 동일하게 재구축한다.
  표현을 더 늘리지 않았으며 optional principal activity는 사용하지 않는다.

## Morlet CWT

omega0=6의 complex Morlet 하나만 사용한다. 주기는 **8,13,20,26,39,52,78,104회**다.
`period = scale * 4π/(6+sqrt(38))`로 변환하고 period<=N/4를 강제한다.
관측 series를 해당 입력 prefix의 평균·population std로 표준화한다. 상수 series는 0이다.
kernel은 admissibility correction을 포함하고 ±8 scale에서 잘라 discrete L2 norm=1로 정규화한다.
SciPy FFT convolution과 zero padding을 사용하며 원형 wrap은 하지 않는다.

양끝으로부터 거리가 sqrt(2)*scale 미만인 계수는 cone of influence로 제외한다.
이 마스크는 peak, global power, region 탐색에 모두 적용한다. cone은 오차가 완전히 사라지는 경계가 아니며
큰 scale의 finite-length 편향은 같은 길이·방법의 surrogate 비교로 추가 제어한다.
global power는 scale마다 유효 시간의 평균이다. concentration=max(global power)/sum(global power)이며
불균일 scale grid에 정의한 탐색 통계이지 연속 spectrum의 확률밀도가 아니다.

raw coefficient·local power·global power·시간별 dominant period는 NPZ에 보존한다.
binary series의 sparsity 때문에 몇 번의 출현만으로도 큰 표준화 power가 생길 수 있다.
power>4는 **후보 영역 생성 threshold**일 뿐 local p-value 또는 유의성 기준이 아니다.

인접 scale/time의 four-neighbor connected region을 구성한다. integrated excess가 최대인 scale을 대표 주기로 정하고
연속 시간 길이가 최소 2×대표 주기 이상일 때만 남긴다.
region score=sum(power−4)/sqrt(cell count), scale stability는 각 시간의 최대 excess ridge가
대표 scale인 비율이다. isolated coefficient는 regime으로 부르지 않는다.
양끝·유효 구간 수·duration·max power·대표 주기·stability를 CSV에 저장한다.

## SSA

L은 **26,52,104**이며, 416회 window의 끝점은 **416,624,832,1040,1245**로 사전 고정했다.
원 series의 window 평균을 제거한 뒤 H[i,j]=x[i+j]인 L×(N−L+1) Hankel trajectory를 만든다.
H Hᵀ eigen decomposition은 trajectory SVD와 동치다. 전체 L개의 singular value와 energy ratio를 반환하고,
leading8개만 elementary matrix를 재구축한 뒤 anti-diagonal averaging으로 시계열로 되돌린다.
leading energy는 mean 제거 후 첫 component의 trajectory energy share다.
residual variance는 원래 단위의 centered series에서 재구축8개 합을 뺀 population variance다.
trajectory energy share와 reconstruction의 variance share는 같은 양이 아니다.

첫8개 중 인접7개 pair를 검사한다. 에너지 비>=0.7, 두 component의 FFT peak concentration>=0.35,
dominant period 차이<=20%, 두 주기 모두8–104일 때만 후보로 남긴다.
period는 두 Fourier peak period 평균, amplitude는 pair 재구축 합의 std다.
pair score=energy share × energy balance × 두 concentration 중 작은 값이다.
비슷한 singular value만으로 oscillation이라 선언하지 않는다. spectral 후보도 global null 검정이 필요하다.

인접 역사 window에서 같은 series/L의 모든 허용 pair를 비교한다. period 비>=1/1.2,
amplitude 비>=0.5일 때 stability score=min(pair scores)×period 비×amplitude 비다.
최대 점수의 두 pair를 보존한다. 겹치는 window의 안정성 자체도 noise에서 생기므로 같은 탐색을 null에 적용한다.

## 전체 탐색과 null

| 항목 | history 하나의 탐색 규모 |
|---|---:|
| Wavelet series×scale | 53×8=424 |
| cone 내 유효 coefficient | 478,166 |
| connected region | 위 grid에서 전부 생성, history마다 발견 수 기록 |
| SSA decomposition | 53×5×3=795 |
| 인접 pair 후보 | 795×7=5,565 |
| 인접 window pair 비교의 상한 | 53×4×3×7²=31,164 |

고정 통계 위치는 coefficient·global spectrum·leading energy·pair·stability를 합해 **516,114개**다.
connected-region family는 같은 coefficient grid를 재사용하는 data-dependent 탐색이다.
이를 임의의 독립 검정 개수로 환산하지 않는다. 각 history의 region 수와 pair 통과 여부는 달라도
후보를 찾을 권리와 모든 평가 위치는 같다. max 통계 자체가 이 선택 자유도를 포함한다.

여섯 primary family는 Wavelet peak / persistent region / global concentration,
SSA leading energy / oscillatory pair / stable pair다.
기존 IID Lotto 및 Curveball fixed-margin history를 각각 **199회** 생성한다.
후자는 row당6개와 전체1–1245회의 번호 빈도를 정확히 보존하고 row당20 trades를 사용한다.
독립 initialization이며 유한 mixing의 한계는 남는다. 각 history에서 53개 표현·정규화·CWT·SSA를 새로 계산하고
자체 최고 번호·shape·시간·scale·window·L·pair를 고른다. 실제 최고 위치를 null에 강제하지 않는다.
번호45개 검색도 이 global maximum에 이미 포함된다.

global empirical p=(1+null maxima>=real maximum 횟수)/(199+1).
여섯 family Bonferroni p=min(1,6p)를 각 null별로 보고한다. 두 null 중 유리한 것만 선택하지 않는다.
최소 raw 간격0.005이며 작은 p의 정밀도는 제한된다. 모든 surrogate의 search-space record를 실제와 비교한다.
구조 p-value는 개발 예측 후보12개의 최적화 p-value가 아니다.

## 예측과 개발 선택

모든 목표 T에서 입력은 정확히1..T−1이다. multiscale 분석은 그중 trailing416회(부족하면 모두)에서
평균·표준화·분해·scale/component 선택을 **매 목표 새로** 계산한다. 전체 역사 CWT/SSA cache는 예측에 사용하지 않는다.
cache key는 제공된 training-prefix bytes이며 바로 이전 대상/동일 L의 계산만 재사용한다.
예측 CSV의 `training_cutoff`는 기존 공통 evaluator의 outer fit/prefix 검증 기준이다.
multiscale 분해의 실제 cutoff는 매 행의 `feature_cutoff=T−1`이며, protocol에 every-target refit을 기록했다.

Wavelet 개발6개 후보: scale set {8,13,20,26,39,52}, {13,20,26,39,52,78},
{20,26,39,52,78,104} × 최소2/3 cycles. phase rule은 하나다.
cone 내 power>4의 충분히 긴 region이 최근2P 이내까지 이어지는 번호에 대해서,
관측된 마지막2P 또는3P에서 intercept+sin+cos OLS를 fit하고 한 회차만 연장한다.
OLS R²>=0.1을 추가 적용한다. 경계 밖 CWT coefficient를 phase로 사용하지 않는다.
지지되지 않는 번호는 W26 frequency로 fallback하며 이를 별도 모델로 비교한다.
이는 training 내부 휴리스틱 지지이며 통계적으로 유의한 oscillation이라는 뜻이 아니다.
416회에서104주기는 cone 내부2주기를 확보하지 못하고78주기는3주기를 확보하지 못한다.
긴 scale을 억지로 예측에 살리지 않는다.

SSA 개발6개 후보: L3개 × {leading2, supported_pair}.
후자는 training에서 위 진단을 통과한 최고 pair를 선택하며, 없으면 W26 fallback한다.
leading2는 centered leading2개를 항상 선택하는 단순 저차원 control이다.
표준 recurrent SSA: 선택 U_i의 마지막 좌표 π_i에 대해
R=Σπ_i U_i[:-1]/(1−Σπ_i²), 선택된 재구축 series 마지막 L−1개에 R을 적용한 뒤 training mean을 더한다.
denominator<=0.05 또는 coefficient norm>10이면 fallback한다. score는[0,1]로 clip하며 확률 calibration을 주장하지 않는다.

개발500개 목표의 Top6 평균으로 선택하고 tie는 선언 순서다. 이후 평가 전 exclusive 생성한
configuration JSON의 SHA-256을 저장하고 이후 평가 전후 byte 불변성을 검사한다.
consensus는 equal-rank 평균만 허용하며, 개발 전체와401–650/651–900 두 절반에서 모두
각 parent보다 엄격히 좋을 때만 평가에 포함한다. 임의 가중치나 final ensemble은 만들지 않는다.

## 평가·다양성·강건성

RandomModel·Frequency26·기존 Gap Logistic과 동일 목표를 비교한다.
Gap fit cadence26, sensitivity13이며 multiscale은 cadence와 관계없이 매 목표 prefix에서 분해한다.
Top6 평균과0–6 hit 분포, Recall@6/10/15, 평균 당첨번호 순위,
Top8/10/12/15>=5 및 Top6/8/10/12/15 all-six 사건을 기록한다.
Random 및 Gap 대비 paired circular block-bootstrap2,000회, block26/13으로 95% 구간을 산출한다.
이 구간은 여러 모델·metric 전체의 동시 신뢰구간이 아니다. 희귀 사건 구간의0 퇴화는 사건확률0의 증거가 아니다.

early901–1015 / middle1016–1130 / recent1131–1245와 시작1001/1101의 같은 고정 예측열 subset을 보고한다.
nearby scale/L sensitivity는 사전12개 후보 전체를 이후에서 진단용으로 평가하며 설정을 다시 선택하지 않는다.
Gap과 번호 좌표를 정렬한 Spearman·Top6/10/15 overlap을 계산한다.
Phase11 고정 예측 CSV가 있으므로 그 ranking도 비교하며 refit은 하지 않는다.
낮은 상관만으로 ensemble 후보 자격을 주지 않는다.
Wavelet/SSA 역사 window 겹침은 같은 noise의 두 변환이므로 독립 확인이 아니다.

## 실행과 prospective

```powershell
python main.py multiscale benchmark
python main.py multiscale analyze --surrogates 199 --workers 4
python main.py multiscale select
python main.py multiscale compare --cadence 26 --sensitivity
python main.py multiscale compare --cadence 13
python main.py multiscale plots
python main.py multiscale prepare-freeze
```

모든 출력은 `reports/multiscale/` 아래다. installed local `.deps/docs-checks`를 PYTHONPATH로 사용하고
BLAS thread 수를1로 제한했다. binary/shape 표현과 실자료 CWT를 저장하고, SSA trajectory는 분해 내에서 재사용한다.
null 표현은 history마다 한 번 구성하여 계산 중 재사용하고 hash를 보존한다. 수백 개 전체 배열을 불필요하게 디스크에 저장하지 않는다.

`draw1247_phase12_multiscale`은 설정·archive 검증 준비 capability다.
원본 prospective archive 없으면 **PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**으로 거부한다.
archive가 있어도 원본 inventory와 기존 phase별 verifier가 필요하며, 이 단계는 실제 refit/발행을 수행하지 않는다.
1246 target은 항상 거부한다. 복원·검증과 별도 명시적 후속 절차 전에는1247 snapshot을 발행하지 않는다.

Morlet scale/cone 수식은 [Torrence & Compo (1998), 원 논문](https://psl.noaa.gov/people/gilbert.p.compo/Torrence_compo1998.pdf),
SSA diagonal averaging·recurrent algorithm은 [Golyandina, Nekrutkin & Zhigljavsky (2001), 원 저서](https://ndl.ethernet.edu.et/bitstream/123456789/32647/1/N.%20Golyandina_2001.pdf)의 방법을 따른다.
Lotto 유의성 판단은 이 문헌의 이론적 noise 임계치 대신 동일한 전체 surrogate search로 한다.
