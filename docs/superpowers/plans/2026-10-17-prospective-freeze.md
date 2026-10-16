# Phase5 prospective freeze implementation plan

Goal: freeze six independently declared tracks for target1246 from source1-1245,
then leave the experiment immutable and unevaluated. No retrieval, commits or pushes.
Architecture: preserve retrospective boundaries; a frozen prospective scope
allows unchanged shared features/models to fit only through the declared local
cutoff and score only its successor. Version2 artifact writing and offline
evaluation live separately from the existing version1 snapshot helper.
Execution: inline using executing-plans, test-driven development, final review.
Spec: user's Phase5 steps1-12 and final execution in this session.

Entry verification: clean HEAD2ee5da879fe7d53be95191ac4d55782551b1f6c5;
136passed2skipped37.88s. Canonical1245 rows,last date2026-10-10;
SHA256 b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e
matches committed blob and provenance metadata. No1246 read or network access.

Fixed protocol BEFORE rankings:
- Tracks: GapLogistic, BayesianStatic, HMM2, HMM3, existing development-weight
  ensemble, UniformRandom control. Ensemble component scores/configs also saved.
- Refit components once at1245 using existing supervised rows105-1245 and
  unchanged canonical feature definitions; no change of model formulas/parameters.
- Bayesian track is existing historical static adapter, Beta(2,13), supervised
  observations105-1245 (not legacy version1 snapshot's draw1 policy).
- Load existing nine-component rank-average weights selected on601-900:
  GapLogistic.2 and each other component.1. Validate and hash source file; never
  rerun weight selection. If source/model unavailable, report and abort freeze.
- Seed42 throughout. Random ranking: uniform seeded permutation of45 tied scores.
  Random unrestricted portfolios: existing uniform_portfolio(20,seed42), prefixes.
- Gap/ensemble direct deterministic Top6 ticket; weighted and coverage methods
  each generate one ordered20-ticket Top12 portfolio, budget5/10/20 are prefixes.
  Also retain budget1 prefixes for exact method/budget comparisons. No selection
  among alternative seeds or portfolios. Controls1/5/10/20 from one uniform list.
- Full45 scores/rank, all exact tie groups/rules, Top6/8/10/12/15 for every track.
- New unique snapshot/manifest/integrity filenames, SHA256 for JSON and manifest,
  append-only registry with FROZEN_UNEVALUATED. No silent overwrite. Fail if
  an existing Phase5 experiment for1246 exists, rather than generate alternatives.
- Offline evaluator requires explicit result JSON; synthetic tests only now.
  It verifies integrity and full snapshot invariants before evaluating all
  declared methods/budgets. It never changes the original artifacts or registry.

- [x] 1. Tests for prospective scope, identical existing formulas on open data,
  full45 rank/ties, target labels missing, rejection of future history; implement
  src/prediction_scope.py and scoped wrappers/shared validation.
- [x] 2. Tests for deterministic exact-budget portfolios, immutable artifacts,
  hashes/registry; implement src/prospective_experiment.py and artifact module.
- [x] 3. Synthetic-only evaluation tests: target mismatch, invalid bonus, tamper,
  equal budgets, no network, all candidate hypotheses; implement evaluator/CLI.
- [x] 4. Full suite, independent review, repair any defects BEFORE actual freeze.
- [x] 5. Generate registered version2 actual1246 exactly once; verify hashes, contents, registry,
  dataset unchanged. Print complete tickets/rankings and provenance. No evaluation.

Review focus: no silent widening of retrospective seal; prospective rows must
exclude target outcome; ensemble weights must match prior selection; malformed
result/snapshot must fail before evaluation; file non-overwrite and registry
uniqueness across retries/concurrency; no claim of trusted external timestamp.

Ruling: strict source byte equality with bounded prefix for version2 avoids
silently freezing from an updated file without reading its future rows. The
registry schema supports later targets, but Phase5 command is fixed at1246;
future authorization is needed to expand the canonical boundary.

Audit note before formal freeze: one initially failing CLI wiring test patched
the new helper while the CLI still called the legacy version1 helper with its
default canonical path. It generated a temporary version1 snapshot through1245
inside pytest's temporary directory, then fixture cleanup removed it. No scores
or rankings were printed/inspected and no registry entry existed. No future
result was read. Corrected test explicitly supplies a synthetic source and the
CLI now uses the version2 experiment helper. This was not a registered Phase5
experiment, and no model/portfolio settings were changed in response.

Review fixes before actual freeze: persistent target reservations survive partial
publication failures, blocking replacement attempts; full model/component/source
and feature cutoff provenance is validated. Failure-injection and malformed
metadata tests failed before repairs and now pass. Registry fields bind to
snapshot, fixed42 seed and actual development endpoint900 are enforced. Version2
evaluation validates saved tickets structurally and never reruns constructors;
future implementation changes cannot silently replace old ticket choices.

Pre-freeze final verification:158passed2skipped44.25s; all136 original tests
remain passing. Source hash still matches entry/committed/metadata hash; existing
ensemble file SHA256 bafa62df6e48597e0e6f66014a2cac41a4f457021fd85faee505e509aa636771,
development_end900 and weights.2/.1 unchanged. No registered real freeze exists.

Completed: registered experiment draw_1246_20261017T0737528545450900_b1f62b66,
2026-10-17T07:37:52.854545+09:00. Six tracks,51,345 labeled training rows
105-1245,45 unlabeled current rows. One registry entry,FROZEN_UNEVALUATED.
Snapshot SHA2561d7ff3c0b5d34803b43951d688700e78b239f74e327b4a07f7bfdbc63e327723.
Manifest SHA25614e2cfe88e29cf5aa79ff4b162065d74e079bdec1d2a58732caf94b6bb4572c0.
Integrity SHA256846bda67e0122c0194a5ee5aff7deeddd6323aaeeef32c6363b326c78705eb85.
Post-publication read-only verification passed; canonical digest unchanged.
No actual1246 result retrieved,inspected or evaluated. No post-ranking code,
model,weight,seed,portfolio or artifact changes. Only this external work log
and the protocol documentation were updated. No commit/push.
