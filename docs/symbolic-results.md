# Phase25 — H24 Symbolic Dynamics / Markov order 결과

**H24: TESTED / INCONCLUSIVE.** Symbolic memory는 동일 complete-search Lotto null 보정을 통과하지 못했다.
개발에서 여덟 encoding 모두 **order0**를 선택했고 **PREDICTIVE_MODEL_NOT_JUSTIFIED / NOT CURRENTLY JUSTIFIED**다.
Randomness의 증명이나 모든 가능한 encoding의 부재 판정은 아니다.
[방법](symbolic-analysis.md) · [고정 계획·review 기록](superpowers/plans/2026-10-18-phase25.md).

## 시작 상태·범위

- Git root `D:/univ/personal/lotto-pattern-lab`, branch `main`, 시작 SHA `3f78febd65f19360d98173742e5cd896f89f759c`.
- 초기 worktree clean, README/docs index/research ideas/canonical CSV 확인, Phase24/H23 완료 상태였다.
- 설명되지 않은 source/data 변경은 없었다. 기존 Windows parallel test4건의 named-pipe WinError5도 시작 때 재현했다.
- 실제 데이터 **1–1245회**만 사용했다. CSV SHA-256 `b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e`.
- 1–200회는 bin fitting, 분석 symbol은201–1245회다. 초기200회에 미래 quantile을 적용한 분석 target을 만들지 않는다.
- 개발 초기 학습201–600, 개발 prequential validation601–900, 이후901–1245로 고정했다. 이후 구간으로 encoding/bin/order/alpha/context를 선택하지 않았다.
- 이 later 구간은 과거 Phase에도 사용했으므로 pristine holdout이 아니다. Draw1246은 설계·선택·평가 어디에도 쓰지 않았다.

## 표현·alphabet·support

Parity7은 odd count, balance13은 `7*CENTER indicator + LOW count`다(LOW1..22/CENTER23/HIGH24..45).
Sum3/4·range3/4는 initial200 quantile, spacing6은 spacing population variance tertile×2+consecutive pair다.
Band10은 bands1–9/10–18/19–27/28–36/37–45의 dominant band×2+max occupancy>=3이며 동률은 최저 band다.
모든 declared class를 유지하고 count<5 state를 삭제하지 않았다.

| Encoding | Declared A | Observed | Min support | Rare symbols | H0 bits | Effective alphabet |
|---|---|---|---|---|---|---|
| parity | 7 | 7 | 14 | [] | 2.262427811 | 4.797982220 |
| balance | 13 | 13 | 3 | [7, 12] | 2.744136911 | 6.699887687 |
| sum3 | 3 | 3 | 275 | [] | 1.565297898 | 2.959386030 |
| sum4 | 4 | 4 | 225 | [] | 1.992413725 | 3.979021585 |
| range3 | 3 | 3 | 316 | [] | 1.581529632 | 2.992870036 |
| range4 | 4 | 4 | 232 | [] | 1.994500824 | 3.984782068 |
| spacing | 6 | 6 | 94 | [] | 2.514789414 | 5.715142274 |
| band | 10 | 10 | 20 | [] | 3.073169985 | 8.416205814 |

각 symbol count·order0 expected frequencies는 `alphabet_support.csv/json`, 고정 bin 경계는 `boundaries.json`,
전체1045symbol sequence는 `symbol_sequences.csv`에 저장했다. Boundary 값은 아래와 같다(고정 encoding은 빈 목록).

| Encoding | Initial1–200 boundaries |
|---|---|
| parity | [] |
| balance | [] |
| sum3 | [126.0, 157.66666666666666] |
| sum4 | [118.0, 141.0, 164.0] |
| range3 | [30.0, 37.0] |
| range4 | [28.75, 34.0, 38.0] |
| spacing | [14.853333333333333, 29.360000000000003] |
| band | [] |

Exact five-band count vector는 159가지 관측, min support1,
count<5 vectors84개였다. 분석은 처음부터 predeclared reduced10이며 사후 grouping하지 않았다.
Transition은 source>=20/destination>=5/expected>=5, word는 expected>=5/usable outgoing prefix>=10,
predictive context는>=20을 사용했다. 같은 규칙을 모든 surrogate에 적용했다.

## 검정·검색공간

Markov orders **0/1/2/3**, alpha **.5/1**이며 부족한 context는 낮은 order로 backoff한다.
Order0는 smoothed memoryless frequency다. Probabilities는 target 직전 count만 사용한다.
Plugin conditional entropy는 bits, prequential logloss는 nats다. 높은 order의 fit entropy 감소를 예측 memory와 구분한다.

**304cells** = entropy24/heldout48/transition16/word48/forbidden80/run-lag88이다.
내부 검색에는 **404declared transitions**, **47,274declared words(L2/3/4)**가 포함된다.
각 history에서 support를 다시 판정하고 자체 strongest cell·transition·word를 선택했다.
Pilot zero-variance cell은 fixed unit scale1로 유지해 **개발·전체 모두304/304**가 검정에 참여했다.
개발의 raw-std fallback cell 수는 56,
전체는 45다.

각 scope에 독립 IID32pilot(seed251001), main **IID199+fixed-margin199**(seed250042)을 실행했다.
Surrogate마다 자신의 first200 quantile, 모든 symbol/context/order/alpha/transition/word/forbidden/run/lag를 다시 만들었다.
Fixed-margin은 row6개와 번호별 column total을 정확히 보존하는 기존 Curveball20trades/row다.
Scope900과1245는 독립 생성하며 full null의 prefix를 dev null로 재사용하지 않는다.
Upper pilot z의 family own maximum에 `p=(1+exceed)/200`과 Bonferroni6을 적용했다.
Runtime은 116.055초, serial worker1이다.

## 전체 global-max 비교

p는 global / family-corrected 순서다. 각 family의 standardized winner raw statistic도 함께 보존한다.

| Family | Winner | Raw | Global z | IID p | Fixed-margin p |
|---|---|---|---|---|---|
| entropy | spacing/order1 | 0.028477897 | 1.910253983 | 0.630 / 1.000 | 0.560 / 1.000 |
| heldout | band/order3_alpha0.5 | -0.026817723 | 1.684086652 | 0.705 / 1.000 | 0.715 / 1.000 |
| transition | spacing/negative | 2.545422184 | 2.279146402 | 0.440 / 1.000 | 0.325 / 1.000 |
| word | spacing/L2_negative | 2.812584360 | 2.146390512 | 0.840 / 1.000 | 0.810 / 1.000 |
| forbidden | sum4/L4_rare_max_expected | 5.275554463 | 1.073992410 | 0.915 / 1.000 | 0.905 / 1.000 |
| run_lag | sum4/lag4 | 0.030721320 | 3.020580689 | 0.705 / 1.000 | 0.680 / 1.000 |

두 null에서 여섯 corrected p가 모두 **1.0**이다. **Symbolic memory는 null calibration을 통과하지 못했다.**

## 개발 global-max와 선택

| Family | Winner | Raw | Global z | IID p | Fixed-margin p |
|---|---|---|---|---|---|
| entropy | sum4/order3 | 0.237298432 | 0.980946578 | 0.965 / 1.000 | 0.950 / 1.000 |
| heldout | spacing/order3_alpha1.0 | -0.022347708 | 1.033623204 | 0.925 / 1.000 | 0.925 / 1.000 |
| transition | balance/negative | 2.403806418 | 2.614834066 | 0.240 / 1.000 | 0.220 / 1.000 |
| word | balance/L2_negative | 2.904601168 | 2.742542722 | 0.555 / 1.000 | 0.500 / 1.000 |
| forbidden | sum3/L4_rare_max_expected | 5.119105555 | 0.971516640 | 0.815 / 1.000 | 0.790 / 1.000 |
| run_lag | sum3/order1_surprise | 3.752849687 | 2.844970628 | 0.740 / 1.000 | 0.690 / 1.000 |

개발도 모든 corrected p가1이다. 선택 gate는 entropy/heldout 양쪽의 corrected evidence,
선택 cell의 방향상 유리한 evidence, lower-order 대비 .01nats 초과·training BIC 개선 및 validation3구간 양의 gain을 요구했다.
Gate가 실패했으며 실제 선택 encoding은 **없다**. 각 encoding의 개발 선택은 다음과 같다.

| Encoding | Selected order | Alpha | Dev logloss | Gain vs order0 | Training BIC0 |
|---|---|---|---|---|---|
| parity | 0 | 1.0 | 1.582955089 | 0.000000000 | 1278.435090440 |
| balance | 0 | 1.0 | 1.896593385 | 0.000000000 | 1560.407208197 |
| sum3 | 0 | 1.0 | 1.095838631 | 0.000000000 | 879.828791567 |
| sum4 | 0 | 1.0 | 1.384523820 | 0.000000000 | 1123.806087275 |
| range3 | 0 | 1.0 | 1.096949411 | 0.000000000 | 889.129623005 |
| range4 | 0 | 1.0 | 1.387458748 | 0.000000000 | 1120.808621279 |
| spacing | 0 | 1.0 | 1.771268801 | 0.000000000 | 1409.625414431 |
| band | 0 | 0.5 | 2.125992452 | 0.000000000 | 1779.000143381 |

`selected_configuration.json` hash는 `d8b946e584f555a9182a4800b27541833eb60af700992df3a86f069051fe6031`다.
그 파일의 `descriptive_best=balance`는 모든 order0 gain=0일 때의 이름순 tie 결과이며 encoding 우위를 뜻하지 않는다.
Support20/bin fit200은 사전 고정했고 later에서 다시 고르지 않았다.

## Entropy와 held-out Markov order

| Encoding | H0 | H1 | H2 | H3 |
|---|---|---|---|---|
| parity | 2.262427811 | 2.248184337 | 2.111539491 | 1.729305134 |
| balance | 2.744136911 | 2.652963512 | 2.274567330 | 1.448082560 |
| sum3 | 1.565297898 | 1.561101528 | 1.556160117 | 1.525910005 |
| sum4 | 1.992413725 | 1.985000923 | 1.963986175 | 1.827140659 |
| range3 | 1.581529632 | 1.580176040 | 1.567454986 | 1.542373287 |
| range4 | 1.994500824 | 1.991528540 | 1.972819080 | 1.842379174 |
| spacing | 2.514789414 | 2.486311517 | 2.382448627 | 1.750889877 |
| band | 3.073169985 | 3.014265225 | 2.451664735 | 1.164589988 |

Raw entropy reduction 최대는 `band/order3`의 1.908579998bits다.
Alphabet이 큰 sparse order3의 과적합 감소이며 동일 null도 같은 효과를 보인다.
표준화된 entropy winner는 spacing/order1 0.028477897bits지만 corrected p1이다.

개발의 가장 큰 raw higher-order gain은 `range3/order1_alpha1.0`의 -0.004571513nats,
later의 raw 최대는 `sum4/order1_alpha1.0`의 0.002711507nats다.
이후 최대값은 사후 모델 선택에 쓰지 않는다. Standardized heldout winner의 raw gain이 음수라는 점도 숨기지 않았다.

아래 later loss는 각 encoding에서 **개발이 고른 alpha**를 고정한 order0–3 과학적 비교다.
번호 predictor 성능표나 later best-order 재선택이 아니다. Order0/best lower-order gain과 BIC 전체는 `heldout_logloss.csv`에 있다.

| Encoding | Frozen alpha | Order0 | Order1 | Order2 | Order3 |
|---|---|---|---|---|---|
| parity | 1.0 | 1.580724179 | 1.590710600 | 1.614827040 | 1.624199778 |
| balance | 1.0 | 1.967784656 | 1.988677079 | 2.026657933 | 2.031396983 |
| sum3 | 1.0 | 1.078516358 | 1.078264878 | 1.085354734 | 1.095170782 |
| sum4 | 1.0 | 1.380710859 | 1.377999352 | 1.399233760 | 1.402758313 |
| range3 | 1.0 | 1.098151090 | 1.100988321 | 1.099765606 | 1.119288474 |
| range4 | 1.0 | 1.386855204 | 1.390820891 | 1.414761771 | 1.418641850 |
| spacing | 1.0 | 1.746872946 | 1.744837266 | 1.785670287 | 1.785670287 |
| band | 0.5 | 2.115876905 | 2.136635389 | 2.142694627 | 2.142694627 |

결론: history를 추가하면 fitted entropy는 줄지만, valid random history보다 재현 가능한 미래 symbolic uncertainty 감소는 확인하지 못했다.

## Transition과 higher-order word

Tail별 가장 강한 standardized transition은 다음과 같다. Common destination 빈도를 expected count로 제거했다.

| Tail | Encoding | Transition | Observed | Expected | Tail residual | z |
|---|---|---|---|---|---|---|
| positive | band | 0→2 | 65 | 46.559386973 | 2.702537492 | 1.099853254 |
| negative | spacing | 3→2 | 13 | 25.972222222 | 2.545422184 | 2.279146402 |

Full family winner는 `spacing`의 3→2,
count13/expected25.972222222다. Normalized transition evidence는 corrected p1이다.
Matrix·row entropy·row concentration·support는 `transition_matrices.csv`에 모두 있다.

Word family winner는 `spacing`, L2, word[3, 2],
count13/expected25.932369362, lift0.501303981, deviance tail residual2.812584360다.
**길이3/4만의 가장 큰 standardized candidate**는 `range4`, L4, word[1, 0, 3, 1],
count12/expected5.270804356, lift2.276692359, tail score2.507384451, z1.891630935다.
전체 word-family corrected p1로 반복 가능한 word rule 근거가 없다. 모든47,274word의 count/expected/lift/deviance/support를 `word_counts.csv`에 저장했다.
L2 baseline은 order0, L3/4 baseline은 smoothed order1이다.

## Forbidden/rare와 run/lag

| Encoding | Supported L2 | Supported L3 | Supported L4 | Supported missing total | Supported count<=1 total |
|---|---|---|---|---|---|
| parity | 26 | 66 | 48 | 0 | 0 |
| balance | 37 | 36 | 11 | 0 | 0 |
| sum3 | 9 | 27 | 81 | 0 | 0 |
| sum4 | 16 | 64 | 51 | 0 | 1 |
| range3 | 9 | 27 | 81 | 0 | 0 |
| range4 | 16 | 64 | 40 | 0 | 1 |
| spacing | 36 | 77 | 0 | 0 | 0 |
| band | 80 | 15 | 0 | 0 | 0 |

Supported missing word는 전체에서 **0개**였다. 대부분의 raw absent word는 expected/support 부족이며 deterministic forbidden pattern으로 해석하지 않는다.
Full forbidden winner는 sum4/L4 rare max expected=5.275554463이며 count<=1인 supported word다.
Corrected p1이다. Spacing/band의 L4는 지원 부족0개여서 그 길이의 rule이 없다고 단정하지 않는다.

Run/lag family winner는 sum4 lag4 recurrence excess 0.030721320,
z3.020580689, corrected p1이다.
Run length 분포·longest·order0/1 expected run tail·transition-away probability는 `run_summary.json`에 있다.
Longest run이나 related concentration state를 근거로 새 symbol grouping을 추가하지 않았다.

## Temporal stability와 encoding agreement

고정 spacing3→2 transition을 early201–548/middle549–896/recent897–1245에 적용했다.

| Era | Start | End | Observed | Expected | Residual | Supported |
|---|---|---|---|---|---|---|
| early | 201 | 548 | 4 | 9.365994236 | -1.753368737 | True |
| middle | 549 | 896 | 8 | 8.965417867 | -0.322426006 | True |
| recent | 897 | 1245 | 1 | 7.459770115 | -2.365126319 | True |

W208/stride52/final endpoint의 값과 support flags는 `transition_stability.csv`다.
고정 word winner의 세 era/rolling 결과는 `word_stability.json`에 있다.
검정되지 않은 유리한 era/window를 새 evidence로 세지 않는다.
Sum3/4, range3/4 같은 correlated encoding은 `representation_agreement.csv`의 descriptive normalized MI로 비교했다.
이를 독립적인 여러 증거로 합치지 않았다.

## 모델·평가·prospective 결정

- SymbolicContextModel: **NOT JUSTIFIED**, DirectContextNumberModel: **NOT IMPLEMENTED / NOT JUSTIFIED**.
- Number walk-forward Top6/hit distribution/Recall@6·10·15/mean winning rank/Top8·10·12·15>=5,
  Random/Frequency26/Gap Logistic 비교와 paired block-bootstrap은 해당 없음. 정당화된 모델을 강제로 만들지 않았다.
- Gap/Graph/GapShape/Mirror와 Spearman·Top6/10/15 overlap도 신규 ranking이 없어 해당 없음.
- **ENSEMBLE: NOT CURRENTLY JUSTIFIED**. Final H17을 만들지 않았다.
- **PROSPECTIVE_ARCHIVE_STATUS = VERIFIED**: 기존30files와12recorded SHA-256은 시작·끝 모두 일치했다.
- **PROSPECTIVE_CAPABILITY_NOT_CREATED_NO_JUSTIFIED_MODEL**. `draw1247_phase25_symbolic` 기능·실제 snapshot은 생성하지 않았다.
- Target1246 거부·archive integrity failure prospective 거부를 테스트했다. 실제 snapshot의 자동 발행은 전혀 없었다.

## Tests·audit·제한

Phase25 전용 **19passed**: 모든 encoding, deterministic symbol/support, development-only bins,
order0/1/2/3·smoothing·conditional entropy·손계산 held-out loss·BIC selection,
word enumeration/terminal prefix/forbidden/runs/lags, synthetic order1/order2 recovery·IID rejection,
surrogate rebuilding/global-search parity/determinism, development-only selection, draw1246suffix/target 거부 등을 확인했다.

전체 `python -m pytest -q`: **4 failed, 1226 passed, 2 skipped in 143.03s (0:02:23)**.
실패4건은 시작 시에도 재현된 기존 complexity/RMT/recurrence/topology parallel-equivalence tests의
**Windows named-pipe PermissionError / WinError5**다. 기존 source/tests를 바꾸거나 skip 처리해 숨기지 않았다.
전체 suite가 green이라고 주장하지 않는다. 원본 결과는 `full_tests.log`, 시작 재현은 `windows_baseline_tests.log`다.

독립 reviewer의 중요 지적2건(pilot-constant cells 제외/terminal prefix support)을 실패 테스트로 재현한 뒤 수정했다.
기존 pilot은 `pre_review_calibration/`에 보존하고 동일64seeds를 다시 생성했다. Main은 수정 뒤 시작했다.
304cell raw/std/unit-fallback 참여와 수정 후 회귀 테스트를 reviewer가 독립 확인했으며 남은 important 지적은 없다.
Export eligibility 열 충돌도 별도 실제 CSV/NPZ export test로 방지했다.

Audit통과:64pilot/대표8main seed replay,796raw vectors의 own-max와24global-p/796maxima rows 재계산,
dictionary 기반의 모든 encoding/target/order/alpha prequential probability 독립 대조,
word code literal enumeration, selection hash, 409protected existing file hashes,
archive30file hashes 및 HEAD 불변. 모든398main history를 두 번째 생성한 검증은 아니다.
Fixed-margin finite mixing,32pilot scale 추정·unit fallback 선택, p해상도.005, initial200학습 비용,
sparse alphabet에서 제한된 word support, 미검정 encoding에 대한 일반화 한계가 남는다.

## 출력·정확한 변경 파일

`reports/symbolic/plots/`의11PNG: symbol frequency, order1 matrices, entropy/order, heldout loss/order,
transition residual, word anomaly, runs/null, IID global-max, fixed global-max, temporal stability, descriptive encoding agreement.
전체 plot을 contact sheet로 시각 점검했다. 모델이 없어 predictive-ranking plot은 해당 없다.

- `.gitignore`
- `README.md`
- `docs/README.md`
- `docs/research-ideas.md`
- `docs/superpowers/plans/2026-10-18-phase25.md`
- `docs/symbolic-analysis.md`
- `docs/symbolic-results.md`
- `src/analysis/symbolic.py`
- `src/analysis/symbolic_diagnostics.py`
- `src/analysis/symbolic_search.py`
- `src/cli.py`
- `src/symbolic_cli.py`
- `tests/test_symbolic.py`
- `tests/test_symbolic_cli.py`
- `tests/test_symbolic_diagnostics.py`
- `tests/test_symbolic_search.py`

Generated output 전체 경로·SHA-256은 `reports/symbolic/output_inventory.json`, 변경 목록은 `changed_files.txt`다.
Raw data·이전 Phase별 source/결과 문서·prospective 원본은 수정하지 않았다.
**Draw1246미사용 / 자동 fetch·import없음 / 자동 prospective 발행없음 / commit없음 / push없음**.
H25 Integrated randomness battery는 미시작, H17 final ensemble은 H25 완료까지 유보다. Phase25에서 종료한다.
