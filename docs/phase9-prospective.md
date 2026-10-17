# Phase 9 prospective record

Experiment: `draw1246_phase9_joint4dstate_20261017T094322096047_14004a94`

Created: 2026-10-17T09:43:22.096047+09:00

Target **1246**, training cutoff **1245**, latest included date **2026-10-10**. Status **FROZEN_UNEVALUATED**. No draw-1246 result was retrieved, searched for, inspected, imported or evaluated.

Git SHA: `36b534687fb79c40d36e68d970303b906b8ab2c9`; working tree dirty with the intended Phase 9 implementation.

Canonical dataset SHA-256: `b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e`

## Independent tracks

| Model | Top 6 | Top 10 | Top 12 | Top 15 |
| --- | --- | --- | --- | --- |
| JointStateFrequencyBaseline | 1, 5, 26, 22, 31, 9 | 1, 5, 26, 22, 31, 9, 24, 25, 7, 10 | 1, 5, 26, 22, 31, 9, 24, 25, 7, 10, 23, 33 | 1, 5, 26, 22, 31, 9, 24, 25, 7, 10, 23, 33, 36, 3, 6 |
| JointStateTranslationModel | 31, 1, 2, 3, 4, 5 | 31, 1, 2, 3, 4, 5, 6, 7, 8, 9 | 31, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 | 31, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14 |
| JointStateChainModel | 42, 1, 2, 3, 4, 5 | 42, 1, 2, 3, 4, 5, 6, 7, 8, 9 | 42, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 | 42, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14 |

The geometric tracks each have only two distinct scores and a 44-number tie: Translation supports 31; Chain supports 42. The many low-number ranks are the fixed tie-breaking fallback, not stronger model evidence. No formula, setting or ticket generation was changed after viewing these rankings.

Ranks are descending score; exact ties favor the smaller number. Complete scores, ranking, ties, Top8 and fitted-state/rule diagnostics are preserved in the JSON and manifest.

Each track freezes direct Top6 and one seeded weighted and one coverage-oriented Top12 portfolio, with unique nested 1/5/10/20-ticket budgets, seed 42. No alternative portfolios were selected after viewing predictions. These are experimental hypotheses, not a predictive claim.

## Immutable artifacts

- [snapshot](D:/univ/personal/lotto-pattern-lab/reports/prospective/phase9/draw1246_phase9_joint4dstate_20261017T094322096047_14004a94.json): `f4afd34787cdbb9080be0682f28021af9f0ab01420db18476bf130262235b996`
- [manifest](D:/univ/personal/lotto-pattern-lab/reports/prospective/phase9/draw1246_phase9_joint4dstate_20261017T094322096047_14004a94_manifest.md): `1ff926c0870bddfc9aaa9e1a6f29feb01eabba28d53807eb87cf075f256d3df0`
- [integrity](D:/univ/personal/lotto-pattern-lab/reports/prospective/phase9/draw1246_phase9_joint4dstate_20261017T094322096047_14004a94_integrity.json): `278b3c2b739d4f688a1ea40ab99a29150123371106163900d80532388f42d2c0`
- [registry](D:/univ/personal/lotto-pattern-lab/reports/prospective/phase9/registry.csv): `a0e4f2c2b6c25d8ebdc00e46fa36616f83f71d555e6ae5132f33553316810c9a`

The registry entry belongs only to Phase 9. All **20** earlier Phase 5/6/7/8 files, including their registries and reservation records, match their before-work hashes byte-for-byte. The canonical dataset hash is unchanged. The Phase 9 publisher has verified its snapshot, manifest, integrity record and registry.

No commit or push was made. This experiment must never be overwritten, regenerated, modified or replaced. Any later work must create separate evidence.
