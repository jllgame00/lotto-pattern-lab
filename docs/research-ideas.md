# Research ideas

H1 fixed-number temporal patterns and H2 gap/periodicity/regime models have been tested with inconclusive evidence. Phase 6 investigates H3: translation through both draw and ordered number axes.

The motivating example is 1 → 4 → 7 → 10 at draws t, t+3, t+6, t+9: Δdraw=+3 and Δnumber=+3. Negative movements are equally eligible. Numbers do not wrap around from45 to1. Ordered lottery labels need not have a meaningful spatial mechanism; this is a hypothesis to test, not an assumption.

H3 is TESTED / INCONCLUSIVE. H4 gap-conditioned 3D translational patterns is TESTED / INCONCLUSIVE. H5 recent-frequency-conditioned 3D translational patterns is TESTED / INCONCLUSIVE. H6 joint gap x recent-frequency interaction is TESTED / INCONCLUSIVE. H7 full4D trajectory geometry and H8 delay embedding/tensor methods are BACKLOG. Add dimensions only for meaningful state variables with causal definitions and sufficient data. Enlarging a search space creates more accidental patterns, not more evidence.

Phase7 asks whether the same 1 → 4 → 7 → 10 trajectory at draw increments3 concentrates within a causal gap state, or whether its PRE-draw gaps also translate by a repeated delta. Mixing states in2D could hypothetically obscure a relationship. This is a hypothesis, not evidence. Gap before target t is t-1 minus the last appearance draw; never-seen numbers are missing. Only current gap is added: no frequency, month, HMM state, periodicity, other third dimension, or4D. Full search correction must become stricter as the state space expands.

Phase 6 uses complete-search surrogate maxima under IID six-of-45 draws and exact-margin randomizations. Raw attractive lines, local peaks, and isolated prize-equivalent events are exploratory. All prospective artifacts are separate from the immutable Phase 5 experiment, and no draw1246 result is retrieved.

Phase7 repeated the complete search under199 surrogates of each null family,
recomputing causal gaps and fitted bins each time. No family survived correction.
The coarse-gap translation model's small historical improvement has paired
intervals containing zero; the coarse-gap chain model performed worse than its
2D parent by point estimate. See [Phase7 results](phase7-results.md). This does
not justify adding dimensions to rescue a preferred narrative. H5 remains a
separate hypothesis, now tested by Phase8.

Phase8 replaces the third dimension with recent appearance frequency; it does
not add frequency to gap. Two numbers with current_gap=2 may differ greatly in
appearances before their latest occurrence (zero versus four in the preceding10
draws). Current gap records time since one event, while recent frequency counts
events over a fixed past window. A(+3,+3) translation might hypothetically occur
more often from HOT sources. This is exploratory, not evidence. OnlyW10/26/52
are tested, with training-only bins and complete all-window surrogate searches.

Phase8 searched all three frequency windows under199+199 complete surrogate
searches. No family survived correction, and no window established reliable
out-of-sample superiority. H5 is TESTED / INCONCLUSIVE.

Phase9 began H6 IN PROGRESS: a globally diluted translation could also be diluted
within gap alone or frequency alone, yet hypothetically concentrate in HIGH-gap
AND HOT-frequency sources. It uses categorical3x3 states and fixed W26, with
causal training-prefix boundaries. This interaction hypothesis increases false-
discovery risk. Complete null searches found no corrected interaction, and
matching-target prediction did not establish improvement over both parents.
H6 concludes TESTED / INCONCLUSIVE. Full continuous4D vectors and arbitrary state
progressions remain deferred; H7/H8 stay backlog.
