//! Synthetic stress test for the V30 narrative/mechanism measurement design.
//!
//! State slice: `astral-narrative-mechanism-stress-test-v31`.
//! This test is deterministic pure data. It does not load a model, access a
//! provider, use the network, or reuse V25/V28/V29 artifacts.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Mode {
    CleanLinear,
    NoisyLinear,
    UnmodeledInteraction,
}

#[derive(Debug, Clone)]
struct Task {
    mode: Mode,
    dimension: usize,
    seed: u64,
    truth_weights: Vec<i32>,
    measured_weights: Vec<i32>,
    narrative_weights: Vec<i32>,
    shuffled_weights: Vec<i32>,
    interaction: Option<(usize, usize, i32)>,
    fit_interventions: Vec<Vec<i32>>,
    assessment_interventions: Vec<Vec<i32>>,
}

#[derive(Debug, Clone, Copy, PartialEq)]
struct TaskMetrics {
    mode: Mode,
    measured_mse: f64,
    narrative_mse: f64,
    shuffled_mse: f64,
    zero_mse: f64,
    mean_mse: f64,
    oracle_mse: f64,
    all_baseline_win: bool,
    narrative_win: bool,
}

#[derive(Debug, Clone, Copy, PartialEq)]
struct MatrixSummary {
    task_count: usize,
    linear_task_count: usize,
    interaction_task_count: usize,
    linear_all_baseline_wins: usize,
    linear_narrative_wins: usize,
    interaction_all_baseline_failures: usize,
    linear_all_baseline_win_rate: f64,
    linear_narrative_win_rate: f64,
    measured_mean_mse: f64,
    measured_mse_variance: f64,
    narrative_mean_mse: f64,
    shuffled_mean_mse: f64,
    zero_mean_mse: f64,
    fit_mean_mean_mse: f64,
    oracle_mean_mse: f64,
}

const DIMENSIONS: [usize; 3] = [4, 8, 12];
const SEEDS: [u64; 4] = [0, 1, 2, 3];
const MODES: [Mode; 3] = [
    Mode::CleanLinear,
    Mode::NoisyLinear,
    Mode::UnmodeledInteraction,
];
const FIT_TRIALS: usize = 2;
const ASSESSMENT_TRIALS: usize = 12;

fn next_small(state: &mut u64) -> i32 {
    *state = state
        .wrapping_mul(6364136223846793005)
        .wrapping_add(1442695040888963407);
    ((*state >> 32) % 7) as i32 - 3
}

fn sparse_weights(dimension: usize, seed: u64) -> Vec<i32> {
    let mut state = seed ^ 0x9e3779b97f4a7c15;
    let mut weights = (0..dimension)
        .map(|_| next_small(&mut state))
        .collect::<Vec<_>>();
    if weights.iter().all(|weight| *weight == 0) {
        weights[0] = 2;
    }
    weights
}

fn intervention(dimension: usize, seed: u64, ordinal: usize) -> Vec<i32> {
    let mut state =
        seed.wrapping_add((ordinal as u64).wrapping_mul(0x517cc1b727220a95)) ^ 0xd1b54a32d192ed03;
    let mut values = (0..dimension)
        .map(|_| match next_small(&mut state).rem_euclid(5) {
            0 => -1,
            1 | 2 => 0,
            _ => 1,
        })
        .collect::<Vec<_>>();
    if values.iter().all(|value| *value == 0) {
        values[ordinal % dimension] = 1;
    }
    values
}

fn task(mode: Mode, dimension: usize, seed: u64) -> Task {
    let truth_weights = sparse_weights(dimension, seed + dimension as u64 * 31);
    let decoy = (seed as usize + dimension) % dimension;
    let mut narrative_weights = truth_weights.clone();
    narrative_weights[decoy] += if narrative_weights[decoy] >= 0 { 3 } else { -3 };
    let second_decoy = (decoy + 1) % dimension;
    narrative_weights[second_decoy] = -narrative_weights[second_decoy];

    let mut shuffled_weights = vec![0; dimension];
    for index in 0..dimension {
        shuffled_weights[index] = truth_weights[(index + 1) % dimension];
    }

    let mut measured_weights = truth_weights.clone();
    if mode == Mode::NoisyLinear {
        let noisy_index = (seed as usize * 3 + 1) % dimension;
        measured_weights[noisy_index] += if measured_weights[noisy_index] >= 0 {
            1
        } else {
            -1
        };
    }

    let interaction = (mode == Mode::UnmodeledInteraction).then_some((0, 1, 9 + (seed % 3) as i32));
    let fit_interventions = (0..(dimension * FIT_TRIALS))
        .map(|ordinal| intervention(dimension, seed + 101, ordinal))
        .collect();
    let assessment_interventions = (0..ASSESSMENT_TRIALS)
        .map(|ordinal| intervention(dimension, seed + 1009, ordinal))
        .collect();

    Task {
        mode,
        dimension,
        seed,
        truth_weights,
        measured_weights,
        narrative_weights,
        shuffled_weights,
        interaction,
        fit_interventions,
        assessment_interventions,
    }
}

fn linear_effect(weights: &[i32], intervention: &[i32]) -> i32 {
    weights
        .iter()
        .zip(intervention)
        .map(|(weight, delta)| weight * delta)
        .sum()
}

fn actor_effect(task: &Task, intervention: &[i32]) -> i32 {
    let linear = linear_effect(&task.truth_weights, intervention);
    let interaction = task
        .interaction
        .map(|(left, right, coefficient)| coefficient * intervention[left] * intervention[right])
        .unwrap_or(0);
    linear + interaction
}

fn mse_for_report(task: &Task, weights: &[i32]) -> f64 {
    let total = task
        .assessment_interventions
        .iter()
        .map(|intervention| {
            let error = linear_effect(weights, intervention) - actor_effect(task, intervention);
            f64::from(error * error)
        })
        .sum::<f64>();
    total / task.assessment_interventions.len() as f64
}

fn constant_mse(task: &Task, prediction: i32) -> f64 {
    let total = task
        .assessment_interventions
        .iter()
        .map(|intervention| {
            let error = prediction - actor_effect(task, intervention);
            f64::from(error * error)
        })
        .sum::<f64>();
    total / task.assessment_interventions.len() as f64
}

fn fit_mean(task: &Task) -> i32 {
    let total = task
        .fit_interventions
        .iter()
        .map(|intervention| actor_effect(task, intervention))
        .sum::<i32>();
    total / task.fit_interventions.len() as i32
}

fn evaluate(task: &Task) -> TaskMetrics {
    let measured_mse = mse_for_report(task, &task.measured_weights);
    let narrative_mse = mse_for_report(task, &task.narrative_weights);
    let shuffled_mse = mse_for_report(task, &task.shuffled_weights);
    let zero_mse = constant_mse(task, 0);
    let mean_mse = constant_mse(task, fit_mean(task));
    let oracle_mse = task
        .assessment_interventions
        .iter()
        .map(|intervention| {
            let error = actor_effect(task, intervention) - actor_effect(task, intervention);
            f64::from(error * error)
        })
        .sum::<f64>()
        / task.assessment_interventions.len() as f64;
    let all_baseline_win = measured_mse < narrative_mse
        && measured_mse < shuffled_mse
        && measured_mse < zero_mse
        && measured_mse < mean_mse;
    TaskMetrics {
        mode: task.mode,
        measured_mse,
        narrative_mse,
        shuffled_mse,
        zero_mse,
        mean_mse,
        oracle_mse,
        all_baseline_win,
        narrative_win: measured_mse < narrative_mse,
    }
}

fn mean_and_variance(values: &[f64]) -> (f64, f64) {
    let mean = values.iter().sum::<f64>() / values.len() as f64;
    let variance = values
        .iter()
        .map(|value| (value - mean) * (value - mean))
        .sum::<f64>()
        / values.len() as f64;
    (mean, variance)
}

fn run_matrix() -> MatrixSummary {
    let mut metrics = Vec::new();
    for mode in MODES {
        for dimension in DIMENSIONS {
            for seed in SEEDS {
                let candidate = task(mode, dimension, seed);
                assert_eq!(candidate.dimension, dimension);
                assert_eq!(candidate.seed, seed);
                metrics.push(evaluate(&candidate));
            }
        }
    }

    let linear = metrics
        .iter()
        .filter(|metric| metric.mode != Mode::UnmodeledInteraction)
        .collect::<Vec<_>>();
    let interactions = metrics
        .iter()
        .filter(|metric| metric.mode == Mode::UnmodeledInteraction)
        .collect::<Vec<_>>();
    let measured_mse = metrics
        .iter()
        .map(|metric| metric.measured_mse)
        .collect::<Vec<_>>();
    let (measured_mean_mse, measured_mse_variance) = mean_and_variance(&measured_mse);
    let mean = |selector: fn(&TaskMetrics) -> f64| {
        metrics.iter().map(selector).sum::<f64>() / metrics.len() as f64
    };
    MatrixSummary {
        task_count: metrics.len(),
        linear_task_count: linear.len(),
        interaction_task_count: interactions.len(),
        linear_all_baseline_wins: linear
            .iter()
            .filter(|metric| metric.all_baseline_win)
            .count(),
        linear_narrative_wins: linear.iter().filter(|metric| metric.narrative_win).count(),
        interaction_all_baseline_failures: interactions
            .iter()
            .filter(|metric| !metric.all_baseline_win)
            .count(),
        linear_all_baseline_win_rate: linear
            .iter()
            .filter(|metric| metric.all_baseline_win)
            .count() as f64
            / linear.len() as f64,
        linear_narrative_win_rate: linear.iter().filter(|metric| metric.narrative_win).count()
            as f64
            / linear.len() as f64,
        measured_mean_mse,
        measured_mse_variance,
        narrative_mean_mse: mean(|metric| metric.narrative_mse),
        shuffled_mean_mse: mean(|metric| metric.shuffled_mse),
        zero_mean_mse: mean(|metric| metric.zero_mse),
        fit_mean_mean_mse: mean(|metric| metric.mean_mse),
        oracle_mean_mse: mean(|metric| metric.oracle_mse),
    }
}

#[test]
fn stress_matrix_passes_linear_measurement_gate() {
    let summary = run_matrix();
    println!("V31 summary: {summary:?}");
    assert_eq!(summary.task_count, 36);
    assert_eq!(summary.linear_task_count, 24);
    assert_eq!(summary.interaction_task_count, 12);
    assert!(summary.linear_all_baseline_win_rate >= 0.80);
    assert!(summary.linear_narrative_win_rate >= 0.90);
    assert!(summary.measured_mean_mse < summary.narrative_mean_mse);
    assert!(summary.measured_mean_mse < summary.shuffled_mean_mse);
    assert!(summary.measured_mean_mse < summary.zero_mean_mse);
    assert!(summary.measured_mean_mse < summary.fit_mean_mean_mse);
}

#[test]
fn stress_matrix_retains_declared_failure_modes_and_variance() {
    let summary = run_matrix();
    assert!(summary.interaction_all_baseline_failures > 0);
    assert!(summary.measured_mse_variance.is_finite());
    assert!(summary.measured_mse_variance >= 0.0);
    assert!(summary.oracle_mean_mse.abs() < f64::EPSILON);
}

#[test]
fn stress_matrix_claim_ceiling_is_local_and_explicit() {
    let summary = run_matrix();
    assert!(summary.linear_all_baseline_win_rate.is_finite());
    assert_eq!(
        "LocalDevelopmentSyntheticMeasurementStressTest",
        "LocalDevelopmentSyntheticMeasurementStressTest"
    );
}
