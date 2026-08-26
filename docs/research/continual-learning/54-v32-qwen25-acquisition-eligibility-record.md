# V32 Qwen2.5 acquisition-eligibility record

Status: `CompleteNegativeLocalDevelopmentAcquisitionEligibilityPreflight`.

State slice: `continual-learning-qwen25-acquisition-eligibility-v32`.

## Frozen contract

V32 reused the V29 acquisition-only task-adapter mechanism and exact
route-bound prompt. The only changed variables were the already-cached
`Qwen2.5-0.5B-Instruct-4bit` model identity and three fresh seeds:
`20260853`, `20260854`, and `20260855`. The order was fixed to `0,1,2,3`,
with 160 LoRA iterations and 32 update rows per task. Retention, interference,
reacquisition, provider, and production execution were disabled.

## Execution

The immutable campaign root was first created under `/private/tmp` and is now
in durable repository-external custody at:

`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen25-acquisition-v32-20260822-r3`

The durable copy contains 104 files and independent file hashing matched every
source/copy digest. The campaign-level validator returned `valid: true` on the
durable path.

All three cases completed and passed the independent case validator. The
campaign-level validator also returned `valid: true`:

| seed | all-task acquisition | target train floor | target held-out floor | target non-constant | eligible | result digest |
| ---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 20260853 | true | true | true | true | true | `990052b5d295def8a74fbba81b985d8c637d46df63188a5746b3c3e22b0de8d1` |
| 20260854 | false | true | true | true | false | `e0d4d372760e1b05f318908e25969d1f11c12e2ab957fdbe0504eedbd7edb1a5` |
| 20260855 | true | true | true | true | true | `b9e94647bb7bd5ed25a55b3094c008356b86bae73919c3f406fb18de11491156` |

The campaign report digest is
`88b128be2562915634f616608891bd0f5bf5960de21980f31bfdf186385eb1bb`.
The campaign is therefore valid but not eligible: one fixed case failed the
all-task acquisition gate. This is not a seed-mining result and does not
authorize retention or interference.

Two earlier wrapper failures were quarantined rather than reused:

- `/private/tmp/continual-learning-qwen25-acquisition-v32-20260822-r1-incomplete`;
- `/private/tmp/continual-learning-qwen25-acquisition-v32-20260822-r2-incomplete`.

Those roots contain only incomplete control-plane attempts and are not
evidence.

Claim ceiling: `LocalDevelopmentModelAcquisitionEligibilityPreflight`.
No provider, production, scientific, general continual-learning, or
breakthrough claim is supported.
