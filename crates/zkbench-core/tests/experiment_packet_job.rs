//! Focused coverage for the catalog-to-durable-packet job seam.
//!
//! State slice: `benchmark-os-plugin-composition-packet-job-v1`.
//! Request extension: `benchmark-os-plugin-composition-packet-job-storage-independent-request-v1`.
//! Keyed receipt extension: `benchmark-os-plugin-composition-packet-store-keyed-receipt-v1`.
//! Result extension: `benchmark-os-plugin-composition-packet-job-receipt-result-v1`.
//! Identity extension: `benchmark-os-plugin-composition-identity-value-v1`.
//! Compatibility extension: `benchmark-os-plugin-composition-packet-store-legacy-seam-containment-v1`.
//! Projector injection slice: `benchmark-os-plugin-composition-packet-job-projector-injection-v1`.
//! Durable projector attribution slice: `benchmark-os-plugin-composition-projector-durable-attribution-v1`.
//! Materialization handoff validation slice: `benchmark-os-plugin-composition-packet-store-materialization-handoff-validation-v1`.
//! Result handoff validation slice: `benchmark-os-plugin-composition-packet-job-result-handoff-validation-v1`.
//! This is local orchestration and packet-integrity coverage, not execution or
//! scientific evidence.

use tempfile::tempdir;
use zkbench_core::experiment_observability::ExperimentProvenance;
use zkbench_core::experiment_packet_store_compat::PluginCompositionPacketStore;
use zkbench_core::{
    serialize_plugin_composition_config_json, ClaimBoundary, ExperimentArtifactKind,
    ExperimentBundle, ExperimentPacketJob, ExperimentPacketJobConfig, ExperimentPacketJobRequest,
    ExperimentPluginFactoryCatalog, GeneratorConfig, InMemoryPluginCompositionPacketStore,
    KeyedPluginCompositionPacketStore, PacketStoreDestination, PacketStoreKey, PacketStoreReceipt,
    PluginCompositionBinding, PluginCompositionIdentity, PluginCompositionPacket,
    PluginCompositionPacketOutput, PluginCompositionProjector, PluginCompositionRunner,
    PluginCompositionSource, StandardPluginCompositionProjector,
    ValidatedPacketStoreMaterialization, LOCAL_JSON_EXPERIMENT_PLUGIN_ID,
    METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
};

use std::sync::{Arc, Mutex};

fn provenance(label: &str) -> ExperimentProvenance {
    ExperimentProvenance {
        who: "experiment-packet-job-test".to_string(),
        what: label.to_string(),
        when: "logical-test-time".to_string(),
        version: "experiment-packet-job-test-v1".to_string(),
        source_revision: "local-uncommitted".to_string(),
    }
}

fn config(
    plugin_id: &str,
    experiment_id: &str,
    run_id: &str,
    provenance: ExperimentProvenance,
    output_root: impl Into<std::path::PathBuf>,
    overwrite: bool,
    protected_paths: Vec<std::path::PathBuf>,
) -> ExperimentPacketJobConfig {
    ExperimentPacketJobConfig {
        plugin_id: plugin_id.to_string(),
        experiment_id: experiment_id.to_string(),
        run_id: run_id.to_string(),
        provenance,
        destination: PacketStoreDestination {
            output_root: output_root.into(),
            overwrite,
            protected_paths,
        },
    }
}

fn request(
    plugin_id: &str,
    experiment_id: &str,
    run_id: &str,
    provenance: ExperimentProvenance,
) -> ExperimentPacketJobRequest {
    ExperimentPacketJobRequest {
        plugin_id: plugin_id.to_string(),
        experiment_id: experiment_id.to_string(),
        run_id: run_id.to_string(),
        provenance,
    }
}

fn generic_packet(experiment_id: &str, run_id: &str) -> PluginCompositionPacket {
    let catalog = ExperimentPluginFactoryCatalog::metacognitive()
        .expect("metacognitive catalog should construct");
    let plugin = catalog
        .instantiate(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("metacognitive plugin should instantiate");
    PluginCompositionRunner::new(
        plugin,
        experiment_id,
        run_id,
        provenance("keyed-store-test-packet"),
    )
    .expect("generic packet runner should construct")
    .run()
    .expect("generic packet runner should run")
    .into()
}

struct MetadataReportProjector;

impl PluginCompositionProjector for MetadataReportProjector {
    fn descriptor(
        &self,
    ) -> zkbench_core::Result<zkbench_core::experiment_observability::ModuleDescriptor> {
        Ok(zkbench_core::experiment_observability::ModuleDescriptor {
            module_id: "plugin-composition-projector".to_string(),
            implementation_id: "packet-job-metadata-report-projector-v1".to_string(),
            version: "1".to_string(),
            source_revision: "packet-job-projector-injection-test-v1".to_string(),
        })
    }

    fn project(
        &self,
        inner: &ExperimentBundle,
    ) -> zkbench_core::Result<Vec<PluginCompositionBinding>> {
        let mut bindings = StandardPluginCompositionProjector.project(inner)?;
        let report = inner.artifact(ExperimentArtifactKind::Report)?;
        let metadata = bindings
            .iter_mut()
            .find(|binding| {
                binding.outer_kind
                    == zkbench_core::experiment_observability::ExperimentArtifactKind::Metadata
            })
            .ok_or_else(|| {
                zkbench_core::ZkBenchError::validation(
                    "packet_job_projector_test",
                    "metadata binding is missing",
                )
            })?;
        metadata.sources.push(PluginCompositionSource {
            inner_kind: ExperimentArtifactKind::Report,
            inner_uri: report.uri.clone(),
            inner_digest: report.digest.clone(),
        });
        Ok(bindings)
    }
}

struct WrongModuleProjector;

impl PluginCompositionProjector for WrongModuleProjector {
    fn descriptor(
        &self,
    ) -> zkbench_core::Result<zkbench_core::experiment_observability::ModuleDescriptor> {
        Ok(zkbench_core::experiment_observability::ModuleDescriptor {
            module_id: "wrong-projector-module".to_string(),
            implementation_id: "wrong-projector-v1".to_string(),
            version: "1".to_string(),
            source_revision: "packet-job-projector-injection-test-v1".to_string(),
        })
    }

    fn project(
        &self,
        _inner: &ExperimentBundle,
    ) -> zkbench_core::Result<Vec<PluginCompositionBinding>> {
        panic!("invalid projector must fail before plugin execution")
    }
}

struct RecordingStore {
    events: Arc<Mutex<Vec<&'static str>>>,
    expected_packet: PluginCompositionPacket,
    materialized_output: PluginCompositionPacketOutput,
    readback_output: PluginCompositionPacketOutput,
    fail_materialize: bool,
}

impl PluginCompositionPacketStore for RecordingStore {
    fn materialize(
        &mut self,
        packet: &PluginCompositionPacket,
    ) -> zkbench_core::Result<PluginCompositionPacketOutput> {
        self.events
            .lock()
            .expect("event lock should not poison")
            .push("materialize");
        if self.fail_materialize {
            return Err(zkbench_core::ZkBenchError::validation(
                "recording_store.materialize",
                "recording materialization failed",
            ));
        }
        if packet != &self.expected_packet {
            return Err(zkbench_core::ZkBenchError::validation(
                "recording_store.packet",
                "job supplied an unexpected packet",
            ));
        }
        Ok(self.materialized_output.clone())
    }

    fn readback(&self) -> zkbench_core::Result<PluginCompositionPacketOutput> {
        self.events
            .lock()
            .expect("event lock should not poison")
            .push("readback");
        Ok(self.readback_output.clone())
    }
}

fn baseline_output(
    dir: &tempfile::TempDir,
    experiment_id: &str,
    run_id: &str,
) -> PluginCompositionPacketOutput {
    let mut job = ExperimentPacketJob::new(
        ExperimentPluginFactoryCatalog::metacognitive()
            .expect("metacognitive catalog should construct"),
        config(
            METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
            experiment_id,
            run_id,
            provenance("recording-store-baseline"),
            dir.path().join("baseline"),
            false,
            Vec::new(),
        ),
    )
    .expect("baseline job should construct");
    job.run_once().expect("baseline job should materialize")
}

#[test]
fn metacognitive_job_materializes_and_reads_back_one_packet() {
    let dir = tempdir().expect("temporary output parent should exist");
    let output_root = dir.path().join("metacognitive-job");
    let mut job = ExperimentPacketJob::new(
        ExperimentPluginFactoryCatalog::metacognitive()
            .expect("metacognitive catalog should construct"),
        config(
            METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
            "job-metacognitive-experiment",
            "job-metacognitive-run",
            provenance("metacognitive-job"),
            output_root.clone(),
            false,
            Vec::new(),
        ),
    )
    .expect("job constructor should validate the registered plugin");

    let output = job
        .run_once()
        .expect("job should complete a packet round trip");
    assert_eq!(
        output.packet.inner.config.plugin_id,
        METACOGNITIVE_EXPERIMENT_PLUGIN_ID
    );
    assert_eq!(
        output.packet.outer.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert_eq!(
        output.manifest.experiment_id,
        "job-metacognitive-experiment"
    );
    assert_eq!(output.manifest.run_id, "job-metacognitive-run");
    assert!(output_root.is_dir());
}

#[test]
fn local_json_job_uses_the_same_job_seam() {
    let dir = tempdir().expect("temporary output parent should exist");
    let mut job = ExperimentPacketJob::new(
        ExperimentPluginFactoryCatalog::local_json_with_metacognitive(
            GeneratorConfig::baseline_fsm(),
        )
        .expect("combined catalog should construct"),
        config(
            LOCAL_JSON_EXPERIMENT_PLUGIN_ID,
            "job-local-experiment",
            "job-local-run",
            provenance("local-json-job"),
            dir.path().join("local-json-job"),
            false,
            Vec::new(),
        ),
    )
    .expect("local job constructor should validate the registered plugin");

    let output = job
        .run_once()
        .expect("local job should complete a packet round trip");
    assert_eq!(
        output.packet.inner.config.plugin_id,
        LOCAL_JSON_EXPERIMENT_PLUGIN_ID
    );
    assert_eq!(
        output.packet.outer.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
}

#[test]
fn unknown_plugin_fails_before_output_creation() {
    let dir = tempdir().expect("temporary output parent should exist");
    let output_root = dir.path().join("unknown-plugin-job");
    let error = ExperimentPacketJob::new(
        ExperimentPluginFactoryCatalog::new(),
        config(
            "missing-plugin",
            "job-unknown-experiment",
            "job-unknown-run",
            provenance("unknown-plugin-job"),
            output_root.clone(),
            false,
            Vec::new(),
        ),
    )
    .err()
    .expect("unknown plugin must fail during construction");

    assert!(error.to_string().contains("not registered"));
    assert!(!output_root.exists());
}

#[test]
fn protected_path_is_delegated_and_second_run_is_rejected() {
    let dir = tempdir().expect("temporary output parent should exist");
    let output_root = dir.path().join("protected-job");
    let mut protected_job = ExperimentPacketJob::new(
        ExperimentPluginFactoryCatalog::metacognitive()
            .expect("metacognitive catalog should construct"),
        config(
            METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
            "job-protected-experiment",
            "job-protected-run",
            provenance("protected-job"),
            output_root.clone(),
            false,
            vec![dir.path().to_path_buf()],
        ),
    )
    .expect("protected job constructor should validate static inputs");
    let error = protected_job
        .run_once()
        .expect_err("protected output root must fail closed");
    assert!(error.to_string().contains("protected path"));
    assert!(!output_root.exists());

    let mut job = ExperimentPacketJob::new(
        ExperimentPluginFactoryCatalog::metacognitive()
            .expect("metacognitive catalog should construct"),
        config(
            METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
            "job-once-experiment",
            "job-once-run",
            provenance("one-shot-job"),
            dir.path().join("one-shot-job"),
            false,
            Vec::new(),
        ),
    )
    .expect("one-shot job constructor should validate");
    job.run_once().expect("first run should complete");
    let second = job
        .run_once()
        .expect_err("second run must be rejected by the job seam");
    assert!(second.to_string().contains("one-shot"));
}

#[test]
fn job_config_rejects_empty_output_or_protected_paths_before_catalog_resolution() {
    let empty_output = config(
        METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
        "job-invalid-output",
        "job-invalid-output-run",
        provenance("invalid-output"),
        std::path::PathBuf::new(),
        false,
        Vec::new(),
    );
    let error = empty_output
        .validate()
        .expect_err("empty output root must fail configuration validation");
    assert!(error.to_string().contains("output root must not be empty"));

    let empty_protected_path = config(
        METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
        "job-invalid-protected",
        "job-invalid-protected-run",
        provenance("invalid-protected"),
        "packet-output",
        false,
        vec![std::path::PathBuf::new()],
    );
    let error = empty_protected_path
        .validate()
        .expect_err("empty protected path must fail configuration validation");
    assert!(error
        .to_string()
        .contains("protected path must not be empty"));
}

#[test]
fn compatibility_injected_store_runs_materialize_then_readback() {
    let dir = tempdir().expect("temporary output parent should exist");
    let baseline = baseline_output(&dir, "recording-experiment", "recording-run");
    let events = Arc::new(Mutex::new(Vec::new()));
    let store = RecordingStore {
        events: events.clone(),
        expected_packet: baseline.packet.clone(),
        materialized_output: baseline.clone(),
        readback_output: baseline.clone(),
        fail_materialize: false,
    };
    let output_root = dir.path().join("recording-only");
    let mut job = ExperimentPacketJob::new_with_store(
        ExperimentPluginFactoryCatalog::metacognitive()
            .expect("metacognitive catalog should construct"),
        config(
            METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
            "recording-experiment",
            "recording-run",
            provenance("recording-store-baseline"),
            output_root.clone(),
            false,
            Vec::new(),
        ),
        Box::new(store),
    )
    .expect("injected store job should construct");

    let output = job.run_once().expect("injected store job should complete");
    assert_eq!(output, baseline);
    assert_eq!(
        *events.lock().expect("event lock should not poison"),
        vec!["materialize", "readback"]
    );
    assert!(!output_root.exists());
}

#[test]
fn compatibility_config_accepts_in_memory_store() {
    let mut job = ExperimentPacketJob::new_with_store(
        // Compatibility path retained for callers that already use the
        // filesystem-shaped config with a custom store.
        ExperimentPluginFactoryCatalog::metacognitive()
            .expect("metacognitive catalog should construct"),
        config(
            METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
            "in-memory-experiment",
            "in-memory-run",
            provenance("in-memory-store"),
            "unused-compatibility-root",
            false,
            Vec::new(),
        ),
        Box::new(InMemoryPluginCompositionPacketStore::new()),
    )
    .expect("in-memory store job should construct");

    let output = job
        .run_once()
        .expect("in-memory store job should complete a packet round trip");
    assert_eq!(output.manifest.experiment_id, "in-memory-experiment");
    assert_eq!(output.manifest.run_id, "in-memory-run");
    assert_eq!(
        output.manifest.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
}

#[test]
fn request_backed_in_memory_job_has_no_filesystem_destination() {
    let mut job = ExperimentPacketJob::new_with_request_and_store(
        ExperimentPluginFactoryCatalog::metacognitive()
            .expect("metacognitive catalog should construct"),
        request(
            METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
            "request-backed-experiment",
            "request-backed-run",
            provenance("request-backed-in-memory-store"),
        ),
        Box::new(InMemoryPluginCompositionPacketStore::new()),
    )
    .expect("request-backed in-memory job should construct");

    let output = job
        .run_once()
        .expect("request-backed in-memory job should complete");
    assert_eq!(output.manifest.experiment_id, "request-backed-experiment");
    assert_eq!(output.manifest.run_id, "request-backed-run");
    assert_eq!(job.request().plugin_id, METACOGNITIVE_EXPERIMENT_PLUGIN_ID);
    let replay = job
        .run_once()
        .expect_err("request-backed jobs remain one-shot");
    assert!(replay.to_string().contains("one-shot"));
}

#[test]
fn replacement_projector_traverses_keyed_job_and_strict_readback() {
    let mut job = ExperimentPacketJob::new_with_request_and_projector_and_keyed_store(
        ExperimentPluginFactoryCatalog::metacognitive()
            .expect("metacognitive catalog should construct"),
        request(
            METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
            "projector-job-experiment",
            "projector-job-run",
            provenance("projector-job"),
        ),
        Box::new(MetadataReportProjector),
        Box::new(InMemoryPluginCompositionPacketStore::new()),
    )
    .expect("replacement projector job should construct");

    let result = job
        .run_once_with_receipt()
        .expect("replacement projector job should materialize and read back");
    let metadata = result
        .output()
        .packet
        .composition_config
        .binding(zkbench_core::experiment_observability::ExperimentArtifactKind::Metadata)
        .expect("metadata binding should exist");
    assert!(metadata
        .sources
        .iter()
        .any(|source| source.inner_kind == ExperimentArtifactKind::Report));
    assert_eq!(
        result
            .output()
            .packet
            .composition_config
            .projector_descriptor()
            .expect("replacement projector identity should survive packet readback")
            .implementation_id,
        "packet-job-metadata-report-projector-v1"
    );
    assert!(result
        .output()
        .packet
        .composition_config
        .has_durable_projector_attribution());
    assert_eq!(
        result.receipt().manifest_digest,
        result.output().manifest_digest
    );
    assert_eq!(
        result.output().packet.outer.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
}

// State slice: benchmark-os-plugin-composition-projector-durable-attribution-v1.
#[test]
fn receipt_manifest_digest_retains_replacement_projector_attribution() {
    let standard_request = request(
        METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
        "receipt-projector-experiment",
        "receipt-projector-run",
        provenance("receipt-standard-projector"),
    );
    let mut standard_job = ExperimentPacketJob::new_with_request_and_keyed_store(
        ExperimentPluginFactoryCatalog::metacognitive().expect("standard catalog should construct"),
        standard_request.clone(),
        Box::new(InMemoryPluginCompositionPacketStore::new()),
    )
    .expect("standard receipt job should construct");
    let standard = standard_job
        .run_once_with_receipt()
        .expect("standard receipt job should complete");

    let mut replacement_job = ExperimentPacketJob::new_with_request_and_projector_and_keyed_store(
        ExperimentPluginFactoryCatalog::metacognitive()
            .expect("replacement catalog should construct"),
        standard_request,
        Box::new(MetadataReportProjector),
        Box::new(InMemoryPluginCompositionPacketStore::new()),
    )
    .expect("replacement receipt job should construct");
    let replacement = replacement_job
        .run_once_with_receipt()
        .expect("replacement receipt job should complete");

    assert_eq!(standard.receipt().key, replacement.receipt().key);
    assert_ne!(
        standard.receipt().manifest_digest,
        replacement.receipt().manifest_digest
    );
    assert_ne!(
        standard
            .output()
            .packet
            .composition_config
            .projector_descriptor()
            .expect("standard output should retain projector identity"),
        replacement
            .output()
            .packet
            .composition_config
            .projector_descriptor()
            .expect("replacement output should retain projector identity")
    );
}

#[test]
fn replacement_projector_traverses_filesystem_job_and_strict_readback() {
    let dir = tempdir().expect("temporary output parent should exist");
    let output_root = dir.path().join("projector-filesystem-job");
    let mut job = ExperimentPacketJob::new_with_projector(
        ExperimentPluginFactoryCatalog::metacognitive()
            .expect("metacognitive catalog should construct"),
        config(
            METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
            "projector-filesystem-experiment",
            "projector-filesystem-run",
            provenance("projector-filesystem-job"),
            output_root.clone(),
            false,
            Vec::new(),
        ),
        Box::new(MetadataReportProjector),
    )
    .expect("filesystem replacement projector job should construct");

    let output = job
        .run_once()
        .expect("filesystem replacement projector job should roundtrip");
    let metadata = output
        .packet
        .composition_config
        .binding(zkbench_core::experiment_observability::ExperimentArtifactKind::Metadata)
        .expect("metadata binding should exist");
    assert!(metadata
        .sources
        .iter()
        .any(|source| source.inner_kind == ExperimentArtifactKind::Report));
    assert!(output_root.is_dir());
}

#[test]
fn invalid_job_projector_fails_before_plugin_execution() {
    let dir = tempdir().expect("temporary output parent should exist");
    let output_root = dir.path().join("invalid-projector-job");
    let error = match ExperimentPacketJob::new_with_projector(
        ExperimentPluginFactoryCatalog::metacognitive()
            .expect("metacognitive catalog should construct"),
        config(
            METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
            "invalid-projector-experiment",
            "invalid-projector-run",
            provenance("invalid-projector-job"),
            output_root.clone(),
            false,
            Vec::new(),
        ),
        Box::new(WrongModuleProjector),
    ) {
        Ok(_) => panic!("invalid projector identity must fail during job construction"),
        Err(error) => error,
    };

    assert!(error.to_string().contains("unsupported module id"));
    assert!(!output_root.exists());
}

#[test]
fn request_validation_precedes_plugin_resolution() {
    let error = ExperimentPacketJob::new_with_request_and_store(
        ExperimentPluginFactoryCatalog::new(),
        request(
            METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
            "",
            "request-validation-run",
            provenance("request-validation"),
        ),
        Box::new(InMemoryPluginCompositionPacketStore::new()),
    )
    .err()
    .expect("invalid request must fail during construction");

    assert!(error.to_string().contains("experiment_id"));
}

#[test]
fn injected_store_rejects_packet_and_manifest_readback_drift() {
    let dir = tempdir().expect("temporary output parent should exist");
    let baseline = baseline_output(&dir, "drift-experiment", "drift-run");

    let mut packet_drift = baseline.clone();
    packet_drift.packet.inner.bundle_id = "drifted-inner-bundle".to_string();
    let store = RecordingStore {
        events: Arc::new(Mutex::new(Vec::new())),
        expected_packet: baseline.packet.clone(),
        materialized_output: baseline.clone(),
        readback_output: packet_drift,
        fail_materialize: false,
    };
    let mut packet_job = ExperimentPacketJob::new_with_store(
        ExperimentPluginFactoryCatalog::metacognitive()
            .expect("metacognitive catalog should construct"),
        config(
            METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
            "drift-experiment",
            "drift-run",
            provenance("recording-store-baseline"),
            dir.path().join("packet-drift"),
            false,
            Vec::new(),
        ),
        Box::new(store),
    )
    .expect("packet drift job should construct");
    let error = packet_job
        .run_once()
        .expect_err("packet readback drift must be rejected");
    assert!(error.to_string().contains("readback"));

    let mut manifest_drift = baseline.clone();
    manifest_drift.manifest.run_id = "drifted-run".to_string();
    let store = RecordingStore {
        events: Arc::new(Mutex::new(Vec::new())),
        expected_packet: baseline.packet.clone(),
        materialized_output: baseline.clone(),
        readback_output: manifest_drift,
        fail_materialize: false,
    };
    let mut manifest_job = ExperimentPacketJob::new_with_store(
        ExperimentPluginFactoryCatalog::metacognitive()
            .expect("metacognitive catalog should construct"),
        config(
            METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
            "drift-experiment",
            "drift-run",
            provenance("recording-store-baseline"),
            dir.path().join("manifest-drift"),
            false,
            Vec::new(),
        ),
        Box::new(store),
    )
    .expect("manifest drift job should construct");
    let error = manifest_job
        .run_once()
        .expect_err("manifest readback drift must be rejected");
    assert!(error.to_string().contains("readback"));
}

#[test]
fn injected_store_failure_prevents_readback_and_replay() {
    let dir = tempdir().expect("temporary output parent should exist");
    let baseline = baseline_output(&dir, "failure-experiment", "failure-run");
    let events = Arc::new(Mutex::new(Vec::new()));
    let store = RecordingStore {
        events: events.clone(),
        expected_packet: baseline.packet.clone(),
        materialized_output: baseline.clone(),
        readback_output: baseline,
        fail_materialize: true,
    };
    let mut job = ExperimentPacketJob::new_with_store(
        ExperimentPluginFactoryCatalog::metacognitive()
            .expect("metacognitive catalog should construct"),
        config(
            METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
            "failure-experiment",
            "failure-run",
            provenance("recording-store-baseline"),
            dir.path().join("failure-only"),
            false,
            Vec::new(),
        ),
        Box::new(store),
    )
    .expect("failure job should construct");
    let error = job
        .run_once()
        .expect_err("materialization failure must be returned");
    assert!(error.to_string().contains("materialization failed"));
    assert_eq!(
        *events.lock().expect("event lock should not poison"),
        vec!["materialize"]
    );
    let replay = job.run_once().expect_err("failed jobs remain one-shot");
    assert!(replay.to_string().contains("one-shot"));
}

#[test]
fn keyed_request_backed_job_roundtrips_through_receipt_bound_store() {
    let mut job = ExperimentPacketJob::new_with_request_and_keyed_store(
        ExperimentPluginFactoryCatalog::metacognitive()
            .expect("metacognitive catalog should construct"),
        request(
            METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
            "keyed-request-experiment",
            "keyed-request-run",
            provenance("keyed-request-store"),
        ),
        Box::new(InMemoryPluginCompositionPacketStore::new()),
    )
    .expect("keyed request-backed job should construct");

    let output = job
        .run_once()
        .expect("keyed request-backed job should roundtrip");
    assert_eq!(output.manifest.experiment_id, "keyed-request-experiment");
    assert_eq!(output.manifest.run_id, "keyed-request-run");
}

#[test]
fn keyed_job_exports_receipt_bound_result_without_breaking_legacy_output() {
    let mut job = ExperimentPacketJob::new_with_request_and_keyed_store(
        ExperimentPluginFactoryCatalog::metacognitive()
            .expect("metacognitive catalog should construct"),
        request(
            METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
            "exported-receipt-experiment",
            "exported-receipt-run",
            provenance("exported-receipt-result"),
        ),
        Box::new(InMemoryPluginCompositionPacketStore::new()),
    )
    .expect("receipt-result job should construct");

    let result = job
        .run_once_with_receipt()
        .expect("receipt-result job should complete");
    assert_eq!(
        result.receipt().key.plugin_id,
        METACOGNITIVE_EXPERIMENT_PLUGIN_ID
    );
    assert_eq!(
        result.receipt().key.experiment_id,
        "exported-receipt-experiment"
    );
    assert_eq!(result.receipt().key.run_id, "exported-receipt-run");
    assert_eq!(
        result.receipt().manifest_digest,
        result.output().manifest_digest
    );
}

#[test]
fn receipt_result_preserves_validated_materialization_on_consuming_handoff() {
    let mut job = ExperimentPacketJob::new_with_request_and_keyed_store(
        ExperimentPluginFactoryCatalog::metacognitive()
            .expect("metacognitive catalog should construct"),
        request(
            METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
            "validated-result-experiment",
            "validated-result-run",
            provenance("validated-result-handoff"),
        ),
        Box::new(InMemoryPluginCompositionPacketStore::new()),
    )
    .expect("validated result job should construct");

    let result = job
        .run_once_with_receipt()
        .expect("validated result job should complete");
    let output_digest = result.output().manifest_digest.clone();
    let receipt_digest = result.receipt().manifest_digest.clone();
    assert_eq!(output_digest, receipt_digest);

    let materialization = result.into_materialization();
    assert_eq!(materialization.output().manifest_digest, output_digest);
    assert_eq!(materialization.receipt().manifest_digest, receipt_digest);
}

#[test]
fn typed_identity_is_shared_without_changing_packet_wire_fields() {
    // State slice: benchmark-os-plugin-composition-identity-constructor-locality-v1.
    let request_identity = request(
        METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
        "identity-experiment",
        "identity-run",
        provenance("typed-identity"),
    )
    .identity()
    .expect("request identity should validate");
    let configured = config(
        METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
        "identity-experiment",
        "identity-run",
        provenance("typed-identity"),
        "unused-output-root",
        false,
        Vec::new(),
    );
    assert_eq!(
        configured
            .identity()
            .expect("config identity should validate"),
        request_identity
    );

    let packet = generic_packet("identity-experiment", "identity-run");
    let packet_identity = packet
        .composition_config
        .identity()
        .expect("composition identity should validate");
    let key = PacketStoreKey::from_packet(&packet).expect("packet key should build");
    assert_eq!(
        key.identity().expect("key identity should validate"),
        packet_identity
    );

    let wire_json = serialize_plugin_composition_config_json(&packet.composition_config)
        .expect("composition config should serialize");
    assert!(wire_json.contains("\"experiment_id\""));
    assert!(wire_json.contains("\"run_id\""));
    assert!(!wire_json.contains("\"identity\""));
}

#[test]
fn typed_identity_rejects_blank_components() {
    let error = PluginCompositionIdentity::new("plugin", " ", "run")
        .expect_err("blank experiment identity must fail");
    assert!(error.to_string().contains("experiment_id"));
}

#[test]
fn keyed_store_materialization_handoff_is_receipt_bound() {
    let packet = generic_packet(
        "materialization-handoff-experiment",
        "materialization-handoff-run",
    );
    let key = PacketStoreKey::from_packet(&packet).expect("packet key should build");
    let mut store = InMemoryPluginCompositionPacketStore::new();
    let handoff = store
        .materialize_keyed_validated(&key, &packet)
        .expect("validated materialization handoff should succeed");
    assert_eq!(handoff.output().packet, packet);
    assert_eq!(handoff.receipt().key, key);

    let (output, receipt) = handoff.into_parts();
    let mut drifted_output = output.clone();
    drifted_output.manifest.run_id = "drifted-materialization-handoff-run".to_string();
    assert!(ValidatedPacketStoreMaterialization::new(drifted_output, receipt).is_err());
}

#[test]
fn keyed_store_rejects_cross_run_receipts() {
    let first = generic_packet("keyed-first-experiment", "keyed-first-run");
    let second = generic_packet("keyed-second-experiment", "keyed-second-run");
    let first_key = PacketStoreKey::from_packet(&first).expect("first packet key should build");
    let second_key = PacketStoreKey::from_packet(&second).expect("second packet key should build");
    let mut store = InMemoryPluginCompositionPacketStore::new();
    let first_materialization = store
        .materialize_keyed(&first_key, &first)
        .expect("first keyed materialization should succeed");
    let _second_materialization = store
        .materialize_keyed(&second_key, &second)
        .expect("second keyed materialization should succeed");

    let forged_cross_run_receipt = PacketStoreReceipt {
        key: second_key,
        manifest_digest: first_materialization.receipt.manifest_digest,
    };
    let error = store
        .readback_keyed(&forged_cross_run_receipt)
        .expect_err("a receipt from another run must not read back this key");
    assert!(error.to_string().contains("receipt"));
}

#[test]
fn packet_store_key_rejects_packet_identity_mismatch_before_materialization() {
    let packet = generic_packet("keyed-identity-experiment", "keyed-identity-run");
    let wrong_key = PacketStoreKey::new(
        METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
        "keyed-identity-experiment",
        "different-run",
    )
    .expect("wrong key shape should still be valid");
    let mut store = InMemoryPluginCompositionPacketStore::new();
    let error = store
        .materialize_keyed(&wrong_key, &packet)
        .expect_err("key identity mismatch must fail before storage");
    assert!(error.to_string().contains("does not match"));
}
