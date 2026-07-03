# Phase 407 HSAI Tiny Z3 Formal Evidence Candidate Notes

State slice: `Phase 407 HSAI tiny Z3 formal-evidence candidate`.

## Boundary

Phase 407 implements local formal-evidence candidate metadata for the tiny Z3
lane:

```text
gateway-local-digest-binding-determinism-v1
```

The candidate binds Phase 403 probe metadata, Phase 404 fixed local Z3
execution metadata, and the Phase 405 read-back output manifest. It remains
local candidate metadata only. It is not reviewed formal evidence, accepted
formal evidence, Level2+ evidence, score-axis evidence, proof authority,
semantic correctness, production readiness, SOTA, breakthrough status, full
security, or authority to execute an action.

## Implemented Surface

Phase 407 adds these Rust surfaces under `hsai-agent-admission`:

- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_FORMAL_EVIDENCE_CANDIDATE_SCHEMA_VERSION`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_FORMAL_EVIDENCE_CANDIDATE_STATE_SLICE`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_FORMAL_EVIDENCE_CANDIDATE_CLAIM_BOUNDARY`;
- `GatewayFormalTinyDigestBackendZ3FormalEvidenceCandidateInput`;
- `GatewayFormalTinyDigestBackendZ3FormalEvidenceCandidate`;
- `GatewayFormalTinyDigestBackendZ3FormalEvidenceCandidateIssue`;
- `GatewayFormalTinyDigestBackendZ3FormalEvidenceCandidateValidation`;
- `gateway_formal_tiny_digest_backend_z3_formal_evidence_candidate_claim_boundary`;
- `gateway_formal_tiny_digest_backend_z3_formal_evidence_candidate_required_nonclaims`;
- `build_gateway_formal_tiny_digest_backend_z3_formal_evidence_candidate`;
- `validate_gateway_formal_tiny_digest_backend_z3_formal_evidence_candidate_input`.

## Required Bindings

Candidate construction binds:

- Phase 403 probe digest;
- Phase 403 probe input digest;
- Phase 404 execution digest;
- Phase 404 execution input digest;
- Phase 405 output manifest digest;
- Phase 405 declared file digests;
- command descriptor digest;
- SMT-LIB2 obligation digest;
- process output digest;
- stdout and stderr summary digests;
- solver verdict label;
- replay command descriptor digest;
- source correspondence statement;
- verifier and reviewer policy ids;
- exact Phase 407 nonclaims.

## Validation Rules

Validation rejects:

- stale or missing probe digests;
- stale or missing execution digests;
- stale or missing Phase 405 output-manifest digests;
- undeclared or missing declared file digests;
- non-`SolverUnsatWithoutCertificate` verdicts;
- missing or overclaiming source correspondence statements;
- missing verifier or reviewer policy ids;
- nonclaim drift;
- claim-boundary drift;
- accepted-evidence path requests;
- Level2+ requests;
- score-axis requests;
- raw-log, raw-provider-response, secret, or undeclared-file reliance;
- checker-transcript or solver-certificate promotion requests;
- semantic-correctness, production-readiness, SOTA, breakthrough,
  full-security, whole-system-proof, or action-authority claims.

## Tests

Focused tests cover:

- valid candidate construction from a real Phase 404/405 local Z3 output when
  `/opt/homebrew/bin/z3` is present;
- preservation of the ladder:
  `quarantined_z3_output_bundle -> formal_evidence_candidate -> reviewed_formal_evidence`;
- all accepted-evidence, Level2+, score-axis, strong-claim, and authority flags
  held false;
- stale execution digest rejection;
- stale output-manifest digest rejection;
- accepted-evidence, Level2+, score-axis, SOTA, and checker-transcript
  promotion rejection;
- nonclaim drift rejection.

## Claim Boundary

Phase 407 supports only this claim:

```text
HSAI has a local formal-evidence candidate metadata lane for one tiny gateway
digest-binding property, bound to Phase 403/404/405 local Z3 artifacts,
declared digests, replay metadata, verifier/reviewer policy ids, and explicit
nonclaims.
```

It does not support reviewed formal evidence, accepted formal evidence, Level2+
formal evidence, score-axis evidence, a system Z3 proof, a Lean proof, a COBALT
containment proof, Rust-to-Lean extraction, source correspondence proof,
whole-system proof, semantic correctness, production readiness, SOTA,
breakthrough status, full security, accepted Evidence Ledger mutation, or
authority to execute an action.

## Next Slice

Phase 408 may define a docs-first reviewed-formal-evidence preview boundary for
the Phase 407 candidate. It must not mutate accepted evidence, create Level2+
evidence, populate score axes, claim semantic correctness, claim production
readiness, claim SOTA, claim breakthrough status, claim full security, or grant
authority to execute an action.
