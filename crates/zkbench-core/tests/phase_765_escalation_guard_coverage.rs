//! Phase 765 claim-boundary escalation-guard coverage.
//!
//! Focused local regression coverage for reachable public API paths in
//! `crates/zkbench-core/src/evidence/escalation_guard.rs`: formal Level4+
//! blocking, claim-boundary downgrade rejection, and the Level1-local helper
//! constructor. Local regression evidence only; not Level2+, not formal proof,
//! and not 100% coverage.

use zkbench_core::{guard_claim_boundary_escalation, ClaimBoundary, ClaimBoundaryEscalationGuard};

#[test]
fn default_guard_blocks_formal_level4_escalation_with_both_blockers() {
    let guard = ClaimBoundaryEscalationGuard::default();
    let result = guard.check_escalation(
        ClaimBoundary::Level1LocalReplay,
        ClaimBoundary::Level4FormalPropertyStatement,
    );

    assert!(!result.allowed);
    assert!(result
        .blocking_reasons
        .iter()
        .any(|reason| reason.contains("Level2+")));
    assert!(result
        .blocking_reasons
        .iter()
        .any(|reason| reason.contains("formal evidence levels")));
}

#[test]
fn default_guard_blocks_claim_boundary_downgrade() {
    let guard = ClaimBoundaryEscalationGuard::default();
    let result = guard.check_escalation(
        ClaimBoundary::Level1LocalReplay,
        ClaimBoundary::Level0DesignNote,
    );

    assert!(!result.allowed);
    assert!(result
        .blocking_reasons
        .iter()
        .any(|reason| reason.contains("downgrade")));
}

#[test]
fn allowing_level1_local_candidates_permits_level0_to_level1() {
    let guard = ClaimBoundaryEscalationGuard::allowing_level1_local_candidates();
    let result = guard.check_escalation(
        ClaimBoundary::Level0DesignNote,
        ClaimBoundary::Level1LocalReplay,
    );

    assert!(result.allowed);
    assert!(result.blocking_reasons.is_empty());
}

#[test]
fn public_helper_rejects_formal_escalation_even_when_level1_local_is_allowed() {
    let error = guard_claim_boundary_escalation(
        ClaimBoundary::Level0DesignNote,
        ClaimBoundary::Level5MachineCheckedScopedProof,
        true,
    )
    .expect_err("formal escalation should remain blocked");

    assert!(error
        .to_string()
        .contains("claim boundary escalation blocked"));
    assert!(error.to_string().contains("formal evidence levels"));
}

#[test]
fn public_helper_rejects_downgrade_through_error_path() {
    let error = guard_claim_boundary_escalation(
        ClaimBoundary::Level1LocalReplay,
        ClaimBoundary::Level0DesignNote,
        true,
    )
    .expect_err("downgrade should be blocked");

    assert!(error.to_string().contains("downgrade"));
}
