//! Promotion-guard regression test for Astral behavior/mechanism/introspection
//! scoring layers.
//!
//! State slice: `astral-scoring-layer-contract-v32`.
//! This test is pure metadata. It does not load a model, call a provider, use
//! the network, or create accepted evidence.

use zkbench_core::ClaimBoundary;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ScoreLayer {
    Behavior,
    Mechanism,
    Introspection,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct EvidenceProfile {
    behavior_observed: bool,
    heldout_endpoint: bool,
    locked_controls: bool,
    direct_intervention_effects: bool,
    measured_mechanism: bool,
    narrative_or_shuffle_controls: bool,
    actor_self_report: bool,
    prediction_locked: bool,
    external_mechanism_comparison: bool,
}

impl EvidenceProfile {
    const fn empty() -> Self {
        Self {
            behavior_observed: false,
            heldout_endpoint: false,
            locked_controls: false,
            direct_intervention_effects: false,
            measured_mechanism: false,
            narrative_or_shuffle_controls: false,
            actor_self_report: false,
            prediction_locked: false,
            external_mechanism_comparison: false,
        }
    }

    const fn behavior_only() -> Self {
        Self {
            behavior_observed: true,
            heldout_endpoint: true,
            locked_controls: true,
            ..Self::empty()
        }
    }

    const fn mechanism() -> Self {
        Self {
            direct_intervention_effects: true,
            measured_mechanism: true,
            narrative_or_shuffle_controls: true,
            ..Self::behavior_only()
        }
    }

    const fn introspection() -> Self {
        Self {
            actor_self_report: true,
            prediction_locked: true,
            external_mechanism_comparison: true,
            ..Self::mechanism()
        }
    }
}

fn highest_supported_layer(profile: EvidenceProfile) -> Option<ScoreLayer> {
    let behavior = profile.behavior_observed && profile.heldout_endpoint && profile.locked_controls;
    let mechanism = behavior
        && profile.direct_intervention_effects
        && profile.measured_mechanism
        && profile.narrative_or_shuffle_controls;
    let introspection = mechanism
        && profile.actor_self_report
        && profile.prediction_locked
        && profile.external_mechanism_comparison;

    if introspection {
        Some(ScoreLayer::Introspection)
    } else if mechanism {
        Some(ScoreLayer::Mechanism)
    } else if behavior {
        Some(ScoreLayer::Behavior)
    } else {
        None
    }
}

fn claim_boundary_for_layer(layer: Option<ScoreLayer>) -> ClaimBoundary {
    match layer {
        None => ClaimBoundary::Level0DesignNote,
        Some(ScoreLayer::Behavior | ScoreLayer::Mechanism | ScoreLayer::Introspection) => {
            ClaimBoundary::Level1LocalReplay
        }
    }
}

#[test]
fn frozen_profiles_have_exact_layer_classification() {
    let profiles = [
        (EvidenceProfile::empty(), None),
        (EvidenceProfile::behavior_only(), Some(ScoreLayer::Behavior)),
        (EvidenceProfile::mechanism(), Some(ScoreLayer::Mechanism)),
        (
            EvidenceProfile {
                actor_self_report: true,
                prediction_locked: true,
                external_mechanism_comparison: true,
                ..EvidenceProfile::mechanism()
            },
            Some(ScoreLayer::Introspection),
        ),
        (
            EvidenceProfile {
                actor_self_report: true,
                prediction_locked: true,
                ..EvidenceProfile::mechanism()
            },
            Some(ScoreLayer::Mechanism),
        ),
        (
            EvidenceProfile {
                direct_intervention_effects: true,
                measured_mechanism: true,
                ..EvidenceProfile::behavior_only()
            },
            Some(ScoreLayer::Behavior),
        ),
    ];

    let unsupported_promotions = profiles
        .iter()
        .filter(|(profile, expected)| highest_supported_layer(*profile) != *expected)
        .count();
    assert_eq!(unsupported_promotions, 0);
}

#[test]
fn v30_and_v31_evidence_stops_at_mechanism() {
    let v30_v31_profile = EvidenceProfile::mechanism();
    assert_eq!(
        highest_supported_layer(v30_v31_profile),
        Some(ScoreLayer::Mechanism)
    );
    assert_ne!(
        highest_supported_layer(v30_v31_profile),
        Some(ScoreLayer::Introspection)
    );
}

#[test]
fn removing_one_introspection_prerequisite_cannot_promote() {
    let qualified = EvidenceProfile::introspection();

    let without_self_report = EvidenceProfile {
        actor_self_report: false,
        ..qualified
    };
    let without_prediction_lock = EvidenceProfile {
        prediction_locked: false,
        ..qualified
    };
    let without_external_comparison = EvidenceProfile {
        external_mechanism_comparison: false,
        ..qualified
    };
    let without_intervention_effects = EvidenceProfile {
        direct_intervention_effects: false,
        ..qualified
    };

    assert_eq!(
        highest_supported_layer(without_self_report),
        Some(ScoreLayer::Mechanism)
    );
    assert_eq!(
        highest_supported_layer(without_prediction_lock),
        Some(ScoreLayer::Mechanism)
    );
    assert_eq!(
        highest_supported_layer(without_external_comparison),
        Some(ScoreLayer::Mechanism)
    );
    assert_eq!(
        highest_supported_layer(without_intervention_effects),
        Some(ScoreLayer::Behavior)
    );

    for layer in [
        None,
        Some(ScoreLayer::Behavior),
        Some(ScoreLayer::Mechanism),
        Some(ScoreLayer::Introspection),
    ] {
        assert!(claim_boundary_for_layer(layer) <= ClaimBoundary::Level1LocalReplay);
    }
}
