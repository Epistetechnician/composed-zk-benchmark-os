//! Typed identity shared by generic plugin-composition seams.
//!
//! State slice: benchmark-os-plugin-composition-identity-value-v1.
//! Constructor locality slice: benchmark-os-plugin-composition-identity-constructor-locality-v1.
//!
//! This value centralizes validation and construction for the plugin,
//! experiment, and run identity tuple used by packet jobs, composition
//! runners, and keyed packet stores. Existing public fields and packet wire
//! schemas remain unchanged; this is an additive in-memory value object.
//! It carries local metadata identity only and does not authorize execution,
//! publication, evidence mutation, or runtime access.

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};

/// Canonical identity tuple for one plugin-composition run.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub struct PluginCompositionIdentity {
    /// Registered plugin identifier.
    pub plugin_id: String,
    /// Outer experiment identity.
    pub experiment_id: String,
    /// Outer run identity.
    pub run_id: String,
}

impl PluginCompositionIdentity {
    /// Construct and validate one typed identity tuple.
    pub fn new(
        plugin_id: impl Into<String>,
        experiment_id: impl Into<String>,
        run_id: impl Into<String>,
    ) -> Result<Self> {
        Self::new_at(
            plugin_id,
            experiment_id,
            run_id,
            "plugin_composition_identity",
        )
    }

    /// Construct and validate one typed identity tuple with a caller-owned
    /// diagnostic path.
    pub fn new_at(
        plugin_id: impl Into<String>,
        experiment_id: impl Into<String>,
        run_id: impl Into<String>,
        path: &str,
    ) -> Result<Self> {
        let identity = Self {
            plugin_id: plugin_id.into(),
            experiment_id: experiment_id.into(),
            run_id: run_id.into(),
        };
        identity.validate_at(path)?;
        Ok(identity)
    }

    /// Validate all identity components with the default diagnostic prefix.
    pub fn validate(&self) -> Result<()> {
        self.validate_at("plugin_composition_identity")
    }

    /// Validate all identity components with a caller-owned diagnostic path.
    pub fn validate_at(&self, path: &str) -> Result<()> {
        for (field, value) in [
            ("plugin_id", &self.plugin_id),
            ("experiment_id", &self.experiment_id),
            ("run_id", &self.run_id),
        ] {
            if value.trim().is_empty() {
                return Err(ZkBenchError::validation(
                    format!("{path}.{field}"),
                    "identity value must not be empty",
                ));
            }
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // State slice: benchmark-os-plugin-composition-identity-constructor-locality-v1.
    #[test]
    fn path_aware_constructor_preserves_identity_and_diagnostic_scope() {
        let identity = PluginCompositionIdentity::new_at(
            "plugin",
            "experiment",
            "run",
            "packet_store_key.identity",
        )
        .expect("valid identity should construct");
        assert_eq!(identity.plugin_id, "plugin");
        assert_eq!(identity.experiment_id, "experiment");
        assert_eq!(identity.run_id, "run");

        let error =
            PluginCompositionIdentity::new_at("plugin", "", "run", "packet_store_key.identity")
                .expect_err("empty identity components must fail closed");
        assert!(error
            .to_string()
            .contains("packet_store_key.identity.experiment_id"));
    }
}
