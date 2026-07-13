#[path = "../src/bin/hsai-mesh-admission/runtime.rs"]
mod runtime;

use serde_json::Value;
use sha2::{Digest, Sha256};

const GOLDEN_ALLOW: &str = include_str!("fixtures/hsai_bridge/golden_allow_request.json");
const GOLDEN_DENY: &str = include_str!("fixtures/hsai_bridge/golden_deny_request.json");
const POLICY: &str = "mesh_policy://repo-patch/golden";

#[test]
fn golden_allow_uses_rust_policy_and_preserves_non_authority() {
    let decision = evaluate(GOLDEN_ALLOW.as_bytes(), POLICY);
    assert_eq!(decision["decision"], "allow");
    assert_eq!(
        decision["request_digest"],
        "sha256:dc95ff8eb49f5116d55ddc0dd7db64c937549863f99ffae7b42ba074a29d805c"
    );
    assert_eq!(
        decision["formal_evidence_metadata"]["grants_authority"],
        false
    );
    assert_eq!(
        decision["formal_evidence_metadata"]["production_readiness_claimed"],
        false
    );
    assert_eq!(
        decision["formal_evidence_metadata"]["state_slice"],
        "phase-747-hsai-mesh-evidence-aware-admission-cli"
    );
    assert_decision_digest_recomputes(&decision);
}

#[test]
fn golden_deny_and_stale_policy_are_valid_decisions() {
    let deny = evaluate(GOLDEN_DENY.as_bytes(), POLICY);
    assert_eq!(deny["decision"], "deny");
    assert_eq!(
        deny["reason_codes"],
        serde_json::json!(["missing_explicit_nonclaims"])
    );

    let stale = evaluate(GOLDEN_ALLOW.as_bytes(), "mesh_policy://repo-patch/current");
    assert_eq!(stale["decision"], "deny");
    assert!(reasons(&stale).contains(&Value::String("stale_policy_id".to_owned())));
}

#[test]
fn evidence_binding_drift_denies_through_existing_evaluator() {
    let mut request: Value = serde_json::from_str(GOLDEN_ALLOW).expect("fixture parses");
    request["attestation_refs"][0]["digest"] = Value::String(format!("sha256:{}", "4".repeat(64)));
    let decision = evaluate(
        &serde_json::to_vec(&request).expect("request serializes"),
        POLICY,
    );
    assert_eq!(decision["decision"], "deny");
    assert!(reasons(&decision).contains(&Value::String(
        "evidence_packet_attestation_binding_mismatch".to_owned()
    )));
}

#[test]
fn duplicate_unknown_and_trailing_json_fail_without_a_decision() {
    let duplicate = GOLDEN_ALLOW.replacen(
        "\"actor_id\": \"operator.golden\",",
        "\"actor_id\":\"operator.golden\",\"\\u0061ctor_id\":\"shadow\",",
        1,
    );
    assert_error(duplicate.as_bytes(), "duplicate keys");

    let mut unknown: Value = serde_json::from_str(GOLDEN_ALLOW).expect("fixture parses");
    unknown["unexpected"] = Value::Bool(true);
    assert_error(
        &serde_json::to_vec(&unknown).expect("request serializes"),
        "wire shape",
    );

    let trailing = format!("{GOLDEN_ALLOW} trailing");
    assert_error(trailing.as_bytes(), "trailing data");
}

#[test]
fn duplicate_sets_malformed_digests_and_wrong_action_fail_closed() {
    let mut duplicate: Value = serde_json::from_str(GOLDEN_ALLOW).expect("fixture parses");
    duplicate["requested_claims"]
        .as_array_mut()
        .expect("claims array")
        .push(Value::String("tests_passed".to_owned()));
    assert_error(
        &serde_json::to_vec(&duplicate).expect("request serializes"),
        "duplicate requested_claims",
    );

    let mut malformed: Value = serde_json::from_str(GOLDEN_ALLOW).expect("fixture parses");
    malformed["candidate_payload_digest"] = Value::String(format!("sha256:{}", "A".repeat(64)));
    assert_error(
        &serde_json::to_vec(&malformed).expect("request serializes"),
        "malformed candidate_payload_digest",
    );

    let mut wrong_action: Value = serde_json::from_str(GOLDEN_ALLOW).expect("fixture parses");
    wrong_action["action_kind"] = Value::String("payment".to_owned());
    assert_error(
        &serde_json::to_vec(&wrong_action).expect("request serializes"),
        "not repo_patch",
    );
}

#[test]
fn oversized_excessively_nested_and_invalid_policy_inputs_fail_closed() {
    assert_error(&vec![b' '; runtime::MAX_INPUT_BYTES + 1], "exceeds 1 MiB");
    let nested = format!("{}0{}", "[".repeat(65), "]".repeat(65));
    assert_error(nested.as_bytes(), "nesting limit");
    let error = runtime::evaluate(GOLDEN_ALLOW.as_bytes(), " current-policy")
        .expect_err("invalid policy fails");
    assert!(error.to_string().contains("current policy id is empty"));
}

#[test]
fn binary_source_is_a_bounded_stdin_stdout_wrapper() {
    let source = include_str!("../src/bin/hsai-mesh-admission/main.rs");
    assert!(source.contains("stdin()"));
    assert!(source.contains("stdout()"));
    assert!(source.contains("--current-policy-id"));
    assert!(source.contains("runtime::evaluate"));
}

#[test]
fn v2_embedded_candidate_and_preflight_evidence_allow_structurally() {
    let request = v2_request();
    let decision = evaluate_request(&request);
    assert_eq!(decision["decision"], "allow");
    assert_eq!(
        decision["formal_evidence_metadata"]["backend"],
        "hsai-rust-v2-evidence-aware-cli"
    );
    assert_eq!(
        decision["formal_evidence_metadata"]["grants_authority"],
        false
    );
    let nonclaim = decision["formal_evidence_metadata"]["nonclaim"]
        .as_str()
        .expect("v2 nonclaim exists");
    assert!(nonclaim.contains("Structural local preflight validation only"));
    assert!(nonclaim.contains("not proof that the declared commands ran"));
    assert_decision_digest_recomputes(&decision);
}

#[test]
fn v2_rejects_candidate_evidence_stage_and_action_digest_tampering() {
    let mut candidate_tamper = v2_request();
    candidate_tamper["candidate_payload"]["summary"] = Value::String("tampered".to_owned());
    assert_v2_error(&candidate_tamper, "candidate_payload digest mismatch");

    let mut evidence_tamper = v2_request();
    evidence_tamper["pre_execution_evidence"]["evaluation_id"] =
        Value::String("tampered-evaluation".to_owned());
    assert_v2_error(&evidence_tamper, "pre_execution_evidence digest mismatch");

    let mut stage_tamper = v2_request();
    stage_tamper["pre_execution_evidence"]["stage_results"]["policy_validation"]["passed"] =
        Value::Bool(false);
    refresh_evidence_digest(&mut stage_tamper);
    assert_v2_error(&stage_tamper, "stage_results digest mismatch");

    let mut action_tamper = v2_request();
    action_tamper["action_proposal_digest"] = Value::String(digest_byte('f'));
    assert_v2_error(&action_tamper, "action_proposal digest mismatch");
}

#[test]
fn v2_failed_or_empty_test_receipts_deny() {
    let mut failed = v2_request();
    failed["pre_execution_evidence"]["preflight_receipt"]["test_results"][0]["returncode"] =
        Value::Number(1.into());
    refresh_evidence_digest(&mut failed);
    let failed_decision = evaluate_request(&failed);
    assert_eq!(failed_decision["decision"], "deny");
    assert!(reasons(&failed_decision).contains(&Value::String("preflight_test_failed".to_owned())));

    let mut empty = v2_request();
    empty["pre_execution_evidence"]["preflight_receipt"]["test_results"] = Value::Array(Vec::new());
    refresh_evidence_digest(&mut empty);
    let empty_decision = evaluate_request(&empty);
    assert_eq!(empty_decision["decision"], "deny");
    assert!(reasons(&empty_decision)
        .contains(&Value::String("preflight_test_results_empty".to_owned())));
}

#[test]
fn v2_path_and_policy_binding_tampering_deny() {
    let mut nonportable = v2_request();
    for pointer in [
        "/candidate_payload/execution_plan/parameters/patch_template/target_file",
        "/candidate_payload/execution_plan/parameters/allowed_paths/0",
        "/pre_execution_evidence/preflight_receipt/target_path",
        "/pre_execution_evidence/preflight_receipt/changed_paths/0",
    ] {
        *nonportable.pointer_mut(pointer).expect("pointer exists") =
            Value::String("../secrets".to_owned());
    }
    refresh_candidate_digest(&mut nonportable);
    refresh_action_proposal_digest(&mut nonportable);
    refresh_evidence_digest(&mut nonportable);
    let nonportable_decision = evaluate_request(&nonportable);
    assert_eq!(nonportable_decision["decision"], "deny");
    assert!(reasons(&nonportable_decision)
        .contains(&Value::String("nonportable_preflight_path".to_owned())));

    let mut protected = v2_request();
    protected["candidate_payload"]["execution_plan"]["parameters"]["protected_paths"] =
        serde_json::json!(["app"]);
    refresh_candidate_digest(&mut protected);
    refresh_action_proposal_digest(&mut protected);
    let protected_decision = evaluate_request(&protected);
    assert_eq!(protected_decision["decision"], "deny");
    assert!(
        reasons(&protected_decision).contains(&Value::String("protected_path_modified".to_owned()))
    );

    let mut policy = v2_request();
    policy["candidate_payload"]["execution_plan"]["parameters"]["mesh_policy_id"] =
        Value::String("mesh_policy://repo-patch/other".to_owned());
    refresh_candidate_digest(&mut policy);
    refresh_action_proposal_digest(&mut policy);
    let policy_decision = evaluate_request(&policy);
    assert_eq!(policy_decision["decision"], "deny");
    assert!(
        reasons(&policy_decision).contains(&Value::String("policy_binding_mismatch".to_owned()))
    );
}

#[test]
fn v2_missing_and_duplicate_preflight_fields_fail_closed() {
    let mut missing = v2_request();
    missing["pre_execution_evidence"]
        .as_object_mut()
        .expect("evidence object")
        .remove("preflight_receipt");
    refresh_evidence_digest(&mut missing);
    assert_v2_error(&missing, "supported wire shape");

    let mut duplicate = v2_request();
    duplicate["pre_execution_evidence"]["preflight_receipt"]["changed_paths"] =
        serde_json::json!(["app/search.py", "app/search.py"]);
    refresh_evidence_digest(&mut duplicate);
    assert_v2_error(&duplicate, "duplicate changed_paths");
}

fn evaluate(input: &[u8], policy: &str) -> Value {
    serde_json::to_value(runtime::evaluate(input, policy).expect("request evaluates"))
        .expect("decision serializes")
}

fn evaluate_request(request: &Value) -> Value {
    evaluate(
        &serde_json::to_vec(request).expect("request serializes"),
        POLICY,
    )
}

fn assert_v2_error(request: &Value, expected: &str) {
    assert_error(
        &serde_json::to_vec(request).expect("request serializes"),
        expected,
    );
}

fn v2_request() -> Value {
    let candidate = serde_json::json!({
        "decision_id": "dec_repo_patch_v2",
        "trigger_id": "trig_repo_patch_v2",
        "decision_type": "investigate_and_patch",
        "autonomy_tier": "approval_required",
        "summary": "Patch the search service in a disposable worktree",
        "reasoning": {
            "primary_hypothesis": "bounded local fixture",
            "evidence": ["preflight receipt"],
            "alternatives_considered": ["reject"]
        },
        "expected_outcome": {
            "target_metrics": {"p95_latency_ms": "unchanged", "error_rate": "unchanged"},
            "time_to_effect": "local"
        },
        "risk": {
            "level": "low",
            "blast_radius": "one fixture file",
            "customer_impact_if_wrong": "none"
        },
        "confidence": 0.8,
        "execution_plan": {
            "system": "repo_patch_service",
            "action": "investigate_and_patch",
            "parameters": {
                "repo_path": "/tmp/disposable-repo",
                "allowed_paths": ["app/search.py"],
                "protected_paths": [".git", "Cargo.toml"],
                "patch_template": {"target_file": "app/search.py", "find": "old", "replace": "new"},
                "test_commands": [["python3", "-m", "unittest"]],
                "mesh_run_id": "run_repo_patch_v2",
                "mesh_action_id": "dec_repo_patch_v2",
                "mesh_policy_id": POLICY,
                "actor_ref": {"actor_id": "operator.v2", "team_id": "team.v2"}
            },
            "rollback_plan": "discard disposable worktree"
        }
    });
    let stage_results = serde_json::json!({
        "policy_validation": {"passed": true, "policy_id": POLICY},
        "execution_readiness": {"passed": true}
    });
    let evidence = serde_json::json!({
        "schema_version": "mesh.repo_patch_pre_execution_evidence.v1",
        "decision_id": "dec_repo_patch_v2",
        "evaluation_id": "eval_repo_patch_v2",
        "evaluation_passed": true,
        "final_recommendation": "execute",
        "blocking_reasons": [],
        "stage_results": stage_results,
        "stage_results_digest": canonical_sha256(&stage_results),
        "preflight_receipt": {
            "state_slice": "mesh.repo_patch_disposable_worktree.v1",
            "base_commit": "a".repeat(40),
            "base_tree": "b".repeat(40),
            "target_path": "app/search.py",
            "target_preimage_digest": digest_byte('4'),
            "target_postimage_digest": digest_byte('5'),
            "authorized_diff_digest": digest_byte('6'),
            "changed_paths": ["app/search.py"],
            "test_results": [{
                "argv": ["python3", "-m", "unittest"],
                "returncode": 0,
                "stdout_digest": digest_byte('7'),
                "stderr_digest": digest_byte('8')
            }]
        }
    });
    let action_proposal = serde_json::json!({
        "decision_id": candidate["decision_id"],
        "execution_plan": candidate["execution_plan"],
        "risk": candidate["risk"],
    });
    let evidence_digest = canonical_sha256(&evidence);
    serde_json::json!({
        "schema_version": "mesh.hsai_admission_request.v2",
        "mesh_run_id": "run_repo_patch_v2",
        "mesh_action_id": "dec_repo_patch_v2",
        "action_kind": "repo_patch",
        "actor_ref": {"actor_id": "operator.v2", "team_id": "team.v2"},
        "mesh_policy_id": POLICY,
        "action_proposal_digest": canonical_sha256(&action_proposal),
        "candidate_payload_digest": canonical_sha256(&candidate),
        "evidence_packet_digest": evidence_digest,
        "attestation_refs": [{"kind": "mesh_pre_execution_evidence", "digest": evidence_digest}],
        "requested_claims": ["no_protected_paths_modified", "patch_applies_cleanly", "tests_passed"],
        "explicit_nonclaims": [
            "does_not_claim_accepted_hsai_evidence",
            "does_not_claim_formal_proof",
            "does_not_claim_global_correctness",
            "does_not_claim_production_certification",
            "does_not_claim_security_review_complete"
        ],
        "created_at": "2026-07-12T00:00:00Z",
        "candidate_payload": candidate,
        "pre_execution_evidence": evidence
    })
}

fn refresh_candidate_digest(request: &mut Value) {
    request["candidate_payload_digest"] =
        Value::String(canonical_sha256(&request["candidate_payload"]));
}

fn refresh_action_proposal_digest(request: &mut Value) {
    let candidate = &request["candidate_payload"];
    let proposal = serde_json::json!({
        "decision_id": candidate["decision_id"],
        "execution_plan": candidate["execution_plan"],
        "risk": candidate["risk"],
    });
    request["action_proposal_digest"] = Value::String(canonical_sha256(&proposal));
}

fn refresh_evidence_digest(request: &mut Value) {
    let digest = canonical_sha256(&request["pre_execution_evidence"]);
    request["evidence_packet_digest"] = Value::String(digest.clone());
    request["attestation_refs"][0]["digest"] = Value::String(digest);
}

fn digest_byte(value: char) -> String {
    format!("sha256:{}", value.to_string().repeat(64))
}

fn assert_error(input: &[u8], expected: &str) {
    let error = runtime::evaluate(input, POLICY).expect_err("input must fail closed");
    assert!(
        error.to_string().contains(expected),
        "error did not contain {expected:?}: {error}"
    );
}

fn reasons(decision: &Value) -> &Vec<Value> {
    decision["reason_codes"]
        .as_array()
        .expect("reason codes array")
}

fn assert_decision_digest_recomputes(decision: &Value) {
    let mut without_digest = decision.clone();
    let actual = without_digest["decision_digest"]
        .as_str()
        .expect("decision digest exists")
        .to_owned();
    without_digest
        .as_object_mut()
        .expect("decision is object")
        .remove("decision_digest");
    assert_eq!(actual, canonical_sha256(&without_digest));
}

fn canonical_sha256(value: &Value) -> String {
    let bytes = canonical_json(value);
    let digest = Sha256::digest(bytes.as_bytes());
    let hex = digest
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect::<String>();
    format!("sha256:{hex}")
}

fn canonical_json(value: &Value) -> String {
    match value {
        Value::Null => "null".to_owned(),
        Value::Bool(value) => value.to_string(),
        Value::Number(value) => value.to_string(),
        Value::String(value) => serde_json::to_string(value).expect("string serializes"),
        Value::Array(values) => format!(
            "[{}]",
            values
                .iter()
                .map(canonical_json)
                .collect::<Vec<_>>()
                .join(",")
        ),
        Value::Object(map) => {
            let mut entries = map.iter().collect::<Vec<_>>();
            entries.sort_by(|(left, _), (right, _)| left.cmp(right));
            format!(
                "{{{}}}",
                entries
                    .into_iter()
                    .map(|(key, value)| format!(
                        "{}:{}",
                        serde_json::to_string(key).expect("key serializes"),
                        canonical_json(value)
                    ))
                    .collect::<Vec<_>>()
                    .join(",")
            )
        }
    }
}
