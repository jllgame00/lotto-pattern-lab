# Phase 12 결과 — H10 Wavelet / SSA multiscale structure

**H10: TESTED / INCONCLUSIVE.** WaveletPhaseModel·SSAModel 모두 **NOT CURRENTLY JUSTIFIED**.

번호5의 약13.42회 SSA 성분은 인접 역사 window에서 상대적으로 안정적이었으며,
두 null의 전체 탐색·6-family 보정 후 p=0.03이었다. 그러나 개발 선택 모델의 이후 예측 우위와
시간적 강건성을 확보하지 못했다. 구조와 예측 두 조건이 필요한 **PROMISING**으로 올리지 않는다.
Wavelet 국소 최대/지속 영역은 전체 탐색 보정을 통과하지 못했다.
하나의 구조 신호가 남으므로 H10 전체를 REJECTED BY CURRENT EVIDENCE로 분류하지도 않는다.

## 작업 시작과 데이터

- Git root: `C:/Users/Samsung/OneDrive/Desktop/university/personal/lotto-pattern-lab`.
- 시작 branch: `main`, SHA: `577358e3cd2b78935edb2f1f999c0f7fb1a1d822`.
- `git rev-parse --show-toplevel`, branch, `git status --short` 및 지정 README3개와 CSV를 먼저 확인했다.
  시작 작업 트리는 clean이며 Phase11이 완료되어 있었다.
- canonical 본번호1–1245회만 사용했다. 원본 CSV SHA-256:
  `3b7bb1e0a37c28ae4b4a97e098180d8407008ec007698c191ed6cf279db8225b`.
- draw1246은 fetch/import/파싱/구조 분석/null/개발/평가에 사용하지 않았다.
- [방법·수식·제외 규칙](multiscale-analysis.md) · [사전 실행 계획](superpowers/plans/2026-10-17-phase12.md).

## 표현과 탐색 공간

번호별 binary45개와 sum/mean/range/std/spacing mean/spacing std/consecutive-pair count/odd count8개,
총53개 series다. bonus와 optional principal activity는 사용하지 않았다.
Morlet omega0=6 한 종류, 주기8/13/20/26/39/52/78/104회, unit-L2 kernel,
입력별 평균 제거·population std 정규화 및 sqrt(2)×scale cone 제외를 사용했다.

SSA는 L=26/52/104, 416회 window 끝점416/624/832/1040/1245다.
전체 singular spectrum과 leading8개 재구축을 계산하며 인접7개 pair만 검색했다.
window별 평균 제거 후 첫 component energy, 보수적 spectral pair,
인접 window간 period/amplitude 안정성을 비교했다.

| 항목 | history 하나의 규모 |
|---|---:|
| Wavelet series×scale | 424 |
| cone 내 coefficient | 478,166 |
| SSA decomposition | 795 |
| SSA 인접 pair 후보 | 5,565 |
| window간 pair 비교의 후보 상한 | 31,164 |
| 고정 통계 위치 합계 | 516,114 |
| 실제 지속 Wavelet 영역 | 56 |
| 실제 spectral 조건을 통과한 SSA pair | 198 |

connected region은 동일 coefficient grid의 전체 연결 성분 탐색이며 위 합계에 독립 검정처럼 더하지 않았다.
통과한 pair와 영역의 수는 data-dependent이고, surrogate마다 자체 후보를 모두 찾는다.
실제에서 고른 번호·시간·scale을 null에 고정하지 않았다.

## 가장 강한 실제 구조

- Wavelet peak: **번호15, 1215회, period20**, normalized power **12.53188**.
  이것만으로 regime을 선언하지 않았다.
- 지속 Wavelet 영역: **번호14, 149–415회, period78**, duration267,
  score **42.07358**, 영역 안 max power7.71666, scale stability1.0.
- global concentration 최고도 번호14, **0.34201**이었다.
- SSA leading energy: **번호5, 209–624회, L26**, centered trajectory energy **0.08156**.
- SSA pair: **번호19, 1–416회, L26**, components1+2(문서 표기는1-based),
  period **11.24324**, energy share **0.13258**, reconstruction std **0.11223**,
  spectral concentration0.45665, score **0.0588651**.
- SSA stability: **번호5, L52**, window **1–416**과 **209–624**, components1+2,
  두 period 모두 **13.41935**. energy share0.09650→0.10443,
  amplitude0.10281→0.10143, pair score0.04856→0.05576,
  stability score **0.0479070**.

동일 번호5의 L104에서도 첫 두 window의13.41935회 성분과 stability0.04477이 남았다.
L26은 pair 조건을 통과하지 못했다. 따라서 한 정확한 L52에서만 보이는 현상은 아니지만,
L에 불변인 결과도 아니다. L52의 최대 pair는 이후417–832회에서 약16.99회로 바뀌고,
625–1040 및830–1245회에서는 후보가 사라졌다. L104에서도 최근 window에는 사라졌다.

별도의 descriptive waveform 비교에서 번호5/L52의 첫 두 window overlap208회 reconstruction 상관은
**0.96587**, 다음 window와는 **0.35595**였다. 이 추가 상관을 primary score로 교체하거나 새 p-value로 해석하지 않았다.
원래 stability family는 period/amplitude 안정성이며 phase 일치까지 증명하는 통계가 아니다.

Wavelet 번호5의 **301–378회, period13** 영역은 같은 SSA 역사 window와 겹쳤다.
전체60개 series/period/window 겹침 기록이 있으나 중복 window/L가 포함된다.
두 방법은 같은 noise realization을 변환하므로 **독립 확인이 아니다**.
번호13의26회 scale 등 동일 번호/scale이 다른 시기에 재출현한 사례도 저장했으며,
그 개별 사례에 별도의 유의성 주장은 하지 않는다.

## IID 및 fixed-margin 전체 null

IID199회 + fixed-margin199회. seed120042, 각 replicate는 SeedSequence로 분리했다.
fixed-margin은 기존 Curveball row당20 trades이며 row당6개와 전체 번호 빈도를 보존한다.
53개 표현·CWT·SSA·window·L·pair를 history마다 재구축하고 여섯 global maxima를 저장했다.

benchmark2+2회는0.900/0.850/1.395/1.604초, 순차398회 예상472.56초였다.
개발 실행과 동시에4개 worker로 본 검정 **288.82초**. 결과에 따른 탐색/replicate 축소는 없었다.

| family | real maximum | IID global p | fixed-margin global p | IID / fixed 보정 p |
|---|---:|---:|---:|---:|
| Wavelet peak | 12.53188 | 0.215 | 0.235 | 1.000 / 1.000 |
| Wavelet persistent region | 42.07358 | 0.305 | 0.345 | 1.000 / 1.000 |
| Wavelet global concentration | 0.34201 | 0.045 | 0.035 | 0.270 / 0.210 |
| SSA leading energy | 0.08156 | 0.505 | 0.515 | 1.000 / 1.000 |
| SSA oscillatory pair | 0.05887 | 0.150 | 0.220 | 0.900 / 1.000 |
| SSA period/amplitude stability | 0.04791 | 0.005 | 0.005 | **0.030 / 0.030** |

p=(1+exceedances)/200, family6 Bonferroni다. 마지막 family는 두 null 모두0/199 exceedances로
Monte Carlo 해상도의 최솟값에 도달했으며 진짜 tail 확률이 정확히0.005라는 뜻은 아니다.
두 null의 선택 중 유리한 쪽만 보고하지 않았다. 번호45개 및 shape/scale/time/L/window 선택이 이미 global maximum에 포함되어 있다.

## 개발 선택과 동결

개발 목표401–900회500개에만 설정을 선택했다. Wavelet6개, SSA6개 후보이며,
이후901–1245회를 개발 함수에 전달하지 않았다. configuration hash는
`5d881e19ec298c76cbec8231400924923651f2bc2a331d5f328b8bc7fd35cdac`다.

| 모델 | 동결 선택 | 개발 전체 Top6 | 개발401–650 | 개발651–900 |
|---|---|---:|---:|---:|
| WaveletPhaseModel | periods13/20/26/39/52/78, min2 cycles, trailing harmonic OLS R²>=0.1 | 0.796 | 0.820 | 0.772 |
| SSAModel | L104, 최고 supported pair, 표준 recurrent SSA | 0.830 | 0.848 | 0.812 |
| consensus 개발 진단 | equal-rank mean | 0.830 | 0.860 | 0.800 |

consensus는 전체에서 SSA보다 엄격히 좋지 않고 개발 후반에도 SSA보다 낮아 사전 조건을 통과하지 못했다.
**이후 consensus 모델은 평가/발행하지 않았으며 final ensemble도 만들지 않았다.**
개발 실행242.12초. 설정 JSON은 이후 평가 전에 생성했고 두 cadence 평가 전후 byte 불변을 확인했다.

## 이후 walk-forward 901–1245

모든 모델이 같은345개 목표를 사용했다. multiscale 평균·정규화·component/scale 선택과 분해는
매 목표의1..T−1에서 trailing416회를 사용했다. Gap Logistic fit만 cadence26/13으로 갱신했다.
full-history descriptive CWT/SSA를 예측에 사용하지 않았다. deterministic Top6 tie는 번호 오름차순이다.

| 모델 | 평균 Top6 | Recall@6 | Recall@10 | Recall@15 | 평균 당첨번호 순위 |
|---|---:|---:|---:|---:|---:|
| Random | 0.7681 | 0.1280 | 0.2198 | 0.3367 | 22.9585 |
| Frequency26 | 0.7739 | 0.1290 | 0.2072 | 0.3145 | 23.3362 |
| Gap Logistic | 0.8348 | 0.1391 | 0.2169 | 0.3309 | 23.0343 |
| WaveletPhaseModel | 0.7739 | 0.1290 | 0.2077 | 0.3145 | 23.3348 |
| SSAModel | 0.8087 | 0.1348 | 0.2130 | 0.3208 | 23.2324 |

| 모델 | hits0 | hits1 | hits2 | hits3 | hits4 | hits5 | hits6 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Random | 149 | 135 | 53 | 8 | 0 | 0 | 0 |
| Frequency26 | 142 | 144 | 54 | 5 | 0 | 0 | 0 |
| Gap Logistic | 141 | 135 | 55 | 13 | 1 | 0 | 0 |
| WaveletPhaseModel | 141 | 146 | 53 | 5 | 0 | 0 | 0 |
| SSAModel | 141 | 143 | 47 | 14 | 0 | 0 | 0 |

Top8/10/12/15>=5 회수: Random0/0/0/0, Frequency0/0/0/4, Gap0/1/1/4,
Wavelet0/0/0/4, SSA0/1/2/4.
Top6/8/10/12/15 all-six 사건은 모든 평가 모델에서 **0회**였다.
희귀 사건의 bootstrap 구간이0으로 퇴화한 것은 사건확률0의 증거가 아니다.

paired circular block-bootstrap2,000회, block26의 평균 Top6 차이와95% 구간:

| 모델 | 대비 Random | 대비 Gap Logistic |
|---|---|---|
| Wavelet | +0.0058 [−0.0899,+0.0986] | −0.0609 [−0.1479,+0.0233] |
| SSA | +0.0406 [−0.0580,+0.1450] | −0.0261 [−0.1217,+0.0696] |

나머지 recall/rank/pool 사건의 paired 구간도 CSV에 있다. 위 구간은 여러 모델·metric·기간에 대한 동시 신뢰구간이 아니다.
cadence26+sensitivity 실행192.59초, cadence13 실행132.88초였다.

## 강건성과 모델 다양성

| 모델 | early901–1015 | middle1016–1130 | recent1131–1245 | 시작1001 | 시작1101 | cadence13 전체 |
|---|---:|---:|---:|---:|---:|---:|
| Gap Logistic | 0.7565 | 0.9130 | 0.8348 | 0.8653 | 0.8828 | 0.8319 |
| Wavelet | 0.6696 | 0.9043 | 0.7478 | 0.8122 | 0.7586 | 0.7739 |
| SSA | 0.6435 | 0.9652 | 0.8174 | 0.8653 | 0.8276 | 0.8087 |

multiple start는 같은 고정 예측열의 이후 subset이다. 새로운 시작마다 개발을 재선택하지 않았다.
SSA의 중간 상승과 매우 약한 early 성능은 안정적인 우위와 맞지 않는다.
Wavelet는345개 목표 중 **8개**에서만 한 번호의 score가 W26 fallback과 달랐고,
**339개** 목표의 전체 순위가 Frequency26과 같았다. 사실상 새 정보의 활동이 매우 작다.
SSA는 매 목표 평균19.44개 번호 score가 fallback과 달랐다.

사전 후보를 이후 sensitivity로만 비교하면 Wavelet6개 설정의 Top6 범위는0.7652–0.7739다.
SSA supported-pair L26/52/104는0.7652/0.8000/0.8087,
leading2 control은0.8377/0.8812/0.8203이었다.
L52 leading2의 높은 이후 점수로 동결 설정을 바꾸지 않았다. 개발에서는0.774로 낮았던 설정을
이후 성능을 본 다음 고르면 새로운 사후 선택이 된다. 이를 검증된 새 모델로 승격하지 않았다.

| 모델 / 기준 | Spearman | Top6 overlap | Top10 overlap | Top15 overlap |
|---|---:|---:|---:|---:|
| Wavelet / Gap | 0.0894 | 0.8087 | 2.3362 | 5.1304 |
| SSA / Gap | 0.0330 | 0.8087 | 2.2232 | 4.8783 |
| Wavelet / Phase11 Recurrence | 0.0330 | 0.9159 | 2.4058 | 5.3217 |
| SSA / Phase11 Recurrence | 0.0209 | 0.9101 | 2.3652 | 5.2058 |

번호 좌표를 정렬한 전체 ranking Spearman이다. Phase11의 기존 고정 CSV만 읽었으며 refit하지 않았다.
낮은 상관은 정보 차이를 보이지만, 작은·불안정한 예측 성능을 보완하는 증명은 아니다.
두 모델 모두 **NOT CURRENTLY JUSTIFIED**. SSA의 구조 진단과 코드·설정은 탐색 자료로 보존한다.

## 그림과 산출물

`reports/multiscale/plots/`에 **11개 PNG**를 생성하고 실제 scalogram·null 비교·SSA 재구축을 직접 확인했다.
matched IID/fixed-margin은 같은 real-selected 번호14, scale/time grid와 공통 color limit를 사용한 시각 예시다.
검정은 이 고정 예시가 아니라 각 null의 자체 global maximum으로 수행했다.

```text
real_scalogram.png
iid_scalogram.png
fixed_margin_scalogram.png
strongest_localized_region.png
global_power_comparison.png
ssa_singular_spectrum.png
ssa_reconstruction.png
ssa_stability_reconstruction.png
real_vs_null_statistics.png
rolling_multiscale_strength.png
predictive_ranking_example.png
```

표현 NPY, CWT NPZ(계수·power·dominant trace·cone·global power), Wavelet/SSA 전체 search,
지역 CSV, null maxima/progress, corrected comparison, 개발 후보별 예측/summary, 동결 설정,
rolling strength, cross-method overlap, reconstruction stability, model activity 및 두 cadence의
predictions/summary/paired/rank diversity/protocol을 저장했다.
로컬 생성 파일은 기존 관례대로 Git-ignore되며 `reports/multiscale/run_manifest.json`에 정확한 파일 목록과 SHA-256을 보존한다.

## Prospective 및 최종 검증

**PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**.

`draw1247_phase12_multiscale` 설정 로딩·원본 archive 검증 준비 gate는 구현했다.
archive가 없으면 즉시 거부하며, 존재하더라도 원본 inventory와 기존 Phase5–10 verifier 전체를 요구한다.
준비 gate는 실제 publication/refit을 하지 않는다. 완전한 발행 기능이 실행 준비되었다고 주장하지 않는다.
1246 target은 거부한다. 이번 작업은1246을 가져오지 않았고1247·1246 prospective snapshot을 발행하지 않았다.
부재한 과거 archive나 옛 hash/예측을 재구성하지 않았다.

전체 테스트: `python -m pytest -q -rs` → **386 passed, 1 skipped**,120.78초.
skip은 기존 `tests/test_predictive_models.py:52`의 optional LightGBM/XGBoost 미설치다.
Phase12 새62개 테스트는 모두 통과했다. 실제 분해 입력을 계측한901/1245 causal boundary,
future suffix 거부, surrogate parity/determinism/global maximum, 개발 전용 선택과 archive block을 포함한다.
리뷰 후 상수 부동소수점 series의 roundoff와 무후보/잘못된 CLI 인자 처리를 보강했다.
동일 seed의 실제+398개 전체 탐색을 다시 재현했고 모든 maximum·null row가 정확히 동일했다.
반복 실행은 새 독립 표본으로 세지 않는다. 최종 manifest audit도 통과했으며,
변경 소스·문서20개와 로컬 산출물44개(자기 자신인 manifest 제외), 그림11개의 hash/목록을 보존했다.

최종 `git diff --check`, 원본 CSV hash, 시작 HEAD 불변 및 archive 부재를 확인했다.
**commit/push는 하지 않았다.** 지정된 Phase12에서 멈추며 MI/Transfer Entropy, graph/hypergraph,
modular/difference-space, entropy/compression, tensor, symmetry/reflection, final ensemble을 구현하지 않았다.

## 정확한 변경 파일

기존 수정5개:

```text
.gitignore
README.md
docs/README.md
docs/research-ideas.md
src/cli.py
```

새 파일15개:

```text
docs/multiscale-analysis.md
docs/phase12-results.md
docs/superpowers/plans/2026-10-17-phase12.md
src/analysis/multiscale.py
src/analysis/multiscale_plots.py
src/analysis/ssa.py
src/analysis/wavelet.py
src/backtest/multiscale.py
src/models/multiscale.py
src/multiscale_cli.py
src/phase12_freeze.py
tests/test_multiscale.py
tests/test_multiscale_pipeline.py
tests/test_ssa.py
tests/test_wavelet.py
```

Git-ignore된 생성 파일과 검증용 local script의 정확한 목록은 run manifest를 기준으로 한다.
