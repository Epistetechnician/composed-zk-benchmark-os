# Phase 410 HSAI Tiny Z3 Reviewed Formal Evidence Record Boundary

State slice: `Phase 410 HSAI tiny Z3 reviewed-formal-evidence record boundary`.

## Boundary

Phase 410 defines the docs-first boundary for a future reviewed-formal-evidence
record over a Phase 409 local tiny-Z3 review preview for:

```text
gateway-local-digest-binding-determinism-v1
```

This phase does not implement reviewed-record code, accepted evidence code,
Level2+ evidence, score-axis population, proof artifact generation, checker
transcript generation, solver certificate generation, Lean execution, COBALT
execution, Rust-to-Lean extraction, benchmark submission, production
deployment, or action authority.

The reviewed record remains below accepted evidence:

```text
quarantined_z3_output_bundle
-> formal_evidence_candidate
-> reviewed_formal_evidence_preview
-> reviewed_formal_evidence
-> accepted_formal_evidence
```

No state transition may skip a state. Phase 410 authorizes no state transition
by itself.

## Reviewed Record Inputs

A future tiny-Z3 reviewed-formal-evidence record must bind:

- Phase 409 review-preview digest.
- Phase 409 review-preview input digest.
- Phase 407 candidate digest.
- Phase 407 candidate input digest.
- Phase 405 output-manifest digest.
- Phase 404 execution digest.
- Phase 403 probe digest.
- Reviewer policy id.
- Verifier policy id.
- Reviewer decision id.
- Reviewer decision timestamp.
- Reviewer decision label.
- Reviewed-scope statement digest.
- Reviewer nonclaim acknowledgement digest.
- Source correspondence statement digest.
- Replay-readiness checklist digest.
- Promotion-rejection checklist digest.
- Accepted-evidence-disabled acknowledgement digest.

The future record must fail closed if any digest is missing, zero, stale, or
inconsistent with the Phase 409 preview.

## Required Preview Decision

A future reviewed-formal-evidence record may be emitted only for this Phase 409
decision:

```text
ReviewPreviewAcceptCandidateScope
```

The following Phase 409 decisions must not produce a reviewed record:

- `ReviewPreviewRejectCandidateScope`;
- `ReviewPreviewNeedsReplay`;
- `ReviewPreviewNeedsCheckerLane`.

Those decisions may support diagnostics or follow-up work, but not reviewed
formal evidence.

## Required Rejection Cases

A future reviewed-record implementation must reject if:

- the Phase 409 preview digest does not match the preview input;
- the Phase 409 preview is not exactly in
  `reviewed_formal_evidence_preview` state;
- the Phase 409 preview decision is not
  `ReviewPreviewAcceptCandidateScope`;
- the Phase 409 preview has any proof, checker-transcript,
  solver-certificate, reviewed-evidence, accepted-evidence, Level2+,
  score-axis, production-readiness, SOTA, breakthrough, full-security,
  semantic-correctness, or authority flag set;
- the candidate digest, candidate-input digest, Phase 405 output-manifest
  digest, Phase 404 execution digest, or Phase 403 probe digest does not match
  the preview;
- the reviewer policy id or verifier policy id does not match the preview;
- the reviewed-scope statement is empty or claims more than the Phase 407
  candidate and Phase 409 preview authorize;
- the reviewer nonclaim acknowledgement does not exactly match the preview
  nonclaims;
- the source correspondence statement digest does not match the preview;
- the replay-readiness checklist does not bind the Phase 403, 404, 405, 407,
  and 409 digests;
- the promotion-rejection checklist does not explicitly reject accepted
  evidence, Level2+ evidence, score axes, SOTA, breakthrough, full-security,
  semantic-correctness, production-readiness, and action authority;
- the accepted-evidence-disabled acknowledgement is missing;
- the record tries to mutate accepted evidence;
- the record tries to create accepted formal evidence;
- the record tries to create Level2+ evidence;
- the record tries to populate score axes;
- the record claims benchmark comparison or SOTA status.

## Evidence Meaning

The maximum future claim from a tiny-Z3 reviewed-formal-evidence record is:

```text
HSAI has a local reviewed formal-evidence record stating that one Phase 407
tiny-Z3 candidate passed a Phase 409 scoped review preview under explicit
review policy, source correspondence statement, nonclaims, replay-readiness
checks, promotion-rejection checks, and accepted-evidence-disabled
acknowledgement.
```

That still is not:

- accepted formal evidence;
- Level2+ evidence;
- score-axis evidence;
- a Lean proof;
- a COBALT containment proof;
- a Rust-to-Lean proof;
- a checker transcript;
- a solver certificate;
- a source correspondence proof;
- whole-system proof;
- semantic correctness;
- production readiness;
- SOTA;
- breakthrough status;
- full security;
- authority to execute an action.

## SOTA-Quality Direction

Phase 410 improves evidence quality by defining a typed, digest-bound reviewed
record for the actual tiny-Z3 lane. It does not turn the lane into accepted
evidence. The responsible path remains:

1. Candidate metadata binds source, solver, execution, and output digests.
2. Review preview classifies the candidate under explicit nonclaims.
3. Reviewed record binds only the accept-preview decision and keeps promotion
   blockers explicit.
4. Accepted formal evidence remains a separate future state through a separate
   accepted-evidence handoff and append-policy path.
5. Level2+, score-axis, SOTA, semantic-correctness, production-readiness, and
   full-security claims remain blocked until their own evidence classes and
   acceptance policies exist.

## Code Phase Exit Criteria

Phase 411 may implement reviewed-record metadata only if it adds:

- a tiny-Z3 reviewed-formal-evidence record input data model;
- a tiny-Z3 reviewed-formal-evidence record data model;
- deterministic digesting for reviewed-record inputs and records;
- validation from a Phase 409 preview;
- canonical reviewed-scope and accepted-evidence-disabled acknowledgement
  helpers;
- fail-closed rejection for every Phase 410 rejection case;
- tests allowing only `ReviewPreviewAcceptCandidateScope`;
- tests rejecting reject-preview, needs-replay, and needs-checker-lane
  decisions;
- tests for preview digest drift, policy drift, nonclaim drift, checklist
  drift, accepted-evidence attempts, Level2+ attempts, score-axis attempts,
  and SOTA attempts;
- no accepted Evidence Ledger mutation;
- no accepted formal evidence;
- no Level2+ evidence;
- no score-axis population.

## Next Slice

Phase 411 may implement the local tiny-Z3 reviewed-formal-evidence record
metadata. It must not mutate accepted evidence, create accepted formal evidence,
create Level2+ evidence, populate score axes, claim semantic correctness, claim
production readiness, claim SOTA, claim breakthrough status, claim full
security, or grant authority to execute an action.
