# Phase 2 — 개별 번호 시간 분석

## 목적과 결론

본번호 여섯 개의 시간적 특성을 기술하며 bonus는 제외합니다. 예측 전략을 도입하지 않습니다. 당시 보고서는 검증된 1245회까지 snapshot을 사용했고 third-party provenance 한계는 유지됩니다. H1은 TESTED / INCONCLUSIVE입니다.

## CLI

```powershell
python main.py inspect 17
python main.py inspect 7 --permutations 4999 --seed 42
python main.py inspect 34 --permutations 4999 --seed 42
python main.py analyze-all --permutations 4999 --seed 42
python main.py inspect 17 --no-plots --permutations 0
python main.py analyze-all --windows 26 52 104 --max-lag 52 --min-cycles 3 --percentile 90 --regime-history 52 --regime-length 3
```

`--reports-dir`로 report root를 바꿉니다. default는 `reports/`, 번호별 table은 `reports/number_N/`, plot은 `reports/plots/`입니다. default는 eligible scope당 199 simulations이며 당시 실행은 4,999였습니다. 0은 simulation을 생략합니다. seed로 결과를 재현하지만 runtime은 달라집니다. scope·setting 변경은 새로운 탐색이며 독립 확인이 아닙니다.

재사용 entry point는 `src/analysis/`의 `calendar_stats`, `rolling_stats`, `autocorrelation_analysis`, `spectral_analysis`, `periodicity_metrics`, `permutation_comparison`, `detect_regimes`, `recurrence_stats`, `analyze_history`, `plot_number`입니다.

## 출력 파일

| File | Contents |
|---|---|
| `number_history_stats.csv` | One row per number: total/rate, all appearance draws and intervals (JSON arrays), gap stats, current gap, runs and longest observed absence |
| `appearance_history.csv` | One row per appearance: number, draw, date and interval from preceding appearance |
| `yearly_number_stats.csv` | Number × year: eligible draws, appearances/rate, expectation/deviation and within-year completed-gap statistics |
| `monthly_number_stats.csv` | Number × month 1–12: eligible draws, rate and ratio to number's full-history rate |
| `year_month_number_stats.csv` | Number × observed year-month, normalized by that month's eligible draws |
| `rolling_number_stats.csv` | Number × window size × endpoint: frequency/rate, gap statistics/status, ACF/spectrum/score, prior-only threshold and high-score flag |
| `periodicity_regimes.csv` | Contiguous confirmed high-score runs, support start, endpoint dates, confirmation/peak draw, score and dominant lag/period |
| `regime_recurrence.csv` | Raw regime starts and coalesced-episode intervals, variability and insufficient/irregular/candidate status |
| `periodicity_null.csv` | Conditional shuffle diagnostics for full history and latest complete window of each size, with raw and Bonferroni-adjusted Monte Carlo p-values |
| `temporal_analysis.json` | Configuration, cutoff, source/normalized CSV hashes, versions, timings, row counts, warnings, full number summaries and ACF/spectral arrays |
| `plots/number_NN_temporal.png` | Nine panels: appearances, gaps, yearly/monthly rates, rolling rates/score, full-history ACF/spectrum and regimes |

빈 CSV cell·JSON `null`은 측정 불가이며 zero evidence가 아닙니다. 처음·마지막 partial year는 실제 draw 수로 나눕니다. monthly ratio는 해당 번호의 월별 rate/전체 rate이며 미출현 번호·미관측 월은 unavailable입니다. per-number expectation은 6/45, yearly expected count는 eligible draws × 6/45, deviation은 observed rate - 6/45입니다.

## 데이터 표현 — Gap과 rolling 경계

appearance interval은 hit 간 draw 거리로 연속이면 1입니다. current gap은 마지막 hit 이후 absent draws로 endpoint hit면 0입니다. longest absence는 observed leading/trailing run도 포함하고 censored boundary 접촉 flag를 남깁니다. 실제 run은 자료 밖으로 이어질 수 있습니다.

calendar year·rolling window의 completed gap은 두 hit가 모두 해당 구간 안인 interval만 씁니다. mean/median은 한 interval, population std는 두 interval 이상이 필요합니다. 열 개 미만은 `unstable`, 없으면 `insufficient`입니다. 기존 whole-history utility의 한 interval population-std 동작은 유지합니다.

width-W endpoint-t는 정확히 t-W+1..t이며 padded/partial window를 export하지 않습니다. 창 안에 출현이 없으면 current gap은 unknown, `absence_lower_bound=W`이며 창 밖 이전 hit를 쓰지 않습니다. completed gap은 boundary-truncated sample이라 full-history 분포의 unbiased 추정이 아닐 수 있습니다.

## 핵심 정의와 계산 — ACF·spectrum·score

default guard는 20 observations·출현 네 번·불출현 네 번입니다. 부족하면 status와 null score를 반환합니다. ACF max lag는 floor(n/3)와 n−12로도 제한하고 각 overlap side에 출현·불출현이 각각 두 번 이상 필요합니다. demeaned biased estimator는 다음과 같습니다.

```text
r(k) = sum_t [(x[t] - mean(x)) (x[t+k] - mean(x))]
       / sum_t [(x[t] - mean(x))^2]
```

lag zero는 탐색하지 않고 유효한 positive lag 상위 세 개를 보고합니다. 전부 nonpositive면 positive-strength는 zero, candidate lag는 null입니다. lag1은 persistence일 수 있으며 주기를 뜻하지 않습니다. estimator는 긴 lag를 감쇠합니다.

[SciPy periodogram](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.periodogram.html)은 unit sampling frequency·Hann window·constant detrending·one-sided `spectrum` scaling을 사용하고 zero padding은 하지 않습니다. default period는2..n/3 draws로 최소 세 cycle입니다. `--min-cycles`의 최소값은2입니다. frequency resolution은 유한하며 이웃 bin·harmonic은 독립 cycle이 아닙니다. power는 확률이 아닙니다.

A는 가장 큰 positive ACF, S는 최대 eligible spectral-bin power/**전체 positive-frequency power**입니다. S의 분모에는 long-period guard로 제외한 power도 포함합니다. G는 population gap variability의 `1/(1+CV_gap^2)`입니다.

```text
periodicity_score = 0.4*A + 0.4*S + 0.2*G
```

component는 모두 [0,1]입니다. 하나라도 missing이면 score도 missing이며 partial score로 낙관하지 않습니다. random binary에도 양의 score, 특히 G의 양의 baseline이 있습니다. weight는 초기 convention이며 최적화하지 않았습니다. window별 null distribution이 다르고 이 score는 미래 출현 확률이 아닙니다.

## Regime과 기술적 recurrence

endpoint마다 같은 number/window의 이전 finite score로 expanding90th percentile을 구하며 최소52 valid past scores가 필요합니다. strict greater만 표시하고 tie는 제외합니다. missing·비연속 endpoint는 run을 끊으며 qualifying endpoint 세 개 연속부터 regime을 기록합니다.

`start_draw`·`end_draw`는 qualifying window endpoints입니다. 최초 underlying observation은 `support_start_draw`, minimum run을 알게 된 때는 `confirmed_draw`입니다. 더 이른 regime start는 retrospective label입니다. `open_at_cutoff`는 endpoint에서 계속되는 run입니다. peak lag/period는 highest-score endpoint에서 가져오며 regime 안에서도 달라질 수 있습니다. 물리적 change point가 아닙니다.

recurrence에서는 support window가 겹친 연속 regime을 합칩니다. `independent_episodes`는 nonoverlap episode라는 뜻이며 통계적 독립성을 주장하지 않습니다. raw regime-start와 episode-start interval을 모두 보고합니다. timing candidate 조건은 다음과 같습니다.

1. nonoverlap episode 네 개 이상, 즉 start interval 세 개 이상입니다.
2. episode interval CV ≤0.25입니다.
3. episode 대표 spectral-period CV ≤0.25입니다.

episode period는 constituent regime 중 highest-score에서 가져오며 candidate interval은 episode-start gap 평균입니다. 나머지는 insufficient/irregular 상태를 구분합니다. candidate도 recurrence null 검정 없는 heuristic 기술값입니다. coalescing은 명백한 overlap만 줄이며 dependence를 제거하지 않습니다. 이 초기 진단은 미실행 H9 / Phase 11 delay embedding과 다릅니다.

## Null / surrogate와 Global search correction

번호별 출현 수를 보존해 binary sequence를 shuffle하고 lag·spectral-bin 탐색을 포함한 전체 score를 다시 계산합니다. B shuffles 중 observed 이상이 E개이면 다음과 같습니다.

```text
p = (1 + E) / (B + 1)
```

temporal order의 one-sided conditional Monte Carlo 비교이며 appearance count 자체의 이상 여부를 검정하지 않습니다. plus-one은 zero p를 막는 보수적 convention입니다. [SciPy 설명](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html)을 참고합니다. null mean/95th quantile·exceedance·resolution·approximate Monte Carlo SE를 보고합니다. 작은 B는 noisy tail을 만듭니다.

사전 fixed scope는 full history와 최신 complete26/52/104입니다. planned family45 × 4 = 180에 ineligible도 보수적으로 포함합니다. 한 번호 inspect에도 같은 family를 쓰고 유리한 single-number correction을 쓰지 않습니다. custom window는45 × (1 + listed window 수)입니다.

이 보정은 모든 rolling window·past peak·regime·recurrence·calendar contrast·다른 setting을 포괄하지 않습니다. 작은 fixed-scope p로 시각 선택 regime을 검증할 수 없습니다. 번호별 marginal count만 보존한 null이며 joint six-number draw simulation이 아닙니다. Bonferroni는 test 독립성을 요구하지 않습니다.

## Leakage 방지

rolling metric·past-only threshold·high-score flag는 prefix invariant입니다. 나중 draw 변경으로 earlier endpoint가 바뀌지 않습니다. endpoint t는 draw t를 포함하므로 target t+1 전의 history 기술에 쓸 수 있고 draw t 예측에는 쓸 수 없습니다. 경계 테스트와 기존 backtest 테스트를 유지합니다. calendar ratio·전체 null·완료 regime·recurrence는 retrospective이며 RandomModel·backtest에 exploration artifact를 전달하지 않습니다.

## 주요 결과와 검증 범위

당시 전체 번호 실행은1–1245회, seed 42, windows 26/52/104, default score/regime, eligible scope당4,999 shuffles입니다.

- number summary45개, appearance7,470개입니다.
- number-year1,125, number-month540, number-year-month12,915 rows입니다.
- trailing rows 160,020, regime1,171, recurrence135 rows입니다.
- planned180 scopes 중 eligible155, sparse25이며 총774,845 shuffles를 완료했습니다.

export/plot 제외 runtime은 **502.8 seconds**(8.4 minutes), rolling/regime58.5 seconds·null439.6 seconds입니다. 다른 작업이 병행되어 환경별 wall-clock입니다. default199는 약25배 적은 simulation budget이나 rolling 비용은 남습니다. rolling CSV는 약35.6 MB입니다. 빠른 테스트는 작은 fixture·zero/9/19 shuffles를 씁니다.

fixed scope 다섯 개의 raw p<0.05였지만 adjusted p<0.05는 없었습니다. 최강 raw는 number8 최신52 draws, score 0.447193, 4,999 중13 exceedances, p=0.0028, adjusted0.504입니다. 180 scopes 탐색 후 특이 구조를 확립하지 못했으며 random임이나 모든 패턴 부재의 증명도 아닙니다.

기술 recurrence rule을 통과한 timing candidate는 세 개였습니다.

| Number | Window | Nonoverlapping episodes | Episode-start gaps | Mean candidate interval |
|---|---:|---:|---|---:|
| 8 | 104 | 4 | 294, 197, 235 | 242.00 draws |
| 13 | 52 | 5 | 200, 295, 194, 178 | 216.75 draws |
| 34 | 52 | 5 | 190, 239, 256, 237 | 230.50 draws |

heuristic scan으로 선택했고 recurrence null test는 없었습니다. number34의 spectral-period CV0.2452는0.25 경계에 가까워 convention에 민감합니다. 다른132개 조합 중 irregular102, insufficient30이었습니다.

번호 **7,17,34**는 결과 전 선택했고 같은 seed·4,999 shuffles로 inspect했습니다. aggregate/individual null table은 일치했고 [plot](../reports/plots/)을 당시 확인했습니다.

- **7:** 세 window에서21 regimes, timing candidate 없음, full-history shuffle p=0.6272입니다.
- **17:**36 regimes로 dominant period가 변했습니다. 104-draw endpoint1051–1076·1124–1147의 peak period는 각각2.12·8.0 draws였습니다. candidate 없음, full-history p=0.1462입니다.
- **34:**23 regimes와 위52-draw candidate입니다. 최신26-draw score 0.4151이 높아 보여도 raw p=0.09·adjusted1.0, full-history p=0.6740입니다.

세 번호의 eligible fixed-scope adjusted p는 모두1.0입니다. 반복 high-score band는 관찰 보조이며 이 예나 전체 결과가 예측력·통계적으로 확립된 recurring regime을 입증하지 않습니다.

supported window는 width 26에서25,625/54,900, width 52에서49,487/53,730, width 104에서51,383/51,390입니다. missing 구간을 low-periodicity regime으로 읽으면 안 됩니다.

당시 검증은 **69 tests passed**, 기존47개 포함입니다. calendar denominator·lag/period guard·missing·null seed·prefix invariance·regime overlap·recurrence guard·export·PNG·CLI path를 검증했습니다. 당시 canonical SHA256은 `b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e`로 유지되었고 advanced predictor·commit/push는 없었습니다.

## 평가·해석·한계·다음 단계

이 Phase는 예측 전략·candidate-pool·prize-aware·prospective 실험이 아닙니다. fixed-scope 보정은 regime scan 전체 보정이 아닙니다. 이후 완료된 예측 비교는 [Phase 3](predictive-experiments.md), 해시 범위는 [provenance](data-provenance.md)를 참고합니다.
