pub const STATE_SLICE_P6: &str = "statebook-p6-read-only-external-sources";
pub const CLAIM_BOUNDARY_P6: &str =
    "local hermetic captured-source import without authority or value movement";

pub const CAPTURED_ARTIFACT_SCHEMA_V1: &str = "statebook-p6-captured-artifact:v1";
pub const REGISTRATION_SCHEMA_V1: &str = "statebook-p6-source-registration:v1";
pub const IMPORT_RECEIPT_SCHEMA_V1: &str = "statebook-p6-import-receipt:v1";

pub const SYNTHETIC_CLEARING_PROFILE_V1: &str = "synthetic-clearing-terms-v1";
pub const SYNTHETIC_CLEARING_NAMESPACE_V1: &str = "synthetic.clearing.v1";

pub const MAX_ARTIFACT_BYTES_V1: usize = 1_048_576;
pub const MAX_REGISTRATIONS_V1: usize = 256;
pub const MAX_PROVENANCE_FIELD_BYTES_V1: usize = 512;
pub const MAX_OBSERVATIONS_V1: usize = 128;
pub const MAX_CLAIM_OR_LIMITATION_COUNT_V1: usize = 32;
pub const MAX_IDENTIFIER_BYTES_V1: usize = 128;
