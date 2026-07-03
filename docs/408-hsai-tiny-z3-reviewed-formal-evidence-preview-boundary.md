# Phase 408 HSAI Tiny Z3 Reviewed Formal Evidence Preview Boundary

State slice: `Phase 408 HSAI tiny Z3 reviewed-formal-evidence preview boundary`.

## Boundary

Phase 408 defines the docs-first boundary for a future reviewed-formal-evidence
preview over a Phase 407 local tiny-Z3 formal-evidence candidate for:

```text
gateway-local-digest-binding-determinism-v1
```

This phase does not implement review-preview code, reviewed evidence code,
accepted evidence code, Level2+ evidence, score-axis population, proof artifact
generation, checker transcript generation, solver certificate generation, Lean
execution, COBALT execution, Rust-to-Lean extraction, benchmark submission, or
production deployment.

The preview state is intentionally separate from reviewed evidence:

```text
quarantined_z3_output_bundle
-> formal_evidence_candidate
-> reviewed_formal_evidence_preview
-> reviewed_formal_evidence
-> accepted_formal_evidence
```

No state transition may skip a state. Phase 408 authorizes no state transition
by itself.

## Review Inputs

A future tiny-Z3 reviewed-formal-evidence preview must bind:

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
- Reviewer nonclaim acknowledgement digest.
- Source correspondence statement digest.
- Replay-readiness checklist digest.
- Promotion-rejection checklist digest.

The preview must fail closed if any digest is missing, zero, stale, or
inconsistent with the candidate.

## Decision Labels

A future preview may use only these decision labels:

| Label | Meaning |
| --- | --- |
| `review_preview_accept_candidate_scope` | The candidate is locally coherent under its declared tiny-Z3 scope and may proceed to a future reviewed-evidence implementation phase. |
| `review_preview_reject_candidate_scope` | The candidate is not locally coherent under its declared tiny-Z3 scope. |
| `review_preview_needs_replay` | The candidate cannot be reviewed without an additional declared replay artifact or replay transcript. |
| `review_preview_needs_checker_lane` | The candidate cannot support a stronger claim without an implemented checker lane. |

No decision label may append accepted evidence, create reviewed evidence, imply
Level2+ evidence, populate score axes, or support a public SOTA/security/
semantic-correctness/production-readiness claim.

## Required Rejection Cases

A future preview must reject or require replay if:

- the Phase 407 candidate digest does not match the candidate input;
- the Phase 407 candidate is not exactly in `formal_evidence_candidate` state;
- the Phase 407 candidate next required state is not
  `reviewed_formal_evidence`;
- the Phase 407 candidate has any proof, checker-transcript,
  solver-certificate, reviewed-evidence, accepted-evidence, Level2+,
  score-axis, production-readiness, SOTA, breakthrough, full-security,
  semantic-correctness, or authority flag set;
- the candidate has no source correspondence statement;
- the reviewer policy id is missing or does not match the candidate;
- the verifier policy id is missing or does not match the candidate;
- the reviewer decision id is not a single-segment id;
- the reviewer nonclaim acknowledgement does not exactly match the candidate
  nonclaims;
- the replay-readiness checklist does not bind the Phase 403, 404, 405, and
  407 digests;
- the promotion-rejection checklist does not explicitly reject accepted
  evidence, Level2+ evidence, score axes, SOTA, full-security,
  semantic-correctness, production-readiness, and authority claims;
- the preview tries to create accepted evidence;
- the preview tries to create reviewed formal evidence directly;
- the preview tries to populate score axes;
- the preview claims benchmark or SOTA comparison.

## Evidence Meaning

The maximum future claim from a tiny-Z3 reviewed-formal-evidence preview is:

```text
This local review preview records that one Phase 407 tiny-Z3 formal-evidence
candidate is ready, rejected, replay-blocked, or checker-lane-blocked under an
explicit review policy and explicit nonclaims.
```

That still is not:

- reviewed formal evidence;
- accepted formal evidence;
- Level2+ evidence;
- score-axis evidence;
- a Lean proof;
- a COBALT containment proof;
- a Rust-to-Lean proof;
- a checker transcript;
- a solver certificate;
- a source correspondence proof;
- semantic correctness;
- production readiness;
- SOTA;
- breakthrough status;
- full security;
- authority to execute an action.

## Code Phase Exit Criteria

Phase 409 may implement review-preview metadata only if it adds:

- a tiny-Z3 reviewed-formal-evidence preview input data model;
- a tiny-Z3 reviewed-formal-evidence preview record data model;
- deterministic digesting for preview inputs and records;
- validation from a Phase 407 candidate;
- canonical replay-readiness and promotion-rejection checklist helpers;
- fail-closed rejection for every Phase 408 rejection case;
- tests for accept-preview, reject-preview, replay-blocked, and
  checker-lane-blocked decisions;
- tests for nonclaim drift, candidate digest drift, policy drift, checklist
  drift, and promotion attempts;
- no reviewed formal evidence emission;
- no accepted Evidence Ledger mutation;
- no Level2+ evidence;
- no score-axis population.

## Next Slice

Phase 409 may implement the local tiny-Z3 reviewed-formal-evidence preview
metadata. It must not mutate accepted evidence, create Level2+ evidence,
populate score axes, claim semantic correctness, claim production readiness,
claim SOTA, claim breakthrough status, claim full security, or grant authority
to execute an action.
