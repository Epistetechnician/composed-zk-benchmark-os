# Phase 523 HSAI Tiny Z3 External Result Import Candidate Metadata Notes

State slice: `Phase 523 HSAI tiny Z3 external result import candidate metadata`.

Phase 523 implements the local metadata lane authorized by Phase 522. It builds
one in-memory `zkbench_core::ExternalResultCandidate` from one exact Phase 521
external-reproduction provenance record, calls
`validate_external_result_candidate`, calls `external_result_quarantine_record`,
and records the candidate, validation, validation-issue, and quarantine-record
digests in HSAI admission metadata.

The valid classification is:

```text
ImportCandidateQuarantinedLocalMetadata
```

The candidate is constrained to:

- owner `zkbench-core`;
- type `ExternalResultCandidate`;
- validator `validate_external_result_candidate`;
- quarantine function `external_result_quarantine_record`;
- status `ExternalResultStatus::Quarantined`;
- requested boundary `ClaimBoundary::Level0DesignNote`;
- no official benchmark claim;
- no formal-evidence claim;
- no proof-system soundness claim.

The Phase 523 record binds the Phase 521 external-reproduction digest and input
digest, Phase 521 blocker and nonpromotion digests, Phase 519 Level2
eligibility digest, Phase 517 score-axis eligibility digest, Phase 515 package
digest, and Phase 513 materialized accepted-ledger artifact digest.

Validation is fail-closed when:

- the Phase 521 record is not exact;
- the Phase 521 classification is not
  `ExternalReproductionBlockedNoIndependentRun`;
- the candidate digest drifts;
- the validator digest drifts;
- the validation issue digest drifts;
- the quarantine record digest drifts;
- `zkbench-core` reports the candidate invalid;
- the quarantine status is not `Quarantined`;
- any promotion or strong claim flag is set.

Implemented tests cover a successful quarantined metadata record, rejection of
invalid Phase 521 state, and rejection of digest drift plus promotion flags.

This phase does not write external-result artifacts, write external-reproduction
artifacts, write Level2 artifacts, populate score axes, create accepted formal
evidence, create Level2+ evidence, generate proof artifacts, generate checker
transcripts, generate solver certificates, run Lean, run new SMT, run COBALT,
run Rust-to-Lean extraction, create benchmark evidence, create external-audit
evidence, prove semantic correctness, establish production readiness, establish
SOTA, establish breakthrough status, establish full security, or grant
authority to execute an action.
