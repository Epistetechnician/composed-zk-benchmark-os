# Phase J Reviewed Proposal Acceptance Policy Notes

Phase J adds reviewed proposal acceptance policy on top of the Phase I synthetic import and evidence append proposal workflow.

## Implemented

- `EvidenceAcceptancePolicy` with conservative and Level1-local-only modes.
- `ClaimBoundaryEscalationGuard` blocking accidental Level2+ promotion.
- `EvidenceReviewDecision`, checklist, and manual review helpers.
- `EvidenceRecordCandidate` creation from reviewed proposals only.
- Deterministic JSON serialization for policy, review decisions, and candidates.
- Integration tests in `tests/phase_j_claim_boundaries.rs`.

## Deliberately Not Implemented

- No live external execution.
- No accepted external evidence.
- No automatic `EvidenceLedger` append.
- No Level2+ actual evidence promotion.
- No fake performance metrics in score reports.

## Claim Boundaries

Evidence append proposals, review decisions, and evidence-record candidates remain pending metadata only.

Conservative candidate creation caps at `Level0DesignNote`.

Strict local-only policy may create `Level1LocalReplay` candidates only when the escalation guard explicitly allows Level0 to Level1 local-only transitions.

Evidence-record candidates are not accepted evidence. Future manual append is required before any ledger mutation.

## Workflow

1. Phase I creates a pending-review `EvidenceAppendProposal`.
2. Phase J manual review produces an `EvidenceReviewDecision`.
3. `EvidenceAcceptancePolicy` validates proposal + decision + target claim boundary.
4. `create_evidence_record_candidate()` emits candidate metadata only.
5. `EvidenceLedger` remains unchanged.

## Validation Summary

Phase J tests cover:

- reviewed proposal to candidate workflow,
- escalation guard blocking Level2 targets,
- automated reviewer rejection,
- acceptance policy JSON round-trip,
- source scans for process execution APIs in `src/evidence/`.

These checks do not establish real external result import, official benchmark evidence, performance evidence, or formal evidence.

## Next Recommended Slice

Phase K gnark recursion adapter preparation (inert manifest and envelope plan only).
