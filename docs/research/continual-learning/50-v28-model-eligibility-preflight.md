# V28 model-eligibility preflight

Status: `ProspectiveLocalDevelopmentModelEligibilityPreflight`.

State slice: `continual-learning-model-eligibility-preflight-v28`.

## Purpose

V28 inserts a cheap, inference-only eligibility gate before any future
retention or interference campaign. It consumes sealed V26/V27 adapter-bank
artifacts, independently revalidates their structure, and evaluates every
task adapter on its own train and held-out facts. It performs no training,
network access, provider call, or promotion.

## Frozen gates

Every case must pass all four gates:

1. every task adapter's exact train accuracy is strictly above that task's
   no-update train accuracy;
2. target task T0 train accuracy is at least `6/8`;
3. target task T0 held-out accuracy is at least `6/8`; and
4. target task T0 does not emit one constant label across its train facts.

The campaign is eligible only when every supplied case passes. Aggregate
training loss cannot substitute for exact choice readout.

## Current readout

The Llama V27 campaign fails V28 in all three cases: T0 is `2/8` on train and
held-out facts and emits a constant label. The Qwen V26 campaign passes all four
gates in two cases, but fails the campaign-wide gate in
`seed-20260840-order-0123` because T2 remains at its `2/8` no-update train
baseline. The original target-scoped V26 candidate therefore remains a local
candidate, not a model-wide eligibility result.

The external reports are:

- `/tmp/continual-learning-eligibility-v28-v26-20260820-r3/report.json`;
- `/tmp/continual-learning-eligibility-v28-v27-20260820-r3/report.json`.

An independent inference-only refresh against the same sealed V26/V27 roots
was completed in r4. Both reports were structurally valid, and each stored
`report_sha256` matched an independent canonical-JSON recomputation. The r4
readout was identical to r3: V26 remained campaign-ineligible because
`seed-20260840-order-0123` failed the all-task-above-no-update gate, and V27
remained ineligible in all three cases because every target emitted a constant
label. No training, network access, adapter mutation, or retention campaign
was performed.

The r4 reports are:

- `/tmp/continual-learning-eligibility-v28-v26-20260820-r4/report.json`
  (`e567235a37e5c1c5442128314439e493f88532c4a8ac04c8ed815830e84c8051`);
- `/tmp/continual-learning-eligibility-v28-v27-20260820-r4/report.json`
  (`49e65fa7316a45f26411ca5a7150bf5d9f4f1edddf37d56fc0984d0bf88d12b3`).

Focused V28 tests pass (`105 passed`), and `lint:fast` passes. The broader
`verify:contracts` gate reached the soak-resume suite after all preceding
Rust/provider suites passed, then four soak tests failed before execution
because the shared macOS temp volume had only `172 MiB` available and
`tempfile` returned `No space left on device`. This is an environment gate
failure, not a V28 result; the broad gate must be rerun after storage is
reclaimed. No cleanup was performed because the workspace contains sealed
artifacts and an unrelated active training run.

Claim ceiling: `LocalDevelopmentModelEligibilityPreflight`. A passing
preflight authorizes only consideration of a separately frozen retention
protocol; it is not scientific evidence, production readiness, provider
validation, or a general continual-learning claim.
