# Phase25 — H24 Symbolic Dynamics / Markov order 방법

## 범위와 시간 경계

질문은 coarse symbol sequence에 valid random Lotto보다 강한 memory·transition·rare word 구조가 있는지다.
단순히 보기 좋은 transition matrix를 만드는 encoding을 선택하지 않는다.
Canonical history는 **1–1245회**만 사용한다. 기존 strict-source reader가 미래 suffix를 CSV로 parse하기 전에 거부한다.
1246회 결과를 수집·import하거나 bin·representation·parameter·model·평가에 사용하지 않는다.

- 1–200: quantile boundary calibration. 이 구간에 미래 경계를 적용한 분석 target symbol을 만들지 않는다.
- 201–600: 개발 Markov 초기 학습.
- 601–900: chronological 개발 prequential validation. 평가 후에만 해당 결과로 count를 갱신한다.
- 901–1245: 이후 prequential validation. Parameters·bin·모델 선택에는 사용하지 않는다.
- 전체 descriptive sequence는201–1245의1045symbols, 개발 sequence는201–900의700symbols다.

처음200회의 fitting 비용을 숨기지 않는다. 연속1–1245회가 데이터 범위이며 처음200회는 Markov uncertainty 검정에서 제외된다.
동일한 시간 경계를 모든 encoding과 surrogate에 적용한다. 이전 연구가 사용한 later 구간은 pristine holdout이 아니다.

## Symbol과 support

| Encoding | Alphabet | 고정 정의 |
|---|---:|---|
| parity | 7 | 홀수 본번호 수0..6 |
| balance | 13 | LOW1..22, CENTER23, HIGH24..45; symbol=7×CENTER indicator+LOW count. HIGH는6−LOW−CENTER |
| sum3/sum4 | 3/4 | Draw sum의 initial200 quantile thirds/quartiles |
| range3/range4 | 3/4 | max−min의 initial200 quantile thirds/quartiles |
| spacing | 6 | 5adjacent spacings의 population variance tertile×2 + consecutive-pair indicator |
| band | 10 | bands1–9/10–18/19–27/28–36/37–45의 dominant band×2 + max occupancy>=3 indicator |

Dominant band 동률은 가장 낮은 index를 택한다. Exact occupancy vector는 sparsity만 audit하고,
분석은 처음부터 reduced10을 사용한다. 결과를 보고 class를 병합·분할하지 않는다.
Quantile 값과 같은 관측은 위쪽 bin에 배정한다. Ties로 빈 symbol이 생겨도 declared alphabet을 줄이지 않는다.
모든 bin은200회에서 동결하고 이후 다시 fitting하지 않는다. 각 surrogate도 자신의 first200으로 fitting한다.

Alphabet audit는 declared/observed state 수, 각 count, minimum support(0포함), count<5 rare states,
marginal entropy bits와 effective alphabet `2^H`를 보고한다. Rare state는 real/null에서 모두 유지한다.

Support 규칙은 하나씩 고정한다: transition source>=20, destination>=5, expected>=5;
word expected>=5와 유효한 outgoing prefix count>=10; predictive context>=20.
Word 마지막의 successor 없는 prefix는 support에 세지 않는다.
지원 부족 cell을 raw transition/word 증거로 승격하지 않으며 same rule을 null에도 적용한다.

## Markov0–3와 uncertainty

Order0는 과거의 destination frequency에 alpha pseudocount를 더한 memoryless baseline이다.
Order k의 context는 정확히 target 직전 ksymbols다. Alpha={.5,1}만 검색한다.

`P(s | context) = (past_count(context,s)+alpha)/(past_count(context)+alpha*A)`

Context count<20이면 같은 alpha의 k−1로 backoff하고 order0까지 내려간다.
따라서 k는 최대 Markov depth다. 보지 못한 destination·context의 probability를0으로 만들지 않는다.
Held-out prediction을 한 다음 count를 업데이트하는 prequential logloss를 nats로 기록한다.
벡터화는 동일 event의 stable occurrence rank를 사용하며 미래 append/change가 과거 확률을 바꾸지 않음을 테스트한다.

Plugin `H(S_t|previous k)`는 full fitted context count의 empirical entropy(bits)다.
`H0−Hk`가 클수록 fitted memory처럼 보이지만 sparse context에서 자동으로 커진다.
Null에 같은 alphabet/support/sample size를 재구축해 finite-sample bias를 보정한다.
Plugin entropy와 support-backoff predictive logloss는 서로 다른 quantity다.

BIC는 training-prefix MLE loglikelihood와 dense declared parameter 수를 사용한다.
`BIC_k=2*(n−k)*H_k*ln(2)+A^k*(A−1)*ln(n−k)`.
이는 sparse effective parameter 수를 작게 세는 유리한 penalty가 아니다. Backoff model의 exact effective-df BIC라고 주장하지 않는다.
개발에서는 alpha별 validation loss를 비교한 뒤 lower order보다 .01nats 초과 개선하고 training BIC도 개선할 때만
높은 order를 허용한다. 동일 loss면 alpha1, 추가 order 개선이 불명확하면 낮은 order를 선호한다.
Alpha와 encoding/order의 선택을 surrogate도 모두 검색한다.

## Transition·words·forbidden·runs

Order1 transition의 expected count는 source exposure × empirical destination frequency다.
Supported cell에서 Pearson residual의 최댓값과 최솟값을 각각 검색한다.
Row entropy·smoothed row concentration도 저장한다. Common destination의 높은 count만을 evidence로 보지 않는다.

모든 declared word L2/3/4를 열거한다. L2 expected는 smoothed order0 product,
L3/4 expected는 smoothed marginal start와 smoothed order1 transition product다(alpha.5 고정).
Expected count는 `(n−L+1)*P(word)`다. Lift, count, support와 signed Poisson-deviance residual을 저장한다.
잔차는 `sign(O−E)*sqrt(2*(O*log(O/E)−(O−E)))`, O=0항은0log0=0으로 처리한다.
Observed count가0/1인 supported word의 max expected, missing fraction, longest supported absent L도 검색한다.
Finite samples의 absent word를 deterministic forbidden rule로 부르지 않는다.

Run은 동일 symbol의 연속 길이다. Longest run r, order0/order1 stationary start 근사에서
길이>=r인 expected run count의 `−log(E)`, transition-away와 order0 chance의 차이를 비교한다.
Order1 expectation은 smoothed diagonal stay probability를 사용한다. 이 근사 score도 Lotto-history null로 보정한다.
Lag={1,2,3,4,8,13,26}에서 same-symbol recurrence−marginal chance의 absolute excess를 secondary로 검색한다.

## 고정 검색공간과 null

| Family | Cells | Encoding당 내용 |
|---|---:|---|
| entropy | 24 | H0−Hk, k1/2/3 |
| heldout | 48 | k1/2/3 × alpha.5/1의 order0 대비 prequential gain |
| transition | 16 | supported positive/suppressed residual |
| word | 48 | L2/3/4 × positive/suppressed deviance residual |
| forbidden | 80 | 각 L의 missing max E/missing fraction/rare max E9 + longest absent length1 |
| run_lag | 88 | longest/order0 surprise/order1 surprise/away gap4 + lag7 |
| **합계** | **304** | 8encoding 모두 동일 |

Cell 안의 transition/word 내부 검색까지 매 history마다 새로 수행한다.
Declared transition candidate 수와 word candidate 수는 `real_summary.json`의 `space`에 정확히 기록한다.
Support에 따라 eligibility가 달라도 양쪽에 같은 규칙을 적용하고 unsupported winner는 neutral0이다.
실제 자료의 eligibility만 null에 고정하지 않는다.

각 scope900/1245에 독립 IID32pilot(seed251001)을 fitting하고 cell mean/sample std를 고정한다.
Pilot std<=1e-12인 cell은 **고정 unit scale1**을 사용하며304개를 모두 유지한다.
Pilot에서 한번도 나타나지 않은 rare-word event가 real/main null에서 생겨도 검색에서 빠지지 않는다.
`raw_std`와 실제 scale을 따로 보존한다. 단위 fallback은 real 결과를 보고 정하지 않는다.

Main은 IID199와 기존 Curveball fixed-margin199다. Main seed250042, child seed는
SeedSequence([seed,kind_code,replicate,scope_length])다. Each scope는 새 history를 생성한다.
Fixed-margin20trades/row는 row6 및 column number totals를 정확히 보존하지만 finite mixing의 한계가 남는다.
각 surrogate는 own initial200 bins, symbol counts, order0–3, alpha, transition/word/missing/run/lag 전체를 재계산한다.
각 cell의 upper pilot z를 만들고 family별 자체 maximum을 택한다.
Suppression과 lag reversal은 별도의 positive anomaly statistic으로 이미 표현되므로 모든 z에 abs를 다시 씌우지 않는다.

`global_p=(1+count(null_own_max>=real_own_max))/200`, `corrected_p=min(1,6*global_p)`.
두 null은 각각 보고하고 유리한 하나만 택하지 않는다. Family별 보정은 개발·전체 scope 각각 수행한다.

## 예측 gate

개발 entropy와 heldout family가 모두 두 null에서 corrected p<=.05여야 한다.
선택 encoding/order의 해당 entropy/gain cell도 양의 z로 같은 family null maxima 보정을 통과해야 한다.
또한 BIC/lower-order .01nats 기준을 통과하고 validation3구간 각각 order0 대비 gain이 양수여야 한다.
다른 transition/forbidden anomaly로 이 gate를 대신 열지 않는다.

통과할 때만 training-only SymbolicContextModel 및 필요 시 별도 DirectContextNumberModel을 구현하고
개발에서 configuration을 동결한 후 later ranking·Random/Frequency26/Gap·paired block bootstrap을 비교한다.
Gate가 실패하면 번호 예측·ensemble correlation·prospective machinery를 생성하지 않는다.
Order0–3의 symbolic later logloss는 과학적 진단으로 보고하되 full-period winning order를 새 모델로 선택하지 않는다.

## 안정성·inspection·검증

Full의 고정 transition/word winner를 분석 symbol sequence의 early/middle/recent thirds 및 W208/stride52에서 다시 본다.
Support 부족 window는 명시하고 새 p-value나 best-era 선택을 하지 않는다.
Encoding agreement는 normalized mutual information의 descriptive matrix이며 correlated encodings를 독립 evidence로 세지 않는다.
Plots는 inspection aid다.

```powershell
python main.py symbolic prepare
python main.py symbolic calibrate
python main.py symbolic analyze
python main.py symbolic diagnostics
python main.py symbolic audit
python -m pytest -q
```

모든 출력은 Git-ignored `reports/symbolic/` 아래다. 기존 complete/partial analysis 덮어쓰기를 거부한다.
Archive는 기존30files/12recorded SHA-256을 시작·끝에 검증하고 byte를 수정하지 않는다.
Audit은64pilot/대표8main seed replay,796raw metric vectors의 own-max/p 재계산, 실제 dictionary count 기반
prequential probabilities와 모든 word code 대조, source/과거 artifact/archive/HEAD hash 불변을 확인한다.
398main history 전부를 두 번째 생성하는 검증은 아니다.
기존 Windows parallel test4건의 WinError5는 숨기거나 기존 test를 수정하지 않고 전체 결과에 보고한다.
H25 Integrated randomness battery와 H17 final ensemble은 구현하지 않는다.
