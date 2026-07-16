use crate::bounds::{
    HERMETIC_PROFILE_V1, MAX_CONTROLLER_NAMES_V1, MAX_NONCLAIMS_V1, MAX_PACKAGE_BYTES_V1,
    PACKAGE_SCHEMA_VERSION_V1, RECEIPT_SCHEMA_VERSION_V1,
};
use crate::canonical::{
    authority_package_digest, digest_to_hex, loss_bound_digest, nonclaim_set_digest,
    preflight_receipt_digest,
};
use crate::error::AuthorityErrorV1;
use crate::json_util::{
    parse_strict_json, read_string_array, reject_unknown_fields, require_bool, require_string,
    validate_digest_hex, validate_exact_rational, validate_identifier,
};
use crate::types::{
    AuditRetentionV1, AuthorityPackageV1, ExactRationalV1, HandoffBindingV1, PauseSemanticsV1,
    PreflightOutcomeV1, PreflightReceiptV1, ProductionGateV1, RollbackSemanticsV1,
};

pub fn evaluate_authority_preflight_v1(
    package_bytes: &[u8],
) -> Result<(AuthorityPackageV1, PreflightReceiptV1), AuthorityErrorV1> {
    if package_bytes.len() > MAX_PACKAGE_BYTES_V1 {
        return Err(AuthorityErrorV1::PackageTooLarge);
    }
    let value = parse_strict_json(package_bytes)?;
    reject_unknown_fields(
        &value,
        &[
            "schema_version",
            "profile_id",
            "authority_owner",
            "maximum_loss",
            "rollback_semantics",
            "pause_semantics",
            "audit_retention",
            "legal_domain",
            "production_gate",
            "controller_names",
            "handoff",
        ],
    )?;

    let schema_version = require_string(&value, "schema_version")?;
    if schema_version != PACKAGE_SCHEMA_VERSION_V1 {
        return Err(AuthorityErrorV1::UnknownSchemaVersion);
    }
    let profile_id = require_string(&value, "profile_id")?;
    if profile_id != HERMETIC_PROFILE_V1 {
        return Err(AuthorityErrorV1::UnknownProfile(profile_id));
    }
    let authority_owner = require_string(&value, "authority_owner")?;
    validate_identifier(&authority_owner)?;
    let legal_domain = require_string(&value, "legal_domain")?;
    validate_identifier(&legal_domain)?;

    let maximum_loss_value = value
        .get("maximum_loss")
        .ok_or(AuthorityErrorV1::MissingField("maximum_loss".into()))?;
    reject_unknown_fields(maximum_loss_value, &["numerator", "denominator"])?;
    let maximum_loss = ExactRationalV1 {
        numerator: require_string(maximum_loss_value, "numerator")?,
        denominator: require_string(maximum_loss_value, "denominator")?,
    };
    validate_exact_rational(&maximum_loss)?;

    let rollback_text = require_string(&value, "rollback_semantics")?;
    let rollback_semantics = RollbackSemanticsV1::parse(&rollback_text)
        .ok_or(AuthorityErrorV1::UnknownEnum(rollback_text))?;
    let pause_text = require_string(&value, "pause_semantics")?;
    let pause_semantics =
        PauseSemanticsV1::parse(&pause_text).ok_or(AuthorityErrorV1::UnknownEnum(pause_text))?;
    let retention_text = require_string(&value, "audit_retention")?;
    let audit_retention = AuditRetentionV1::parse(&retention_text)
        .ok_or(AuthorityErrorV1::UnknownEnum(retention_text))?;
    let gate_text = require_string(&value, "production_gate")?;
    if gate_text == "authorized" {
        return Err(AuthorityErrorV1::AuthorizedGateRejected);
    }
    let production_gate =
        ProductionGateV1::parse(&gate_text).ok_or(AuthorityErrorV1::UnknownEnum(gate_text))?;

    let controller_names = read_string_array(&value, "controller_names")?;
    if controller_names.len() > MAX_CONTROLLER_NAMES_V1 {
        return Err(AuthorityErrorV1::TooManyControllerNames);
    }

    let handoff_value = value
        .get("handoff")
        .ok_or(AuthorityErrorV1::MissingField("handoff".into()))?;
    reject_unknown_fields(
        handoff_value,
        &[
            "decision_record_digest",
            "intent_digest",
            "decision_context_digest",
            "outcome",
            "grants_authority",
        ],
    )?;
    let handoff = HandoffBindingV1 {
        decision_record_digest: require_string(handoff_value, "decision_record_digest")?,
        intent_digest: require_string(handoff_value, "intent_digest")?,
        decision_context_digest: require_string(handoff_value, "decision_context_digest")?,
        outcome: require_string(handoff_value, "outcome")?,
        grants_authority: require_bool(handoff_value, "grants_authority")?,
    };
    if handoff.grants_authority {
        return Err(AuthorityErrorV1::HandoffGrantsAuthority);
    }
    validate_digest_hex(&handoff.decision_record_digest)?;
    validate_digest_hex(&handoff.intent_digest)?;
    validate_digest_hex(&handoff.decision_context_digest)?;
    validate_identifier(&handoff.outcome)?;

    let loss_digest = digest_to_hex(loss_bound_digest(
        &maximum_loss.numerator,
        &maximum_loss.denominator,
    ));
    let package_digest = digest_to_hex(authority_package_digest(
        &profile_id,
        &authority_owner,
        &loss_digest,
        rollback_semantics.as_str(),
        pause_semantics.as_str(),
        audit_retention.as_str(),
        &legal_domain,
        production_gate.as_str(),
        &handoff.decision_record_digest,
    ));

    let package = AuthorityPackageV1 {
        schema_version,
        profile_id: profile_id.clone(),
        authority_owner,
        maximum_loss,
        rollback_semantics,
        pause_semantics,
        audit_retention,
        legal_domain,
        production_gate,
        controller_names,
        handoff,
        package_digest: package_digest.clone(),
    };

    let outcome = match production_gate {
        ProductionGateV1::Incomplete => PreflightOutcomeV1::Incomplete,
        ProductionGateV1::Denied => PreflightOutcomeV1::Denied,
    };
    let adapter_nonclaims = default_nonclaims();
    if adapter_nonclaims.len() > MAX_NONCLAIMS_V1 {
        return Err(AuthorityErrorV1::TooManyNonclaims);
    }
    let nonclaim_digest = digest_to_hex(nonclaim_set_digest(&adapter_nonclaims));
    let outcome_text = match outcome {
        PreflightOutcomeV1::Incomplete => "incomplete",
        PreflightOutcomeV1::Denied => "denied",
    };
    let receipt_digest = digest_to_hex(preflight_receipt_digest(
        &profile_id,
        outcome_text,
        &package_digest,
        &loss_digest,
        &nonclaim_digest,
    ));

    let receipt = PreflightReceiptV1 {
        schema_version: RECEIPT_SCHEMA_VERSION_V1.to_owned(),
        profile_id,
        outcome,
        grants_authority: false,
        package_digest,
        preflight_receipt_digest: receipt_digest,
        loss_bound_digest: loss_digest,
        nonclaim_set_digest: nonclaim_digest,
        adapter_nonclaims,
    };
    Ok((package, receipt))
}

fn default_nonclaims() -> Vec<String> {
    vec![
        "no_controller_invoked".to_owned(),
        "no_signing_or_custody".to_owned(),
        "no_pause_actuator".to_owned(),
        "no_transfer_or_settlement".to_owned(),
        "grants_authority_false".to_owned(),
        "authorized_gate_forbidden_in_this_slice".to_owned(),
        "no_value_movement".to_owned(),
    ]
}
