# Phase M Recursion Envelope Stress Spec

## Status And Claim Boundary

Phase M is opened for docs-first boundary specification only.

This phase defines the recursion-envelope stress lane after Phase L local soak
acceptance. It does not authorize implementation code, live gnark execution,
external repository checkout, external result import, benchmark outputs,
official benchmark evidence, Level2+ evidence creation, or any claim that a
recursion proof is semantic proof.

The current authorized state slice is:

```text
docs/63-phase-m-recursion-envelope-stress-spec.md
docs/12-task-list.md
README.md
AGENTS.md
```

All artifacts described here are design contracts until a future explicit phase
opens implementation.

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

A future `RecursionEnvelopeCandidate` should be inert Rust data. It should
describe:

- envelope id;
- source artifact digest set;
- input claim boundaries;
- input evidence classifications;
- recursion depth;
- aggregation width;
- digest-chain root;
- verifier acceptance status, if a future executable adapter is authorized;
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

Future Phase M implementation should validate:

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

## Next Implementation Slice

The next Phase M slice, if explicitly authorized, should be local Rust contract
types and validation tests only:

```text
RecursionEnvelopeCandidate
RecursionEnvelopeInputRef
RecursionEnvelopeValidation
claim-boundary non-escalation tests
metric-label absence tests
```

That future slice should still avoid live gnark execution and should not produce
benchmark outputs.
