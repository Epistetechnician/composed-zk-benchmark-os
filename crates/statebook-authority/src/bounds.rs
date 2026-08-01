pub const STATE_SLICE_P7: &str = "statebook-p7-authority-integration-preflight";
pub const CLAIM_BOUNDARY_P7: &str =
    "local hermetic authority preflight without controller invocation or value movement";

pub const PACKAGE_SCHEMA_VERSION_V1: &str = "statebook-p7-authority-package:v1";
pub const RECEIPT_SCHEMA_VERSION_V1: &str = "statebook-p7-preflight-receipt:v1";
pub const HERMETIC_PROFILE_V1: &str = "hermetic-authority-preflight-v1";

pub const MAX_PACKAGE_BYTES_V1: usize = 65_536;
pub const MAX_IDENTIFIER_BYTES_V1: usize = 128;
pub const MAX_NONCLAIMS_V1: usize = 32;
pub const MAX_CONTROLLER_NAMES_V1: usize = 8;
