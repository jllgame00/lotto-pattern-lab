# Gap robustness and candidate-pool research

Execute inline with test-driven development; no commits or pushes.

Fixed design before new results: read only canonical rows1..1244; never parse
or hash the sealed suffix. Reject target/history1245+ throughout research.
Prior artifacts containing1245 are not reused. Block current prediction at
the seal. New results have their own reports/prize_research directory.

No new fitted model complexity or tuning. Preserve C=1, cadence26, seed42.
Gap-only and gap+periodicity logistic refit independently at starts401,501,
601,701,801 through1244. Five heuristics: largest gap, smallest gap, gap/mean,
z=(gap+1-mean)/std, mean-reversion=-abs(z). No pre-existing GapModel exists.
At primary start601 also evaluate all existing available model/feature groups.
Exact coefficient/scaling audits and within-target logit contribution variability
explain ranking mechanics; they cannot explain chance realization causally.

Candidate pools6,8,10,12,15: histogram0..6 and >=3/4/5/6 probabilities;
exact Hypergeom(45,6,K) reference, fixed seeded Monte Carlo, uncertainty.
Primary portfolio pool fixed at Top12, configurable separately; budgets1,5,10,20,
three seeded replicates. Two construction methods: score-weighted unique
combination sampling, greedy coverage of five-subsets then pairs. Construction
sees scores/rankings only. Prefixes give equal nested budgets. Enumerate at most
C(15,6)=5005 small-pool combinations; never enumerate C(45,6).
RandomModel Top12 portfolios use identical construction/budgets; also evaluate
unrestricted uniform random45 portfolios as a separate reference. The six-number
pool supports only one unique ticket and is not used for20-ticket portfolios.

All models use bonus only in post-construction prize evaluation. Count 1st,
2nd,3rd separately and both ticket events and draws with events. Do not treat
three replicates as three times as many independent historical draws.
Paired circular26-draw bootstrap2000 reps, time blocks, exact binomial rare-event
intervals for draw counts, multiplicity warnings. Bootstrap degenerate rare-event
intervals must not be interpreted as proof of zero risk/probability.

- [x] Seal loader/CLI/feature/model/backtest boundaries + adversarial tests.
- [x] Gap heuristics, coefficient/scaler/contribution audits + tests.
- [x] Candidate-pool/prize mathematics and deterministic portfolios + tests.
- [x] Robustness/report orchestration, pairwise comparisons, CLI and docs.
- [x] Diagnose dependencies once without disabling environment restrictions.
- [x] Run tests and fixed experiments, independent code review, report limitations.

Run completed219.771s. No stable gap-vs-random or gap-vs-heuristic advantage;
no corrected pool concentration result. Optional tree backends remain blocked.
Prior phase accessed1245 for current prediction; this phase did not read/use it.
