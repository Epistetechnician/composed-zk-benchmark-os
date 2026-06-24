//! Pure-data adversarial end-to-end harness over the local HSAI crates.
//!
//! This crate is local regression coverage only. It does not verify managed
//! attestation service signatures, TEE quotes, JWTs, or any live backend.

/// Claim boundary for this harness.
pub const CLAIM_BOUNDARY: &str =
    "pure-data local regression harness; not external attestation evidence or proof";

#[cfg(test)]
mod tests {
    use hsai_agent_admission::{
        accepted_claim_envelope, evaluate_admission, AdmissionClaimBoundary, AdmissionSourceKind,
        AdmissionVerdict, AgentAdmissionCandidate, AgentAdmissionJournal, AgentAdmissionPolicy,
        ArtifactDigest, NonClaimLabel,
    };
    use hsai_agent_anchor_registry::{
        anchor_acceptance_policy, anchor_tier_predicate, AgentAnchorError, AgentAnchorRegistry,
        AgentAnchorSet, AnchorTier, PHASE_4_CLAIM_BOUNDARY,
    };
    use hsai_agent_case::{
        ActionId, AgentCase, EvidenceLane, MemoryRoot, ModelId, OracleContract, Verdict,
    };
    use hsai_attestation::{
        report_data_binding, AttestationInput, AttestationLane, ManagedTokenVerifier, Token,
    };
    use hsai_claim_envelope::{
        admits, conjoin, AcceptancePolicy, ClaimEnvelope, Hash, LaneId, Maturity, Predicate,
        PropertyKind, Rejection, SubjectId, TimeWindow, TrustRootClass,
    };
    use hsai_distinct_agent::{
        distinctness, Anchor, AnchorBundle, DistinctAgentLane, IdentityRegistry, RegisterError,
    };
    use hsai_economy::{Credits, DemurragePolicy, Economy, EconomyError, FloorPlusDemandPeg};
    use hsai_economy_sim::{run, run_with_funding, sweep, FundingRule, PolicyChoice, SimConfig};
    use hsai_membrane::{AutonomyLevel, ExternalAmount, Membrane, MembraneError};
    use proptest::prelude::*;
    use std::collections::BTreeSet;

    const OBSERVED_AT: u64 = 150;
    const GOOD_NONCE: u64 = 7;
    const GOOD_NOT_BEFORE: u64 = 100;
    const GOOD_NOT_AFTER: u64 = 300;

    fn subject(id: &str) -> SubjectId {
        SubjectId(id.to_owned())
    }

    fn harness_subject() -> SubjectId {
        subject("agent-e2e")
    }

    fn harness_anchor() -> Anchor {
        Anchor::HardwareAttested {
            vendor: "harness".to_owned(),
            device: "dev-0".to_owned(),
        }
    }

    fn hardware_anchor(vendor: &str, device: &str) -> Anchor {
        Anchor::HardwareAttested {
            vendor: vendor.to_owned(),
            device: device.to_owned(),
        }
    }

    fn case_for(subject: SubjectId, observed_at: u64) -> AgentCase {
        AgentCase {
            action: ActionId("harness-action".to_owned()),
            subject: subject.clone(),
            claimed_model: ModelId("harness-model".to_owned()),
            memory_root: MemoryRoot([9; 32]),
            observed_at,
            oracle: OracleContract {
                expected: Verdict::Accept,
                target_guarantees: BTreeSet::from([distinctness(&subject)]),
                excluded: BTreeSet::new(),
            },
        }
    }

    fn harness_case() -> AgentCase {
        case_for(harness_subject(), OBSERVED_AT)
    }

    fn case_hash(case: &AgentCase) -> Vec<u8> {
        let mut bytes = Vec::new();
        bytes.extend(case.action.0.as_bytes());
        bytes.extend(case.subject.0.as_bytes());
        bytes.extend(case.claimed_model.0.as_bytes());
        bytes.extend(case.memory_root.0);
        bytes.extend(case.observed_at.to_be_bytes());
        bytes
    }

    fn measurements() -> Vec<u8> {
        vec![1, 2, 3, 4]
    }

    fn attestation_input(case: &AgentCase, anchor: Anchor) -> AttestationInput {
        let report_data =
            report_data_binding(b"harness-agent-pubkey", GOOD_NONCE, &case_hash(case));
        AttestationInput {
            anchor: anchor.clone(),
            token: Token {
                signed_jwt: None,
                anchor_id: anchor.anchor_id(),
                nonce: GOOD_NONCE,
                report_data: report_data.clone(),
                measurements: measurements(),
                not_before: GOOD_NOT_BEFORE,
                not_after: GOOD_NOT_AFTER,
            },
            expected_nonce: GOOD_NONCE,
            expected_report_data: report_data,
            expected_measurements: measurements(),
        }
    }

    fn distinct_lane(anchor: Anchor) -> DistinctAgentLane {
        DistinctAgentLane::new(AnchorBundle(BTreeSet::from([anchor])))
    }

    fn attestation_lane(input: AttestationInput) -> AttestationLane<ManagedTokenVerifier> {
        AttestationLane::new(ManagedTokenVerifier, vec![input])
    }

    fn joined_env(case: &AgentCase, input: AttestationInput) -> ClaimEnvelope {
        let distinct_env = distinct_lane(input.anchor.clone()).evaluate(case);
        let attestation_env = attestation_lane(input).evaluate(case);
        conjoin(distinct_env, attestation_env)
    }

    fn distinct_policy(subject: &SubjectId, at: u64) -> AcceptancePolicy {
        AcceptancePolicy {
            require: BTreeSet::from([distinctness(subject)]),
            min_maturity: Maturity::Attested,
            forbid_roots: BTreeSet::<TrustRootClass>::new(),
            require_closed: true,
            at,
        }
    }

    fn forbidden_root_policy(subject: &SubjectId, at: u64) -> AcceptancePolicy {
        AcceptancePolicy {
            forbid_roots: BTreeSet::from([TrustRootClass::HardwareVendor]),
            ..distinct_policy(subject, at)
        }
    }

    fn work_predicate(worker: &SubjectId) -> Predicate {
        Predicate {
            subject: worker.clone(),
            property: PropertyKind::PolicyCompliance,
        }
    }

    fn work_env(worker: &SubjectId) -> ClaimEnvelope {
        ClaimEnvelope::new(
            BTreeSet::from([work_predicate(worker)]),
            BTreeSet::new(),
            BTreeSet::new(),
            Maturity::Local,
            BTreeSet::new(),
            TimeWindow::all(),
            LaneId::Named("harness-work".to_owned()),
        )
    }

    fn work_policy(worker: &SubjectId) -> AcceptancePolicy {
        AcceptancePolicy {
            require: BTreeSet::from([work_predicate(worker)]),
            min_maturity: Maturity::Local,
            forbid_roots: BTreeSet::<TrustRootClass>::new(),
            require_closed: true,
            at: OBSERVED_AT,
        }
    }

    fn admission_nonclaim(value: &str) -> NonClaimLabel {
        NonClaimLabel(value.to_owned())
    }

    fn admission_artifact(id: &str, byte: u8) -> ArtifactDigest {
        ArtifactDigest {
            id: id.to_owned(),
            sha256: Hash([byte; 32]),
        }
    }

    fn admission_policy() -> AgentAdmissionPolicy {
        AgentAdmissionPolicy::local_default(BTreeSet::from([
            admission_nonclaim("not accepted evidence"),
            admission_nonclaim("not semantic correctness"),
            admission_nonclaim("not proof"),
        ]))
    }

    fn admission_nonclaims() -> BTreeSet<NonClaimLabel> {
        BTreeSet::from([
            admission_nonclaim("not accepted evidence"),
            admission_nonclaim("not semantic correctness"),
            admission_nonclaim("not proof"),
        ])
    }

    fn admission_artifacts() -> BTreeSet<ArtifactDigest> {
        BTreeSet::from([
            admission_artifact("agent-case", 1),
            admission_artifact("claim-envelope", 2),
        ])
    }

    fn admission_candidate(
        id: &str,
        subject: SubjectId,
        envelope: ClaimEnvelope,
    ) -> AgentAdmissionCandidate {
        AgentAdmissionCandidate::from_envelope(
            id,
            subject,
            envelope,
            admission_artifacts(),
            admission_nonclaims(),
        )
    }

    fn accepted_through_admission(
        journal: &mut AgentAdmissionJournal,
        candidate: &AgentAdmissionCandidate,
    ) -> Option<ClaimEnvelope> {
        let policy = admission_policy();
        let decision = evaluate_admission(candidate, &policy);
        let accepted = accepted_claim_envelope(candidate, &policy, &decision).cloned();
        journal
            .append_decision(candidate, &policy, decision)
            .expect("valid admission decision appends to journal");
        accepted
    }

    fn economy_policy() -> DemurragePolicy {
        DemurragePolicy {
            peg: FloorPlusDemandPeg {
                floor: 100,
                demand_multiplier: 0,
            },
            rate: 1,
        }
    }

    fn register_valid(case: &AgentCase) -> IdentityRegistry {
        let input = attestation_input(case, harness_anchor());
        let env = joined_env(case, input);
        let mut registry = IdentityRegistry::new();
        registry
            .register(
                case.subject.clone(),
                env,
                distinct_policy(&case.subject, case.observed_at),
            )
            .expect("valid harness identity registers");
        registry
    }

    fn phase4_policy(subject: &SubjectId, at: u64) -> AcceptancePolicy {
        anchor_acceptance_policy(subject, at, Maturity::Attested)
    }

    fn phase4_anchor_set(subject: SubjectId, anchor: Anchor) -> AgentAnchorSet {
        AgentAnchorSet {
            subject,
            runtime_anchors: BTreeSet::from([anchor]),
            ..AgentAnchorSet::default()
        }
    }

    fn register_phase4(
        registry: &mut AgentAnchorRegistry,
        case: &AgentCase,
        anchor: Anchor,
        env: ClaimEnvelope,
    ) -> Result<AnchorTier, AgentAnchorError> {
        registry
            .register(
                phase4_anchor_set(case.subject.clone(), anchor),
                env,
                phase4_policy(&case.subject, case.observed_at),
            )
            .map(|registered| registered.tier.clone())
    }

    fn open_assumption_rejection(rejections: &[Rejection], case: &AgentCase, anchor: &Anchor) {
        assert!(rejections.contains(&Rejection::OpenAssumption(
            anchor.validity_assumption(&case.subject)
        )));
    }

    #[test]
    fn eh_1_valid_attestation_closes_distinctness() {
        let case = harness_case();
        let anchor = harness_anchor();
        let input = attestation_input(&case, anchor.clone());
        let joined = joined_env(&case, input);

        assert!(joined.assumptions.is_empty());
        assert!(joined.guarantees.contains(&distinctness(&case.subject)));
        assert!(joined
            .guarantees
            .contains(&anchor.validity_assumption(&case.subject)));
        assert_eq!(joined.maturity, Maturity::Attested);
        assert_eq!(
            admits(
                distinct_policy(&case.subject, case.observed_at),
                joined.clone()
            ),
            Ok(())
        );

        let mut registry = IdentityRegistry::new();
        assert!(registry
            .register(
                case.subject.clone(),
                joined,
                distinct_policy(&case.subject, case.observed_at),
            )
            .is_ok());
    }

    #[test]
    fn eh_2_nonce_mismatch_keeps_distinctness_inadmissible() {
        let case = harness_case();
        let anchor = harness_anchor();
        let mut input = attestation_input(&case, anchor.clone());
        input.expected_nonce = GOOD_NONCE + 1;

        let attestation = attestation_lane(input.clone()).evaluate(&case);
        assert_eq!(attestation.maturity, Maturity::Stub);

        let joined = joined_env(&case, input);
        assert!(joined
            .assumptions
            .contains(&anchor.validity_assumption(&case.subject)));
        let rejected = admits(
            distinct_policy(&case.subject, case.observed_at),
            joined.clone(),
        )
        .expect_err("nonce mismatch is inadmissible");
        open_assumption_rejection(&rejected, &case, &anchor);

        let mut registry = IdentityRegistry::new();
        assert!(registry
            .register(
                case.subject.clone(),
                joined,
                distinct_policy(&case.subject, case.observed_at),
            )
            .is_err());
    }

    #[test]
    fn eh_3_measurement_mismatch_keeps_distinctness_inadmissible() {
        let case = harness_case();
        let anchor = harness_anchor();
        let mut input = attestation_input(&case, anchor.clone());
        input.expected_measurements = vec![9, 9, 9];

        let attestation = attestation_lane(input.clone()).evaluate(&case);
        assert_eq!(attestation.maturity, Maturity::Stub);
        let joined = joined_env(&case, input);
        let rejected = admits(
            distinct_policy(&case.subject, case.observed_at),
            joined.clone(),
        )
        .expect_err("measurement mismatch is inadmissible");
        open_assumption_rejection(&rejected, &case, &anchor);

        let mut registry = IdentityRegistry::new();
        assert!(registry
            .register(
                case.subject.clone(),
                joined,
                distinct_policy(&case.subject, case.observed_at),
            )
            .is_err());
    }

    #[test]
    fn eh_4_expired_attestation_keeps_distinctness_inadmissible() {
        let case = case_for(harness_subject(), GOOD_NOT_AFTER + 1);
        let anchor = harness_anchor();
        let input = attestation_input(&case, anchor.clone());

        let attestation = attestation_lane(input.clone()).evaluate(&case);
        assert_eq!(attestation.maturity, Maturity::Stub);
        let joined = joined_env(&case, input);
        let rejected = admits(
            distinct_policy(&case.subject, case.observed_at),
            joined.clone(),
        )
        .expect_err("expired token is inadmissible");
        open_assumption_rejection(&rejected, &case, &anchor);

        let mut registry = IdentityRegistry::new();
        assert!(registry
            .register(
                case.subject.clone(),
                joined,
                distinct_policy(&case.subject, case.observed_at),
            )
            .is_err());
    }

    #[test]
    fn eh_5_anchor_reuse_is_rejected() {
        let case_a = case_for(subject("agent-a"), OBSERVED_AT);
        let anchor = harness_anchor();
        let mut registry = IdentityRegistry::new();
        registry
            .register(
                case_a.subject.clone(),
                joined_env(&case_a, attestation_input(&case_a, anchor.clone())),
                distinct_policy(&case_a.subject, case_a.observed_at),
            )
            .expect("first registration succeeds");

        let case_b = case_for(subject("agent-b"), OBSERVED_AT);
        assert_eq!(
            registry.register(
                case_b.subject.clone(),
                joined_env(&case_b, attestation_input(&case_b, anchor.clone())),
                distinct_policy(&case_b.subject, case_b.observed_at),
            ),
            Err(RegisterError::SybilAnchorReuse(anchor.trust_root()))
        );
    }

    #[test]
    fn eh_6_unregistered_worker_cannot_earn() {
        let registry = IdentityRegistry::new();
        let worker = harness_subject();
        let mut economy = Economy::new(economy_policy());

        assert_eq!(
            economy.earn(
                &registry,
                worker.clone(),
                work_env(&worker),
                work_policy(&worker),
                0,
            ),
            Err(EconomyError::NotRegistered(worker))
        );
    }

    #[test]
    fn eh_7_registered_worker_can_earn() {
        let case = harness_case();
        let registry = register_valid(&case);
        let mut economy = Economy::new(economy_policy());
        let before = economy.total_credits();

        let earned = economy
            .earn(
                &registry,
                case.subject.clone(),
                work_env(&case.subject),
                work_policy(&case.subject),
                0,
            )
            .expect("registered admitted work earns");

        assert!(earned.0 > 0);
        assert_eq!(economy.balance(&case.subject), earned);
        assert_eq!(economy.total_credits(), Credits(before.0 + earned.0));
    }

    #[test]
    fn eh_8_frozen_worker_cannot_cross_membrane() {
        let case = harness_case();
        let registry = register_valid(&case);
        let mut economy = Economy::new(economy_policy());
        economy
            .earn(
                &registry,
                case.subject.clone(),
                work_env(&case.subject),
                work_policy(&case.subject),
                0,
            )
            .expect("earn gives positive balance");

        economy.freeze(case.subject.clone());
        let economy_before = economy.clone();
        let mut membrane = Membrane::new(10);
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

        assert_eq!(
            membrane.convert_in(
                &mut economy,
                &registry,
                case.subject.clone(),
                ExternalAmount(1),
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
    fn eh_9_forbidden_hardware_trust_root_is_rejected() {
        let case = harness_case();
        let env = joined_env(&case, attestation_input(&case, harness_anchor()));
        let rejected = admits(
            forbidden_root_policy(&case.subject, case.observed_at),
            env.clone(),
        )
        .expect_err("hardware root is forbidden");
        assert!(matches!(
            rejected.as_slice(),
            [Rejection::ForbiddenTrustRoot(_)]
        ));

        let mut registry = IdentityRegistry::new();
        assert!(registry
            .register(
                case.subject.clone(),
                env,
                forbidden_root_policy(&case.subject, case.observed_at),
            )
            .is_err());
        assert!(registry.identity(&case.subject).is_none());
    }

    #[test]
    fn eh_10_funding_rule_invariants_still_hold() {
        let base = SimConfig {
            agents: 3,
            ticks: 4,
            seed: 11,
            floor: 2,
            demand_multiplier: 1,
            max_demand: 4,
            earn_prob: 70,
            gift_prob: 20,
            gift_percent: 10,
            policy: PolicyChoice::Demurrage { rate: 1 },
        };
        let policies = [
            PolicyChoice::Demurrage { rate: 1 },
            PolicyChoice::MutualCredit { credit_limit: 20 },
        ];
        let rules = [
            FundingRule::None,
            FundingRule::Even,
            FundingRule::ProportionalToBalance,
        ];
        let seeds = [1, 2];

        for cell in sweep(base, &policies, &rules, &seeds) {
            assert!(cell.terminal_gini <= 1000);
        }
        assert_eq!(run(base), run_with_funding(base, FundingRule::Even));
    }

    #[test]
    fn eh_11_phase4_anchor_registry_accepts_closed_attested_path() {
        let case = harness_case();
        let anchor = harness_anchor();
        let env = joined_env(&case, attestation_input(&case, anchor.clone()));

        let mut registry = AgentAnchorRegistry::new();
        let registered = registry
            .register(
                phase4_anchor_set(case.subject.clone(), anchor),
                env,
                phase4_policy(&case.subject, case.observed_at),
            )
            .expect("closed attested harness envelope should register in Phase 4");

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
                "does-not-prove:global-software-agent-uniqueness".to_owned()
            ),
        }));
        assert!(PHASE_4_CLAIM_BOUNDARY.contains("not global software-agent uniqueness"));
        assert!(registry
            .used_runtime_anchor_ids()
            .contains(&harness_anchor().anchor_id()));
        assert_eq!(registry.active_count(), 1);
        assert_eq!(registry.registered_count(), 1);
        assert!(registry.validate_internal_state().is_ok());
    }

    #[test]
    fn eh_12_phase4_rejects_expired_attestation_without_state_mutation() {
        let case = case_for(harness_subject(), GOOD_NOT_AFTER + 1);
        let anchor = harness_anchor();
        let env = joined_env(&case, attestation_input(&case, anchor.clone()));
        let mut registry = AgentAnchorRegistry::new();

        assert!(matches!(
            register_phase4(&mut registry, &case, anchor, env),
            Err(AgentAnchorError::NotAdmitted(_))
        ));
        assert_eq!(registry.active_count(), 0);
        assert_eq!(registry.registered_count(), 0);
        assert!(registry.validate_internal_state().is_ok());
    }

    #[test]
    fn eh_13_phase4_rejects_reused_runtime_anchor_without_extra_identity() {
        let case_a = case_for(subject("agent-a"), OBSERVED_AT);
        let case_b = case_for(subject("agent-b"), OBSERVED_AT);
        let anchor = harness_anchor();
        let mut registry = AgentAnchorRegistry::new();

        assert_eq!(
            register_phase4(
                &mut registry,
                &case_a,
                anchor.clone(),
                joined_env(&case_a, attestation_input(&case_a, anchor.clone())),
            ),
            Ok(AnchorTier::HardwareAnchoredAgent)
        );

        assert_eq!(
            register_phase4(
                &mut registry,
                &case_b,
                anchor.clone(),
                joined_env(&case_b, attestation_input(&case_b, anchor.clone())),
            ),
            Err(AgentAnchorError::AnchorReuse(anchor.anchor_id()))
        );
        assert_eq!(registry.active_count(), 1);
        assert_eq!(registry.registered_count(), 1);
        assert!(registry.validate_internal_state().is_ok());
    }

    #[test]
    fn eh_14_phase4_rejects_proof_theater_missing_runtime_validity() {
        let case = harness_case();
        let anchor = harness_anchor();
        let env = ClaimEnvelope::new(
            BTreeSet::from([distinctness(&case.subject)]),
            BTreeSet::new(),
            BTreeSet::new(),
            Maturity::Attested,
            BTreeSet::from([anchor.trust_root()]),
            TimeWindow::all(),
            LaneId::Named("proof-theater".to_owned()),
        );
        let mut registry = AgentAnchorRegistry::new();

        assert_eq!(
            register_phase4(&mut registry, &case, anchor.clone(), env),
            Err(AgentAnchorError::MissingRuntimeValidity(anchor.anchor_id()))
        );
        assert_eq!(registry.active_count(), 0);
        assert_eq!(registry.registered_count(), 0);
        assert!(registry.validate_internal_state().is_ok());
    }

    #[test]
    fn eh_15_phase4_rejects_anchor_set_that_does_not_match_attested_runtime() {
        let case = harness_case();
        let attested_anchor = harness_anchor();
        let requested_anchor = hardware_anchor("harness", "dev-1");
        let env = joined_env(&case, attestation_input(&case, attested_anchor.clone()));
        let mut registry = AgentAnchorRegistry::new();

        assert_eq!(
            register_phase4(&mut registry, &case, requested_anchor.clone(), env),
            Err(AgentAnchorError::MissingRuntimeValidity(
                requested_anchor.anchor_id()
            ))
        );
        assert_eq!(registry.active_count(), 0);
        assert_eq!(registry.registered_count(), 0);
        assert!(registry.validate_internal_state().is_ok());
    }

    #[test]
    fn eh_16_phase4_rejects_revoked_runtime_anchor_for_new_identity() {
        let case_a = case_for(subject("agent-a"), OBSERVED_AT);
        let case_b = case_for(subject("agent-b"), OBSERVED_AT);
        let anchor = harness_anchor();
        let mut registry = AgentAnchorRegistry::new();

        assert_eq!(
            register_phase4(
                &mut registry,
                &case_a,
                anchor.clone(),
                joined_env(&case_a, attestation_input(&case_a, anchor.clone())),
            ),
            Ok(AnchorTier::HardwareAnchoredAgent)
        );
        registry
            .revoke_runtime_anchor(&case_a.subject, &anchor, OBSERVED_AT + 1)
            .expect("registered runtime anchor can be revoked");

        assert_eq!(
            register_phase4(
                &mut registry,
                &case_b,
                anchor.clone(),
                joined_env(&case_b, attestation_input(&case_b, anchor.clone())),
            ),
            Err(AgentAnchorError::RevokedAnchor(anchor.anchor_id()))
        );
        assert_eq!(registry.active_count(), 0);
        assert_eq!(registry.registered_count(), 1);
        assert!(registry
            .revoked_runtime_anchor_ids()
            .contains(&anchor.anchor_id()));
        assert!(registry.validate_internal_state().is_ok());
    }

    #[test]
    fn eh_17_phase4_registration_can_be_gated_by_agent_admission() {
        let case = harness_case();
        let anchor = harness_anchor();
        let envelope = joined_env(&case, attestation_input(&case, anchor.clone()));
        let candidate =
            admission_candidate("candidate-e2e-accepted", case.subject.clone(), envelope);
        let mut journal = AgentAdmissionJournal::default();
        let accepted = accepted_through_admission(&mut journal, &candidate)
            .expect("valid local claim-envelope proposal should be admitted");

        let mut registry = AgentAnchorRegistry::new();
        let tier = register_phase4(&mut registry, &case, anchor, accepted)
            .expect("admitted closed attested envelope can reach Phase 4 registry");

        assert_eq!(tier, AnchorTier::HardwareAnchoredAgent);
        assert_eq!(journal.entries.len(), 1);
        assert!(journal.validate().is_empty());
        assert_eq!(
            journal.entries[0].decision.verdict,
            AdmissionVerdict::Accepted
        );
        assert_eq!(registry.active_count(), 1);
        assert!(registry.validate_internal_state().is_ok());
    }

    #[test]
    fn eh_18_rejected_agent_admission_candidate_does_not_export_envelope() {
        let case = harness_case();
        let anchor = harness_anchor();
        let envelope = joined_env(&case, attestation_input(&case, anchor));
        let mut candidate =
            admission_candidate("candidate-e2e-rejected", case.subject.clone(), envelope);
        candidate.provider_direct_authority_requested = true;
        candidate.requested_claim_boundary = AdmissionClaimBoundary::Level2OrHigher;

        let policy = admission_policy();
        let decision = evaluate_admission(&candidate, &policy);
        assert_eq!(decision.verdict, AdmissionVerdict::Rejected);
        assert!(accepted_claim_envelope(&candidate, &policy, &decision).is_none());

        let mut journal = AgentAdmissionJournal::default();
        journal
            .append_decision(&candidate, &policy, decision)
            .expect("rejected decision is still auditable");
        assert!(journal.validate().is_empty());

        let registry = AgentAnchorRegistry::new();
        assert_eq!(registry.active_count(), 0);
        assert_eq!(registry.registered_count(), 0);
    }

    #[test]
    fn eh_19_raw_provider_admission_candidate_is_quarantined_before_economy() {
        let case = harness_case();
        let anchor = harness_anchor();
        let envelope = joined_env(&case, attestation_input(&case, anchor));
        let mut candidate =
            admission_candidate("candidate-e2e-quarantined", case.subject.clone(), envelope);
        candidate.source_kind = AdmissionSourceKind::ProviderResponse;
        candidate.strict_typed = false;

        let policy = admission_policy();
        let decision = evaluate_admission(&candidate, &policy);
        assert_eq!(decision.verdict, AdmissionVerdict::Quarantined);
        assert!(accepted_claim_envelope(&candidate, &policy, &decision).is_none());

        let mut journal = AgentAdmissionJournal::default();
        journal
            .append_decision(&candidate, &policy, decision)
            .expect("quarantined decision is still auditable");
        assert!(journal.validate().is_empty());

        let registry = IdentityRegistry::new();
        let mut economy = Economy::new(economy_policy());
        assert_eq!(
            economy.earn(
                &registry,
                case.subject.clone(),
                work_env(&case.subject),
                work_policy(&case.subject),
                0,
            ),
            Err(EconomyError::NotRegistered(case.subject))
        );
    }

    #[derive(Clone, Copy, Debug)]
    enum Fault {
        Nonce,
        Measurement,
        ReportData,
        Expired,
        AnchorId,
    }

    fn apply_fault(input: &mut AttestationInput, fault: Fault) {
        match fault {
            Fault::Nonce => input.expected_nonce = input.expected_nonce.saturating_add(1),
            Fault::Measurement => input.expected_measurements.push(99),
            Fault::ReportData => input.expected_report_data.push(42),
            Fault::Expired => input.token.not_after = OBSERVED_AT - 1,
            Fault::AnchorId => input.token.anchor_id = "wrong-anchor".to_owned(),
        }
    }

    fn fault_strategy() -> impl Strategy<Value = Fault> {
        prop_oneof![
            Just(Fault::Nonce),
            Just(Fault::Measurement),
            Just(Fault::ReportData),
            Just(Fault::Expired),
            Just(Fault::AnchorId),
        ]
    }

    fn anchor_strategy() -> impl Strategy<Value = Anchor> {
        (0_u8..8, 0_u8..8).prop_map(|(vendor, device)| {
            hardware_anchor(&format!("vendor-{vendor}"), &format!("device-{device}"))
        })
    }

    fn level_strategy() -> impl Strategy<Value = AutonomyLevel> {
        prop_oneof![
            Just(AutonomyLevel::Supervised),
            Just(AutonomyLevel::Bounded),
            Just(AutonomyLevel::Autonomous),
        ]
    }

    proptest! {
        #[test]
        fn ehp_1_single_fault_prevents_registration(fault in fault_strategy()) {
            let case = harness_case();
            let mut input = attestation_input(&case, harness_anchor());
            apply_fault(&mut input, fault);
            let env = joined_env(&case, input);
            prop_assert!(admits(distinct_policy(&case.subject, case.observed_at), env).is_err());
        }

        #[test]
        fn ehp_2_accepted_path_never_exceeds_attested(
            not_before in 0_u64..OBSERVED_AT,
            not_after in OBSERVED_AT..1000_u64,
            measurement in proptest::collection::vec(any::<u8>(), 0..16),
        ) {
            let case = harness_case();
            let mut input = attestation_input(&case, harness_anchor());
            input.token.not_before = not_before;
            input.token.not_after = not_after;
            input.token.measurements = measurement.clone();
            input.expected_measurements = measurement;

            let distinct = distinct_lane(input.anchor.clone()).evaluate(&case);
            let attestation = attestation_lane(input).evaluate(&case);
            prop_assert!(distinct.maturity <= Maturity::Attested);
            prop_assert!(attestation.maturity <= Maturity::Attested);
            let joined = conjoin(distinct, attestation);
            prop_assert!(joined.maturity <= Maturity::Attested);
        }

        #[test]
        fn ehp_3_registry_admits_at_most_one_identity_per_trust_root(anchor in anchor_strategy()) {
            let case_a = case_for(subject("agent-a"), OBSERVED_AT);
            let case_b = case_for(subject("agent-b"), OBSERVED_AT);
            let mut registry = IdentityRegistry::new();

            prop_assert!(registry
                .register(
                    case_a.subject.clone(),
                    joined_env(&case_a, attestation_input(&case_a, anchor.clone())),
                    distinct_policy(&case_a.subject, case_a.observed_at),
                )
                .is_ok());

            prop_assert_eq!(
                registry.register(
                    case_b.subject.clone(),
                    joined_env(&case_b, attestation_input(&case_b, anchor.clone())),
                    distinct_policy(&case_b.subject, case_b.observed_at),
                ),
                Err(RegisterError::SybilAnchorReuse(anchor.trust_root()))
            );
        }

        #[test]
        fn ehp_4_freeze_is_a_hard_membrane_gate(
            balance in 1_i128..500,
            base_cap in 1_u128..100,
            amount_seed in 0_u128..100,
            level in level_strategy(),
        ) {
            let case = harness_case();
            let registry = register_valid(&case);
            let mut economy = Economy::new(economy_policy());
            economy
                .credit_external(&registry, case.subject.clone(), Credits(balance))
                .expect("fixture credit succeeds");
            economy.freeze(case.subject.clone());
            let before_economy = economy.clone();
            let mut membrane = Membrane::new(base_cap);
            let before_membrane = membrane.clone();
            let cap = membrane.cap_for(level);
            let amount = (amount_seed % cap).saturating_add(1) as i128;

            prop_assert_eq!(
                membrane.convert_out(
                    &mut economy,
                    &registry,
                    case.subject.clone(),
                    Credits(amount),
                    level,
                ),
                Err(MembraneError::Economy(EconomyError::Frozen(case.subject.clone())))
            );
            prop_assert_eq!(economy.clone(), before_economy.clone());
            prop_assert_eq!(membrane.clone(), before_membrane.clone());

            prop_assert_eq!(
                membrane.convert_in(
                    &mut economy,
                    &registry,
                    case.subject.clone(),
                    ExternalAmount(amount as u128),
                    level,
                ),
                Err(MembraneError::Economy(EconomyError::Frozen(case.subject.clone())))
            );
            prop_assert_eq!(economy, before_economy);
            prop_assert_eq!(membrane, before_membrane);
        }

        #[test]
        fn ehp_5_phase4_single_faults_leave_registry_empty(fault in fault_strategy()) {
            let case = harness_case();
            let anchor = harness_anchor();
            let mut input = attestation_input(&case, anchor.clone());
            apply_fault(&mut input, fault);
            let env = joined_env(&case, input);
            let mut registry = AgentAnchorRegistry::new();

            prop_assert!(matches!(
                register_phase4(&mut registry, &case, anchor, env),
                Err(AgentAnchorError::NotAdmitted(_))
            ));
            prop_assert_eq!(registry.active_count(), 0);
            prop_assert_eq!(registry.registered_count(), 0);
            prop_assert!(registry.validate_internal_state().is_ok());
        }
    }
}
