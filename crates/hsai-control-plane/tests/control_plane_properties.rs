use hsai_control_plane::*;
use proptest::prelude::*;

fn capability_strategy() -> impl Strategy<Value = Capability> {
    prop_oneof![
        Just(Capability::Read),
        Just(Capability::Write),
        Just(Capability::Network),
        Just(Capability::Secrets),
        Just(Capability::Spend),
        Just(Capability::Replication),
        Just(Capability::CodeExecution),
        Just(Capability::SelfModification),
    ]
}

proptest! {
    #[test]
    fn replay_guard_accepts_only_the_exact_next_nonce(first in any::<u64>()) {
        let guard = ReplayGuard::new(first);
        let next = guard.consume(first);
        if first == u64::MAX {
            prop_assert_eq!(next, Err(ReplayBlocker::NonceExhausted));
        } else {
            prop_assert_eq!(next, Ok(ReplayGuard::new(first + 1)));
        }

        let wrong = first.wrapping_add(1);
        prop_assert_eq!(
            guard.consume(wrong),
            Err(ReplayBlocker::UnexpectedNonce {
                expected: first,
                received: wrong,
            })
        );
        prop_assert_eq!(guard.next_nonce(), first);
    }

    #[test]
    fn capability_sets_are_explicitly_monotone(
        requested in prop::collection::btree_set(capability_strategy(), 1..=8),
        denied in capability_strategy(),
    ) {
        let requested = CapabilitySet::new(requested.iter().copied());
        prop_assert!(requested.is_subset_of(&requested));

        if !requested.contains(denied) {
            let expanded = CapabilitySet::new(
                requested.iter().copied().chain(std::iter::once(denied)),
            );
            prop_assert!(!expanded.is_subset_of(&requested));
        }
    }

    #[test]
    fn proposal_and_terminal_states_never_begin_execution(
        state in prop_oneof![
            Just(ControlState::Proposal),
            Just(ControlState::Quarantined),
            Just(ControlState::Rejected),
            Just(ControlState::Completed),
            Just(ControlState::RolledBack),
            Just(ControlState::Frozen),
            Just(ControlState::Shutdown),
        ],
    ) {
        prop_assert!(transition_state(state, StateTransition::BeginExecution).is_err());
    }

    #[test]
    fn successful_market_matches_are_never_authoritative(
        price in 0u64..100,
        deadline in 1u64..200,
    ) {
        let job = ComputeJobRequest {
            job_id: "job-property".to_owned(),
            program_digest: Digest::from_text("program-property"),
            input_commitment: Digest::from_text("input-property"),
            route: ComputeRoute::ProofMarket,
            required_capabilities: CapabilitySet::new([Capability::CodeExecution]),
            minimum_confidentiality: ConfidentialityTier::TransportEncrypted,
            minimum_verifiability: VerifiabilityTier::ZkProof,
            max_price_units: price,
            deadline,
        };
        let offer = ComputeOffer {
            offer_id: "offer-property".to_owned(),
            job_id: job.job_id.clone(),
            provider_id: "provider-property".to_owned(),
            offered_capabilities: CapabilitySet::new([Capability::CodeExecution]),
            confidentiality: ConfidentialityTier::TransportEncrypted,
            verifiability: VerifiabilityTier::ZkProof,
            price_units: price,
            completion_deadline: deadline,
            result_digest: Some(Digest::from_text("result-property")),
            proof_digest: Some(Digest::from_text("proof-property")),
        };

        let matched = match_compute_job(&job, &offer).expect("generated match is valid");
        prop_assert!(!matched.settlement.executed);
        prop_assert!(!matched.proof_verified);
        prop_assert!(!matched.authority_granted);
        prop_assert_eq!(matched.settlement.amount_units, price);
    }
}
