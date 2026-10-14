# V41R27R19 Offline Provenance Differential Audit Record

State slice: `V41R27R19OfflineProvenanceDifferentialAudit`.

## Scope

This audit compares the recorded provenance of the terminal V41R27R19 failure
with the retained V41R30R1/R2 replications and V41R31R4 paired diagnosis. It
does not run compute or infer missing worker payload content.

## Confirmed matching bindings

The records agree on:

- RGS source commit:
  `c3b287d4227db94a43af7888d0211fb337c330fa`;
- frozen worker identity:
  `v41r27-panel-8-seed-412019`;
- source archive SHA-256:
  `sha256:8b1802d97b14d83b6d6d4596589664885efd973cec1e02ac03250acf0e250645`;
- H100 execution target and CUDA-backed runtime family;
- model/tokenizer frozen identity;
- pinned package family: PyTorch `2.10.0`, Transformers `4.57.6`,
  PEFT `0.18.1`;
- optimizer, 256-step worker, protected gate, acquisition gate, and
  no-retry governance.

V41R31R4 additionally verified identical source, runner, method, instrument,
requirements, runtime, geometry, quantization, contract, adapter, and
trainable-state hashes between its control and deterministic intervention.

## Missing evidence

The V41R27R19 failing worker payload is not present in the current Astral
worktree. Its original runtime disk was lost before a durable artifact became
available. The V41R27R19 record retains the terminal observation
`pass:false`, protected accuracy `1.0`, and command identity, but not the
worker-result JSON or adapter bundle.

Therefore this audit cannot compare the original failure's receipts, adapter
state, score rows, or per-step hashes against V41R30/V41R31. It cannot prove
or disprove hidden worker-state divergence inside the lost payload.

## Diagnosis

No recorded provenance mismatch explains the original failure. The remaining
evidence-supported hypotheses are:

1. history-dependent process state not captured by the frozen provenance fields;
2. rare stochastic or scheduling behavior outside the tested deterministic
   controls;
3. an unrecorded state difference inside the lost V41R27R19 runtime payload.

The third hypothesis is now untestable from the current custody set unless the
original bundle is recovered externally. Any new test of the first or second
hypothesis requires a separately preregistered identity.

V41R27 remains terminal at census `30/48`, qualification `NotAssessed`.
No qualification, continual-self-improvement, introspection, SOTA,
production-readiness, or breakthrough claim is supported.

Claim ceiling:
`OfflineV41R27R19ProvenanceDifferentialAuditWithLostOriginalPayload`.
