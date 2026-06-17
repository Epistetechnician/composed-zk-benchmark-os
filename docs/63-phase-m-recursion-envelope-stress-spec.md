# Phase M Recursion Envelope Stress Spec

## Status And Claim Boundary

Phase M is implemented for inert local contract types and inert
adapter-preparation metadata.

This phase defines the recursion-envelope stress lane after Phase L local soak
acceptance. The current implementation slice includes local Rust data types,
serialization helpers, validation results, claim-boundary tests, fixture-backed
validation checks, and adapter-preparation metadata only. It does not authorize
live gnark execution, Go code, external repository checkout, external result
import, benchmark outputs, official benchmark evidence, Level2+ evidence
creation, or any claim that a recursion proof is semantic proof.

The current authorized state slice is:

```text
docs/63-phase-m-recursion-envelope-stress-spec.md
docs/12-task-list.md
README.md
AGENTS.md
crates/zkbench-core/src/recursion.rs
crates/zkbench-core/tests/phase_m_recursion_envelope.rs
crates/zkbench-core/tests/fixtures/phase_m_recursion_envelope_valid.json
crates/zkbench-core/tests/fixtures/phase_m_recursion_envelope_invalid.json
```

All Phase M Rust artifacts are inert local contract data until a future explicit
phase opens executable adapter work.

## Purpose

Phase M should stress recursive proof envelopes as evidence transport, not as a
semantic correctness oracle. The useful question is:

```text
Can a recursion envelope bind a bounded set of already-classified local
artifacts without hiding weak evidence or raising its claim boundary?
```

The answer must remain claim-capped by the weakest input. A recursion envelope
can make aggregation structure testable; it cannot make a local replay into
official benchmark evidence or a machine-checked semantic proof.

## Inputs

Future implementation may consume only local, non-secret, already-classified
inputs:

- local replay manifests;
- local replay results;
- benchmark pack manifests;
- artifact digest sets;
- evidence-record candidates;
- append previews;
- local health reports;
- explicit claim-boundary labels.

Inputs must carry stable artifact hashes. Any missing hash, ambiguous claim
boundary, forbidden positive claim text, or unclassified input must fail closed.

## Recursion Envelope Model

`RecursionEnvelopeCandidate` is inert Rust data. It describes:

- envelope id;
- source artifact digest set;
- input claim boundaries;
- input evidence classifications;
- recursion depth;
- aggregation width;
- digest-chain root;
- optional verifier acceptance status, which remains metadata only unless a
  future executable adapter is authorized;
- output claim boundary;
- explicit limitations.

The output claim boundary must be the minimum supported by the input evidence
and the recursion statement. In this repo's current Level 1 foundation, the
output remains local metadata unless a future reviewed phase admits stronger
evidence.

## Candidate Metrics

Phase M may define metric names but must not populate official benchmark scores
in this docs-first phase.

Candidate metric labels:

- `recursion_depth`;
- `aggregation_width`;
- `envelope_digest_chain_length`;
- `envelope_input_count`;
- `envelope_verification_status`;
- `recursion_proof_size_bytes`;
- `recursion_verifier_time_ms`;
- `recursion_prover_time_ms`;
- `recursion_memory_bytes`.

Timing, memory, and proof-size labels are future adapter metrics only. They must
not be produced by local soak telemetry and must not be reported as ZK backend
performance without a future explicit execution phase.

## Validation Rules

Phase M implementation validates:

- every envelope input has a stable digest;
- every input claim boundary is explicit;
- output claim boundary does not exceed the weakest input boundary;
- recursion-specific metrics are absent unless a future execution phase is
  explicitly authorized;
- local replay artifacts remain local replay artifacts;
- append previews remain previews and do not mutate `EvidenceLedger`;
- Level2 eligibility reports remain not Level2 evidence;
- verifier acceptance is never interpreted as semantic correctness;
- recursion aggregation cannot hide rejected, quarantined, or inconclusive
  input state.

The validation-hardening slice adds fixture-backed JSON checks for one valid
local envelope candidate and one fail-closed invalid candidate. It also scans
the Phase M Rust contract file, Phase M integration test, and Phase M JSON
fixtures for executable-adapter affordances such as process spawning, network
socket/client markers, Go runner markers, external clone markers, gnark prove or
verify markers, and forbidden pre-authorization performance metric labels.

The adapter-preparation metadata slice adds:

- `RecursionAdapterPreparationPlan`;
- `RecursionAdapterPreparationArtifact`;
- `RecursionAdapterPreparationTarget`;
- `RecursionAdapterPreparationValidation`.

These structures describe only future adapter readiness metadata. Validation
rejects missing source inputs, missing expected artifacts, non-portable artifact
references, claim boundaries above `Level0DesignNote`, executable adapter
authorization, executable step lists, and missing recursion-proof limitation
text.

## Required Negative Tests

Future implementation must reject:

- envelope output claiming semantic proof from local replay inputs;
- envelope output claiming official benchmark evidence from local telemetry;
- missing artifact digest;
- stale digest-chain root;
- input claim boundary higher than its referenced artifact;
- output claim boundary higher than the weakest input;
- hidden `prover_time`, `verifier_time`, `proof_size`, or memory metric emitted
  before executable adapter authorization;
- append preview treated as accepted evidence;
- Level2 eligibility report treated as Level2 evidence.

## Non-Goals

- No live gnark execution.
- No Go code in `zkbench-core`.
- No external repo clone or vendored source.
- No external benchmark run.
- No official benchmark evidence.
- No Level2+ evidence creation.
- No dashboard.
- No claim that recursion proof is semantic proof.
- No claim that verifier acceptance proves the source spec was meaningful.

## Implemented Slice

The implemented Phase M slice is local Rust contract types, adapter-preparation
metadata, and validation tests only:

```text
RecursionEnvelopeCandidate
RecursionEnvelopeInputRef
RecursionEnvelopeValidation
claim-boundary non-escalation tests
metric-label absence tests
fixture-backed valid and invalid candidate checks
source-scan checks for forbidden executable-adapter hooks
adapter-preparation metadata and validation tests
```

This slice still avoids live gnark execution and does not produce benchmark
outputs.
