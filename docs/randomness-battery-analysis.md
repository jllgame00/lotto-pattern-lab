# Phase26 / H25 — Integrated randomness battery 방법

이 연구는 실제 1–1245회가 동일한 제약의 random Lotto history와 구별되는지 검사한다. 하나의 큰 이상치와 여러 작은 편향의 누적을 별도 질문으로 고정한다. 예측 모델·ensemble·prospective prediction은 만들지 않는다. [실행 전 고정 계획](superpowers/plans/2026-10-18-phase26.md), [결과](randomness-battery-results.md)를 함께 읽는다.

## 자료와 두 null track

각 행은 1..45에서 중복 없는 본번호 여섯 개다. 기존 strict loader는 CSV를 분석하기 전에 회차가 정확히 1..1245인지 확인하고 미래 회차 suffix를 거절한다. 실제1246 자료는 읽거나 수집하지 않는다. Synthetic reference draw는 역사 회차가 아니다.

- Track A: uniform six-of-45 IID Lotto. Marginal frequency까지 포함한 9families / 2200units.
- Track B: 각 분석 구간의 관측 번호별 총출현 횟수와 행별 여섯 개를 보존하는 Curveball fixed-margin null. Marginal family51units와 margin만으로 결정되는 sum/odd-count 평균2units를 제외한 8families / 2147units.

행 내 45bits를 독립 Bernoulli로 취급하지 않는다. 전체 monobit 비율은 구조적으로 6/45이므로 검정하지 않는다. Shape variance·분포·관계·시간 통계는 margin 이외의 정보도 포함하여 Track B에 남기고 조건부 null로 비교한다. Fixed-margin 통계의 textbook IID reference는 유의성 기준이 아니다.

## 고정 표현과 inventory

표현은 번호별 binary45/time, draw binary45, sorted6, adjacent gaps5, shape7, fixed five-band counts뿐이다. Shape는 sum, range, population std, spacing mean, population spacing std, consecutive-pair count, odd count다. Bands는 1–9/10–18/19–27/28–36/37–45다.

| Family | A units | B units | 검정 통계 |
|---|---:|---:|---|
| marginal | 51 | 0 | 45번호 count 양측, chi-square, likelihood ratio, count dispersion, 최대 표준화 편차, 상위5/하위5 count 비율 |
| serial | 495 | 495 | 번호별 절대 lag correlation7개, lag1 transition G, 2/3-bit word G, appearance/nonappearance 후 조건부 확률 차이 |
| run_gap | 225 | 225 | 번호별 최장 absence/appearance run, run count, geometric gap GOF, gap CV² |
| overlap | 35 | 35 | 7lags의 overlap 평균·분산·평균 Jaccard·분포 GOF·최대 overlap |
| shape_distribution | 21 | 19 | 7shape의 평균·분산·고정 bin CDF 제곱거리; B에서 sum/odd 평균 제외 |
| shape_temporal | 108 | 108 | 7shape+5band의 6lags 절대 rank correlation, 고정 threshold 이진 transition G·최장 run·run count |
| relational | 992 | 992 | 990pair count 양측, pair dispersion, supported triple의 최대 excess |
| spacing | 47 | 47 | 44difference count 양측, opportunity-corrected GOF, adjacent-gap GOF, normalized gap-vector concentration |
| spectral_entropy | 226 | 226 | 번호별 첫13 FFT bin 집중도·flatness deficit·block2/3/4 entropy deficit, 한 개의 번호평균 normalized LZ78 |
| 합계 | **2200** | **2147** | |

Serial/overlap lags={1,2,3,4,8,13,26}; shape/band lags={1,2,4,8,13,26}. 전체 45번호와 선언된 모든 lag를 검색한다. Unit-level p가 작아 보이는 일부만 선택하여 omnibus에 넣지 않는다. Constant unit도 제거하지 않는다. Serial 등의 maximum과 aggregate는 해당 family maximum과 family 내 평균 bounded anomaly로 모두 보존한다.

2200/2147은 omnibus에 전달되는 scalar cell 수다. 그중 supported-triple cell은 **14190개 triple 전체 검색의 maximum**이다. 따라서 embedded triple 후보까지 펼친 candidate-cell 수는 A16389/B16336이다. 990pairs는 이미 개별 unit으로 계산된다. Histogram bins·FFT13개·word class는 선언된 aggregate의 내부 항이며 추가 선택 parameter가 아니다. 구체 key·방향·support·bin inventory는 `reports/randomness_battery/real_inventory.json`에 저장한다.

## 제약에 맞는 reference와 support

Overlap은 Hypergeometric(45,6,6), 기대 overlap=.8이다. Exact0..6 count를 저장하고 GOF는 0/1/2/≥3으로 고정 pooling한다. Pair 기대확률=15/990=1/66, triple=20/14190이다. Triple은 기대≥1 및 관측≥5를 동일하게 적용하며 적격 후보가 없으면 해당 maximum=0을 유지한다. Full에서 triple 기대=1.754757, 415회 era에서는 .584919여서 triple unit이 중립0이다. Era에서 support를 완화하지 않는다.

Absolute difference d의 기회 수는 45−d다. 전체 unordered pair990개에서 확률 (45−d)/990을 사용한다. Adjacent gap d=1..40의 확률은 C(45−d,5)/C(45,6)이며, 5N개 gap의 GOF bins는 1..8 각각/9–12/13–20/21–40이다. Normalized spacing concentration은 draw별 gap/sum(gap)이 균등 .2에서 벗어나는 제곱거리의 평균이다.

Gap은 관측 appearance 사이의 완결된 inter-arrival distance다. Geometric reference의 p는 해당 번호의 관측 appearance 비율이고 bins는 1/2/3/4/5/6–8/9–13/14–26/27–52/>52다. 시작·끝의 censored absence run은 최장 run에 포함한다. Geometric GOF는 진단 통계이며 censoring/추정 bias까지 null에 똑같이 재현한다.

Shape reference는 독립 synthetic IID65536draws(seed260001)로 고정한다. 실제 자료·era를 보고 bin을 선택하지 않는다. Shape CDF reference와 median-side threshold에 같은 reference를 쓴다. Band side는 count≥2다. 다음은 histogram edges다.

- Sum: 20부터256까지 등간격12bins.
- Range: [4,10,20,25,30,35,40,45].
- Std: [0,4,6,8,10,12,14,16,18,23].
- Spacing mean: [.5,1.5,…,9.5].
- Spacing std: [0,1,2,3,4,5,6,8,12,20].
- Consecutive pairs: [−.5,.5,…,5.5]; odd count: [−.5,.5,…,6.5].

CDF distance는 고정 edges의 누적확률 차이 제곱 평균이다. Spectral summary는 DC를 제외한 첫13 FFT bins만 쓴다. Block entropy deficit은 L·H(관측 binary marginal)−H(overlapping block L)이며 finite-sample에서 음수가 가능하다. LZ78은 기존 normalized complexity를 관측 binary entropy로 나눈 뒤45번호 평균 한 개만 쓴다. 독립 bitstream의 이론 p-value를 사용하지 않는다.

## Leave-self-out 정규화

각 track/scope별 실제1+surrogate199의 **200행 augmented pool**을 구성한다. 각 행은 자기 자신을 제외한199행을 reference로 사용한다. 실제 행의 reference는199surrogates, surrogate 한 행의 reference는 다른198surrogates+실제 행이다. 이는 동일 reference 크기를 가진 permutation-equivariant randomization 절차다. 실제 행이 surrogate reference에 포함됨을 명시하며 독립 reference bank라고 부르지 않는다. IID null 아래 모든 행이 대칭적이고, fixed-margin에서는 기존 sampling의 근사 exchangeability에 의존한다.

Center=peer median, scale=1.4826·peer MAD, MAD가0이면 peer sample std, 그것도0이면1이다. 원래 statistic 방향에 따라 upper z / lower −z / two-sided |z|로 바꾼다. 완전히 constant인 unit은 z=0,p=1이다. Robust z는 Gaussian tail 확률이 아니다.

Upper unit p=(1+자신 이상인 peer 수)/200, lower는 이하인 peer 수다. 양측은 min(1,2·min(upper,lower))로 계산한다. Ties를 포함하여 보수적으로 처리한다. 모든 surrogate도 자기 자신을 제외한 동일 방법으로 unit z/p를 받는다.

## 사전 고정한 세 omnibus

FamilyMaxScore는 family 내 oriented z 최대값이다. FamilyMax omnibus는 모든 family maximum의 최대값이다.

SumOfAnomalies는 `clip(z−1,0,4)`의 가중합이다. Threshold1/cap4를 고정하고 각 family에 같은 총가중치, 그 안의 각 unit에 같은 가중치를 준다. 큰 raw scale이나 많은 pair 수가 합계를 자동 지배하지 않는다.

Higher Criticism도 같은 unit weights를 쓴다. Weighted empirical CDF F_w(p)로 `sqrt(M_eff)·(F_w(p)−p)/sqrt(p·(1−p))`의 양의 최대값을 p≤.5에서 계산한다. Tied p의 마지막 누적지점을 사용한다. `M_eff=1/sum(weight²)`는 **Kish weighting scale이며 독립 검정 수 추정치가 아니다**. Discrete하고 서로 의존하는 unit p에 asymptotic HC 유의수준을 적용하지 않는다.

세 meta-score 각각을199surrogate의 동일 meta-score와 plus-one empirical p로 비교한다. Track 내 Bonferroni3, 두 track 전체 Bonferroni6을 모두 보고한다. 최종 H25 상태는 full history의 전체6보정을 사용한다. 세 점수 중 유리한 것만 주 검정으로 바꾸지 않는다. Family별 탐색 p는 own-family null maxima와 비교하고9/8family 보정도 저장한다.

## Surrogates·시간 안정성·검증

IID199+fixed-margin199, seed260042. 각 replicate는 full1–1245와 early1–415/middle416–830/recent831–1245를 각각 독립 생성한다. Fixed-margin era는 그 era의 margin을 보존한다. SeedSequence([260042,track_code,replicate,scope_id,scope_length])를 사용하고 기존 Curveball20trades/row를 적용한다. 총1592history vector에 완전한 battery를 재구축한다. Fixed-margin 유한 mixing은 exact independent uniform sampler의 보증이 아니며 조건부 결론의 한계다.

Era battery/가중치/threshold는 재설계하지 않는다. Era 결과는 robustness이며 별도18검정(3eras×2tracks×3scores) 보정을 보고한다. 199null의 최소 p=.005로18보정 최소=.09다. 이 해상도에서 era-level .05 rejection은 불가능하다. Family를 하나씩 빼면서 전체 real/null meta-score·가중치·p를 다시 계산한다. 이 결과는 descriptive stability이고 주 판정을 바꾸지 않는다. Family-drop scan은 track별27/24검정 보정을 함께 저장한다.

`audit`은 모든1592개 저장 raw vector의 inventory와 raw→peer normalization→meta→p를 재검증한다. 8pools에서 대표3행의 peer median/MAD·inclusive rank·weighted sum/HC를 별도 계산하고, 양 track×4scopes×첫/마지막 replicate의16histories를 seed에서 재생성한다. 모든1592histories를 다시 생성했다고 주장하지 않는다. 원본 data/과거 tracked artifacts/HEAD와 prospective30files/12recorded SHA-256도 시작 기록과 비교한다.

## 실행과 증거 기록

```powershell
python main.py randomness-battery prepare
python main.py randomness-battery analyze
python main.py randomness-battery diagnostics
python main.py randomness-battery audit
python -m src.analysis.evidence_ledger --check
```

기존 main 결과가 있으면 `analyze`는 덮어쓰기를 거절한다. 출력은 `reports/randomness_battery/` 아래로 제한한다. Archive 검증 실패는 정확한 불일치를 보고하고 중단한다. Archive를 재작성하거나 hash를 갱신하지 않는다.

이전 가설들은 [증거 종합](research-evidence-synthesis.md)에 기술적으로 나열할 뿐 p-value를 결합하지 않는다. [후보 원장](weak-signal-candidates.md)과 [JSON](weak-signal-candidates.json)은 과학적 null 근거·역사 예측 점추정치·ensemble bookkeeping을 구분한다. 현재 없는 과거 출력은 HISTORICAL_UNAVAILABLE로 표시하고 문서에서 재구축하지 않는다. H17은 BACKLOG이며 다음 Phase다.
