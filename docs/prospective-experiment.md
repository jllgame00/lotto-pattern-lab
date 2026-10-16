# Phase5 prospective experiment protocol

The fixed target is1246 and the source is draws1-1245 only. No result after1245
is fetched or inspected by generation. Draw1245 is training data and is not a
pristine holdout. This experiment carries no claim of predictive performance.

## Generate and preserve

```powershell
python main.py freeze-next
```

This version2 command uses the six requested tracks: Gap Logistic, Bayesian
static, HMM2, HMM3, the existing development-weight ensemble and UniformRandom.
It uses seed42, unchanged Phase4 formulas and settings, and refits each required
component once at cutoff1245. Canonical features are shared with historical
experiments. Training label rows start105 because features require104 prior
draws; these labels end1245. Current feature rows target1246, use only1-1245,
and contain no target label or bonus. The Bayesian adapter retains its Phase4
supervised-history definition, not the older version1 snapshot helper's draw1
counting policy. HMMs retain260-draw windows,40 iterations,two initializations.

The historical default seal remains1244. Explicit immutable prospective scopes
allow only the supplied complete prefix (at most1245) and its next target.
The new source loader rejects unknown suffixes using byte size without reading
the next row. File bytes and ensemble-source hash are rechecked before writing.

The ensemble loads the existing development-weight artifact, verifies its nine
components and rank normalization, and preserves weights selected on601-900:
GapLogistic.2; GapHazard,BayesianStatic,BayesianRecent,HMM2,HMM3,SimilarityModel,
Frequency52,GapPeriodicityLogistic each.1. No weight fitting occurs at freeze time.
An unavailable or mismatched source/model aborts rather than silently substitutes.

Each track preserves45 scores,complete rank,Top6/8/10/12/15,exact ties and tie
rules. Non-random ties prefer the smaller number. UniformRandom assigns6/45 to
every number and uses one NumPy seed42 permutation to break ties uniformly.

Gap Logistic and Ensemble each have one direct Top6 ticket and one20-ticket
portfolio per weighted/coverage method using Top12 candidates. Budgets1/5/10/20
are nested prefixes. The direct ticket is separate from a method's budget1
prefix. UniformRandom has one unrestricted uniform45 portfolio with the same
budgets; its random ranking Top6 is the direct-ticket control. No alternative
seeds or attractive portfolios are searched. Coverage prioritizes new five-number
subsets,then pairs,then the existing seeded weighted priority. Weighted generation
uses the existing product-weight/Gumbel construction.

Gap/ensemble Top8/10/12/15 winner coverage and>=3/4/5/all6 indicators are all
predeclared. No cutoff is selected after the result. Rankings for the other four
tracks are preserved and evaluated identically as secondary diagnostics.

## Artifacts and recovery

Unique timestamped snapshot JSON and human-readable manifest contain provenance,
configurations,features,all rankings and exact ticket sets. JSON also embeds
the current source implementations and their hashes, component scores,fitted
parameters/scalers,and the original ensemble-weight file text/hash. This permits
audit even though Phase5 code is intentionally uncommitted.

An integrity record stores SHA256 for snapshot and manifest. Their hashes are
also recorded in `reports/prospective/registry.csv`, initially
`FROZEN_UNEVALUATED`. A persistent per-target reservation is created before
artifact writes; a failure cannot silently permit a replacement experiment.
Never remove a reservation merely to rerun predictions. Partial publication
requires explicit recovery of that same experiment. All files use exclusive
creation; registry access is serialized. Existing target1246 cannot be frozen
again by this command. The registry can retain future targets alongside it;
expanding source authorization beyond1245 requires a later phase.

These are local integrity records, not trusted external timestamping. The saved
generation time and this session's externally displayed hashes provide an
audit trail, but cannot prove that nobody elsewhere knew the outcome.

## Evaluate later, offline

Only once an explicit result is legitimately available:

```powershell
python main.py evaluate-freeze <snapshot.json> <result.json> --output <new-evaluation.json>
```

Result schema: `draw_no` as integer,`main_numbers` as six unique integers1-45,
`bonus` as one distinct integer1-45. The draw number must match the snapshot.
The evaluator validates hashes,registry metadata,rankings,model/ensemble
provenance,cutoffs and portfolio invariants before using the supplied result.
It never retrieves anything,loads canonical history,refits models,regenerates
tickets,changes the freeze,or overwrites existing evaluation files.

It reports Top6 hits,Top8/10/12/15 main-winner coverage and threshold indicators,
mean winning rank,recall,best ticket hits by method/budget,per-ticket prize class,
separate first/second/third counts and equal-budget frozen-control differences.
Only synthetic results are used to test it during Phase5. The real1246 snapshot
remains unevaluated. Registry status is not changed automatically by this read-only
evaluator; future result registration should be an explicit separate action.

## Entry verification and test audit

Entry HEAD: `2ee5da879fe7d53be95191ac4d55782551b1f6c5`; working tree clean and
Phase4 already committed.136tests passed,2optional dependency tests skipped.
Canonical1245 rows through2026-10-10; SHA256
`b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e`
matches committed bytes and provenance metadata. No source update was performed.

One early CLI wiring test inadvertently invoked the legacy version1 helper on
the canonical prefix instead of its intended new-helper stub. It produced a
temporary legacy snapshot in pytest scratch space,which fixture cleanup removed.
No scores/rankings were displayed or inspected,no target result was read,and no
registry entry existed. The test now explicitly supplies a synthetic source.
No model,weight,seed or portfolio policy changed because of that draft. The
registered version2 six-track experiment is generated only after full verification.

## Registered experiment

Generated once at **2026-10-17T07:37:52.854545+09:00** after **158 passed,2 skipped**
(44.25s). The working tree contains the intentional,uncommitted Phase5 changes.
No commit or push was made. All six requested tracks succeeded without redesign.

Experiment:`draw_1246_20261017T0737528545450900_b1f62b66`.
Training data ends1245; target1246 remains unseen and unevaluated by this work.
One registry entry has status`FROZEN_UNEVALUATED`.

Files under`reports/prospective/`:

- `draw_1246_20261017T0737528545450900_b1f62b66.json`
- `draw_1246_20261017T0737528545450900_b1f62b66_manifest.md`
- `draw_1246_20261017T0737528545450900_b1f62b66_integrity.json`
- `registry.csv`
- `draw_1246.reservation.json` (persistent duplicate-publication guard)

SHA256:

```text
snapshot  1d7ff3c0b5d34803b43951d688700e78b239f74e327b4a07f7bfdbc63e327723
manifest  14e2cfe88e29cf5aa79ff4b162065d74e079bdec1d2a58732caf94b6bb4572c0
integrity 846bda67e0122c0194a5ee5aff7deeddd6323aaeeef32c6363b326c78705eb85
dataset   b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e
Git       2ee5da879fe7d53be95191ac4d55782551b1f6c5
```

Read-only post-publication verification confirmed the complete six-track schema,
all45 ranks/scores,TopK consistency,portfolios,model/ensemble provenance,hashes,
one registry row and unchanged canonical data. The real evaluator was not run.
No predictions,weights,seeds,portfolios or frozen artifacts were changed afterward.
