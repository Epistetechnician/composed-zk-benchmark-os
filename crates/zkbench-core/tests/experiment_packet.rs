// State slice: benchmark-os-experiment-packet-materialization-readback-v1.
// Write-safety extension: benchmark-os-experiment-packet-write-symlink-preflight-v1.
// Integrity extension: benchmark-os-experiment-packet-canonical-digest-sidecar-v1.
// Generic transport extension: benchmark-os-plugin-agnostic-packet-materialization-readback-v1.
// Output handoff validation slice: benchmark-os-plugin-composition-output-handoff-validation-v1.
// Durable projector attribution slice: benchmark-os-plugin-composition-projector-durable-attribution-v1.
// Packet-output handoff validation slice: benchmark-os-experiment-packet-output-handoff-validation-v1.
// Canonical typed transport slice: benchmark-os-experiment-packet-canonical-typed-transport-v1.
// This test module covers only local packet files, integrity, and claim limits.

use std::fs;

use tempfile::tempdir;
use zkbench_core::experiment_observability::{
    ExperimentProvenance, ExperimentRunner, ObservabilityBudget, ObservabilitySignals,
};
use zkbench_core::{
    compute_artifact_digest_bytes, compute_experiment_packet_manifest_digest,
    deserialize_experiment_packet_manifest_json, deserialize_plugin_composition_config_json,
    read_experiment_packet_outputs, read_plugin_composition_packet_outputs,
    read_plugin_composition_packet_outputs_validated, serialize_experiment_packet_manifest_json,
    serialize_plugin_composition_config_json, write_experiment_packet_outputs,
    write_plugin_composition_packet_outputs, write_plugin_composition_packet_outputs_validated,
    ArtifactKind, ArtifactRole, ClaimBoundary, ExperimentPacket, ExperimentPacketComposition,
    ExperimentPluginFactoryCatalog, GeneratorConfig, LocalJsonExperimentRunner, PacketStoreKey,
    PacketStoreReceipt, PluginCompositionPacket, PluginCompositionRunner,
    EXPERIMENT_PACKET_COMPOSITION_CONFIG_PATH, EXPERIMENT_PACKET_INNER_BUNDLE_DIGEST_PATH,
    EXPERIMENT_PACKET_INNER_BUNDLE_PATH, EXPERIMENT_PACKET_MANIFEST_PATH,
    EXPERIMENT_PACKET_OUTER_BUNDLE_PATH,
};

fn provenance(label: &str) -> ExperimentProvenance {
    ExperimentProvenance {
        who: "experiment-packet-test".to_string(),
        what: label.to_string(),
        when: "logical-test-time".to_string(),
        version: "experiment-packet-test-v1".to_string(),
        source_revision: "local-uncommitted".to_string(),
    }
}

fn packet(experiment_id: &str, run_id: &str) -> ExperimentPacket {
    let mut runner = LocalJsonExperimentRunner::new(
        GeneratorConfig::baseline_fsm(),
        experiment_id,
        run_id,
        ObservabilitySignals {
            novelty_milli: 200,
            uncertainty_milli: 300,
            failure_milli: 800,
        },
        provenance("compose-local-packet"),
        ObservabilityBudget {
            tier1_samples_remaining: 1,
            tier2_deep_dives_remaining: 1,
            tier3_gold_cases_remaining: 0,
        },
    )
    .expect("runner should construct");
    let outer = runner.run().expect("runner should compose the packet");
    let composition_config = runner
        .composition_config()
        .expect("runner should retain composition config")
        .clone();
    let inner = ExperimentPluginFactoryCatalog::local_json(GeneratorConfig::baseline_fsm())
        .expect("local factory catalog should construct")
        .run(zkbench_core::LOCAL_JSON_EXPERIMENT_PLUGIN_ID)
        .expect("inner local bundle should run through the factory catalog");
    ExperimentPacket {
        inner,
        composition_config,
        outer,
    }
}

fn generic_packet(experiment_id: &str, run_id: &str) -> PluginCompositionPacket {
    let catalog = ExperimentPluginFactoryCatalog::metacognitive()
        .expect("metacognitive catalog should construct");
    let plugin = catalog
        .instantiate(zkbench_core::METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("metacognitive plugin should instantiate");
    let runner = PluginCompositionRunner::new(
        plugin,
        experiment_id,
        run_id,
        provenance("compose-generic-packet"),
    )
    .expect("generic runner should construct");
    runner.run().expect("generic composition should run").into()
}

#[test]
fn packet_materialization_round_trips_with_declared_files_and_digests() {
    let dir = tempdir().expect("temporary output parent should exist");
    let output_root = dir.path().join("experiment-packet");
    let packet = packet("packet-experiment-1", "packet-run-1");

    let written = write_experiment_packet_outputs(&output_root, &packet, false, &[])
        .expect("typed packet should materialize");
    let read = read_experiment_packet_outputs(&output_root, &[])
        .expect("materialized packet should read back");

    assert_eq!(written.packet, packet);
    assert_eq!(read.packet, packet);
    assert_eq!(written.manifest, read.manifest);
    assert_eq!(
        written.manifest_digest,
        compute_experiment_packet_manifest_digest(&written.manifest)
            .expect("manifest digest should be deterministic")
    );
    assert_eq!(
        fs::read(output_root.join(EXPERIMENT_PACKET_MANIFEST_PATH))
            .expect("manifest should be present"),
        serde_json::to_string(&written.manifest)
            .expect("manifest should serialize")
            .as_bytes()
    );
    assert!(output_root
        .join(EXPERIMENT_PACKET_INNER_BUNDLE_PATH)
        .is_file());
    assert!(output_root
        .join(EXPERIMENT_PACKET_COMPOSITION_CONFIG_PATH)
        .is_file());
    assert!(output_root
        .join(EXPERIMENT_PACKET_OUTER_BUNDLE_PATH)
        .is_file());
}

#[test]
fn packet_readback_rejects_payload_tampering_even_when_sidecar_is_updated() {
    let dir = tempdir().expect("temporary output parent should exist");
    let output_root = dir.path().join("tampered-packet");
    let packet = packet("packet-experiment-2", "packet-run-2");
    write_experiment_packet_outputs(&output_root, &packet, false, &[])
        .expect("packet should materialize");

    let inner_path = output_root.join(EXPERIMENT_PACKET_INNER_BUNDLE_PATH);
    let mut tampered = fs::read(&inner_path).expect("inner bundle should be readable");
    tampered.push(b' ');
    fs::write(&inner_path, &tampered).expect("test should tamper with inner bytes");
    let digest = compute_artifact_digest_bytes(
        &tampered,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    );
    fs::write(
        output_root.join(EXPERIMENT_PACKET_INNER_BUNDLE_DIGEST_PATH),
        format!("{}\n", digest.hex_digest),
    )
    .expect("test should update the stale sidecar");

    let stale_sidecar = read_experiment_packet_outputs(&output_root, &[])
        .expect_err("a changed payload must invalidate the original manifest");
    assert!(stale_sidecar.to_string().contains("payload bytes"));

    let manifest_path = output_root.join(EXPERIMENT_PACKET_MANIFEST_PATH);
    let manifest_json = fs::read_to_string(&manifest_path).expect("manifest should be readable");
    let mut manifest = deserialize_experiment_packet_manifest_json(&manifest_json)
        .expect("original manifest should be valid");
    manifest.inner_bundle.digest = digest;
    let updated_manifest_json = serialize_experiment_packet_manifest_json(&manifest)
        .expect("updated manifest should serialize");
    fs::write(&manifest_path, &updated_manifest_json).expect("test should update manifest bytes");
    let updated_manifest_digest = compute_experiment_packet_manifest_digest(&manifest)
        .expect("updated manifest should digest");
    fs::write(
        output_root.join(zkbench_core::EXPERIMENT_PACKET_MANIFEST_DIGEST_PATH),
        format!("{}\n", updated_manifest_digest.hex_digest),
    )
    .expect("test should update manifest sidecar");

    let error = read_experiment_packet_outputs(&output_root, &[])
        .expect_err("updated sidecars must not make noncanonical JSON valid");
    assert!(error.to_string().contains("inner_bytes"));
}

#[test]
fn packet_readback_rejects_noncanonical_digest_sidecar_whitespace() {
    let dir = tempdir().expect("temporary output parent should exist");
    let output_root = dir.path().join("noncanonical-sidecar-packet");
    let packet = packet("packet-experiment-sidecar", "packet-run-sidecar");
    write_experiment_packet_outputs(&output_root, &packet, false, &[])
        .expect("packet should materialize");

    let sidecar_path = output_root.join(EXPERIMENT_PACKET_INNER_BUNDLE_DIGEST_PATH);
    let canonical = fs::read_to_string(&sidecar_path).expect("sidecar should be readable");
    fs::write(&sidecar_path, format!(" {canonical}"))
        .expect("test should add leading sidecar whitespace");

    let error = read_experiment_packet_outputs(&output_root, &[])
        .expect_err("leading sidecar whitespace must be rejected");
    assert!(error.to_string().contains("digest sidecar"));

    fs::write(&sidecar_path, format!("{canonical}\n"))
        .expect("test should add trailing sidecar whitespace");
    let error = read_experiment_packet_outputs(&output_root, &[])
        .expect_err("trailing sidecar whitespace must be rejected");
    assert!(error.to_string().contains("digest sidecar"));
}

#[test]
fn packet_write_requires_explicit_matching_overwrite() {
    let dir = tempdir().expect("temporary output parent should exist");
    let output_root = dir.path().join("overwrite-packet");
    let first = packet("packet-experiment-3", "packet-run-3");
    let second = packet("packet-experiment-4", "packet-run-4");

    write_experiment_packet_outputs(&output_root, &first, false, &[])
        .expect("first packet should materialize");
    let occupied = write_experiment_packet_outputs(&output_root, &first, false, &[])
        .expect_err("non-overwrite writes must reject an occupied root");
    assert!(occupied.to_string().contains("explicit overwrite"));
    write_experiment_packet_outputs(&output_root, &first, true, &[])
        .expect("matching overwrite should be idempotent");
    let drift = write_experiment_packet_outputs(&output_root, &second, true, &[])
        .expect_err("mismatched overwrite must not repair an existing packet");
    assert!(drift.to_string().contains("typed packet") || drift.to_string().contains("match"));
}

#[test]
fn packet_readback_rejects_missing_and_unexpected_files() {
    let dir = tempdir().expect("temporary output parent should exist");
    let missing_root = dir.path().join("missing-packet");
    let packet = packet("packet-experiment-5", "packet-run-5");
    write_experiment_packet_outputs(&missing_root, &packet, false, &[])
        .expect("packet should materialize");
    fs::remove_file(missing_root.join(EXPERIMENT_PACKET_OUTER_BUNDLE_PATH))
        .expect("test should remove one declared file");
    let missing = read_experiment_packet_outputs(&missing_root, &[])
        .expect_err("missing packet file must be rejected");
    assert!(missing.to_string().contains("missing"));

    let unexpected_root = dir.path().join("unexpected-packet");
    write_experiment_packet_outputs(&unexpected_root, &packet, false, &[])
        .expect("second packet should materialize");
    fs::write(unexpected_root.join("unexpected.txt"), b"unlisted")
        .expect("test should add an unexpected file");
    let unexpected = read_experiment_packet_outputs(&unexpected_root, &[])
        .expect_err("unexpected packet file must be rejected");
    assert!(unexpected.to_string().contains("unexpected"));
}

#[test]
fn packet_output_root_rejects_protected_paths() {
    let dir = tempdir().expect("temporary output parent should exist");
    let output_root = dir.path().join("protected-packet");
    let packet = packet("packet-experiment-6", "packet-run-6");
    let error =
        write_experiment_packet_outputs(&output_root, &packet, false, &[dir.path().to_path_buf()])
            .expect_err("packet output must not overlap a protected parent");
    assert!(error.to_string().contains("protected path"));
}

#[cfg(unix)]
#[test]
fn packet_readback_rejects_symlinked_payload_paths() {
    use std::os::unix::fs::symlink;

    let dir = tempdir().expect("temporary output parent should exist");
    let output_root = dir.path().join("symlink-packet");
    let packet = packet("packet-experiment-7", "packet-run-7");
    write_experiment_packet_outputs(&output_root, &packet, false, &[])
        .expect("packet should materialize");
    let target = output_root.join(EXPERIMENT_PACKET_INNER_BUNDLE_PATH);
    let backup = dir.path().join("inner-backup.json");
    fs::rename(&target, &backup).expect("test should move the real payload");
    symlink(&backup, &target).expect("test should install a symlink payload");

    let error = read_experiment_packet_outputs(&output_root, &[])
        .expect_err("symlinked packet payload must be rejected");
    assert!(error.to_string().contains("symlink"));
}

#[test]
fn packet_claim_ceiling_remains_level_zero() {
    let packet = packet("packet-experiment-8", "packet-run-8");
    assert_eq!(packet.outer.claim_boundary, ClaimBoundary::Level0DesignNote);
}

#[test]
fn generic_plugin_packet_materialization_round_trips_through_same_filesystem_seam() {
    let dir = tempdir().expect("temporary output parent should exist");
    let output_root = dir.path().join("generic-plugin-packet");
    let packet = generic_packet("generic-packet-experiment-1", "generic-packet-run-1");

    let written = write_plugin_composition_packet_outputs(&output_root, &packet, false, &[])
        .expect("generic packet should materialize");
    let read = read_plugin_composition_packet_outputs(&output_root, &[])
        .expect("generic packet should read back");

    assert_eq!(written.packet, packet);
    assert_eq!(read.packet, packet);
    assert_eq!(written.manifest, read.manifest);
    assert_eq!(
        written.manifest.experiment_id,
        "generic-packet-experiment-1"
    );
    assert_eq!(written.manifest.run_id, "generic-packet-run-1");
    assert_eq!(
        packet.composition_config.experiment_id(),
        "generic-packet-experiment-1"
    );
    assert_eq!(packet.composition_config.run_id(), "generic-packet-run-1");
    assert_eq!(
        packet
            .composition_config
            .projector_descriptor()
            .expect("generic packet should retain projector identity")
            .implementation_id,
        "standard-plugin-composition-projector-v1"
    );
    assert!(packet
        .composition_config
        .has_durable_projector_attribution());
    assert_eq!(packet.outer.claim_boundary, ClaimBoundary::Level0DesignNote);
}

#[test]
fn canonical_typed_transport_preserves_legacy_packet_output() {
    let dir = tempdir().expect("temporary output parent should exist");
    let legacy_root = dir.path().join("legacy-packet");
    let typed_root = dir.path().join("typed-packet");
    let packet = generic_packet("typed-transport-experiment-1", "typed-transport-run-1");

    let legacy = write_plugin_composition_packet_outputs(&legacy_root, &packet, false, &[])
        .expect("legacy packet writer should materialize");
    let typed = write_plugin_composition_packet_outputs_validated(&typed_root, &packet, false, &[])
        .expect("typed packet writer should materialize");
    assert_eq!(typed.as_output(), &legacy);

    let typed_read = read_plugin_composition_packet_outputs_validated(&typed_root, &[])
        .expect("typed packet reader should read back");
    let legacy_read = read_plugin_composition_packet_outputs(&typed_root, &[])
        .expect("legacy packet reader should read back typed output");
    assert_eq!(typed_read.as_output(), &legacy_read);
    assert_eq!(typed_read.packet(), &packet);
}

#[test]
fn generic_output_uses_fallible_packet_handoff_before_materialization() {
    let catalog = ExperimentPluginFactoryCatalog::metacognitive()
        .expect("metacognitive catalog should construct");
    let plugin = catalog
        .instantiate(zkbench_core::METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("metacognitive plugin should instantiate");
    let output = PluginCompositionRunner::new(
        plugin,
        "fallible-handoff-experiment",
        "fallible-handoff-run",
        provenance("fallible-handoff"),
    )
    .expect("generic runner should construct")
    .run()
    .expect("generic composition should run");
    let packet = output
        .clone()
        .try_into_packet()
        .expect("validated output should convert to a packet");
    assert_eq!(packet.inner, output.inner);
    assert_eq!(packet.composition_config, output.config);
    assert_eq!(packet.outer, output.outer);

    let mut tampered = output;
    tampered.config.run_id = "drifted-fallible-handoff-run".to_string();
    assert!(tampered.try_into_packet().is_err());
}

#[test]
fn packet_output_handoff_owns_canonical_manifest_and_digest() {
    let dir = tempdir().expect("temporary output parent should exist");
    let output_root = dir.path().join("validated-packet-output");
    let packet = packet("validated-output-experiment", "validated-output-run");
    let output = write_experiment_packet_outputs(&output_root, &packet, false, &[])
        .expect("packet output should materialize");
    let expected_digest = output.manifest_digest.clone();
    let validated = output
        .clone()
        .into_validated()
        .expect("canonical packet output should validate");

    assert_eq!(validated.packet(), &packet);
    assert_eq!(validated.manifest_digest(), &expected_digest);
    assert_eq!(validated.as_output(), &output);

    let mut drifted = output;
    drifted.packet.composition_config.run_id = "drifted-output-run".to_string();
    assert!(drifted.into_validated().is_err());

    assert_eq!(
        validated.into_output(),
        write_experiment_packet_outputs(
            dir.path().join("validated-packet-output-copy"),
            &packet,
            false,
            &[],
        )
        .expect("equivalent packet output should materialize")
    );
}

#[test]
fn typed_packet_output_issues_receipt_without_reopening_public_fields() {
    let dir = tempdir().expect("temporary output parent should exist");
    let output_root = dir.path().join("typed-receipt-packet");
    let packet = generic_packet("typed-receipt-experiment", "typed-receipt-run");
    let output = write_plugin_composition_packet_outputs(&output_root, &packet, false, &[])
        .expect("generic packet output should materialize");
    let validated = output
        .clone()
        .into_validated()
        .expect("generic packet output should validate");
    let key = PacketStoreKey::from_packet(&packet).expect("packet key should derive");

    let typed_receipt = PacketStoreReceipt::from_validated_output(key.clone(), &validated)
        .expect("typed receipt should issue from validated output");
    let compatibility_receipt = PacketStoreReceipt::from_output(key, &output)
        .expect("compatibility receipt should retain the same contract");
    assert_eq!(typed_receipt, compatibility_receipt);
    assert_eq!(typed_receipt.manifest_digest, output.manifest_digest);

    let mut drifted = output;
    drifted.packet.composition_config.run_id = "typed-receipt-drift".to_string();
    assert!(drifted.into_validated().is_err());
}

#[test]
fn generic_plugin_packet_rejects_noncanonical_config_after_manifest_reseal() {
    let dir = tempdir().expect("temporary output parent should exist");
    let output_root = dir.path().join("generic-noncanonical-packet");
    let packet = generic_packet("generic-packet-experiment-2", "generic-packet-run-2");
    write_plugin_composition_packet_outputs(&output_root, &packet, false, &[])
        .expect("generic packet should materialize");

    let config_path = output_root.join(EXPERIMENT_PACKET_COMPOSITION_CONFIG_PATH);
    let mut config_bytes = fs::read(&config_path).expect("generic config should be readable");
    config_bytes.push(b' ');
    fs::write(&config_path, &config_bytes).expect("test should tamper with config bytes");
    let config_digest = compute_artifact_digest_bytes(
        &config_bytes,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    );
    let manifest_path = output_root.join(EXPERIMENT_PACKET_MANIFEST_PATH);
    let manifest_json = fs::read_to_string(&manifest_path).expect("manifest should be readable");
    let mut manifest = deserialize_experiment_packet_manifest_json(&manifest_json)
        .expect("manifest should be valid before tampering");
    manifest.composition_config.digest = config_digest;
    let updated_manifest_json = serialize_experiment_packet_manifest_json(&manifest)
        .expect("updated manifest should serialize");
    fs::write(&manifest_path, &updated_manifest_json).expect("test should update manifest");
    let updated_manifest_digest = compute_experiment_packet_manifest_digest(&manifest)
        .expect("updated manifest should digest");
    fs::write(
        output_root.join(zkbench_core::EXPERIMENT_PACKET_COMPOSITION_CONFIG_DIGEST_PATH),
        format!("{}\n", manifest.composition_config.digest.hex_digest),
    )
    .expect("test should update config sidecar");
    fs::write(
        output_root.join(zkbench_core::EXPERIMENT_PACKET_MANIFEST_DIGEST_PATH),
        format!("{}\n", updated_manifest_digest.hex_digest),
    )
    .expect("test should update manifest sidecar");

    let error = read_plugin_composition_packet_outputs(&output_root, &[])
        .expect_err("noncanonical generic config must be rejected");
    assert!(error.to_string().contains("config_bytes"));
}

#[test]
fn generic_plugin_packet_rejects_projector_descriptor_drift_after_resealing() {
    let dir = tempdir().expect("temporary output parent should exist");
    let output_root = dir.path().join("generic-projector-drift-packet");
    let packet = generic_packet(
        "generic-projector-drift-experiment",
        "generic-projector-drift-run",
    );
    write_plugin_composition_packet_outputs(&output_root, &packet, false, &[])
        .expect("generic packet should materialize");

    let config_path = output_root.join(EXPERIMENT_PACKET_COMPOSITION_CONFIG_PATH);
    let config_json = fs::read_to_string(&config_path).expect("generic config should be readable");
    let mut config = deserialize_plugin_composition_config_json(&config_json)
        .expect("generic config should deserialize");
    config
        .projector_descriptor
        .as_mut()
        .expect("new generic packet should retain projector identity")
        .implementation_id = "tampered-projector-v1".to_string();
    let tampered_config_json = serialize_plugin_composition_config_json(&config)
        .expect("tampered config should serialize canonically");
    fs::write(&config_path, &tampered_config_json).expect("test should tamper with config");

    let config_digest = compute_artifact_digest_bytes(
        tampered_config_json.as_bytes(),
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    );
    let manifest_path = output_root.join(EXPERIMENT_PACKET_MANIFEST_PATH);
    let manifest_json = fs::read_to_string(&manifest_path).expect("manifest should be readable");
    let mut manifest = deserialize_experiment_packet_manifest_json(&manifest_json)
        .expect("manifest should be valid before tampering");
    manifest.composition_config.digest = config_digest.clone();
    let updated_manifest_json = serialize_experiment_packet_manifest_json(&manifest)
        .expect("updated manifest should serialize");
    fs::write(&manifest_path, updated_manifest_json)
        .expect("test should update the manifest bytes");
    let updated_manifest_digest = compute_experiment_packet_manifest_digest(&manifest)
        .expect("updated manifest digest should compute");
    fs::write(
        output_root.join(zkbench_core::EXPERIMENT_PACKET_COMPOSITION_CONFIG_DIGEST_PATH),
        format!("{}\n", config_digest.hex_digest),
    )
    .expect("test should reseal the config sidecar");
    fs::write(
        output_root.join(zkbench_core::EXPERIMENT_PACKET_MANIFEST_DIGEST_PATH),
        format!("{}\n", updated_manifest_digest.hex_digest),
    )
    .expect("test should reseal the manifest sidecar");

    let error = read_plugin_composition_packet_outputs(&output_root, &[])
        .expect_err("descriptor drift must fail cross-artifact validation");
    assert!(error.to_string().contains("outer_config_digest"));
}
