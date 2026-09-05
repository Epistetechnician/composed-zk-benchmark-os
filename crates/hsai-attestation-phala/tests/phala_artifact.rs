use hsai_agent_case::EvidenceLane;
use hsai_agent_case::{ActionId, AgentCase, MemoryRoot, ModelId, OracleContract, Verdict};
use hsai_attestation_phala::{
    parse_phala_artifact, validate_phala_artifact, validate_phala_artifact_with_quote_verifier,
    PhalaArtifactAttestationLane, PhalaArtifactBundle, PhalaQuoteVerificationError,
    PhalaQuoteVerifier, PhalaValidationError, PhalaValidationPolicy, ValidatedPhalaAttestation,
    VerifiedPhalaQuote,
};
use hsai_claim_envelope::{
    admits, conjoin, AcceptancePolicy, Maturity, Predicate, PropertyKind, SubjectId, TrustRoot,
    TrustRootClass, VendorId,
};
use hsai_distinct_agent::{distinctness, Anchor, AnchorBundle, DistinctAgentLane};
use std::collections::BTreeSet;

const FIXTURE: &str = include_str!("fixtures/phala_trust_center_app_2026_06_16.json");

struct FixtureQuoteVerifier;

impl PhalaQuoteVerifier for FixtureQuoteVerifier {
    fn verify_quote(
        &self,
        quote: &[u8],
        expected_report_data: &[u8],
    ) -> Result<VerifiedPhalaQuote, PhalaQuoteVerificationError> {
        if quote.is_empty() || expected_report_data.is_empty() {
            return Err(PhalaQuoteVerificationError::Invalid);
        }
        Ok(VerifiedPhalaQuote {
            report_data: expected_report_data.to_vec(),
            trust_roots: BTreeSet::from([root("test:fixture-quote-verifier")]),
        })
    }
}

struct UnboundQuoteVerifier;

impl PhalaQuoteVerifier for UnboundQuoteVerifier {
    fn verify_quote(
        &self,
        _quote: &[u8],
        expected_report_data: &[u8],
    ) -> Result<VerifiedPhalaQuote, PhalaQuoteVerificationError> {
        Ok(VerifiedPhalaQuote {
            report_data: vec![0; expected_report_data.len()],
            trust_roots: BTreeSet::from([root("test:unbound-quote-verifier")]),
        })
    }
}

fn validate_fixture(
    bundle: &PhalaArtifactBundle,
    policy: &PhalaValidationPolicy,
    now: u64,
) -> Result<ValidatedPhalaAttestation, PhalaValidationError> {
    validate_phala_artifact_with_quote_verifier(bundle, policy, now, &FixtureQuoteVerifier)
}

fn bind_bundle_to_case(mut bundle: PhalaArtifactBundle, case: &AgentCase) -> PhalaArtifactBundle {
    let case_hash = hsai_attestation_phala::agent_case_hash(case).expect("case hash serializes");
    bundle.case_hash_hex = encode_hex(&case_hash);
    let nonce = bundle.nonce_hex.to_ascii_lowercase();
    let suffix_len = bundle
        .report_data_hex
        .len()
        .saturating_sub(nonce.len() + 64);
    bundle.report_data_hex = format!("{nonce}{}{}", bundle.case_hash_hex, "0".repeat(suffix_len));
    bundle
}

fn encode_hex(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

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
    let original = bundle();
    let bundle = bind_bundle_to_case(original.clone(), &case(&original));
    let policy = PhalaValidationPolicy::for_bundle(&bundle, 600);
    let validated = validate_fixture(&bundle, &policy, bundle.observed_timestamp)
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
    let attestation = PhalaArtifactAttestationLane::new(anchor, bundle, policy)
        .evaluate_with_quote_verifier(&case, &FixtureQuoteVerifier);
    let combined = conjoin(distinct, attestation);

    assert_eq!(combined.maturity, Maturity::Attested);
    assert!(combined.assumptions.is_empty());
    assert!(admits(acceptance_policy(&case), combined).is_ok());
}

#[test]
fn artifact_cannot_transfer_to_a_different_case_or_subject() {
    let original = bundle();
    let original_case = case(&original);
    let bundle = bind_bundle_to_case(original, &original_case);
    let policy = PhalaValidationPolicy::for_bundle(&bundle, 600);
    let anchor = anchor(&bundle);
    let mut transferred = original_case;
    transferred.subject = subject("different-agent");

    let attestation = PhalaArtifactAttestationLane::new(anchor, bundle, policy)
        .evaluate_with_quote_verifier(&transferred, &FixtureQuoteVerifier);

    assert_eq!(attestation.maturity, Maturity::Stub);
    assert!(attestation.guarantees.is_empty());
}

#[test]
fn artifact_without_authenticated_quote_is_not_validated() {
    let bundle = bundle();
    let policy = PhalaValidationPolicy::for_bundle(&bundle, 600);

    assert!(matches!(
        validate_phala_artifact(&bundle, &policy, bundle.observed_timestamp),
        Err(PhalaValidationError::QuoteUnverified)
    ));
}

#[test]
fn quote_backend_must_return_bound_report_data_and_a_trust_root() {
    let bundle = bundle();
    let policy = PhalaValidationPolicy::for_bundle(&bundle, 600);

    assert!(matches!(
        validate_phala_artifact_with_quote_verifier(
            &bundle,
            &policy,
            bundle.observed_timestamp,
            &UnboundQuoteVerifier,
        ),
        Err(PhalaValidationError::QuoteUnverified)
    ));
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
    let validated = validate_fixture(&bundle, &policy, bundle.observed_timestamp)
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

#[test]
fn artifact_parser_and_hex_validation_fail_closed() {
    assert!(matches!(
        parse_phala_artifact("{not json"),
        Err(PhalaValidationError::InvalidJson(_))
    ));

    let bundle = bundle();
    let policy = PhalaValidationPolicy::for_bundle(&bundle, 600);
    let mut bad_quote = bundle.clone();
    bad_quote.quote_hex = "not-hex".to_owned();
    assert!(matches!(
        validate_phala_artifact(&bad_quote, &policy, bundle.observed_timestamp),
        Err(PhalaValidationError::InvalidHex { field, .. }) if field == "quote_hex"
    ));

    let mut bad_case_hash = bundle.clone();
    bad_case_hash.case_hash_hex.pop();
    assert!(matches!(
        validate_phala_artifact(&bad_case_hash, &policy, bundle.observed_timestamp),
        Err(PhalaValidationError::InvalidHexLength { field, .. }) if field == "case_hash_hex"
    ));
}

#[test]
fn freshness_and_managed_verifier_rejections_are_explicit() {
    let bundle = bundle();
    let policy = PhalaValidationPolicy::for_bundle(&bundle, 600);

    assert!(matches!(
        validate_phala_artifact(&bundle, &policy, bundle.observed_timestamp - 1),
        Err(PhalaValidationError::ObservationInFuture { .. })
    ));

    let mut wrong_kind = bundle.clone();
    wrong_kind.verifier_mode.kind = "other-managed-verifier".to_owned();
    assert!(matches!(
        validate_phala_artifact(&wrong_kind, &policy, bundle.observed_timestamp),
        Err(PhalaValidationError::ManagedVerifierUntrusted(value))
            if value == "other-managed-verifier"
    ));

    let mut wrong_status = bundle.clone();
    wrong_status.verifier_mode.verification_status = "OutOfDate".to_owned();
    assert!(matches!(
        validate_phala_artifact(&wrong_status, &policy, bundle.observed_timestamp),
        Err(PhalaValidationError::ManagedVerifierUntrusted(value)) if value == "OutOfDate"
    ));
}

#[test]
fn event_payload_docker_digest_and_rtmr_shape_rejections_are_explicit() {
    let bundle = bundle();
    let policy = PhalaValidationPolicy::for_bundle(&bundle, 600);

    let mut missing_event = bundle.clone();
    missing_event
        .rtmr3_event_log
        .retain(|event| event.event != "compose-hash");
    assert!(matches!(
        validate_phala_artifact(&missing_event, &policy, bundle.observed_timestamp),
        Err(PhalaValidationError::MissingEvent(event)) if event == "compose-hash"
    ));

    let mut bad_event_payload = bundle.clone();
    let app_event = bad_event_payload
        .rtmr3_event_log
        .iter_mut()
        .find(|event| event.event == "app-id")
        .expect("fixture has app-id event");
    mutate_first_hex_char(&mut app_event.event_payload);
    assert!(matches!(
        validate_phala_artifact(&bad_event_payload, &policy, bundle.observed_timestamp),
        Err(PhalaValidationError::EventPayloadMismatch { event, .. }) if event == "app-id"
    ));

    let mut bad_docker_digest = bundle.clone();
    bad_docker_digest.docker_image_digests[0] = "sha512:not-supported".to_owned();
    assert!(matches!(
        validate_phala_artifact(&bad_docker_digest, &policy, bundle.observed_timestamp),
        Err(PhalaValidationError::InvalidHex { field, .. }) if field == "docker_image_digest"
    ));

    let mut wrong_imr = bundle.clone();
    wrong_imr.rtmr3_event_log[0].imr = 2;
    assert!(matches!(
        validate_phala_artifact(&wrong_imr, &policy, bundle.observed_timestamp),
        Err(PhalaValidationError::RtmrReplayMismatch { actual, expected })
            if actual == "2" && expected == "3"
    ));
}
