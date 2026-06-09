//! Parsed AST wrapper.

use serde::{Deserialize, Serialize};

use super::surface::SurfaceSpec;

/// Validated representation of a parsed Surface DSL document.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ParsedAst {
    /// Validated surface spec.
    pub spec: SurfaceSpec,
}

impl ParsedAst {
    /// Construct a Parsed AST from a validated SurfaceSpec.
    pub fn new(spec: SurfaceSpec) -> Self {
        Self { spec }
    }
}
