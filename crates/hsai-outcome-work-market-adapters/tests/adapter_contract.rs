use hsai_control_plane::{Capability, CapabilitySet, Digest};
use hsai_outcome_work_market::{
    build_payout_intent, create_outcome_market, open_outcome_market, resolve_work, EvidenceStatus,
    MarketObservation, MarketSource, PaymentRail, PayoutStatus, WorkEvidencePacket, WorkJob,
};
use hsai_outcome_work_market_adapters::{
    confirm_hyperliquid_observation, prepare_hyperliquid_observation, prepare_payment,
    reconcile_payment, ChainObservationStatus, HyperliquidTestnetConfig, PaymentPreparationStatus,
    HYPERLIQUID_TESTNET_API_URL, HYPERLIQUID_TESTNET_CHAIN_ID, HYPERLIQUID_TESTNET_RPC_URL,
};
use hsai_outcome_work_market_offchain::{
    append_quote, close_market, create_offchain_log, replay_projection,
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

#[test]
fn testnet_observation_and_payment_reconciliation_remain_dry_run() {
    let job = job();
    let frozen_market =
        create_outcome_market(&job, "market-1", MarketSource::HyperliquidTestnet, 100, 150)
            .expect("market creates");
    let market = open_outcome_market(&frozen_market, 110).expect("market opens");
    let log = create_offchain_log(&market).expect("offchain log creates");
    let log = append_quote(
        &log,
        MarketObservation {
            market_id: market.market_id.clone(),
            job_digest: job.digest(),
            source: MarketSource::HyperliquidTestnet,
            sequence: 1,
            observed_at: 110,
            yes_price_micros: 700_000,
            liquidity_units: 10,
        },
    )
    .expect("quote appends");
    let log = close_market(&log, 150).expect("market closes");
    let signal = replay_projection(&log)
        .expect("projection replays")
        .signal
        .expect("signal exists");
    let config = HyperliquidTestnetConfig {
        chain_id: HYPERLIQUID_TESTNET_CHAIN_ID,
        rpc_url: HYPERLIQUID_TESTNET_RPC_URL.to_owned(),
        api_url: HYPERLIQUID_TESTNET_API_URL.to_owned(),
        market_id: market.market_id.clone(),
        market_digest: market.digest(),
        job_digest: job.digest(),
    };
    let pending =
        prepare_hyperliquid_observation(&config, "observation-1", "tx-1", signal.digest(), 120)
            .expect("testnet observation prepares");
    assert_eq!(pending.status, ChainObservationStatus::Pending);
    assert!(pending.block_number.is_none());
    let confirmed = confirm_hyperliquid_observation(&config, &pending, 42)
        .expect("testnet observation confirms");
    assert_eq!(confirmed.status, ChainObservationStatus::Confirmed);
    assert_eq!(confirmed.block_number, Some(42));

    let evidence = WorkEvidencePacket {
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
    };
    let resolution = resolve_work(&job, &evidence, 210).expect("work resolves");
    let payout = build_payout_intent(
        &job,
        &evidence,
        &resolution,
        "payout-1",
        PaymentRail::Tempo,
        "job-1:payout:v1",
    )
    .expect("payout intent prepares");
    let payment = prepare_payment(&payout, "provider-1").expect("payment prepares");
    assert_eq!(payment.status, PaymentPreparationStatus::Prepared);
    assert_eq!(payment.rail, PaymentRail::Tempo);
    assert!(payment.external_reference.is_none());
    assert_eq!(payout.status, PayoutStatus::PendingAuthorization);
    assert!(!payout.authority_granted);

    let confirmed_payment = reconcile_payment(
        &payment,
        "tempo-tx-1",
        PaymentPreparationStatus::Confirmed,
        Some(220),
    )
    .expect("payment reconciles");
    assert_eq!(
        confirmed_payment.external_reference.as_deref(),
        Some("tempo-tx-1")
    );
    assert_eq!(confirmed_payment.confirmed_at, Some(220));

    assert!(reconcile_payment(
        &payment,
        "tempo-tx-2",
        PaymentPreparationStatus::Prepared,
        None,
    )
    .is_err());
}
