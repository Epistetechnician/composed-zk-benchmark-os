use hsai_agent_case::{
    ActionId, AgentCase, EvidenceLane, MemoryRoot, ModelId, OracleContract, Verdict,
};
use hsai_attestation::{
    report_data_binding, AttestationInput, AttestationLane, ManagedTokenVerifier, Token,
};
use hsai_claim_envelope::{
    conjoin, AcceptancePolicy, ClaimEnvelope, LaneId, Maturity, Predicate, PropertyKind, Rejection,
    SubjectId, TimeWindow, TrustRootClass,
};
use hsai_distinct_agent::{
    distinctness, Anchor, AnchorBundle, DistinctAgentLane, IdentityRegistry, RegisterError,
};
use hsai_economy::{Credits, DemurragePolicy, Economy, EconomyError, FloorPlusDemandPeg};
use hsai_membrane::{AutonomyLevel, ExternalAmount, Membrane, MembraneError};
use std::collections::BTreeSet;

fn subject(id: &str) -> SubjectId {
    SubjectId(id.to_owned())
}

fn phase1_anchor() -> Anchor {
    Anchor::HardwareAttested {
        vendor: "phala-dstack-tdx".to_owned(),
        device: "compose-agent-case-emitter-v1".to_owned(),
    }
}

fn phase1_case(subject_id: &str) -> AgentCase {
    let subject = subject(subject_id);
    AgentCase {
        action: ActionId("admit-work-claim".to_owned()),
        subject: subject.clone(),
        claimed_model: ModelId("agent-case-emitter-v1".to_owned()),
        memory_root: MemoryRoot([3; 32]),
        observed_at: 150,
        oracle: OracleContract {
            expected: Verdict::Accept,
            target_guarantees: BTreeSet::from([distinctness(&subject)]),
            excluded: BTreeSet::new(),
        },
    }
}

fn case_hash(case: &AgentCase) -> Vec<u8> {
    let mut bytes = Vec::new();
    bytes.extend(case.action.0.as_bytes());
    bytes.extend(case.subject.0.as_bytes());
    bytes.extend(case.memory_root.0);
    bytes
}

fn phase1_input(case: &AgentCase) -> AttestationInput {
    let anchor = phase1_anchor();
    let nonce = 42;
    let report_data = report_data_binding(b"agent-pubkey-v1", nonce, &case_hash(case));
    let measurements = b"compose-hash:agent-case-emitter-v1".to_vec();

    AttestationInput {
        anchor: anchor.clone(),
        token: Token {
            signed_jwt: None,
            anchor_id: anchor.anchor_id(),
            nonce,
            report_data: report_data.clone(),
            measurements: measurements.clone(),
            not_before: 100,
            not_after: 300,
        },
        expected_nonce: nonce,
        expected_report_data: report_data,
        expected_measurements: measurements,
    }
}

fn closed_distinct_env(case: &AgentCase, input: AttestationInput) -> ClaimEnvelope {
    let distinct =
        DistinctAgentLane::new(AnchorBundle(BTreeSet::from([input.anchor.clone()]))).evaluate(case);
    let attestation = AttestationLane::new(ManagedTokenVerifier, vec![input]).evaluate(case);
    conjoin(distinct, attestation)
}

fn distinct_policy(subject: &SubjectId) -> AcceptancePolicy {
    AcceptancePolicy {
        require: BTreeSet::from([distinctness(subject)]),
        min_maturity: Maturity::Attested,
        forbid_roots: BTreeSet::<TrustRootClass>::new(),
        require_closed: true,
        at: 150,
    }
}

fn forbidden_hardware_policy(subject: &SubjectId) -> AcceptancePolicy {
    AcceptancePolicy {
        forbid_roots: BTreeSet::from([TrustRootClass::HardwareVendor]),
        ..distinct_policy(subject)
    }
}

fn work_predicate(worker: &SubjectId) -> Predicate {
    Predicate {
        subject: worker.clone(),
        property: PropertyKind::PolicyCompliance,
    }
}

fn admitted_work_env(worker: &SubjectId) -> ClaimEnvelope {
    ClaimEnvelope::new(
        BTreeSet::from([work_predicate(worker)]),
        BTreeSet::new(),
        BTreeSet::new(),
        Maturity::Local,
        BTreeSet::new(),
        TimeWindow::all(),
        LaneId::Named("phase1-local-work".to_owned()),
    )
}

fn work_policy(worker: &SubjectId) -> AcceptancePolicy {
    AcceptancePolicy {
        require: BTreeSet::from([work_predicate(worker)]),
        min_maturity: Maturity::Local,
        forbid_roots: BTreeSet::<TrustRootClass>::new(),
        require_closed: true,
        at: 150,
    }
}

fn economy_policy() -> DemurragePolicy {
    DemurragePolicy {
        peg: FloorPlusDemandPeg {
            floor: 10,
            demand_multiplier: 2,
        },
        rate: 0,
    }
}

#[test]
fn phase1_valid_attestation_registers_earns_and_freeze_blocks_membrane() {
    let case = phase1_case("agentA");
    let env = closed_distinct_env(&case, phase1_input(&case));
    assert!(env.assumptions.is_empty());
    assert_eq!(env.maturity, Maturity::Attested);

    let mut registry = IdentityRegistry::new();
    registry
        .register(case.subject.clone(), env, distinct_policy(&case.subject))
        .expect("accepted phase-1 attestation should register");

    let mut economy = Economy::new(economy_policy());
    assert_eq!(
        economy.earn(
            &registry,
            case.subject.clone(),
            admitted_work_env(&case.subject),
            work_policy(&case.subject),
            3,
        ),
        Ok(Credits(16))
    );
    assert_eq!(economy.balance(&case.subject), Credits(16));

    let mut membrane = Membrane::new(10);
    assert_eq!(
        membrane.convert_out(
            &mut economy,
            &registry,
            case.subject.clone(),
            Credits(6),
            AutonomyLevel::Autonomous,
        ),
        Ok(ExternalAmount(6))
    );
    assert_eq!(economy.balance(&case.subject), Credits(10));

    economy.freeze(case.subject.clone());
    let economy_before = economy.clone();
    let membrane_before = membrane.clone();
    assert_eq!(
        membrane.convert_out(
            &mut economy,
            &registry,
            case.subject.clone(),
            Credits(1),
            AutonomyLevel::Autonomous,
        ),
        Err(MembraneError::Economy(EconomyError::Frozen(
            case.subject.clone()
        )))
    );
    assert_eq!(economy, economy_before);
    assert_eq!(membrane, membrane_before);
}

#[test]
fn phase1_report_data_mismatch_leaves_distinctness_inadmissible() {
    let case = phase1_case("agentA");
    let mut input = phase1_input(&case);
    input.expected_report_data = report_data_binding(b"agent-pubkey-v2", 42, &case_hash(&case));

    let env = closed_distinct_env(&case, input);
    let anchor_assumption = phase1_anchor().validity_assumption(&case.subject);
    assert!(env.assumptions.contains(&anchor_assumption));

    let mut registry = IdentityRegistry::new();
    assert_eq!(
        registry.register(case.subject.clone(), env, distinct_policy(&case.subject)),
        Err(RegisterError::NotAdmitted(vec![
            Rejection::InsufficientMaturity {
                actual: Maturity::Stub,
                required: Maturity::Attested,
            },
            Rejection::OpenAssumption(anchor_assumption),
        ]))
    );
}

#[test]
fn phase1_reused_anchor_is_rejected_after_first_registration() {
    let case_a = phase1_case("agentA");
    let mut registry = IdentityRegistry::new();
    registry
        .register(
            case_a.subject.clone(),
            closed_distinct_env(&case_a, phase1_input(&case_a)),
            distinct_policy(&case_a.subject),
        )
        .expect("first identity should register");

    let case_b = phase1_case("agentB");
    assert_eq!(
        registry.register(
            case_b.subject.clone(),
            closed_distinct_env(&case_b, phase1_input(&case_b)),
            distinct_policy(&case_b.subject),
        ),
        Err(RegisterError::SybilAnchorReuse(
            phase1_anchor().trust_root()
        ))
    );
}

#[test]
fn phase1_forbidden_hardware_root_rejects_without_registration() {
    let case = phase1_case("agentA");
    let env = closed_distinct_env(&case, phase1_input(&case));
    let root = phase1_anchor().trust_root();

    let mut registry = IdentityRegistry::new();
    assert_eq!(
        registry.register(
            case.subject.clone(),
            env,
            forbidden_hardware_policy(&case.subject),
        ),
        Err(RegisterError::NotAdmitted(vec![
            Rejection::ForbiddenTrustRoot(root)
        ]))
    );
    assert!(registry.identity(&case.subject).is_none());
}
