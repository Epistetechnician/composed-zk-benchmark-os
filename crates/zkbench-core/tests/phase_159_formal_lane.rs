//! Phase 159 — formal lane interface stub integration tests.

use std::fs;
use std::path::Path;

use zkbench_core::evidence::ClaimBoundary;
use zkbench_core::{
    mandatory_lane_outcome_nonclaims, FormalLane, FormalLaneError, FormalLaneProofStatus,
    FormalPropertyAssertion, FormalPropertyScope, FormalVerifier, NoopFormalVerifier,
};

fn sample_assertion(scope: FormalPropertyScope) -> FormalPropertyAssertion {
    FormalPropertyAssertion {
        id: "prop_0".to_string(),
        scope,
        statement: "scoped property holds".to_string(),
        bound_machine_id: "m0".to_string(),
        nonclaims: FormalPropertyAssertion::mandatory_nonclaims(),
    }
}

#[test]
fn noop_verifier_returns_declared_only_for_every_scope() {
    let scopes = [
        FormalPropertyScope::TransitionGuard {
            transition_id: "t0".to_string(),
        },
        FormalPropertyScope::Invariant {
            invariant_id: "inv0".to_string(),
        },
        FormalPropertyScope::LoopBound {
            loop_id: "loop0".to_string(),
        },
        FormalPropertyScope::Machine,
    ];
    let verifier = NoopFormalVerifier;
    for scope in &scopes {
        let assertion = sample_assertion(scope.clone());
        let proof = verifier
            .verify(&assertion)
            .unwrap_or_else(|e| panic!("noop verifier should succeed: {e:?}"));
        assert_eq!(proof.status, FormalLaneProofStatus::DeclaredOnly);
        assert_eq!(proof.claim_boundary, ClaimBoundary::Level0DesignNote);
    }
}

#[test]
fn formal_lane_evaluate_carries_mandatory_nonclaims() {
    let lane = FormalLane::new(NoopFormalVerifier);
    let assertion = sample_assertion(FormalPropertyScope::Machine);
    let outcome = lane.evaluate(&assertion).expect("evaluate should succeed");
    let expected = mandatory_lane_outcome_nonclaims();
    assert_eq!(outcome.nonclaims, expected);
    assert_eq!(outcome.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert!(outcome
        .nonclaims
        .iter()
        .any(|n| n.contains("declared-only")));
    assert!(outcome
        .nonclaims
        .iter()
        .any(|n| n.contains("no formal tool was run")));
}

#[test]
fn noop_verifier_rejects_malformed_assertion_via_lane() {
    let lane = FormalLane::new(NoopFormalVerifier);
    let mut assertion = sample_assertion(FormalPropertyScope::Machine);
    assertion.statement = "  ".to_string();
    let err = lane
        .evaluate(&assertion)
        .expect_err("empty statement should be rejected");
    let msg = err.to_string();
    assert!(msg.contains("malformed assertion"));
}

#[test]
fn declared_only_never_escalates_above_level0() {
    // Even though FormalLaneProofStatus has MachineCheckedScoped and
    // IndependentlyReproduced variants, the shipped NoopFormalVerifier must
    // never produce them. Those variants are reserved for a future
    // implementation phase that integrates with a real formal tool.
    let verifier = NoopFormalVerifier;
    let assertion = sample_assertion(FormalPropertyScope::Machine);
    let proof = verifier.verify(&assertion).expect("should succeed");
    assert_ne!(proof.status, FormalLaneProofStatus::MachineCheckedScoped);
    assert_ne!(proof.status, FormalLaneProofStatus::IndependentlyReproduced);
    assert_ne!(proof.status, FormalLaneProofStatus::ProofAttempted);
}

#[test]
fn formal_module_source_contains_no_forbidden_integrations() {
    // The Phase 159 boundary forbids integration with any real formal tool.
    // Source-scan the shipped formal module to prove the seam is inert. We
    // check for actual integration patterns (imports, command invocations,
    // network/filesystem calls) rather than doc mentions of tool names.
    let module_path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("src")
        .join("formal")
        .join("mod.rs");
    let source = fs::read_to_string(&module_path)
        .unwrap_or_else(|e| panic!("failed to read formal module source: {e}"));
    let lowered = source.to_ascii_lowercase();
    // Forbidden integration patterns. Each is a real-code signal, not a doc
    // mention. Tool names that collide with common words (clean, lean) are
    // matched only as import/instantiation prefixes.
    let forbidden = [
        "use coq",
        "extern crate coq",
        "use lean",
        "extern crate lean",
        "use rocq",
        "extern crate rocq",
        "use dafny",
        "extern crate dafny",
        "use fstar",
        "extern crate fstar",
        "use garden",
        "extern crate garden",
        "use zklean",
        "extern crate zklean",
        "command::new",
        "process::command",
        "std::process",
        "reqwest::",
        "std::net::",
        "std::fs::write",
        "std::fs::read",
        "fs::write",
        "tcplistener",
        "tcpstream",
    ];
    for needle in &forbidden {
        assert!(
            !lowered.contains(needle),
            "formal module source must not reference forbidden integration '{needle}'"
        );
    }
    // The seam must explicitly reference the noop behavior.
    assert!(lowered.contains("noopformalverifier"));
    assert!(lowered.contains("declaredonly"));
}

#[test]
fn formal_lane_error_is_exposed() {
    // Ensure the error type is publicly re-exported and constructible.
    let err = FormalLaneError::MalformedAssertion {
        path: "id".to_string(),
        reason: "test".to_string(),
    };
    assert!(matches!(err, FormalLaneError::MalformedAssertion { .. }));
}
