use statebook_core::parse_source_contract_v1;

use crate::bounds::{
    CAPTURED_ARTIFACT_SCHEMA_V1, IMPORT_RECEIPT_SCHEMA_V1, MAX_ARTIFACT_BYTES_V1,
    MAX_CLAIM_OR_LIMITATION_COUNT_V1, MAX_OBSERVATIONS_V1, SYNTHETIC_CLEARING_NAMESPACE_V1,
    SYNTHETIC_CLEARING_PROFILE_V1,
};
use crate::canonical::{
    captured_artifact_digest, digest_to_hex, import_receipt_digest, raw_sha256,
};
use crate::error::SourceErrorV1;
use crate::json_util::{
    parse_strict_json, read_string_array, reject_unknown_fields, require_i64, require_string,
    validate_digest_hex, validate_identifier,
};
use crate::types::{EvidenceClassV1, ImportReceiptV1, SourceRegistryV1};

const CLOSED_PROFILES: &[&str] = &[SYNTHETIC_CLEARING_PROFILE_V1];

pub fn import_captured_terms_v1(
    envelope_bytes: &[u8],
    terms_bytes: &[u8],
    registry: &mut SourceRegistryV1,
) -> Result<ImportReceiptV1, SourceErrorV1> {
    if envelope_bytes.len() > MAX_ARTIFACT_BYTES_V1 || terms_bytes.len() > MAX_ARTIFACT_BYTES_V1 {
        return Err(SourceErrorV1::ArtifactTooLarge);
    }

    let value = parse_strict_json(envelope_bytes)?;
    reject_unknown_fields(
        &value,
        &[
            "schema_version",
            "profile_id",
            "venue_namespace",
            "source_contract_id",
            "source_revision",
            "published_at",
            "retrieved_at",
            "evidence_class",
            "content_sha256",
            "supported_claims",
            "limitations",
            "unknown_facts",
        ],
    )?;

    let schema_version = require_string(&value, "schema_version")?;
    if schema_version != CAPTURED_ARTIFACT_SCHEMA_V1 {
        return Err(SourceErrorV1::UnknownSchemaVersion);
    }
    let profile_id = require_string(&value, "profile_id")?;
    if !CLOSED_PROFILES.contains(&profile_id.as_str()) {
        return Err(SourceErrorV1::UnknownProfile(profile_id));
    }
    let venue_namespace = require_string(&value, "venue_namespace")?;
    if venue_namespace != SYNTHETIC_CLEARING_NAMESPACE_V1 {
        return Err(SourceErrorV1::VenueNamespaceMismatch);
    }
    let source_contract_id = require_string(&value, "source_contract_id")?;
    let source_revision = require_string(&value, "source_revision")?;
    let published_at = require_i64(&value, "published_at")?;
    let retrieved_at = require_i64(&value, "retrieved_at")?;
    let evidence_class_text = require_string(&value, "evidence_class")?;
    let evidence_class = EvidenceClassV1::parse(&evidence_class_text)
        .ok_or(SourceErrorV1::UnknownEvidenceClass(evidence_class_text))?;
    if !evidence_class.may_enter_assurance() {
        return Err(SourceErrorV1::IllustrativeNarrativeRejected);
    }
    let content_sha256 = require_string(&value, "content_sha256")?;
    validate_digest_hex(&content_sha256)?;

    for field in [
        &profile_id,
        &venue_namespace,
        &source_contract_id,
        &source_revision,
    ] {
        validate_identifier(field)?;
    }

    let supported_claims = read_string_array(&value, "supported_claims")?;
    let limitations = read_string_array(&value, "limitations")?;
    let unknown_facts = read_string_array(&value, "unknown_facts")?;
    if supported_claims.len() > MAX_CLAIM_OR_LIMITATION_COUNT_V1
        || limitations.len() > MAX_CLAIM_OR_LIMITATION_COUNT_V1
    {
        return Err(SourceErrorV1::TooManyClaimsOrLimitations);
    }
    if unknown_facts.len() > MAX_OBSERVATIONS_V1 {
        return Err(SourceErrorV1::TooManyObservations);
    }

    let computed = digest_to_hex(raw_sha256(terms_bytes));
    if computed != content_sha256 {
        return Err(SourceErrorV1::ContentDigestMismatch);
    }

    parse_source_contract_v1(terms_bytes).map_err(|_| SourceErrorV1::TermsParseRejected)?;

    let registration = registry.register(
        &venue_namespace,
        &source_contract_id,
        &source_revision,
        published_at,
        retrieved_at,
        evidence_class,
        &content_sha256,
        supported_claims,
        limitations,
    )?;

    let artifact_digest = digest_to_hex(captured_artifact_digest(
        &profile_id,
        &venue_namespace,
        &content_sha256,
        envelope_bytes,
    ));
    let import_digest = digest_to_hex(import_receipt_digest(
        &profile_id,
        &venue_namespace,
        &source_contract_id,
        &source_revision,
        &content_sha256,
        &artifact_digest,
        &registration.registration_digest,
    ));

    Ok(ImportReceiptV1 {
        schema_version: IMPORT_RECEIPT_SCHEMA_V1.to_owned(),
        profile_id,
        venue_namespace,
        source_contract_id,
        source_revision,
        evidence_class,
        content_sha256,
        artifact_digest,
        registration_digest: registration.registration_digest,
        import_receipt_digest: import_digest,
        unknown_facts,
        adapter_nonclaims: default_import_nonclaims(),
    })
}

fn default_import_nonclaims() -> Vec<String> {
    vec![
        "does_not_prove_price_or_solvency".to_owned(),
        "does_not_prove_semantics_or_legality".to_owned(),
        "does_not_prove_execution_or_finality".to_owned(),
        "does_not_grant_authority".to_owned(),
        "captured_replay_only".to_owned(),
        "no_live_network_in_this_slice".to_owned(),
    ]
}
