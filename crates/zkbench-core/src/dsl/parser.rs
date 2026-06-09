//! YAML parser entry points.

use crate::error::Result;

use super::ast::ParsedAst;
use super::surface::SurfaceSpec;
use super::validation::validate_surface_spec;

/// Parse YAML into a raw Surface DSL spec.
pub fn parse_yaml_spec(input: &str) -> Result<SurfaceSpec> {
    serde_yaml::from_str(input).map_err(Into::into)
}

/// Parse YAML into a validated Parsed AST.
pub fn parse_yaml_ast(input: &str) -> Result<ParsedAst> {
    let spec = parse_yaml_spec(input)?;
    validate_surface_spec(&spec)?;
    Ok(ParsedAst::new(spec))
}
