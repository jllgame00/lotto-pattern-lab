# Regime, Bayesian and ensemble research implementation plan

> Implement inline using executing-plans and test-driven-development. No second commit.

Goal: compare different statistical assumptions without relaxing the retrospective seal.
Architecture: new models use the existing fit/score_rows contract and canonical causal
features. A batched implementation fits independent small Bernoulli HMMs. Ensembles
consume previously emitted scores, never refit component models on evaluation labels.
Stack: existing NumPy, SciPy, pandas, matplotlib, pytest.
Spec: user's Phase 4 sections A-P in this session.

Protocol fixed before results: targets601-1244; cadence26; development601-900;
later evaluation901-1244. Robustness starts501/701 and cadence13, retaining
the same settings. Beta prior(2,13), recency half-life52; hazard prior strength75;
HMM states2/3, trailing260 labeled draws, two seeded initializations, maximum40 EM
iterations, transition pseudocounts diagonal8/off-diagonal1, emission prior(2,13).
These are conservative choices, not optimized settings. HMM training begins with
the shared supervised series at draw105. No actual1245 data is read in this work.

- [x] 1. tests/test_regime_models.py: verify hazard bins/smoothing, Bayesian algebra,
  causal online updates, seal, numerical forward recursion against enumeration,
  HMM deterministic fitting, transition normalization and minimum observations.
  Implement src/models/hazard.py, bayesian.py, bernoulli_hmm.py, regime.py.
- [x] 2. tests/test_ensembles.py: normalization ties, frozen development weights,
  strict split and evaluation-label invariance. Implement src/models/ensemble.py.
- [x] 3. tests/test_prospective.py: immutable exclusive writes, complete snapshot,
  bounded local loading, no network, no future rows. Implement src/prospective.py.
  This separate command may use local canonical1245 only when explicitly invoked;
  it is not run on the actual dataset in this phase. Synthetic fixtures verify it.
- [x] 4. src/regime_cli.py and src/analysis/regime_research.py: commands, hazard eras,
  independent comparisons, frozen ensemble ablations, null HMM diagnostics,
  parameter/init stability, causal-state/periodicity relationships, selected plots.
  Reuse existing ranking/candidate/portfolio reports. Test CLI on synthetic data.
- [x] 5. Run full tests, actual sealed-prefix experiment, review, document numerical
  results/limitations/dependencies/runtime. No conclusions from isolated prizes.

Review focus: sequential state updates cannot skip missing observations; filtered
probabilities must not use smoothing with future observations; normalization handles
constant scores; ensemble weights never use later labels; prospective reads bounded
by fixed canonical cutoff and never overwrites snapshots or source data.

Checkpoint: existing clean HEAD5b66beed885de7ee4d240e06100e474c03609497 already has
the requested checkpoint message.114passed2skipped13.25s. Push refused by proxy
127.0.0.1:9. No duplicate commit or history modification.
Ruling: work in requested workspace, preserve existing defaults and all old outputs;
use separate reports/regime_research. No further commits per user instruction.
Ruling: later evaluation is untouched by this ensemble's weight selection only;
prior research examined it, so it is not a pristine holdout.

Progress: initial full suite128passed2skipped20.21s. Added causal prefix/refit and
synthetic strong-regime tests. Independent review found no important mathematical
or leakage defect; exact enumeration reproduced one EM step within2.78e-17.
Provenance fallback fix: missing Git now records unknown dirty status, not false;
regression failed before fix and passes afterward. This small fix is necessary
for truthful snapshot provenance. No actual canonical freeze command executed.
Retrospective/prospective policy parity is intentionally not claimed; distinct
observation origins and fixed snapshot model subset are documented explicitly.

Final verification:136passed2skipped21.67s; compileall and git diff--check pass
(line-ending advisories only). Default historical run291.34s. Independently
reconstructed9660 individual and10320 later rankings,48300+51600 pool counts,
all251808 budget rows,57960 state probabilities, and27 rare-event classifications
against the bounded open prefix. Source hash matches; no actual1245 read.
Plots for7/17/34 generated;17 visually inspected. Reports and full methods/results
in docs/regime-research.md. No model or ensemble establishes a reliable advantage.
No second commit. The prospective capability was tested only with synthetic data.
Review disposition: actual report checks performed by parent; separate policy
parity and inability to verify unseen status are explicit documented limitations.
No unresolved reviewer findings.
