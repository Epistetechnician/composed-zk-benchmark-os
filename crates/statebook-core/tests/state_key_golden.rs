mod support;

use serde_json::Value;
use statebook_core::{
    derive_state_key, parse_normalization_profile_v1, parse_source_contract_v1, validate_and_lower,
};

const BASELINE: &[u8] = include_bytes!("fixtures/terminal_contract_baseline_v1.json");
const PROFILE: &str = include_str!("fixtures/normalization_profile_v1.json");
const GOLDEN: &str = include_str!("fixtures/state_key_golden_v1.json");

#[test]
fn production_and_implementation_diverse_encoder_match_frozen_golden() {
    let source = parse_source_contract_v1(BASELINE).unwrap();
    let profile = parse_normalization_profile_v1(PROFILE.as_bytes()).unwrap();
    let contract = validate_and_lower(source, &profile).unwrap();
    let receipt = derive_state_key(&contract);
    let golden: Value = serde_json::from_str(GOLDEN).unwrap();

    assert_eq!(
        hex::encode(receipt.canonical_preimage()),
        golden["canonical_preimage_hex"].as_str().unwrap()
    );
    assert_eq!(
        receipt.canonical_preimage().len() as u64,
        golden["canonical_preimage_length"].as_u64().unwrap()
    );
    assert_eq!(
        receipt.state_key().to_hex(),
        golden["state_key_sha256"].as_str().unwrap()
    );
    assert_eq!(
        receipt.lineage().source_document_digest().to_hex(),
        golden["source_document_sha256"].as_str().unwrap()
    );
    assert_eq!(
        receipt.lineage().normalization_profile_digest().to_hex(),
        golden["normalization_profile_sha256"].as_str().unwrap()
    );

    let independent =
        support::independent_state_key::encode_and_hash(&golden["normalized_semantics"]);
    assert_eq!(independent.preimage, receipt.canonical_preimage());
    assert_eq!(
        hex::encode(independent.digest),
        receipt.state_key().to_hex()
    );
    let independent_validated = support::independent_state_key::encode_and_hash_validated_contract(
        &golden,
        &independent.digest,
    );
    assert_eq!(
        hex::encode(independent_validated),
        golden["validated_contract_sha256"].as_str().unwrap()
    );
    assert_eq!(
        receipt.validated_contract_digest().to_hex(),
        golden["validated_contract_sha256"].as_str().unwrap()
    );
}

#[test]
fn implementation_diverse_encoder_covers_all_comparator_rounding_and_set_tags() {
    let baseline_source: Value = serde_json::from_slice(BASELINE).unwrap();
    let golden: Value = serde_json::from_str(GOLDEN).unwrap();
    let baseline_semantics = golden["normalized_semantics"].clone();

    for kind in [
        "less_than",
        "less_than_or_equal",
        "equal",
        "greater_than_or_equal",
        "greater_than",
    ] {
        let mut source = baseline_source.clone();
        source["payoff"]["comparator"]["kind"] = Value::String(kind.to_owned());
        let mut semantics = baseline_semantics.clone();
        semantics["comparator_kind"] = Value::String(kind.to_owned());
        assert_diverse_agreement(&source, &semantics);
    }

    for endpoints in ["open_open", "open_closed", "closed_open", "closed_closed"] {
        let mut source = baseline_source.clone();
        source["payoff"]["comparator"] = serde_json::json!({
            "kind":"in_range",
            "threshold":null,
            "lower":{"numerator":"90000","denominator":"1"},
            "upper":{"numerator":"110000","denominator":"1"},
            "endpoints":endpoints
        });
        let mut semantics = baseline_semantics.clone();
        semantics["comparator_kind"] = Value::String("in_range".to_owned());
        semantics["lower_numerator"] = Value::String("90000".to_owned());
        semantics["lower_denominator"] = Value::String("1".to_owned());
        semantics["upper_numerator"] = Value::String("110000".to_owned());
        semantics["upper_denominator"] = Value::String("1".to_owned());
        semantics["endpoint_policy"] = Value::String(endpoints.to_owned());
        assert_diverse_agreement(&source, &semantics);
    }

    for rounding in ["toward_zero", "floor", "ceiling", "half_even"] {
        let mut source = baseline_source.clone();
        source["settlement"]["rounding_mode"] = Value::String(rounding.to_owned());
        let mut semantics = baseline_semantics.clone();
        semantics["rounding_mode"] = Value::String(rounding.to_owned());
        assert_diverse_agreement(&source, &semantics);
    }

    let mut source = baseline_source;
    source["explicit_non_equivalences"] =
        serde_json::json!(["no-path-dependence", "no-physical-delivery"]);
    let mut semantics = baseline_semantics;
    semantics["explicit_non_equivalences"] =
        serde_json::json!(["no-physical-delivery", "no-path-dependence"]);
    assert_diverse_agreement(&source, &semantics);
}

fn assert_diverse_agreement(source: &Value, normalized_semantics: &Value) {
    let source = parse_source_contract_v1(&serde_json::to_vec(source).unwrap()).unwrap();
    let profile = parse_normalization_profile_v1(PROFILE.as_bytes()).unwrap();
    let receipt = derive_state_key(&validate_and_lower(source, &profile).unwrap());
    let independent = support::independent_state_key::encode_and_hash(normalized_semantics);
    assert_eq!(independent.preimage, receipt.canonical_preimage());
    assert_eq!(
        hex::encode(independent.digest),
        receipt.state_key().to_hex()
    );
}
