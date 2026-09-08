use hsai_control_plane::Digest;
use hsai_control_plane::{Capability, CapabilitySet};
use hsai_outcome_work_market::PaymentRail;
use hsai_outcome_work_market::{
    create_outcome_market, open_outcome_market, MarketObservation, MarketSource, WorkJob,
};
use hsai_outcome_work_market_offchain::{
    append_fill, append_provider_bid, append_quote, close_market, create_offchain_log,
    decode_event_log, encode_event_log, match_best_bid, project_advisory_budget, replay_projection,
    BaselineMechanism, BaselineQuote, EventLogStorageError, OffchainEvent, OffchainMarketLog,
    OffchainMarketLogFileStore, WorkQuote,
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
fn replay_reconstructs_projection_and_advisory_budget() {
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
            yes_price_micros: 600_000,
            liquidity_units: 10,
        },
    )
    .expect("first quote appends");
    let log = append_quote(
        &log,
        MarketObservation {
            market_id: market.market_id.clone(),
            job_digest: job.digest(),
            source: MarketSource::Offchain,
            sequence: 2,
            observed_at: 130,
            yes_price_micros: 800_000,
            liquidity_units: 20,
        },
    )
    .expect("second quote appends");
    let log = close_market(&log, 150).expect("market closes");
    let projection = replay_projection(&log).expect("projection replays");
    assert_eq!(
        projection.signal.as_ref().expect("signal").yes_price_micros,
        700_000
    );
    assert_eq!(projection.quote_count, 2);
    assert_eq!(
        project_advisory_budget(&job, projection.signal.as_ref().expect("signal")),
        82
    );
    assert_eq!(projection, replay_projection(&log).expect("replay repeats"));
}

#[test]
fn replay_rejects_quote_after_close_and_baselines_are_explicit() {
    let job = job();
    let frozen = create_outcome_market(&job, "market-1", MarketSource::Offchain, 100, 150)
        .expect("market creates");
    let market = open_outcome_market(&frozen, 110).expect("market opens");
    let log = create_offchain_log(&market).expect("log creates");
    let log = close_market(&log, 150).expect("market closes");
    let quote = MarketObservation {
        market_id: market.market_id.clone(),
        job_digest: job.digest(),
        source: MarketSource::Offchain,
        sequence: 1,
        observed_at: 110,
        yes_price_micros: 600_000,
        liquidity_units: 10,
    };
    assert!(append_quote(&log, quote).is_err());

    let fixed = BaselineQuote {
        mechanism: BaselineMechanism::FixedBounty,
        price_units: job.base_bounty_units,
    };
    let auction = BaselineQuote {
        mechanism: BaselineMechanism::ProviderAuction,
        price_units: 55,
    };
    assert_eq!(fixed.price_units, 40);
    assert_eq!(auction.price_units, 55);

    let forged = OffchainMarketLog {
        market,
        events: vec![
            OffchainEvent::Close { closed_at: 150 },
            OffchainEvent::Bid(WorkQuote {
                quote_id: "late-quote".to_owned(),
                market_digest: frozen.digest(),
                job_digest: job.digest(),
                provider_id: "provider-late".to_owned(),
                price_units: 50,
                success_probability_micros: 500_000,
                capacity_units: 1,
                posted_at: 110,
                expires_at: 140,
            }),
        ],
    };
    assert!(replay_projection(&forged).is_err());
}

#[test]
fn deterministic_matching_selects_lowest_valid_bid_and_replays_fill() {
    let job = job();
    let frozen = create_outcome_market(&job, "market-1", MarketSource::Offchain, 100, 150)
        .expect("market creates");
    let market = open_outcome_market(&frozen, 110).expect("market opens");
    let log = create_offchain_log(&market).expect("log creates");
    let log = append_provider_bid(
        &log,
        &job,
        WorkQuote {
            quote_id: "quote-expensive".to_owned(),
            market_digest: market.digest(),
            job_digest: job.digest(),
            provider_id: "provider-a".to_owned(),
            price_units: 70,
            success_probability_micros: 900_000,
            capacity_units: 1,
            posted_at: 111,
            expires_at: 140,
        },
    )
    .expect("first bid appends");
    let log = append_provider_bid(
        &log,
        &job,
        WorkQuote {
            quote_id: "quote-cheap".to_owned(),
            market_digest: market.digest(),
            job_digest: job.digest(),
            provider_id: "provider-b".to_owned(),
            price_units: 60,
            success_probability_micros: 700_000,
            capacity_units: 2,
            posted_at: 112,
            expires_at: 140,
        },
    )
    .expect("second bid appends");
    let fill = match_best_bid(&log, &job, 120).expect("best bid matches");
    assert_eq!(fill.quote_id, "quote-cheap");
    assert_eq!(fill.price_units, 60);
    let log = append_fill(&log, fill.clone()).expect("fill appends");
    let second_fill = match_best_bid(&log, &job, 121).expect("capacity remains");
    assert_eq!(second_fill.quote_id, "quote-cheap");
    assert_ne!(second_fill.allocation_id, fill.allocation_id);
    let log = append_fill(&log, second_fill).expect("second fill appends");
    let projection = replay_projection(&log).expect("projection replays");
    assert_eq!(projection.bid_count, 2);
    assert_eq!(projection.fill_count, 2);
    assert_eq!(projection.fills[0], fill);
    assert!(append_fill(&log, fill).is_err());
    let third_fill = match_best_bid(&log, &job, 122).expect("next provider remains");
    assert_eq!(third_fill.quote_id, "quote-expensive");
    let log = append_fill(&log, third_fill).expect("third fill appends");
    assert!(match_best_bid(&log, &job, 123).is_err());
}

#[test]
fn canonical_event_log_readback_preserves_digest_and_replay() {
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
    let log = close_market(&log, 150).expect("market closes");
    let bytes = encode_event_log(&log).expect("log encodes");
    let decoded = decode_event_log(&bytes).expect("log decodes");
    assert_eq!(decoded, log);
    assert_eq!(decoded.digest(), log.digest());
    assert_eq!(
        replay_projection(&decoded).expect("decoded log replays"),
        replay_projection(&log).expect("original log replays")
    );
    assert!(decode_event_log(b"not-json").is_err());
}

#[test]
fn file_store_initializes_canonical_log_and_verifies_readback_digest() {
    let job = job();
    let frozen = create_outcome_market(&job, "market-1", MarketSource::Offchain, 100, 150)
        .expect("market creates");
    let market = open_outcome_market(&frozen, 110).expect("market opens");
    let log = create_offchain_log(&market).expect("log creates");
    let directory = tempfile::tempdir().expect("temporary directory creates");
    let path = directory.path().join("events.json");
    let store = OffchainMarketLogFileStore::new(&path).expect("store creates");

    store.initialize(&log).expect("log initializes");

    let read = store
        .read_if_digest(&log.digest())
        .expect("readback verifies");
    assert_eq!(read, log);
    assert_eq!(
        std::fs::read(&path).expect("bytes read"),
        encode_event_log(&log).unwrap()
    );
}

#[test]
fn file_store_replaces_atomically_and_rejects_stale_expected_digest() {
    let job = job();
    let frozen = create_outcome_market(&job, "market-1", MarketSource::Offchain, 100, 150)
        .expect("market creates");
    let market = open_outcome_market(&frozen, 110).expect("market opens");
    let initial = create_offchain_log(&market).expect("log creates");
    let next = append_quote(
        &initial,
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
    let directory = tempfile::tempdir().expect("temporary directory creates");
    let path = directory.path().join("events.json");
    let store = OffchainMarketLogFileStore::new(&path).expect("store creates");

    store.initialize(&initial).expect("initializes");
    store
        .replace_if_digest(Some(initial.digest()), &next)
        .expect("replacement succeeds");
    assert_eq!(store.read().expect("replacement reads"), next);
    assert!(!path.with_extension("json.tmp").exists());

    let error = store
        .replace_if_digest(Some(initial.digest()), &initial)
        .expect_err("stale replacement rejects");
    assert_eq!(
        error,
        EventLogStorageError::Stale {
            expected: Some(initial.digest()),
            actual: Some(next.digest()),
        }
    );
}

#[test]
fn file_store_rejects_noncanonical_malformed_and_stale_bytes() {
    let job = job();
    let frozen = create_outcome_market(&job, "market-1", MarketSource::Offchain, 100, 150)
        .expect("market creates");
    let market = open_outcome_market(&frozen, 110).expect("market opens");
    let log = create_offchain_log(&market).expect("log creates");
    let directory = tempfile::tempdir().expect("temporary directory creates");
    let path = directory.path().join("events.json");
    let store = OffchainMarketLogFileStore::new(&path).expect("store creates");
    let canonical = encode_event_log(&log).expect("log encodes");

    let mut noncanonical = canonical.clone();
    noncanonical.push(b' ');
    std::fs::write(&path, noncanonical).expect("noncanonical bytes write");
    assert_eq!(
        store.read().expect_err("noncanonical bytes reject"),
        EventLogStorageError::NonCanonicalBytes
    );

    std::fs::write(&path, b"not-json").expect("malformed bytes write");
    assert!(matches!(
        store.read(),
        Err(EventLogStorageError::Serialization(_))
    ));

    let stale = close_market(&log, 150).expect("syntactically closed log creates");
    std::fs::write(&path, encode_event_log(&stale).expect("stale log encodes"))
        .expect("stale bytes write");
    assert!(matches!(
        store.read(),
        Err(EventLogStorageError::InvalidEventLog(_))
    ));

    std::fs::remove_file(&path).expect("malformed target removes");
    std::fs::write(path.with_extension("json.tmp"), canonical).expect("temporary bytes write");
    assert_eq!(
        store.read().expect_err("stale temporary bytes reject"),
        EventLogStorageError::StaleTemporaryArtifact
    );
}

#[test]
fn file_store_readback_digest_check_rejects_wrong_caller_expectation() {
    let job = job();
    let frozen = create_outcome_market(&job, "market-1", MarketSource::Offchain, 100, 150)
        .expect("market creates");
    let market = open_outcome_market(&frozen, 110).expect("market opens");
    let log = create_offchain_log(&market).expect("log creates");
    let directory = tempfile::tempdir().expect("temporary directory creates");
    let store = OffchainMarketLogFileStore::new(directory.path().join("events.json"))
        .expect("store creates");
    store.initialize(&log).expect("log initializes");

    let expected = digest("different-log");
    assert_eq!(
        store
            .read_if_digest(&expected)
            .expect_err("wrong digest rejects"),
        EventLogStorageError::ReadbackDigestMismatch {
            expected,
            actual: log.digest(),
        }
    );
}
