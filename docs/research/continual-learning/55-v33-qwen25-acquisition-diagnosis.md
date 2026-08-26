# V33 Qwen2.5 acquisition diagnosis

Status: `CompleteNonTargetAcquisitionInstabilityDiagnosis`.

State slice: `continual-learning-diagnosis-qwen25-acquisition-v33`.

## Finding

V33 is a read-only diagnosis over the independently validated V32 campaign.
It performs no model execution, training, adapter mutation, retention,
provider, or production work.

The target task T0 is robust across all three V32 cases: it reaches `8/8`
train and held-out accuracy, improves over its no-update baseline, and does
not emit a constant label. The campaign failure is entirely non-target:

- seed `20260854`, T3: adapter train and held-out accuracy `4/8`, exactly
  tied with its `4/8` no-update baseline;
- seed `20260855`, T1: adapter train and held-out accuracy `2/8`, above its
  `0/8` baseline but emitted a constant `C` on all eight train facts.

The independent diagnosis validator returned `valid: true` with
classification `NonTargetAcquisitionInstabilityNotTargetFailure`.

The diagnosis was first written under `/private/tmp` and is now in durable
repository-external custody at:

`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen25-diagnosis-v33-20260822-r1/diagnosis.json`

The durable diagnosis copy is byte-identical to the source, and its
independent validator returned `valid: true`.

Report digest:
`c0b5dc34389c2c31e27fb5e4adeb126269751b3aebb5572f6bd9a43278a1630b`.

## Next hypothesis boundary

The next experiment must improve per-task acquisition stability across
non-target routes while preserving the exact T0 behavior. A retention run is
still unauthorized because the V32 campaign-wide acquisition gate remains
false. No seed mining or adaptive assessment tuning is authorized by this
diagnosis.

Claim ceiling: `LocalDevelopmentQwen25AcquisitionFailureDiagnosis`.
