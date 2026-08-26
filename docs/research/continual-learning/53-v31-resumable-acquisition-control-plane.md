# V31 resumable acquisition control-plane record

Status: `CompleteLocalControlPlaneReadyForAssessment`.

State slice: `continual-learning-model-acquisition-eligibility-v31-resumable`.

## Purpose

V31 closes the operational gap exposed by V30: a task adapter can exist after
the parent process stops, while the assessment and result manifest remain
unsealed. V31 treats the V30 artifact as read-only input and creates a fresh,
immutable output root. It validates the fixed model, seed, order, task
manifest, raw-text datasets, audit facts, adapter configuration, adapter
digests, and training-log digests before classifying each task as complete or
pending.

The resumable path writes immutable `pending`, `running`, `complete`, or
`failed` task events. It never overwrites a task artifact. A timeout, failed
subprocess, missing adapter, failed digest, or resource-guard rejection
produces an incomplete receipt and cannot produce `eligible: true`.

## Executed control-plane receipt

The control plane was executed against the independently validated V30 result
at:

`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen36-acquisition-v30-20260821-r2`

The original V31 receipt was created outside the repository under `/private/tmp`
and was byte-identical copied into durable repository-external custody at:

`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen36-resume-v31-20260822-r1`

The durable custody copy contains 9 files. Independent file hashing matched
all 9 source/copy digests, and the V31 validator returned `valid: true` on the
durable path.

The independent validator returned `valid: true` with:

- all four task artifacts bound and complete;
- source manifest digest `0bec3eff24a1382b0b85ff8ce5917e7d08f1f821b72483da9d225cd687154970`;
- receipt digest `46221fc797707449da29493bb5ca086c17b85c79c89666e879872f8d59a1a3b1`;
- observed source peak memory `25.551 GB`, guarded projection `25.8 GB`, and projected task budget `300 s`;
- status `ready_for_assessment`;
- `eligible: false`, with retention, interference, provider, and production claims all false.

`ready_for_assessment` means only that task artifacts are structurally
available for a separately authorized assessment. It is not a learning,
retention, interference, provider, production, or scientific result. No new
model training or assessment was executed in this V31 control-plane run.

Claim ceiling: `LocalDevelopmentModelAcquisitionEligibilityPreflight`.
