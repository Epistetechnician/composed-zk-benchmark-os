# Phase 656 HSAI Tiny-Z3 Gateway Digest-Binding Execution Preflight Notes

State slice: `phase-656-hsai-tiny-z3-gateway-digest-binding-execution-preflight`.

Phase 656 implements local preflight metadata for the Phase 655 narrow
execution boundary. It locks the exact target property and source bindings
needed before a later phase may run one tiny-Z3 obligation.

This phase does not execute Z3 and does not invoke any backend command.

## Implemented

- `HSAI_TINY_Z3_GATEWAY_DIGEST_BINDING_EXECUTION_PROPERTY_ID`.
- `HSAI_TINY_Z3_GATEWAY_DIGEST_BINDING_EXECUTION_PREFLIGHT_*` schema,
  state-slice, and claim-boundary constants.
- `HsaiTinyZ3GatewayDigestBindingExecutionPreflightInput`.
- `HsaiTinyZ3GatewayDigestBindingExecutionPreflight`.
- Preflight classification, label, validation, and issue types.
- Helpers for expected-output grammar, transcript redaction, artifact
  quarantine, replay instruction, failure taxonomy, required nonclaims,
  nonclaim digest, input-manifest-set digest, and nonpromotion digest.
- Build and validation helpers that require:
  - property id `gateway_proposal_digest_binding_determinism_v1`;
  - lane class `TinyZ3ReplayExtension`;
  - one exact Phase 650 `NotRun` execution packet;
  - one exact Phase 653 tiny-Z3 local observation;
  - hermetic input manifest digests;
  - fixed Z3 argv digest;
  - empty environment digest;
  - 5000 ms timeout policy digest;
  - output grammar, redaction, quarantine, replay, and failure-taxonomy
    digests;
  - `Level1LocalReplayOrLower` mapping;
  - negative promotion flags all false.

## Validation

Focused validation target:

```bash
cargo test -p hsai-agent-admission --lib phase656_hsai_tiny_z3_gateway_digest_binding_execution_preflight -- --nocapture
```

Focused tests cover:

- valid preflight metadata over Phase 650 and Phase 653 sources;
- property-id drift rejection;
- hermetic-manifest and command/output policy drift rejection;
- Phase 653 source-observation drift rejection;
- backend-command, accepted-evidence, Level2+, and SOTA promotion rejection.

## Evidence Ceiling

The ceiling after Phase 656 remains:

```text
Level1LocalReplayOrLower preflight metadata only.
```

Phase 656 is not:

- backend execution;
- Z3 execution;
- Lean execution;
- COBALT execution;
- Rust-to-Lean extraction;
- DeepProve execution;
- proof artifact generation;
- checker transcript generation;
- solver certificate generation;
- raw transcript retention;
- accepted formal evidence;
- Level2+ evidence;
- score-axis evidence;
- benchmark evidence;
- semantic correctness;
- production readiness;
- SOTA;
- full security;
- authority to execute an action.

## Next Responsible Phase

The next phase may run exactly one local tiny-Z3 obligation only if it consumes
this preflight, preserves the Phase 655 property id exactly, records bounded
stdout/stderr summaries only, and keeps every promotion flag false.

The next phase must not broaden into Lean, COBALT, Rust-to-Lean extraction,
repository-scale benchmarks, accepted evidence, Level2+, score axes,
production-readiness claims, SOTA claims, semantic-correctness claims, or
full-security claims.

## Defensible Claim

The strongest defensible claim after Phase 656 is:

```text
HSAI has local preflight metadata for one tiny-Z3 gateway proposal
digest-binding determinism obligation, with exact property, source, hermetic
input, command-policy, quarantine, replay, failure-taxonomy, and nonpromotion
bindings.
```

It does not justify:

```text
HSAI ran Z3 for Phase 656.
HSAI proved gateway correctness.
HSAI has accepted formal evidence.
HSAI has Level2+ evidence.
HSAI populated score axes.
HSAI is production ready.
HSAI is SOTA.
HSAI is fully secure.
```
