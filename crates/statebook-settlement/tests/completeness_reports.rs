use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use statebook_core::{
    analyze_terminal_residual_v1, derive_state_key, parse_normalization_profile_v1,
    parse_source_contract_v1, validate_and_lower, ContractPositionV1, DeclaredStateDomainV1,
    DeclaredTerminalStateV1, PayoffCompletenessReportV1, SemanticCompletenessReport,
    SignedRational,
};
use statebook_settlement::{
    compose_completeness_reports_v1, derive_analysis_subject_v1, parse_completeness_fixture_v1,
    AssuranceCompletenessStatusV1, CapitalCompletenessStatusV1, CompletenessMissingFactV1,
    CompletenessReasonV1, ExecutionCompletenessStatusV1, RecoveryCompletenessStatusV1,
    RecoveryPathProfileV1, SettlementCompletenessStatusV1,
};

const BASELINE: &[u8] =
    include_bytes!("../../statebook-core/tests/fixtures/terminal_contract_baseline_v1.json");
const PROFILE: &[u8] =
    include_bytes!("../../statebook-core/tests/fixtures/normalization_profile_v1.json");
const FIXTURE: &[u8] = include_bytes!("fixtures/completeness_reports_v1.json");

fn rational(numerator: i128, denominator: u128) -> SignedRational {
    SignedRational::new(numerator, denominator).unwrap()
}

fn composed(bytes: &[u8], evaluated_at: i64) -> statebook_settlement::SevenCompletenessReportsV1 {
    let (semantic, payoff) = reports();
    let fixture = parse_completeness_fixture_v1(bytes).unwrap();
    compose_completeness_reports_v1(&semantic, &payoff, &fixture, evaluated_at).unwrap()
}

fn mutate(update: impl FnOnce(&mut Value)) -> Vec<u8> {
    let mut value: Value = serde_json::from_slice(FIXTURE).unwrap();
    update(&mut value);
    serde_json::to_vec(&value).unwrap()
}

fn assert_no_bare_success_value(value: &Value) {
    match value {
        Value::String(value) => {
            assert!(!matches!(
                value.as_str(),
                "recognized" | "final" | "executable"
            ));
        }
        Value::Array(values) => values.iter().for_each(assert_no_bare_success_value),
        Value::Object(values) => values.values().for_each(assert_no_bare_success_value),
        _ => {}
    }
}

fn bind_capital_context(value: &mut Value) {
    let capital = &value["capital"];
    let field = |tag: u16, bytes: Vec<u8>| {
        [
            tag.to_be_bytes().as_slice(),
            (bytes.len() as u32).to_be_bytes().as_slice(),
            bytes.as_slice(),
        ]
        .concat()
    };
    let digest = |name: &str| hex::decode(capital[name].as_str().unwrap()).unwrap();
    let rational = |name: &str| {
        let rational = SignedRational::parse(
            capital[name]["numerator"].as_str().unwrap(),
            capital[name]["denominator"].as_str().unwrap(),
        )
        .unwrap();
        [
            rational.numerator().to_be_bytes().as_slice(),
            rational.denominator().to_be_bytes().as_slice(),
        ]
        .concat()
    };
    let payload = [
        field(1, 1_u16.to_be_bytes().to_vec()),
        field(2, digest("analysis_subject_digest")),
        field(
            3,
            capital["authority_id"]
                .as_str()
                .unwrap()
                .as_bytes()
                .to_vec(),
        ),
        field(
            4,
            capital["eligible_account"]
                .as_str()
                .unwrap()
                .as_bytes()
                .to_vec(),
        ),
        field(5, capital["model_id"].as_str().unwrap().as_bytes().to_vec()),
        field(
            6,
            (capital["model_version"].as_u64().unwrap() as u32)
                .to_be_bytes()
                .to_vec(),
        ),
        field(7, digest("model_digest")),
        field(8, rational("haircut")),
        field(
            9,
            capital["margin_rule_id"]
                .as_str()
                .unwrap()
                .as_bytes()
                .to_vec(),
        ),
        field(
            10,
            capital["jurisdiction"]
                .as_str()
                .unwrap()
                .as_bytes()
                .to_vec(),
        ),
        field(
            11,
            capital["liquidation_horizon_seconds"]
                .as_u64()
                .unwrap()
                .to_be_bytes()
                .to_vec(),
        ),
        field(
            12,
            capital["observed_at"]
                .as_i64()
                .unwrap()
                .to_be_bytes()
                .to_vec(),
        ),
        field(
            13,
            capital["expires_at"]
                .as_i64()
                .unwrap()
                .to_be_bytes()
                .to_vec(),
        ),
    ]
    .concat();
    let mut hasher = Sha256::new();
    hasher.update(b"statebook:p3-capital-context:v1\0");
    hasher.update(1_u16.to_be_bytes());
    hasher.update(payload);
    let context_digest = hex::encode(hasher.finalize());
    for receipt in value["capital"]["receipts"].as_array_mut().unwrap() {
        receipt["capital_context_digest"] = json!(context_digest);
    }
}

fn reports() -> (SemanticCompletenessReport, PayoffCompletenessReportV1) {
    let profile = parse_normalization_profile_v1(PROFILE).unwrap();
    let contract =
        validate_and_lower(parse_source_contract_v1(BASELINE).unwrap(), &profile).unwrap();
    let semantic = contract.completeness().clone();
    let domain = DeclaredStateDomainV1::try_new([
        DeclaredTerminalStateV1::try_new("below", rational(99_999, 1)).unwrap(),
        DeclaredTerminalStateV1::try_new("equal", rational(100_000, 1)).unwrap(),
        DeclaredTerminalStateV1::try_new("above", rational(100_001, 1)).unwrap(),
    ])
    .unwrap();
    let payoff = analyze_terminal_residual_v1(
        ContractPositionV1::new(&contract, rational(1, 1)),
        &[ContractPositionV1::new(&contract, rational(1, 1))],
        &domain,
    )
    .unwrap();
    (semantic, payoff)
}

fn reports_with_two_candidates() -> (SemanticCompletenessReport, PayoffCompletenessReportV1) {
    let profile = parse_normalization_profile_v1(PROFILE).unwrap();
    let baseline =
        validate_and_lower(parse_source_contract_v1(BASELINE).unwrap(), &profile).unwrap();
    let mut alternate_source: Value = serde_json::from_slice(BASELINE).unwrap();
    alternate_source["payoff"]["comparator"]["kind"] = json!("greater_than");
    let alternate_bytes = serde_json::to_vec(&alternate_source).unwrap();
    let alternate = validate_and_lower(
        parse_source_contract_v1(&alternate_bytes).unwrap(),
        &profile,
    )
    .unwrap();
    let semantic = baseline.completeness().clone();
    let domain = DeclaredStateDomainV1::try_new([
        DeclaredTerminalStateV1::try_new("below", rational(99_999, 1)).unwrap(),
        DeclaredTerminalStateV1::try_new("equal", rational(100_000, 1)).unwrap(),
        DeclaredTerminalStateV1::try_new("above", rational(100_001, 1)).unwrap(),
    ])
    .unwrap();
    let payoff = analyze_terminal_residual_v1(
        ContractPositionV1::new(&baseline, rational(1, 1)),
        &[
            ContractPositionV1::new(&baseline, rational(1, 1)),
            ContractPositionV1::new(&alternate, rational(1, 1)),
        ],
        &domain,
    )
    .unwrap();
    (semantic, payoff)
}

fn reports_with_negative_candidate() -> (SemanticCompletenessReport, PayoffCompletenessReportV1) {
    let profile = parse_normalization_profile_v1(PROFILE).unwrap();
    let contract =
        validate_and_lower(parse_source_contract_v1(BASELINE).unwrap(), &profile).unwrap();
    let semantic = contract.completeness().clone();
    let domain = DeclaredStateDomainV1::try_new([
        DeclaredTerminalStateV1::try_new("below", rational(99_999, 1)).unwrap(),
        DeclaredTerminalStateV1::try_new("equal", rational(100_000, 1)).unwrap(),
        DeclaredTerminalStateV1::try_new("above", rational(100_001, 1)).unwrap(),
    ])
    .unwrap();
    let payoff = analyze_terminal_residual_v1(
        ContractPositionV1::new(&contract, rational(1, 1)),
        &[ContractPositionV1::new(&contract, rational(-1, 1))],
        &domain,
    )
    .unwrap();
    (semantic, payoff)
}

#[test]
fn frozen_subject_and_profile_identity() {
    let (semantic, payoff) = reports();
    let subject = derive_analysis_subject_v1(&semantic, &payoff);
    assert_eq!(
        subject.digest().to_hex(),
        "fd4c10a8b9cadc57e5021b9fdf380ce3abbbb7e270bbb981113de47eded7d73a"
    );
    assert_eq!(
        RecoveryPathProfileV1::statebook_externalization_v1()
            .digest()
            .to_hex(),
        "3d412a89c19e5e2ec4812bde5233784574815cab2fc063dab5653d113730601e"
    );
    let profile = parse_normalization_profile_v1(PROFILE).unwrap();
    let contract =
        validate_and_lower(parse_source_contract_v1(BASELINE).unwrap(), &profile).unwrap();
    let receipt = derive_state_key(&contract);
    assert_eq!(receipt.canonical_preimage().len(), 701);
    assert_eq!(
        receipt.state_key().to_hex(),
        "f1662f3fb5a10c074680c0baf76ba488b7230337456358be92f3127d8a632c08"
    );
    assert_eq!(
        receipt.validated_contract_digest().to_hex(),
        "7634410968adb9b56c62f213de7956796f9f3f62b102d4f6efe7f45d86858788"
    );
    assert_eq!(
        payoff.domain_digest().to_hex(),
        "67cb8e1807cd3e619f73d569f70de494ef60610f4d44acea236b0ee006e45e6a"
    );
}

#[test]
fn full_fixture_returns_seven_independent_fixture_qualified_reports() {
    let report = composed(FIXTURE, 1500);
    assert_eq!(
        report.execution().status(),
        ExecutionCompletenessStatusV1::ExecutableInFixture
    );
    assert_eq!(
        report.capital().status(),
        CapitalCompletenessStatusV1::RecognizedInFixture
    );
    assert_eq!(
        report.settlement().status(),
        SettlementCompletenessStatusV1::FinalInFixture
    );
    assert_eq!(
        report.assurance().status(),
        AssuranceCompletenessStatusV1::AllRequiredObservedInFixture
    );
    assert_eq!(
        report.recovery().status(),
        RecoveryCompletenessStatusV1::CompleteOnVersionedFixtureProfile
    );
    assert_eq!(
        report.execution().legs()[0].executable_quantity(),
        rational(1, 1)
    );
    assert_eq!(
        report.execution().legs()[0].average_price(),
        Some(rational(201, 2))
    );
    assert_eq!(
        report.execution().legs()[0].worst_price(),
        Some(rational(101, 1))
    );
    assert_eq!(report.assurance().properties().len(), 9);
    assert_eq!(report.recovery().paths().len(), 14);
    assert!(report.capital().context().is_some());
    assert!(report
        .settlement()
        .context()
        .unwrap()
        .reversal_rule()
        .is_some());
    assert_eq!(
        report.recovery().context().unwrap().in_flight_items().len(),
        1
    );
    let serialized = serde_json::to_value(&report).unwrap();
    assert_no_bare_success_value(&serialized);
    assert_eq!(
        serialized["capital"]["receipts"][0]["verdict"],
        json!("recognized_in_fixture")
    );
    let object = serialized.as_object().unwrap();
    for forbidden in [
        "complete",
        "all_complete",
        "weakest",
        "score",
        "rank",
        "safe",
        "authorized",
        "release",
    ] {
        assert!(!object.contains_key(forbidden));
    }
}

#[test]
fn absence_staleness_and_dimension_isolation_are_typed() {
    let absent = composed(br#"{"schema_version":"statebook-completeness-fixture:v1","execution":null,"capital":null,"settlement":null,"assurance":null,"recovery":null}"#, 1500);
    assert_eq!(
        absent.execution().status(),
        ExecutionCompletenessStatusV1::NotObserved
    );
    assert_eq!(
        absent.capital().status(),
        CapitalCompletenessStatusV1::NotEvaluated
    );
    assert_eq!(
        absent.settlement().status(),
        SettlementCompletenessStatusV1::Unknown
    );
    assert_eq!(
        absent.assurance().status(),
        AssuranceCompletenessStatusV1::NotObserved
    );
    assert_eq!(
        absent.recovery().status(),
        RecoveryCompletenessStatusV1::NotObserved
    );
    assert!(absent.execution().fixture_digest().is_none());
    let fresh = composed(FIXTURE, 1500);
    let stale_execution = mutate(|value| value["execution"]["expires_at"] = json!(1499));
    let stale = composed(&stale_execution, 1500);
    assert_eq!(
        stale.execution().status(),
        ExecutionCompletenessStatusV1::NotObserved
    );
    assert!(stale.execution().fixture_digest().is_some());
    assert_eq!(
        fresh.capital().report_digest(),
        stale.capital().report_digest()
    );
    assert_eq!(
        fresh.settlement().report_digest(),
        stale.settlement().report_digest()
    );
    assert_eq!(
        fresh.assurance().report_digest(),
        stale.assurance().report_digest()
    );
    assert_eq!(
        fresh.recovery().report_digest(),
        stale.recovery().report_digest()
    );
}

#[test]
fn execution_maximal_prefix_and_explicit_support_precedence_are_exact() {
    let partial_bytes = mutate(|value| {
        value["execution"]["legs"][0]["maximum_fee"] = json!({"numerator":"1","denominator":"20"});
    });
    let partial = composed(&partial_bytes, 1500);
    assert_eq!(
        partial.execution().status(),
        ExecutionCompletenessStatusV1::PartiallyExecutableInFixture
    );
    assert_eq!(
        partial.execution().legs()[0].executable_quantity(),
        rational(1, 2)
    );
    assert_eq!(
        partial.execution().legs()[0].unfilled_quantity(),
        rational(1, 2)
    );
    let unsupported_bytes =
        mutate(|value| value["execution"]["legs"][0]["atomicity"] = json!("unsupported"));
    assert_eq!(
        composed(&unsupported_bytes, 1500).execution().status(),
        ExecutionCompletenessStatusV1::NotExecutableInFixture
    );
}

#[test]
fn capital_settlement_assurance_and_recovery_precedence_remain_independent() {
    let denied = mutate(|value| {
        value["capital"]["receipts"][0]["verdict"] = json!("denied");
        value["capital"]["receipts"][0]["recognized_quantity"] =
            json!({"numerator":"0","denominator":"1"});
    });
    assert_eq!(
        composed(&denied, 1500).capital().status(),
        CapitalCompletenessStatusV1::NotRecognizedInFixture
    );
    let disputed = mutate(|value| value["settlement"]["disputed"] = json!(true));
    assert_eq!(
        composed(&disputed, 1500).settlement().status(),
        SettlementCompletenessStatusV1::DisputedInFixture
    );
    let assurance_fail =
        mutate(|value| value["assurance"]["observations"][0]["verdict"] = json!("fail"));
    assert_eq!(
        composed(&assurance_fail, 1500).assurance().status(),
        AssuranceCompletenessStatusV1::ContradictedInFixture
    );
    let missing_path = mutate(|value| {
        value["recovery"]["paths"].as_array_mut().unwrap().pop();
    });
    assert_eq!(
        composed(&missing_path, 1500).recovery().status(),
        RecoveryCompletenessStatusV1::IncompleteOnVersionedFixtureProfile
    );
    let mismatch = mutate(|value| {
        value["recovery"]["in_flight_items"][0]["observed_digest"] =
            json!("4444444444444444444444444444444444444444444444444444444444444444")
    });
    assert_eq!(
        composed(&mismatch, 1500).recovery().status(),
        RecoveryCompletenessStatusV1::FailedInFixture
    );
}

#[test]
fn bindings_duplicate_keys_unknown_fields_and_financial_numbers_fail_closed() {
    let wrong_subject = mutate(|value| {
        value["execution"]["analysis_subject_digest"] =
            json!("0000000000000000000000000000000000000000000000000000000000000000")
    });
    let (semantic, payoff) = reports();
    let fixture = parse_completeness_fixture_v1(&wrong_subject).unwrap();
    assert!(compose_completeness_reports_v1(&semantic, &payoff, &fixture, 1500).is_err());
    let wrong_profile = mutate(|value| {
        value["recovery"]["recovery_profile_digest"] =
            json!("0000000000000000000000000000000000000000000000000000000000000000")
    });
    let fixture = parse_completeness_fixture_v1(&wrong_profile).unwrap();
    assert!(compose_completeness_reports_v1(&semantic, &payoff, &fixture, 1500).is_err());
    assert!(parse_completeness_fixture_v1(br#"{"schema_version":"statebook-completeness-fixture:v1","schema_version":"statebook-completeness-fixture:v1","execution":null,"capital":null,"settlement":null,"assurance":null,"recovery":null}"#).is_err());
    assert!(parse_completeness_fixture_v1(br#"{"schema_version":"statebook-completeness-fixture:v1","unexpected":true,"execution":null,"capital":null,"settlement":null,"assurance":null,"recovery":null}"#).is_err());
    let numeric =
        mutate(|value| value["execution"]["legs"][0]["requested_quantity"]["numerator"] = json!(1));
    assert!(parse_completeness_fixture_v1(&numeric).is_err());
    let floating = mutate(|value| {
        value["execution"]["legs"][0]["requested_quantity"]["numerator"] = json!(1.5)
    });
    assert!(parse_completeness_fixture_v1(&floating).is_err());
}

#[test]
fn invalid_times_fail_closed_before_evaluation() {
    for bytes in [
        mutate(|value| value["execution"]["observed_at"] = json!(-1)),
        mutate(|value| value["capital"]["expires_at"] = json!(-1)),
        mutate(|value| value["execution"]["legs"][0]["deadline"] = json!(999)),
    ] {
        assert!(parse_completeness_fixture_v1(&bytes).is_err());
    }
    let (semantic, payoff) = reports();
    let fixture = parse_completeness_fixture_v1(FIXTURE).unwrap();
    assert!(compose_completeness_reports_v1(&semantic, &payoff, &fixture, -1).is_err());
}

#[test]
fn validated_fixture_exposes_only_a_sanitized_parse_receipt() {
    let fixture = parse_completeness_fixture_v1(FIXTURE).unwrap();
    assert_eq!(
        fixture.schema_version(),
        "statebook-completeness-fixture:v1"
    );
    assert!(fixture.has_execution());
    assert!(fixture.has_capital());
    assert!(fixture.has_settlement());
    assert!(fixture.has_assurance());
    assert!(fixture.has_recovery());
    let serialized = serde_json::to_value(&fixture).unwrap();
    assert_eq!(serialized.as_object().unwrap().len(), 7);
    assert!(serialized.get("execution").is_none());
}

#[test]
fn typed_missing_facts_and_capital_residuals_are_identity_bearing() {
    let absent = composed(
        br#"{"schema_version":"statebook-completeness-fixture:v1","execution":null,"capital":null,"settlement":null,"assurance":null,"recovery":null}"#,
        1500,
    );
    for facts in [
        absent.execution().missing_facts(),
        absent.capital().missing_facts(),
        absent.settlement().missing_facts(),
        absent.assurance().missing_facts(),
        absent.recovery().missing_facts(),
    ] {
        assert!(facts.contains(&CompletenessMissingFactV1::Fixture));
    }
    let missing_root = mutate(|value| {
        value["assurance"]["observations"][0]["current_roots"] = json!([]);
    });
    let changed = composed(&missing_root, 1500);
    assert!(changed
        .assurance()
        .missing_facts()
        .contains(&CompletenessMissingFactV1::CurrentAssuranceRoot));
    assert_ne!(
        composed(FIXTURE, 1500).assurance().report_digest(),
        changed.assurance().report_digest()
    );
    let partial = mutate(|value| {
        value["capital"]["receipts"][0]["recognized_quantity"] =
            json!({"numerator":"1","denominator":"2"});
    });
    assert_eq!(
        composed(&partial, 1500).capital().receipts()[0].recognition_residual(),
        rational(1, 2)
    );
}

#[test]
fn semantic_collection_reordering_changes_only_raw_document_lineage() {
    let reordered = mutate(|value| {
        value["assurance"]["observations"]
            .as_array_mut()
            .unwrap()
            .reverse();
        value["execution"]["legs"][0]["levels"]
            .as_array_mut()
            .unwrap()
            .reverse();
        value["execution"]["source_evidence_digests"]
            .as_array_mut()
            .unwrap()
            .reverse();
        value["capital"]["receipts"]
            .as_array_mut()
            .unwrap()
            .reverse();
        value["capital"]["source_evidence_digests"]
            .as_array_mut()
            .unwrap()
            .reverse();
        value["settlement"]["stages"]
            .as_array_mut()
            .unwrap()
            .reverse();
        value["settlement"]["source_evidence_digests"]
            .as_array_mut()
            .unwrap()
            .reverse();
        value["assurance"]["observations"][0]["current_roots"]
            .as_array_mut()
            .unwrap()
            .reverse();
        value["assurance"]["observations"][0]["dependency_roots"]
            .as_array_mut()
            .unwrap()
            .reverse();
        value["assurance"]["source_evidence_digests"]
            .as_array_mut()
            .unwrap()
            .reverse();
        value["recovery"]["paths"].as_array_mut().unwrap().reverse();
        value["recovery"]["paths"][0]["capabilities"]
            .as_array_mut()
            .unwrap()
            .reverse();
        value["recovery"]["in_flight_items"]
            .as_array_mut()
            .unwrap()
            .reverse();
        value["recovery"]["canary_stages"]
            .as_array_mut()
            .unwrap()
            .reverse();
        value["recovery"]["source_evidence_digests"]
            .as_array_mut()
            .unwrap()
            .reverse();
    });
    let first = composed(FIXTURE, 1500);
    let second = composed(&reordered, 1500);
    assert_ne!(
        first.fixture_document_sha256(),
        second.fixture_document_sha256()
    );
    assert_eq!(first.composition_digest(), second.composition_digest());
    assert_eq!(
        first.execution().fixture_digest(),
        second.execution().fixture_digest()
    );
    assert_eq!(
        first.capital().fixture_digest(),
        second.capital().fixture_digest()
    );
    assert_eq!(
        first.settlement().fixture_digest(),
        second.settlement().fixture_digest()
    );
    assert_eq!(
        first.assurance().fixture_digest(),
        second.assurance().fixture_digest()
    );
    assert_eq!(
        first.recovery().fixture_digest(),
        second.recovery().fixture_digest()
    );
    assert_eq!(
        first.execution().report_digest(),
        second.execution().report_digest()
    );
    assert_eq!(
        first.assurance().report_digest(),
        second.assurance().report_digest()
    );
    assert_eq!(
        first.capital().report_digest(),
        second.capital().report_digest()
    );
    assert_eq!(
        first.settlement().report_digest(),
        second.settlement().report_digest()
    );
    assert_eq!(
        first.recovery().report_digest(),
        second.recovery().report_digest()
    );
}

#[test]
fn multi_element_source_root_reconciliation_canary_and_capital_sets_are_invariant() {
    let mut value: Value = serde_json::from_slice(FIXTURE).unwrap();
    for (dimension, digest) in [
        (
            "execution",
            "0101010101010101010101010101010101010101010101010101010101010101",
        ),
        (
            "capital",
            "0202020202020202020202020202020202020202020202020202020202020202",
        ),
        (
            "settlement",
            "0303030303030303030303030303030303030303030303030303030303030303",
        ),
        (
            "assurance",
            "0404040404040404040404040404040404040404040404040404040404040404",
        ),
        (
            "recovery",
            "0505050505050505050505050505050505050505050505050505050505050505",
        ),
    ] {
        value[dimension]["source_evidence_digests"]
            .as_array_mut()
            .unwrap()
            .push(json!(digest));
    }
    value["assurance"]["observations"][0]["current_roots"]
        .as_array_mut()
        .unwrap()
        .push(json!({"root_class":"kms","root_id":"second-current-root"}));
    value["assurance"]["observations"][0]["dependency_roots"]
        .as_array_mut()
        .unwrap()
        .push(json!({"root_class":"ci_cd","root_id":"second-dependency-root"}));
    value["recovery"]["in_flight_items"]
        .as_array_mut()
        .unwrap()
        .push(json!({
            "item_id":"item-2",
            "expected_digest":"0909090909090909090909090909090909090909090909090909090909090909",
            "observed_digest":"0909090909090909090909090909090909090909090909090909090909090909"
        }));
    value["recovery"]["canary_stages"]
        .as_array_mut()
        .unwrap()
        .push(json!("unknown"));
    let first_bytes = serde_json::to_vec(&value).unwrap();
    let first = composed(&first_bytes, 1500);
    for dimension in [
        "execution",
        "capital",
        "settlement",
        "assurance",
        "recovery",
    ] {
        value[dimension]["source_evidence_digests"]
            .as_array_mut()
            .unwrap()
            .reverse();
    }
    value["assurance"]["observations"][0]["current_roots"]
        .as_array_mut()
        .unwrap()
        .reverse();
    value["assurance"]["observations"][0]["dependency_roots"]
        .as_array_mut()
        .unwrap()
        .reverse();
    value["recovery"]["in_flight_items"]
        .as_array_mut()
        .unwrap()
        .reverse();
    value["recovery"]["canary_stages"]
        .as_array_mut()
        .unwrap()
        .reverse();
    let second_bytes = serde_json::to_vec(&value).unwrap();
    let second = composed(&second_bytes, 1500);
    assert_ne!(
        first.fixture_document_sha256(),
        second.fixture_document_sha256()
    );
    assert_eq!(first.composition_digest(), second.composition_digest());
    assert_eq!(
        first.execution().fixture_digest(),
        second.execution().fixture_digest()
    );
    assert_eq!(
        first.capital().fixture_digest(),
        second.capital().fixture_digest()
    );
    assert_eq!(
        first.settlement().fixture_digest(),
        second.settlement().fixture_digest()
    );
    assert_eq!(
        first.assurance().fixture_digest(),
        second.assurance().fixture_digest()
    );
    assert_eq!(
        first.recovery().fixture_digest(),
        second.recovery().fixture_digest()
    );

    let (semantic, payoff) = reports_with_two_candidates();
    let subject = derive_analysis_subject_v1(&semantic, &payoff);
    let mut value: Value = serde_json::from_slice(FIXTURE).unwrap();
    value["execution"] = Value::Null;
    value["settlement"] = Value::Null;
    value["assurance"] = Value::Null;
    value["recovery"] = Value::Null;
    value["capital"]["analysis_subject_digest"] = json!(subject.digest().to_hex());
    let receipt_template = value["capital"]["receipts"][0].clone();
    value["capital"]["receipts"] = Value::Array(
        payoff
            .candidate()
            .iter()
            .map(|candidate| {
                let mut receipt = receipt_template.clone();
                receipt["state_key"] = json!(candidate.state_key().digest().to_hex());
                receipt["recognized_quantity"] = json!({
                    "numerator": candidate.quantity().checked_abs().unwrap().numerator().to_string(),
                    "denominator": candidate.quantity().denominator().to_string()
                });
                receipt
            })
            .collect(),
    );
    bind_capital_context(&mut value);
    let first_bytes = serde_json::to_vec(&value).unwrap();
    let fixture = parse_completeness_fixture_v1(&first_bytes).unwrap();
    let first = compose_completeness_reports_v1(&semantic, &payoff, &fixture, 1500).unwrap();
    value["capital"]["receipts"]
        .as_array_mut()
        .unwrap()
        .reverse();
    let second_bytes = serde_json::to_vec(&value).unwrap();
    let fixture = parse_completeness_fixture_v1(&second_bytes).unwrap();
    let second = compose_completeness_reports_v1(&semantic, &payoff, &fixture, 1500).unwrap();
    assert_ne!(
        first.fixture_document_sha256(),
        second.fixture_document_sha256()
    );
    assert_eq!(
        first.capital().fixture_digest(),
        second.capital().fixture_digest()
    );
    assert_eq!(
        first.capital().report_digest(),
        second.capital().report_digest()
    );
    assert_eq!(first.composition_digest(), second.composition_digest());
}

#[test]
fn frozen_full_report_digests() {
    let report = composed(FIXTURE, 1500);
    let actual = vec![
        report.semantic_report_digest().to_hex(),
        report.payoff_report_digest().to_hex(),
        report.execution().report_digest().to_hex(),
        report.capital().report_digest().to_hex(),
        report.settlement().report_digest().to_hex(),
        report.assurance().report_digest().to_hex(),
        report.recovery().report_digest().to_hex(),
        report.composition_digest().to_hex(),
    ];
    assert_eq!(
        actual,
        vec![
            "d27052f12380f8eb98e0ba84e649eb2a1f11b58ebf9fb27c7d47ea1c0a6666cf",
            "d6d87c5a28bc70196bb0515a3d2c998737c0a8957fd3074a909d1d9294ad1ec0",
            "fee730a504c8ca64770fdaf270fd396e6212012a6c24d69a87e8fab3040b1a09",
            "31feadcb2e6e3e44c96961149e451085aa54a92c55df1d119316bc2d9e1628f2",
            "de8407321899a9e3e551c30e1f6808025f32bbd648687b56c9862401c78325eb",
            "df98f15fe4fc0e47b81a5e0acab446dcf141db0749b75cc1efc674bf2c71b41f",
            "e4c47a38d42cd01378850c53c05950e266a0f8a1d30f720e0b2ab41298cdae7e",
            "5becefa3f2ab8239dc516fbdb965544f0126ca341723c871c7babe2aff69086f",
        ]
    );
}

#[test]
fn missing_required_execution_leg_is_not_observed() {
    let (semantic, payoff) = reports_with_two_candidates();
    let subject = derive_analysis_subject_v1(&semantic, &payoff);
    let bytes = mutate(|value| {
        value["execution"]["analysis_subject_digest"] = json!(subject.digest().to_hex());
        value["capital"] = Value::Null;
        value["settlement"] = Value::Null;
        value["assurance"] = Value::Null;
        value["recovery"] = Value::Null;
    });
    let fixture = parse_completeness_fixture_v1(&bytes).unwrap();
    let report = compose_completeness_reports_v1(&semantic, &payoff, &fixture, 1500).unwrap();
    assert_eq!(
        report.execution().status(),
        ExecutionCompletenessStatusV1::NotObserved
    );
}

#[test]
fn precedence_is_order_invariant_and_expiry_dominates_recovery_failure() {
    let assurance = mutate(|value| {
        value["assurance"]["observations"][0]["verdict"] = json!("unknown");
        value["assurance"]["observations"][1]["verdict"] = json!("fail");
    });
    let mut reordered: Value = serde_json::from_slice(&assurance).unwrap();
    reordered["assurance"]["observations"]
        .as_array_mut()
        .unwrap()
        .reverse();
    let reordered = serde_json::to_vec(&reordered).unwrap();
    assert_eq!(
        composed(&assurance, 1500).assurance().status(),
        AssuranceCompletenessStatusV1::ContradictedInFixture
    );
    assert_eq!(
        composed(&reordered, 1500).assurance().status(),
        AssuranceCompletenessStatusV1::ContradictedInFixture
    );

    let technical_conditional =
        mutate(|value| value["settlement"]["stages"][0]["verdict"] = json!("conditional"));
    assert_eq!(
        composed(&technical_conditional, 1500).settlement().status(),
        SettlementCompletenessStatusV1::PendingInFixture
    );
    let legal_conditional =
        mutate(|value| value["settlement"]["stages"][5]["verdict"] = json!("conditional"));
    assert_eq!(
        composed(&legal_conditional, 1500).settlement().status(),
        SettlementCompletenessStatusV1::ConditionalInFixture
    );
    let unsupported = mutate(|value| value["settlement"]["domains_compatible"] = json!(false));
    assert_eq!(
        composed(&unsupported, 1500).settlement().status(),
        SettlementCompletenessStatusV1::UnsupportedInFixture
    );
    let unknown = mutate(|value| value["settlement"]["reversal_rule"] = Value::Null);
    assert_eq!(
        composed(&unknown, 1500).settlement().status(),
        SettlementCompletenessStatusV1::Unknown
    );
    let disputed_over_unsupported = mutate(|value| {
        value["settlement"]["disputed"] = json!(true);
        value["settlement"]["domains_compatible"] = json!(false);
    });
    assert_eq!(
        composed(&disputed_over_unsupported, 1500)
            .settlement()
            .status(),
        SettlementCompletenessStatusV1::DisputedInFixture
    );
    let unsupported_over_unknown = mutate(|value| {
        value["settlement"]["domains_compatible"] = json!(false);
        value["settlement"]["reversal_rule"] = Value::Null;
    });
    assert_eq!(
        composed(&unsupported_over_unknown, 1500)
            .settlement()
            .status(),
        SettlementCompletenessStatusV1::UnsupportedInFixture
    );
    let unknown_over_pending = mutate(|value| {
        value["settlement"]["reversal_rule"] = Value::Null;
        value["settlement"]["stages"][0]["verdict"] = json!("pending");
    });
    assert_eq!(
        composed(&unknown_over_pending, 1500).settlement().status(),
        SettlementCompletenessStatusV1::Unknown
    );
    let pending_over_conditional = mutate(|value| {
        value["settlement"]["stages"][0]["verdict"] = json!("pending");
        value["settlement"]["stages"][5]["verdict"] = json!("conditional");
    });
    assert_eq!(
        composed(&pending_over_conditional, 1500)
            .settlement()
            .status(),
        SettlementCompletenessStatusV1::PendingInFixture
    );
    assert_eq!(
        composed(FIXTURE, 1500).settlement().status(),
        SettlementCompletenessStatusV1::FinalInFixture
    );

    let stale_failed_recovery = mutate(|value| {
        value["recovery"]["expires_at"] = json!(1499);
        value["recovery"]["evidence_preserved"] = json!("fail");
    });
    assert_eq!(
        composed(&stale_failed_recovery, 1500).recovery().status(),
        RecoveryCompletenessStatusV1::IncompleteOnVersionedFixtureProfile
    );
}

#[test]
fn capital_partial_and_expired_states_are_typed() {
    let partial = mutate(|value| {
        value["capital"]["receipts"][0]["recognized_quantity"] =
            json!({"numerator":"1","denominator":"2"});
    });
    assert_eq!(
        composed(&partial, 1500).capital().status(),
        CapitalCompletenessStatusV1::PartiallyRecognizedInFixture
    );
    let expired = mutate(|value| {
        value["capital"]["expires_at"] = json!(1499);
        bind_capital_context(value);
    });
    assert_eq!(
        composed(&expired, 1500).capital().status(),
        CapitalCompletenessStatusV1::NotEvaluated
    );
}

#[test]
fn assurance_incompleteness_and_malformed_property_cases_fail_closed() {
    let missing_property = mutate(|value| {
        value["assurance"]["observations"]
            .as_array_mut()
            .unwrap()
            .pop();
    });
    assert_eq!(
        composed(&missing_property, 1500).assurance().status(),
        AssuranceCompletenessStatusV1::IncompleteInFixture
    );
    let missing_root = mutate(|value| {
        value["assurance"]["observations"][0]["current_roots"] = json!([]);
    });
    assert_eq!(
        composed(&missing_root, 1500).assurance().status(),
        AssuranceCompletenessStatusV1::IncompleteInFixture
    );
    for flag in ["replayed", "revoked", "superseded", "equivocated"] {
        let bytes = mutate(|value| {
            value["assurance"]["observations"][0][flag] = json!(true);
        });
        assert_eq!(
            composed(&bytes, 1500).assurance().status(),
            AssuranceCompletenessStatusV1::IncompleteInFixture
        );
    }
    let wrong_property = mutate(|value| {
        value["assurance"]["observations"][0]["property"] =
            value["assurance"]["observations"][1]["property"].clone();
    });
    assert!(parse_completeness_fixture_v1(&wrong_property).is_err());
}

#[test]
fn recovery_pause_only_and_control_failures_are_distinct() {
    let pause_only = mutate(|value| {
        value["recovery"]["paths"][0]["capabilities"][0]["verdict"] = json!("unknown");
    });
    let pause_only_report = composed(&pause_only, 1500);
    assert_eq!(
        pause_only_report.recovery().status(),
        RecoveryCompletenessStatusV1::IncompleteOnVersionedFixtureProfile
    );
    assert!(pause_only_report
        .recovery()
        .reasons()
        .contains(&CompletenessReasonV1::MissingRecoveryCapability));
    assert!(pause_only_report
        .recovery()
        .missing_facts()
        .contains(&CompletenessMissingFactV1::RecoveryCapability));
    for field in ["evidence_preserved", "liabilities_duplicate_free"] {
        let unknown = mutate(|value| value["recovery"][field] = json!("unknown"));
        let unknown_report = composed(&unknown, 1500);
        assert_eq!(
            unknown_report.recovery().status(),
            RecoveryCompletenessStatusV1::IncompleteOnVersionedFixtureProfile
        );
        assert!(unknown_report
            .recovery()
            .reasons()
            .contains(&CompletenessReasonV1::MissingRecoveryCapability));
        assert!(unknown_report
            .recovery()
            .missing_facts()
            .contains(&CompletenessMissingFactV1::RecoveryCapability));
    }
    for field in ["evidence_preserved", "liabilities_duplicate_free"] {
        let failed = mutate(|value| value["recovery"][field] = json!("fail"));
        assert_eq!(
            composed(&failed, 1500).recovery().status(),
            RecoveryCompletenessStatusV1::FailedInFixture
        );
    }
    let failed_canary = mutate(|value| value["recovery"]["canary_stages"] = json!(["fail"]));
    assert_eq!(
        composed(&failed_canary, 1500).recovery().status(),
        RecoveryCompletenessStatusV1::FailedInFixture
    );
}

#[test]
fn negative_candidate_requires_sell_execution_and_positive_capital_magnitude() {
    let (semantic, payoff) = reports_with_negative_candidate();
    let subject = derive_analysis_subject_v1(&semantic, &payoff);
    let bytes = mutate(|value| {
        value["execution"]["analysis_subject_digest"] = json!(subject.digest().to_hex());
        value["execution"]["legs"][0]["side"] = json!("sell");
        value["execution"]["legs"][0]["price_bound"] = json!({"numerator":"99","denominator":"1"});
        value["capital"]["analysis_subject_digest"] = json!(subject.digest().to_hex());
        value["settlement"] = Value::Null;
        value["assurance"] = Value::Null;
        value["recovery"] = Value::Null;
        bind_capital_context(value);
    });
    let fixture = parse_completeness_fixture_v1(&bytes).unwrap();
    let report = compose_completeness_reports_v1(&semantic, &payoff, &fixture, 1500).unwrap();
    assert_eq!(
        report.execution().status(),
        ExecutionCompletenessStatusV1::ExecutableInFixture
    );
    assert_eq!(
        report.capital().status(),
        CapitalCompletenessStatusV1::RecognizedInFixture
    );
    assert_eq!(
        report.capital().receipts()[0].required_quantity(),
        rational(-1, 1)
    );
    assert_eq!(
        report.capital().receipts()[0].recognized_quantity(),
        rational(1, 1)
    );
}

#[test]
fn exact_arithmetic_overflow_emits_no_report() {
    let largest = i128::MAX.to_string();
    let bytes = mutate(|value| {
        for field in ["reference_price", "price_bound", "maximum_fee"] {
            value["execution"]["legs"][0][field]["numerator"] = json!(largest);
        }
        value["execution"]["legs"][0]["levels"][0]["price"]["numerator"] = json!(largest);
    });
    let (semantic, payoff) = reports();
    let fixture = parse_completeness_fixture_v1(&bytes).unwrap();
    assert!(compose_completeness_reports_v1(&semantic, &payoff, &fixture, 1500).is_err());
}

#[test]
fn new_public_facts_are_canonical_identity_bearing() {
    let baseline = composed(FIXTURE, 1500);
    let execution = mutate(|value| {
        value["execution"]["legs"][0]["reference_price"] =
            json!({"numerator":"99","denominator":"1"})
    });
    assert_ne!(
        baseline.execution().report_digest(),
        composed(&execution, 1500).execution().report_digest()
    );
    let capital = mutate(|value| {
        value["capital"]["receipts"][0]["recognized_quantity"] =
            json!({"numerator":"1","denominator":"2"})
    });
    assert_ne!(
        baseline.capital().report_digest(),
        composed(&capital, 1500).capital().report_digest()
    );
    let settlement = mutate(|value| value["settlement"]["reversal_rule"] = json!("different-rule"));
    assert_ne!(
        baseline.settlement().report_digest(),
        composed(&settlement, 1500).settlement().report_digest()
    );
    let assurance = mutate(|value| value["assurance"]["nonce"] = json!("different-nonce"));
    assert_ne!(
        baseline.assurance().report_digest(),
        composed(&assurance, 1500).assurance().report_digest()
    );
    let recovery = mutate(|value| {
        value["recovery"]["liability_after_digest"] =
            json!("8888888888888888888888888888888888888888888888888888888888888888")
    });
    assert_ne!(
        baseline.recovery().report_digest(),
        composed(&recovery, 1500).recovery().report_digest()
    );
}

#[test]
fn each_dimension_mutation_is_digest_isolated_from_the_other_four() {
    let baseline = composed(FIXTURE, 1500);
    let mutations = [
        mutate(|value| {
            value["execution"]["legs"][0]["reference_price"] =
                json!({"numerator":"99","denominator":"1"})
        }),
        mutate(|value| {
            value["capital"]["receipts"][0]["recognized_quantity"] =
                json!({"numerator":"1","denominator":"2"})
        }),
        mutate(|value| value["settlement"]["reversal_rule"] = json!("other-reversal-rule")),
        mutate(|value| value["assurance"]["nonce"] = json!("other-nonce")),
        mutate(|value| {
            value["recovery"]["liability_after_digest"] =
                json!("8888888888888888888888888888888888888888888888888888888888888888")
        }),
    ];
    let expected = [
        baseline.execution().report_digest(),
        baseline.capital().report_digest(),
        baseline.settlement().report_digest(),
        baseline.assurance().report_digest(),
        baseline.recovery().report_digest(),
    ];
    let expected_bytes = [
        serde_json::to_vec(baseline.execution()).unwrap(),
        serde_json::to_vec(baseline.capital()).unwrap(),
        serde_json::to_vec(baseline.settlement()).unwrap(),
        serde_json::to_vec(baseline.assurance()).unwrap(),
        serde_json::to_vec(baseline.recovery()).unwrap(),
    ];
    for (owned, bytes) in mutations.iter().enumerate() {
        let changed = composed(bytes, 1500);
        let actual = [
            changed.execution().report_digest(),
            changed.capital().report_digest(),
            changed.settlement().report_digest(),
            changed.assurance().report_digest(),
            changed.recovery().report_digest(),
        ];
        let actual_bytes = [
            serde_json::to_vec(changed.execution()).unwrap(),
            serde_json::to_vec(changed.capital()).unwrap(),
            serde_json::to_vec(changed.settlement()).unwrap(),
            serde_json::to_vec(changed.assurance()).unwrap(),
            serde_json::to_vec(changed.recovery()).unwrap(),
        ];
        for index in 0..5 {
            if index == owned {
                assert_ne!(actual[index], expected[index]);
            } else {
                assert_eq!(actual[index], expected[index]);
                assert_eq!(actual_bytes[index], expected_bytes[index]);
            }
        }
    }
}

#[test]
fn capital_context_binding_rejects_each_material_statement_mismatch() {
    let mutations: Vec<Vec<u8>> = vec![
        mutate(|value| value["capital"]["authority_id"] = json!("other-authority")),
        mutate(|value| value["capital"]["eligible_account"] = json!("other-account")),
        mutate(|value| value["capital"]["model_id"] = json!("other-model")),
        mutate(|value| value["capital"]["model_version"] = json!(2)),
        mutate(|value| {
            value["capital"]["model_digest"] =
                json!("7777777777777777777777777777777777777777777777777777777777777777")
        }),
        mutate(|value| value["capital"]["haircut"] = json!({"numerator":"1","denominator":"10"})),
        mutate(|value| value["capital"]["margin_rule_id"] = json!("other-rule")),
        mutate(|value| value["capital"]["jurisdiction"] = json!("other-jurisdiction")),
        mutate(|value| value["capital"]["liquidation_horizon_seconds"] = json!(7200)),
        mutate(|value| value["capital"]["observed_at"] = json!(1001)),
        mutate(|value| value["capital"]["expires_at"] = json!(2001)),
    ];
    let (semantic, payoff) = reports();
    for bytes in mutations {
        let fixture = parse_completeness_fixture_v1(&bytes).unwrap();
        assert!(compose_completeness_reports_v1(&semantic, &payoff, &fixture, 1500).is_err());
    }
}

#[test]
fn strict_digest_and_resource_bounds_fail_closed() {
    let uppercase = mutate(|value| {
        value["capital"]["model_digest"] =
            json!("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    });
    assert!(parse_completeness_fixture_v1(&uppercase).is_err());
    for invalid in [
        "".to_owned(),
        "non ascii".to_owned(),
        "line\nbreak".to_owned(),
        "é".to_owned(),
        "x".repeat(129),
    ] {
        let bytes = mutate(|value| value["execution"]["venue_id"] = json!(invalid));
        assert!(parse_completeness_fixture_v1(&bytes).is_err());
    }
    for invalid in ["0".to_owned(), "g".repeat(64)] {
        let bytes = mutate(|value| value["capital"]["model_digest"] = json!(invalid));
        assert!(parse_completeness_fixture_v1(&bytes).is_err());
    }
    let denied_nonzero =
        mutate(|value| value["capital"]["receipts"][0]["verdict"] = json!("denied"));
    assert!(parse_completeness_fixture_v1(&denied_nonzero).is_err());
    let mut exact_limit: Value = serde_json::from_slice(FIXTURE).unwrap();
    let prototype = exact_limit["execution"]["legs"][0].clone();
    let mut legs = Vec::new();
    for index in 0..64_u64 {
        let mut leg = prototype.clone();
        leg["leg_id"] = json!(format!("leg-{index}"));
        leg["state_key"] = json!(format!("{index:064x}"));
        legs.push(leg);
    }
    exact_limit["execution"]["legs"] = Value::Array(legs.clone());
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&exact_limit).unwrap()).is_ok());
    let mut over = prototype;
    over["leg_id"] = json!("leg-64");
    over["state_key"] = json!(format!("{:064x}", 64_u64));
    legs.push(over);
    exact_limit["execution"]["legs"] = Value::Array(legs);
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&exact_limit).unwrap()).is_err());
    let mut exact_bytes = FIXTURE.to_vec();
    exact_bytes.resize(statebook_settlement::MAX_FIXTURE_BYTES_V1, b' ');
    assert!(parse_completeness_fixture_v1(&exact_bytes).is_ok());
    exact_bytes.push(b' ');
    assert!(parse_completeness_fixture_v1(&exact_bytes).is_err());
}

#[test]
fn every_reachable_exact_resource_limit_and_each_plus_one_are_enforced() {
    let mut value: Value = serde_json::from_slice(FIXTURE).unwrap();
    let level = value["execution"]["legs"][0]["levels"][0].clone();
    let levels: Vec<_> = (0..64_u64)
        .map(|index| {
            let mut item = level.clone();
            item["level_id"] = json!(format!("level-{index}"));
            item
        })
        .collect();
    value["execution"]["legs"][0]["levels"] = Value::Array(levels.clone());
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_ok());
    let mut over_levels = levels;
    let mut extra_level = level;
    extra_level["level_id"] = json!("level-64");
    over_levels.push(extra_level);
    value["execution"]["legs"][0]["levels"] = Value::Array(over_levels);
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_err());

    let mut value: Value = serde_json::from_slice(FIXTURE).unwrap();
    let receipt = value["capital"]["receipts"][0].clone();
    let receipts: Vec<_> = (0..64_u64)
        .map(|index| {
            let mut item = receipt.clone();
            item["state_key"] = json!(format!("{index:064x}"));
            item
        })
        .collect();
    value["capital"]["receipts"] = Value::Array(receipts.clone());
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_ok());
    let mut over_receipts = receipts;
    let mut extra_receipt = receipt;
    extra_receipt["state_key"] = json!(format!("{:064x}", 64_u64));
    over_receipts.push(extra_receipt);
    value["capital"]["receipts"] = Value::Array(over_receipts);
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_err());

    let mut value: Value = serde_json::from_slice(FIXTURE).unwrap();
    let stage_set = value["settlement"]["stages"].as_array().unwrap().clone();
    let stages: Vec<_> = (0..64_u64)
        .flat_map(|index| {
            stage_set.iter().cloned().map(move |mut item| {
                item["obligation_id"] = json!(format!("obligation-{index}"));
                item
            })
        })
        .collect();
    value["settlement"]["stages"] = Value::Array(stages.clone());
    assert_eq!(
        value["settlement"]["stages"].as_array().unwrap().len(),
        64 * 6
    );
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_ok());
    let mut over_stages = stages;
    over_stages.extend(stage_set.into_iter().map(|mut item| {
        item["obligation_id"] = json!("obligation-64");
        item
    }));
    value["settlement"]["stages"] = Value::Array(over_stages);
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_err());

    let mut value: Value = serde_json::from_slice(FIXTURE).unwrap();
    assert_eq!(
        value["assurance"]["observations"].as_array().unwrap().len(),
        statebook_settlement::ASSURANCE_PROPERTY_COUNT_V1
    );
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_ok());
    let duplicate_observation = value["assurance"]["observations"][0].clone();
    value["assurance"]["observations"]
        .as_array_mut()
        .unwrap()
        .push(duplicate_observation);
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_err());

    let mut value: Value = serde_json::from_slice(FIXTURE).unwrap();
    assert_eq!(
        value["recovery"]["paths"].as_array().unwrap().len(),
        statebook_settlement::RECOVERY_PATH_COUNT_V1
    );
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_ok());
    let duplicate_path = value["recovery"]["paths"][0].clone();
    value["recovery"]["paths"]
        .as_array_mut()
        .unwrap()
        .push(duplicate_path);
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_err());

    let mut value: Value = serde_json::from_slice(FIXTURE).unwrap();
    let root = value["assurance"]["observations"][0]["current_roots"][0].clone();
    let roots: Vec<_> = (0..32_u64)
        .map(|index| {
            let mut item = root.clone();
            item["root_id"] = json!(format!("root-{index}"));
            item
        })
        .collect();
    value["assurance"]["observations"][0]["current_roots"] = Value::Array(roots.clone());
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_ok());
    let mut over_roots = roots;
    let mut extra_root = root;
    extra_root["root_id"] = json!("root-32");
    over_roots.push(extra_root);
    value["assurance"]["observations"][0]["current_roots"] = Value::Array(over_roots);
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_err());

    let mut value: Value = serde_json::from_slice(FIXTURE).unwrap();
    let root = value["assurance"]["observations"][0]["dependency_roots"][0].clone();
    let roots: Vec<_> = (0..32_u64)
        .map(|index| {
            let mut item = root.clone();
            item["root_id"] = json!(format!("dependency-root-{index}"));
            item
        })
        .collect();
    value["assurance"]["observations"][0]["dependency_roots"] = Value::Array(roots.clone());
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_ok());
    let mut over_roots = roots;
    let mut extra_root = root;
    extra_root["root_id"] = json!("dependency-root-32");
    over_roots.push(extra_root);
    value["assurance"]["observations"][0]["dependency_roots"] = Value::Array(over_roots);
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_err());

    let mut value: Value = serde_json::from_slice(FIXTURE).unwrap();
    let item = value["recovery"]["in_flight_items"][0].clone();
    let items: Vec<_> = (0..256_u64)
        .map(|index| {
            let mut entry = item.clone();
            entry["item_id"] = json!(format!("item-{index}"));
            entry
        })
        .collect();
    value["recovery"]["in_flight_items"] = Value::Array(items.clone());
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_ok());
    let mut over_items = items;
    let mut extra_item = item;
    extra_item["item_id"] = json!("item-256");
    over_items.push(extra_item);
    value["recovery"]["in_flight_items"] = Value::Array(over_items);
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_err());

    let mut value: Value = serde_json::from_slice(FIXTURE).unwrap();
    value["recovery"]["canary_stages"] = Value::Array(vec![json!("pass"); 16]);
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_ok());
    value["recovery"]["canary_stages"] = Value::Array(vec![json!("pass"); 17]);
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_err());

    let mut value: Value = serde_json::from_slice(FIXTURE).unwrap();
    let evidence: Vec<_> = (0..256_u64)
        .map(|index| json!(format!("{index:064x}")))
        .collect();
    value["execution"]["source_evidence_digests"] = Value::Array(evidence.clone());
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_ok());
    let mut over_evidence = evidence;
    over_evidence.push(json!(format!("{:064x}", 256_u64)));
    value["execution"]["source_evidence_digests"] = Value::Array(over_evidence);
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_err());

    let mut value: Value = serde_json::from_slice(FIXTURE).unwrap();
    let leg = value["execution"]["legs"][0].clone();
    let level = leg["levels"][0].clone();
    let full_levels: Vec<_> = (0..64_u64)
        .map(|index| {
            let mut entry = level.clone();
            entry["level_id"] = json!(format!("level-{index}"));
            entry
        })
        .collect();
    let full_legs: Vec<_> = (0..64_u64)
        .map(|index| {
            let mut entry = leg.clone();
            entry["leg_id"] = json!(format!("leg-{index}"));
            entry["state_key"] = json!(format!("{index:064x}"));
            entry["levels"] = Value::Array(full_levels.clone());
            entry
        })
        .collect();
    value["execution"]["legs"] = Value::Array(full_legs);
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_ok());
    let mut extra_level = level;
    extra_level["level_id"] = json!("level-64");
    value["execution"]["legs"][0]["levels"]
        .as_array_mut()
        .unwrap()
        .push(extra_level);
    assert!(parse_completeness_fixture_v1(&serde_json::to_vec(&value).unwrap()).is_err());
}

mod independent_canonical {
    use super::*;
    use ring::digest::{digest as ring_digest, SHA256};
    use statebook_settlement::{
        AssurancePropertyV1, AssuranceVerdictV1, CompletenessAssumptionV1, CompletenessDimensionV1,
        CompletenessMissingFactV1, CompletenessReasonV1, DependencyDisclosureV1, DigestV1,
        FixtureSupportV1, RecoveryCapabilityV1, RootClassV1, SettlementStageV1,
        SevenCompletenessReportsV1,
    };

    fn record(fields: impl IntoIterator<Item = (u16, Vec<u8>)>) -> Vec<u8> {
        let mut output = Vec::new();
        for (tag, value) in fields {
            output.extend_from_slice(&tag.to_be_bytes());
            output.extend_from_slice(&(value.len() as u32).to_be_bytes());
            output.extend_from_slice(&value);
        }
        output
    }

    fn sequence(values: impl IntoIterator<Item = Vec<u8>>) -> Vec<u8> {
        let values: Vec<_> = values.into_iter().collect();
        let mut output = Vec::new();
        output.extend_from_slice(&(values.len() as u32).to_be_bytes());
        for value in values {
            output.extend_from_slice(&(value.len() as u32).to_be_bytes());
            output.extend_from_slice(&value);
        }
        output
    }

    fn rational(value: SignedRational) -> Vec<u8> {
        [
            value.numerator().to_be_bytes().as_slice(),
            value.denominator().to_be_bytes().as_slice(),
        ]
        .concat()
    }

    fn optional_rational(value: Option<SignedRational>) -> Vec<u8> {
        value.map_or_else(
            || vec![0],
            |value| {
                let mut output = vec![1];
                output.extend_from_slice(&rational(value));
                output
            },
        )
    }

    fn optional_digest(value: Option<DigestV1>) -> Vec<u8> {
        value.map_or_else(
            || vec![0],
            |value| {
                let mut output = vec![1];
                output.extend_from_slice(value.as_bytes());
                output
            },
        )
    }

    fn optional_i64(value: Option<i64>) -> Vec<u8> {
        value.map_or_else(
            || vec![0],
            |value| {
                let mut output = vec![1];
                output.extend_from_slice(&value.to_be_bytes());
                output
            },
        )
    }

    fn optional_string(value: Option<&str>) -> Vec<u8> {
        value.map_or_else(
            || vec![0],
            |value| {
                let mut output = vec![1];
                output.extend_from_slice(&(value.len() as u32).to_be_bytes());
                output.extend_from_slice(value.as_bytes());
                output
            },
        )
    }

    fn present(value: Vec<u8>) -> Vec<u8> {
        let mut output = vec![1];
        output.extend_from_slice(&value);
        output
    }

    fn ring_sha256(domain: &[u8], payload: &[u8]) -> String {
        let mut input = Vec::new();
        input.extend_from_slice(domain);
        input.extend_from_slice(&1_u16.to_be_bytes());
        input.extend_from_slice(payload);
        hex::encode(ring_digest(&SHA256, &input).as_ref())
    }

    fn dimension_tag(value: CompletenessDimensionV1) -> u8 {
        match value {
            CompletenessDimensionV1::Execution => 1,
            CompletenessDimensionV1::Capital => 2,
            CompletenessDimensionV1::Settlement => 3,
            CompletenessDimensionV1::Assurance => 4,
            CompletenessDimensionV1::Recovery => 5,
        }
    }

    fn assumption_tag(value: CompletenessAssumptionV1) -> u8 {
        match value {
            CompletenessAssumptionV1::HermeticFixtureOnly => 1,
            CompletenessAssumptionV1::NoLiveAuthority => 2,
            CompletenessAssumptionV1::NoCrossDimensionInference => 3,
            CompletenessAssumptionV1::FixedWidthExactArithmetic => 4,
            CompletenessAssumptionV1::CurrentRootsDisclosedNotResolved => 5,
            CompletenessAssumptionV1::VersionedRecoveryProfileOnly => 6,
        }
    }

    fn reason_tag(value: CompletenessReasonV1) -> u8 {
        match value {
            CompletenessReasonV1::MissingFixture => 1,
            CompletenessReasonV1::StaleOrFutureObservation => 2,
            CompletenessReasonV1::MissingObservation => 3,
            CompletenessReasonV1::ExplicitlyUnsupported => 4,
            CompletenessReasonV1::PartialQuantity => 5,
            CompletenessReasonV1::ZeroExecutableQuantity => 6,
            CompletenessReasonV1::ExplicitDenial => 7,
            CompletenessReasonV1::PartialRecognition => 8,
            CompletenessReasonV1::DisputedOrReversed => 9,
            CompletenessReasonV1::IncompatibleFinalityDomain => 10,
            CompletenessReasonV1::PendingStage => 11,
            CompletenessReasonV1::ConditionalLegalFinality => 12,
            CompletenessReasonV1::MissingAssuranceProperty => 13,
            CompletenessReasonV1::UnknownAssuranceVerdict => 14,
            CompletenessReasonV1::MissingCurrentRoot => 15,
            CompletenessReasonV1::UnknownDependencyAncestry => 16,
            CompletenessReasonV1::ReplayOrRevocationState => 17,
            CompletenessReasonV1::ExplicitAssuranceFailure => 18,
            CompletenessReasonV1::MissingRecoveryPath => 19,
            CompletenessReasonV1::MissingRecoveryCapability => 20,
            CompletenessReasonV1::RecoveryControlFailure => 21,
            CompletenessReasonV1::ReconciliationMismatch => 22,
            CompletenessReasonV1::EvidenceLoss => 23,
            CompletenessReasonV1::DuplicateLiability => 24,
            CompletenessReasonV1::MissingOrFailedCanary => 25,
        }
    }

    fn missing_fact_tag(value: CompletenessMissingFactV1) -> u8 {
        match value {
            CompletenessMissingFactV1::Fixture => 1,
            CompletenessMissingFactV1::CurrentObservation => 2,
            CompletenessMissingFactV1::RequiredExecutionLeg => 3,
            CompletenessMissingFactV1::RequiredCapitalReceipt => 4,
            CompletenessMissingFactV1::SettlementPolicyOrStage => 5,
            CompletenessMissingFactV1::AssuranceProperty => 6,
            CompletenessMissingFactV1::CurrentAssuranceRoot => 7,
            CompletenessMissingFactV1::DependencyAncestry => 8,
            CompletenessMissingFactV1::RecoveryPath => 9,
            CompletenessMissingFactV1::RecoveryCapability => 10,
            CompletenessMissingFactV1::InFlightReconciliation => 11,
            CompletenessMissingFactV1::CanaryStage => 12,
        }
    }

    fn assurance_property_tag(value: AssurancePropertyV1) -> u8 {
        match value {
            AssurancePropertyV1::ActionAuthorization => 1,
            AssurancePropertyV1::SourceAuthenticityAndFreshness => 2,
            AssurancePropertyV1::CalculationIntegrity => 3,
            AssurancePropertyV1::StateTransitionIntegrity => 4,
            AssurancePropertyV1::SolvencyAndLiquidResourceSupport => 5,
            AssurancePropertyV1::DestinationAndRoutePolicy => 6,
            AssurancePropertyV1::AnomalyAndEmergencyClearance => 7,
            AssurancePropertyV1::EvidenceRootDisclosure => 8,
            AssurancePropertyV1::FinancialBasisBinding => 9,
        }
    }

    fn verdict_tag(value: AssuranceVerdictV1) -> u8 {
        match value {
            AssuranceVerdictV1::Pass => 1,
            AssuranceVerdictV1::Fail => 2,
            AssuranceVerdictV1::Unknown => 3,
        }
    }

    fn root_class_tag(value: RootClassV1) -> u8 {
        match value {
            RootClassV1::Data => 1,
            RootClassV1::Operator => 2,
            RootClassV1::Cloud => 3,
            RootClassV1::Kms => 4,
            RootClassV1::Rpc => 5,
            RootClassV1::CiCd => 6,
            RootClassV1::Model => 7,
            RootClassV1::Signer => 8,
        }
    }

    fn capability_tag(value: RecoveryCapabilityV1) -> u8 {
        match value {
            RecoveryCapabilityV1::StopExternalization => 1,
            RecoveryCapabilityV1::ReconcileEveryInFlightItem => 2,
            RecoveryCapabilityV1::PreserveEvidence => 3,
            RecoveryCapabilityV1::RestoreLiabilitiesWithoutDuplication => 4,
            RecoveryCapabilityV1::ReopenThroughBoundedCanaryStages => 5,
        }
    }

    fn stage_tag(value: SettlementStageV1) -> u8 {
        match value {
            SettlementStageV1::SourceObservation => 1,
            SettlementStageV1::SourceFinality => 2,
            SettlementStageV1::DestinationObservation => 3,
            SettlementStageV1::DestinationFinality => 4,
            SettlementStageV1::OperationalReconciliation => 5,
            SettlementStageV1::LegalFinality => 6,
        }
    }

    fn support_tag(value: FixtureSupportV1) -> u8 {
        match value {
            FixtureSupportV1::Supported => 1,
            FixtureSupportV1::Unsupported => 2,
            FixtureSupportV1::Unknown => 3,
        }
    }

    fn enum_set(values: impl IntoIterator<Item = u8>) -> Vec<u8> {
        sequence(values.into_iter().map(|value| vec![value]))
    }

    fn digest_set<'a>(values: impl IntoIterator<Item = &'a DigestV1>) -> Vec<u8> {
        sequence(values.into_iter().map(|value| value.as_bytes().to_vec()))
    }

    fn meta<R>(report: &R) -> Vec<u8>
    where
        R: ReportView,
    {
        record([
            (1, report.schema_version().to_be_bytes().to_vec()),
            (2, vec![dimension_tag(report.dimension())]),
            (3, report.analysis_subject_digest().as_bytes().to_vec()),
            (4, optional_digest(report.fixture_digest())),
            (5, vec![1]),
            (6, digest_set(report.source_evidence_digests())),
            (
                7,
                enum_set(
                    report
                        .assumptions()
                        .iter()
                        .map(|value| assumption_tag(*value)),
                ),
            ),
            (
                8,
                enum_set(report.reasons().iter().map(|value| reason_tag(*value))),
            ),
            (9, report.evaluated_at().to_be_bytes().to_vec()),
            (10, optional_i64(report.expires_at())),
            (
                11,
                enum_set(
                    report
                        .missing_facts()
                        .iter()
                        .map(|value| missing_fact_tag(*value)),
                ),
            ),
        ])
    }

    trait ReportView {
        fn schema_version(&self) -> u16;
        fn dimension(&self) -> CompletenessDimensionV1;
        fn analysis_subject_digest(&self) -> DigestV1;
        fn fixture_digest(&self) -> Option<DigestV1>;
        fn source_evidence_digests(&self) -> &std::collections::BTreeSet<DigestV1>;
        fn assumptions(&self) -> &std::collections::BTreeSet<CompletenessAssumptionV1>;
        fn reasons(&self) -> &std::collections::BTreeSet<CompletenessReasonV1>;
        fn missing_facts(&self) -> &std::collections::BTreeSet<CompletenessMissingFactV1>;
        fn evaluated_at(&self) -> i64;
        fn expires_at(&self) -> Option<i64>;
    }

    macro_rules! report_view {
        ($type:ty) => {
            impl ReportView for $type {
                fn schema_version(&self) -> u16 {
                    self.schema_version()
                }
                fn dimension(&self) -> CompletenessDimensionV1 {
                    self.dimension()
                }
                fn analysis_subject_digest(&self) -> DigestV1 {
                    self.analysis_subject_digest()
                }
                fn fixture_digest(&self) -> Option<DigestV1> {
                    self.fixture_digest()
                }
                fn source_evidence_digests(&self) -> &std::collections::BTreeSet<DigestV1> {
                    self.source_evidence_digests()
                }
                fn assumptions(&self) -> &std::collections::BTreeSet<CompletenessAssumptionV1> {
                    self.assumptions()
                }
                fn reasons(&self) -> &std::collections::BTreeSet<CompletenessReasonV1> {
                    self.reasons()
                }
                fn missing_facts(&self) -> &std::collections::BTreeSet<CompletenessMissingFactV1> {
                    self.missing_facts()
                }
                fn evaluated_at(&self) -> i64 {
                    self.evaluated_at()
                }
                fn expires_at(&self) -> Option<i64> {
                    self.expires_at()
                }
            }
        };
    }

    report_view!(statebook_settlement::ExecutionCompletenessReportV1);
    report_view!(statebook_settlement::CapitalCompletenessReportV1);
    report_view!(statebook_settlement::SettlementCompletenessReportV1);
    report_view!(statebook_settlement::AssuranceCompletenessReportV1);
    report_view!(statebook_settlement::RecoveryCompletenessReportV1);

    fn receipt(value: &statebook_core::AggregatedPositionReceiptV1) -> Vec<u8> {
        record([
            (1, value.state_key().digest().as_bytes().to_vec()),
            (
                2,
                sequence(
                    value
                        .validated_contract_digests()
                        .iter()
                        .map(|digest| digest.as_bytes().to_vec()),
                ),
            ),
            (3, rational(value.quantity())),
        ])
    }

    fn subject(report: &SevenCompletenessReportsV1) -> Vec<u8> {
        record([
            (1, report.semantic_report_digest().as_bytes().to_vec()),
            (2, receipt(report.payoff().target())),
            (3, sequence(report.payoff().candidate().iter().map(receipt))),
            (4, report.payoff().domain_digest().as_bytes().to_vec()),
            (5, report.payoff_report_digest().as_bytes().to_vec()),
        ])
    }

    fn profile(profile: &RecoveryPathProfileV1) -> Vec<u8> {
        record([
            (1, profile.schema_version().to_be_bytes().to_vec()),
            (2, profile.profile_id().as_bytes().to_vec()),
            (3, profile.profile_version().to_be_bytes().to_vec()),
            (
                4,
                sequence(
                    profile
                        .required_path_ids()
                        .iter()
                        .map(|value| value.as_bytes().to_vec()),
                ),
            ),
            (
                5,
                enum_set(
                    profile
                        .required_capabilities()
                        .iter()
                        .map(|value| capability_tag(*value)),
                ),
            ),
        ])
    }

    fn execution(report: &SevenCompletenessReportsV1) -> Vec<u8> {
        let report = report.execution();
        record([
            (1, meta(report)),
            (2, vec![1]),
            (
                3,
                sequence(report.legs().iter().map(|leg| {
                    record([
                        (1, leg.leg_id().as_bytes().to_vec()),
                        (2, leg.asset().as_bytes().to_vec()),
                        (3, rational(leg.requested_quantity())),
                        (4, rational(leg.executable_quantity())),
                        (5, rational(leg.unfilled_quantity())),
                        (6, rational(leg.gross_notional())),
                        (7, optional_rational(leg.average_price())),
                        (8, optional_rational(leg.worst_price())),
                        (9, rational(leg.fee())),
                        (10, optional_rational(leg.slippage())),
                        (11, vec![support_tag(leg.queue())]),
                        (12, vec![support_tag(leg.atomicity())]),
                        (13, vec![support_tag(leg.leg_failure_model())]),
                        (14, leg.deadline().to_be_bytes().to_vec()),
                        (15, vec![1]),
                        (16, rational(leg.reference_price())),
                        (17, rational(leg.price_bound())),
                        (18, rational(leg.fee_rate())),
                        (19, rational(leg.maximum_fee())),
                        (20, rational(leg.maximum_slippage())),
                    ])
                })),
            ),
            (
                4,
                present(record([
                    (1, report.context().unwrap().venue_id().as_bytes().to_vec()),
                    (
                        2,
                        report.context().unwrap().account_id().as_bytes().to_vec(),
                    ),
                    (
                        3,
                        report
                            .context()
                            .unwrap()
                            .observed_at()
                            .to_be_bytes()
                            .to_vec(),
                    ),
                ])),
            ),
        ])
    }

    fn capital(report: &SevenCompletenessReportsV1) -> Vec<u8> {
        let report = report.capital();
        let context = report.context().unwrap();
        record([
            (1, meta(report)),
            (2, vec![1]),
            (
                3,
                sequence(report.receipts().iter().map(|receipt| {
                    record([
                        (1, receipt.state_key().digest().as_bytes().to_vec()),
                        (2, rational(receipt.required_quantity())),
                        (3, rational(receipt.recognized_quantity())),
                        (4, vec![1]),
                        (5, rational(receipt.recognition_residual())),
                        (6, receipt.capital_context_digest().as_bytes().to_vec()),
                    ])
                })),
            ),
            (
                4,
                present(record([
                    (1, context.authority_id().as_bytes().to_vec()),
                    (2, context.eligible_account().as_bytes().to_vec()),
                    (3, context.model_id().as_bytes().to_vec()),
                    (4, context.model_version().to_be_bytes().to_vec()),
                    (5, context.model_digest().as_bytes().to_vec()),
                    (6, rational(context.haircut())),
                    (7, context.margin_rule_id().as_bytes().to_vec()),
                    (8, context.jurisdiction().as_bytes().to_vec()),
                    (
                        9,
                        context.liquidation_horizon_seconds().to_be_bytes().to_vec(),
                    ),
                    (10, context.observed_at().to_be_bytes().to_vec()),
                    (11, context.capital_context_digest().as_bytes().to_vec()),
                ])),
            ),
        ])
    }

    fn settlement(report: &SevenCompletenessReportsV1) -> Vec<u8> {
        let report = report.settlement();
        let context = report.context().unwrap();
        record([
            (1, meta(report)),
            (2, vec![1]),
            (
                3,
                sequence(report.stages().iter().map(|stage| {
                    record([
                        (1, stage.obligation_id().as_bytes().to_vec()),
                        (2, vec![stage_tag(stage.stage())]),
                        (3, vec![1]),
                    ])
                })),
            ),
            (
                4,
                present(record([
                    (1, context.source_finality_domain().as_bytes().to_vec()),
                    (2, context.destination_finality_domain().as_bytes().to_vec()),
                    (3, optional_string(context.reversal_rule())),
                    (4, optional_string(context.insolvency_rule())),
                    (5, vec![u8::from(context.disputed())]),
                    (6, vec![u8::from(context.reversed())]),
                    (7, vec![u8::from(context.reconciliation_mismatch())]),
                    (8, vec![u8::from(context.domains_compatible())]),
                    (9, vec![u8::from(context.transition_supported())]),
                    (10, context.observed_at().to_be_bytes().to_vec()),
                ])),
            ),
        ])
    }

    fn root_set<'a>(
        roots: impl IntoIterator<Item = &'a statebook_settlement::AssuranceRootV1>,
    ) -> Vec<u8> {
        sequence(roots.into_iter().map(|root| {
            record([
                (1, vec![root_class_tag(root.root_class())]),
                (2, root.root_id().as_bytes().to_vec()),
            ])
        }))
    }

    fn assurance(report: &SevenCompletenessReportsV1) -> Vec<u8> {
        let report = report.assurance();
        let context = report.context().unwrap();
        record([
            (1, meta(report)),
            (2, vec![1]),
            (
                3,
                sequence(report.properties().iter().map(|property| {
                    record([
                        (1, vec![assurance_property_tag(property.property())]),
                        (2, vec![verdict_tag(property.verdict())]),
                        (3, root_set(property.current_roots())),
                        (4, root_set(property.dependency_roots())),
                        (
                            5,
                            vec![match property.dependency_disclosure() {
                                DependencyDisclosureV1::Complete => 1,
                                DependencyDisclosureV1::Unknown => 2,
                            }],
                        ),
                        (6, vec![u8::from(property.replayed())]),
                        (7, vec![u8::from(property.revoked())]),
                        (8, vec![u8::from(property.superseded())]),
                        (9, vec![u8::from(property.equivocated())]),
                    ])
                })),
            ),
            (
                4,
                present(record([
                    (1, context.issuer_id().as_bytes().to_vec()),
                    (2, context.subject_id().as_bytes().to_vec()),
                    (3, context.scope_digest().as_bytes().to_vec()),
                    (4, context.nonce().as_bytes().to_vec()),
                    (5, context.observed_at().to_be_bytes().to_vec()),
                ])),
            ),
        ])
    }

    fn recovery(report: &SevenCompletenessReportsV1) -> Vec<u8> {
        let report = report.recovery();
        let context = report.context().unwrap();
        record([
            (1, meta(report)),
            (2, vec![1]),
            (
                3,
                sequence(report.paths().iter().map(|path| {
                    record([
                        (1, path.path_id().as_bytes().to_vec()),
                        (
                            2,
                            sequence(path.capabilities().iter().map(|(capability, verdict)| {
                                vec![capability_tag(*capability), verdict_tag(*verdict)]
                            })),
                        ),
                    ])
                })),
            ),
            (
                4,
                present(record([
                    (
                        1,
                        sequence(context.in_flight_items().iter().map(|item| {
                            record([
                                (1, item.item_id().as_bytes().to_vec()),
                                (2, item.expected_digest().as_bytes().to_vec()),
                                (3, item.observed_digest().as_bytes().to_vec()),
                            ])
                        })),
                    ),
                    (2, vec![verdict_tag(context.evidence_preserved())]),
                    (3, vec![verdict_tag(context.liabilities_duplicate_free())]),
                    (
                        4,
                        sequence(
                            context
                                .canary_stages()
                                .iter()
                                .map(|value| vec![verdict_tag(*value)]),
                        ),
                    ),
                    (5, context.observed_at().to_be_bytes().to_vec()),
                    (6, context.evidence_preservation_ref().as_bytes().to_vec()),
                    (7, context.liability_before_digest().as_bytes().to_vec()),
                    (8, context.liability_after_digest().as_bytes().to_vec()),
                ])),
            ),
        ])
    }

    fn composition(report: &SevenCompletenessReportsV1) -> Vec<u8> {
        record([
            (1, report.analysis_subject().digest().as_bytes().to_vec()),
            (2, report.evaluated_at().to_be_bytes().to_vec()),
            (3, report.recovery_profile_digest().as_bytes().to_vec()),
            (4, report.semantic_report_digest().as_bytes().to_vec()),
            (5, report.payoff_report_digest().as_bytes().to_vec()),
            (6, report.execution().report_digest().as_bytes().to_vec()),
            (7, report.capital().report_digest().as_bytes().to_vec()),
            (8, report.settlement().report_digest().as_bytes().to_vec()),
            (9, report.assurance().report_digest().as_bytes().to_vec()),
            (10, report.recovery().report_digest().as_bytes().to_vec()),
        ])
    }

    fn semantic(report: &SevenCompletenessReportsV1) -> Vec<u8> {
        let report = report.semantic();
        record([
            (
                1,
                vec![match report.status() {
                    statebook_core::SemanticCompletenessStatus::Complete => 1,
                    statebook_core::SemanticCompletenessStatus::Incomplete => 2,
                    statebook_core::SemanticCompletenessStatus::Unknown => 3,
                }],
            ),
            (2, enum_set(std::iter::empty())),
            (3, enum_set(std::iter::empty())),
            (4, sequence(std::iter::empty())),
            (5, report.source_terms_digest().as_bytes().to_vec()),
            (6, report.normalization_profile_digest().as_bytes().to_vec()),
        ])
    }

    fn payoff(report: &SevenCompletenessReportsV1) -> Vec<u8> {
        let report = report.payoff();
        let assumption = |value: statebook_core::PayoffAssumptionV1| match value {
            statebook_core::PayoffAssumptionV1::FiniteDeclaredDomainOnly => 1,
            statebook_core::PayoffAssumptionV1::ObservationIsFinalCorrectedNormalizedValue => 2,
            statebook_core::PayoffAssumptionV1::ContractRoundingPrecedesPositionQuantity => 3,
            statebook_core::PayoffAssumptionV1::NoAssetConversion => 4,
        };
        let unmodeled = |value: statebook_core::UnmodeledResidualClassV1| match value {
            statebook_core::UnmodeledResidualClassV1::BasisOutsideNormalizedReference => 1,
            statebook_core::UnmodeledResidualClassV1::TimingOutsideTerminalObservation => 2,
            statebook_core::UnmodeledResidualClassV1::FxConversion => 3,
            statebook_core::UnmodeledResidualClassV1::DefaultRealization => 4,
            statebook_core::UnmodeledResidualClassV1::LegalEnforceability => 5,
            statebook_core::UnmodeledResidualClassV1::Liquidity => 6,
            statebook_core::UnmodeledResidualClassV1::JumpBetweenDeclaredStates => 7,
            statebook_core::UnmodeledResidualClassV1::ModelOutsideDeclaredDomain => 8,
        };
        record([
            (
                1,
                vec![match report.status() {
                    statebook_core::PayoffCompletenessStatusV1::ExactOnDeclaredDomain => 1,
                    statebook_core::PayoffCompletenessStatusV1::ApproximateOnDeclaredDomain => 2,
                    statebook_core::PayoffCompletenessStatusV1::Incomplete => 3,
                }],
            ),
            (2, receipt(report.target())),
            (3, sequence(report.candidate().iter().map(receipt))),
            (4, report.domain_digest().as_bytes().to_vec()),
            (
                5,
                sequence(report.states().iter().map(|state| {
                    let status = match state.status() {
                        statebook_core::StateEvaluationStatusV1::Evaluated => vec![1],
                        statebook_core::StateEvaluationStatusV1::Unsupported { .. } => {
                            panic!("frozen payoff unexpectedly unsupported")
                        }
                    };
                    record([
                        (1, state.state_id().as_bytes().to_vec()),
                        (2, rational(state.observation())),
                        (3, status),
                        (
                            4,
                            sequence(state.residual_by_asset().iter().map(|(asset, amount)| {
                                record([(1, asset.as_bytes().to_vec()), (2, rational(*amount))])
                            })),
                        ),
                    ])
                })),
            ),
            (
                6,
                sequence(report.worst_case_by_asset().iter().map(|worst| {
                    record([
                        (1, worst.asset().as_bytes().to_vec()),
                        (2, rational(worst.absolute_amount())),
                        (
                            3,
                            sequence(
                                worst
                                    .state_ids()
                                    .iter()
                                    .map(|value| value.as_bytes().to_vec()),
                            ),
                        ),
                    ])
                })),
            ),
            (
                7,
                enum_set(report.assumptions().iter().map(|value| assumption(*value))),
            ),
            (
                8,
                enum_set(
                    report
                        .unmodeled_residual_classes()
                        .iter()
                        .map(|value| unmodeled(*value)),
                ),
            ),
            (
                9,
                sequence(
                    report
                        .explicit_non_equivalences()
                        .iter()
                        .map(|value| value.as_bytes().to_vec()),
                ),
            ),
        ])
    }

    fn json_rational(value: &Value) -> Vec<u8> {
        rational(
            SignedRational::parse(
                value["numerator"].as_str().unwrap(),
                value["denominator"].as_str().unwrap(),
            )
            .unwrap(),
        )
    }

    fn json_digest(value: &Value) -> Vec<u8> {
        hex::decode(value.as_str().unwrap()).unwrap()
    }

    fn json_digest_set(values: &Value) -> Vec<u8> {
        let mut values: Vec<_> = values.as_array().unwrap().iter().map(json_digest).collect();
        values.sort();
        sequence(values)
    }

    fn json_optional_string(value: &Value) -> Vec<u8> {
        value.as_str().map_or_else(
            || vec![0],
            |value| {
                let mut output = vec![1];
                output.extend_from_slice(&(value.len() as u32).to_be_bytes());
                output.extend_from_slice(value.as_bytes());
                output
            },
        )
    }

    fn json_support(value: &Value) -> u8 {
        match value.as_str().unwrap() {
            "supported" => 1,
            "unsupported" => 2,
            "unknown" => 3,
            other => panic!("unknown fixture support: {other}"),
        }
    }

    fn fixture_execution(root: &Value) -> Vec<u8> {
        let fixture = &root["execution"];
        let mut legs = fixture["legs"].as_array().unwrap().clone();
        legs.sort_by(|a, b| a["leg_id"].as_str().cmp(&b["leg_id"].as_str()));
        record([
            (1, json_digest(&fixture["analysis_subject_digest"])),
            (
                2,
                fixture["observed_at"]
                    .as_i64()
                    .unwrap()
                    .to_be_bytes()
                    .to_vec(),
            ),
            (
                3,
                fixture["expires_at"]
                    .as_i64()
                    .unwrap()
                    .to_be_bytes()
                    .to_vec(),
            ),
            (4, fixture["venue_id"].as_str().unwrap().as_bytes().to_vec()),
            (
                5,
                fixture["account_id"].as_str().unwrap().as_bytes().to_vec(),
            ),
            (
                6,
                sequence(legs.iter().map(|leg| {
                    let mut levels = leg["levels"].as_array().unwrap().clone();
                    levels.sort_by(|a, b| a["level_id"].as_str().cmp(&b["level_id"].as_str()));
                    record([
                        (1, leg["leg_id"].as_str().unwrap().as_bytes().to_vec()),
                        (2, json_digest(&leg["state_key"])),
                        (3, leg["asset"].as_str().unwrap().as_bytes().to_vec()),
                        (4, vec![if leg["side"] == "buy" { 1 } else { 2 }]),
                        (5, json_rational(&leg["requested_quantity"])),
                        (6, json_rational(&leg["reference_price"])),
                        (7, json_rational(&leg["price_bound"])),
                        (8, json_rational(&leg["fee_rate"])),
                        (9, json_rational(&leg["maximum_fee"])),
                        (10, json_rational(&leg["maximum_slippage"])),
                        (11, leg["deadline"].as_i64().unwrap().to_be_bytes().to_vec()),
                        (12, vec![json_support(&leg["queue"])]),
                        (13, vec![json_support(&leg["atomicity"])]),
                        (14, vec![json_support(&leg["leg_failure_model"])]),
                        (
                            15,
                            sequence(levels.iter().map(|level| {
                                record([
                                    (1, level["level_id"].as_str().unwrap().as_bytes().to_vec()),
                                    (2, json_rational(&level["price"])),
                                    (3, json_rational(&level["quantity"])),
                                ])
                            })),
                        ),
                    ])
                })),
            ),
            (7, json_digest_set(&fixture["source_evidence_digests"])),
        ])
    }

    fn fixture_capital(root: &Value) -> Vec<u8> {
        let fixture = &root["capital"];
        let mut receipts = fixture["receipts"].as_array().unwrap().clone();
        receipts.sort_by(|a, b| a["state_key"].as_str().cmp(&b["state_key"].as_str()));
        record([
            (1, json_digest(&fixture["analysis_subject_digest"])),
            (
                2,
                fixture["observed_at"]
                    .as_i64()
                    .unwrap()
                    .to_be_bytes()
                    .to_vec(),
            ),
            (
                3,
                fixture["expires_at"]
                    .as_i64()
                    .unwrap()
                    .to_be_bytes()
                    .to_vec(),
            ),
            (
                4,
                fixture["authority_id"]
                    .as_str()
                    .unwrap()
                    .as_bytes()
                    .to_vec(),
            ),
            (
                5,
                fixture["eligible_account"]
                    .as_str()
                    .unwrap()
                    .as_bytes()
                    .to_vec(),
            ),
            (6, fixture["model_id"].as_str().unwrap().as_bytes().to_vec()),
            (
                7,
                (fixture["model_version"].as_u64().unwrap() as u32)
                    .to_be_bytes()
                    .to_vec(),
            ),
            (8, json_digest(&fixture["model_digest"])),
            (9, json_rational(&fixture["haircut"])),
            (
                10,
                fixture["margin_rule_id"]
                    .as_str()
                    .unwrap()
                    .as_bytes()
                    .to_vec(),
            ),
            (
                11,
                fixture["jurisdiction"]
                    .as_str()
                    .unwrap()
                    .as_bytes()
                    .to_vec(),
            ),
            (
                12,
                fixture["liquidation_horizon_seconds"]
                    .as_u64()
                    .unwrap()
                    .to_be_bytes()
                    .to_vec(),
            ),
            (
                13,
                sequence(receipts.iter().map(|receipt| {
                    record([
                        (1, json_digest(&receipt["state_key"])),
                        (2, json_rational(&receipt["recognized_quantity"])),
                        (
                            3,
                            vec![if receipt["verdict"] == "recognized" {
                                1
                            } else {
                                2
                            }],
                        ),
                        (4, json_digest(&receipt["capital_context_digest"])),
                    ])
                })),
            ),
            (14, json_digest_set(&fixture["source_evidence_digests"])),
        ])
    }

    fn fixture_capital_context(root: &Value) -> Vec<u8> {
        let fixture = &root["capital"];
        record([
            (1, 1_u16.to_be_bytes().to_vec()),
            (2, json_digest(&fixture["analysis_subject_digest"])),
            (
                3,
                fixture["authority_id"]
                    .as_str()
                    .unwrap()
                    .as_bytes()
                    .to_vec(),
            ),
            (
                4,
                fixture["eligible_account"]
                    .as_str()
                    .unwrap()
                    .as_bytes()
                    .to_vec(),
            ),
            (5, fixture["model_id"].as_str().unwrap().as_bytes().to_vec()),
            (
                6,
                (fixture["model_version"].as_u64().unwrap() as u32)
                    .to_be_bytes()
                    .to_vec(),
            ),
            (7, json_digest(&fixture["model_digest"])),
            (8, json_rational(&fixture["haircut"])),
            (
                9,
                fixture["margin_rule_id"]
                    .as_str()
                    .unwrap()
                    .as_bytes()
                    .to_vec(),
            ),
            (
                10,
                fixture["jurisdiction"]
                    .as_str()
                    .unwrap()
                    .as_bytes()
                    .to_vec(),
            ),
            (
                11,
                fixture["liquidation_horizon_seconds"]
                    .as_u64()
                    .unwrap()
                    .to_be_bytes()
                    .to_vec(),
            ),
            (
                12,
                fixture["observed_at"]
                    .as_i64()
                    .unwrap()
                    .to_be_bytes()
                    .to_vec(),
            ),
            (
                13,
                fixture["expires_at"]
                    .as_i64()
                    .unwrap()
                    .to_be_bytes()
                    .to_vec(),
            ),
        ])
    }

    fn fixture_settlement(root: &Value) -> Vec<u8> {
        let fixture = &root["settlement"];
        let mut stages = fixture["stages"].as_array().unwrap().clone();
        let stage_name = |value: &Value| match value.as_str().unwrap() {
            "source_observation" => 1,
            "source_finality" => 2,
            "destination_observation" => 3,
            "destination_finality" => 4,
            "operational_reconciliation" => 5,
            "legal_finality" => 6,
            other => panic!("unknown stage: {other}"),
        };
        stages.sort_by_key(|value| {
            (
                value["obligation_id"].as_str().unwrap().to_owned(),
                stage_name(&value["stage"]),
            )
        });
        record([
            (1, json_digest(&fixture["analysis_subject_digest"])),
            (
                2,
                fixture["observed_at"]
                    .as_i64()
                    .unwrap()
                    .to_be_bytes()
                    .to_vec(),
            ),
            (
                3,
                fixture["expires_at"]
                    .as_i64()
                    .unwrap()
                    .to_be_bytes()
                    .to_vec(),
            ),
            (
                4,
                fixture["source_finality_domain"]
                    .as_str()
                    .unwrap()
                    .as_bytes()
                    .to_vec(),
            ),
            (
                5,
                fixture["destination_finality_domain"]
                    .as_str()
                    .unwrap()
                    .as_bytes()
                    .to_vec(),
            ),
            (
                6,
                vec![u8::from(fixture["domains_compatible"].as_bool().unwrap())],
            ),
            (
                7,
                vec![u8::from(fixture["transition_supported"].as_bool().unwrap())],
            ),
            (8, json_optional_string(&fixture["reversal_rule"])),
            (9, json_optional_string(&fixture["insolvency_rule"])),
            (10, vec![u8::from(fixture["disputed"].as_bool().unwrap())]),
            (11, vec![u8::from(fixture["reversed"].as_bool().unwrap())]),
            (
                12,
                vec![u8::from(
                    fixture["reconciliation_mismatch"].as_bool().unwrap(),
                )],
            ),
            (
                13,
                sequence(stages.iter().map(|stage| {
                    record([
                        (
                            1,
                            stage["obligation_id"].as_str().unwrap().as_bytes().to_vec(),
                        ),
                        (2, vec![stage_name(&stage["stage"])]),
                        (
                            3,
                            vec![match stage["verdict"].as_str().unwrap() {
                                "passed" => 1,
                                "pending" => 2,
                                "conditional" => 3,
                                "unknown" => 4,
                                other => panic!("unknown stage verdict: {other}"),
                            }],
                        ),
                    ])
                })),
            ),
            (14, json_digest_set(&fixture["source_evidence_digests"])),
        ])
    }

    fn json_root_set(value: &Value) -> Vec<u8> {
        let mut roots: Vec<_> = value
            .as_array()
            .unwrap()
            .iter()
            .map(|root| {
                let class = match root["root_class"].as_str().unwrap() {
                    "data" => 1,
                    "operator" => 2,
                    "cloud" => 3,
                    "kms" => 4,
                    "rpc" => 5,
                    "ci_cd" => 6,
                    "model" => 7,
                    "signer" => 8,
                    other => panic!("unknown root class: {other}"),
                };
                (class, root["root_id"].as_str().unwrap().to_owned())
            })
            .collect();
        roots.sort();
        sequence(
            roots
                .into_iter()
                .map(|(class, id)| record([(1, vec![class]), (2, id.into_bytes())])),
        )
    }

    fn fixture_assurance(root: &Value) -> Vec<u8> {
        let fixture = &root["assurance"];
        let property = |value: &Value| match value.as_str().unwrap() {
            "action_authorization" => 1,
            "source_authenticity_and_freshness" => 2,
            "calculation_integrity" => 3,
            "state_transition_integrity" => 4,
            "solvency_and_liquid_resource_support" => 5,
            "destination_and_route_policy" => 6,
            "anomaly_and_emergency_clearance" => 7,
            "evidence_root_disclosure" => 8,
            "financial_basis_binding" => 9,
            other => panic!("unknown property: {other}"),
        };
        let mut observations = fixture["observations"].as_array().unwrap().clone();
        observations.sort_by_key(|value| property(&value["property"]));
        record([
            (1, json_digest(&fixture["analysis_subject_digest"])),
            (
                2,
                fixture["observed_at"]
                    .as_i64()
                    .unwrap()
                    .to_be_bytes()
                    .to_vec(),
            ),
            (
                3,
                fixture["expires_at"]
                    .as_i64()
                    .unwrap()
                    .to_be_bytes()
                    .to_vec(),
            ),
            (
                4,
                fixture["issuer_id"].as_str().unwrap().as_bytes().to_vec(),
            ),
            (
                5,
                fixture["subject_id"].as_str().unwrap().as_bytes().to_vec(),
            ),
            (6, json_digest(&fixture["scope_digest"])),
            (7, fixture["nonce"].as_str().unwrap().as_bytes().to_vec()),
            (
                8,
                sequence(observations.iter().map(|observation| {
                    record([
                        (1, vec![property(&observation["property"])]),
                        (
                            2,
                            vec![match observation["verdict"].as_str().unwrap() {
                                "pass" => 1,
                                "fail" => 2,
                                "unknown" => 3,
                                other => panic!("unknown assurance verdict: {other}"),
                            }],
                        ),
                        (3, json_root_set(&observation["current_roots"])),
                        (4, json_root_set(&observation["dependency_roots"])),
                        (
                            5,
                            vec![if observation["dependency_disclosure"] == "complete" {
                                1
                            } else {
                                2
                            }],
                        ),
                        (
                            6,
                            vec![u8::from(observation["replayed"].as_bool().unwrap())],
                        ),
                        (7, vec![u8::from(observation["revoked"].as_bool().unwrap())]),
                        (
                            8,
                            vec![u8::from(observation["superseded"].as_bool().unwrap())],
                        ),
                        (
                            9,
                            vec![u8::from(observation["equivocated"].as_bool().unwrap())],
                        ),
                    ])
                })),
            ),
            (9, json_digest_set(&fixture["source_evidence_digests"])),
        ])
    }

    fn fixture_recovery(root: &Value) -> Vec<u8> {
        let fixture = &root["recovery"];
        let capability = |value: &Value| match value.as_str().unwrap() {
            "stop_externalization" => 1,
            "reconcile_every_in_flight_item" => 2,
            "preserve_evidence" => 3,
            "restore_liabilities_without_duplication" => 4,
            "reopen_through_bounded_canary_stages" => 5,
            other => panic!("unknown capability: {other}"),
        };
        let verdict = |value: &Value| match value.as_str().unwrap() {
            "pass" => 1,
            "fail" => 2,
            "unknown" => 3,
            other => panic!("unknown recovery verdict: {other}"),
        };
        let mut paths = fixture["paths"].as_array().unwrap().clone();
        paths.sort_by(|a, b| a["path_id"].as_str().cmp(&b["path_id"].as_str()));
        let mut items = fixture["in_flight_items"].as_array().unwrap().clone();
        items.sort_by(|a, b| a["item_id"].as_str().cmp(&b["item_id"].as_str()));
        let mut canaries: Vec<_> = fixture["canary_stages"]
            .as_array()
            .unwrap()
            .iter()
            .map(verdict)
            .collect();
        canaries.sort();
        record([
            (1, json_digest(&fixture["analysis_subject_digest"])),
            (2, json_digest(&fixture["recovery_profile_digest"])),
            (
                3,
                fixture["observed_at"]
                    .as_i64()
                    .unwrap()
                    .to_be_bytes()
                    .to_vec(),
            ),
            (
                4,
                fixture["expires_at"]
                    .as_i64()
                    .unwrap()
                    .to_be_bytes()
                    .to_vec(),
            ),
            (
                5,
                sequence(paths.iter().map(|path| {
                    let mut capabilities = path["capabilities"].as_array().unwrap().clone();
                    capabilities.sort_by_key(|value| capability(&value["capability"]));
                    record([
                        (1, path["path_id"].as_str().unwrap().as_bytes().to_vec()),
                        (
                            2,
                            sequence(capabilities.iter().map(|value| {
                                vec![capability(&value["capability"]), verdict(&value["verdict"])]
                            })),
                        ),
                    ])
                })),
            ),
            (
                6,
                sequence(items.iter().map(|item| {
                    record([
                        (1, item["item_id"].as_str().unwrap().as_bytes().to_vec()),
                        (2, json_digest(&item["expected_digest"])),
                        (3, json_digest(&item["observed_digest"])),
                    ])
                })),
            ),
            (
                7,
                fixture["evidence_preservation_ref"]
                    .as_str()
                    .unwrap()
                    .as_bytes()
                    .to_vec(),
            ),
            (8, json_digest(&fixture["liability_before_digest"])),
            (9, json_digest(&fixture["liability_after_digest"])),
            (10, vec![verdict(&fixture["evidence_preserved"])]),
            (11, vec![verdict(&fixture["liabilities_duplicate_free"])]),
            (12, sequence(canaries.into_iter().map(|value| vec![value]))),
            (13, json_digest_set(&fixture["source_evidence_digests"])),
        ])
    }

    #[test]
    fn ring_and_independent_tlv_encoder_reproduce_every_p3_identity() {
        let report = composed(FIXTURE, 1500);
        let profile_value = RecoveryPathProfileV1::statebook_externalization_v1();
        let fixture_json: Value = serde_json::from_slice(FIXTURE).unwrap();
        let cases = [
            (
                b"statebook:p3-semantic-report:v1\0".as_slice(),
                semantic(&report),
                report.semantic_report_digest().to_hex(),
            ),
            (
                b"statebook:p3-payoff-report:v1\0".as_slice(),
                payoff(&report),
                report.payoff_report_digest().to_hex(),
            ),
            (
                b"statebook:p3-analysis-subject:v1\0".as_slice(),
                subject(&report),
                report.analysis_subject().digest().to_hex(),
            ),
            (
                b"statebook:p3-recovery-profile:v1\0".as_slice(),
                profile(&profile_value),
                profile_value.digest().to_hex(),
            ),
            (
                b"statebook:p3-execution-fixture:v1\0".as_slice(),
                fixture_execution(&fixture_json),
                report.execution().fixture_digest().unwrap().to_hex(),
            ),
            (
                b"statebook:p3-capital-fixture:v1\0".as_slice(),
                fixture_capital(&fixture_json),
                report.capital().fixture_digest().unwrap().to_hex(),
            ),
            (
                b"statebook:p3-capital-context:v1\0".as_slice(),
                fixture_capital_context(&fixture_json),
                report
                    .capital()
                    .context()
                    .unwrap()
                    .capital_context_digest()
                    .to_hex(),
            ),
            (
                b"statebook:p3-settlement-fixture:v1\0".as_slice(),
                fixture_settlement(&fixture_json),
                report.settlement().fixture_digest().unwrap().to_hex(),
            ),
            (
                b"statebook:p3-assurance-fixture:v1\0".as_slice(),
                fixture_assurance(&fixture_json),
                report.assurance().fixture_digest().unwrap().to_hex(),
            ),
            (
                b"statebook:p3-recovery-fixture:v1\0".as_slice(),
                fixture_recovery(&fixture_json),
                report.recovery().fixture_digest().unwrap().to_hex(),
            ),
            (
                b"statebook:p3-execution-report:v1\0".as_slice(),
                execution(&report),
                report.execution().report_digest().to_hex(),
            ),
            (
                b"statebook:p3-capital-report:v1\0".as_slice(),
                capital(&report),
                report.capital().report_digest().to_hex(),
            ),
            (
                b"statebook:p3-settlement-report:v1\0".as_slice(),
                settlement(&report),
                report.settlement().report_digest().to_hex(),
            ),
            (
                b"statebook:p3-assurance-report:v1\0".as_slice(),
                assurance(&report),
                report.assurance().report_digest().to_hex(),
            ),
            (
                b"statebook:p3-recovery-report:v1\0".as_slice(),
                recovery(&report),
                report.recovery().report_digest().to_hex(),
            ),
            (
                b"statebook:p3-seven-report-composition:v1\0".as_slice(),
                composition(&report),
                report.composition_digest().to_hex(),
            ),
        ];
        for (domain, preimage, expected) in cases {
            assert_eq!(ring_sha256(domain, &preimage), expected);
        }
    }
}
