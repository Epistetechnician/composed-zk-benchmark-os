use hsai_control_plane::{Capability, CapabilitySet, Digest};
use hsai_outcome_work_market::{
    create_outcome_market, open_outcome_market, MarketObservation, MarketSource, PaymentRail,
    WorkJob,
};
use hsai_outcome_work_market_offchain::{
    append_fill, append_provider_bid, append_quote, close_market, create_offchain_log,
    match_best_bid, replay_projection, MatchRecord, OffchainEvent, OffchainMarketLog, WorkQuote,
};
use hsai_outcome_work_market_offchain_checker::check_projection;
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

fn filled_log() -> hsai_outcome_work_market_offchain::OffchainMarketLog {
    let job = job();
    let frozen = create_outcome_market(&job, "market-1", MarketSource::Offchain, 100, 150)
        .expect("market creates");
    let market = open_outcome_market(&frozen, 110).expect("market opens");
    let log = create_offchain_log(&market).expect("log creates");
    let log = append_quote(
        &log,
        MarketObservation {
            market_id: market.market_id.clone(),
            job_digest: job.digest(),
            source: MarketSource::Offchain,
            sequence: 1,
            observed_at: 110,
            yes_price_micros: 700_000,
            liquidity_units: 10,
        },
    )
    .expect("quote appends");
    let log = append_provider_bid(
        &log,
        &job,
        WorkQuote {
            quote_id: "quote-1".to_owned(),
            market_digest: market.digest(),
            job_digest: job.digest(),
            provider_id: "provider-1".to_owned(),
            price_units: 60,
            success_probability_micros: 800_000,
            capacity_units: 1,
            posted_at: 111,
            expires_at: 140,
        },
    )
    .expect("bid appends");
    let fill = match_best_bid(&log, &job, 120).expect("bid matches");
    let log = append_fill(&log, fill).expect("fill appends");
    close_market(&log, 150).expect("market closes")
}

#[test]
fn independent_checker_accepts_replayed_projection() {
    let log = filled_log();
    let projection = replay_projection(&log).expect("projection replays");
    check_projection(&log, &projection).expect("checker accepts");
}

#[test]
fn independent_checker_rejects_forged_fill_projection() {
    let log = filled_log();
    let mut projection = replay_projection(&log).expect("projection replays");
    projection.fills[0] = MatchRecord {
        allocation_id: "forged".to_owned(),
        ..projection.fills[0].clone()
    };
    assert!(check_projection(&log, &projection).is_err());

    let forged_log = OffchainMarketLog {
        market: log.market,
        events: vec![OffchainEvent::Fill(MatchRecord {
            allocation_id: "unknown".to_owned(),
            quote_id: "missing".to_owned(),
            market_digest: digest("market"),
            job_digest: digest("job"),
            provider_id: "provider".to_owned(),
            price_units: 1,
            allocated_units: 1,
            matched_at: 120,
        })],
    };
    assert!(replay_projection(&forged_log).is_err());

    let mut overallocated_log = filled_log();
    let second_fill = projection.fills[0].clone();
    let second_fill = MatchRecord {
        allocation_id: "allocation-over-capacity".to_owned(),
        ..second_fill
    };
    overallocated_log
        .events
        .push(OffchainEvent::Fill(second_fill));
    assert!(check_projection(&overallocated_log, &projection).is_err());
}
