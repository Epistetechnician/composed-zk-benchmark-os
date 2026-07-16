use ring::digest::{digest, SHA256};
use serde_json::Value;

pub struct IndependentReceipt {
    pub preimage: Vec<u8>,
    pub digest: [u8; 32],
}

pub fn encode_and_hash(value: &Value) -> IndependentReceipt {
    let mut bytes = b"statebook:state-key:v1\0".to_vec();
    bytes.extend_from_slice(&1_u16.to_be_bytes());
    for (tag, name) in [
        (1, "reference_namespace"),
        (2, "reference_identifier"),
        (3, "reference_unit"),
        (4, "benchmark_administrator"),
        (5, "methodology_version"),
    ] {
        tlv(&mut bytes, tag, text(value, name));
    }
    tlv(
        &mut bytes,
        6,
        &hex::decode(text(value, "methodology_sha256")).unwrap(),
    );
    for (tag, name) in [(7, "fallback_rule"), (8, "calendar"), (9, "timezone")] {
        tlv(&mut bytes, tag, text(value, name));
    }
    tlv(
        &mut bytes,
        10,
        &value["observation_start"].as_i64().unwrap().to_be_bytes(),
    );
    tlv(
        &mut bytes,
        11,
        &value["observation_end"].as_i64().unwrap().to_be_bytes(),
    );
    for (tag, name) in [
        (12, "sampling_rule"),
        (13, "disruption_rule"),
        (14, "correction_rule"),
    ] {
        tlv(&mut bytes, tag, text(value, name));
    }

    let kind = text(value, "comparator_kind");
    let mut comparator = vec![match kind {
        b"less_than" => 1,
        b"less_than_or_equal" => 2,
        b"equal" => 3,
        b"greater_than_or_equal" => 4,
        b"greater_than" => 5,
        b"in_range" => 6,
        other => panic!(
            "unsupported golden comparator: {}",
            String::from_utf8_lossy(other)
        ),
    }];
    if kind == b"in_range" {
        comparator.extend_from_slice(&rational(
            text(value, "lower_numerator"),
            text(value, "lower_denominator"),
        ));
        comparator.extend_from_slice(&rational(
            text(value, "upper_numerator"),
            text(value, "upper_denominator"),
        ));
        comparator.push(match text(value, "endpoint_policy") {
            b"open_open" => 1,
            b"open_closed" => 2,
            b"closed_open" => 3,
            b"closed_closed" => 4,
            _ => panic!("unsupported golden endpoint policy"),
        });
    } else {
        comparator.extend_from_slice(&rational(
            text(value, "threshold_numerator"),
            text(value, "threshold_denominator"),
        ));
    }
    tlv(&mut bytes, 15, &comparator);
    tlv(
        &mut bytes,
        16,
        &rational(
            text(value, "payoff_numerator"),
            text(value, "payoff_denominator"),
        ),
    );
    tlv(&mut bytes, 17, text(value, "settlement_asset"));
    tlv(
        &mut bytes,
        18,
        &scaled(
            text(value, "settlement_unit_coefficient"),
            value["settlement_unit_scale"].as_u64().unwrap() as u8,
        ),
    );
    let rounding = match text(value, "rounding_mode") {
        b"toward_zero" => 1,
        b"floor" => 2,
        b"ceiling" => 3,
        b"half_even" => 4,
        _ => panic!("unsupported golden rounding mode"),
    };
    tlv(&mut bytes, 19, &[rounding]);
    tlv(
        &mut bytes,
        20,
        &scaled(
            text(value, "rounding_quantum_coefficient"),
            value["rounding_quantum_scale"].as_u64().unwrap() as u8,
        ),
    );
    tlv(
        &mut bytes,
        21,
        &value["settlement_deadline"].as_i64().unwrap().to_be_bytes(),
    );
    for (tag, name) in [
        (22, "dispute_rule"),
        (23, "default_rule"),
        (24, "governing_rule"),
        (25, "finality_domain"),
    ] {
        tlv(&mut bytes, tag, text(value, name));
    }
    let members = value["explicit_non_equivalences"].as_array().unwrap();
    let mut members: Vec<Vec<u8>> = members
        .iter()
        .map(|member| {
            let member = member.as_str().unwrap().as_bytes();
            let mut encoded = (member.len() as u32).to_be_bytes().to_vec();
            encoded.extend_from_slice(member);
            encoded
        })
        .collect();
    members.sort();
    let mut set = Vec::new();
    set.extend_from_slice(&(members.len() as u32).to_be_bytes());
    for member in members {
        set.extend_from_slice(&member);
    }
    tlv(&mut bytes, 26, &set);

    let mut output = [0_u8; 32];
    output.copy_from_slice(digest(&SHA256, &bytes).as_ref());
    IndependentReceipt {
        preimage: bytes,
        digest: output,
    }
}

pub fn encode_and_hash_validated_contract(golden: &Value, state_key: &[u8; 32]) -> [u8; 32] {
    let lineage = &golden["lineage"];
    let mut bytes = b"statebook:validated-contract:v1\0".to_vec();
    tlv(&mut bytes, 1, text(lineage, "venue_namespace"));
    tlv(&mut bytes, 2, text(lineage, "source_contract_id"));
    tlv(&mut bytes, 3, text(lineage, "source_revision"));
    tlv(
        &mut bytes,
        4,
        &lineage["source_observed_at"]
            .as_i64()
            .unwrap()
            .to_be_bytes(),
    );
    tlv(
        &mut bytes,
        5,
        &hex::decode(text(golden, "source_document_sha256")).unwrap(),
    );
    tlv(&mut bytes, 6, text(lineage, "normalization_profile_id"));
    tlv(
        &mut bytes,
        7,
        &(lineage["normalization_profile_version"].as_u64().unwrap() as u32).to_be_bytes(),
    );
    tlv(
        &mut bytes,
        8,
        &hex::decode(text(golden, "normalization_profile_sha256")).unwrap(),
    );
    tlv(&mut bytes, 9, state_key);
    let mut output = [0_u8; 32];
    output.copy_from_slice(digest(&SHA256, &bytes).as_ref());
    output
}

fn text<'a>(value: &'a Value, name: &str) -> &'a [u8] {
    value[name].as_str().unwrap().as_bytes()
}

fn rational(numerator: &[u8], denominator: &[u8]) -> Vec<u8> {
    let numerator = std::str::from_utf8(numerator)
        .unwrap()
        .parse::<i128>()
        .unwrap();
    let denominator = std::str::from_utf8(denominator)
        .unwrap()
        .parse::<u128>()
        .unwrap();
    let mut bytes = numerator.to_be_bytes().to_vec();
    bytes.extend_from_slice(&denominator.to_be_bytes());
    bytes
}

fn scaled(coefficient: &[u8], scale: u8) -> Vec<u8> {
    let coefficient = std::str::from_utf8(coefficient)
        .unwrap()
        .parse::<i128>()
        .unwrap();
    let mut bytes = coefficient.to_be_bytes().to_vec();
    bytes.push(scale);
    bytes
}

fn tlv(output: &mut Vec<u8>, tag: u16, payload: &[u8]) {
    output.extend_from_slice(&tag.to_be_bytes());
    output.extend_from_slice(&(payload.len() as u32).to_be_bytes());
    output.extend_from_slice(payload);
}
