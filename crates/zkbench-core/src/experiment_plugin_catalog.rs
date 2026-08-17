//! In-process experiment plugin factories.
//!
//! State slice: `benchmark-os-experiment-plugin-factory-catalog-v1`.
//!
//! The catalog owns implementation construction while the serializable
//! `ExperimentPluginRegistry` remains a descriptor-only metadata inventory.
//! Registration is explicit and in-process: no filesystem discovery, dynamic
//! loading, process execution, network access, or credential loading occurs.

use crate::error::{Result, ZkBenchError};
use crate::experiment::{
    local_json_experiment_plugin_descriptor, ExperimentBundle, ExperimentPlugin,
    ExperimentPluginDescriptor, ExperimentPluginRegistry, LocalJsonExperimentPlugin,
    ValidatedExperimentPluginOutput,
};
use crate::experiment_metacognitive::{
    metacognitive_experiment_plugin_descriptor, MetacognitiveMonitorControlExperimentPlugin,
};
use crate::generator::GeneratorConfig;

/// Factory seam for constructing one typed experiment plugin implementation.
pub trait ExperimentPluginFactory: Send + Sync {
    /// Return the descriptor owned by this factory.
    fn descriptor(&self) -> &ExperimentPluginDescriptor;

    /// Construct the plugin without executing an experiment.
    fn instantiate(&self) -> Result<Box<dyn ExperimentPlugin>>;
}

/// Explicit in-process factory inventory for experiment plugins.
pub struct ExperimentPluginFactoryCatalog {
    factories: Vec<Box<dyn ExperimentPluginFactory>>,
}

impl Default for ExperimentPluginFactoryCatalog {
    fn default() -> Self {
        Self::new()
    }
}

impl ExperimentPluginFactoryCatalog {
    /// Construct an empty factory catalog.
    pub fn new() -> Self {
        Self {
            factories: Vec::new(),
        }
    }

    /// Construct the catalog containing the shipped local JSON factory.
    pub fn local_json(config: GeneratorConfig) -> Result<Self> {
        let mut catalog = Self::new();
        catalog.register(LocalJsonExperimentPluginFactory::new(config)?)?;
        Ok(catalog)
    }

    /// Construct the catalog containing only the synthetic metacognitive plugin.
    pub fn metacognitive() -> Result<Self> {
        let mut catalog = Self::new();
        catalog.register(MetacognitiveMonitorControlExperimentPluginFactory::new())?;
        Ok(catalog)
    }

    /// Construct the catalog containing both shipped typed plugin adapters.
    pub fn local_json_with_metacognitive(config: GeneratorConfig) -> Result<Self> {
        let mut catalog = Self::local_json(config)?;
        catalog.register(MetacognitiveMonitorControlExperimentPluginFactory::new())?;
        Ok(catalog)
    }

    /// Register one factory after validating its descriptor and uniqueness.
    pub fn register<F>(&mut self, factory: F) -> Result<()>
    where
        F: ExperimentPluginFactory + 'static,
    {
        let descriptor = factory.descriptor();
        descriptor.validate("plugin_factory.descriptor")?;
        if self
            .factories
            .iter()
            .any(|registered| registered.descriptor().plugin_id == descriptor.plugin_id)
        {
            return Err(ZkBenchError::validation(
                "plugin_factory.descriptor.plugin_id",
                "plugin factory id is duplicated",
            ));
        }
        self.factories.push(Box::new(factory));
        Ok(())
    }

    /// Resolve registered metadata without constructing or executing a plugin.
    pub fn resolve(&self, plugin_id: &str) -> Option<&ExperimentPluginDescriptor> {
        self.factories
            .iter()
            .find(|factory| factory.descriptor().plugin_id == plugin_id)
            .map(|factory| factory.descriptor())
    }

    /// Validate every registered factory descriptor.
    pub fn validate(&self) -> Result<()> {
        let mut plugin_ids = std::collections::BTreeSet::new();
        for (index, factory) in self.factories.iter().enumerate() {
            let descriptor = factory.descriptor();
            descriptor.validate(&format!("factories[{index}].descriptor"))?;
            if !plugin_ids.insert(&descriptor.plugin_id) {
                return Err(ZkBenchError::validation(
                    format!("factories[{index}].descriptor.plugin_id"),
                    "plugin factory id is duplicated",
                ));
            }
        }
        Ok(())
    }

    /// Instantiate one registered plugin and verify the implementation identity.
    pub fn instantiate(&self, plugin_id: &str) -> Result<Box<dyn ExperimentPlugin>> {
        self.validate()?;
        let factory = self
            .factories
            .iter()
            .find(|factory| factory.descriptor().plugin_id == plugin_id)
            .ok_or_else(|| {
                ZkBenchError::validation(
                    "plugin_id",
                    format!("plugin {plugin_id} is not registered"),
                )
            })?;
        let descriptor = factory.descriptor().clone();
        let plugin = factory.instantiate()?;
        plugin
            .descriptor()
            .validate("plugin_factory.instantiated_plugin")?;
        if plugin.descriptor() != &descriptor {
            return Err(ZkBenchError::validation(
                "plugin_factory.instantiated_plugin",
                "instantiated plugin descriptor does not match its registered factory",
            ));
        }
        Ok(plugin)
    }

    /// Run one registered plugin through descriptor-to-bundle validation.
    pub fn run(&self, plugin_id: &str) -> Result<ExperimentBundle> {
        Ok(self.run_validated_output(plugin_id)?.into_bundle())
    }

    /// Run one registered plugin and retain its descriptor-bound validation.
    pub fn run_validated_output(&self, plugin_id: &str) -> Result<ValidatedExperimentPluginOutput> {
        self.instantiate(plugin_id)?.run_validated_output()
    }

    /// Export descriptor metadata without executable factory state.
    pub fn metadata_registry(&self) -> ExperimentPluginRegistry {
        ExperimentPluginRegistry {
            plugins: self
                .factories
                .iter()
                .map(|factory| factory.descriptor().clone())
                .collect(),
        }
    }
}

/// Factory for the shipped local JSON experiment plugin.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LocalJsonExperimentPluginFactory {
    descriptor: ExperimentPluginDescriptor,
    config: GeneratorConfig,
}

impl LocalJsonExperimentPluginFactory {
    /// Construct a factory owning the typed local generator configuration.
    pub fn new(config: GeneratorConfig) -> Result<Self> {
        let descriptor = local_json_experiment_plugin_descriptor();
        descriptor.validate("local_json_plugin_factory.descriptor")?;
        Ok(Self { descriptor, config })
    }
}

impl ExperimentPluginFactory for LocalJsonExperimentPluginFactory {
    fn descriptor(&self) -> &ExperimentPluginDescriptor {
        &self.descriptor
    }

    fn instantiate(&self) -> Result<Box<dyn ExperimentPlugin>> {
        Ok(Box::new(LocalJsonExperimentPlugin::new(
            self.config.clone(),
        )?))
    }
}

/// Factory for the synthetic metacognitive pure-data plugin.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MetacognitiveMonitorControlExperimentPluginFactory {
    descriptor: ExperimentPluginDescriptor,
}

impl MetacognitiveMonitorControlExperimentPluginFactory {
    /// Construct the stateless synthetic factory.
    pub fn new() -> Self {
        Self {
            descriptor: metacognitive_experiment_plugin_descriptor(),
        }
    }
}

impl Default for MetacognitiveMonitorControlExperimentPluginFactory {
    fn default() -> Self {
        Self::new()
    }
}

impl ExperimentPluginFactory for MetacognitiveMonitorControlExperimentPluginFactory {
    fn descriptor(&self) -> &ExperimentPluginDescriptor {
        &self.descriptor
    }

    fn instantiate(&self) -> Result<Box<dyn ExperimentPlugin>> {
        Ok(Box::new(MetacognitiveMonitorControlExperimentPlugin::new()))
    }
}
