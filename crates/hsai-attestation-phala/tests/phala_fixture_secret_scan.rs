use serde_json::Value;

const FIXTURES: &[(&str, &str)] = &[
    (
        "phala_hsai_owned_real_2026_06_16.json",
        include_str!("fixtures/phala_hsai_owned_real_2026_06_16.json"),
    ),
    (
        "phala_trust_center_app_2026_06_16.json",
        include_str!("fixtures/phala_trust_center_app_2026_06_16.json"),
    ),
];

const FORBIDDEN_MARKERS: &[&str] = &[
    "-----BEGIN PRIVATE KEY-----",
    "-----BEGIN EC PRIVATE KEY-----",
    "-----BEGIN RSA PRIVATE KEY-----",
    "-----BEGIN OPENSSH PRIVATE KEY-----",
    "sk_live_",
    "sk_test_",
    "ghp_",
    "xoxb-",
    "AKIA",
];

const FORBIDDEN_SECRET_FIELDS: &[&str] = &[
    "private_key",
    "private_keys",
    "api_token",
    "api_tokens",
    "session_cookie",
    "session_cookies",
    "bearer_token",
    "bearer_tokens",
    "live_service_credential",
    "live_service_credentials",
];

#[test]
fn committed_phala_fixtures_do_not_contain_secret_shapes() {
    for (name, text) in FIXTURES {
        for marker in FORBIDDEN_MARKERS {
            assert!(
                !text.contains(marker),
                "{name} contains forbidden secret marker {marker}"
            );
        }

        let parsed: Value = serde_json::from_str(text).expect("fixture JSON should parse");
        let mut forbidden_fields = Vec::new();
        collect_forbidden_secret_fields("$", &parsed, &mut forbidden_fields);
        assert!(
            forbidden_fields.is_empty(),
            "{name} contains forbidden secret value fields: {forbidden_fields:?}"
        );
    }
}

fn collect_forbidden_secret_fields(path: &str, value: &Value, found: &mut Vec<String>) {
    match value {
        Value::Object(object) => {
            for (key, child) in object {
                let child_path = format!("{path}.{key}");
                if FORBIDDEN_SECRET_FIELDS.contains(&key.as_str()) {
                    found.push(child_path.clone());
                }
                collect_forbidden_secret_fields(&child_path, child, found);
            }
        }
        Value::Array(items) => {
            for (index, child) in items.iter().enumerate() {
                collect_forbidden_secret_fields(&format!("{path}[{index}]"), child, found);
            }
        }
        Value::Null | Value::Bool(_) | Value::Number(_) | Value::String(_) => {}
    }
}
