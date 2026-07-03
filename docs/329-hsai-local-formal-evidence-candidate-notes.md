# Phase 329 HSAI Local Formal Evidence Candidate Notes

State slice: `Phase 329 HSAI local formal-evidence candidate data model`.

## Boundary

Phase 329 implements the first local formal-evidence candidate data model for
the real formal command lane. It binds a read-back Phase 327 quarantined
fixed-SMT execution output to the Phase 323 source bundle, Phase 325 preflight,
Phase 326 process output digest, fixed executable digest, fixed argv template
digest, solver verdict, stream summaries, replay descriptor, verifier policy,
reviewer policy, source correspondence statement, and explicit nonclaims.

This is candidate evidence only. It is not reviewed formal evidence, accepted
formal evidence, Level2+ evidence, score-axis evidence, proof authority,
semantic correctness, production readiness, SOTA, breakthrough status, full
security, or authority to execute an action.

## Implemented Surface

Phase 329 adds:

- `GATEWAY_FORMAL_REAL_COMMAND_LANE_FORMAL_EVIDENCE_CANDIDATE_SCHEMA_VERSION`.
- `GATEWAY_FORMAL_REAL_COMMAND_LANE_FORMAL_EVIDENCE_CANDIDATE_STATE_SLICE`.
- `GATEWAY_FORMAL_REAL_COMMAND_LANE_FORMAL_EVIDENCE_CANDIDATE_CLAIM_BOUNDARY`.
- `GatewayFormalRealCommandLaneFormalEvidenceCandidateInput`.
- `GatewayFormalRealCommandLaneFormalEvidenceCandidate`.
- `GatewayFormalRealCommandLaneFormalEvidenceCandidateIssue`.
- `GatewayFormalRealCommandLaneFormalEvidenceCandidateValidation`.
- Candidate nonclaim helpers.
- `build_gateway_formal_real_command_lane_formal_evidence_candidate`.
- `validate_gateway_formal_real_command_lane_formal_evidence_candidate_input`.

## Validation Rules

Candidate construction requires:

- Phase 323 manifest digest match;
- Phase 325 preflight digest match;
- Phase 327 output-bundle manifest digest match;
- Phase 326 process-output digest match through the Phase 327 manifest;
- fixed executable digest match;
- fixed argv template digest match;
- SMT-LIB2 obligation digest match;
- expected-output grammar digest match;
- replay command descriptor digest match;
- `SolverUnsatWithoutCertificate` verdict;
- nonempty source correspondence statement;
- single-segment verifier and reviewer policy ids;
- exact Phase 329 nonclaim set;
- no accepted-evidence output path;
- no Level2+ request;
- no score-axis request;
- no whole-system proof, semantic-correctness, production-readiness, SOTA,
  breakthrough, full-security, or authority claim;
- no raw log, raw provider response, secret, or undeclared-file reliance;
- no checker-transcript or solver-certificate promotion request.

## Tests

Focused tests cover:

- valid candidate construction from a real Phase 326/327 hermetic fixed-SMT
  output;
- preservation of the promotion ladder:
  `quarantined_output -> formal_evidence_candidate -> reviewed_formal_evidence`;
- all proof/evidence/score/claim/authority flags held false;
- stale preflight digest rejection;
- accepted-evidence/SOTA/score-axis promotion rejection;
- nonclaim drift rejection;
- non-eligible solver verdict rejection;
- raw-log and checker-transcript-promotion reliance rejection.

## Claim Boundary

Phase 329 supports this claim:

```text
HSAI has a local formal-evidence candidate lane for one gateway admission
invariant, with digest-bound replay, nonclaim preservation, and explicit
promotion rejection.
```

It does not support accepted formal evidence, reviewed formal evidence, Level2+
formal evidence, score-axis evidence, a system Z3 proof, a Lean proof, a COBALT
containment proof, Rust-to-Lean extraction, source correspondence proof,
whole-system proof, semantic correctness, production readiness, SOTA,
breakthrough status, full security, accepted Evidence Ledger mutation, or
authority to execute an action.

## Next Slice

Phase 330 may implement a local reviewed-formal-evidence preview boundary for a
Phase 329 candidate. That slice must still avoid accepted Evidence Ledger
mutation, Level2+ evidence, score-axis population, SOTA claims, full-security
claims, production-readiness claims, semantic-correctness claims, and action
authority.
