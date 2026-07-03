# Phase 330 HSAI Reviewed Formal Evidence Preview Boundary

State slice: `Phase 330 HSAI reviewed-formal-evidence preview boundary for Phase 329 candidates`.

## Boundary

Phase 330 defines the docs-first boundary for a future reviewed-formal-evidence
preview over a Phase 329 local formal-evidence candidate. It does not implement
reviewed evidence code, accepted evidence code, Level2+ evidence, score-axis
population, proof artifact generation, checker transcript generation, solver
certificate generation, Lean execution, COBALT execution, Rust-to-Lean
extraction, benchmark submission, or production deployment.

This phase keeps the promotion ladder explicit:

```text
quarantined_output
-> formal_evidence_candidate
-> reviewed_formal_evidence_preview
-> reviewed_formal_evidence
-> accepted_formal_evidence
```

The preview state is intentionally separate from reviewed evidence. It lets the
repo define review inputs and rejection rules before any future code can emit a
reviewed formal-evidence record.

## Review Inputs

A future reviewed-formal-evidence preview must bind:

- Phase 329 candidate digest.
- Phase 329 candidate input digest.
- Phase 327 output-bundle manifest digest.
- Phase 325 preflight digest.
- Phase 323 source-manifest digest.
- Reviewer policy id.
- Verifier policy id.
- Reviewer decision id.
- Reviewer decision timestamp.
- Reviewer decision label.
- Reviewer nonclaim acknowledgement digest.
- Source correspondence statement digest.
- Replay-readiness checklist digest.
- Promotion-rejection checklist digest.

The review preview must fail closed if any digest is missing, zero, stale, or
inconsistent with the candidate.

## Decision Labels

A future preview may use only these decision labels:

| Label | Meaning |
| --- | --- |
| `review_preview_accept_candidate_scope` | The candidate is locally coherent under its declared scope and may proceed to a future reviewed-evidence implementation phase. |
| `review_preview_reject_candidate_scope` | The candidate is not locally coherent under its declared scope. |
| `review_preview_needs_replay` | The candidate cannot be reviewed without an additional declared replay artifact or replay transcript. |
| `review_preview_needs_checker_lane` | The candidate cannot support a stronger claim without an implemented checker lane. |

No decision label may append accepted evidence or imply Level2+ evidence.

## Required Rejection Cases

A future preview must reject or require replay if:

- the Phase 329 candidate digest does not match the candidate input;
- the Phase 329 candidate has any proof, checker-transcript,
  solver-certificate, reviewed-evidence, accepted-evidence, Level2+,
  score-axis, production-readiness, SOTA, breakthrough, full-security,
  semantic-correctness, or authority flag set;
- the candidate has no source correspondence statement;
- the reviewer policy id is missing or does not match the candidate;
- the verifier policy id is missing or does not match the candidate;
- the reviewer decision id is not a single-segment id;
- the reviewer nonclaim acknowledgement does not exactly match the candidate
  nonclaims;
- the replay-readiness checklist does not bind the Phase 323, 325, 327, and
  329 digests;
- the promotion-rejection checklist does not explicitly reject accepted
  evidence, Level2+ evidence, score axes, SOTA, full-security,
  semantic-correctness, production-readiness, and authority claims;
- the preview tries to create accepted evidence;
- the preview tries to create reviewed formal evidence directly;
- the preview tries to populate score axes;
- the preview claims benchmark or SOTA comparison.

## Evidence Meaning

The maximum future claim from a reviewed-formal-evidence preview is:

```text
This local review preview records that one Phase 329 formal-evidence candidate
is ready, rejected, replay-blocked, or checker-lane-blocked under an explicit
review policy and explicit nonclaims.
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

## SOTA-Quality Direction

Phase 330 improves evidence quality by forcing review to be a typed state
transition rather than a prose assertion. The direction toward SOTA-quality is:

1. Candidate evidence is built from declared digests.
2. Review preview checks candidate coherence and nonclaim preservation.
3. Reviewed evidence remains a separate future state.
4. Accepted evidence remains a separate future state through the repository
   accepted-evidence path.
5. SOTA claims remain blocked until separate benchmark methodology and external
   comparison evidence exist.

The defensible claim after a future Phase 331 implementation would be:

```text
HSAI has a local reviewed-formal-evidence preview lane that can classify one
formal-evidence candidate as scoped-acceptable, rejected, replay-blocked, or
checker-lane-blocked without creating accepted evidence.
```

That is review discipline, not accepted evidence and not SOTA.

## Future Code Phase Exit Criteria

A future Phase 331 implementation may create review preview metadata only if it
adds:

- a reviewed-formal-evidence preview input data model;
- a reviewed-formal-evidence preview record data model;
- deterministic digesting for preview inputs and records;
- validation from a Phase 329 candidate;
- fail-closed rejection for every Phase 330 rejection case;
- tests for accept-preview, reject-preview, replay-blocked, and
  checker-lane-blocked decisions;
- tests for nonclaim drift, candidate digest drift, policy drift, and promotion
  attempts;
- no reviewed formal evidence emission;
- no accepted Evidence Ledger mutation;
- no Level2+ evidence;
- no score-axis population.

No broader property than
`attestation_challenge_binding_deterministic_input_sensitive` is authorized by
this boundary.
