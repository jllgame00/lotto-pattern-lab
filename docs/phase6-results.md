# Phase 6 — 2D Translation 결과

## 결론

H3는 **TESTED / INCONCLUSIVE**입니다. 전체 null-search 보정 후 구조와 안정적 예측 우위를 확립하지 못했습니다.

## 가설

번호축과 회차축을 함께 이동하는 패턴이 무작위 자료보다 강하고 다음 회차 예측에도 유용한지 검증했습니다.

## 데이터 및 검증 범위

ordered number label의 translation을 시험했습니다. canonical 1–1245회,1,245×45 binary 본번호 matrix, row별 six ones입니다. 당시 SHA-256은 `b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e`입니다. 당시1246 이후 결과를 가져오거나 확인·평가하지 않았고 Phase 5 파일·registry hash를 보존했습니다. 당시 commit/push는 없었습니다.

## 방법과 주요 결과

최강 raw shift는(+42 draws,-5 numbers),960 matches/6,426 opportunities, rate .149393, IID .133333, lift1.120448, z 3.787162입니다. 다음은(+1,+8),895/6,131과(+38,+14),731/4,969입니다. 전체 과거에서 선택한 탐색 결과이며 backtest에 소급 적용한 rule이 아닙니다.

(+42,-5) rate는1–415에서 .152827,416–830에서 .146293,831–1245에서 .147117입니다. 같은 부호도 selection-biased 기술값이며 corrected test는 inconclusive입니다. rolling260과 top10 era table을 export했습니다.

최장 maximal chain은7 points입니다. 예:873/number3→903/21의(+5,+3),280/37→334/13의(+9,-4)입니다. 398 surrogate 모두 같은 길이 이상이며 random longest 평균은 약7.8입니다. overlapping subchain은 독립 발견이 아닙니다.

Hough 최대는(+9,-2),23 positions 중12, density .521739, draw 498/45→696/1입니다. raw z 5.479667은 전체 surrogate 탐색에서 보통입니다. 2D spectral maximum .0003561도 두 null에서 보통입니다.

## Null / surrogate 비교

| Search statistic | IID global p | Fixed-margin global p | IID six-family adjusted p | Fixed-margin adjusted p |
|---|---:|---:|---:|---:|
| Shift | .055 | .080 | .330 | .480 |
| Directional asymmetry | .285 | .255 | 1 | 1 |
| Chain-count score | .650 | .635 | 1 | 1 |
| Longest chain | 1 | 1 | 1 | 1 |
| Hough line | .375 | .405 | 1 | 1 |
| Spectral concentration | .795 | .725 | 1 | 1 |

각 null199 histories, seed 60042이며 matrix cell 평균 약23.1%가 바뀌었습니다. exact-margin은 row sums·number frequencies를 보존하나 finite mixing 한계가 있습니다. 보정 후 통과 family는 없습니다. 제한된 탐색의 근거 부재이지 모든 구조 부재의 증명은 아닙니다.

## Walk-forward 결과

설정은 사전 선언했습니다. development 401–900, later 901–1245, cadence 26입니다. earlier Phase가 사용한 history라 later도 pristine holdout이 아닙니다. interval은2000-replicate26-draw circular block bootstrap이며 많은 비교를 보정하지 않았습니다.

| Model | All401–1245 avg Top6 | Later901–1245 avg Top6 | Later difference vs Random | Paired95% interval |
|---|---:|---:|---:|---|
| Uniform Random | .802367 | .768116 | 0 | baseline |
| Translation | .815385 | .776812 | +.008696 | [-.092754,.107246] |
| Chain | .794083 | .834783 | +.066667 | [-.043478,.171087] |
| Fixed equal-rank combination | .841420 | .823188 | +.055072 | [-.043478,.168116] |
| Existing Gap Logistic | .842604 | .823188 | +.055072 | [-.046449,.168116] |

| Model, later period | Winning-number mean rank | Recall@6 | Recall@10 | Recall@15 |
|---|---:|---:|---:|---:|
| Random |22.9585|.128019|.219807|.336715|
| Translation |23.0444|.129469|.219324|.316425|
| Chain |22.7884|.139130|.225604|.326570|
| Combination |22.8744|.137198|.222222|.336232|
| Gap Logistic |23.0478|.137198|.218357|.330918|

start401/501/601/701/801/901의 primary hit interval은 모두 zero를 포함합니다. early/middle/recent는 Translation .8546/.8298/.7616, Chain .7482/.8121/.8221입니다. cadence 13 later는 Translation .7681, Chain .8029, combination .8116, Gap Logistic .8203, Random .7681이며 모두 paired interval이 zero를 포함합니다.

later ablation은 Translation positive .7594·negative .8522·short .8638·long .7623, Chain .8406/.8029/.7739/.8087입니다. 모두 zero를 포함하므로 evaluation을 본 뒤 최고 ablation을 prospective 모델로 승격하지 않았습니다.

## Candidate-pool / prize-aware 결과

전체845 targets에서 본번호5개 이상 포함한 pool 수입니다.

| Model | Top8 | Top10 | Top12 | Top15 | Top15 all6 |
|---|---:|---:|---:|---:|---:|
| Random |0|0|2|8|0|
| Translation |0|0|1|5|0|
| Chain |0|1|1|3|1|
| Combination |0|0|2|7|0|
| Gap Logistic |0|2|5|10|0|

Chain의 Top15 all-six는 development draw 466입니다. pool event이며 실제 six-number ticket prize가 아닙니다. uniform ranking의845 targets 기대는 Top15 >=5 약9.87·all-six .519입니다. 여러 탐색 중 한 all-six가 예측력의 증거는 아닙니다.

later 345 targets의 Top15 >=5는 Translation3·Chain1·combination3·Gap3·Random0, Top12는1/0/1/1/0, Top10은0/0/0/1/0, Top8은 모두0입니다. all-six도 없습니다. seeded Random zero는 random probability zero가 아닙니다. exact >=5는 Top8 .000258,Top10 .001109,Top12 .003322,Top15 .011675입니다. export는 full0..6·>=3/4/5/6·exact reference·marginal/paired interval을 포함하며 all-zero 퇴화를 flag합니다.

## 검증과 runtime

당시 전체 regression은 synthetic path·exact margins·full-search maximum·두 모델 target poisoning·기존 Gap Logistic 동일성·deterministic portfolio·immutable publication·registry corruption을 검증했습니다. **183 passed,2 dependency-related skipped**,48.78 seconds였습니다.

199+199 search는 다른 작업과 병행해 raw 첫 export부터 마지막 null까지 약465.5 seconds였습니다. plot-label 오류는 재현·수정하고 saved search로 render했으며 null 재선택은 없었습니다. cadence 26은108.9 seconds, cadence 13은85.6 seconds였습니다. pool interval 확장은 saved prediction에서 계산하고 prediction은 바꾸지 않았습니다.

## Prospective experiment

당시 Translation·Chain·사전 equal-rank combination을 독립 동결하고 full score/rank·fixed-seed Top12 portfolio를 보존했습니다. development combination .854가 component 점추정치보다 높아도 검증된 우위가 아니며 실험 track입니다. exact portfolio·configuration·rules·source/hash는 원본 manifest/JSON에 있습니다. Phase 5는 바꾸지 않았고 prospective 결과는 평가하지 않았습니다.

## 해석

출력 경로는 `reports/spatiotemporal/global_null_comparison.csv`, `surrogate_maxima.csv`, `walk_forward_26/`, `walk_forward_13/`, `plots/`입니다. [방법](spatiotemporal-analysis.md)과 함께 읽습니다. H3는 **TESTED / INCONCLUSIVE**입니다. 당시 후속 H4의3D는 아직 구현 전이었으나 현재는 [Phase 7 완료 결과](phase7-results.md)가 있습니다. 현재1246회는 알려진 결과이며 아래 원본의 FROZEN_UNEVALUATED는 당시 상태입니다. 원본 파일 가용성은 [현재 workflow](prospective-workflow.md)를 참고합니다. 아래 frozen record 구역은 byte-for-byte 보존합니다.


## 한계

ordered label의 의미, 중첩된 탐색, finite mixing과 기존 역사 구간 재사용이 한계입니다.

## 다음 단계

H3의 완료 상태를 유지합니다. 후속 H4는 이미 Phase 7에서 검증했으며 아래 동결 기록은 당시 원문으로 보존합니다.

## Frozen experiment record

Created2026-10-17T08:12:26.305582+09:00, target1246, cutoff1245,
Git`6ce221ce15fb1c8996a1a8b134811b202d16d646`, intentional dirty Phase6 working tree.
Status: **FROZEN_UNEVALUATED**.

- Experiment:`draw1246_phase6_2d_20261017T081226305582_3b783b3c`
- [Snapshot](../reports/prospective/phase6/draw1246_phase6_2d_20261017T081226305582_3b783b3c.json)
  SHA-256:`eda0f22b15f11d967484849391779de5187faf6c420e71052b9e48d7c82c5d01`
- [Manifest and exact ticket portfolios](../reports/prospective/phase6/draw1246_phase6_2d_20261017T081226305582_3b783b3c_manifest.md)
  SHA-256:`4def791e4a57e8ed802529a50a221d414523da7a3d5059b76b50a241c05c5b9b`
- [Integrity record](../reports/prospective/phase6/draw1246_phase6_2d_20261017T081226305582_3b783b3c_integrity.json)
  SHA-256:`a9392735ad80ea2122082521138816c36f280305fd57e241ddf5a7a6607f46c0`
- [Separate Phase6 registry](../reports/prospective/phase6/registry.csv)

Full ranked Top15 lists (Top6/8/10/12 are their respective prefixes):

- Translation:`3,11,38,8,41,39,40,23,13,17,25,36,26,28,12`
- Chain:`25,45,14,5,15,2,39,37,1,3,4,6,7,8,9`
- Combination:`25,39,3,11,37,38,15,8,41,45,40,23,13,14,17`

Exact ties use smaller number first; tied positions are not evidence of stronger
model preference. In particular the Chain ranking has a large tied baseline
group. Full score vectors and tie groups are preserved in the snapshot. No
model or portfolio was redesigned after inspecting these frozen rankings.

The Phase5 snapshot, manifest, integrity record, reservation and registry were
all verified byte-for-byte unchanged after publication. Canonical hash is also
unchanged. No result for1246 or later was retrieved, inspected, or evaluated.
