# Astral V49 r3 (template-held-out) + Lane B gate (LocalDevelopmentUnreviewed)

Slices: astral-neuron-level-causal-lane-v49-execution, instrument-validity-gate-v1, neuron-control-lanes-unreviewed-execution-v1. Code committed before the run (commit "r3 preregistered code"); output `r3.json` (1915 B), seed 51, same node/model/offline, 201 s.

Changes vs r2: 12 templates split template-disjoint (fit 0,1,6,7; tune 2,5,8,11; assess 3,4,9,10); known-bad now needs |z|<2 AND |effect|<10% of selected.

V49 result: **Candidate** on held-out templates. Selected 32 neurons: margin drop 1.06 (tune) and 1.14 (assess) vs matched-random gaps 1.05 / 1.17; p = 0.001 (1000-draw floor), Holm rejects both; text-only 0, shuffled -0.0008, constant -0.06 do not separate.

Lane B gate: **InstrumentNotValid**, single failure `lens_sensitivity`. Passed: tail shape (n=7680, min -57, max 44, excess kurtosis 11.6), both signs (48% positive), positive control (top-512 drop 2.96 > 1.14), near-miss (ranks 33-64: 0.35 < 1.14), known-bad (shuffled effect -0.0003, z -0.08). Lens: margin z=18.9, logprob z=5.8, both p=0.001; the preregistered tolerance (0.5 x max z = 9.45) was exceeded by the 13.1 gap in z.

Verdict `NotValidated`. Both readouts independently separate the set from controls at the p floor, but the z-gap tolerance is a crude, scale-sensitive rule; it was not retuned. A rank-based or sign-agreement lens criterion would need a fresh identity (r4).

Limits: one model, one task family (12 templates), first-order gradient selection, three layers, single run, unreviewed. Not accepted evidence, Level2+, proof, SOTA, production, introspection claim.
