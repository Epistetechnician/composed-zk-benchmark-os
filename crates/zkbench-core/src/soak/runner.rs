//! Local soak runner.

use std::fs;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::ClaimBoundary;
use crate::generator::{FamilyKind, GeneratorConfig, InstanceParams};
use crate::mutation::{
    apply_mutation_pass, BadCountersPass, CorruptedGuardsPass, MissingConstraintsPass, MutationPass,
};
use crate::pack::BenchmarkPackWriter;
use crate::replay::{
    build_local_replay_manifest_for_instance, build_local_replay_manifest_for_mutation,
    run_local_replay,
};

use super::config::{SoakConfig, SoakExecutionReportVersion, SoakFailure, SoakPackDescriptor};

/// Deterministic report emitted by a local soak run.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakExecutionReport {
    /// Report schema version.
    pub version: SoakExecutionReportVersion,
    /// Claim boundary for this soak metadata report.
    pub claim_boundary: ClaimBoundary,
    /// Soak configuration used.
    pub config: SoakConfig,
    /// Pack descriptors written by the soak run.
    pub pack_descriptors: Vec<SoakPackDescriptor>,
    /// Total packs written.
    pub total_packs_written: usize,
    /// Total replay results across all packs.
    pub total_replay_results: usize,
    /// Total failures encountered.
    pub total_failures: usize,
    /// Failure records.
    #[serde(default)]
    pub failures: Vec<SoakFailure>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Run a long local soak and write deterministic Level 1 benchmark packs.
pub fn run_local_soak(config: &SoakConfig, root: impl AsRef<Path>) -> Result<SoakExecutionReport> {
    validate_soak_config(config)?;
    let root = root.as_ref();
    fs::create_dir_all(root).map_err(|error| {
        ZkBenchError::benchmark_pack(root.display().to_string(), error.to_string())
    })?;

    let mut pack_descriptors = Vec::new();
    let mut failures = Vec::new();
    let mut total_replay_results = 0usize;

    for family_kind in &config.plan.family_kinds {
        if !family_kind.is_implemented() {
            return Err(ZkBenchError::generation(
                "soak.family_kind",
                format!("family kind {family_kind:?} is not implemented for local soak"),
            ));
        }
        for seed in &config.plan.seeds {
            match write_soak_pack(root, config, *family_kind, *seed) {
                Ok(descriptor) => {
                    total_replay_results =
                        total_replay_results.saturating_add(descriptor.replay_result_count);
                    pack_descriptors.push(descriptor);
                }
                Err(error) => failures.push(SoakFailure {
                    family_kind: *family_kind,
                    seed: *seed,
                    message: error.to_string(),
                }),
            }
        }
    }

    let report = SoakExecutionReport {
        version: SoakExecutionReportVersion::default(),
        claim_boundary: ClaimBoundary::Level0DesignNote,
        config: config.clone(),
        total_packs_written: pack_descriptors.len(),
        total_replay_results,
        total_failures: failures.len(),
        failures,
        pack_descriptors,
        notes: vec![
            "Local soak execution is not official benchmark evidence.".to_string(),
            "Soak packs remain Level1LocalReplay at most.".to_string(),
            "No external backend was invoked by this soak run.".to_string(),
        ],
    };

    write_soak_execution_report(root, &report)?;
    Ok(report)
}

fn write_soak_pack(
    root: &Path,
    config: &SoakConfig,
    family_kind: FamilyKind,
    seed: u64,
) -> Result<SoakPackDescriptor> {
    let generator_config = generator_config_for_family(family_kind, seed);
    let instance =
        crate::generator::generate_instance(generator_config, InstanceParams::default())?;

    let mut writer = BenchmarkPackWriter::new(pack_id_for(family_kind, seed))
        .include_score_report(config.include_score_report)
        .overwrite(true)
        .with_generated_instance(instance.clone());

    let instance_manifest = build_local_replay_manifest_for_instance(&instance)?;
    let instance_result = run_local_replay(&instance_manifest)?;
    writer = writer
        .with_replay_manifest(instance_manifest)
        .with_replay_result(instance_result);

    let mut mutation_passes_skipped = 0usize;
    if config.plan.apply_mutations {
        for pass in [
            &MissingConstraintsPass as &dyn MutationPass,
            &CorruptedGuardsPass,
            &BadCountersPass,
        ] {
            let Ok(mutation) = apply_mutation_pass(&instance, pass) else {
                mutation_passes_skipped += 1;
                continue;
            };
            let mutation_manifest = build_local_replay_manifest_for_mutation(&mutation)?;
            let mutation_result = run_local_replay(&mutation_manifest)?;
            writer = writer
                .with_mutated_instance(mutation)
                .with_replay_manifest(mutation_manifest)
                .with_replay_result(mutation_result);
        }
    }

    let pack_root = pack_root_for(root, config, family_kind, seed);
    if pack_root.exists() {
        fs::remove_dir_all(&pack_root).map_err(|error| {
            ZkBenchError::benchmark_pack(pack_root.display().to_string(), error.to_string())
        })?;
    }
    let manifest = writer.write_to(&pack_root)?;
    if manifest.claim_boundary > config.plan.claim_boundary_cap {
        return Err(ZkBenchError::benchmark_pack(
            manifest.id.clone(),
            format!(
                "pack claim boundary {:?} exceeds soak cap {:?}",
                manifest.claim_boundary, config.plan.claim_boundary_cap
            ),
        ));
    }

    Ok(SoakPackDescriptor {
        pack_id: manifest.id,
        family_kind,
        seed,
        pack_root_relative: relative_pack_path(config, family_kind, seed),
        replay_result_count: manifest.summary.replay_result_count,
        mutated_instance_count: manifest.summary.mutated_instance_count,
        mutation_passes_skipped,
    })
}

fn validate_soak_config(config: &SoakConfig) -> Result<()> {
    if config.plan.family_kinds.is_empty() {
        return Err(ZkBenchError::benchmark_pack(
            "soak.config",
            "soak plan must include at least one family kind",
        ));
    }
    if config.plan.seeds.is_empty() {
        return Err(ZkBenchError::benchmark_pack(
            "soak.config",
            "soak plan must include at least one seed",
        ));
    }
    if config.plan.claim_boundary_cap > ClaimBoundary::Level1LocalReplay {
        return Err(ZkBenchError::benchmark_pack(
            "soak.config",
            "soak claim boundary cap must not exceed Level1LocalReplay",
        ));
    }
    if config.packs_subdirectory.is_empty()
        || Path::new(&config.packs_subdirectory).is_absolute()
        || config.packs_subdirectory.contains("..")
    {
        return Err(ZkBenchError::benchmark_pack(
            "soak.config",
            "packs_subdirectory must be a non-empty relative path",
        ));
    }
    Ok(())
}

fn generator_config_for_family(family_kind: FamilyKind, seed: u64) -> GeneratorConfig {
    match family_kind {
        FamilyKind::BaselineFsm => GeneratorConfig::baseline_fsm().seed(seed),
        FamilyKind::BranchingFsm => GeneratorConfig::branching_fsm().seed(seed),
        FamilyKind::BoundedCounterLoop => GeneratorConfig::bounded_counter_loop()
            .seed(seed)
            .loop_bound(3),
        _ => GeneratorConfig::baseline_fsm().seed(seed),
    }
}

fn pack_id_for(family_kind: FamilyKind, seed: u64) -> String {
    format!("phase_l_soak_{}_seed_{seed}", family_kind.id_segment())
}

fn relative_pack_path(config: &SoakConfig, family_kind: FamilyKind, seed: u64) -> String {
    format!(
        "{}/{}/seed_{seed}",
        config.packs_subdirectory,
        family_kind.id_segment()
    )
}

fn pack_root_for(root: &Path, config: &SoakConfig, family_kind: FamilyKind, seed: u64) -> PathBuf {
    root.join(relative_pack_path(config, family_kind, seed))
}

fn write_soak_execution_report(root: &Path, report: &SoakExecutionReport) -> Result<()> {
    let bytes = serde_json::to_vec_pretty(report)
        .map_err(|error| ZkBenchError::serialization("soak.execution_report", error.to_string()))?;
    fs::write(root.join("soak_execution_report.json"), bytes).map_err(|error| {
        ZkBenchError::benchmark_pack(
            root.join("soak_execution_report.json")
                .display()
                .to_string(),
            error.to_string(),
        )
    })
}

/// Serialize a soak execution report to deterministic pretty JSON.
pub fn serialize_soak_execution_report_json(report: &SoakExecutionReport) -> Result<String> {
    serde_json::to_string_pretty(report)
        .map_err(|error| ZkBenchError::serialization("soak.execution_report", error.to_string()))
}

/// Deserialize a soak execution report from JSON.
pub fn deserialize_soak_execution_report_json(json: &str) -> Result<SoakExecutionReport> {
    serde_json::from_str(json)
        .map_err(|error| ZkBenchError::deserialization("soak.execution_report", error.to_string()))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::soak::SoakPlan;

    #[test]
    fn soak_plan_default_uses_implemented_families_only() {
        let plan = SoakPlan::default();
        assert!(plan
            .family_kinds
            .iter()
            .all(|family| family.is_implemented()));
        assert_eq!(plan.claim_boundary_cap, ClaimBoundary::Level1LocalReplay);
    }
}
