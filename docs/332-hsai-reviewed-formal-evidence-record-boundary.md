# Phase 332 HSAI Reviewed Formal Evidence Record Boundary

State slice: `Phase 332 HSAI reviewed-formal-evidence record boundary`.

## Boundary

Phase 332 defines the docs-first boundary for a future reviewed-formal-evidence
record over a Phase 331 review preview. It does not implement reviewed evidence
code, accepted evidence code, Level2+ evidence, score-axis population, proof
artifact generation, checker transcript generation, solver certificate
generation, Lean execution, COBALT execution, Rust-to-Lean extraction,
benchmark submission, or production deployment.

This phase keeps the evidence ladder explicit:

```text
quarantined_output
-> formal_evidence_candidate
-> reviewed_formal_evidence_preview
-> reviewed_formal_evidence
-> accepted_formal_evidence
```

The reviewed record is still local reviewed evidence. It is not accepted
evidence and must not mutate the accepted Evidence Ledger.

## Reviewed Record Inputs

A future reviewed-formal-evidence record must bind:

- Phase 331 review-preview digest.
- Phase 331 preview-input digest.
- Phase 329 candidate digest.
- Phase 329 candidate-input digest.
- Phase 327 output-bundle manifest digest.
- Phase 325 preflight digest.
- Phase 323 source-manifest digest.
- Reviewer policy id.
- Verifier policy id.
- Reviewer decision id.
- Reviewer decision timestamp.
- Reviewer decision label.
- Reviewed-scope statement digest.
- Nonclaim acknowledgement digest.
- Promotion-rejection checklist digest.
- Accepted-evidence-disabled acknowledgement digest.

The reviewed record must fail closed if any digest is missing, zero, stale, or
inconsistent with the preview.

## Required Preview State

A future reviewed record may be emitted only for this Phase 331 preview
decision:

```text
ReviewPreviewAcceptCandidateScope
```

The following preview decisions must not produce a reviewed record:

- `ReviewPreviewRejectCandidateScope`;
- `ReviewPreviewNeedsReplay`;
- `ReviewPreviewNeedsCheckerLane`.

Those decisions may support diagnostics or follow-up work, but not reviewed
formal evidence.

## Required Rejection Cases

A future reviewed-record implementation must reject if:

- the Phase 331 preview digest does not match the preview input;
- the Phase 331 preview is not in `reviewed_formal_evidence_preview` state;
- the Phase 331 preview decision is not `ReviewPreviewAcceptCandidateScope`;
- the preview has any proof, checker-transcript, solver-certificate,
  reviewed-evidence, accepted-evidence, Level2+, score-axis,
  production-readiness, SOTA, breakthrough, full-security,
  semantic-correctness, or authority flag set;
- the candidate digest, candidate-input digest, Phase 327 digest, preflight
  digest, or Phase 323 digest does not match the preview;
- the reviewer policy id or verifier policy id does not match the preview;
- the reviewed-scope statement is empty or claims more than the Phase 329
  candidate and Phase 331 preview authorize;
- the nonclaim acknowledgement does not exactly match the preview nonclaims;
- the promotion-rejection checklist does not explicitly reject accepted
  evidence, Level2+ evidence, score axes, SOTA, full-security,
  semantic-correctness, production-readiness, and action authority;
- the accepted-evidence-disabled acknowledgement is missing;
- the record tries to mutate accepted evidence;
- the record tries to create Level2+ evidence;
- the record tries to populate score axes;
- the record claims benchmark or SOTA comparison.

## Evidence Meaning

The maximum future claim from a reviewed-formal-evidence record is:

```text
This local reviewed formal-evidence record states that one Phase 329 candidate
passed a Phase 331 scoped review preview under an explicit review policy,
explicit nonclaims, and accepted-evidence-disabled acknowledgement.
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

Phase 332 improves evidence quality by defining the first reviewed state as a
typed, digest-bound record rather than a prose acceptance. The direction toward
SOTA-quality is:

1. Candidate evidence binds source and execution digests.
2. Review preview classifies candidate review state.
3. Reviewed record binds the accepted preview and nonclaims.
4. Accepted evidence remains a separate future state through the repository
   accepted-evidence append path.
5. SOTA claims remain blocked until benchmark methodology and external
   comparison evidence exist.

The defensible claim after a future Phase 333 implementation would be:

```text
HSAI has a local reviewed formal-evidence record for one scoped gateway
admission invariant, with digest-bound candidate and preview provenance,
explicit nonclaims, and accepted-evidence-disabled acknowledgement.
```

That is reviewed local evidence. It is not accepted evidence and not SOTA.

## Future Code Phase Exit Criteria

A future Phase 333 implementation may create reviewed-record metadata only if
it adds:

- a reviewed formal-evidence record input data model;
- a reviewed formal-evidence record data model;
- deterministic digesting for reviewed-record inputs and records;
- validation from a Phase 331 preview;
- fail-closed rejection for every Phase 332 rejection case;
- tests for reviewed-record construction from
  `ReviewPreviewAcceptCandidateScope`;
- tests rejecting the reject, needs-replay, and needs-checker-lane preview
  decisions;
- tests for nonclaim drift, preview digest drift, policy drift, accepted
  evidence attempts, Level2+ attempts, score-axis attempts, and SOTA attempts;
- no accepted Evidence Ledger mutation;
- no Level2+ evidence;
- no score-axis population.

No broader property than
`attestation_challenge_binding_deterministic_input_sensitive` is authorized by
this boundary.
