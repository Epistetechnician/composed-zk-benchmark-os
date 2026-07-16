use serde_json::Value;

use crate::bounds::{
    FIXTURE_ADAPTER_SCHEMA_VERSION_V1, HANDOFF_SCHEMA_VERSION_V1, HSAI_FIXTURE_SCHEMA_VERSION_V1,
    MAX_FIXTURE_BYTES_V1, MAX_NONCLAIMS_V1, MAX_OBSERVATIONS_V1,
};
use crate::error::AdapterErrorV1;
use crate::json_util::{
    parse_strict_json_adapter, reject_unknown_fields_adapter, require_string_adapter,
    validate_digest_hex_adapter, validate_identifier_adapter,
};
use crate::types::{
    DecisionHandoffInputV1, FixtureAdapterInputV1, HandoffEnvelopeV1, MappedObservationV1,
};

const FIXTURE_PROFILES: &[&str] = &["hermetic-observation-v1", "hermetic-minimal-v1"];

pub fn parse_fixture_adapter_input_v1(
    bytes: &[u8],
) -> Result<FixtureAdapterInputV1, AdapterErrorV1> {
    if bytes.len() > MAX_FIXTURE_BYTES_V1 {
        return Err(AdapterErrorV1::FixtureTooLarge);
    }
    let value = parse_strict_json_adapter(bytes)?;
    reject_unknown_fields_adapter(
        &value,
        &[
            "schema_version",
            "profile_id",
            "issuer",
            "subject",
            "property",
            "scope",
            "nonce",
            "issue_at",
            "expiry_at",
            "trust_roots",
            "policy_version",
            "source_refs",
            "dependency_roots",
            "unknown_facts",
        ],
    )?;
    let schema_version = require_string_adapter(&value, "schema_version")?;
    if schema_version != FIXTURE_ADAPTER_SCHEMA_VERSION_V1 {
        return Err(AdapterErrorV1::UnknownSchemaVersion);
    }
    let profile_id = require_string_adapter(&value, "profile_id")?;
    if !FIXTURE_PROFILES.contains(&profile_id.as_str()) {
        return Err(AdapterErrorV1::UnknownProfile(profile_id));
    }
    let input = FixtureAdapterInputV1 {
        schema_version,
        profile_id,
        issuer: require_string_adapter(&value, "issuer")?,
        subject: require_string_adapter(&value, "subject")?,
        property: require_string_adapter(&value, "property")?,
        scope: require_string_adapter(&value, "scope")?,
        nonce: require_string_adapter(&value, "nonce")?,
        issue_at: value
            .get("issue_at")
            .and_then(Value::as_i64)
            .ok_or_else(|| AdapterErrorV1::MissingField("issue_at".into()))?,
        expiry_at: value.get("expiry_at").and_then(Value::as_i64),
        trust_roots: read_string_array(&value, "trust_roots")?,
        policy_version: require_string_adapter(&value, "policy_version")?,
        source_refs: read_string_array(&value, "source_refs")?,
        dependency_roots: read_string_array(&value, "dependency_roots")?,
        unknown_facts: read_string_array(&value, "unknown_facts")?,
    };
    for field in [
        &input.issuer,
        &input.subject,
        &input.property,
        &input.scope,
        &input.nonce,
        &input.policy_version,
    ] {
        validate_identifier_adapter(field)?;
    }
    if input.trust_roots.len() > MAX_OBSERVATIONS_V1 {
        return Err(AdapterErrorV1::TooManyObservations);
    }
    if input.unknown_facts.len() > MAX_NONCLAIMS_V1 {
        return Err(AdapterErrorV1::TooManyNonclaims);
    }
    Ok(input)
}

pub fn map_fixture_observation_v1(
    input: &FixtureAdapterInputV1,
) -> Result<MappedObservationV1, AdapterErrorV1> {
    Ok(MappedObservationV1 {
        issuer: input.issuer.clone(),
        subject: input.subject.clone(),
        property: input.property.clone(),
        scope: input.scope.clone(),
        nonce: input.nonce.clone(),
        issue_at: input.issue_at,
        expiry_at: input.expiry_at,
        trust_roots: input.trust_roots.clone(),
        policy_version: input.policy_version.clone(),
        source_refs: input.source_refs.clone(),
        dependency_roots: input.dependency_roots.clone(),
        unknown_facts: input.unknown_facts.clone(),
        evidence_maturity: "fixture_qualified".to_owned(),
        adapter_nonclaims: default_adapter_nonclaims(),
    })
}

pub fn map_hsai_fixture_envelope_v1(bytes: &[u8]) -> Result<MappedObservationV1, AdapterErrorV1> {
    if bytes.len() > MAX_FIXTURE_BYTES_V1 {
        return Err(AdapterErrorV1::FixtureTooLarge);
    }
    let value = parse_strict_json_adapter(bytes)?;
    reject_unknown_fields_adapter(
        &value,
        &[
            "schema_version",
            "maturity",
            "trust_roots",
            "valid",
            "facts",
            "unknown_facts",
        ],
    )?;
    let schema_version = require_string_adapter(&value, "schema_version")?;
    if schema_version != HSAI_FIXTURE_SCHEMA_VERSION_V1 {
        return Err(AdapterErrorV1::UnknownSchemaVersion);
    }
    let maturity = require_string_adapter(&value, "maturity")?;
    if !matches!(
        maturity.as_str(),
        "provisional" | "supported" | "proven" | "unknown"
    ) {
        return Err(AdapterErrorV1::UnknownField("maturity".into()));
    }
    let facts = value
        .get("facts")
        .ok_or_else(|| AdapterErrorV1::MissingField("facts".into()))?;
    reject_unknown_fields_adapter(
        facts,
        &[
            "issuer",
            "subject",
            "property",
            "scope",
            "nonce",
            "issue_at",
            "expiry_at",
            "policy_version",
            "source_refs",
            "dependency_roots",
        ],
    )?;
    let issuer = require_string_adapter(facts, "issuer")?;
    let subject = require_string_adapter(facts, "subject")?;
    let property = require_string_adapter(facts, "property")?;
    let scope = require_string_adapter(facts, "scope")?;
    let nonce = require_string_adapter(facts, "nonce")?;
    for field in [&issuer, &subject, &property, &scope, &nonce] {
        validate_identifier_adapter(field)?;
    }
    let policy_version = facts
        .get("policy_version")
        .and_then(Value::as_str)
        .unwrap_or("unknown")
        .to_owned();
    validate_identifier_adapter(&policy_version)?;
    let trust_roots = read_string_array(&value, "trust_roots")?;
    if trust_roots.len() > MAX_OBSERVATIONS_V1 {
        return Err(AdapterErrorV1::TooManyObservations);
    }
    let unknown_facts = read_string_array(&value, "unknown_facts")?;
    if unknown_facts.len() > MAX_NONCLAIMS_V1 {
        return Err(AdapterErrorV1::TooManyNonclaims);
    }
    let mut nonclaims = default_adapter_nonclaims();
    nonclaims.push("does_not_prove_price_or_solvency".to_owned());
    nonclaims.push("does_not_prove_execution_or_finality".to_owned());
    nonclaims.push("evidence_maturity_not_financial_expiry".to_owned());
    Ok(MappedObservationV1 {
        issuer,
        subject,
        property,
        scope,
        nonce,
        issue_at: facts
            .get("issue_at")
            .and_then(Value::as_i64)
            .ok_or_else(|| AdapterErrorV1::MissingField("facts.issue_at".into()))?,
        expiry_at: facts.get("expiry_at").and_then(Value::as_i64),
        trust_roots,
        policy_version,
        source_refs: read_string_array(facts, "source_refs")?,
        dependency_roots: read_string_array(facts, "dependency_roots")?,
        unknown_facts,
        evidence_maturity: maturity,
        adapter_nonclaims: nonclaims,
    })
}

pub fn handoff_decision_record_v1(
    decision_json_or_digest_bound: &DecisionHandoffInputV1<'_>,
) -> Result<HandoffEnvelopeV1, AdapterErrorV1> {
    let (decision_record_digest, intent_digest, decision_context_digest, outcome) =
        match decision_json_or_digest_bound {
            DecisionHandoffInputV1::DecisionJson(json_text) => {
                let value = parse_strict_json_adapter(json_text.as_bytes())?;
                reject_unknown_fields_adapter(
                    &value,
                    &[
                        "record_digest",
                        "intent_digest",
                        "decision_context_digest",
                        "outcome",
                    ],
                )?;
                (
                    require_string_adapter(&value, "record_digest")?,
                    require_string_adapter(&value, "intent_digest")?,
                    require_string_adapter(&value, "decision_context_digest")?,
                    require_string_adapter(&value, "outcome")?,
                )
            }
            DecisionHandoffInputV1::DigestBound {
                decision_record_digest,
                intent_digest,
                decision_context_digest,
                outcome,
            } => (
                (*decision_record_digest).to_owned(),
                (*intent_digest).to_owned(),
                (*decision_context_digest).to_owned(),
                (*outcome).to_owned(),
            ),
        };
    validate_digest_hex_adapter(&decision_record_digest)?;
    validate_digest_hex_adapter(&intent_digest)?;
    validate_digest_hex_adapter(&decision_context_digest)?;
    validate_identifier_adapter(&outcome)?;
    Ok(HandoffEnvelopeV1 {
        schema_version: HANDOFF_SCHEMA_VERSION_V1.to_owned(),
        grants_authority: false,
        decision_record_digest,
        intent_digest,
        decision_context_digest,
        outcome,
        adapter_nonclaims: handoff_nonclaims(),
    })
}

fn read_string_array(value: &Value, field: &str) -> Result<Vec<String>, AdapterErrorV1> {
    let Some(array) = value.get(field).and_then(Value::as_array) else {
        return Ok(Vec::new());
    };
    let mut out = Vec::new();
    for item in array {
        let text = item.as_str().ok_or(AdapterErrorV1::MalformedJson)?;
        validate_identifier_adapter(text)?;
        out.push(text.to_owned());
    }
    Ok(out)
}

fn default_adapter_nonclaims() -> Vec<String> {
    vec![
        "does_not_prove_price_or_solvency".to_owned(),
        "does_not_prove_semantics_or_legality".to_owned(),
        "does_not_grant_authority".to_owned(),
    ]
}

fn handoff_nonclaims() -> Vec<String> {
    vec![
        "proposal_only".to_owned(),
        "no_admission_mutation".to_owned(),
        "no_evidence_ledger_append".to_owned(),
        "no_signing_or_custody".to_owned(),
        "no_transfer_command".to_owned(),
        "grants_authority_false".to_owned(),
    ]
}
