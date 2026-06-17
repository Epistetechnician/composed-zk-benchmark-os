use hsai_agent_anchor_registry::{
    anchor_acceptance_policy, anchor_tier_predicate, AgentAnchorRegistry, AgentAnchorSet,
    AnchorTier, PHASE_4_CLAIM_BOUNDARY,
};
use hsai_agent_case::EvidenceLane;
use hsai_agent_case::{ActionId, AgentCase, MemoryRoot, ModelId, OracleContract, Verdict};
use hsai_attestation_phala::{
    parse_phala_artifact, PhalaArtifactAttestationLane, PhalaArtifactBundle, PhalaValidationPolicy,
};
use hsai_claim_envelope::{
    admits, conjoin, Maturity, Predicate, PropertyKind, SubjectId, TrustRoot, VendorId,
};
use hsai_distinct_agent::{distinctness, Anchor, AnchorBundle, DistinctAgentLane};
use std::collections::BTreeSet;

const REAL_PHALA_FIXTURE: &str = include_str!(
    "../../hsai-attestation-phala/tests/fixtures/phala_hsai_owned_real_2026_06_16.json"
);

fn bundle() -> PhalaArtifactBundle {
    parse_phala_artifact(REAL_PHALA_FIXTURE).expect("real HSAI-owned fixture must parse")
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
        subject: subject("hsai-capture-agent-2026-06-16"),
        claimed_model: ModelId("hsai-capture-emitter-2026-06-16".to_owned()),
        memory_root: MemoryRoot([7; 32]),
        observed_at: bundle.observed_timestamp,
        oracle: OracleContract {
            expected: Verdict::Accept,
            target_guarantees: BTreeSet::from([distinctness(&subject(
                "hsai-capture-agent-2026-06-16",
            ))]),
            excluded: BTreeSet::from([semantic_correctness_action1()]),
        },
    }
}

fn phala_anchor(bundle: &PhalaArtifactBundle) -> Anchor {
    Anchor::HardwareAttested {
        vendor: "phala-dstack".to_owned(),
        device: bundle.app_id.clone(),
    }
}

fn root(id: &str) -> TrustRoot {
    TrustRoot::HardwareVendor(VendorId(id.to_owned()))
}

#[test]
fn accepted_real_phala_artifact_authorizes_phase4_registry_start() {
    let bundle = bundle();
    let case = case(&bundle);
    let anchor = phala_anchor(&bundle);
    let policy = PhalaValidationPolicy::for_bundle(&bundle, 600);

    let distinct =
        DistinctAgentLane::new(AnchorBundle(BTreeSet::from([anchor.clone()]))).evaluate(&case);
    let attestation =
        PhalaArtifactAttestationLane::new(anchor.clone(), bundle.clone(), policy).evaluate(&case);
    let admitted = conjoin(distinct, attestation);
    let phase4_policy =
        anchor_acceptance_policy(&case.subject, case.observed_at, Maturity::Attested);

    assert!(admits(phase4_policy.clone(), admitted.clone()).is_ok());
    assert_eq!(admitted.maturity, Maturity::Attested);
    assert!(admitted.assumptions.is_empty());
    assert!(admitted
        .trust_roots
        .contains(&root("managed:phala-trust-center")));
    assert!(admitted
        .trust_roots
        .contains(&root("managed:intel-trust-authority")));

    let mut registry = AgentAnchorRegistry::new();
    let registered = registry
        .register(
            AgentAnchorSet {
                subject: case.subject.clone(),
                runtime_anchors: BTreeSet::from([anchor]),
                ..AgentAnchorSet::default()
            },
            admitted,
            phase4_policy,
        )
        .expect("accepted real HSAI-owned Phala artifact should authorize Phase 4 registry registration");

    assert_eq!(registered.tier, AnchorTier::HardwareAnchoredAgent);
    assert_eq!(registered.envelope.maturity, Maturity::Attested);
    assert!(registered
        .envelope
        .guarantees
        .contains(&anchor_tier_predicate(
            &case.subject,
            &AnchorTier::HardwareAnchoredAgent
        )));
    assert!(registered.envelope.excludes.contains(&Predicate {
        subject: case.subject.clone(),
        property: PropertyKind::Custom(
            "does-not-prove:global-software-agent-uniqueness".to_owned(),
        ),
    }));
    assert!(PHASE_4_CLAIM_BOUNDARY.contains("not global software-agent uniqueness"));
    assert_eq!(registry.active_count(), 1);
    assert_eq!(registry.registered_count(), 1);
    assert!(registry.validate_internal_state().is_ok());
}
