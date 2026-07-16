use crate::model::{
    Comparator, EndpointPolicy, NormalizedTerminalSemantics, RoundingMode, Sha256Digest,
    StateKeyReceiptV1, StateKeyV1, ValidatedContract,
};
use crate::{STATE_KEY_DOMAIN_V1, STATE_KEY_SCHEMA_V1};
use sha2::{Digest, Sha256};

const VALIDATED_CONTRACT_DOMAIN_V1: &[u8] = b"statebook:validated-contract:v1\0";

pub fn derive_state_key(contract: &ValidatedContract) -> StateKeyReceiptV1 {
    let canonical_preimage = canonical_preimage(&contract.semantics);
    let state_key = StateKeyV1::new(hash(&canonical_preimage));
    let validated_contract_digest = validated_contract_digest(contract, state_key);
    StateKeyReceiptV1 {
        state_key,
        canonical_preimage,
        validated_contract_digest,
        lineage: contract.lineage.clone(),
    }
}

fn canonical_preimage(semantics: &NormalizedTerminalSemantics) -> Vec<u8> {
    let mut output = Vec::new();
    output.extend_from_slice(STATE_KEY_DOMAIN_V1);
    output.extend_from_slice(&STATE_KEY_SCHEMA_V1.to_be_bytes());
    field(&mut output, 1, semantics.reference_namespace.as_bytes());
    field(&mut output, 2, semantics.reference_identifier.as_bytes());
    field(&mut output, 3, semantics.reference_unit.as_bytes());
    field(&mut output, 4, semantics.benchmark_administrator.as_bytes());
    field(&mut output, 5, semantics.methodology_version.as_bytes());
    field(&mut output, 6, semantics.methodology_sha256.as_bytes());
    field(&mut output, 7, semantics.fallback_rule.as_bytes());
    field(&mut output, 8, semantics.calendar.as_bytes());
    field(&mut output, 9, semantics.timezone.as_bytes());
    field(&mut output, 10, &semantics.observation_start.to_be_bytes());
    field(&mut output, 11, &semantics.observation_end.to_be_bytes());
    field(&mut output, 12, semantics.sampling_rule.as_bytes());
    field(&mut output, 13, semantics.disruption_rule.as_bytes());
    field(&mut output, 14, semantics.correction_rule.as_bytes());
    field(&mut output, 15, &encode_comparator(&semantics.comparator));
    field(&mut output, 16, &encode_rational(semantics.payoff_amount));
    field(&mut output, 17, semantics.settlement_asset.as_bytes());
    field(
        &mut output,
        18,
        &encode_scaled(semantics.settlement_unit_scale),
    );
    field(&mut output, 19, &[rounding_tag(semantics.rounding_mode)]);
    field(&mut output, 20, &encode_scaled(semantics.rounding_quantum));
    field(
        &mut output,
        21,
        &semantics.settlement_deadline.to_be_bytes(),
    );
    field(&mut output, 22, semantics.dispute_rule.as_bytes());
    field(&mut output, 23, semantics.default_rule.as_bytes());
    field(&mut output, 24, semantics.governing_rule.as_bytes());
    field(&mut output, 25, semantics.finality_domain.as_bytes());
    field(
        &mut output,
        26,
        &encode_set(
            semantics
                .explicit_non_equivalences
                .iter()
                .map(String::as_bytes),
        ),
    );
    output
}

fn encode_comparator(comparator: &Comparator) -> Vec<u8> {
    let mut output = Vec::new();
    match comparator {
        Comparator::LessThan { threshold } => {
            output.push(1);
            output.extend_from_slice(&encode_rational(*threshold));
        }
        Comparator::LessThanOrEqual { threshold } => {
            output.push(2);
            output.extend_from_slice(&encode_rational(*threshold));
        }
        Comparator::Equal { threshold } => {
            output.push(3);
            output.extend_from_slice(&encode_rational(*threshold));
        }
        Comparator::GreaterThanOrEqual { threshold } => {
            output.push(4);
            output.extend_from_slice(&encode_rational(*threshold));
        }
        Comparator::GreaterThan { threshold } => {
            output.push(5);
            output.extend_from_slice(&encode_rational(*threshold));
        }
        Comparator::InRange {
            lower,
            upper,
            endpoints,
        } => {
            output.push(6);
            output.extend_from_slice(&encode_rational(*lower));
            output.extend_from_slice(&encode_rational(*upper));
            output.push(endpoint_tag(*endpoints));
        }
    }
    output
}

fn encode_rational(value: crate::SignedRational) -> Vec<u8> {
    let mut output = Vec::with_capacity(32);
    output.extend_from_slice(&value.numerator().to_be_bytes());
    output.extend_from_slice(&value.denominator().to_be_bytes());
    output
}

fn encode_scaled(value: crate::ScaledInteger) -> Vec<u8> {
    let mut output = Vec::with_capacity(17);
    output.extend_from_slice(&value.coefficient().to_be_bytes());
    output.push(value.scale());
    output
}

fn encode_set<'a>(values: impl Iterator<Item = &'a [u8]>) -> Vec<u8> {
    let mut values: Vec<Vec<u8>> = values
        .map(|value| {
            let mut encoded = u32::try_from(value.len())
                .expect("validated semantic text length fits u32")
                .to_be_bytes()
                .to_vec();
            encoded.extend_from_slice(value);
            encoded
        })
        .collect();
    values.sort();
    let mut output = Vec::new();
    output.extend_from_slice(
        &u32::try_from(values.len())
            .expect("validated set length fits u32")
            .to_be_bytes(),
    );
    for value in values {
        output.extend_from_slice(&value);
    }
    output
}

fn field(output: &mut Vec<u8>, tag: u16, payload: &[u8]) {
    output.extend_from_slice(&tag.to_be_bytes());
    output.extend_from_slice(
        &u32::try_from(payload.len())
            .expect("validated field length fits u32")
            .to_be_bytes(),
    );
    output.extend_from_slice(payload);
}

fn endpoint_tag(value: EndpointPolicy) -> u8 {
    match value {
        EndpointPolicy::OpenOpen => 1,
        EndpointPolicy::OpenClosed => 2,
        EndpointPolicy::ClosedOpen => 3,
        EndpointPolicy::ClosedClosed => 4,
    }
}

fn rounding_tag(value: RoundingMode) -> u8 {
    match value {
        RoundingMode::TowardZero => 1,
        RoundingMode::Floor => 2,
        RoundingMode::Ceiling => 3,
        RoundingMode::HalfEven => 4,
    }
}

fn validated_contract_digest(contract: &ValidatedContract, state_key: StateKeyV1) -> Sha256Digest {
    let lineage = contract.lineage();
    let mut preimage = VALIDATED_CONTRACT_DOMAIN_V1.to_vec();
    field(&mut preimage, 1, lineage.venue_namespace().as_bytes());
    field(&mut preimage, 2, lineage.source_contract_id().as_bytes());
    field(&mut preimage, 3, lineage.source_revision().as_bytes());
    field(
        &mut preimage,
        4,
        &lineage.source_observed_at().to_be_bytes(),
    );
    field(
        &mut preimage,
        5,
        lineage.source_document_digest().as_bytes(),
    );
    field(
        &mut preimage,
        6,
        lineage.normalization_profile_id().as_bytes(),
    );
    field(
        &mut preimage,
        7,
        &lineage.normalization_profile_version().to_be_bytes(),
    );
    field(
        &mut preimage,
        8,
        lineage.normalization_profile_digest().as_bytes(),
    );
    field(&mut preimage, 9, state_key.digest().as_bytes());
    hash(&preimage)
}

fn hash(bytes: &[u8]) -> Sha256Digest {
    Sha256Digest::from_bytes(Sha256::digest(bytes).into())
}
