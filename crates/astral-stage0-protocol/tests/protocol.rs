use astral_stage0_protocol::{
    development_split, normalized_regret, require_unreserved_seed, select_exploratory_method,
    selected_head, tagged_sha256, CandidateMethod, ClaimBoundary, CompetitiveBaseline,
    DevelopmentSplit, MethodAssessment, ProtocolError, RESERVED_FUTURE_FAMILIES,
};
use std::collections::BTreeMap;

#[test]
fn development_boundary_fails_closed() {
    assert_eq!(development_split(0), Ok(DevelopmentSplit::Train));
    assert_eq!(
        development_split(175),
        Ok(DevelopmentSplit::DevelopmentDesign)
    );
    assert_eq!(
        development_split(191),
        Ok(DevelopmentSplit::DevelopmentAssessment)
    );
    assert_eq!(
        development_split(192),
        Err(ProtocolError::FamilySealed(192))
    );
    for family in RESERVED_FUTURE_FAMILIES {
        assert!(matches!(
            development_split(family),
            Err(ProtocolError::FamilySealed(_))
        ));
    }
    assert_eq!(
        require_unreserved_seed(173),
        Err(ProtocolError::SeedSealed(173))
    );
}

#[test]
fn selection_uses_absolute_score_and_lowest_index_tie() {
    assert_eq!(selected_head([-2.0, 2.0, 1.0, 0.0]), Ok(0));
    assert_eq!(
        selected_head([f64::NAN, 0.0, 0.0, 0.0]),
        Err(ProtocolError::NonFinite)
    );
}

#[test]
fn regret_matches_dead_zone_and_bounds() {
    assert_eq!(
        normalized_regret([1e-5, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]),
        Ok((0.0, false))
    );
    assert_eq!(
        normalized_regret([1.0, 0.5, 0.0, 0.0], [0.0, 2.0, 0.0, 0.0]),
        Ok((0.5, true))
    );
}

#[test]
fn exploratory_winner_uses_minimum_cell_then_panel_order() {
    let l1 = eligible_assessment(CandidateMethod::AbsoluteProductL1, 0.20);
    let l2 = eligible_assessment(CandidateMethod::AbsoluteProductL2, 0.30);
    assert_eq!(
        select_exploratory_method(&[l1, l2]),
        Some(CandidateMethod::AbsoluteProductL2)
    );
}

#[test]
fn claim_boundary_cannot_accidentally_promote_research() {
    let boundary = ClaimBoundary::default();
    assert!(boundary.local_cross_language_parity_only);
    assert!(!boundary.accepted_evidence);
    assert!(!boundary.stage0_pass);
    assert!(!boundary.independent_replication);
    assert!(!boundary.self_modeling);
}

#[test]
fn tagged_hash_is_deterministic_and_field_bound() {
    let first = tagged_sha256("astral.test", &[b"ab", b"c"]);
    assert_eq!(first, tagged_sha256("astral.test", &[b"ab", b"c"]));
    assert_ne!(first, tagged_sha256("astral.test", &[b"a", b"bc"]));
    assert_ne!(first, tagged_sha256("astral.other", &[b"ab", b"c"]));
}

fn eligible_assessment(method: CandidateMethod, value: f64) -> MethodAssessment {
    let coverage_by_seed = [(1, 1.0), (2, 1.0), (3, 1.0)].into_iter().collect();
    let permutation_advantage_by_seed = [(1, 0.1), (2, 0.1), (3, 0.1)].into_iter().collect();
    let per_seed: BTreeMap<_, _> = [(1, value), (2, value), (3, value)].into_iter().collect();
    let advantage_by_baseline_and_seed = CompetitiveBaseline::PANEL
        .into_iter()
        .map(|baseline| (baseline, per_seed.clone()))
        .collect();
    MethodAssessment {
        method,
        coverage_by_seed,
        advantage_by_baseline_and_seed,
        permutation_advantage_by_seed,
    }
}
