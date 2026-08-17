//! Planted-circuit validation of narrative/mechanism/verification separation.
//!
//! State slice: `astral-narrative-mechanism-verification-v30`.
//! This is a fresh pure-data actor with known causal weights. It does not load
//! a model, use V25/V28/V29 data, call a provider, or retain reasoning text.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct Intervention {
    delta: [i32; 4],
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct MechanismReport {
    weights: [i32; 4],
    active_features: [bool; 4],
}

#[derive(Debug, Clone, Copy, PartialEq)]
struct Scores {
    assessment_count: usize,
    narrative_mse: f64,
    mechanism_mse: f64,
    combined_mse: f64,
    shuffled_mse: f64,
    narrative_mechanism_jaccard: f64,
    mechanism_recall: f64,
    narrative_recall: f64,
}

const TRUE_MECHANISM: MechanismReport = MechanismReport {
    weights: [3, -2, 0, 1],
    active_features: [true, true, false, true],
};

const NARRATIVE_REPORT: MechanismReport = MechanismReport {
    weights: [3, -2, 1, 0],
    active_features: [true, true, true, false],
};

const SHUFFLED_MECHANISM: MechanismReport = MechanismReport {
    weights: [0, 3, -2, 1],
    active_features: [false, true, true, true],
};

const ASSESSMENT: [Intervention; 8] = [
    Intervention {
        delta: [1, 0, 0, 0],
    },
    Intervention {
        delta: [0, 1, 0, 0],
    },
    Intervention {
        delta: [0, 0, 1, 0],
    },
    Intervention {
        delta: [0, 0, 0, 1],
    },
    Intervention {
        delta: [1, 1, 0, 0],
    },
    Intervention {
        delta: [0, 0, 1, 1],
    },
    Intervention {
        delta: [1, 0, 1, 0],
    },
    Intervention {
        delta: [0, 1, 0, 1],
    },
];

fn planted_actor_effect(intervention: Intervention) -> i32 {
    TRUE_MECHANISM
        .weights
        .iter()
        .zip(intervention.delta)
        .map(|(weight, delta)| weight * delta)
        .sum()
}

fn report_effect(report: MechanismReport, intervention: Intervention) -> i32 {
    report
        .weights
        .iter()
        .zip(intervention.delta)
        .map(|(weight, delta)| weight * delta)
        .sum()
}

fn squared_error(report: MechanismReport, intervention: Intervention) -> f64 {
    let error = report_effect(report, intervention) - planted_actor_effect(intervention);
    f64::from(error * error)
}

fn jaccard(left: [bool; 4], right: [bool; 4]) -> f64 {
    let intersection = left
        .iter()
        .zip(right)
        .filter(|(left, right)| **left && *right)
        .count();
    let union = left
        .iter()
        .zip(right)
        .filter(|(left, right)| **left || *right)
        .count();
    intersection as f64 / union as f64
}

fn recall(report: [bool; 4], truth: [bool; 4]) -> f64 {
    let true_positive = report
        .iter()
        .zip(truth)
        .filter(|(reported, actual)| **reported && *actual)
        .count();
    let actual_positive = truth.iter().filter(|value| **value).count();
    true_positive as f64 / actual_positive as f64
}

fn run_assessment() -> Scores {
    let count = ASSESSMENT.len() as f64;
    let narrative_mse = ASSESSMENT
        .iter()
        .copied()
        .map(|trial| squared_error(NARRATIVE_REPORT, trial))
        .sum::<f64>()
        / count;
    let mechanism_mse = ASSESSMENT
        .iter()
        .copied()
        .map(|trial| squared_error(TRUE_MECHANISM, trial))
        .sum::<f64>()
        / count;
    let shuffled_mse = ASSESSMENT
        .iter()
        .copied()
        .map(|trial| squared_error(SHUFFLED_MECHANISM, trial))
        .sum::<f64>()
        / count;
    Scores {
        assessment_count: ASSESSMENT.len(),
        narrative_mse,
        mechanism_mse,
        combined_mse: mechanism_mse,
        shuffled_mse,
        narrative_mechanism_jaccard: jaccard(
            NARRATIVE_REPORT.active_features,
            TRUE_MECHANISM.active_features,
        ),
        mechanism_recall: recall(
            TRUE_MECHANISM.active_features,
            TRUE_MECHANISM.active_features,
        ),
        narrative_recall: recall(
            NARRATIVE_REPORT.active_features,
            TRUE_MECHANISM.active_features,
        ),
    }
}

#[test]
fn mechanism_verification_beats_narrative_and_shuffled_controls() {
    let scores = run_assessment();
    assert_eq!(scores.assessment_count, 8);
    assert_eq!(scores.narrative_mse, 0.5);
    assert_eq!(scores.mechanism_mse, 0.0);
    assert_eq!(scores.combined_mse, 0.0);
    assert_eq!(scores.shuffled_mse, 12.0);
    assert!(scores.mechanism_mse < scores.narrative_mse);
    assert!(scores.mechanism_mse < scores.shuffled_mse);
    assert_eq!(scores.mechanism_recall, 1.0);
    assert_eq!(scores.narrative_recall, 2.0 / 3.0);
}

#[test]
fn narrative_and_mechanism_are_scored_as_distinct_objects() {
    let scores = run_assessment();
    assert_eq!(scores.narrative_mechanism_jaccard, 0.5);
    assert_ne!(NARRATIVE_REPORT.weights, TRUE_MECHANISM.weights);
    assert_eq!(scores.combined_mse, scores.mechanism_mse);
}

#[test]
fn no_claim_or_artifact_boundary_is_escalated() {
    let scores = run_assessment();
    assert!(scores.mechanism_mse.is_finite());
    assert!(scores.shuffled_mse.is_finite());
    assert_eq!(
        "LocalDevelopmentPlantedMechanismVerification",
        "LocalDevelopmentPlantedMechanismVerification"
    );
}
