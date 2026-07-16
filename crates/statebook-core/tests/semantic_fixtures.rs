use serde_json::{json, Value};
use statebook_core::{
    assess_semantic_completeness, derive_state_key, parse_normalization_profile_v1,
    parse_source_contract_v1, validate_and_lower, LoweringError, SemanticCompletenessStatus,
    SemanticField,
};
use std::collections::BTreeSet;

const CASES: &str = include_str!("fixtures/terminal_contract_cases_v1.json");
const PROFILE: &str = include_str!("fixtures/normalization_profile_v1.json");

fn cases() -> Value {
    serde_json::from_str(CASES).unwrap()
}

fn profile() -> statebook_core::ValidatedNormalizationProfileV1 {
    parse_normalization_profile_v1(PROFILE.as_bytes()).unwrap()
}

fn lower(value: &Value) -> statebook_core::ValidatedContract {
    let source = parse_source_contract_v1(&serde_json::to_vec(value).unwrap()).unwrap();
    validate_and_lower(source, &profile()).unwrap()
}

#[test]
fn every_declared_material_mutation_changes_state_key() {
    let fixture = cases();
    let baseline = fixture["baseline"].clone();
    let baseline_key = derive_state_key(&lower(&baseline)).state_key();
    let mutations = fixture["material_mutations"].as_array().unwrap();
    let expected_names: BTreeSet<&str> = [
        "reference_namespace",
        "reference_identifier",
        "reference_unit",
        "benchmark_administrator",
        "methodology_version",
        "methodology_sha256",
        "fallback_rule",
        "calendar",
        "timezone",
        "observation_start",
        "observation_end",
        "sampling_rule",
        "disruption_rule",
        "correction_rule",
        "comparator",
        "threshold",
        "payoff_amount",
        "settlement_asset",
        "unit_scale",
        "rounding_mode",
        "rounding_quantum",
        "deadline",
        "dispute_rule",
        "default_rule",
        "governing_rule",
        "finality_domain",
        "non_equivalence",
    ]
    .into_iter()
    .collect();
    let actual_names: BTreeSet<&str> = mutations
        .iter()
        .map(|mutation| mutation["name"].as_str().unwrap())
        .collect();
    let pointers: BTreeSet<&str> = mutations
        .iter()
        .map(|mutation| mutation["pointer"].as_str().unwrap())
        .collect();
    assert_eq!(actual_names, expected_names);
    assert_eq!(pointers.len(), mutations.len());

    for mutation in mutations {
        let mut candidate = baseline.clone();
        let pointer = mutation["pointer"].as_str().unwrap();
        *candidate.pointer_mut(pointer).unwrap() = mutation["value"].clone();
        assert_eq!(
            leaf_differences(&baseline, &candidate),
            1,
            "{}",
            mutation["name"]
        );
        let candidate_key = derive_state_key(&lower(&candidate)).state_key();
        assert_ne!(
            candidate_key, baseline_key,
            "material mutation did not diverge: {}",
            mutation["name"]
        );
    }
}

#[test]
fn source_serialization_and_set_order_do_not_change_state_identity() {
    let fixture = cases();
    let baseline = fixture["baseline"].clone();
    let compact = serde_json::to_vec(&baseline).unwrap();
    let pretty = serde_json::to_vec_pretty(&baseline).unwrap();
    let source_a = parse_source_contract_v1(&compact).unwrap();
    let source_b = parse_source_contract_v1(&pretty).unwrap();
    assert_ne!(
        source_a.source_document_digest(),
        source_b.source_document_digest()
    );
    let contract_a = validate_and_lower(source_a, &profile()).unwrap();
    let contract_b = validate_and_lower(source_b, &profile()).unwrap();
    assert_eq!(
        derive_state_key(&contract_a).state_key(),
        derive_state_key(&contract_b).state_key()
    );

    let mut permuted = baseline.clone();
    permuted["explicit_non_equivalences"] = json!(["no-path-dependence", "no-physical-delivery"]);
    assert_eq!(
        derive_state_key(&contract_a).state_key(),
        derive_state_key(&lower(&permuted)).state_key()
    );

    let reversed_top_level = format!(
        "{{\"unknown_terms\":{},\"explicit_non_equivalences\":{},\"settlement\":{},\"payoff\":{},\"observation\":{},\"economic_reference\":{},\"source_observed_at\":{},\"source_revision\":{},\"source_contract_id\":{},\"venue_namespace\":{},\"schema_version\":{}}}",
        serde_json::to_string(&baseline["unknown_terms"]).unwrap(),
        serde_json::to_string(&baseline["explicit_non_equivalences"]).unwrap(),
        serde_json::to_string(&baseline["settlement"]).unwrap(),
        serde_json::to_string(&baseline["payoff"]).unwrap(),
        serde_json::to_string(&baseline["observation"]).unwrap(),
        serde_json::to_string(&baseline["economic_reference"]).unwrap(),
        baseline["source_observed_at"],
        serde_json::to_string(&baseline["source_revision"]).unwrap(),
        serde_json::to_string(&baseline["source_contract_id"]).unwrap(),
        serde_json::to_string(&baseline["venue_namespace"]).unwrap(),
        serde_json::to_string(&baseline["schema_version"]).unwrap(),
    );
    let reordered_source = parse_source_contract_v1(reversed_top_level.as_bytes()).unwrap();
    assert_ne!(
        contract_a.lineage().source_document_digest(),
        reordered_source.source_document_digest()
    );
    let reordered = validate_and_lower(reordered_source, &profile()).unwrap();
    assert_eq!(
        derive_state_key(&contract_a).state_key(),
        derive_state_key(&reordered).state_key()
    );
}

#[test]
fn exact_equivalents_converge_and_range_endpoint_policy_diverges() {
    let fixture = cases();
    let baseline = fixture["baseline"].clone();
    let baseline_key = derive_state_key(&lower(&baseline)).state_key();

    let mut reduced = baseline.clone();
    reduced["payoff"]["amount"] = json!({"numerator":"200","denominator":"2"});
    reduced["settlement"]["unit_scale"] = json!("0.0100");
    reduced["settlement"]["rounding_quantum"] = json!("0.010000");
    assert_eq!(baseline_key, derive_state_key(&lower(&reduced)).state_key());

    let mut closed = baseline.clone();
    closed["payoff"]["comparator"] = json!({
        "kind":"in_range",
        "threshold":null,
        "lower":{"numerator":"90000","denominator":"1"},
        "upper":{"numerator":"110000","denominator":"1"},
        "endpoints":"closed_closed"
    });
    let mut open = closed.clone();
    open["payoff"]["comparator"]["endpoints"] = json!("open_closed");
    assert_ne!(
        derive_state_key(&lower(&closed)).state_key(),
        derive_state_key(&lower(&open)).state_key()
    );
}

#[test]
fn lineage_changes_do_not_pollute_state_identity() {
    let fixture = cases();
    let baseline = fixture["baseline"].clone();
    let original_profile = profile();
    let original_source =
        parse_source_contract_v1(&serde_json::to_vec(&baseline).unwrap()).unwrap();
    let original = validate_and_lower(original_source, &original_profile).unwrap();
    let original_receipt = derive_state_key(&original);

    let mut changed_source = baseline;
    changed_source["venue_namespace"] = json!("fixture.venue.beta");
    changed_source["source_contract_id"] = json!("OTHER-SOURCE-ID");
    changed_source["source_revision"] = json!("rev-2");
    let changed_source =
        parse_source_contract_v1(&serde_json::to_vec(&changed_source).unwrap()).unwrap();
    let changed = validate_and_lower(changed_source, &original_profile).unwrap();
    let changed_receipt = derive_state_key(&changed);
    assert_eq!(original_receipt.state_key(), changed_receipt.state_key());
    assert_ne!(
        original_receipt.validated_contract_digest(),
        changed_receipt.validated_contract_digest()
    );

    let mut profile_json: Value = serde_json::from_str(PROFILE).unwrap();
    profile_json["profile_version"] = json!(2);
    let changed_profile =
        parse_normalization_profile_v1(&serde_json::to_vec(&profile_json).unwrap()).unwrap();
    let source =
        parse_source_contract_v1(&serde_json::to_vec(&fixture["baseline"]).unwrap()).unwrap();
    let changed_profile_contract = validate_and_lower(source, &changed_profile).unwrap();
    let changed_profile_receipt = derive_state_key(&changed_profile_contract);
    assert_eq!(
        original_receipt.state_key(),
        changed_profile_receipt.state_key()
    );
    assert_ne!(
        original_receipt.validated_contract_digest(),
        changed_profile_receipt.validated_contract_digest()
    );
}

#[test]
fn incomplete_unknown_and_unsupported_inputs_never_receive_keys() {
    let fixture = cases();
    let missing_cases = [
        ("/venue_namespace", SemanticField::VenueNamespace),
        ("/source_contract_id", SemanticField::SourceContractId),
        ("/source_revision", SemanticField::SourceRevision),
        ("/source_observed_at", SemanticField::SourceObservedAt),
        (
            "/economic_reference/namespace",
            SemanticField::ReferenceNamespace,
        ),
        (
            "/economic_reference/identifier",
            SemanticField::ReferenceIdentifier,
        ),
        ("/economic_reference/unit", SemanticField::ReferenceUnit),
        (
            "/economic_reference/benchmark_administrator",
            SemanticField::BenchmarkAdministrator,
        ),
        (
            "/economic_reference/methodology_version",
            SemanticField::MethodologyVersion,
        ),
        (
            "/economic_reference/methodology_sha256",
            SemanticField::MethodologySha256,
        ),
        (
            "/economic_reference/fallback_rule",
            SemanticField::FallbackRule,
        ),
        ("/economic_reference/calendar", SemanticField::Calendar),
        ("/economic_reference/timezone", SemanticField::Timezone),
        ("/observation/start", SemanticField::ObservationStart),
        ("/observation/end", SemanticField::ObservationEnd),
        ("/observation/sampling_rule", SemanticField::SamplingRule),
        (
            "/observation/disruption_rule",
            SemanticField::DisruptionRule,
        ),
        (
            "/observation/correction_rule",
            SemanticField::CorrectionRule,
        ),
        ("/payoff/kind", SemanticField::PayoffKind),
        ("/payoff/comparator", SemanticField::Comparator),
        ("/payoff/amount", SemanticField::PayoffAmount),
        ("/settlement/asset", SemanticField::SettlementAsset),
        ("/settlement/unit_scale", SemanticField::SettlementUnitScale),
        ("/settlement/rounding_mode", SemanticField::RoundingMode),
        (
            "/settlement/rounding_quantum",
            SemanticField::RoundingQuantum,
        ),
        ("/settlement/deadline", SemanticField::SettlementDeadline),
        ("/settlement/dispute_rule", SemanticField::DisputeRule),
        ("/settlement/default_rule", SemanticField::DefaultRule),
        ("/settlement/governing_rule", SemanticField::GoverningRule),
        ("/settlement/finality_domain", SemanticField::FinalityDomain),
        (
            "/explicit_non_equivalences",
            SemanticField::ExplicitNonEquivalences,
        ),
    ];
    for (pointer, expected) in missing_cases {
        let mut missing = fixture["baseline"].clone();
        remove_pointer(&mut missing, pointer);
        let source = parse_source_contract_v1(&serde_json::to_vec(&missing).unwrap()).unwrap();
        let report = assess_semantic_completeness(&source, &profile());
        assert_eq!(
            report.status(),
            SemanticCompletenessStatus::Incomplete,
            "{pointer}"
        );
        assert!(report.missing_terms().contains(&expected), "{pointer}");
        assert!(matches!(
            validate_and_lower(source, &profile()),
            Err(LoweringError::Incomplete(_))
        ));
    }

    let mut missing_threshold = fixture["baseline"].clone();
    missing_threshold["payoff"]["comparator"]["threshold"] = Value::Null;
    let source =
        parse_source_contract_v1(&serde_json::to_vec(&missing_threshold).unwrap()).unwrap();
    let report = assess_semantic_completeness(&source, &profile());
    assert_eq!(report.status(), SemanticCompletenessStatus::Incomplete);
    assert!(report.missing_terms().contains(&SemanticField::Comparator));

    let mut complete_range = fixture["baseline"].clone();
    complete_range["payoff"]["comparator"] = json!({
        "kind":"in_range",
        "threshold":null,
        "lower":{"numerator":"90000","denominator":"1"},
        "upper":{"numerator":"110000","denominator":"1"},
        "endpoints":"closed_closed"
    });
    for operand in ["lower", "upper", "endpoints"] {
        let mut missing_range_operand = complete_range.clone();
        missing_range_operand["payoff"]["comparator"][operand] = Value::Null;
        let source =
            parse_source_contract_v1(&serde_json::to_vec(&missing_range_operand).unwrap()).unwrap();
        let report = assess_semantic_completeness(&source, &profile());
        assert_eq!(report.status(), SemanticCompletenessStatus::Incomplete);
        assert!(report.missing_terms().contains(&SemanticField::Comparator));
        assert!(matches!(
            validate_and_lower(source, &profile()),
            Err(LoweringError::Incomplete(_))
        ));
    }

    let mut unknown = fixture["baseline"].clone();
    unknown["unknown_terms"] = json!(["calendar"]);
    let source = parse_source_contract_v1(&serde_json::to_vec(&unknown).unwrap()).unwrap();
    assert!(matches!(
        validate_and_lower(source, &profile()),
        Err(LoweringError::Unknown(_))
    ));

    let mut unsupported = fixture["baseline"].clone();
    unsupported["payoff"]["kind"] = json!("perpetual");
    let source = parse_source_contract_v1(&serde_json::to_vec(&unsupported).unwrap()).unwrap();
    assert!(matches!(
        validate_and_lower(source, &profile()),
        Err(LoweringError::Unsupported(_))
    ));

    for (pointer, value) in [
        ("/payoff/comparator/kind", json!("approximately_equal")),
        ("/settlement/rounding_mode", json!("bankers_guess")),
    ] {
        let mut candidate = fixture["baseline"].clone();
        *candidate.pointer_mut(pointer).unwrap() = value;
        let source = parse_source_contract_v1(&serde_json::to_vec(&candidate).unwrap()).unwrap();
        assert_eq!(
            assess_semantic_completeness(&source, &profile()).status(),
            SemanticCompletenessStatus::Unknown
        );
        assert!(matches!(
            validate_and_lower(source, &profile()),
            Err(LoweringError::Unsupported(_))
        ));
    }
}

#[test]
fn malformed_and_ambiguous_inputs_fail_closed() {
    let duplicate = br#"{"schema_version":"statebook-terminal-source:v1","schema_version":"statebook-terminal-source:v1"}"#;
    assert!(parse_source_contract_v1(duplicate).is_err());

    let fixture = cases();
    let mut duplicate_set = fixture["baseline"].clone();
    duplicate_set["explicit_non_equivalences"] = json!(["same", "same"]);
    assert!(validate_and_lower(
        parse_source_contract_v1(&serde_json::to_vec(&duplicate_set).unwrap()).unwrap(),
        &profile()
    )
    .is_err());

    let mut numeric_exact = fixture["baseline"].clone();
    numeric_exact["payoff"]["amount"]["numerator"] = json!(100.0);
    assert!(parse_source_contract_v1(&serde_json::to_vec(&numeric_exact).unwrap()).is_err());

    let mut unicode = fixture["baseline"].clone();
    unicode["economic_reference"]["identifier"] = json!("BTC-ＵSD");
    assert!(validate_and_lower(
        parse_source_contract_v1(&serde_json::to_vec(&unicode).unwrap()).unwrap(),
        &profile()
    )
    .is_err());
}

#[test]
fn arithmetic_ranges_and_time_order_are_checked() {
    let fixture = cases();
    for (pointer, value) in [
        ("/payoff/amount/denominator", json!("0")),
        ("/settlement/unit_scale", json!("0")),
        ("/settlement/unit_scale", json!("-0.01")),
        ("/settlement/rounding_quantum", json!("-0.01")),
        (
            "/settlement/rounding_quantum",
            json!("0.0000000000000000001"),
        ),
        ("/observation/start", json!(1798732801)),
        ("/settlement/deadline", json!(1798732800)),
    ] {
        let mut candidate = fixture["baseline"].clone();
        *candidate.pointer_mut(pointer).unwrap() = value;
        let source = parse_source_contract_v1(&serde_json::to_vec(&candidate).unwrap()).unwrap();
        assert!(validate_and_lower(source, &profile()).is_err(), "{pointer}");
    }

    let mut range = fixture["baseline"].clone();
    range["payoff"]["comparator"] = json!({
        "kind":"in_range",
        "threshold":null,
        "lower":{"numerator":"2","denominator":"1"},
        "upper":{"numerator":"1","denominator":"1"},
        "endpoints":"closed_closed"
    });
    let source = parse_source_contract_v1(&serde_json::to_vec(&range).unwrap()).unwrap();
    assert!(matches!(
        validate_and_lower(source, &profile()),
        Err(LoweringError::InvalidRange)
    ));

    for endpoints in ["open_open", "open_closed", "closed_open"] {
        let mut equal_open = fixture["baseline"].clone();
        equal_open["payoff"]["comparator"] = json!({
            "kind":"in_range",
            "threshold":null,
            "lower":{"numerator":"1","denominator":"1"},
            "upper":{"numerator":"1","denominator":"1"},
            "endpoints":endpoints
        });
        let source = parse_source_contract_v1(&serde_json::to_vec(&equal_open).unwrap()).unwrap();
        assert!(matches!(
            validate_and_lower(source, &profile()),
            Err(LoweringError::InvalidRange)
        ));
    }

    let mut comparison_overflow = fixture["baseline"].clone();
    comparison_overflow["payoff"]["comparator"] = json!({
        "kind":"in_range",
        "threshold":null,
        "lower":{"numerator":"170141183460469231731687303715884105727","denominator":"1"},
        "upper":{"numerator":"170141183460469231731687303715884105727","denominator":"2"},
        "endpoints":"closed_closed"
    });
    let source =
        parse_source_contract_v1(&serde_json::to_vec(&comparison_overflow).unwrap()).unwrap();
    assert!(matches!(
        validate_and_lower(source, &profile()),
        Err(LoweringError::Exact { .. })
    ));

    for comparator in [
        json!({
            "kind":"greater_than_or_equal",
            "threshold":{"numerator":"1","denominator":"1"},
            "lower":{"numerator":"0","denominator":"1"},
            "upper":null,
            "endpoints":null
        }),
        json!({
            "kind":"in_range",
            "threshold":{"numerator":"1","denominator":"1"},
            "lower":{"numerator":"0","denominator":"1"},
            "upper":{"numerator":"2","denominator":"1"},
            "endpoints":"closed_closed"
        }),
    ] {
        let mut ambiguous = fixture["baseline"].clone();
        ambiguous["payoff"]["comparator"] = comparator;
        let source = parse_source_contract_v1(&serde_json::to_vec(&ambiguous).unwrap()).unwrap();
        assert!(matches!(
            validate_and_lower(source, &profile()),
            Err(LoweringError::Unsupported(_))
        ));
    }
}

#[test]
fn profile_mapping_contract_is_closed() {
    let mut profile_json: Value = serde_json::from_str(PROFILE).unwrap();
    profile_json["mappings"].as_array_mut().unwrap().pop();
    assert!(parse_normalization_profile_v1(&serde_json::to_vec(&profile_json).unwrap()).is_err());

    let mut profile_json: Value = serde_json::from_str(PROFILE).unwrap();
    profile_json["mappings"][0]["transform"] = json!("unknown");
    let profile =
        parse_normalization_profile_v1(&serde_json::to_vec(&profile_json).unwrap()).unwrap();
    let source =
        parse_source_contract_v1(&serde_json::to_vec(&cases()["baseline"]).unwrap()).unwrap();
    assert_eq!(
        assess_semantic_completeness(&source, &profile).status(),
        SemanticCompletenessStatus::Unknown
    );

    let mut duplicate: Value = serde_json::from_str(PROFILE).unwrap();
    let first = duplicate["mappings"][0].clone();
    duplicate["mappings"].as_array_mut().unwrap().push(first);
    assert!(parse_normalization_profile_v1(&serde_json::to_vec(&duplicate).unwrap()).is_err());

    let mut non_identity: Value = serde_json::from_str(PROFILE).unwrap();
    non_identity["mappings"][0]["source_field"] = json!("source_contract_id");
    assert!(parse_normalization_profile_v1(&serde_json::to_vec(&non_identity).unwrap()).is_err());
}

fn remove_pointer(value: &mut Value, pointer: &str) {
    let (parent, leaf) = pointer.rsplit_once('/').unwrap();
    let parent = if parent.is_empty() {
        value
    } else {
        value.pointer_mut(parent).unwrap()
    };
    parent.as_object_mut().unwrap().remove(leaf).unwrap();
}

fn leaf_differences(left: &Value, right: &Value) -> usize {
    match (left, right) {
        (Value::Object(left), Value::Object(right)) => left
            .keys()
            .chain(right.keys())
            .collect::<BTreeSet<_>>()
            .into_iter()
            .map(|key| match (left.get(key), right.get(key)) {
                (Some(left), Some(right)) => leaf_differences(left, right),
                _ => 1,
            })
            .sum(),
        (Value::Array(left), Value::Array(right)) if left.len() == right.len() => left
            .iter()
            .zip(right)
            .map(|(left, right)| leaf_differences(left, right))
            .sum(),
        _ => usize::from(left != right),
    }
}
