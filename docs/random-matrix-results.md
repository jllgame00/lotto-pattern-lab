# Phase22 / H21 — Random Matrix Theory / collective number modes 결과

## 최종 결정

**H21: TESTED / INCONCLUSIVE.** 실제 Lotto correlation 구조에 valid random Lotto history보다 강하고 안정적인 collective mode가 있다는 corrected evidence를 확보하지 못했다. Localized mode와 몇몇 rolling peak가 보였지만 전체 검색/가족 보정을 통과하지 못했다. 무작위성이나 collective structure의 부재를 수학적으로 증명한 결과는 아니다.

**PREDICTIVE_MODEL_NOT_JUSTIFIED.** SpectralFactorModel/SpectralResidualModel을 만들지 않았다. RandomModel/Frequency26/Gap Logistic/Graph와의 predictive walk-forward,paired predictive bootstrap,후보 모델 rank correlation은 해당되지 않아 실행하지 않았다. Ensemble은 **NOT CURRENTLY JUSTIFIED**이며 H17 final ensemble은 만들지 않았다. H22–H25도 시작하지 않았다.

**Prospective capability: NOT CREATED — NO JUSTIFIED PREDICTIVE MODEL.**

**PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION**

방법은 [RMT 분석](random-matrix-analysis.md),사전 고정 규칙과 개발 gate는 [계획](superpowers/plans/2026-10-18-phase22.md)에 있다.

## Workspace / 실행 범위

- Git root: `C:/Users/Samsung/OneDrive/Desktop/university/personal/lotto-pattern-lab`.
- 시작 branch `main`,SHA `06c17aa62e8adf1e47e1421cac96d6e04c3e6b90`,status clean. Phase21/H20 완료와55개 artifact hashes를 먼저 확인했다. 무관한 source/data 변경은 없었다.
- 실제 본번호1–1245회만 사용했다. Bonus 제외,45binary columns,row합6.1246 fetch/import/use/design/eval 없음.
- 개발1–900와전체1–1245를 독립 calibration/null scope로 사용했다. 이후901–1245의 predictive evaluation은 gate 실패로 수행하지 않았다.
- 기존 tracked377files 및data/prior reports606files를 시작 baseline에 기록했다. 공용 roadmap/CLI/ignore 변경 외의 기존 source/docs/data/reports는 hash로 보호한다.
- Independent IID32pilots×2scope(seed221001),main IID199+fixed199×2scope(seed220042),workers3. 모든 null은 자기 matrix/constraint/window/rank/lag/search를 새로 구성했다. 총796scope-search다.
- 본 experiment runtime **224.379687초**. Benchmark serial 추정406.471520초는 실제3worker runtime과 구분한다.

## Matrix / zero mode / search space

Primary는 interval-local sample correlation45×45,secondary는 sample covariance(ddof1)다. Correlation의 구조 nullvector는 sample_std이고 covariance는ones다. Active coordinates에서 이 방향의 직교여공간으로 제한해44개의 비자명 mode를 구했다. 구조적 zero를 작은 eigenvalue anomaly로 세지 않았다. Zero-variance column 처리는 별도 tests로 검증했다.

W={104,208,416,624},stride104,마지막 cutoff 포함. Leading r={1,2,3,5},same-W endpoint index separation k={1,2,4},three nonoverlap era,full-scope lag L={1,2,4,8,13}다. Lag matrix는 비대칭이므로 SVD를 사용했다. Covariance에 별도 primary hypothesis를 추가하지 않았다.

|family|full1–1245|development1–900|
|---|---:|---:|
|largest|40|28|
|smallest|40|28|
|localization|1760|1232|
|rolling concentration|156|108|
|subspace stability/recurrence|372|228|
|lagged secondary|75|75|
|합계 / eligible|2443 / 2443|1699 / 1699|

Rolling fits는 full39/dev27개다. Whole/세era까지 포함하면 각scope43/31개의 correlation/covariance fit이 저장됐다. Null마다 완전히 같은 inventory를 사용했다.

## Whole-history spectrum

|quantity|correlation primary|covariance secondary|
|---|---:|---:|
|largest nontrivial eigenvalue|1.393598268|.163374474|
|smallest nontrivial eigenvalue|.700221477|.079374064|
|spectral entropy|3.768519198|3.767029394|
|effective rank|43.315875083|43.251390979|
|leading explained variance|.030968850|.031411888|
|structural-direction residual norm|3.0754e−15|4.1793e−16|

Correlation 상위5eigenvalues는1.393598268/1.353367002/1.305281768/1.293223707/1.279179954다. 전체44개,spacing,cumulative explained variance,IPR/PR는 `spectrum_rows.csv`와 `diagnostics.json`에 있다. Leading mode IPR=.057179216,PR=17.488872로 여러 번호에 걸쳐 있다. Inspection용 상위 loading 번호는21/40/10/33/11/39/24/3/5/17이다. 안정된 번호 집단이라는 뜻이 아니다.

Effective q=.035369775의 descriptive MP bulk는[.674215261,1.443586552]였다. Whole spectrum은 그 안에 있지만 MP 경계 자체로 과학적 결정을 내리지 않았다. Whole λ1을 largest-family own global maxima와 비교하면 양 null에서global/corrected p=1이었다.

Trace-normalized covariance/correlation spectrum의 최대 차이는.000664690,leading5projector overlap=.822529965였다. Broad spectral shape는 scaling에 크게 달라지지 않았으나 개별 mode가 같은 것은 아니다(최대 principal angle=.950412217rad). Covariance whole λ1의 matching-null median은 IID=.162338999,fixed=.161085754,centered+.001035475/+.002288719,percentile=.648241206/.778894472였다. 이는 secondary descriptive 비교이며 covariance를 별도로 유의하다고 주장하지 않는다.

## 강한 개별 spectral 예시

|family winner|interval/config|raw statistic|pilot z|
|---|---|---:|---:|
|largest eigenvalue|W104,729–832|λ1=2.678947049|3.186245480|
|smallest anomaly|W104,1–104|λ44=.141750969 (검색은−λ44)|.942310827|
|localization|W416,729–1144,mode31|IPR=.156765688,PR=6.378946908|10.313939295|
|rolling concentration|W104,729–832,r1|.059532157|3.186245480|
|stability/recurrence|W104,r1,1–104 vs209–312,k2|overlap=.144101185|5.517184332|
|lagged secondary|lag1,left singular mode3|IPR=.085420735|3.231792352|

Mode31의localized loading 상위 번호는27/45/32/44/42/8/23/36/7/29였다. Inspection용이며 leading outlier나 안정된 semantic group으로 승격하지 않는다. 특히 bulk의 near-degenerate mode IPR는 numerical basis에 의존한다.

Raw rolling concentration의 최댓값은같은W104/729–832의r5=.252642409였다. Raw subspace overlap 최댓값은W624/r3의.809308322였지만 이는 크게 겹치는 창이며 standalone evidence가 아니다. Family winner는 cell별 pilot 표준화 뒤의 최대값으로 선택한다.

## IID / fixed-margin global-max / corrected p

각 null199회,p=(1+exceedances)/200,여섯 family Bonferroni6이다. Lagged는 scientific 해석상 secondary이나 같은 보수적6family correction에 포함했다.

|family|IID global p|fixed global p|IID corrected p|fixed corrected p|
|---|---:|---:|---:|---:|
|largest|.210|.190|1|1|
|smallest|1|1|1|1|
|localization|.080|.055|.480|.330|
|concentration|.315|.270|1|1|
|stability|.400|.375|1|1|
|lagged secondary|.695|.620|1|1|

큰 z값도 corrected discovery가 아니었다. Localized mode의 matching-cell null median은 IID=.060720436,fixed=.061003002이며 centered+.096045251/+.095762686,percentile은모두1이었다. 그러나 각 surrogate가1760localization cells에서 자기 최대를 찾도록 하면global p=.080/.055로 올라가며 correction 후 .480/.330이다.

W104 λ1의matching-cell median은2.417657186/2.415811143,centered+.261289863/+.263135906였다. Cell percentile은.994974874/.989949749여도 전체40largest 검색의global p는.210/.190이다. Stability winner의cell percentile도양null1이지만372cell own-global 비교는.400/.375였다. 모든2443cell의 finite-sample table을 저장했다.

## 시간 안정성과 lagged singular spectrum

Full의세 era pair overlap 최솟값은r1=.000464419,r2=.012467196,r3=.032014675,r5=.072930356이었다. 개발에서는.001902417/.021561098/.064240502/.096512381이었다. 동일한 leading number span이 장기간 유지된다고 주장할 corrected evidence가 없다. Sign flip은 불안정성으로 세지 않았고,rank 경계를 가로지르는 near-degeneracy의 회전 가능성도 제한으로 남긴다.

|lag|largest singular value|
|---|---:|
|1|.348448206|
|2|.366324138|
|4|.378993865|
|8|.360354115|
|13|.377019684|

Raw largest SV는lag4의.378993865다. 이cell 자체를 lagged-family null own maxima와 비교한global/corrected p는두null 모두1이었다. 위 family table의.695/.620은lag4 SV가 아닌lag1 left-mode3 IPR라는 **전체 lag family winner**에 대응한다. 비대칭 matrix에 ordinary eigenvalue 분석을 하지 않았다.

## Phase14 Graph와의 관계

기존 manifest hash가 맞는 `structural_cache.npz`만 읽었다. Graph의W104에서 정확히 일치하는11endpoint를 사용했고 Graph를 fit/retune하지 않았다. Leading |loading| 대 node strength의Spearman은−.314690..+.228433,중앙값−.022651이었다. Top6 overlap 평균은.727273이었다. 저장K2/K3 communities에 leading5leverage mass를 비교한55개 기술적 행의size-adjusted absolute excess 최댓값은.084819였다.

뚜렷하고 일관된 Graph–RMT number grouping 대응을 확인하지 못했다. 이는검정/예측결론이 아니라 기술적 관찰이다. Node strength=5×frequency이므로 그상관은 frequency 관계를 포함한다. Graph의과거ensemble-candidate 판정을 바꾸지 않았다. RMT predictor가없어 Graph/Gap/GapShape/Mirror predictive rank 상관도계산하지 않았다.

## 개발 결정과 예측 생략

|개발 family|IID global / corrected|fixed global / corrected|
|---|---:|---:|
|largest|.245 / 1|.290 / 1|
|smallest|1 / 1|1 / 1|
|localization|.860 / 1|.845 / 1|
|concentration|.370 / 1|.385 / 1|
|stability|.290 / 1|.270 / 1|
|lagged secondary|.845 / 1|.835 / 1|

Required whole leading-mode cell과모든r의nonoverlap-era-min cell은각각양nullglobal/corrected p=1이었다. 따라서whole_leading_mode_passed=false,stable_ranks=[]다. Selection SHA256은 `398980049fcb9b13fa25a030f865f4a35c9db2f81c2b491ace72ba3e87db2eb3`이다. 이후901–1245를model selection에쓰거나무의미한예측모델을강제로만들지않았다. **PREDICTIVE_MODEL_NOT_JUSTIFIED / NOT CURRENTLY JUSTIFIED**다.

## 검증과 산출물

전체suite는 **1133 passed,1 skipped,0 failed**,291.72초였다. 신규Phase22 tests50개는모두통과했다. Skip은기존 `tests/test_predictive_models.py:52`의optional LightGBM/XGBoost 미설치다. 수학25tests,검색6tests,초기pipeline7tests의RED를관찰하고구현했다. 독립review가발견한orphan partial-output 덮어쓰기위험은9개회귀실패→preflight수정후성공으로검증했다. 추가gate fixture는유의한rolling winner가실패한필수whole/era-min cell을구제하지못함을검증했다.

64pilots를모두exact replay하고8개의IID/fixed 첫/마지막replicate×scope complete search/raw spectra를seed로재생성했다. **796개저장null vector전부를 독립 standardization→own maximum→global p→family correction으로감사했다.** 실제모든43/31interval의corr/cov eigenvalues는projected helper와별도의45좌표eigvalsh로검증했고모든lag SVD도독립재계산했다.398개원래history를전부두번생성했다는주장은하지않는다.

`reports/random_matrix/plots/`의11개PNG는 correlation,spectrum/MP,real-vs-IID,real-vs-fixed,leading loadings,IPR,rolling largest,subspace stability,frozen Graph comparison,lagged singular spectrum,covariance sensitivity다. Predictive ranking plot은모델이없어해당하지않는다. 그림은inspection aid이며검정을대신하지않는다.

Canonical raw-byte SHA256은 `3b7bb1e0a37c28ae4b4a97e098180d8407008ec007698c191ed6cf279db8225b`로불변이다. 기존Phase21이하수치/문서/산출물을보존했다. 정확한변경파일과산출물hash는 `reports/random_matrix/manifest.json`,검증상세는 `audit_result.json`,`test_result.json`,`review_result.json`에있다. 과거prospectivearchive는없으므로원본파일의byte검증을주장하지않는다.

변경파일은18개다.

```text
.gitignore
README.md
docs/README.md
docs/research-ideas.md
docs/random-matrix-analysis.md
docs/random-matrix-results.md
docs/superpowers/plans/2026-10-18-phase22.md
src/cli.py
src/random_matrix_cli.py
src/analysis/random_matrix.py
src/analysis/random_matrix_search.py
src/analysis/random_matrix_diagnostics.py
src/analysis/random_matrix_audit.py
tests/test_random_matrix.py
tests/test_random_matrix_search.py
tests/test_random_matrix_cli.py
tests/test_random_matrix_diagnostics.py
tests/test_random_matrix_audit.py
```

실제1246을fetch/import/use/evaluate하지않았고,canonical CSV/이전prospectiveevidence를수정하지않았다.1247 snapshot발행,commit/push없음. Phase22에서종료한다.
