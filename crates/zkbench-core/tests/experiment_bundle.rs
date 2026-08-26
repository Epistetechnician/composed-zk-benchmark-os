// State slices:
// - `benchmark-os-experiment-bundle-plugin-contract-v1`
// - `benchmark-os-static-plugin-registry-dispatch-v1`
// - `benchmark-os-experiment-bundle-integrity-v1`
// - `benchmark-os-plugin-output-binding-v1`
// - `benchmark-os-validated-plugin-output-value-v1`
// - `benchmark-os-experiment-bundle-validated-readback-v1`
// - `benchmark-os-experiment-plugin-factory-catalog-v1`
// - `benchmark-os-plugin-registry-descriptor-only-separation-v1`

use zkbench_core::{
    compute_experiment_bundle_digest, deserialize_experiment_bundle_json,
    local_json_experiment_plugin_descriptor, serialize_experiment_bundle_json,
    validate_experiment_bundle, ExperimentArtifactKind, ExperimentBundle,
    ExperimentBundleValidationIssueKind, ExperimentPlugin, ExperimentPluginDescriptor,
    ExperimentPluginFactory, ExperimentPluginFactoryCatalog, ExperimentPluginRegistry,
    LocalJsonExperimentPlugin, MeasurementStatus, MechanismMeasurementKind, MetricKind,
    ValidatedExperimentBundle,
};

#[test]
fn bundle_artifact_access_requires_one_matching_kind() {
    let bundle = LocalJsonExperimentPlugin::baseline()
        .expect("local plugin should construct")
        .run()
        .expect("local plugin should emit a bundle");
    let report = bundle
        .artifact(ExperimentArtifactKind::Report)
        .expect("report artifact should be present exactly once")
        .clone();
    assert_eq!(report.uri, "report/report.json");

    let mut missing = bundle.clone();
    missing
        .artifacts
        .retain(|artifact| artifact.kind != ExperimentArtifactKind::Report);
    let error = missing
        .artifact(ExperimentArtifactKind::Report)
        .expect_err("missing artifact kinds must fail closed");
    assert!(error
        .to_string()
        .contains("required artifact kind Report is missing"));

    let mut duplicate = bundle;
    duplicate.artifacts.push(report);
    let error = duplicate
        .artifact(ExperimentArtifactKind::Report)
        .expect_err("duplicate artifact kinds must fail closed");
    assert!(error
        .to_string()
        .contains("artifact kind Report is duplicated"));
}

#[test]
fn local_plugin_emits_complete_bundle_with_explicit_sparse_mechanisms() {
    let plugin = LocalJsonExperimentPlugin::baseline().expect("local plugin should construct");
    let bundle = plugin.run().expect("local plugin should emit a bundle");
    let validation = validate_experiment_bundle(&bundle);

    assert!(
        validation.valid,
        "bundle validation issues: {:?}",
        validation.issues
    );
    assert_eq!(bundle.artifacts.len(), 8);
    assert_eq!(
        bundle.config.plugin_id,
        local_json_experiment_plugin_descriptor().plugin_id
    );
    assert!(bundle
        .mechanism_ledger
        .measurements
        .iter()
        .any(|measurement| {
            measurement.kind == MechanismMeasurementKind::Activation
                && measurement.status == MeasurementStatus::Unsupported
                && measurement.reason.is_some()
        }));
    assert!(bundle
        .metrics
        .measurements
        .iter()
        .all(|metric| metric.status == MeasurementStatus::Collected));
    assert!(bundle
        .non_claims
        .iter()
        .any(|non_claim| non_claim.contains("not official benchmark evidence")));
}

#[test]
fn bundle_json_and_digest_are_deterministic_and_round_trip() {
    let first = LocalJsonExperimentPlugin::baseline()
        .expect("local plugin should construct")
        .run()
        .expect("first bundle should emit");
    let second = LocalJsonExperimentPlugin::baseline()
        .expect("local plugin should construct")
        .run()
        .expect("second bundle should emit");

    let first_json = serialize_experiment_bundle_json(&first).expect("first JSON should serialize");
    let second_json =
        serialize_experiment_bundle_json(&second).expect("second JSON should serialize");
    assert_eq!(first_json, second_json);
    assert_eq!(
        compute_experiment_bundle_digest(&first).expect("first digest should compute"),
        compute_experiment_bundle_digest(&second).expect("second digest should compute")
    );
    assert_eq!(
        deserialize_experiment_bundle_json(&first_json).expect("bundle should deserialize"),
        first
    );
    assert_eq!(
        ValidatedExperimentBundle::from_canonical_json(&first_json)
            .expect("canonical bundle should validate")
            .bundle(),
        &first
    );
}

#[test]
fn validated_bundle_readback_rejects_noncanonical_and_semantically_invalid_json() {
    let bundle = LocalJsonExperimentPlugin::baseline()
        .expect("local plugin should construct")
        .run()
        .expect("bundle should emit");
    let json = serialize_experiment_bundle_json(&bundle).expect("bundle should serialize");
    assert!(ValidatedExperimentBundle::from_canonical_json(&format!(" {json}")).is_err());

    let mut invalid = bundle;
    invalid.report.claim_boundary =
        zkbench_core::ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    let invalid_json = serialize_experiment_bundle_json(&invalid)
        .expect("semantically invalid bundle should still serialize");
    assert!(ValidatedExperimentBundle::from_canonical_json(&invalid_json).is_err());
}

#[test]
fn registry_resolves_static_plugin_metadata_without_dynamic_loading() {
    let registry = ExperimentPluginRegistry::default();
    registry
        .validate()
        .expect("shipped registry should validate");
    let descriptor = registry
        .resolve("local-json-experiment-plugin-v1")
        .expect("shipped plugin should be registered");

    assert_eq!(descriptor.task_id, "generated-benchmark-instance-task");
    assert_eq!(
        descriptor.collector_id,
        "local-replay-mechanism-collector-v1"
    );
    assert_eq!(descriptor.evaluator_id, "local-replay-evaluator-v1");
}

#[test]
fn catalog_dispatch_runs_the_selected_plugin_end_to_end() {
    let catalog =
        ExperimentPluginFactoryCatalog::local_json(zkbench_core::GeneratorConfig::baseline_fsm())
            .expect("local factory catalog should construct");
    let bundle = catalog
        .run("local-json-experiment-plugin-v1")
        .expect("registered plugin should run through the factory catalog");

    assert!(validate_experiment_bundle(&bundle).valid);
    assert_eq!(
        bundle.lifecycle,
        zkbench_core::ExperimentLifecycle::Completed
    );
}

#[test]
fn validated_plugin_output_binds_descriptor_and_bundle_without_wire_changes() {
    let catalog =
        ExperimentPluginFactoryCatalog::local_json(zkbench_core::GeneratorConfig::baseline_fsm())
            .expect("local factory catalog should construct");
    let validated = catalog
        .run_validated_output("local-json-experiment-plugin-v1")
        .expect("validated plugin output should construct");

    assert_eq!(
        validated.descriptor(),
        &local_json_experiment_plugin_descriptor()
    );
    assert_eq!(
        validated.bundle().config.plugin_id,
        validated.descriptor().plugin_id
    );
    assert!(validate_experiment_bundle(validated.bundle()).valid);

    let bundle = validated.into_bundle();
    assert_eq!(
        bundle.schema_version.value,
        "benchmark-os-experiment-bundle-v1"
    );
}

#[test]
fn catalog_rejects_unknown_plugin_without_running_anything() {
    let catalog =
        ExperimentPluginFactoryCatalog::local_json(zkbench_core::GeneratorConfig::baseline_fsm())
            .expect("local factory catalog should construct");
    let error = catalog
        .run("missing-plugin")
        .expect_err("unknown plugin must fail closed in the executable catalog");

    assert!(error.to_string().contains("not registered"));
}

#[derive(Clone)]
struct DescriptorMismatchPlugin {
    descriptor: ExperimentPluginDescriptor,
    bundle: ExperimentBundle,
}

impl ExperimentPlugin for DescriptorMismatchPlugin {
    fn descriptor(&self) -> &ExperimentPluginDescriptor {
        &self.descriptor
    }

    fn run(&self) -> zkbench_core::Result<ExperimentBundle> {
        Ok(self.bundle.clone())
    }
}

#[test]
fn plugin_output_binding_rejects_descriptor_drift_before_returning_bundle() {
    let source = LocalJsonExperimentPlugin::baseline()
        .expect("local plugin should construct")
        .run()
        .expect("local plugin should emit a valid bundle");
    let mut descriptor = local_json_experiment_plugin_descriptor();
    descriptor.model_id = "unbound-model-v1".to_string();
    let plugin = DescriptorMismatchPlugin {
        descriptor,
        bundle: source,
    };

    let error = plugin
        .run_validated()
        .expect_err("descriptor drift must fail closed");
    assert!(error.to_string().contains("model_version.model_id"));
}

#[test]
fn plugin_output_binding_rejects_claim_ceiling_escalation() {
    let source = LocalJsonExperimentPlugin::baseline()
        .expect("local plugin should construct")
        .run()
        .expect("local plugin should emit a valid bundle");
    let mut descriptor = local_json_experiment_plugin_descriptor();
    descriptor.claim_boundary = zkbench_core::ClaimBoundary::Level0DesignNote;
    let plugin = DescriptorMismatchPlugin {
        descriptor,
        bundle: source,
    };

    let error = plugin
        .run_validated()
        .expect_err("descriptor ceiling drift must fail closed");
    assert!(error
        .to_string()
        .contains("exceeds plugin descriptor ceiling"));
}

struct CatalogFixtureFactory {
    descriptor: ExperimentPluginDescriptor,
    plugin_descriptor: ExperimentPluginDescriptor,
    bundle: ExperimentBundle,
}

impl ExperimentPluginFactory for CatalogFixtureFactory {
    fn descriptor(&self) -> &ExperimentPluginDescriptor {
        &self.descriptor
    }

    fn instantiate(&self) -> zkbench_core::Result<Box<dyn ExperimentPlugin>> {
        Ok(Box::new(DescriptorMismatchPlugin {
            descriptor: self.plugin_descriptor.clone(),
            bundle: self.bundle.clone(),
        }))
    }
}

struct NonExecutingFactory {
    descriptor: ExperimentPluginDescriptor,
}

impl ExperimentPluginFactory for NonExecutingFactory {
    fn descriptor(&self) -> &ExperimentPluginDescriptor {
        &self.descriptor
    }

    fn instantiate(&self) -> zkbench_core::Result<Box<dyn ExperimentPlugin>> {
        panic!("registration must not instantiate factories")
    }
}

#[test]
fn factory_catalog_registers_without_instantiation_and_exports_metadata_only() {
    let descriptor = local_json_experiment_plugin_descriptor();
    let mut catalog = ExperimentPluginFactoryCatalog::new();
    catalog
        .register(NonExecutingFactory {
            descriptor: descriptor.clone(),
        })
        .expect("registration should validate without constructing a plugin");

    assert_eq!(catalog.resolve(&descriptor.plugin_id), Some(&descriptor));
    let registry = catalog.metadata_registry();
    assert_eq!(registry.plugins, vec![descriptor]);
    registry
        .validate()
        .expect("metadata-only registry should validate");
}

#[test]
fn factory_catalog_runs_local_plugin_through_output_binding() {
    let catalog =
        ExperimentPluginFactoryCatalog::local_json(zkbench_core::GeneratorConfig::baseline_fsm())
            .expect("local factory catalog should construct");
    let bundle = catalog
        .run(zkbench_core::LOCAL_JSON_EXPERIMENT_PLUGIN_ID)
        .expect("catalog should run the selected plugin");

    assert!(validate_experiment_bundle(&bundle).valid);
    assert_eq!(
        catalog.metadata_registry(),
        ExperimentPluginRegistry::default()
    );
}

#[test]
fn factory_catalog_rejects_duplicate_and_invalid_descriptors() {
    let descriptor = local_json_experiment_plugin_descriptor();
    let mut catalog = ExperimentPluginFactoryCatalog::new();
    catalog
        .register(NonExecutingFactory {
            descriptor: descriptor.clone(),
        })
        .expect("first factory should register");
    let duplicate = catalog
        .register(NonExecutingFactory { descriptor })
        .expect_err("duplicate factory ids must fail closed");
    assert!(duplicate.to_string().contains("duplicated"));

    let mut invalid_descriptor = local_json_experiment_plugin_descriptor();
    invalid_descriptor.plugin_id.clear();
    let invalid = ExperimentPluginFactoryCatalog::new().register(NonExecutingFactory {
        descriptor: invalid_descriptor,
    });
    assert!(invalid.is_err());
}

#[test]
fn factory_catalog_rejects_instantiated_descriptor_drift() {
    let bundle = LocalJsonExperimentPlugin::baseline()
        .expect("local plugin should construct")
        .run()
        .expect("local plugin should emit a valid bundle");
    let registered = local_json_experiment_plugin_descriptor();
    let mut instantiated = registered.clone();
    instantiated.model_id = "drifted-model-v1".to_string();
    let mut catalog = ExperimentPluginFactoryCatalog::new();
    catalog
        .register(CatalogFixtureFactory {
            descriptor: registered,
            plugin_descriptor: instantiated,
            bundle,
        })
        .expect("factory descriptor itself should register");

    let error = catalog
        .instantiate(zkbench_core::LOCAL_JSON_EXPERIMENT_PLUGIN_ID)
        .err()
        .expect("factory output descriptor drift must fail closed");
    assert!(error.to_string().contains("does not match"));
}

#[test]
fn validation_rejects_missing_reason_and_duplicate_artifact() {
    let plugin = LocalJsonExperimentPlugin::baseline().expect("local plugin should construct");
    let mut bundle = plugin.run().expect("local plugin should emit a bundle");
    bundle
        .mechanism_ledger
        .measurements
        .iter_mut()
        .find(|measurement| measurement.kind == MechanismMeasurementKind::Activation)
        .expect("activation measurement should exist")
        .reason = None;
    bundle.artifacts.push(bundle.artifacts[0].clone());

    let validation = validate_experiment_bundle(&bundle);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.kind == ExperimentBundleValidationIssueKind::InvalidMeasurementState));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.kind == ExperimentBundleValidationIssueKind::DuplicateArtifactUri));
}

#[test]
fn validation_rejects_component_digest_drift() {
    let plugin = LocalJsonExperimentPlugin::baseline().expect("local plugin should construct");
    let mut bundle = plugin.run().expect("local plugin should emit a bundle");
    bundle
        .artifacts
        .iter_mut()
        .find(|artifact| artifact.kind == zkbench_core::ExperimentArtifactKind::Config)
        .expect("config artifact should exist")
        .digest
        .hex_digest = "0".repeat(64);

    let validation = validate_experiment_bundle(&bundle);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.kind == ExperimentBundleValidationIssueKind::DigestBindingMismatch));
}

#[test]
fn validation_rejects_internal_digest_and_metric_kind_drift() {
    let plugin = LocalJsonExperimentPlugin::baseline().expect("local plugin should construct");
    let mut bundle = plugin.run().expect("local plugin should emit a bundle");
    bundle.config.canonical_json.push(' ');
    bundle.metrics.measurements[0].kind = MetricKind::StatusLabel;

    let validation = validate_experiment_bundle(&bundle);
    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == ExperimentBundleValidationIssueKind::DigestBindingMismatch
            && issue.path == "config.digest"
    }));
    assert!(validation.issues.iter().any(
        |issue| issue.kind == ExperimentBundleValidationIssueKind::IncompatibleMeasurementValue
    ));
}
