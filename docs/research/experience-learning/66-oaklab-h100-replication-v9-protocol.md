# Oak Lab H100 replication V9 protocol

State slice: `oaklab-experience-learning-h100-replication-v9`.

V9 is a new protocol identity after the terminal V8 synthetic failure. V8 is
historical and cannot be patched, retuned, or used as scientific input.

## New mechanism

The treatment is a segment-budgeted update policy. A trajectory is partitioned
into fixed 32-row segments. The policy chooses `apply` or `skip` only at a
segment boundary, using the completed previous segment's loss and operation
cost. The selected bit is held for all 32 rows. Current-segment outcomes never
enter the current action. The controller has only two float64 statistics,
three integer/bit fields, and explicit byte accounting; there is no
per-parameter eligibility trace, q table, replay, or hidden accumulation.

The complete-policy estimand is the paired segment utility

`(loss_treatment-loss_control) + 0.002*(ops_treatment-ops_control) + 0.05*(storage_treatment-storage_control)/dimension`.

The primary direction is negative. The controller updates its utility and cost
exponentially at segment boundaries, with an exact tie-to-apply rule. The first
segment is warmup. Adaptation is measured only within declared post-shift
segments and is censored at segment end.

## Qualification contract

The source, compiler, validator, tests, compiled artifact, `AGENTS.md`, and
campaign-manifest artifact are recursively closed and digest-bound. The frozen
generator roster has six synthetic families, 256 rows per trajectory, eight
segments, and a no-conditional-draw/no-redraw/no-future-data rule. Fit uses 48
seeds beginning at 9000; tune uses 24 seeds beginning at 10000; assessment
seeds begin at 11000 but assessment remains absent until every lock and a
separate real-execution authorization exists.

The fixed controls are batch-one SGD, lambda-zero, always-apply,
matched-random, noise-floor, and oracle-feature SGD. Raw family rows and
counter evidence are mandatory. Holm adjustment, power `0.80`, ICC `0.50`,
minimum effect `0.05`, three repeats, null behavior, storage bytes, operations,
updates, latency, and measured joules are predeclared. Caller-supplied gate
booleans are forbidden.

## Authorization boundary

Implementation is prohibited until an independent reviewer returns a signed,
packet-bound `ACCEPT` for the exact frozen bytes. After `ACCEPT`, only
synthetic qualification is allowed. A synthetic `candidate` is required before
any separate real-execution authorization, fresh custody/manifests,
GiveMeANode allocation, H100 job, privileged joule capture, or publication
gate. Any failed review, qualification, lock, custody, resource, statistical,
energy, or validator gate closes V9 without retuning.

V6, V7, V8, Phase 836, and the plasticity guard remain closed historical lanes.
Astral remains isolated. No SOTA or production claim is authorized.

Every mutation in this phase names state slice
`oaklab-experience-learning-h100-replication-v9`.
