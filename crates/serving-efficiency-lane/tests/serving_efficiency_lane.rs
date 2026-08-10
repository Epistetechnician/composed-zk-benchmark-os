use serving_efficiency_lane::{
    default_lane_descriptor, evaluate_adoption, evaluation_report_digest,
    evaluation_request_digest, evaluation_request_digest_hex, hex_lower, is_lower_hex64,
    lane_descriptor_digest, require_single_regime, tagged_sha256, validate_baseline,
    validate_evaluation_request, validate_lane_descriptor, validate_measured_results,
    validate_preregistered_gates, CandidateClass, CandidateDisposition, ClaimCeiling,
    EvaluationRegime, EvaluationReport, EvaluationRequest, GateFailure, LaneClaimBoundary,
    LaneError, MeasuredResults, PreregisteredGates, ServingBaselineDescriptor,
    BASELINE_FIXTURE_BYTES, BASELINE_FIXTURE_PATH, BASELINE_FIXTURE_SHA256, STATE_SLICE,
};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

fn preregistered_gates() -> PreregisteredGates {
    PreregisteredGates {
        max_full_cost_per_verified_utility: 10.0,
        min_pass_all_k: 0.95,
        max_p95_latency_ms: 5_000.0,
        min_concurrency: 64,
    }
}

fn measured_results() -> MeasuredResults {
    MeasuredResults {
        full_cost_per_verified_utility: 8.0,
        pass_all_k: 0.97,
        p95_latency_ms: 4_200.0,
        concurrency: 128,
        cached_input_tokens: 1_000,
        uncached_input_tokens: 2_000,
    }
}

fn sample_request(adoption_slice: Option<&str>) -> EvaluationRequest {
    EvaluationRequest {
        lane_descriptor_digest_hex: hex_lower(&lane_descriptor_digest(&default_lane_descriptor())),
        candidate_class: CandidateClass::ServingSideKvManagement,
        regime: EvaluationRegime::NormalizedCausal,
        gates: preregistered_gates(),
        adoption_phase_state_slice: adoption_slice.map(str::to_owned),
    }
}

fn sample_report(request: &EvaluationRequest) -> EvaluationReport {
    EvaluationReport {
        request_digest_hex: evaluation_request_digest_hex(request),
        regime: request.regime,
        results: measured_results(),
        claim_ceiling: ClaimCeiling::InertMetadataOnly,
    }
}

#[test]
fn baseline_fixture_digest_matches_repository_file() {
    let workspace_root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("crate should live under workspace/crates");
    let fixture = workspace_root.join(BASELINE_FIXTURE_PATH);
    let bytes = fs::read(&fixture).expect("baseline fixture should be readable");
    assert_eq!(bytes.len() as u64, BASELINE_FIXTURE_BYTES);
    let digest: [u8; 32] = Sha256::digest(&bytes).into();
    assert_eq!(hex_lower(&digest), BASELINE_FIXTURE_SHA256);
    assert_eq!(
        validate_baseline(&ServingBaselineDescriptor::phase799_recorded()),
        Ok(())
    );
}

#[test]
fn default_lane_descriptor_is_inert_and_reference_only() {
    let descriptor = default_lane_descriptor();
    assert_eq!(descriptor.state_slice, STATE_SLICE);
    assert_eq!(validate_lane_descriptor(&descriptor), Ok(()));
    assert_eq!(descriptor.disposition, CandidateDisposition::ReferenceOnly);
    assert_eq!(descriptor.candidate_classes, CandidateClass::PANEL.to_vec());
    for class in CandidateClass::PANEL {
        assert_eq!(
            class.phase799_disposition(),
            CandidateDisposition::ReferenceOnly
        );
    }
    assert_eq!(descriptor.claim_boundary, LaneClaimBoundary::default());
    assert!(descriptor.claim_boundary.inert_metadata_only);
    assert!(!descriptor.claim_boundary.accepted_evidence);
    assert!(!descriptor.claim_boundary.benchmark_evidence);
    assert!(!descriptor.claim_boundary.production_readiness);
    assert!(!descriptor.claim_boundary.sota);
    assert!(!descriptor.claim_boundary.authority_granted);
}

#[test]
fn lane_descriptor_validation_fails_closed() {
    let mut descriptor = default_lane_descriptor();
    descriptor.state_slice = "other-slice".to_owned();
    assert_eq!(
        validate_lane_descriptor(&descriptor),
        Err(LaneError::StateSliceMismatch)
    );

    let mut descriptor = default_lane_descriptor();
    descriptor.schema_version = "serving-efficiency-lane-v2".to_owned();
    assert_eq!(
        validate_lane_descriptor(&descriptor),
        Err(LaneError::SchemaVersionMismatch)
    );

    let mut descriptor = default_lane_descriptor();
    descriptor.candidate_classes.clear();
    assert_eq!(
        validate_lane_descriptor(&descriptor),
        Err(LaneError::EmptyCandidateSet)
    );

    let mut descriptor = default_lane_descriptor();
    descriptor
        .candidate_classes
        .push(CandidateClass::AgentMemoryPolicyMode);
    assert_eq!(
        validate_lane_descriptor(&descriptor),
        Err(LaneError::DuplicateCandidateClass)
    );

    let mut descriptor = default_lane_descriptor();
    descriptor.claim_boundary.production_readiness = true;
    assert_eq!(
        validate_lane_descriptor(&descriptor),
        Err(LaneError::ClaimEscalation)
    );

    let mut descriptor = default_lane_descriptor();
    descriptor.baseline.max_model_len = 262_144;
    assert_eq!(
        validate_lane_descriptor(&descriptor),
        Err(LaneError::BaselineBindingMismatch)
    );
}

#[test]
fn baseline_binding_is_exact_and_digest_sensitive() {
    let recorded = ServingBaselineDescriptor::phase799_recorded();

    let mut mutated = recorded.clone();
    mutated.prefix_caching_enabled = false;
    assert_eq!(
        validate_baseline(&mutated),
        Err(LaneError::BaselineBindingMismatch)
    );
    assert_ne!(recorded.digest(), mutated.digest());

    let mut mutated = recorded.clone();
    mutated.fixture_sha256 = "0".repeat(64);
    assert_ne!(recorded.digest(), mutated.digest());

    let mut mutated = recorded.clone();
    mutated.max_num_seqs = 512;
    assert_ne!(recorded.digest(), mutated.digest());
}

#[test]
fn tagged_hash_is_deterministic_and_field_bound() {
    let first = tagged_sha256("serving.test", &[b"ab", b"c"]);
    assert_eq!(first, tagged_sha256("serving.test", &[b"ab", b"c"]));
    assert_ne!(first, tagged_sha256("serving.test", &[b"a", b"bc"]));
    assert_ne!(first, tagged_sha256("serving.other", &[b"ab", b"c"]));
    assert!(is_lower_hex64(&hex_lower(&first)));
    assert!(!is_lower_hex64(&"0".repeat(63)));
    assert!(!is_lower_hex64(&format!("{}G", "0".repeat(63))));
    assert!(!is_lower_hex64(&format!("{}A", "0".repeat(63))));
}

#[test]
fn adoption_stays_unauthorized_without_a_reviewed_phase() {
    let request = sample_request(None);
    let report = sample_report(&request);
    let decision = evaluate_adoption(&request, &report).expect("valid request/report pair");
    assert!(decision.all_gates_passed);
    assert!(!decision.adoption_authorized);
    assert!(decision.failures.is_empty());
}

#[test]
fn adoption_metadata_decision_requires_every_gate() {
    let request = sample_request(Some("future-adoption-phase"));
    let report = sample_report(&request);
    let decision = evaluate_adoption(&request, &report).expect("valid request/report pair");
    assert!(decision.all_gates_passed);
    assert!(decision.adoption_authorized);

    let request = sample_request(Some("future-adoption-phase"));
    let mut report = sample_report(&request);
    report.results.full_cost_per_verified_utility = 20.0;
    let decision = evaluate_adoption(&request, &report).expect("valid request/report pair");
    assert_eq!(decision.failures, vec![GateFailure::Cost]);
    assert!(!decision.adoption_authorized);

    let request = sample_request(Some("future-adoption-phase"));
    let mut report = sample_report(&request);
    report.results.pass_all_k = 0.5;
    report.results.concurrency = 1;
    let decision = evaluate_adoption(&request, &report).expect("valid request/report pair");
    assert_eq!(
        decision.failures,
        vec![GateFailure::Reliability, GateFailure::Concurrency]
    );
    assert!(!decision.adoption_authorized);

    let request = sample_request(Some("future-adoption-phase"));
    let mut report = sample_report(&request);
    report.results.p95_latency_ms = 9_000.0;
    let decision = evaluate_adoption(&request, &report).expect("valid request/report pair");
    assert_eq!(decision.failures, vec![GateFailure::Latency]);
    assert!(!decision.adoption_authorized);
}

#[test]
fn request_report_binding_fails_closed() {
    let request = sample_request(None);

    let mut report = sample_report(&request);
    report.request_digest_hex = "0".repeat(64);
    assert_eq!(
        evaluate_adoption(&request, &report),
        Err(LaneError::RequestBindingMismatch)
    );

    let mut report = sample_report(&request);
    report.regime = EvaluationRegime::NativeBestDeployment;
    assert_eq!(
        evaluate_adoption(&request, &report),
        Err(LaneError::RegimeMismatch)
    );

    let mut report = sample_report(&request);
    report.request_digest_hex = "not-hex".to_owned();
    assert_eq!(
        evaluate_adoption(&request, &report),
        Err(LaneError::InvalidDigestEncoding)
    );

    let mut report = sample_report(&request);
    report.results.pass_all_k = f64::NAN;
    assert_eq!(
        evaluate_adoption(&request, &report),
        Err(LaneError::NonFiniteMetric)
    );

    let request = sample_request(Some("  "));
    assert_eq!(
        validate_evaluation_request(&request),
        Err(LaneError::EmptyAdoptionPhaseSlice)
    );
}

#[test]
fn regime_pooling_rejects_mixed_reports() {
    let request = sample_request(None);
    let causal = sample_report(&request);
    let mut native = sample_report(&request);
    native.regime = EvaluationRegime::NativeBestDeployment;
    assert_eq!(
        require_single_regime(&[causal.clone(), native]),
        Err(LaneError::RegimePooling)
    );
    assert_eq!(
        require_single_regime(&[causal]),
        Ok(EvaluationRegime::NormalizedCausal)
    );
    assert_eq!(require_single_regime(&[]), Err(LaneError::EmptyReportSet));
}

#[test]
fn metrics_and_gates_fail_closed() {
    let mut gates = preregistered_gates();
    gates.max_full_cost_per_verified_utility = f64::NAN;
    assert_eq!(
        validate_preregistered_gates(&gates),
        Err(LaneError::NonFiniteMetric)
    );

    let mut gates = preregistered_gates();
    gates.min_pass_all_k = 1.5;
    assert_eq!(
        validate_preregistered_gates(&gates),
        Err(LaneError::InvalidGateThreshold)
    );

    let mut gates = preregistered_gates();
    gates.min_concurrency = 0;
    assert_eq!(
        validate_preregistered_gates(&gates),
        Err(LaneError::InvalidGateThreshold)
    );

    let mut results = measured_results();
    results.pass_all_k = f64::INFINITY;
    assert_eq!(
        validate_measured_results(&results),
        Err(LaneError::NonFiniteMetric)
    );

    let mut results = measured_results();
    results.concurrency = 0;
    assert_eq!(
        validate_measured_results(&results),
        Err(LaneError::InvalidMeasurement)
    );
}

#[test]
fn request_and_report_digests_bind_every_field() {
    let request = sample_request(None);
    let base_request = evaluation_request_digest(&request);

    let mut mutated = request.clone();
    mutated.gates.min_concurrency = 123;
    assert_ne!(base_request, evaluation_request_digest(&mutated));

    let mut mutated = request.clone();
    mutated.adoption_phase_state_slice = Some("reviewed-phase".to_owned());
    assert_ne!(base_request, evaluation_request_digest(&mutated));

    let mut mutated = request.clone();
    mutated.candidate_class = CandidateClass::AgentMemoryPolicyMode;
    assert_ne!(base_request, evaluation_request_digest(&mutated));

    let report = sample_report(&request);
    let base_report = evaluation_report_digest(&report);

    let mut mutated_report = report.clone();
    mutated_report.results.cached_input_tokens += 1;
    assert_ne!(base_report, evaluation_report_digest(&mutated_report));

    let mut mutated_report = report.clone();
    mutated_report.results.uncached_input_tokens += 1;
    assert_ne!(base_report, evaluation_report_digest(&mutated_report));
}
