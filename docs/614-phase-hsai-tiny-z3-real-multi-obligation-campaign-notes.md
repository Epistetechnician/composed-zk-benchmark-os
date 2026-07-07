# Phase 614 HSAI Tiny Z3 Real Multi-Obligation Campaign Notes

State slice: `phase-614-hsai-tiny-z3-real-multi-obligation-campaign`.

## What Changed

Phase 614 implements the Phase 613 boundary as in-memory Rust metadata under
`crates/hsai-agent-admission/src/lib.rs`.

Added surfaces:

- `GatewayFormalTinyZ3RealMultiObligationCampaignRequest`
- `GatewayFormalTinyZ3RealMultiObligationObservation`
- `GatewayFormalTinyZ3RealMultiObligationCampaignSummary`
- `GatewayFormalTinyZ3RealMultiObligationCampaignError`
- `gateway_formal_tiny_z3_real_multi_obligation_campaign_claim_boundary`
- `build_gateway_formal_tiny_z3_real_multi_obligation_campaign_summary`

The summary builder accepts existing Phase 529 hermetic local Z3 result
objects, validates that they remain local `LaneASmtZ3RunObservedLocalOnly`
metadata, requires unique obligation digests, counts `unsat` and `sat`
verdicts, and optionally requires a mixed-verdict campaign.

## Validation Behavior

The builder rejects:

- invalid campaign requests;
- empty result sets;
- expected-count mismatches;
- duplicate obligation digests;
- mixed-verdict-required campaigns with only one verdict class;
- source results that drift into accepted evidence, Level2 evidence,
  score-axis population, proof/checker/solver-certificate artifacts, Lean,
  COBALT, Rust-to-Lean, benchmark, external-audit, semantic-correctness,
  production-readiness, SOTA, full-security, or action-authority claims.

Focused tests cover mixed `unsat`/`sat` campaign summaries, optional local real
Z3 execution when a `z3` binary is available, invalid request rejection,
expected-count mismatch rejection, duplicate-obligation rejection,
promotion-drift rejection, and mixed-verdict requirement rejection.

## Claim Boundary

Phase 614 remains local `Level1LocalReplay`-class regression metadata. It does
not write campaign files, import external results, mutate the accepted Evidence
Ledger, create accepted formal evidence, create Level2+ evidence, populate
score axes, generate proof artifacts, generate checker transcripts, generate
solver certificates, run Lean, run COBALT, run Rust-to-Lean extraction, create
benchmark evidence, prove semantic correctness, establish production
readiness, establish SOTA, establish breakthrough status, establish full
security, establish external audit status, record human-review acceptance, or
grant authority to execute an action.
