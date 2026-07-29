# V28 Gate 1 Acquisition-Qualification Implementation Notes

State slice:
`astral-rgs-v28-gate1-acquisition-qualification-implementation`.

Status: `ImplementationFrozen / HermeticTestsPass /
ModelAccessNotRun / OneShotExecutionAuthorized`.

## Implemented boundary

The Astral side now contains an independent, fail-closed consumer under
`tools/astral-rgs-acquisition-v28-gate1/`. It does not import the RGS producer.
It freezes and recomputes:

- immutable V28R2 packet and corpus identities;
- two nonpersistent and seven persistent arm identities;
- three seeds, three orders, and the exact update/storage budget;
- raw-score A-D argmax with deterministic lowest-index tie handling;
- token-input, observation, cell, packet, and artifact hashes;
- preparation/update/evaluation process separation and source isolation;
- exact balanced-superblock futility arithmetic;
- family-cluster accuracy bounds and gain thresholds;
- the paired family-level no-update reference at
  `sha256:52f1da63e9446e43a927713f95168371137bf49d0e4287dfae9ff1c3fb604705`;
- arm stopping semantics and final Gate 1 disposition;
- absence of retention/recovery, selection, assessment, confirmation, and
  independent-replication promotion.

The RGS side implements the corresponding target-blind source projection,
deterministic replay, sparse-gradient layer selection, multiscale clocks,
modular and compressed task states, representation anchors, isolated MLX
workers, external-information controls, one-shot coordinator, and durable
failure records.

## Leakage control

The update bundle contains one row per V28R2 family and only immutable source
and support text plus their hashes. Its construction never reads `target_index`
or query records. Each 128-token presentation is a deterministic contiguous
window selected from the complete source/support token stream by family-id
hash. Evaluation questions, options, expected labels, baseline scores, and
target indices are rejected if they enter an update row.

The persistent evaluator receives only the saved state, label-blind query
bundle, and a non-model answer key used after each balanced inference block for
futility and correctness. It receives no source rows or retrieval index.

## Execution boundary

No model, tokenizer, optimizer, adapter, external-information control, or
campaign ledger was accessed or created in this implementation slice. Before
execution, both implementations must be committed and clean, the exact cached
checkpoint must pass inventory, and a separate one-shot authorization must
bind those commits. The first claimed campaign is consuming even if it fails.

Passing implementation tests establish only local instrument coverage. They do
not establish acquisition, retention, recovery, continual learning, model
self-improvement, benchmark performance, independent replication, or a
breakthrough.
