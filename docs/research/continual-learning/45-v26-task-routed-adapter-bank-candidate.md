# V26 task-routed adapter-bank candidate

Status: `ProspectiveLocalDevelopmentTaskRoutedAdapterBankCandidate`.

State slice: `continual-learning-candidate-task-routed-adapter-bank-v26`.

## Why this candidate

V25's fresh holdout invalidated the seed/order search candidate for shared
replay. Earlier controlled runs show that replay rows are present and that
row-order changes do not repair shared-adapter interference. The immutable
task-adapter bank is the only local mechanism that repeatedly preserves the
held-out task under a solvable, route-bound prompt. V26 therefore evaluates
that mechanism as an explicit bounded architecture candidate rather than
relabeling it as replay learning.

## Single changed mechanism

Each task is trained from the same frozen base into a fresh LoRA adapter. An
exact task-token route selects the adapter at assessment. Existing shared
sequential and shared replay strategies remain comparison baselines. No
adapter is resumed into another task slot, overwritten, or merged.

## Frozen contract

- Cached Qwen2.5-0.5B-Instruct-4bit, offline MLX runtime.
- Four tasks; eight train and eight disjoint held-out facts per task; two per
  modular residue in each split.
- Route-bound residue-only prompt; raw compositional pair absent; training and
  assessment prompt bytes identical.
- 160 LoRA iterations, 32 rows/update, AdamW `0.0001`, batch size `2`, eight
  layers, maximum sequence length `192`.
- Fresh seeds and task orders are declared before execution. Each case is
  independently executed and independently validated.

## Candidate gates

Every case must pass all four gates:

1. retrieval acquisition exceeds no-update acquisition;
2. routed-bank acquisition exceeds no-update acquisition;
3. routed-bank held-out retention exceeds shared naive retention; and
4. routed-bank held-out retention is at least `6/8`.

The campaign candidate requires every preregistered fresh case to pass. A pass
supports only `LocalDevelopmentTaskRoutedAdapterBankCandidate`. It does not
support shared-replay learning, general continual-learning claims, production
readiness, provider execution, or breakthrough claims.

## Stop rules

Any invalid artifact, route reuse, prompt leakage, failed candidate gate, or
validator disagreement stops the campaign. Do not mine additional seeds after
a failed fresh holdout. Do not provision an H100 unless local telemetry first
shows runtime or memory is the remaining bottleneck after all scientific gates
pass.
