# Phase 6 — 2D Translation 방법

## 목적과 연구 가설

ordered label의 이동 구조를 탐색합니다. 번호 label의 공간 관계를 가정하지 않습니다. 대각선은 mechanism의 증거가 아니며 fitted score는 출현 확률이 아닙니다. H3는 TESTED / INCONCLUSIVE입니다.

## 데이터 표현

1,245 × 45 binary matrix, row별 본번호 six ones를 사용합니다. 1–1245회만 사용하며 bonus는 제외합니다. bounded reader는 unknown suffix를 parsing하지 않고 거부합니다. 당시 1246회 이후 결과를 가져오지 않았습니다. 1245회는 허용된 역사 자료이며 pristine holdout이 아닙니다. 기존 연구 명령의 cutoff는 유지합니다.

Phase 5 snapshot·registry를 보존하고 Phase 6은 별도 `reports/prospective/phase6/` namespace를 사용했습니다. 별도 experiment ID·persistent reservation·exclusive creation·SHA-256·append-only registry를 갖추며 `freeze-2d` 재실행으로 재생성할 수 없습니다. 당시 uncommitted source를 내장하고 hash를 남겼습니다. 현재 원본 가용성은 [workflow](prospective-workflow.md)를 참고합니다.

## 핵심 정의와 계산 방법

dt1..52, dn-15..15에서 destination이 finite rectangle 안에 있는 source cell만 허용합니다. `valid_opportunities`는 observed source ones, `observed_matches`는 이동 후 관측된 pair 수입니다. `match_rate=matches/opportunities`, IID 기준 p=6/45입니다. `overlap_area`는 허용된 전체 cell 수, `joint_rate=matches/area`의 기준은 p²입니다. source가 없으면 rate는 NaN입니다. `raw_z=(matches-opportunities*p)/sqrt(opportunities*p*(1-p))`는 search statistic입니다. pair 중첩과 random denominator 때문에 단순 local normal 검정으로 해석할 수 없습니다. dn0은 reference로 export하되 translational maximum에서 제외합니다. positive-time overlap은 2D autocorrelation의 중복 없는 절반이며 negative-time shift는 반대 number displacement와 같습니다. same-draw / zero-displacement peak는 제외합니다.

Directional asymmetry는 양·음 displacement 각각의 opportunity로 정규화한 conditional rate를 비교합니다. 단순화한 variance는 같은 surrogate maximum으로 calibration하며 독립 유의성 검정으로 사용하지 않습니다.

같은 translation에서 길이 3,4,5 chain count를 탐색합니다. null expected count는 `(T-(L-1)*dt)*(45-(L-1)*abs(dn))*p**L`, count z-score는 기술 통계입니다. `maximal_chains.csv`는 관측 predecessor가 없는 run의 길이·geometric forward maximum·endpoints·`-L*log(p)`를 보고합니다. 이 score는 search-adjusted surprise가 아닙니다. 중첩된 짧은 chain은 count에 기여하지만 독립 발견이 아닙니다. 다른 slope도 점을 공유할 수 있습니다. 길이 5 초과에는 별도 maximum-longest-chain statistic을 사용하며 기하학적 불가능성을 보상하지 않습니다.

Hough는 primitive slope dt1..12, dn±1..6의 모든 intercept `dt*number_index-dn*draw_index`와 최소 12 eligible lattice positions를 사용합니다. support·length·density·endpoints·binomial-reference z-score를 보고합니다. primitive direction으로 같은 line의 중복을 막습니다. 모든 line을 탐색하되 상위 50개만 export합니다. surrogate 출력에 slope별 best만 남겨도 global maximum은 같습니다.

2D FFT는 row/column centering, 양 축 Hann tapering, nonzero temporal / number frequencies를 사용합니다. 중복 없는 positive-time half-plane에서 power를 정규화하며 최대 normalized power가 여섯 번째 statistic입니다. finite 45-number boundary·row별 six totals·tapering·discrete axis 때문에 peak를 물리적·예측적 주기로 해석할 수 없습니다. FFT는 predictor 입력이 아닙니다.

## Null / surrogate 설계와 Global search correction

199 seeded IID history와 독립 초기화한 199 curveball surrogate에 같은 전체 탐색을 합니다. Curveball은 20*T random row-pair trades로 정확한 row/column sums를 보존합니다. finite mixing은 한계이며 exact margins가 모든 fixed-margin matrix의 정확한 uniform sampling을 뜻하지 않습니다. changed-cell fraction을 export합니다.

`global_p=(1+# null maxima >= real maximum)/(199+1)`입니다. shift·absolute direction·chain-count score·longest chain·Hough score·spectral concentration 여섯 statistic에 Bonferroni를 적용해 `family_adjusted_p`를 구합니다. 두 null 모두에서 근거가 필요합니다. 최소 global p resolution은 .005, adjusted는 .03입니다. Monte Carlo 추정이며 exact analytic p-value가 아닙니다. local/raw score로 유의성을 주장하지 않고 전체 maxima를 보존합니다.

## Leakage 방지와 예측 모델

TranslationModel은 expanding prefix에서 100 IID prior opportunities로 conditional overlap을 shrink하고 양의 excess rate 상위 20개를 남깁니다. target T에서 T-dt만 보고 source_number+dn에 support를 더하며 candidate에 기하학적으로 유효한 rule weight 합으로 나눕니다. wrapping은 없고 score는 `p+(1-p)*support_fraction`입니다.

ChainModel은 이전 collinear 두 점을 조건으로 세 번째 점을 같은 방식으로 shrink합니다. T-dt와 T-2dt의 두 predecessor가 필요합니다. training에서 양의 support를 얻지 못한 임의 slope의 pair만으로는 부족합니다. 같은 bounded score를 사용하며 두 모델은 전체 history 보고서나 target outcome을 읽지 않습니다.

Combined2D는 두 percentile rank를 고정 equal weight로 평균합니다. 동률에는 average rank, 최종 score tie에는 작은 번호 우선을 적용합니다. 사전 선언 ablation이며 최적화 winner가 아닙니다. development 401–900 평균은 .854, Translation .842, Chain .766이었습니다. 별도 freeze에 남긴 제한적 기술 근거이며 안정적 우위의 증거는 아닙니다.

## 평가 지표와 Walk-forward

401–1245 targets, cadence 26이며 primary는 cadence 13으로도 실행했습니다. score는 T-1까지 history만 사용하고 learned rule·Logistic scaling은 refit 사이에 고정합니다. Gap Logistic의 six gap columns·기존 구현을 유지하고 compatibility test로 동일성을 확인합니다. RandomModel도 target-specific seed를 유지합니다. development는 900까지, later는 901–1245입니다. 앞선 Phase가 사용한 구간이므로 pristine holdout이 아닙니다.

start 401/501/601/701/801/901은 같은 실행의 nested slice로 prediction과 refit calendar를 유지합니다. early/middle/recent 및 별도 cadence 13 실행으로 불안정성을 봅니다. 두 family 모두 positive·negative·short 1–13·longer 14–52 shift ablation을 비교합니다.

평균 hit와 pool threshold/mean 차이는 2000회 paired 26-draw circular block bootstrap을 사용합니다. 많은 model/window/pool 비교에 대해 보정하지 않은 interval입니다. marginal Clopper–Pearson은 independent-indicator 진단용입니다. all-zero bootstrap 퇴화가 rare event를 배제하지 못하므로 exact hypergeometric rate와 upper bound를 함께 봅니다. pool containment는 ticket prize·평균 ranking 개선과 구분합니다.

## 출력 파일과 CLI

`python main.py analyze-2d --surrogates 199`는 shift·direction·maximal chain·chain-count·Hough·spectral·rolling/era·전체 null 보고서를 만듭니다. `python main.py compare-2d`는 audit prediction·ranking/pool·development·time block·개별 5+ event를 저장합니다. sensitivity는 `python main.py compare-2d --cadence 13 --primary-only`입니다. 당시 `python main.py freeze-2d`는 세 track의 전체 순위·score·Top6/8/10/12/15·direct Top6·seeded weighted/coverage 1/5/10/20 tickets를 동결했습니다. 같은 20-ticket generation prefix를 사용하고 portfolio search는 하지 않습니다. exact ticket은 원본 JSON·manifest에 있습니다.

경로는 `reports/spatiotemporal/`, plot은 `plots/`입니다. `plot_matrix(x,path,start=...,end=...)`는 허용된 draw range를 지원합니다. `verify_2d(snapshot)`는 target 결과 없이 hash·registry pointer·구조를 검증합니다. Phase 5 evaluator를 Phase 6에 재사용하지 않습니다.

## 한계와 현재 결과

ordered label의 의미·중첩 탐색·finite mixing·역사 구간 재사용이 한계입니다. [완료 결과](phase6-results.md)와 [색인](README.md)을 참고합니다. 일부 출력과 동결 원본은 이 체크아웃에 없습니다.
