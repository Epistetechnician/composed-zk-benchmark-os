//! Attach inert external replay plans and reproduction metadata to local packs.

use std::fs;
use std::path::Path;

use crate::adapters::{
    build_gnark_recursion_envelope_plan, build_zk_harness_dry_run_plan_from_pack,
    build_zkml_narrow_workload_plan, serialize_gnark_recursion_envelope_plan_json,
    serialize_zk_harness_dry_run_plan_json, serialize_zkml_narrow_workload_plan_json,
};
use crate::error::{Result, ZkBenchError};
use crate::evidence::{compute_artifact_digest, ArtifactKind, ArtifactRole, ClaimBoundary};
use crate::pack::manifest::{BenchmarkPackFile, BenchmarkPackFileRole, BenchmarkPackManifest};
use crate::pack::reader::BenchmarkPackReader;
use crate::pack::writer::{digest_for_bytes, validate_relative_path};

use super::eligibility::{evaluate_level2_eligibility, Level2EligibilityReport};
use super::metadata::{
    BenchmarkPackReproductionMetadata, BenchmarkPackReproductionMetadataVersion,
    ExternalReplayPlanAttachment, ExternalReplayPlanKind,
};
use super::validation::validate_benchmark_pack_reproduction_metadata;

const REPRODUCTION_METADATA_PATH: &str = "reproduction/metadata.json";

/// Attach inert external replay plans and reproduction metadata to an existing pack.
pub fn attach_reproduction_bundle_to_pack(
    root: impl AsRef<Path>,
) -> Result<BenchmarkPackReproductionMetadata> {
    let root = root.as_ref();
    let reader = BenchmarkPackReader::read(root)?;
    let validation = reader.validate();
    if !validation.valid {
        return Err(ZkBenchError::benchmark_pack(
            root.display().to_string(),
            format!("source pack validation failed: {:?}", validation.errors),
        ));
    }
    if reader.manifest().reproduction_metadata_ref.is_some() {
        return Err(ZkBenchError::benchmark_pack(
            REPRODUCTION_METADATA_PATH,
            "reproduction metadata is already attached to this pack",
        ));
    }

    let source_manifest = reader.manifest().clone();
    let source_pack_manifest_digest = compute_artifact_digest(
        &source_manifest,
        Some(ArtifactKind::BenchmarkPackManifest),
        Some(ArtifactRole::Manifest),
    )?;

    let zk_harness_plan = build_zk_harness_dry_run_plan_from_pack(&reader)?;
    let gnark_plan = build_gnark_recursion_envelope_plan()?;
    let zkml_plan = build_zkml_narrow_workload_plan()?;

    let mut new_files = Vec::new();
    let mut attachments = Vec::new();

    let plan_specs = [
        (
            ExternalReplayPlanKind::ZkHarnessDryRun,
            format!("external_plans/zk_harness/{}.json", zk_harness_plan.id),
            serialize_zk_harness_dry_run_plan_json(&zk_harness_plan)?,
        ),
        (
            ExternalReplayPlanKind::GnarkRecursionEnvelope,
            format!("external_plans/gnark_recursion/{}.json", gnark_plan.id),
            serialize_gnark_recursion_envelope_plan_json(&gnark_plan)?,
        ),
        (
            ExternalReplayPlanKind::ZkmlNarrowWorkload,
            format!("external_plans/zkml_narrow/{}.json", zkml_plan.id),
            serialize_zkml_narrow_workload_plan_json(&zkml_plan)?,
        ),
    ];

    for (kind, relative_path, json) in plan_specs {
        let file = write_bytes_artifact(
            root,
            &relative_path,
            json.as_bytes(),
            BenchmarkPackFileRole::ExternalReplayPlan,
        )?;
        attachments.push(ExternalReplayPlanAttachment {
            kind,
            plan_id: plan_id_from_path(&relative_path),
            relative_path,
            plan_digest: file.digest.clone(),
            execution_policy: "Disabled".to_string(),
            inert: true,
            notes: vec!["Inert external replay plan attachment only.".to_string()],
        });
        new_files.push(file);
    }

    let mut metadata = BenchmarkPackReproductionMetadata {
        id: format!("reproduction_{}", source_manifest.id),
        version: BenchmarkPackReproductionMetadataVersion::default(),
        source_pack_id: source_manifest.id.clone(),
        source_pack_manifest_digest,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        attachments,
        level2_eligibility: Level2EligibilityReport {
            version: Default::default(),
            status: super::eligibility::Level2EligibilityStatus::Blocked,
            eligible: false,
            blocking_reasons: Vec::new(),
            claim_boundary: ClaimBoundary::Level0DesignNote,
            notes: Vec::new(),
        },
        notes: vec![
            "Reproduction metadata is not official benchmark evidence.".to_string(),
            "Attached external replay plans are inert and disabled by default.".to_string(),
        ],
    };
    metadata.level2_eligibility = evaluate_level2_eligibility(&reader, &metadata);

    let metadata_bytes = serde_json::to_vec_pretty(&metadata).map_err(|error| {
        ZkBenchError::serialization(REPRODUCTION_METADATA_PATH, error.to_string())
    })?;
    new_files.push(write_bytes_artifact(
        root,
        REPRODUCTION_METADATA_PATH,
        &metadata_bytes,
        BenchmarkPackFileRole::ReproductionMetadata,
    )?);

    let metadata_validation = validate_benchmark_pack_reproduction_metadata(&metadata);
    if !metadata_validation.valid {
        return Err(ZkBenchError::benchmark_pack(
            REPRODUCTION_METADATA_PATH,
            format!(
                "reproduction metadata validation failed: {:?}",
                metadata_validation.issues
            ),
        ));
    }

    let mut manifest = source_manifest;
    manifest.files.extend(new_files);
    manifest.reproduction_metadata_ref = Some(REPRODUCTION_METADATA_PATH.to_string());
    manifest.summary.external_replay_plan_count = metadata.attachments.len();
    manifest.summary.reproduction_metadata_count = 1;
    manifest.notes.push(
        "Reproduction metadata and inert external replay plans are Level0DesignNote attachments only."
            .to_string(),
    );
    write_updated_manifest(root, &manifest)?;

    Ok(metadata)
}

fn write_bytes_artifact(
    root: &Path,
    relative_path: &str,
    bytes: &[u8],
    role: BenchmarkPackFileRole,
) -> Result<BenchmarkPackFile> {
    validate_relative_path(relative_path)?;
    let path = root.join(relative_path);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|error| {
            ZkBenchError::benchmark_pack(parent.display().to_string(), error.to_string())
        })?;
    }
    fs::write(&path, bytes).map_err(|error| {
        ZkBenchError::benchmark_pack(path.display().to_string(), error.to_string())
    })?;
    Ok(BenchmarkPackFile {
        relative_path: relative_path.to_string(),
        role,
        digest: digest_for_bytes(bytes, role),
        required: true,
        notes: Vec::new(),
    })
}

fn write_updated_manifest(root: &Path, manifest: &BenchmarkPackManifest) -> Result<()> {
    let bytes = serde_json::to_vec_pretty(manifest).map_err(|error| {
        ZkBenchError::serialization("benchmark_pack.pack_json", error.to_string())
    })?;
    fs::write(root.join("pack.json"), &bytes).map_err(|error| {
        ZkBenchError::benchmark_pack(root.join("pack.json").display().to_string(), error.to_string())
    })
}

fn plan_id_from_path(relative_path: &str) -> String {
    Path::new(relative_path)
        .file_stem()
        .and_then(|stem| stem.to_str())
        .unwrap_or(relative_path)
        .to_string()
}
