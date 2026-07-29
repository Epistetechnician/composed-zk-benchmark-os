# V28R7 Single-Cell Acquisition Pilot Execution Record

State slice: `astral-rgs-v28r7-single-cell-acquisition-pilot-execution`.

Status: `Completed / PilotNoSignal / R2Valid / ExternalReviewNotRun`.

V28R7 completed from clean RGS commit `c006c174` and Astral commit `aa8bacd`.
The immutable artifact is
`astral-rgs-v28r7-pilot-8ae838f1e467-r1`, with canonical manifest
`sha256:8ae838f1e467cb75483aa79aad170ddd168b35129bd236441b391905118d1e9f`
and packet
`sha256:930ba5df8e2f0a6d21fa4b6cd7c75f13e918b21343503a8f8b93cf1d6f640169`.

Novelty passed exactly: both unchanged-checkpoint baselines had zero
chance-normalized lift and byte-identical observations. Context and retrieval
controls nevertheless remained at `0.25`. All seven persistent arms completed
the exact 768-step, 786,432-token budget, but none passed any signal gate:

- naive, replay, sparse, nested and representation-distillation arms: `0.25`;
- modular ghost state: `0.248155`, gain `-0.001845`;
- compressed recollection: `0.249023`, gain `-0.000977`;
- every Bonferroni bootstrap lower bound was at most zero;
- no process exceeded the 8 GiB RSS ceiling.

Compressed recollection used 4,128,683 state bytes versus 17,633,077 for
modular ghost state, a 76.6% reduction, but compression did not produce
acquisition.

The first Astral report failed because its validator ordered the correct panel
set incorrectly and recomputed three nonuniform summaries with different float
arithmetic. That failed report remains immutable. The bounded R2 correction at
commit `b5b4696` read the same artifact, executed no model, and returned
`valid=true`, `errors=[]`, `PilotNoSignal`; report canonical hash
`sha256:bac9c99be9afeaedc310f7c41fb98048d43dbd69431a8e7f6712c19dfa1f2292`.

This is not evidence for acquisition, continual learning, self-improvement,
retention, recovery, selection, SOTA, confirmation, or replication. Because
both positive controls failed, the current instrument should not advance to a
powered campaign. The claim ceiling remains
`LocalSingleSeedOrderAcquisitionPilotV28R7`.
