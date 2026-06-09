//! Identifier helpers.

/// Shared identifier string used by the v0 schema.
pub type SpecId = String;

/// Returns true when an identifier is non-empty after trimming whitespace.
pub fn is_non_empty_id(id: &str) -> bool {
    !id.trim().is_empty()
}
