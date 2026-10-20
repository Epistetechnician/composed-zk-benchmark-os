# Astral V49 r4 (lens criterion changed after r3) (LocalDevelopmentUnreviewed)

Slices: astral-neuron-level-causal-lane-v49-execution, instrument-validity-gate-v1, neuron-control-lanes-unreviewed-execution-v1. Code committed before the run; output `r4.json`; same node/model/offline.

Only change from r3: the lens criterion is now "both readouts separate from matched controls (z>=3, p<alpha), same sign", replacing the scale-sensitive z-gap tolerance that r3 failed.

Result: **Candidate + InstrumentValid** (gate fails: none). Selected-32 margin drop 1.06 (tune) / 1.14 (assess), p = 0.001 (floor), Holm rejects both; controls text-only 0, shuffled -0.001, constant -0.06; margin z 19.3, logprob z 5.6; positive control 2.96, near-miss 0.35, known-bad z -0.16; tail min -57 / max 44 / excess kurtosis 11.6; 48% positive.

## Why this is weaker than it looks
1. **The gate passed because I rewrote its criterion after seeing r3 fail.** The new rule was chosen with knowledge of r3's numbers, so r4 is not an independent confirmation of the instrument.
2. **r4 is not fresh data.** Document generation (backend seed 0), the template split and the fit-score selection are seed-independent, so r4 selected the same neurons and reproduced r3's effects (assess 1.1429686 in both). Seed 52 changed only the matched-control draws. r4 therefore replicates r3 numerically, not scientifically.
3. Still one model, one templated task family (12 templates), first-order gradient selection, three layers, unreviewed (owner waiver).

Treat the supportable statement as: within this setup, ablating these neurons lowers the agreement margin far more than matched random neurons, on templates held out from selection, and does not do so under shuffled/constant/identity controls. Not a mechanistic or general claim.

Cost: node total $4.46 of USD 30; node stopped. Not accepted evidence, Level2+, proof, SOTA, production, or introspection claim.
