# Phase 607 HSAI Tiny Z3 Real Materialized Operator Capture Implementation Notes

State slice: `Phase 607 HSAI tiny Z3 real materialized operator capture`.

Phase 607 implements the local staging capture surface authorized by
`docs/606-phase-hsai-tiny-z3-real-materialized-external-operator-capture-boundary.md`:

```text
Phase 605 handoff packet
  + operator-declared Phase 604 focused run telemetry
  + transcript and redaction digests
  -> quarantined local capture packet output and readback
```

This phase is a staging-data collection surface. It does not execute the
operator run, import external results, mutate the accepted Evidence Ledger,
accept independent external reproduction, create accepted formal evidence,
create Level2+ evidence, populate score axes, run Lean, run COBALT, run
Rust-to-Lean extraction, create proof artifacts, create checker transcripts,
create solver certificates, create benchmark evidence, record human-review
acceptance, or claim semantic correctness, production readiness, SOTA status,
breakthrough status, full security, global uniqueness, external audit status,
or authority to execute an action.

## Implemented Surface

Phase 607 adds local Rust types and functions under
`crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalTinyZ3RealMaterializedPhase605HandoffPacket`;
- `GatewayFormalTinyZ3RealMaterializedOperatorProvenance`;
- `GatewayFormalTinyZ3RealMaterializedExecutionObservation`;
- `GatewayFormalTinyZ3RealMaterializedTranscriptDigests`;
- `GatewayFormalTinyZ3RealMaterializedArtifactRetentionDeclaration`;
- `GatewayFormalTinyZ3RealMaterializedReviewerRouting`;
- `GatewayFormalTinyZ3RealMaterializedCaptureRedactionReport`;
- `GatewayFormalTinyZ3RealMaterializedCaptureNonpromotionReport`;
- `GatewayFormalTinyZ3RealMaterializedOperatorCaptureOutputManifest`;
- `materialize_gateway_formal_tiny_z3_real_materialized_operator_capture_output_bundle`;
- `read_gateway_formal_tiny_z3_real_materialized_operator_capture_output_bundle`.

The declared quarantined output namespace is:

```text
phase605-real-z3-materialized-operator-capture/
  manifest.json
  phase605-handoff-packet.json
  operator-provenance.json
  execution-observation.json
  transcript-digests.json
  artifact-retention-declaration.json
  reviewer-routing.json
  redaction-report.json
  nonpromotion-report.json
  digests.json
```

Each declared file gets a `.sha256` sidecar. Readback rejects missing files,
undeclared files, symlinks, stale sidecars, digest drift, malformed JSON,
invalid Phase 605 handoff binding, invalid operator provenance, skipped or
failed Phase 604 focused runs, transcript digest drift, forbidden retained
artifacts, invalid reviewer routing, invalid redaction, nonpromotion drift, and
manifest semantic drift.

## Staging Deployment Meaning

This is the deployable staging primitive:

```text
staging operator runner -> Phase 607 quarantined capture output root
```

A staging service or CLI may run the Phase 604 focused command outside this
crate, collect the required telemetry, then call the Phase 607 materializer
with a caller-selected output root. The materializer only packages and
validates the declared telemetry. It does not execute the command and does not
accept the resulting packet as evidence.

## Guardrails

The implementation requires:

- exact Phase 605 document path binding;
- exact Phase 604 focused command binding;
- nonzero Phase 603, Phase 604, and Phase 605 document digests;
- full repository commit hash;
- branch and dirty-status declaration;
- Z3 executable path and version output containing `Z3`;
- focused Phase 604 test pass;
- no skipped run;
- stdout and stderr transcript digests;
- quarantine-only artifact retention;
- reviewer routing without human-review acceptance;
- redaction report with no secrets, credentials, private machine identifiers,
  raw retained logs, raw provider responses, undeclared files, accepted
  evidence artifacts, Level2 artifacts, score-axis artifacts, proof artifacts,
  checker transcripts, solver certificates, benchmark artifacts, or production
  deployment artifacts;
- nonpromotion report keeping all stronger claims false.

## Evidence Meaning

Phase 607 supports only this claim:

```text
HSAI can locally materialize and read back a quarantined staging capture packet
for an operator-declared Phase 604 focused real-Z3 run.
```

It is not external result import, not accepted evidence, not accepted formal
evidence, not independent external reproduction accepted by the repo, not
Level2+ evidence, not score-axis evidence, not Lean proof, not SMT proof
authority, not COBALT containment evidence, not Rust-to-Lean proof, not checker
transcript authority, not solver certificate authority, not benchmark evidence,
not external audit, not SOTA, not semantic correctness, not production
readiness, not full security, and not authority to execute an action.

## Tests

Focused tests cover:

- successful Phase 607 materialization and readback;
- stale sidecar rejection;
- forbidden retained proof artifact rejection;
- skipped or missing-Z3 run rejection;
- human-review acceptance promotion rejection.
