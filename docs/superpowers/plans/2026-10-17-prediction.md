# Predictive experiments implementation plan

Use superpowers:executing-plans and test-driven-development inline.

Goal: reproducible out-of-sample ranking experiments, never a prediction claim.
Architecture: a centrally generated causal feature table; fitted models accept
explicit training rows/cutoff; a separate chronological ranking runner retains
the existing RandomModel backtester unchanged.

Fixed before evaluation: 104 history draws; supervised targets 105 onward;
evaluation 601 through penultimate draw (1244 in current snapshot), cadence 26,
seed 42, expanding training. No tuning. Latest observed draw is reserved.
Similarity: same-number neighbors, K=30, Euclidean standardized distance,
inverse (1+distance) weighting, Beta prior equivalent to 15 observations at 6/45.
Logistic: pooled L2 logistic, C=1, unpenalized intercept, training imputation
and scaling. SciPy L-BFGS implementation because sklearn is unavailable.
RF adapter: 100 trees, depth 4, leaf 50, max_features=sqrt, n_jobs=1.
LightGBM adapter: 100 trees, learning rate .03, 7 leaves, depth 3, leaf 100,
single thread, deterministic seed. XGBoost fallback only if installed.

- [x] tests/test_features.py -> src/analysis/features.py: target alignment,
  prefix invariance, bonus exclusion, online regimes, feature groups.
- [x] tests/test_predictive_models.py -> src/models/predictive.py: training-only
  preprocessing, similarity neighbors, deterministic logistic/RF/boosting,
  unique deterministic ranking and seeded weighted tickets.
- [x] tests/test_ranking.py -> src/backtest/ranking.py: cadence and audit
  boundaries, same-target comparisons, random simulations, block bootstrap,
  ablations and early/middle/recent performance.
- [x] src/prediction_cli.py and src/cli.py: compare-models, predict-current,
  explain-number, explicit unavailable-dependency reports, protected outputs.
- [x] Run all tests, fixed available-model comparisons and seven logistic ablations. Export
  sample/full features, audit, importance, results and runtime. Review code.

Unresolved environment limitation: Random Forest and boosting implementations
are adapters only; their integration tests and full comparisons await installed
scikit-learn and LightGBM/XGBoost. Attempts to install all three packages failed.
They were not replaced with another algorithm or reported as evaluated.

Review focus: never impute from evaluation rows; never include target labels
in scoring data; online regime confirmation must not backdate knowledge;
single-class or all-missing columns must be handled; overlapping windows and
multiple comparisons require cautious interpretation. No commit or push.
