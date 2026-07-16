#![forbid(unsafe_code)]

mod bounds;
mod error;
mod golden;
mod types;

pub use bounds::{
    CLAIM_BOUNDARY_P8, EVALUATION_RECEIPT_SCHEMA_V1, GOLDEN_PATH_PROFILE_V1, STATE_SLICE_P8,
};
pub use error::EvaluationErrorV1;
pub use golden::{reject_unbound_authority_statement_v1, run_hermetic_golden_path_v1};
pub use types::EvaluationReceiptV1;
