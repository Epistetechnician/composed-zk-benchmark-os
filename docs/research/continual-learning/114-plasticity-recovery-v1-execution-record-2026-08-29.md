# Plasticity Recovery V1 Execution Record

State slice: `continual-learning-plasticity-recovery-v1`.

## Execution

The exact synthetic factorial completed locally with 60 cases: five arms,
four data seeds, and three fit-order seeds. Fit transitions completed before a
single digest-bound prediction lock; assessment effects were computed only
after that lock. The untouched base remained unchanged, and every case used
32 gradient evaluations plus 32 shadow evaluations.

External artifact root:

`/Users/shaanp/Documents/research-artifacts/continual-learning-plasticity-recovery-v1-20260829`

Result SHA-256:

`6d9c20de01e3b636132c99a81d6c08352d124e7e6326038feb1fc45354e44f1e`

Prediction-lock SHA-256:

`3e92fef1680b60576e4197058ec8674f456351a1d85a3e68a9808670811fb542`

The independent aggregate-only validator passed the artifact readback.

## Observed result

| Arm | Mean improvement vs untouched base | Bootstrap 95% interval | Positive cases | All hard guards |
|---|---:|---|---:|---|
| `fixed_adapter` | `0.03010138` | `[0.02797528, 0.03204850]` | `12/12` | no |
| `replay` | `0.03190428` | `[0.03053775, 0.03316524]` | `12/12` | no |
| `selective_reinit` | `0.02901171` | `[0.02627461, 0.03155480]` | `12/12` | no |
| `replay_selective_reinit` | `0.03103478` | `[0.02931935, 0.03255088]` | `12/12` | no |

All non-control arms exceeded the fixed effect threshold and bootstrap
requirement. The forgetting guard failed for each non-control arm; order
stability, calibration, rollback, base immutability, and equal compute were
otherwise mechanically checked. Therefore no arm is a continual-learning
candidate under the preregistered rule. The synthetic mechanism is closed as
a candidate for this slice; the implementation remains useful as a guarded
replay/reinitialization test fixture.

Classification: `NoCandidate`.

Astral integration: `not_run`.

ZK/PQC custody proof: `not_run`.

GiveMeANode: `not_submitted`; a hard USD spend ceiling was not recorded.

Claim ceiling: `LocalDevelopmentPlasticityRecoverySyntheticOnly`.

Every mutation in this execution record touches state slice
`continual-learning-plasticity-recovery-v1`.
