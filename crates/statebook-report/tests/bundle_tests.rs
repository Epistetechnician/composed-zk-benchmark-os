mod support;

use statebook_report::{
    build_golden_bundle_from_decision, materialize_audit_bundle_v1,
    readback_validate_audit_bundle_v1, AuditBundleV1, BundleErrorV1, MAX_BUNDLE_BYTES_V1,
    MAX_NONCLAIMS_V1,
};
use statebook_settlement::parse_settlement_scenario_v1;
use std::fs;
use tempfile::tempdir;

const IMMEDIATE_FIXTURE: &[u8] =
    include_bytes!("../../statebook-settlement/tests/fixtures/p4/immediate_v1.json");

fn golden_bundle() -> AuditBundleV1 {
    let scenario = parse_settlement_scenario_v1(IMMEDIATE_FIXTURE).expect("parse scenario");
    let evaluated_at = scenario.clock().now();
    let (request, state, clock) = scenario.into_kernel_input();
    let record =
        statebook_settlement::decide_and_transition(request, state, clock).expect("decide");
    let outcome = serde_json::to_value(record.outcome()).expect("outcome");
    let reasons: Vec<String> = record
        .reasons()
        .iter()
        .map(|reason| {
            serde_json::to_value(reason)
                .expect("reason")
                .as_str()
                .expect("reason str")
                .to_owned()
        })
        .collect();
    let decision_json = serde_json::json!({
        "schema_version": 1,
        "outcome": outcome,
        "intent_digest": record.intent_digest().to_hex(),
        "decision_context_digest": record.decision_context_digest().to_hex(),
        "instant_release_amount": {
            "numerator": record.instant_release_amount().numerator().to_string(),
            "denominator": record.instant_release_amount().denominator().to_string()
        },
        "ledger_tip_before": "0000000000000000000000000000000000000000000000000000000000000000",
        "ledger_tip_after": record.record_digest().to_hex(),
        "reasons": reasons,
        "evaluated_at": evaluated_at,
        "record_digest": record.record_digest().to_hex()
    });
    build_golden_bundle_from_decision("golden-bundle-v1", &decision_json).expect("bundle")
}

#[test]
fn full_roundtrip_materialize_and_readback() {
    let dir = tempdir().unwrap();
    let bundle = golden_bundle();
    let receipt = materialize_audit_bundle_v1(dir.path(), &bundle).expect("materialize");
    let validated = readback_validate_audit_bundle_v1(dir.path()).expect("readback");
    assert_eq!(receipt.manifest_digest, validated.manifest_digest);
    assert_eq!(receipt.audit_trace_digest, validated.audit_trace_digest);
    assert_eq!(receipt.nonclaim_set_digest, validated.nonclaim_set_digest);
}

#[test]
fn missing_file_rejects() {
    let dir = tempdir().unwrap();
    let bundle = golden_bundle();
    materialize_audit_bundle_v1(dir.path(), &bundle).unwrap();
    fs::remove_file(dir.path().join("records/decision.json")).unwrap();
    assert!(matches!(
        readback_validate_audit_bundle_v1(dir.path()),
        Err(BundleErrorV1::MissingFile(_))
    ));
}

#[test]
fn extra_file_rejects() {
    let dir = tempdir().unwrap();
    let bundle = golden_bundle();
    materialize_audit_bundle_v1(dir.path(), &bundle).unwrap();
    fs::write(dir.path().join("records/extra.json"), b"{}\n").unwrap();
    assert!(matches!(
        readback_validate_audit_bundle_v1(dir.path()),
        Err(BundleErrorV1::ExtraFile(_))
    ));
}

#[test]
fn path_traversal_rejects() {
    let dir = tempdir().unwrap();
    let bundle = golden_bundle();
    materialize_audit_bundle_v1(dir.path(), &bundle).unwrap();
    fs::write(dir.path().join("records/evidence.json"), b"{}").unwrap();
    fs::write(
        dir.path().join("manifest.json"),
        br#"{"schema_version":"statebook-p5-audit-bundle:v1","bundle_id":"x","members":{"../evil.json":"0000000000000000000000000000000000000000000000000000000000000000"},"manifest_digest":"0000000000000000000000000000000000000000000000000000000000000000","audit_trace_digest":"0000000000000000000000000000000000000000000000000000000000000000","nonclaim_set_digest":"0000000000000000000000000000000000000000000000000000000000000000"}"#,
    )
    .unwrap();
    assert!(readback_validate_audit_bundle_v1(dir.path()).is_err());
}

#[test]
#[cfg(unix)]
fn symlink_rejects() {
    use std::os::unix::fs::symlink;
    let dir = tempdir().unwrap();
    let bundle = golden_bundle();
    materialize_audit_bundle_v1(dir.path(), &bundle).unwrap();
    fs::remove_file(dir.path().join("records/evidence.json")).unwrap();
    symlink("/etc/passwd", dir.path().join("records/evidence.json")).unwrap();
    assert!(matches!(
        readback_validate_audit_bundle_v1(dir.path()),
        Err(BundleErrorV1::Symlink(_))
    ));
}

#[test]
fn stale_digest_rejects() {
    let dir = tempdir().unwrap();
    let bundle = golden_bundle();
    materialize_audit_bundle_v1(dir.path(), &bundle).unwrap();
    fs::write(
        dir.path().join("digests/manifest.sha256"),
        "0000000000000000000000000000000000000000000000000000000000000000\n",
    )
    .unwrap();
    assert!(matches!(
        readback_validate_audit_bundle_v1(dir.path()),
        Err(BundleErrorV1::StaleManifestDigest)
    ));
}

#[test]
fn tampered_nonclaim_rejects() {
    use statebook_report::{digest_to_hex, manifest_digest, member_digest};

    let dir = tempdir().unwrap();
    let bundle = golden_bundle();
    materialize_audit_bundle_v1(dir.path(), &bundle).unwrap();
    let path = dir.path().join("records/nonclaims.json");
    let mut value: serde_json::Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
    value["nonclaims"]
        .as_array_mut()
        .unwrap()
        .push(serde_json::json!("tampered_claim"));
    value["nonclaim_set_digest"] =
        serde_json::json!("0000000000000000000000000000000000000000000000000000000000000000");
    let tampered_bytes = serde_json::to_vec(&value).unwrap();
    fs::write(&path, &tampered_bytes).unwrap();

    let manifest_path = dir.path().join("manifest.json");
    let mut manifest: serde_json::Value =
        serde_json::from_slice(&fs::read(&manifest_path).unwrap()).unwrap();
    manifest["members"]["records/nonclaims.json"] = serde_json::json!(digest_to_hex(
        member_digest("records/nonclaims.json", &tampered_bytes)
    ));
    let mut digest_pairs = Vec::new();
    for path in statebook_report::REQUIRED_MEMBER_PATHS {
        let file_path = dir.path().join(path);
        let bytes = fs::read(&file_path).unwrap();
        digest_pairs.push(((*path).to_owned(), member_digest(path, &bytes)));
    }
    let manifest_digest_hex = digest_to_hex(manifest_digest(
        manifest["bundle_id"].as_str().unwrap(),
        &digest_pairs,
    ));
    manifest["manifest_digest"] = serde_json::json!(manifest_digest_hex);
    fs::write(&manifest_path, serde_json::to_vec(&manifest).unwrap()).unwrap();
    fs::write(
        dir.path().join("digests/manifest.sha256"),
        format!("{manifest_digest_hex}\n"),
    )
    .unwrap();

    assert!(matches!(
        readback_validate_audit_bundle_v1(dir.path()),
        Err(BundleErrorV1::TamperedNonclaimSet)
    ));
}

#[test]
fn composition_digest_mismatch_rejects() {
    let dir = tempdir().unwrap();
    let mut bundle = golden_bundle();
    bundle.composition_digest =
        "0000000000000000000000000000000000000000000000000000000000000001".to_owned();
    assert!(matches!(
        materialize_audit_bundle_v1(dir.path(), &bundle),
        Err(BundleErrorV1::CompositionDigestMismatch)
    ));
}

#[test]
fn decision_context_digest_mismatch_rejects() {
    let dir = tempdir().unwrap();
    let mut bundle = golden_bundle();
    bundle.decision_record.decision_context_digest =
        "0000000000000000000000000000000000000000000000000000000000000001".to_owned();
    assert!(matches!(
        materialize_audit_bundle_v1(dir.path(), &bundle),
        Err(BundleErrorV1::DecisionContextDigestMismatch)
    ));
}

#[test]
fn resource_limit_plus_one_rejects() {
    let dir = tempdir().unwrap();
    let mut bundle = golden_bundle();
    bundle.nonclaims.nonclaims = (0..=MAX_NONCLAIMS_V1)
        .map(|index| format!("nonclaim-{index}"))
        .collect();
    assert!(matches!(
        materialize_audit_bundle_v1(dir.path(), &bundle),
        Err(BundleErrorV1::TooManyNonclaims)
    ));
    let oversized = vec![b'a'; MAX_BUNDLE_BYTES_V1 + 1];
    fs::write(dir.path().join("manifest.json"), &oversized).unwrap();
    assert!(matches!(
        readback_validate_audit_bundle_v1(dir.path()),
        Err(BundleErrorV1::BundleTooLarge | BundleErrorV1::MissingFile(_))
    ));
}
