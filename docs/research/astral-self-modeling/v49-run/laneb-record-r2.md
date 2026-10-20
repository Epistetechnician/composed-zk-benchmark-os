# Lane B instrument-validity gate on V49 r2 (LocalDevelopmentUnreviewed)

Slice: instrument-validity-gate-v1 (under neuron-control-lanes-unreviewed-execution-v1). Same node/model/offline as r2; script `tools/astral-neuron-level-causal-lane-v49/run_laneb.py`; output `laneb-r2.json`. Thresholds were set in code before the run (known-bad must have |z| < 2; lens tolerance 0.5 x max z).

Gate verdict: **InstrumentNotValid** (single failure: known-bad instrument control).

| Check | Result |
|---|---|
| (i) activation shape (3840 raw last-position values) | min -59.0, max 50.25, excess kurtosis 15.6: heavy tails, non-degenerate; pass |
| (ii) both signs | 45.7% positive, 54.3% negative; pass |
| (iii) two readouts | margin z = 24.9, logprob z = 13.9, both p = 0.001; pass |
| (iv) positive control / near miss | top-512 ablation 3.42 > selected 1.24; ranks 33-64 give 0.55 < 1.24; pass |
| (v) known-bad (shuffled-label readout) | effect 0.073 but z = 4.08, above the |z| < 2 bar; **fail** |

Interpretation: the shuffled-label readout is tiny in absolute terms (0.07 vs 1.24) yet the matched-control spread under shuffling is so narrow that z crosses the bar, so the bar as written cannot be treated as passed. Per slice rule it is not retuned. Consequence: the r2 `Candidate` stays recorded but is NOT instrument-validated; do not cite it as a mechanistic result. A redesigned known-bad criterion (e.g. absolute-effect floor) needs a fresh identity.

Cost: node total about $3.4 of USD 30 (see `gman usage`). Not accepted evidence, Level2+, proof, SOTA, or production claim.
