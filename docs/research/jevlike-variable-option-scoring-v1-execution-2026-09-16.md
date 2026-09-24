# Jevlike variable-option scoring V1 execution record

State slice: `jevlike-variable-option-scoring-v1`.

Execution status: `COMPLETE / NO_CANDIDATE_HELD_OUT_STRONGEST_BASELINE`.

## Frozen execution identity

- Upstream Jevlike revision:
  `94f5fd1b0b11d52bbdfdf4e0ee6aa96b568f8452`.
- Encoder: Jevlike `tiny` byte encoder.
- Device: CPU.
- Pretrained weights: none.
- Host-model execution: false.
- Network during training/evaluation: false.
- Evidence Ledger mutation: false.
- Aggregate report: `/Users/shaanp/.codex/runs/jevlike-variable-option-scoring-v1/aggregate-report.json`.
- Aggregate report digest:
  `sha256:7432bdfd659af66a59202d281656db10d6061da3e3dd035afce7b25d8a055ab9`.

## Data and controls

The input was derived from existing archived synthetic FSM actor observations,
with oracle-derived first-divergence labels. Entire source runs were assigned
to one split: 400 fit rows, 200 tune rows, and 100 held-out test rows. The
test menus contained 3–6 options; fit menus ranged from 3–135 options.

The held-out controls were shuffled context and deterministic option
permutation. The latter remapped labels with the candidate ordering and
therefore tests whether the scorer depends on option position.

## Results

| Measurement | Held-out result |
|---|---:|
| Jevlike top-1 | 0.48 |
| Jevlike top-3 | 0.85 |
| Jevlike ECE | 0.0604 |
| Strongest simple baseline | 0.45 |
| Uniform-random expected top-1 | 0.2375 |
| Shuffled-context top-1 | 0.37 |
| Option-permuted top-1 | 0.48 |

The paired comparison produced 18 model-only wins and 15 baseline-only wins
over 100 test cases. Exact two-sided McNemar p was `0.7283324808813632`.
The tune result was 0.325 top-1 versus a 0.30 majority-label baseline.

## Disposition

`NoCandidateHeldOutStrongestBaseline`.

The model passed the option-permutation identity check and exceeded the random
baseline, but the held-out top-1 gain over the strongest simple baseline was
only three percentage points and was not supported by the paired comparison.
The tune result was also weak. The shuffled-context control retained 0.37
top-1, so the result does not support a strong context-grounded localization
claim.

Do not retune this run, promote the checkpoint, connect it to a host model,
use it for causal interventions, or treat it as Astral, self-modeling,
alignment, proof, benchmark, or production evidence. A continuation requires
a new protocol identity with a stronger task construction or an independently
reviewed label/control design.

Claim ceiling: `LocalDevelopmentVariableOptionScoringFeasibilityOnly`.

Every mutation governed by this record touches state slice
`jevlike-variable-option-scoring-v1`.
