//! Benchmark pack writer.

use std::fs;
use std::path::{Path, PathBuf};

use serde::Serialize;

use crate::error::{Result, ZkBenchError};
use crate::evidence::{compute_artifact_digest_bytes, ArtifactDigest, EvidenceLedger};
use crate::generator::GeneratedBenchmarkInstance;
use crate::mutation::MutatedBenchmarkInstance;
use crate::replay::{ReplayManifest, ReplayResult};
use crate::scoring::{score_report_from_evidence, validate_score_report, ScoreReport};

use super::manifest::{
    BenchmarkPackFile, BenchmarkPackFileRole, BenchmarkPackManifest, BenchmarkPackSummary,
    BenchmarkPackVersion,
};

/// Writer for local benchmark packs.
#[derive(Debug, Clone)]
pub struct BenchmarkPackWriter {
    pack_id: String,
    generated_instances: Vec<GeneratedBenchmarkInstance>,
    mutated_instances: Vec<MutatedBenchmarkInstance>,
    replay_manifests: Vec<ReplayManifest>,
    replay_results: Vec<ReplayResult>,
    evidence_ledger: Option<EvidenceLedger>,
    score_report: Option<ScoreReport>,
    include_score_report: bool,
    overwrite: bool,
}

impl BenchmarkPackWriter {
    /// Create a new local benchmark pack writer.
    pub fn new(pack_id: impl Into<String>) -> Self {
        Self {
            pack_id: pack_id.into(),
            generated_instances: Vec::new(),
            mutated_instances: Vec::new(),
            replay_manifests: Vec::new(),
            replay_results: Vec::new(),
            evidence_ledger: None,
            score_report: None,
            include_score_report: true,
            overwrite: false,
        }
    }

    /// Add a generated Benchmark Instance.
    pub fn with_generated_instance(mut self, instance: GeneratedBenchmarkInstance) -> Self {
        self.generated_instances.push(instance);
        self
    }

    /// Add a mutated Benchmark Instance.
    pub fn with_mutated_instance(mut self, instance: MutatedBenchmarkInstance) -> Self {
        self.mutated_instances.push(instance);
        self
    }

    /// Add a Replay Manifest.
    pub fn with_replay_manifest(mut self, manifest: ReplayManifest) -> Self {
        self.replay_manifests.push(manifest);
        self
    }

    /// Add a Replay Result.
    pub fn with_replay_result(mut self, result: ReplayResult) -> Self {
        self.replay_results.push(result);
        self
    }

    /// Add an Evidence Ledger.
    pub fn with_evidence_ledger(mut self, ledger: EvidenceLedger) -> Self {
        self.evidence_ledger = Some(ledger);
        self
    }

    /// Add a conservative Score Report.
    pub fn with_score_report(mut self, report: ScoreReport) -> Self {
        self.score_report = Some(report);
        self
    }

    /// Configure whether to write a conservative Score Report.
    pub fn include_score_report(mut self, include: bool) -> Self {
        self.include_score_report = include;
        self
    }

    /// Configure whether writing may overwrite a non-empty pack directory.
    pub fn overwrite(mut self, overwrite: bool) -> Self {
        self.overwrite = overwrite;
        self
    }

    /// Write a local pack into the supplied directory.
    pub fn write_to(&self, root: impl AsRef<Path>) -> Result<BenchmarkPackManifest> {
        let root = root.as_ref();
        if root.exists() && !root.is_dir() {
            return Err(ZkBenchError::benchmark_pack(
                root.display().to_string(),
                "pack root exists and is not a directory",
            ));
        }
        if root.exists() && !self.overwrite && directory_has_entries(root)? {
            return Err(ZkBenchError::benchmark_pack(
                root.display().to_string(),
                "pack root is non-empty; set overwrite(true) to replace local pack files",
            ));
        }
        fs::create_dir_all(root).map_err(|error| {
            ZkBenchError::benchmark_pack(root.display().to_string(), error.to_string())
        })?;

        let mut files = Vec::new();
        files.push(write_readme(root, &self.pack_id)?);

        for (index, instance) in self.generated_instances.iter().enumerate() {
            let relative_path = if index == 0 {
                "specs/generated_instance.json".to_string()
            } else {
                format!("specs/generated_instances/{}.json", instance.id)
            };
            files.push(write_json_artifact(
                root,
                &relative_path,
                instance,
                BenchmarkPackFileRole::GeneratedInstance,
            )?);
        }

        for instance in &self.mutated_instances {
            let relative_path = format!("specs/mutated_instances/{}.json", instance.id);
            files.push(write_json_artifact(
                root,
                &relative_path,
                instance,
                BenchmarkPackFileRole::MutatedInstance,
            )?);
        }

        for manifest in &self.replay_manifests {
            let relative_path = format!("replay/manifests/{}.json", manifest.id);
            files.push(write_json_artifact(
                root,
                &relative_path,
                manifest,
                BenchmarkPackFileRole::ReplayManifest,
            )?);
        }

        for result in &self.replay_results {
            let relative_path = format!("replay/results/{}.json", result.id);
            files.push(write_json_artifact(
                root,
                &relative_path,
                result,
                BenchmarkPackFileRole::ReplayResult,
            )?);
        }

        let ledger = self.resolved_ledger()?;
        files.push(write_json_artifact(
            root,
            "evidence/ledger.json",
            &ledger,
            BenchmarkPackFileRole::EvidenceLedger,
        )?);

        let score_report_count = if self.include_score_report {
            let report = self.resolved_score_report(&ledger)?;
            files.push(write_json_artifact(
                root,
                "reports/score_report.json",
                &report,
                BenchmarkPackFileRole::ScoreReport,
            )?);
            1
        } else {
            0
        };

        let manifest = BenchmarkPackManifest {
            id: self.pack_id.clone(),
            version: BenchmarkPackVersion::default(),
            claim_boundary: crate::evidence::ClaimBoundary::Level1LocalReplay,
            local_generator_version: self
                .generated_instances
                .first()
                .map(|instance| instance.generation_provenance.generator_version.clone()),
            local_adapter_version: self
                .replay_results
                .first()
                .map(|result| result.provenance.replay_version.value.clone()),
            generated_instance_ids: self
                .generated_instances
                .iter()
                .map(|instance| instance.id.clone())
                .collect(),
            mutation_ids: self
                .mutated_instances
                .iter()
                .map(|instance| instance.id.clone())
                .collect(),
            replay_manifest_ids: self
                .replay_manifests
                .iter()
                .map(|manifest| manifest.id.clone())
                .collect(),
            replay_result_ids: self
                .replay_results
                .iter()
                .map(|result| result.id.clone())
                .collect(),
            evidence_ledger_ref: Some("evidence/ledger.json".to_string()),
            files,
            summary: BenchmarkPackSummary {
                generated_instance_count: self.generated_instances.len(),
                mutated_instance_count: self.mutated_instances.len(),
                replay_manifest_count: self.replay_manifests.len(),
                replay_result_count: self.replay_results.len(),
                evidence_record_count: ledger.summary.entry_count,
                score_report_count,
                local_only: true,
            },
            notes: vec![
                "Local benchmark pack only; local replay is not official benchmark evidence."
                    .to_string(),
                "No external backend artifacts, proof-system results, or formal evidence are included."
                    .to_string(),
                "pack.json excludes its own digest to avoid circular artifact hashing.".to_string(),
            ],
        };
        write_pack_manifest(root, &manifest)?;
        Ok(manifest)
    }

    fn resolved_ledger(&self) -> Result<EvidenceLedger> {
        if let Some(ledger) = &self.evidence_ledger {
            return Ok(ledger.clone());
        }
        let mut ledger = EvidenceLedger::new();
        for result in &self.replay_results {
            ledger.append_replay_result(result)?;
        }
        Ok(ledger)
    }

    fn resolved_score_report(&self, ledger: &EvidenceLedger) -> Result<ScoreReport> {
        let report = self.score_report.clone().unwrap_or_else(|| {
            let records = ledger
                .entries
                .iter()
                .map(|entry| entry.evidence_record.clone())
                .collect::<Vec<_>>();
            score_report_from_evidence(&records)
        });
        let validation = validate_score_report(&report);
        if !validation.valid {
            return Err(ZkBenchError::benchmark_pack(
                "reports/score_report.json",
                format!("score report validation failed: {:?}", validation.issues),
            ));
        }
        Ok(report)
    }
}

fn write_readme(root: &Path, pack_id: &str) -> Result<BenchmarkPackFile> {
    let readme = format!(
        "# {pack_id}\n\n\
         This pack contains local replay artifacts only.\n\n\
         This is a local Benchmark Pack skeleton for Composed ZK Benchmark OS.\n\n\
         Claim boundary:\n\n\
         - local replay is not official benchmark evidence\n\
         - a benchmark pass is not proof\n\
         - recursion proof is not semantic proof\n\
         - no external backend was invoked by this pack\n\
         - claim boundary is Level1LocalReplay or lower\n\
         - no benchmark performance result is included\n\
         - no formal evidence is included\n"
    );
    write_bytes_artifact(
        root,
        "README.md",
        readme.as_bytes(),
        BenchmarkPackFileRole::Readme,
    )
}

fn write_pack_manifest(root: &Path, manifest: &BenchmarkPackManifest) -> Result<()> {
    let bytes = serde_json::to_vec_pretty(manifest).map_err(|error| {
        ZkBenchError::serialization("benchmark_pack.pack_json", error.to_string())
    })?;
    write_bytes(root.join("pack.json"), &bytes)
}

fn write_json_artifact<T: Serialize>(
    root: &Path,
    relative_path: &str,
    value: &T,
    role: BenchmarkPackFileRole,
) -> Result<BenchmarkPackFile> {
    let bytes = serde_json::to_vec_pretty(value).map_err(|error| {
        ZkBenchError::serialization(format!("benchmark_pack.{relative_path}"), error.to_string())
    })?;
    write_bytes_artifact(root, relative_path, &bytes, role)
}

fn write_bytes_artifact(
    root: &Path,
    relative_path: &str,
    bytes: &[u8],
    role: BenchmarkPackFileRole,
) -> Result<BenchmarkPackFile> {
    validate_relative_path(relative_path)?;
    write_bytes(root.join(relative_path), bytes)?;
    let digest = digest_for_bytes(bytes, role);
    Ok(BenchmarkPackFile {
        relative_path: relative_path.to_string(),
        role,
        digest,
        required: true,
        notes: Vec::new(),
    })
}

pub(crate) fn digest_for_bytes(bytes: &[u8], role: BenchmarkPackFileRole) -> ArtifactDigest {
    compute_artifact_digest_bytes(
        bytes,
        Some(role.artifact_kind()),
        Some(role.artifact_role()),
    )
}

pub(crate) fn validate_relative_path(relative_path: &str) -> Result<()> {
    let path = Path::new(relative_path);
    if relative_path.is_empty()
        || path.is_absolute()
        || relative_path.contains("..")
        || relative_path.contains('\\')
    {
        return Err(ZkBenchError::benchmark_pack(
            "benchmark_pack.relative_path",
            format!("invalid pack relative path {relative_path:?}"),
        ));
    }
    Ok(())
}

fn write_bytes(path: PathBuf, bytes: &[u8]) -> Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|error| {
            ZkBenchError::benchmark_pack(parent.display().to_string(), error.to_string())
        })?;
    }
    fs::write(&path, bytes).map_err(|error| {
        ZkBenchError::benchmark_pack(path.display().to_string(), error.to_string())
    })
}

fn directory_has_entries(path: &Path) -> Result<bool> {
    let mut entries = fs::read_dir(path).map_err(|error| {
        ZkBenchError::benchmark_pack(path.display().to_string(), error.to_string())
    })?;
    entries
        .next()
        .transpose()
        .map(|entry| entry.is_some())
        .map_err(|error| {
            ZkBenchError::benchmark_pack(path.display().to_string(), error.to_string())
        })
}
