# Phase 443 HSAI Tiny Z3 Accepted Append Decision Candidate Notes

State slice: `Phase 443 HSAI tiny Z3 accepted-append decision candidate metadata`.

Phase 443 implements deterministic pure-data accepted-append decision candidate
metadata over one Phase 441 tiny-Z3 accepted-append preflight review. The
candidate stores only digests, reviewer metadata, proposal metadata,
accepted-append preflight review label, bounded candidate disposition, explicit
nonclaims, and nonpromotion flags. It does not write filesystem artifacts,
mutate the accepted Evidence Ledger, change accepted append policy, create
accepted formal evidence, create Level2+ evidence, populate score axes,
generate proof artifacts, generate checker transcripts, generate solver
certificates, run Lean, run new SMT, run COBALT, run Rust-to-Lean extraction,
submit benchmarks, claim semantic correctness, claim production readiness,
claim SOTA, claim breakthrough status, claim full security, or grant authority
to execute an action.

## Implemented Surface

The implementation is additive in `crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalTinyDigestBackendZ3AcceptedAppendDecisionCandidateInput`;
- `GatewayFormalTinyDigestBackendZ3AcceptedAppendDecisionCandidate`;
- `GatewayFormalTinyDigestBackendZ3AcceptedAppendDecisionCandidateDisposition`;
- `GatewayFormalTinyDigestBackendZ3AcceptedAppendDecisionCandidateIssue`;
- `GatewayFormalTinyDigestBackendZ3AcceptedAppendDecisionCandidateValidation`;
- `gateway_formal_tiny_digest_backend_z3_accepted_append_decision_candidate_claim_boundary`;
- `gateway_formal_tiny_digest_backend_z3_accepted_append_decision_candidate_required_nonclaims`;
- `build_gateway_formal_tiny_digest_backend_z3_accepted_append_decision_candidate`;
- `validate_gateway_formal_tiny_digest_backend_z3_accepted_append_decision_candidate_input`.

## Candidate Dispositions

The implemented candidate dispositions are:

- `tiny_z3_decision_candidate_scope_acceptable`;
- `tiny_z3_decision_candidate_rejected`;
- `tiny_z3_accepted_append_decision_still_blocked`;
- `tiny_z3_accepted_ledger_mutation_still_blocked`;
- `tiny_z3_level2_evidence_still_blocked`.

The three blocking labels remain non-promotional. They do not authorize accepted
append policy changes, accepted Evidence Ledger mutation, accepted evidence,
Level2+ evidence, or score axes.

## Required Bindings

Each candidate input must bind:

- one Phase 441 accepted-append preflight review digest;
- one Phase 441 accepted-append preflight review input digest;
- one Phase 439 accepted-append preflight digest;
- one Phase 439 accepted-append preflight input digest;
- one Phase 437 proposal-candidate review digest;
- one Phase 437 proposal-candidate review input digest;
- one Phase 435 proposal candidate digest;
- one Phase 435 proposal candidate input digest;
- one Phase 433 materialized audit package review digest;
- one Phase 431 materialized audit package manifest digest;
- one Phase 429 serialization-preview review digest;
- one Phase 427 serialization-preview digest;
- one Phase 425 audit package digest;
- one Phase 423 review-record digest;
- one Phase 421 local reviewed metadata digest;
- one Phase 405 local Z3 output manifest digest;
- one Phase 404 local Z3 execution digest;
- declared file digest map digest;
- explicit nonclaims and their digest;
- reviewer policy id;
- reviewer decision id;
- proposal policy id;
- proposal candidate id;
- proposal review id;
- append preflight id;
- append preflight review id;
- accepted append decision candidate id;
- candidate created timestamp;
- current accepted append blocker digest;
- accepted-append preflight review label;
- accepted-append decision candidate disposition.

## Rejection Cases

Validation rejects:

- wrong schema version;
- invalid accepted append decision candidate id;
- invalid reviewer policy id;
- invalid reviewer decision id;
- invalid proposal policy id;
- invalid proposal candidate id;
- invalid proposal review id;
- invalid append preflight id;
- invalid append preflight review id;
- missing candidate timestamp;
- zero required digests;
- Phase 441 review digest drift;
- promoted or drifted Phase 441 review state;
- accepted append blocker drift;
- nonclaim drift;
- candidate summaries that claim accepted evidence, Level2+ evidence,
  score-axis evidence, proof authority, checker authority, solver-certificate
  authority, benchmark evidence, semantic correctness, production readiness,
  SOTA, breakthrough status, full security, or action authority;
- accepted evidence mutation requests;
- accepted append policy change requests;
- accepted formal evidence creation;
- Level2+ evidence creation;
- score-axis population;
- proof artifact promotion;
- checker transcript promotion;
- solver certificate promotion;
- benchmark or SOTA comparison claims;
- semantic correctness claims;
- production-readiness claims;
- SOTA claims;
- breakthrough claims;
- full-security claims;
- action-authority claims.

## Claim Boundary

The maximum claim after Phase 443 is:

HSAI can construct deterministic digest-only decision candidate metadata for
one Phase 441 tiny-Z3 accepted-append preflight review while preserving the
current accepted append and accepted-ledger blockers.

This is not accepted evidence, not formal proof, not new backend execution, not
a Lean/COBALT/Rust-to-Lean run, not Level2+ evidence, not score-axis evidence,
not semantic correctness, not production readiness, not SOTA, not breakthrough
status, and not full security.

## Tests

Phase 443 adds tests that:

- build deterministic accepted-append decision candidate metadata;
- verify the candidate binds the Phase 441 review digest;
- verify the candidate binds the Phase 441 review input digest;
- verify the Phase 439, Phase 437, Phase 435, Phase 404, and Phase 405 digests
  remain bound through the candidate;
- verify blocking candidate dispositions remain non-promotional;
- reject Phase 441 review digest drift;
- reject promotional candidate-summary text;
- reject accepted-evidence, Level2, score-axis, proof, checker, solver, SOTA,
  full-security, and action-authority promotion attempts.

## Next Slice

The next responsible slice is Phase 444: a docs-first boundary for decision
candidate review metadata over the Phase 443 candidate. That boundary must keep
review metadata separate from accepted formal evidence, accepted Evidence
Ledger mutation, accepted append policy changes, Level2+ evidence, score axes,
Lean execution, new SMT execution, COBALT execution, Rust-to-Lean extraction,
semantic correctness, production readiness, SOTA, breakthrough status, full
security, and action authority.
