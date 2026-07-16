use std::path::Path;

use serde_json::json;
use statebook_authority::{
    attach_authority_statement_v1, evaluate_attached_statement_v1, AuthorityRegistryV1,
    CapitalOverlayStatusV1, SYNTHETIC_AUTHORITY_NAMESPACE_V1, SYNTHETIC_AUTHORITY_PROFILE_V1,
};
use statebook_core::{
    analyze_terminal_residual_v1, derive_state_key, parse_normalization_profile_v1,
    parse_source_contract_v1, validate_and_lower, ContractPositionV1, DeclaredStateDomainV1,
    DeclaredTerminalStateV1, SignedRational,
};
use statebook_report::{
    build_golden_bundle_from_decision, handoff_decision_record_v1, materialize_audit_bundle_v1,
    readback_validate_audit_bundle_v1, DecisionHandoffInputV1,
};
use statebook_settlement::{
    compose_completeness_reports_v1, decide_and_transition, parse_completeness_fixture_v1,
    parse_settlement_scenario_v1,
};
use statebook_source::{import_captured_terms_v1, SourceRegistryV1};

use crate::bounds::{EVALUATION_RECEIPT_SCHEMA_V1, GOLDEN_PATH_PROFILE_V1};
use crate::error::EvaluationErrorV1;
use crate::types::EvaluationReceiptV1;

const P6_ENVELOPE: &[u8] =
    include_bytes!("../../statebook-source/tests/fixtures/captured_envelope_v1.json");
const P6_TERMS: &[u8] =
    include_bytes!("../../statebook-source/tests/fixtures/terms_payload_v1.json");
const P1_PROFILE: &[u8] =
    include_bytes!("../../statebook-core/tests/fixtures/normalization_profile_v1.json");
const P3_FIXTURE: &[u8] =
    include_bytes!("../../statebook-settlement/tests/fixtures/completeness_reports_v1.json");
const P4_IMMEDIATE: &[u8] =
    include_bytes!("../../statebook-settlement/tests/fixtures/p4/immediate_v1.json");

fn rational(numerator: i128, denominator: u128) -> SignedRational {
    SignedRational::new(numerator, denominator).expect("fixture rational")
}

/// Run the frozen hermetic P1–P7 golden path into `bundle_root`.
pub fn run_hermetic_golden_path_v1(
    bundle_root: &Path,
) -> Result<EvaluationReceiptV1, EvaluationErrorV1> {
    let mut source_registry = SourceRegistryV1::new();
    let import = import_captured_terms_v1(P6_ENVELOPE, P6_TERMS, &mut source_registry)
        .map_err(|error| EvaluationErrorV1::SourceImport(error.to_string()))?;

    let profile = parse_normalization_profile_v1(P1_PROFILE)
        .map_err(|error| EvaluationErrorV1::SemanticPipeline(error.to_string()))?;
    let parsed = parse_source_contract_v1(P6_TERMS)
        .map_err(|error| EvaluationErrorV1::SemanticPipeline(error.to_string()))?;
    let contract = validate_and_lower(parsed, &profile)
        .map_err(|error| EvaluationErrorV1::SemanticPipeline(error.to_string()))?;
    let state_key_receipt = derive_state_key(&contract);
    let validated_contract_digest = state_key_receipt.validated_contract_digest().to_hex();
    let semantic = contract.completeness().clone();

    let domain = DeclaredStateDomainV1::try_new([
        DeclaredTerminalStateV1::try_new("below", rational(99_999, 1))
            .map_err(|error| EvaluationErrorV1::PayoffAnalysis(error.to_string()))?,
        DeclaredTerminalStateV1::try_new("equal", rational(100_000, 1))
            .map_err(|error| EvaluationErrorV1::PayoffAnalysis(error.to_string()))?,
        DeclaredTerminalStateV1::try_new("above", rational(100_001, 1))
            .map_err(|error| EvaluationErrorV1::PayoffAnalysis(error.to_string()))?,
    ])
    .map_err(|error| EvaluationErrorV1::PayoffAnalysis(error.to_string()))?;
    let payoff = analyze_terminal_residual_v1(
        ContractPositionV1::new(&contract, rational(1, 1)),
        &[ContractPositionV1::new(&contract, rational(1, 1))],
        &domain,
    )
    .map_err(|error| EvaluationErrorV1::PayoffAnalysis(error.to_string()))?;
    let payoff_domain_digest = payoff.domain_digest().to_hex();

    let completeness_fixture = parse_completeness_fixture_v1(P3_FIXTURE)
        .map_err(|error| EvaluationErrorV1::Completeness(error.to_string()))?;
    let completeness =
        compose_completeness_reports_v1(&semantic, &payoff, &completeness_fixture, 1500)
            .map_err(|error| EvaluationErrorV1::Completeness(error.to_string()))?;
    let capital_status = format!("{:?}", completeness.capital().status());

    let scenario = parse_settlement_scenario_v1(P4_IMMEDIATE)
        .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
    let evaluated_at = scenario.clock().now();
    let (request, state, clock) = scenario.into_kernel_input();
    let decision = decide_and_transition(request, state, clock)
        .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
    let decision_outcome = format!("{:?}", decision.outcome()).to_ascii_lowercase();
    let decision_record_digest = decision.record_digest().to_hex();

    let handoff = handoff_decision_record_v1(&DecisionHandoffInputV1::DigestBound {
        decision_record_digest: &decision_record_digest,
        intent_digest: &decision.intent_digest().to_hex(),
        decision_context_digest: &decision.decision_context_digest().to_hex(),
        outcome: "immediate",
    })
    .map_err(|error| EvaluationErrorV1::ReportBundle(error.to_string()))?;
    if handoff.grants_authority {
        return Err(EvaluationErrorV1::ReportBundle(
            "handoff granted authority".into(),
        ));
    }

    let decision_json = json!({
        "schema_version": 1,
        "outcome": "immediate",
        "intent_digest": decision.intent_digest().to_hex(),
        "decision_context_digest": decision.decision_context_digest().to_hex(),
        "instant_release_amount": {
            "numerator": decision.instant_release_amount().numerator().to_string(),
            "denominator": decision.instant_release_amount().denominator().to_string()
        },
        "ledger_tip_before": "0000000000000000000000000000000000000000000000000000000000000000",
        "ledger_tip_after": decision_record_digest,
        "reasons": [],
        "evaluated_at": evaluated_at,
        "record_digest": decision_record_digest
    });
    let bundle = build_golden_bundle_from_decision("e2e-golden-bundle-v1", &decision_json)
        .map_err(|error| EvaluationErrorV1::ReportBundle(error.to_string()))?;
    let materialize = materialize_audit_bundle_v1(bundle_root, &bundle)
        .map_err(|error| EvaluationErrorV1::ReportBundle(error.to_string()))?;
    let readback = readback_validate_audit_bundle_v1(bundle_root)
        .map_err(|error| EvaluationErrorV1::ReportBundle(error.to_string()))?;
    if materialize.manifest_digest != readback.manifest_digest {
        return Err(EvaluationErrorV1::DigestBindingMismatch(
            "manifest digest mismatch after readback".into(),
        ));
    }

    let statement = json!({
        "schema_version": "statebook-p7-authority-statement:v1",
        "profile_id": SYNTHETIC_AUTHORITY_PROFILE_V1,
        "authority_namespace": SYNTHETIC_AUTHORITY_NAMESPACE_V1,
        "authority_id": "synthetic-clearing-officer-v1",
        "statement_revision": "e2e-rev-1",
        "eligible_account": "acct-fixture-001",
        "model_id": "synthetic-margin-model-v1",
        "model_version": "1",
        "model_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "margin_rule_id": "synthetic-margin-rule-v1",
        "jurisdiction": "synthetic-jurisdiction-v1",
        "subject_terms_digest": validated_contract_digest,
        "economic_residual_digest": payoff_domain_digest,
        "recognized_numerator": "1",
        "recognized_denominator": "1",
        "issued_at": 1000,
        "expires_at": 2000,
        "grants_execution_authority": false,
        "limitations": ["synthetic-non-authoritative", "e2e-harness-only"]
    });
    let statement_bytes = serde_json::to_vec(&statement)
        .map_err(|error| EvaluationErrorV1::Authority(error.to_string()))?;
    let mut authority_registry = AuthorityRegistryV1::new();
    let attach = attach_authority_statement_v1(&statement_bytes, &mut authority_registry, 1500)
        .map_err(|error| EvaluationErrorV1::Authority(error.to_string()))?;
    if attach.subject_terms_digest != validated_contract_digest
        || attach.economic_residual_digest != payoff_domain_digest
    {
        return Err(EvaluationErrorV1::DigestBindingMismatch(
            "authority receipt digests diverged from P1/P2".into(),
        ));
    }
    if attach.grants_execution_authority {
        return Err(EvaluationErrorV1::Authority(
            "attach granted execution authority".into(),
        ));
    }
    let overlay = evaluate_attached_statement_v1(
        &authority_registry,
        &attach.authority_namespace,
        &attach.authority_id,
        &attach.statement_revision,
        1500,
    )
    .map_err(|error| EvaluationErrorV1::Authority(error.to_string()))?;
    if overlay.status != CapitalOverlayStatusV1::RecognizedInFixture {
        return Err(EvaluationErrorV1::Authority(format!(
            "unexpected overlay status {:?}",
            overlay.status
        )));
    }

    Ok(EvaluationReceiptV1 {
        schema_version: EVALUATION_RECEIPT_SCHEMA_V1.to_owned(),
        profile_id: GOLDEN_PATH_PROFILE_V1.to_owned(),
        source_import_digest: import.import_receipt_digest,
        state_key: state_key_receipt.state_key().to_hex(),
        validated_contract_digest,
        payoff_domain_digest,
        payoff_status: format!("{:?}", payoff.status()),
        capital_status,
        decision_outcome,
        decision_record_digest,
        handoff_grants_authority: false,
        bundle_manifest_digest: readback.manifest_digest,
        authority_attach_digest: attach.attach_receipt_digest,
        authority_overlay_status: overlay.status.as_str().to_owned(),
        grants_execution_authority: false,
        nonclaims: vec![
            "hermetic_composed_regression_only".to_owned(),
            "does_not_grant_live_authority".to_owned(),
            "does_not_calibrate_production_thresholds".to_owned(),
            "no_value_movement".to_owned(),
            "p7_legal_ops_gate_unsatisfied".to_owned(),
        ],
    })
}

/// Reject P7 attach when the caller-supplied subject digest does not match the
/// golden-path validated contract digest.
pub fn reject_unbound_authority_statement_v1(
    validated_contract_digest: &str,
    forged_subject_terms_digest: &str,
) -> Result<(), EvaluationErrorV1> {
    if validated_contract_digest == forged_subject_terms_digest {
        return Err(EvaluationErrorV1::DigestBindingMismatch(
            "forged digest unexpectedly matched".into(),
        ));
    }
    Err(EvaluationErrorV1::DigestBindingMismatch(format!(
        "subject_terms_digest {forged_subject_terms_digest} != validated_contract_digest {validated_contract_digest}"
    )))
}
