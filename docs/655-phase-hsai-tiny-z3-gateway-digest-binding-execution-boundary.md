# Phase 655 HSAI Tiny-Z3 Gateway Digest-Binding Execution Boundary

State slice: `phase-655-hsai-tiny-z3-gateway-digest-binding-execution-boundary`.

Phase 655 opens the first narrow execution-boundary phase after the Phase 654
responsible pre-execution architecture closure. It names one backend lane and
one target property. It does not execute the backend.

## Backend Lane

The only lane named by this boundary is:

```text
TinyZ3ReplayExtension
```

Lean, COBALT, Rust-to-Lean extraction, federated proof dispatch, DeepProve,
zkML, Aeneas, Hax, Coq, TLA+, CBMC, and repository-scale benchmark execution
remain out of scope.

## Target Property

The only target property named by this boundary is:

```text
gateway_proposal_digest_binding_determinism_v1
```

The property is intentionally small:

```text
For one selected non-secret gateway proposal fixture shape, the normalized
proposal fields bind to a deterministic proposal digest. The same normalized
input must produce the same digest label, and selected single-field mutations
must produce a different digest label.
```

This property is not:

```text
gateway semantic correctness
attestation correctness
model-output correctness
accepted-evidence correctness
production readiness
SOTA
full security
```

## Required Inputs For A Later Execution Phase

A later implementation phase may execute only if it supplies all of the
following local non-secret inputs:

1. One exact Phase 650 execution packet with:
   - `lane_class = TinyZ3ReplayExtension`;
   - `status = NotRun`;
   - `classification = LocalExecutionPacketMetadataRecorded`.
2. One Phase 653 local tiny-Z3 extension observation binding, used only as
   prior local observation context, not as accepted evidence.
3. One static SMT-LIB2 obligation for
   `gateway_proposal_digest_binding_determinism_v1`.
4. One static expected-output grammar.
5. One executable identity digest for the local `z3` executable.
6. One fixed argv digest for `-in -smt2`.
7. One empty-environment digest.
8. One timeout policy digest.
9. One transcript redaction policy digest.
10. One artifact quarantine policy digest.
11. One replay instruction digest.
12. One nonpromotion digest binding all negative claim flags.

The later execution phase must reject secrets, credentials, raw provider
payloads, network endpoints, shell fragments, inherited environments,
undeclared input files, accepted Evidence Ledger paths, score-axis paths,
benchmark output paths, and proof-promotion paths.

## Required Output Shape For A Later Execution Phase

A later implementation may record only local quarantined output metadata:

- execution result id;
- source Phase 650 packet digest;
- source Phase 653 observation digest;
- property id;
- obligation digest;
- executable digest;
- argv digest;
- environment digest;
- timeout policy digest;
- bounded stdout summary digest;
- bounded stderr summary digest;
- solver verdict label;
- output classification digest;
- transcript redaction report digest;
- artifact quarantine report digest;
- replay instruction digest;
- nonpromotion digest.

It must not retain raw stdout, raw stderr, raw solver logs, proof artifacts,
checker transcripts, solver certificates, accepted Evidence Ledger files,
score-axis files, benchmark outputs, or external-result imports.

## Required Failure Taxonomy

A later implementation must classify at least these failure modes:

- missing executable;
- executable digest mismatch;
- invalid Phase 650 source packet;
- invalid Phase 653 source observation;
- invalid obligation digest;
- invalid expected-output grammar;
- timeout;
- solver unknown;
- solver invalid output;
- transcript mismatch;
- nondeterministic replay;
- raw transcript retention attempt;
- artifact quarantine violation;
- promotion attempt.

## Required Negative Promotion Tests

Before any later run output can be committed, focused tests must prove rejection
for:

- accepted-evidence creation;
- accepted formal-evidence creation;
- accepted Evidence Ledger mutation;
- Level2+ evidence creation;
- score-axis population;
- proof artifact creation;
- checker transcript creation;
- solver certificate creation;
- raw transcript retention;
- benchmark evidence creation;
- semantic-correctness claim;
- production-readiness claim;
- SOTA claim;
- breakthrough claim;
- full-security claim;
- external-audit claim;
- human-review acceptance claim;
- action-authority claim.

## Evidence Ceiling

The ceiling after Phase 655 remains:

```text
Level1LocalReplayOrLower execution-boundary metadata only.
```

Phase 655 does not create:

```text
backend execution
accepted evidence
accepted formal evidence
Level2+ evidence
score-axis evidence
proof artifacts
checker transcripts
solver certificates
benchmark evidence
semantic correctness
production readiness
SOTA
full security
```

## Next Responsible Phase

The next responsible phase may implement a local run only if it preserves this
boundary exactly. That phase should be named separately and should run at most
one tiny-Z3 obligation for `gateway_proposal_digest_binding_determinism_v1`.

The next phase must not broaden into:

- Lean;
- COBALT;
- Rust-to-Lean extraction;
- repository-scale benchmarks;
- multiple unrelated obligations;
- accepted evidence;
- Level2+ evidence;
- score-axis evidence;
- production, SOTA, semantic-correctness, or full-security claims.

## Defensible Claim

The strongest defensible claim after Phase 655 is:

```text
HSAI has a narrow tiny-Z3 execution boundary for one gateway proposal
digest-binding determinism property, with explicit hermetic input,
quarantine, replay, failure-taxonomy, and nonpromotion requirements.
```

It does not justify:

```text
HSAI ran the Phase 655 backend.
HSAI proved gateway correctness.
HSAI has accepted formal evidence.
HSAI has Level2+ evidence.
HSAI populated score axes.
HSAI is production ready.
HSAI is SOTA.
HSAI is fully secure.
```
