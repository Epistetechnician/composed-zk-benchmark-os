//! Pure-data serving-efficiency lane contracts.
//!
//! State slice: `phase-800-serving-efficiency-lane-inert-metadata`.
//!
//! Inert metadata only. This crate performs no model execution, serving,
//! benchmarking, network, process, environment, or evidence-lane I/O. It binds
//! the Phase 799 memory architecture sustainability and serving efficiency
//! boundary into typed, digest-chained contracts: lane descriptors, candidate
//! classes, evaluation request/report shapes, preregistered gates, and a
//! fail-closed adoption decision that models "a separately reviewed phase is
//! still required" as data.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

pub const STATE_SLICE: &str = "phase-800-serving-efficiency-lane-inert-metadata";
pub const LANE_SCHEMA_VERSION: &str = "serving-efficiency-lane-v1";
pub const TAG_DOMAIN: &str = "serving-efficiency-lane.v1";

/// Baseline serving facts recorded by the Phase 799 boundary from the Phase
/// 57+ Phala CVM attestation fixture. The deployment configuration is owned
/// by the product repository; this crate binds the recorded facts only.
pub const BASELINE_FIXTURE_PATH: &str =
    "crates/hsai-attestation-phala/tests/fixtures/phala_trust_center_app_2026_06_16.json";
pub const BASELINE_FIXTURE_SHA256: &str =
    "33135af6b978a4f0255cdcf453c3479c46b1fa2d8aac8f019649b4c1ed6becf3";
pub const BASELINE_FIXTURE_BYTES: u64 = 54_662;
pub const BASELINE_MODEL_ID: &str = "Qwen/Qwen3-Next-80B-A3B-Thinking-FP8";
pub const BASELINE_MAX_MODEL_LEN: u64 = 131_072;
pub const BASELINE_MAX_NUM_SEQS: u64 = 256;

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CandidateClass {
    KdaHybridAttentionModelLane,
    ServingSideKvManagement,
    DisaggregatedKvStorageRouting,
    AgentMemoryPolicyMode,
}

impl CandidateClass {
    pub const PANEL: [Self; 4] = [
        Self::KdaHybridAttentionModelLane,
        Self::ServingSideKvManagement,
        Self::DisaggregatedKvStorageRouting,
        Self::AgentMemoryPolicyMode,
    ];

    pub fn as_label(self) -> &'static str {
        match self {
            Self::KdaHybridAttentionModelLane => "kda_hybrid_attention_model_lane",
            Self::ServingSideKvManagement => "serving_side_kv_management",
            Self::DisaggregatedKvStorageRouting => "disaggregated_kv_storage_routing",
            Self::AgentMemoryPolicyMode => "agent_memory_policy_mode",
        }
    }

    /// Phase 799 fixes every candidate class at REFERENCE-ONLY until a future
    /// reviewed phase justifies adoption with measured evidence.
    pub fn phase799_disposition(self) -> CandidateDisposition {
        CandidateDisposition::ReferenceOnly
    }
}

/// Closed on purpose: the only disposition available before a separately
/// reviewed adoption phase exists. Extending this enum is itself a reviewed
/// state slice.
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CandidateDisposition {
    ReferenceOnly,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EvaluationRegime {
    NormalizedCausal,
    NativeBestDeployment,
}

impl EvaluationRegime {
    pub fn as_label(self) -> &'static str {
        match self {
            Self::NormalizedCausal => "normalized_causal",
            Self::NativeBestDeployment => "native_best_deployment",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct LaneClaimBoundary {
    pub inert_metadata_only: bool,
    pub accepted_evidence: bool,
    pub benchmark_evidence: bool,
    pub production_readiness: bool,
    pub sota: bool,
    pub authority_granted: bool,
}

impl Default for LaneClaimBoundary {
    fn default() -> Self {
        Self {
            inert_metadata_only: true,
            accepted_evidence: false,
            benchmark_evidence: false,
            production_readiness: false,
            sota: false,
            authority_granted: false,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct ServingBaselineDescriptor {
    pub model_id: String,
    pub max_model_len: u64,
    pub max_num_seqs: u64,
    pub prefix_caching_enabled: bool,
    pub single_instance: bool,
    pub fixture_path: String,
    pub fixture_sha256: String,
    pub fixture_bytes: u64,
}

impl ServingBaselineDescriptor {
    pub fn phase799_recorded() -> Self {
        Self {
            model_id: BASELINE_MODEL_ID.to_owned(),
            max_model_len: BASELINE_MAX_MODEL_LEN,
            max_num_seqs: BASELINE_MAX_NUM_SEQS,
            prefix_caching_enabled: true,
            single_instance: true,
            fixture_path: BASELINE_FIXTURE_PATH.to_owned(),
            fixture_sha256: BASELINE_FIXTURE_SHA256.to_owned(),
            fixture_bytes: BASELINE_FIXTURE_BYTES,
        }
    }

    pub fn digest(&self) -> [u8; 32] {
        tagged_sha256(
            TAG_DOMAIN,
            &[
                b"baseline",
                self.model_id.as_bytes(),
                &self.max_model_len.to_be_bytes(),
                &self.max_num_seqs.to_be_bytes(),
                &[u8::from(self.prefix_caching_enabled)],
                &[u8::from(self.single_instance)],
                self.fixture_path.as_bytes(),
                self.fixture_sha256.as_bytes(),
                &self.fixture_bytes.to_be_bytes(),
            ],
        )
    }
}

/// The baseline is a recorded fact, not a tunable. Any change requires a
/// reviewed phase that updates the Phase 799 record and these constants.
pub fn validate_baseline(descriptor: &ServingBaselineDescriptor) -> Result<(), LaneError> {
    if descriptor == &ServingBaselineDescriptor::phase799_recorded() {
        Ok(())
    } else {
        Err(LaneError::BaselineBindingMismatch)
    }
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct ServingEfficiencyLaneDescriptor {
    pub state_slice: String,
    pub schema_version: String,
    pub baseline: ServingBaselineDescriptor,
    pub candidate_classes: Vec<CandidateClass>,
    pub disposition: CandidateDisposition,
    pub claim_boundary: LaneClaimBoundary,
}

pub fn default_lane_descriptor() -> ServingEfficiencyLaneDescriptor {
    ServingEfficiencyLaneDescriptor {
        state_slice: STATE_SLICE.to_owned(),
        schema_version: LANE_SCHEMA_VERSION.to_owned(),
        baseline: ServingBaselineDescriptor::phase799_recorded(),
        candidate_classes: CandidateClass::PANEL.to_vec(),
        disposition: CandidateDisposition::ReferenceOnly,
        claim_boundary: LaneClaimBoundary::default(),
    }
}

pub fn validate_lane_descriptor(
    descriptor: &ServingEfficiencyLaneDescriptor,
) -> Result<(), LaneError> {
    if descriptor.state_slice != STATE_SLICE {
        return Err(LaneError::StateSliceMismatch);
    }
    if descriptor.schema_version != LANE_SCHEMA_VERSION {
        return Err(LaneError::SchemaVersionMismatch);
    }
    validate_baseline(&descriptor.baseline)?;
    if descriptor.candidate_classes.is_empty() {
        return Err(LaneError::EmptyCandidateSet);
    }
    let mut sorted = descriptor.candidate_classes.clone();
    sorted.sort_unstable();
    sorted.dedup();
    if sorted.len() != descriptor.candidate_classes.len() {
        return Err(LaneError::DuplicateCandidateClass);
    }
    if descriptor.disposition != CandidateDisposition::ReferenceOnly {
        return Err(LaneError::DispositionNotReferenceOnly);
    }
    if descriptor.claim_boundary != LaneClaimBoundary::default() {
        return Err(LaneError::ClaimEscalation);
    }
    Ok(())
}

pub fn lane_descriptor_digest(descriptor: &ServingEfficiencyLaneDescriptor) -> [u8; 32] {
    let mut fields: Vec<&[u8]> = vec![
        b"lane-descriptor",
        descriptor.state_slice.as_bytes(),
        descriptor.schema_version.as_bytes(),
    ];
    let baseline_digest = descriptor.baseline.digest();
    fields.push(&baseline_digest);
    for class in &descriptor.candidate_classes {
        fields.push(class.as_label().as_bytes());
    }
    fields.push(b"reference_only");
    let boundary = descriptor.claim_boundary;
    let flags = [
        u8::from(boundary.inert_metadata_only),
        u8::from(boundary.accepted_evidence),
        u8::from(boundary.benchmark_evidence),
        u8::from(boundary.production_readiness),
        u8::from(boundary.sota),
        u8::from(boundary.authority_granted),
    ];
    fields.push(&flags);
    tagged_sha256(TAG_DOMAIN, &fields)
}

#[derive(Clone, Copy, Debug, PartialEq, Serialize, Deserialize)]
pub struct PreregisteredGates {
    pub max_full_cost_per_verified_utility: f64,
    pub min_pass_all_k: f64,
    pub max_p95_latency_ms: f64,
    pub min_concurrency: u64,
}

pub fn validate_preregistered_gates(gates: &PreregisteredGates) -> Result<(), LaneError> {
    let finite = gates.max_full_cost_per_verified_utility.is_finite()
        && gates.min_pass_all_k.is_finite()
        && gates.max_p95_latency_ms.is_finite();
    if !finite {
        return Err(LaneError::NonFiniteMetric);
    }
    if gates.max_full_cost_per_verified_utility <= 0.0
        || !(0.0..=1.0).contains(&gates.min_pass_all_k)
        || gates.max_p95_latency_ms <= 0.0
        || gates.min_concurrency == 0
    {
        return Err(LaneError::InvalidGateThreshold);
    }
    Ok(())
}

#[derive(Clone, Copy, Debug, PartialEq, Serialize, Deserialize)]
pub struct MeasuredResults {
    pub full_cost_per_verified_utility: f64,
    pub pass_all_k: f64,
    pub p95_latency_ms: f64,
    pub concurrency: u64,
    /// Cached and uncached input tokens remain separate cost lines; missing
    /// telemetry fails closed and is never silently zero.
    pub cached_input_tokens: u64,
    pub uncached_input_tokens: u64,
}

pub fn validate_measured_results(results: &MeasuredResults) -> Result<(), LaneError> {
    let finite = results.full_cost_per_verified_utility.is_finite()
        && results.pass_all_k.is_finite()
        && results.p95_latency_ms.is_finite();
    if !finite {
        return Err(LaneError::NonFiniteMetric);
    }
    if results.full_cost_per_verified_utility < 0.0
        || !(0.0..=1.0).contains(&results.pass_all_k)
        || results.p95_latency_ms < 0.0
        || results.concurrency == 0
    {
        return Err(LaneError::InvalidMeasurement);
    }
    Ok(())
}

/// Closed claim ceiling for this crate: nothing produced here is more than
/// inert metadata.
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ClaimCeiling {
    InertMetadataOnly,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct EvaluationRequest {
    pub lane_descriptor_digest_hex: String,
    pub candidate_class: CandidateClass,
    pub regime: EvaluationRegime,
    pub gates: PreregisteredGates,
    /// Names the separately reviewed adoption phase, when one exists. `None`
    /// keeps adoption unauthorized no matter how good the measurements are.
    pub adoption_phase_state_slice: Option<String>,
}

pub fn validate_evaluation_request(request: &EvaluationRequest) -> Result<(), LaneError> {
    if !is_lower_hex64(&request.lane_descriptor_digest_hex) {
        return Err(LaneError::InvalidDigestEncoding);
    }
    validate_preregistered_gates(&request.gates)?;
    if let Some(slice) = &request.adoption_phase_state_slice {
        if slice.trim().is_empty() {
            return Err(LaneError::EmptyAdoptionPhaseSlice);
        }
    }
    Ok(())
}

pub fn evaluation_request_digest(request: &EvaluationRequest) -> [u8; 32] {
    let gates = request.gates;
    let adoption = request
        .adoption_phase_state_slice
        .as_deref()
        .unwrap_or("none");
    tagged_sha256(
        TAG_DOMAIN,
        &[
            b"evaluation-request",
            request.lane_descriptor_digest_hex.as_bytes(),
            request.candidate_class.as_label().as_bytes(),
            request.regime.as_label().as_bytes(),
            &gates
                .max_full_cost_per_verified_utility
                .to_bits()
                .to_be_bytes(),
            &gates.min_pass_all_k.to_bits().to_be_bytes(),
            &gates.max_p95_latency_ms.to_bits().to_be_bytes(),
            &gates.min_concurrency.to_be_bytes(),
            adoption.as_bytes(),
        ],
    )
}

pub fn evaluation_request_digest_hex(request: &EvaluationRequest) -> String {
    hex_lower(&evaluation_request_digest(request))
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct EvaluationReport {
    pub request_digest_hex: String,
    pub regime: EvaluationRegime,
    pub results: MeasuredResults,
    pub claim_ceiling: ClaimCeiling,
}

pub fn validate_evaluation_report(report: &EvaluationReport) -> Result<(), LaneError> {
    if !is_lower_hex64(&report.request_digest_hex) {
        return Err(LaneError::InvalidDigestEncoding);
    }
    validate_measured_results(&report.results)
}

pub fn evaluation_report_digest(report: &EvaluationReport) -> [u8; 32] {
    let results = report.results;
    tagged_sha256(
        TAG_DOMAIN,
        &[
            b"evaluation-report",
            report.request_digest_hex.as_bytes(),
            report.regime.as_label().as_bytes(),
            &results
                .full_cost_per_verified_utility
                .to_bits()
                .to_be_bytes(),
            &results.pass_all_k.to_bits().to_be_bytes(),
            &results.p95_latency_ms.to_bits().to_be_bytes(),
            &results.concurrency.to_be_bytes(),
            &results.cached_input_tokens.to_be_bytes(),
            &results.uncached_input_tokens.to_be_bytes(),
            b"inert_metadata_only",
        ],
    )
}

/// Normalized causal results and native-best deployment results may never be
/// pooled into one claim.
pub fn require_single_regime(reports: &[EvaluationReport]) -> Result<EvaluationRegime, LaneError> {
    let first = reports.first().ok_or(LaneError::EmptyReportSet)?;
    if reports.iter().any(|report| report.regime != first.regime) {
        return Err(LaneError::RegimePooling);
    }
    Ok(first.regime)
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum GateFailure {
    Cost,
    Reliability,
    Latency,
    Concurrency,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct AdoptionDecision {
    pub candidate_class: CandidateClass,
    pub regime: EvaluationRegime,
    pub all_gates_passed: bool,
    /// Metadata-level decision only. Even `true` does not adopt anything:
    /// actual adoption still requires the separately reviewed phase named in
    /// the request, with license/supply-chain review and attestation
    /// compatibility per Phase 799 section 5.
    pub adoption_authorized: bool,
    pub failures: Vec<GateFailure>,
}

pub fn evaluate_adoption(
    request: &EvaluationRequest,
    report: &EvaluationReport,
) -> Result<AdoptionDecision, LaneError> {
    validate_evaluation_request(request)?;
    validate_evaluation_report(report)?;
    if report.request_digest_hex != evaluation_request_digest_hex(request) {
        return Err(LaneError::RequestBindingMismatch);
    }
    if report.regime != request.regime {
        return Err(LaneError::RegimeMismatch);
    }
    let gates = request.gates;
    let results = report.results;
    let mut failures = Vec::new();
    if results.full_cost_per_verified_utility > gates.max_full_cost_per_verified_utility {
        failures.push(GateFailure::Cost);
    }
    if results.pass_all_k < gates.min_pass_all_k {
        failures.push(GateFailure::Reliability);
    }
    if results.p95_latency_ms > gates.max_p95_latency_ms {
        failures.push(GateFailure::Latency);
    }
    if results.concurrency < gates.min_concurrency {
        failures.push(GateFailure::Concurrency);
    }
    failures.sort();
    failures.dedup();
    let all_gates_passed = failures.is_empty();
    let adoption_authorized = all_gates_passed
        && request
            .adoption_phase_state_slice
            .as_deref()
            .is_some_and(|slice| !slice.trim().is_empty());
    Ok(AdoptionDecision {
        candidate_class: request.candidate_class,
        regime: request.regime,
        all_gates_passed,
        adoption_authorized,
        failures,
    })
}

pub fn tagged_sha256(domain: &str, fields: &[&[u8]]) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update((domain.len() as u64).to_be_bytes());
    digest.update(domain.as_bytes());
    for field in fields {
        digest.update((field.len() as u64).to_be_bytes());
        digest.update(field);
    }
    digest.finalize().into()
}

pub fn hex_lower(bytes: &[u8; 32]) -> String {
    let mut text = String::with_capacity(64);
    for byte in bytes {
        text.push_str(&format!("{byte:02x}"));
    }
    text
}

pub fn is_lower_hex64(text: &str) -> bool {
    text.len() == 64
        && text
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum LaneError {
    StateSliceMismatch,
    SchemaVersionMismatch,
    BaselineBindingMismatch,
    EmptyCandidateSet,
    DuplicateCandidateClass,
    DispositionNotReferenceOnly,
    ClaimEscalation,
    InvalidGateThreshold,
    NonFiniteMetric,
    InvalidMeasurement,
    InvalidDigestEncoding,
    EmptyAdoptionPhaseSlice,
    RequestBindingMismatch,
    RegimeMismatch,
    RegimePooling,
    EmptyReportSet,
}
