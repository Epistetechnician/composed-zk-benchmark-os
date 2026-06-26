use serde::Serialize;
use zkbench_core::evidence::{
    canonical_json_bytes, compute_artifact_digest, compute_artifact_digest_bytes,
    compute_artifact_digest_for_json, ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole,
};

#[derive(Serialize)]
struct DigestFixture {
    alpha: u8,
    beta: &'static str,
}

struct FailingSerialize;

impl Serialize for FailingSerialize {
    fn serialize<S>(&self, _serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        Err(serde::ser::Error::custom(
            "forced digest serialization failure",
        ))
    }
}

#[test]
fn canonical_json_bytes_and_struct_digest_share_exact_bytes() {
    let value = DigestFixture {
        alpha: 7,
        beta: "local",
    };

    let bytes = canonical_json_bytes(&value).expect("fixture should serialize");

    assert_eq!(bytes, br#"{"alpha":7,"beta":"local"}"#);

    let digest = compute_artifact_digest(
        &value,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    )
    .expect("fixture digest should compute");
    let direct_digest = compute_artifact_digest_bytes(
        &bytes,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    );

    assert_eq!(digest, direct_digest);
    assert_eq!(digest.algorithm, ArtifactDigestAlgorithm::Sha256);
    assert_eq!(digest.byte_len, bytes.len());
    assert_eq!(digest.kind, Some(ArtifactKind::Other));
    assert_eq!(digest.role, Some(ArtifactRole::Manifest));
    assert_eq!(digest.hex_digest.len(), 64);
    assert!(digest
        .hex_digest
        .chars()
        .all(|ch| ch.is_ascii_hexdigit() && !ch.is_ascii_uppercase()));
}

#[test]
fn raw_and_json_digest_helpers_preserve_byte_level_identity() {
    let pretty_json = "{\n  \"alpha\": 7\n}\n";
    let json_digest = compute_artifact_digest_for_json(
        pretty_json,
        Some(ArtifactKind::ScoreReport),
        Some(ArtifactRole::Report),
    );
    let raw_digest = compute_artifact_digest_bytes(
        pretty_json.as_bytes(),
        Some(ArtifactKind::ScoreReport),
        Some(ArtifactRole::Report),
    );

    assert_eq!(json_digest, raw_digest);
    assert_eq!(json_digest.byte_len, pretty_json.len());

    let compact_digest = compute_artifact_digest_for_json(
        r#"{"alpha":7}"#,
        Some(ArtifactKind::ScoreReport),
        Some(ArtifactRole::Report),
    );

    assert_ne!(json_digest.hex_digest, compact_digest.hex_digest);

    let different_metadata_digest =
        compute_artifact_digest_bytes(pretty_json.as_bytes(), None, Some(ArtifactRole::Digest));

    assert_eq!(json_digest.hex_digest, different_metadata_digest.hex_digest);
    assert_ne!(json_digest.kind, different_metadata_digest.kind);
    assert_ne!(json_digest.role, different_metadata_digest.role);
}

#[test]
fn empty_raw_digest_uses_the_standard_sha256_empty_payload_hash() {
    let digest = compute_artifact_digest_bytes(&[], None, None);

    assert_eq!(digest.algorithm, ArtifactDigestAlgorithm::Sha256);
    assert_eq!(
        digest.hex_digest,
        "e3b0c44298fc1c149afbf4c8996fb924\
         27ae41e4649b934ca495991b7852b855"
            .replace(' ', "")
    );
    assert_eq!(digest.byte_len, 0);
    assert_eq!(digest.kind, None);
    assert_eq!(digest.role, None);
}

#[test]
fn serialization_failures_are_reported_with_digest_context() {
    let error = canonical_json_bytes(&FailingSerialize).expect_err("serializer should fail");
    let rendered = error.to_string();

    assert!(rendered.contains("canonical_json_bytes"));
    assert!(rendered.contains("forced digest serialization failure"));

    let digest_error = compute_artifact_digest(&FailingSerialize, Some(ArtifactKind::Other), None)
        .expect_err("digesting a failing serializer should fail");
    let rendered = digest_error.to_string();

    assert!(rendered.contains("canonical_json_bytes"));
    assert!(rendered.contains("forced digest serialization failure"));
}
