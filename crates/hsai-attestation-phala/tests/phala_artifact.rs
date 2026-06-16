use hsai_agent_case::EvidenceLane;
use hsai_agent_case::{ActionId, AgentCase, MemoryRoot, ModelId, OracleContract, Verdict};
use hsai_attestation_phala::{
    parse_phala_artifact, validate_phala_artifact, PhalaArtifactBundle, PhalaAttestationLane,
    PhalaValidationError, PhalaValidationPolicy,
};
use hsai_claim_envelope::{
    admits, conjoin, AcceptancePolicy, Maturity, Predicate, PropertyKind, SubjectId, TrustRoot,
    TrustRootClass, VendorId,
};
use hsai_distinct_agent::{distinctness, Anchor, AnchorBundle, DistinctAgentLane};
use std::collections::BTreeSet;

const FIXTURE: &str = include_str!("fixtures/phala_trust_center_app_2026_06_16.json");

fn bundle() -> PhalaArtifactBundle {
    parse_phala_artifact(FIXTURE).expect("fixture must parse")
}

fn anchor(bundle: &PhalaArtifactBundle) -> Anchor {
    Anchor::HardwareAttested {
        vendor: "phala-dstack".to_owned(),
        device: bundle.app_id.clone(),
    }
}

fn subject(id: &str) -> SubjectId {
    SubjectId(id.to_owned())
}

fn semantic_correctness_action1() -> Predicate {
    Predicate {
        subject: subject("action1"),
        property: PropertyKind::SemanticCorrectness,
    }
}

fn case(bundle: &PhalaArtifactBundle) -> AgentCase {
    AgentCase {
        action: ActionId("action1".to_owned()),
        subject: subject("agentA"),
        claimed_model: ModelId("modelA".to_owned()),
        memory_root: MemoryRoot([7; 32]),
        observed_at: bundle.observed_timestamp,
        oracle: OracleContract {
            expected: Verdict::Accept,
            target_guarantees: BTreeSet::from([distinctness(&subject("agentA"))]),
            excluded: BTreeSet::from([semantic_correctness_action1()]),
        },
    }
}

fn acceptance_policy(case: &AgentCase) -> AcceptancePolicy {
    AcceptancePolicy {
        require: BTreeSet::from([distinctness(&case.subject)]),
        min_maturity: Maturity::Attested,
        forbid_roots: BTreeSet::<TrustRootClass>::new(),
        require_closed: true,
        at: case.observed_at,
    }
}

fn root(id: &str) -> TrustRoot {
    TrustRoot::HardwareVendor(VendorId(id.to_owned()))
}

fn mutate_first_hex_char(value: &mut String) {
    let replacement = if value.starts_with('0') { "1" } else { "0" };
    value.replace_range(0..1, replacement);
}

#[test]
fn accepted_captured_artifact_closes_distinctness() {
    let bundle = bundle();
    let policy = PhalaValidationPolicy::for_bundle(&bundle, 600);
    let validated = validate_phala_artifact(&bundle, &policy, bundle.observed_timestamp)
        .expect("captured artifact must validate");

    assert_eq!(validated.anchor_id, bundle.anchor_id);
    assert_eq!(validated.report_data_hex, bundle.report_data_hex);
    assert_eq!(validated.compose_hash, bundle.compose_hash);
    assert!(validated
        .trust_roots
        .contains(&root("managed:phala-trust-center")));
    assert!(validated
        .trust_roots
        .contains(&root("managed:intel-trust-authority")));

    let case = case(&bundle);
    let anchor = anchor(&bundle);
    let distinct =
        DistinctAgentLane::new(AnchorBundle(BTreeSet::from([anchor.clone()]))).evaluate(&case);
    let attestation = PhalaAttestationLane::new(anchor, bundle, policy).evaluate(&case);
    let combined = conjoin(distinct, attestation);

    assert_eq!(combined.maturity, Maturity::Attested);
    assert!(combined.assumptions.is_empty());
    assert!(admits(acceptance_policy(&case), combined).is_ok());
}

#[test]
fn mutated_report_data_rejects() {
    let bundle = bundle();
    let policy = PhalaValidationPolicy::for_bundle(&bundle, 600);
    let mut mutated = bundle.clone();
    mutate_first_hex_char(&mut mutated.report_data_hex);

    assert!(matches!(
        validate_phala_artifact(&mutated, &policy, bundle.observed_timestamp),
        Err(PhalaValidationError::ReportDataMismatch { .. })
    ));
}

#[test]
fn mutated_compose_hash_rejects() {
    let bundle = bundle();
    let policy = PhalaValidationPolicy::for_bundle(&bundle, 600);
    let mut mutated = bundle.clone();
    mutate_first_hex_char(&mut mutated.compose_hash);

    assert!(matches!(
        validate_phala_artifact(&mutated, &policy, bundle.observed_timestamp),
        Err(PhalaValidationError::ComposeHashMismatch { .. })
    ));
}

#[test]
fn stale_timestamp_rejects() {
    let bundle = bundle();
    let policy = PhalaValidationPolicy::for_bundle(&bundle, 60);
    let now = bundle.observed_timestamp + 61;

    assert!(matches!(
        validate_phala_artifact(&bundle, &policy, now),
        Err(PhalaValidationError::Stale { .. })
    ));
}

#[test]
fn wrong_anchor_rejects() {
    let bundle = bundle();
    let mut policy = PhalaValidationPolicy::for_bundle(&bundle, 600);
    policy.expected_anchor_id = "hw:phala-dstack:wrong-anchor".to_owned();

    assert!(matches!(
        validate_phala_artifact(&bundle, &policy, bundle.observed_timestamp),
        Err(PhalaValidationError::AnchorMismatch { .. })
    ));
}

#[test]
fn managed_verifier_dependency_is_visible_in_trust_roots() {
    let bundle = bundle();
    let policy = PhalaValidationPolicy::for_bundle(&bundle, 600);
    let validated = validate_phala_artifact(&bundle, &policy, bundle.observed_timestamp)
        .expect("captured artifact must validate");

    assert!(validated
        .trust_roots
        .contains(&root("managed:phala-trust-center")));
    assert!(validated
        .trust_roots
        .contains(&root("managed:intel-trust-authority")));
    assert!(validated
        .trust_roots
        .contains(&root(&format!("dstack-os:{}", bundle.os_image_hash))));
    assert!(validated
        .trust_roots
        .contains(&root(&format!("compose:{}", bundle.compose_hash))));
}

#[test]
fn missing_required_docker_digest_rejects() {
    let bundle = bundle();
    let mut policy = PhalaValidationPolicy::for_bundle(&bundle, 600);
    policy.required_docker_image_digests = BTreeSet::from([
        "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff".to_owned(),
    ]);

    assert!(matches!(
        validate_phala_artifact(&bundle, &policy, bundle.observed_timestamp),
        Err(PhalaValidationError::MissingDockerDigest(_))
    ));
}

#[test]
fn mutated_rtmr_event_log_rejects() {
    let bundle = bundle();
    let policy = PhalaValidationPolicy::for_bundle(&bundle, 600);
    let mut mutated = bundle.clone();
    mutate_first_hex_char(&mut mutated.rtmr3_event_log[0].digest);

    assert!(matches!(
        validate_phala_artifact(&mutated, &policy, bundle.observed_timestamp),
        Err(PhalaValidationError::RtmrReplayMismatch { .. })
    ));
}
