use hsai_control_plane::{Capability, CapabilitySet, Digest};
use hsai_outcome_work_market::{
    build_payout_intent, create_outcome_market, open_outcome_market, resolve_work, EvidenceStatus,
    MarketObservation, MarketSource, MarketState, PaymentRail, WorkEvidencePacket, WorkJob,
    WorkOutcome,
};
use hsai_outcome_work_market_checker::{
    check_market_signal, check_market_state, check_outcome_market, check_payout_intent,
    check_resolution,
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
        payment_rails: BTreeSet::from([PaymentRail::Tempo]),
        claim_ceiling: "LocalVerifiedWorkOutcome".to_owned(),
    }
}

fn evidence(job: &WorkJob, status: EvidenceStatus) -> WorkEvidencePacket {
    WorkEvidencePacket {
        evidence_id: "evidence-1".to_owned(),
        job_digest: job.digest(),
        provider_id: "provider-1".to_owned(),
        artifact_digest: digest("artifact"),
        evaluator_id: "evaluator-1".to_owned(),
        evaluator_digest: digest("evaluator"),
        assessment_set_commitment: job.assessment_set_commitment.clone(),
        status,
        submitted_at: 180,
        accepted_at: (status == EvidenceStatus::Accepted).then_some(190),
        independently_validated: status == EvidenceStatus::Accepted,
        contradictory: false,
    }
}

#[test]
fn checker_detects_forged_resolution_and_payout() {
    let job = job();
    let _market = create_outcome_market(&job, "market-1", MarketSource::Offchain, 100, 150)
        .expect("market creates");
    let evidence = evidence(&job, EvidenceStatus::Accepted);
    let resolution = resolve_work(&job, &evidence, 210).expect("resolution creates");
    let payout = build_payout_intent(
        &job,
        &evidence,
        &resolution,
        "payout-1",
        PaymentRail::Tempo,
        "job-1:payout:v1",
    )
    .expect("payout creates");
    assert!(check_resolution(&job, &evidence, &resolution).is_empty());
    assert!(check_payout_intent(&job, &evidence, &resolution, &payout).is_empty());

    let mut forged_resolution = resolution.clone();
    forged_resolution.outcome = WorkOutcome::No;
    assert!(!check_resolution(&job, &evidence, &forged_resolution).is_empty());

    let mut forged_payout = payout;
    forged_payout.authority_granted = true;
    assert!(!check_payout_intent(&job, &evidence, &resolution, &forged_payout).is_empty());
}

#[test]
fn checker_recomputes_market_state_and_signal() {
    let job = job();
    let frozen = create_outcome_market(&job, "market-1", MarketSource::Offchain, 100, 150)
        .expect("market creates");
    let market = open_outcome_market(&frozen, 110).expect("market opens");
    let observation = MarketObservation {
        market_id: "market-1".to_owned(),
        job_digest: job.digest(),
        source: MarketSource::Offchain,
        sequence: 1,
        observed_at: 110,
        yes_price_micros: 700_000,
        liquidity_units: 100,
    };
    let state = MarketState::new(&market)
        .record(&market, observation)
        .expect("observation records");
    let signal = state.close_signal(&market, 150).expect("signal closes");
    assert!(check_market_state(&market, &state).is_empty());
    assert!(check_market_signal(&market, &state, &signal, 150).is_empty());

    let mut forged = signal;
    forged.advisory_only = false;
    assert!(!check_market_signal(&market, &state, &forged, 150).is_empty());
}

#[test]
fn checker_covers_the_complete_local_work_to_payout_path() {
    let job = job();
    let frozen = create_outcome_market(&job, "market-1", MarketSource::Offchain, 100, 150)
        .expect("market creates");
    let market = open_outcome_market(&frozen, 110).expect("market opens");
    let observation = MarketObservation {
        market_id: "market-1".to_owned(),
        job_digest: job.digest(),
        source: MarketSource::Offchain,
        sequence: 1,
        observed_at: 110,
        yes_price_micros: 650_000,
        liquidity_units: 100,
    };
    let state = MarketState::new(&market)
        .record(&market, observation)
        .expect("observation records");
    let signal = state.close_signal(&market, 150).expect("signal closes");
    let evidence = evidence(&job, EvidenceStatus::Accepted);
    let resolution = resolve_work(&job, &evidence, 210).expect("resolution creates");
    let payout = build_payout_intent(
        &job,
        &evidence,
        &resolution,
        "payout-1",
        PaymentRail::Tempo,
        "job-1:payout:v1",
    )
    .expect("payout creates");

    assert!(check_outcome_market(&job, &market).is_empty());
    assert!(check_market_state(&market, &state).is_empty());
    assert!(check_market_signal(&market, &state, &signal, 150).is_empty());
    assert!(check_resolution(&job, &evidence, &resolution).is_empty());
    assert!(check_payout_intent(&job, &evidence, &resolution, &payout).is_empty());
    assert!(signal.advisory_only);
    assert!(!payout.authority_granted);
}
