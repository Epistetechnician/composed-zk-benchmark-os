# Plasticity Recovery V2 Execution Record

State slice: `continual-learning-plasticity-recovery-v2`.

## Execution

The preregistered fresh exact-synthetic factorial completed 72 cases: six
arms, four fresh data seeds, and three fresh fit-order seeds. Tune predictions
were sealed before assessment effects. Every case used 32 gradient evaluations
and 32 shadow evaluations; the base state was unchanged and adapter state was
reversible.

External artifact root:

`/Users/shaanp/Documents/research-artifacts/continual-learning-plasticity-recovery-v2-20260829`

Result SHA-256:

`441b821ba22fbfa939417c48fd14a1269b32bd9e9bf8190f916d373e0c981c99`

Prediction-lock SHA-256:

`f0b41024f7dc34d05679fe24bd4e8b606bb38a1919d74914c6a99770e476c310`

Independent aggregate-only artifact validation passed.

## Observed result

| Arm | Mean improvement vs untouched base | Bootstrap 95% interval | Positive cases | All hard guards |
|---|---:|---|---:|---|
| `fixed_adapter` | `0.02892867` | `[0.02745330, 0.03032186]` | `12/12` | no |
| `replay` | `0.03122115` | `[0.03022741, 0.03224000]` | `12/12` | no |
| `selective_reinit` | `0.02808654` | `[0.02665234, 0.02937276]` | `12/12` | no |
| `replay_selective_reinit` | `0.02989522` | `[0.02899275, 0.03082009]` | `12/12` | no |
| `protected_replay` | `0.03220089` | `[0.03066969, 0.03359022]` | `12/12` | no |

`protected_replay` produced the strongest held-out improvement and passed the
fixed effect, bootstrap, and positive-case requirements. It failed the fixed
per-case forgetting guard. The other updating arms also failed forgetting;
calibration, rollback fidelity, base immutability, equal compute, and order
stability passed.

Decision: `NoCandidate`. The protected-replay mechanism does not advance to a
cached-model experiment. GiveMeANode, Astral integration, and ZK/PQC custody
proof remain `not_run`.

Claim ceiling: `LocalDevelopmentPlasticityRecoveryV2SyntheticOnly`.

Every mutation in this execution record touches state slice
`continual-learning-plasticity-recovery-v2`.
