use zkbench_core::external_runner::{
    contains_rejected_path, ExternalValidationIssue, ExternalValidationIssueSeverity,
};

#[test]
fn external_validation_warning_constructor_preserves_fields_and_severity() {
    let warning = ExternalValidationIssue::warning(
        "artifact_capture.warnings[0]",
        "operator review is still required",
    );

    assert_eq!(warning.path, "artifact_capture.warnings[0]");
    assert_eq!(warning.message, "operator review is still required");
    assert_eq!(warning.severity, ExternalValidationIssueSeverity::Warning);
}

#[test]
fn rejected_path_detection_covers_windows_absolute_path_edges() {
    assert!(contains_rejected_path("C:/operator/live-artifact.json"));
    assert!(contains_rejected_path("D:\\operator\\live-artifact.json"));

    assert!(!contains_rejected_path("1:/operator/live-artifact.json"));
    assert!(!contains_rejected_path("C:relative-artifact.json"));
    assert!(!contains_rejected_path("C:"));
    assert!(!contains_rejected_path("portable/operator-artifact.json"));
}
