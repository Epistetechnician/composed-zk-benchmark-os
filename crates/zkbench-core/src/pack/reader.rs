//! Benchmark pack reader and local validator.

use std::fs;
use std::path::{Path, PathBuf};

use crate::error::{Result, ZkBenchError};
use crate::evidence::EvidenceLedger;
use crate::scoring::{validate_score_report, ScoreReport};

use super::manifest::{BenchmarkPackFileRole, BenchmarkPackManifest};
use super::validation::{BenchmarkPackValidation, BenchmarkPackValidationError};
use super::writer::{digest_for_bytes, validate_relative_path};

/// Reader for an on-disk local benchmark pack.
#[derive(Debug, Clone)]
pub struct BenchmarkPackReader {
    root: PathBuf,
    manifest: BenchmarkPackManifest,
}

impl BenchmarkPackReader {
    /// Read a benchmark pack manifest from a root directory.
    pub fn read(root: impl AsRef<Path>) -> Result<Self> {
        let root = root.as_ref().to_path_buf();
        let manifest_path = root.join("pack.json");
        let json = fs::read_to_string(&manifest_path).map_err(|error| {
            ZkBenchError::benchmark_pack(manifest_path.display().to_string(), error.to_string())
        })?;
        let manifest = serde_json::from_str(&json).map_err(|error| {
            ZkBenchError::deserialization("benchmark_pack.pack_json", error.to_string())
        })?;
        Ok(Self { root, manifest })
    }

    /// Return the pack root.
    pub fn root(&self) -> &Path {
        &self.root
    }

    /// Return the pack manifest.
    pub fn manifest(&self) -> &BenchmarkPackManifest {
        &self.manifest
    }

    /// Load the Evidence Ledger when present.
    pub fn load_evidence_ledger(&self) -> Result<Option<EvidenceLedger>> {
        let Some(file) = self
            .manifest
            .files
            .iter()
            .find(|file| file.role == BenchmarkPackFileRole::EvidenceLedger)
        else {
            return Ok(None);
        };
        validate_relative_path(&file.relative_path)?;
        let path = self.root.join(&file.relative_path);
        let json = fs::read_to_string(&path).map_err(|error| {
            ZkBenchError::evidence_ledger(path.display().to_string(), error.to_string())
        })?;
        let ledger = serde_json::from_str(&json).map_err(|error| {
            ZkBenchError::deserialization("benchmark_pack.evidence_ledger", error.to_string())
        })?;
        Ok(Some(ledger))
    }

    /// Load the Score Report when present.
    pub fn load_score_report(&self) -> Result<Option<ScoreReport>> {
        let Some(file) = self
            .manifest
            .files
            .iter()
            .find(|file| file.role == BenchmarkPackFileRole::ScoreReport)
        else {
            return Ok(None);
        };
        validate_relative_path(&file.relative_path)?;
        let path = self.root.join(&file.relative_path);
        let json = fs::read_to_string(&path).map_err(|error| {
            ZkBenchError::benchmark_pack(path.display().to_string(), error.to_string())
        })?;
        let report = serde_json::from_str(&json).map_err(|error| {
            ZkBenchError::deserialization("benchmark_pack.score_report", error.to_string())
        })?;
        Ok(Some(report))
    }

    /// Validate local pack file digests and ledger chain.
    pub fn validate(&self) -> BenchmarkPackValidation {
        let mut errors = Vec::new();

        if !self.manifest.uses_relative_paths_only() {
            errors.push(BenchmarkPackValidationError {
                path: "pack.json".to_string(),
                message: "manifest contains non-relative or parent-traversing paths".to_string(),
            });
        }

        for (index, note) in self.manifest.notes.iter().enumerate() {
            push_forbidden_claim_text_error(format!("pack.json#notes[{index}]"), note, &mut errors);
        }

        for file in &self.manifest.files {
            if let Err(error) = validate_relative_path(&file.relative_path) {
                errors.push(BenchmarkPackValidationError {
                    path: file.relative_path.clone(),
                    message: error.to_string(),
                });
                continue;
            }
            for (index, note) in file.notes.iter().enumerate() {
                push_forbidden_claim_text_error(
                    format!("{}#notes[{index}]", file.relative_path),
                    note,
                    &mut errors,
                );
            }
            let path = self.root.join(&file.relative_path);
            let bytes = match fs::read(&path) {
                Ok(bytes) => bytes,
                Err(error) => {
                    if file.required {
                        errors.push(BenchmarkPackValidationError {
                            path: file.relative_path.clone(),
                            message: error.to_string(),
                        });
                    }
                    continue;
                }
            };
            let digest = digest_for_bytes(&bytes, file.role);
            if digest != file.digest {
                errors.push(BenchmarkPackValidationError {
                    path: file.relative_path.clone(),
                    message: "file digest mismatch".to_string(),
                });
            }
        }
        push_summary_count_error(
            "pack.json#summary.generated_instance_count",
            self.manifest.summary.generated_instance_count,
            self.count_files_by_role(BenchmarkPackFileRole::GeneratedInstance),
            &mut errors,
        );
        push_summary_count_error(
            "pack.json#summary.mutated_instance_count",
            self.manifest.summary.mutated_instance_count,
            self.count_files_by_role(BenchmarkPackFileRole::MutatedInstance),
            &mut errors,
        );
        push_summary_count_error(
            "pack.json#summary.replay_manifest_count",
            self.manifest.summary.replay_manifest_count,
            self.count_files_by_role(BenchmarkPackFileRole::ReplayManifest),
            &mut errors,
        );
        push_summary_count_error(
            "pack.json#summary.replay_result_count",
            self.manifest.summary.replay_result_count,
            self.count_files_by_role(BenchmarkPackFileRole::ReplayResult),
            &mut errors,
        );
        push_summary_count_error(
            "pack.json#summary.score_report_count",
            self.manifest.summary.score_report_count,
            self.count_files_by_role(BenchmarkPackFileRole::ScoreReport),
            &mut errors,
        );
        if !self.manifest.summary.local_only {
            errors.push(BenchmarkPackValidationError {
                path: "pack.json#summary.local_only".to_string(),
                message: "benchmark pack summary must remain local-only".to_string(),
            });
        }

        match self.load_evidence_ledger() {
            Ok(Some(ledger)) => {
                let validation = ledger.validate();
                push_summary_count_error(
                    "pack.json#summary.evidence_record_count",
                    self.manifest.summary.evidence_record_count,
                    validation.summary.entry_count,
                    &mut errors,
                );
                for error in validation.errors {
                    errors.push(BenchmarkPackValidationError {
                        path: format!("evidence/ledger.json#{}", error.sequence_number),
                        message: error.message,
                    });
                }
            }
            Ok(None) => errors.push(BenchmarkPackValidationError {
                path: "evidence/ledger.json".to_string(),
                message: "required local evidence ledger is missing".to_string(),
            }),
            Err(error) => errors.push(BenchmarkPackValidationError {
                path: "evidence/ledger.json".to_string(),
                message: error.to_string(),
            }),
        }

        self.validate_score_report_files(&mut errors);

        if self.manifest.claim_boundary > crate::evidence::ClaimBoundary::Level1LocalReplay {
            errors.push(BenchmarkPackValidationError {
                path: "pack.json".to_string(),
                message: "pack manifest claim boundary exceeds Level1LocalReplay".to_string(),
            });
        }

        BenchmarkPackValidation::from_errors(errors, self.manifest.summary.clone())
    }

    fn count_files_by_role(&self, role: BenchmarkPackFileRole) -> usize {
        self.manifest
            .files
            .iter()
            .filter(|file| file.role == role)
            .count()
    }

    fn validate_score_report_files(&self, errors: &mut Vec<BenchmarkPackValidationError>) {
        for file in self
            .manifest
            .files
            .iter()
            .filter(|file| file.role == BenchmarkPackFileRole::ScoreReport)
        {
            if let Err(error) = validate_relative_path(&file.relative_path) {
                errors.push(BenchmarkPackValidationError {
                    path: file.relative_path.clone(),
                    message: error.to_string(),
                });
                continue;
            }
            let path = self.root.join(&file.relative_path);
            let json = match fs::read_to_string(&path) {
                Ok(json) => json,
                Err(error) => {
                    errors.push(BenchmarkPackValidationError {
                        path: file.relative_path.clone(),
                        message: error.to_string(),
                    });
                    continue;
                }
            };
            let report: ScoreReport = match serde_json::from_str(&json) {
                Ok(report) => report,
                Err(error) => {
                    errors.push(BenchmarkPackValidationError {
                        path: file.relative_path.clone(),
                        message: error.to_string(),
                    });
                    continue;
                }
            };
            let validation = validate_score_report(&report);
            for issue in validation.issues {
                errors.push(BenchmarkPackValidationError {
                    path: format!("{}#{}", file.relative_path, issue.path),
                    message: issue.message,
                });
            }
        }
    }
}

fn push_summary_count_error(
    path: &'static str,
    actual: usize,
    expected: usize,
    errors: &mut Vec<BenchmarkPackValidationError>,
) {
    if actual != expected {
        errors.push(BenchmarkPackValidationError {
            path: path.to_string(),
            message: format!("pack summary count {actual} does not match expected {expected}"),
        });
    }
}

fn push_forbidden_claim_text_error(
    path: String,
    text: &str,
    errors: &mut Vec<BenchmarkPackValidationError>,
) {
    if contains_forbidden_pack_claim_text(text) {
        errors.push(BenchmarkPackValidationError {
            path,
            message: "pack metadata contains forbidden claim language".to_string(),
        });
    }
}

fn contains_forbidden_pack_claim_text(text: &str) -> bool {
    let lowered = text.to_ascii_lowercase();
    if lowered.contains("not official benchmark evidence")
        || lowered.contains("not official benchmark result")
        || lowered.contains("no official benchmark evidence")
        || lowered.contains("no official benchmark result")
        || lowered.contains("does not create official benchmark evidence")
        || lowered.contains("does not create official benchmark result")
        || lowered.contains(
            "no external backend artifacts, proof-system results, or formal evidence are included",
        )
    {
        return false;
    }
    crate::external_runner::contains_forbidden_claim_text(text)
}
