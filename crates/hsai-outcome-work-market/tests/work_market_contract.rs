use hsai_control_plane::{Capability, CapabilitySet, Digest};
use hsai_outcome_work_market::{
    build_payout_intent, create_outcome_market, open_outcome_market, resolve_work,
    validate_market_observation, ContractBlocker, EvidenceStatus, MarketObservation, MarketSource,
    MarketState, PaymentRail, PayoutStatus, WorkEvidencePacket, WorkJob, WorkOutcome,
    PRICE_SCALE_MICROS,
};
use std::collections::BTreeSet;

fn digest(label: &str) -> Digest {
    Digest::from_text(label)
}

fn job() -> WorkJob {
    WorkJob {
        job_id: "job-1".to_owned(),
        buyer_id: "buyer-1".to_owned(),
        objective_digest: digest("objective"),
        program_digest: digest("program"),
        input_commitment: digest("input"),
        output_schema_digest: digest("output-schema"),
        acceptance_policy_digest: digest("acceptance-policy"),
        assessment_set_commitment: digest("assessment-set"),
        resource_budget_units: 100,
        deadline: 200,
        grace_period: 20,
        required_capabilities: CapabilitySet::new([Capability::CodeExecution]),
        max_price_units: 100,
        base_bounty_units: 40,
        payment_rails: BTreeSet::from([PaymentRail::Stripe, PaymentRail::Tempo]),
        claim_ceiling: "LocalVerifiedWorkOutcome".to_owned(),
    }
}

fn accepted_evidence(job: &WorkJob) -> WorkEvidencePacket {
    WorkEvidencePacket {
        evidence_id: "evidence-1".to_owned(),
        job_digest: job.digest(),
        provider_id: "provider-1".to_owned(),
        artifact_digest: digest("artifact"),
        evaluator_id: "evaluator-1".to_owned(),
        evaluator_digest: digest("evaluator"),
        assessment_set_commitment: job.assessment_set_commitment.clone(),
        status: EvidenceStatus::Accepted,
        submitted_at: 180,
        accepted_at: Some(190),
        independently_validated: true,
        contradictory: false,
    }
}

#[test]
fn accepted_work_resolves_and_creates_pending_payout() {
    let job = job();
    let market = create_outcome_market(&job, "market-1", MarketSource::Offchain, 100, 150)
        .expect("valid job creates a market");
    assert_eq!(market.job_digest, job.digest());

    let evidence = accepted_evidence(&job);
    let resolution = resolve_work(&job, &evidence, 210).expect("accepted evidence resolves");
    assert_eq!(resolution.outcome, WorkOutcome::Yes);
    assert!(resolution.payout_eligible);
    assert!(!resolution.authority_granted);

    let payout = build_payout_intent(
        &job,
        &evidence,
        &resolution,
        "payout-1",
        PaymentRail::Tempo,
        "job-1:payout:v1",
    )
    .expect("accepted work creates a payout intent");
    assert_eq!(payout.amount_units, 40);
    assert_eq!(payout.status, PayoutStatus::PendingAuthorization);
    assert!(!payout.authority_granted);
}

#[test]
fn rejected_and_unknown_work_cannot_create_payout_eligibility() {
    let job = job();
    for status in [EvidenceStatus::Rejected, EvidenceStatus::Unknown] {
        let mut evidence = accepted_evidence(&job);
        evidence.status = status;
        evidence.accepted_at = None;
        evidence.independently_validated = status == EvidenceStatus::Rejected;
        let resolution =
            resolve_work(&job, &evidence, 210).expect("non-accepted evidence resolves");
        assert_ne!(resolution.outcome, WorkOutcome::Yes);
        assert!(!resolution.payout_eligible);
        assert!(build_payout_intent(
            &job,
            &evidence,
            &resolution,
            "payout-1",
            PaymentRail::Tempo,
            "job-1:payout:v1",
        )
        .is_err());
    }

    let mut unvalidated_rejection = accepted_evidence(&job);
    unvalidated_rejection.status = EvidenceStatus::Rejected;
    unvalidated_rejection.accepted_at = None;
    unvalidated_rejection.independently_validated = false;
    let blockers = resolve_work(&job, &unvalidated_rejection, 210)
        .expect_err("unvalidated rejection cannot resolve");
    assert!(blockers.contains(&ContractBlocker::EvidenceNotIndependent));
}

#[test]
fn observations_require_open_market_binding_and_monotonic_price_data() {
    let job = job();
    let frozen =
        create_outcome_market(&job, "market-1", MarketSource::HyperliquidTestnet, 100, 150)
            .expect("market creates");
    let opened = open_outcome_market(&frozen, 110).expect("market opens");
    let valid = MarketObservation {
        market_id: "market-1".to_owned(),
        job_digest: job.digest(),
        source: MarketSource::HyperliquidTestnet,
        sequence: 1,
        observed_at: 111,
        yes_price_micros: 720_000,
        liquidity_units: 100,
    };
    assert!(validate_market_observation(&opened, &valid, None).is_ok());

    let mut forged = valid.clone();
    forged.yes_price_micros = PRICE_SCALE_MICROS + 1;
    forged.sequence = 1;
    let blockers = validate_market_observation(&opened, &forged, Some(1))
        .expect_err("replayed out-of-range observation rejects");
    assert!(blockers.contains(&ContractBlocker::PriceOutOfRange));
    assert!(blockers.contains(&ContractBlocker::ObservationSequenceReplay));

    let mut wrong_source = valid;
    wrong_source.source = MarketSource::Offchain;
    let blockers = validate_market_observation(&opened, &wrong_source, None)
        .expect_err("source drift rejects");
    assert!(blockers.contains(&ContractBlocker::ObservationSourceMismatch));
}

#[test]
fn closed_market_produces_replayable_advisory_twap() {
    let job = job();
    let frozen = create_outcome_market(&job, "market-1", MarketSource::Offchain, 100, 150)
        .expect("market creates");
    let opened = open_outcome_market(&frozen, 110).expect("market opens");
    let first = MarketObservation {
        market_id: "market-1".to_owned(),
        job_digest: job.digest(),
        source: MarketSource::Offchain,
        sequence: 1,
        observed_at: 110,
        yes_price_micros: 600_000,
        liquidity_units: 100,
    };
    let second = MarketObservation {
        observed_at: 130,
        yes_price_micros: 800_000,
        sequence: 2,
        ..first.clone()
    };
    let state = MarketState::new(&opened)
        .record(&opened, first)
        .expect("first observation records")
        .record(&opened, second)
        .expect("second observation records");
    let signal = state
        .close_signal(&opened, 150)
        .expect("closed market produces signal");
    assert_eq!(signal.yes_price_micros, 700_000);
    assert_eq!(signal.observation_count, 2);
    assert_eq!(signal.market_digest, opened.digest());
}
