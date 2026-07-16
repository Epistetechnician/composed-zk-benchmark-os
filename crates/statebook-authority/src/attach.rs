use crate::bounds::{
    ATTACH_RECEIPT_SCHEMA_V1, AUTHORITY_STATEMENT_SCHEMA_V1, CAPITAL_OVERLAY_SCHEMA_V1,
    LEGAL_OPS_GATE_AUTHORITY_OWNER_V1, LEGAL_OPS_GATE_LEGAL_REVIEW_V1,
    LEGAL_OPS_GATE_LIVE_PRODUCTS_DEFERRED_V1, LEGAL_OPS_GATE_LOSS_LIMITS_V1,
    LEGAL_OPS_GATE_OPERATIONAL_EVIDENCE_V1, LEGAL_OPS_GATE_THREAT_MODEL_V1,
    MAX_LIMITATION_OR_NONCLAIM_COUNT_V1, MAX_STATEMENT_BYTES_V1, SYNTHETIC_AUTHORITY_NAMESPACE_V1,
    SYNTHETIC_AUTHORITY_PROFILE_V1,
};
use crate::canonical::{
    attach_receipt_digest, authority_statement_digest, capital_overlay_digest, digest_to_hex,
};
use crate::error::AuthorityErrorV1;
use crate::json_util::{
    parse_strict_json, read_string_array, reject_unknown_fields, require_bool, require_i64,
    require_string, validate_digest_hex, validate_identifier, validate_rational,
};
use crate::types::{
    AttachReceiptV1, AuthorityRegistryV1, CapitalOverlayStatusV1, CapitalOverlayV1,
    StatementStatusV1,
};

const CLOSED_PROFILES: &[&str] = &[SYNTHETIC_AUTHORITY_PROFILE_V1];

pub fn attach_authority_statement_v1(
    statement_bytes: &[u8],
    registry: &mut AuthorityRegistryV1,
    evaluated_at: i64,
) -> Result<AttachReceiptV1, AuthorityErrorV1> {
    if statement_bytes.len() > MAX_STATEMENT_BYTES_V1 {
        return Err(AuthorityErrorV1::StatementTooLarge);
    }

    let value = parse_strict_json(statement_bytes)?;
    reject_unknown_fields(
        &value,
        &[
            "schema_version",
            "profile_id",
            "authority_namespace",
            "authority_id",
            "statement_revision",
            "eligible_account",
            "model_id",
            "model_version",
            "model_digest",
            "margin_rule_id",
            "jurisdiction",
            "subject_terms_digest",
            "economic_residual_digest",
            "recognized_numerator",
            "recognized_denominator",
            "issued_at",
            "expires_at",
            "grants_execution_authority",
            "limitations",
        ],
    )?;

    let schema_version = require_string(&value, "schema_version")?;
    if schema_version != AUTHORITY_STATEMENT_SCHEMA_V1 {
        return Err(AuthorityErrorV1::UnknownSchemaVersion);
    }
    let profile_id = require_string(&value, "profile_id")?;
    if !CLOSED_PROFILES.contains(&profile_id.as_str()) {
        return Err(AuthorityErrorV1::UnknownProfile(profile_id));
    }
    let authority_namespace = require_string(&value, "authority_namespace")?;
    if authority_namespace != SYNTHETIC_AUTHORITY_NAMESPACE_V1 {
        return Err(AuthorityErrorV1::AuthorityNamespaceMismatch);
    }

    let authority_id = require_string(&value, "authority_id")?;
    let statement_revision = require_string(&value, "statement_revision")?;
    let eligible_account = require_string(&value, "eligible_account")?;
    let model_id = require_string(&value, "model_id")?;
    let model_version = require_string(&value, "model_version")?;
    let model_digest = require_string(&value, "model_digest")?;
    let margin_rule_id = require_string(&value, "margin_rule_id")?;
    let jurisdiction = require_string(&value, "jurisdiction")?;
    let subject_terms_digest = require_string(&value, "subject_terms_digest")?;
    let economic_residual_digest = require_string(&value, "economic_residual_digest")?;
    let recognized_numerator = require_string(&value, "recognized_numerator")?;
    let recognized_denominator = require_string(&value, "recognized_denominator")?;
    let issued_at = require_i64(&value, "issued_at")?;
    let expires_at = require_i64(&value, "expires_at")?;
    let grants_execution_authority = require_bool(&value, "grants_execution_authority")?;
    let limitations = read_string_array(&value, "limitations")?;

    if grants_execution_authority {
        return Err(AuthorityErrorV1::ExecutionAuthorityGrantForbidden);
    }
    if issued_at >= expires_at {
        return Err(AuthorityErrorV1::InvalidValidityWindow);
    }
    if limitations.len() > MAX_LIMITATION_OR_NONCLAIM_COUNT_V1 {
        return Err(AuthorityErrorV1::TooManyLimitationsOrNonclaims);
    }

    for field in [
        &profile_id,
        &authority_namespace,
        &authority_id,
        &statement_revision,
        &eligible_account,
        &model_id,
        &model_version,
        &margin_rule_id,
        &jurisdiction,
    ] {
        validate_identifier(field)?;
    }
    validate_digest_hex(&model_digest)?;
    validate_digest_hex(&subject_terms_digest)?;
    validate_digest_hex(&economic_residual_digest)?;
    validate_rational(&recognized_numerator, &recognized_denominator)?;

    let statement_digest = digest_to_hex(authority_statement_digest(
        &profile_id,
        &authority_namespace,
        &authority_id,
        &statement_revision,
        &subject_terms_digest,
        &economic_residual_digest,
        &recognized_numerator,
        &recognized_denominator,
        issued_at,
        expires_at,
    ));

    let registration = registry.register(
        &profile_id,
        &authority_namespace,
        &authority_id,
        &statement_revision,
        &eligible_account,
        &model_id,
        &model_version,
        &model_digest,
        &margin_rule_id,
        &jurisdiction,
        &subject_terms_digest,
        &economic_residual_digest,
        &recognized_numerator,
        &recognized_denominator,
        issued_at,
        expires_at,
        &statement_digest,
    )?;

    let overlay = evaluate_capital_overlay(
        &registration.authority_id,
        &registration.eligible_account,
        &registration.subject_terms_digest,
        &registration.economic_residual_digest,
        &registration.recognized_numerator,
        &registration.recognized_denominator,
        registration.status,
        registration.issued_at,
        registration.expires_at,
        evaluated_at,
    );

    let attach_digest = digest_to_hex(attach_receipt_digest(
        &profile_id,
        &authority_namespace,
        &authority_id,
        &statement_revision,
        &statement_digest,
        &registration.registration_digest,
        &overlay.overlay_digest,
        &economic_residual_digest,
    ));

    Ok(AttachReceiptV1 {
        schema_version: ATTACH_RECEIPT_SCHEMA_V1.to_owned(),
        profile_id,
        authority_namespace,
        authority_id,
        statement_revision,
        subject_terms_digest,
        economic_residual_digest,
        statement_digest,
        registration_digest: registration.registration_digest,
        attach_receipt_digest: attach_digest,
        grants_execution_authority: false,
        capital_overlay: overlay,
        adapter_nonclaims: default_attach_nonclaims(),
        legal_ops_gate_deferred: legal_ops_gate_deferred(),
    })
}

pub fn evaluate_attached_statement_v1(
    registry: &AuthorityRegistryV1,
    authority_namespace: &str,
    authority_id: &str,
    statement_revision: &str,
    evaluated_at: i64,
) -> Result<CapitalOverlayV1, AuthorityErrorV1> {
    let Some(registration) = registry.get(authority_namespace, authority_id, statement_revision)
    else {
        return Err(AuthorityErrorV1::StatementNotFound);
    };
    Ok(evaluate_capital_overlay(
        &registration.authority_id,
        &registration.eligible_account,
        &registration.subject_terms_digest,
        &registration.economic_residual_digest,
        &registration.recognized_numerator,
        &registration.recognized_denominator,
        registration.status,
        registration.issued_at,
        registration.expires_at,
        evaluated_at,
    ))
}

#[allow(clippy::too_many_arguments)]
fn evaluate_capital_overlay(
    authority_id: &str,
    eligible_account: &str,
    subject_terms_digest: &str,
    economic_residual_digest: &str,
    recognized_numerator: &str,
    recognized_denominator: &str,
    status: StatementStatusV1,
    issued_at: i64,
    expires_at: i64,
    evaluated_at: i64,
) -> CapitalOverlayV1 {
    let overlay_status = if status == StatementStatusV1::Revoked
        || evaluated_at >= expires_at
        || evaluated_at < issued_at
    {
        CapitalOverlayStatusV1::NotRecognizedInFixture
    } else if recognized_numerator == recognized_denominator {
        CapitalOverlayStatusV1::RecognizedInFixture
    } else if recognized_numerator == "0" {
        CapitalOverlayStatusV1::NotRecognizedInFixture
    } else {
        CapitalOverlayStatusV1::PartiallyRecognizedInFixture
    };

    let overlay_digest = digest_to_hex(capital_overlay_digest(
        overlay_status.as_str(),
        authority_id,
        eligible_account,
        subject_terms_digest,
        economic_residual_digest,
        recognized_numerator,
        recognized_denominator,
        evaluated_at,
    ));

    CapitalOverlayV1 {
        schema_version: CAPITAL_OVERLAY_SCHEMA_V1.to_owned(),
        status: overlay_status,
        authority_id: authority_id.to_owned(),
        eligible_account: eligible_account.to_owned(),
        subject_terms_digest: subject_terms_digest.to_owned(),
        economic_residual_digest: economic_residual_digest.to_owned(),
        recognized_numerator: recognized_numerator.to_owned(),
        recognized_denominator: recognized_denominator.to_owned(),
        evaluated_at,
        overlay_digest,
    }
}

fn default_attach_nonclaims() -> Vec<String> {
    vec![
        "does_not_prove_price_or_solvency".to_owned(),
        "does_not_prove_semantics_or_legality".to_owned(),
        "does_not_prove_execution_or_finality".to_owned(),
        "does_not_grant_execution_authority".to_owned(),
        "synthetic_fixture_only".to_owned(),
        "capital_overlay_only".to_owned(),
        "no_value_movement".to_owned(),
        "live_authority_products_deferred".to_owned(),
    ]
}

fn legal_ops_gate_deferred() -> Vec<String> {
    vec![
        LEGAL_OPS_GATE_THREAT_MODEL_V1.to_owned(),
        LEGAL_OPS_GATE_LEGAL_REVIEW_V1.to_owned(),
        LEGAL_OPS_GATE_OPERATIONAL_EVIDENCE_V1.to_owned(),
        LEGAL_OPS_GATE_LOSS_LIMITS_V1.to_owned(),
        LEGAL_OPS_GATE_AUTHORITY_OWNER_V1.to_owned(),
        LEGAL_OPS_GATE_LIVE_PRODUCTS_DEFERRED_V1.to_owned(),
    ]
}
