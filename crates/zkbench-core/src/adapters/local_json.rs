//! Local JSON adapter.
//!
//! This is not a real ZK backend adapter. It serializes local replay inputs,
//! evaluates selected traces with the local oracle, and emits conservative
//! Level1LocalReplay evidence.

use serde::{Deserialize, Serialize};

use crate::dsl::{evaluate_trace, OracleOutcome, TraceSpec};
use crate::error::{Result, ZkBenchError};
use crate::evidence::{
    classify_result, compute_artifact_digest, ArtifactKind, ArtifactRole, BackendOutcome,
    ClaimBoundary, EvidenceClass, EvidenceRecord, ExpectedVerdict, ProvenanceRecord,
};
use crate::generator::BenchmarkInstance;
use crate::replay::{
    ReplayCommand, ReplayFailureMode, ReplayManifest, ReplayMode, ReplayProvenance, ReplayResult,
    ReplaySerializationVersion, ReplayStatus, ReplayTraceResult,
};

use super::{AdapterCapabilitySet, BackendAdapter, BackendTarget};

/// Local JSON adapter id.
pub const LOCAL_JSON_ADAPTER_ID: &str = "local_json_adapter_v0";

/// Local JSON adapter config.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalJsonAdapterConfig {
    /// Adapter id.
    pub adapter_id: String,
    /// Local target id.
    pub target_id: String,
    /// Default replay mode.
    pub default_replay_mode: ReplayMode,
}

impl Default for LocalJsonAdapterConfig {
    fn default() -> Self {
        Self {
            adapter_id: LOCAL_JSON_ADAPTER_ID.to_string(),
            target_id: "local_oracle".to_string(),
            default_replay_mode: ReplayMode::LocalOracle,
        }
    }
}

/// Local JSON adapter.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct LocalJsonAdapter {
    /// Adapter config.
    pub config: LocalJsonAdapterConfig,
}

/// Local replay input wrapper.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LocalJsonReplayInput {
    /// Replay manifest.
    pub manifest: ReplayManifest,
}

/// Local replay output wrapper.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalJsonReplayOutput {
    /// Replay result.
    pub replay_result: ReplayResult,
    /// Summary.
    pub summary: LocalJsonReplaySummary,
}

/// Local replay summary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct LocalJsonReplaySummary {
    /// Trace count.
    pub trace_count: usize,
    /// Accepted local traces.
    pub local_accepted_count: usize,
    /// Rejected local traces.
    pub local_rejected_count: usize,
    /// Capability gaps.
    pub capability_gap_count: usize,
    /// Inconclusive traces.
    pub inconclusive_count: usize,
    /// Evidence record count.
    pub evidence_record_count: usize,
}

/// Conservative local JSON adapter capabilities.
pub fn local_json_capabilities() -> AdapterCapabilitySet {
    AdapterCapabilitySet {
        supports_execution: true,
        supports_proving: false,
        supports_verification_timing: false,
        supports_negative_tests: true,
        supports_trace_export: true,
        supports_constraint_count: false,
        supports_formal_semantics: false,
        supports_machine_checked_proof: false,
        supports_recursion: false,
        supports_zkml_metrics: false,
        supports_replay_manifest: true,
        supports_artifact_hashing: true,
        supports_public_private_boundary_checks: false,
    }
}

impl LocalJsonAdapter {
    /// Replay a local manifest.
    pub fn replay(&self, manifest: &ReplayManifest) -> Result<ReplayResult> {
        if manifest.claim_boundary > ClaimBoundary::Level1LocalReplay {
            return Err(ZkBenchError::replay(
                "replay_manifest.claim_boundary",
                "local JSON adapter refuses actual evidence above Level1LocalReplay",
            ));
        }
        if manifest.adapter_id != self.config.adapter_id {
            return Err(ZkBenchError::replay(
                "replay_manifest.adapter_id",
                format!(
                    "manifest adapter id '{}' does not match '{}'",
                    manifest.adapter_id, self.config.adapter_id
                ),
            ));
        }

        let trace_inputs = self.trace_inputs(manifest)?;
        let mut trace_results = Vec::new();
        for (trace, expected_verdict) in trace_inputs {
            let (oracle_outcome, backend_outcome) = match manifest.replay_mode {
                ReplayMode::LocalOracle => {
                    let outcome = evaluate_trace(
                        subject_ir(manifest).ok_or_else(|| {
                            ZkBenchError::replay(
                                "replay_manifest.subject",
                                "replay subject is missing Semantic IR",
                            )
                        })?,
                        &trace,
                    )?;
                    let backend = backend_from_oracle(&outcome);
                    (outcome, backend)
                }
                ReplayMode::MockOutcome => {
                    let mock = mock_backend_outcome(manifest)?;
                    (
                        OracleOutcome::Inconclusive {
                            reason: "mock outcome mode does not run local oracle".to_string(),
                        },
                        mock,
                    )
                }
            };
            let result_classification = classify_result(expected_verdict, backend_outcome);
            let mut notes = vec![
                "Backend outcome is a local adapter representation, not proof-system acceptance."
                    .to_string(),
            ];
            if result_classification
                == crate::evidence::ResultClassification::ExpectedRejectAcceptedUnsoundCandidate
            {
                notes.push(
                    "Expected reject plus backend accepted is an unsound acceptance candidate, not a proven exploit."
                        .to_string(),
                );
            }
            trace_results.push(ReplayTraceResult {
                trace_id: trace.id,
                expected_verdict,
                local_oracle_outcome: oracle_outcome,
                backend_outcome,
                result_classification,
                notes,
            });
        }

        let evidence_records = trace_results
            .iter()
            .map(|trace_result| self.evidence_from_trace_result(manifest, trace_result))
            .collect::<Result<Vec<_>>>()?;
        let status = replay_status(&trace_results);
        let failure_mode = match status {
            ReplayStatus::MalformedManifest => ReplayFailureMode::MalformedManifest,
            ReplayStatus::AdapterError => ReplayFailureMode::AdapterError,
            ReplayStatus::Completed
            | ReplayStatus::CompletedWithRejectedTraces
            | ReplayStatus::CapabilityGap
            | ReplayStatus::Inconclusive => ReplayFailureMode::None,
        };
        let result_digest_input = (&manifest.id, &self.config.adapter_id, &trace_results);
        let result_digest = compute_artifact_digest(
            &result_digest_input,
            Some(ArtifactKind::ReplayResult),
            Some(ArtifactRole::Output),
        )?;
        Ok(ReplayResult {
            id: format!("result_{}", result_digest.hex_digest),
            manifest_id: manifest.id.clone(),
            adapter_id: self.config.adapter_id.clone(),
            replay_mode: manifest.replay_mode,
            status,
            failure_mode,
            trace_results,
            evidence_records,
            claim_boundary: ClaimBoundary::Level1LocalReplay,
            artifact_refs: manifest.input_artifacts.clone(),
            provenance: ReplayProvenance {
                replay_version: ReplaySerializationVersion::default(),
                adapter_id: self.config.adapter_id.clone(),
                logical_created_at: format!("phase-f-local-replay-v0:manifest:{}", manifest.id),
                notes: vec!["Local JSON adapter ran no external backend command.".to_string()],
            },
            notes: vec![
                "Local oracle replay only; local accepted is not proof-system accepted."
                    .to_string(),
                "Local replay is not official benchmark evidence.".to_string(),
            ],
        })
    }

    /// Replay and return summary.
    pub fn replay_with_summary(
        &self,
        input: LocalJsonReplayInput,
    ) -> Result<LocalJsonReplayOutput> {
        let replay_result = self.replay(&input.manifest)?;
        let summary = LocalJsonReplaySummary::from_result(&replay_result);
        Ok(LocalJsonReplayOutput {
            replay_result,
            summary,
        })
    }

    fn trace_inputs(&self, manifest: &ReplayManifest) -> Result<Vec<(TraceSpec, ExpectedVerdict)>> {
        match manifest.subject.kind {
            crate::replay::ReplaySubjectKind::GeneratedInstance => {
                let instance = manifest
                    .subject
                    .generated_instance
                    .as_ref()
                    .ok_or_else(|| {
                        ZkBenchError::replay(
                            "replay_manifest.subject.generated_instance",
                            "generated instance payload is missing",
                        )
                    })?;
                manifest
                    .selected_traces
                    .iter()
                    .map(|selection| {
                        let trace = instance
                            .accepted_traces
                            .iter()
                            .chain(instance.rejected_traces.iter())
                            .find(|trace| trace.id == selection.trace_id)
                            .cloned()
                            .ok_or_else(|| {
                                ZkBenchError::replay(
                                    "replay_manifest.selected_traces",
                                    format!("trace '{}' was not found", selection.trace_id),
                                )
                            })?;
                        Ok((trace, selection.expected_verdict))
                    })
                    .collect()
            }
            crate::replay::ReplaySubjectKind::MutatedInstance => {
                let mutation = manifest.subject.mutated_instance.as_ref().ok_or_else(|| {
                    ZkBenchError::replay(
                        "replay_manifest.subject.mutated_instance",
                        "mutated instance payload is missing",
                    )
                })?;
                manifest
                    .selected_traces
                    .iter()
                    .map(|selection| {
                        if selection.trace_id != mutation.primary_trace.id {
                            return Err(ZkBenchError::replay(
                                "replay_manifest.selected_traces",
                                format!(
                                    "trace '{}' is not available in mutated instance '{}'",
                                    selection.trace_id, mutation.id
                                ),
                            ));
                        }
                        Ok((mutation.primary_trace.clone(), selection.expected_verdict))
                    })
                    .collect()
            }
        }
    }

    fn evidence_from_trace_result(
        &self,
        manifest: &ReplayManifest,
        trace_result: &ReplayTraceResult,
    ) -> Result<EvidenceRecord> {
        Ok(EvidenceRecord {
            evidence_class: EvidenceClass::LocalReplay,
            claim_boundary: ClaimBoundary::Level1LocalReplay,
            provenance: ProvenanceRecord {
                source: format!("{}:{}", self.config.adapter_id, manifest.id),
                captured_at: Some(ReplaySerializationVersion::default().value),
                command: None,
                notes: vec![
                    "Local oracle replay; no external backend command was run.".to_string(),
                    format!("trace_id={}", trace_result.trace_id),
                ],
            },
            artifact_digest: Some(compute_artifact_digest(
                trace_result,
                Some(ArtifactKind::ReplayResult),
                Some(ArtifactRole::Evidence),
            )?),
            notes: vec![
                "Local semantic replay evidence only.".to_string(),
                "Local replay is not official benchmark evidence.".to_string(),
            ],
            backend_target: Some(self.target()),
        })
    }
}

impl LocalJsonReplaySummary {
    /// Build a local replay summary from a ReplayResult.
    pub fn from_result(result: &ReplayResult) -> Self {
        let mut summary = Self {
            trace_count: result.trace_results.len(),
            evidence_record_count: result.evidence_records.len(),
            ..Self::default()
        };
        for trace_result in &result.trace_results {
            match trace_result.local_oracle_outcome {
                OracleOutcome::Accepted => summary.local_accepted_count += 1,
                OracleOutcome::Rejected { .. } => summary.local_rejected_count += 1,
                OracleOutcome::CapabilityGap { .. } => summary.capability_gap_count += 1,
                OracleOutcome::Inconclusive { .. } => summary.inconclusive_count += 1,
            }
        }
        summary
    }
}

impl BackendAdapter for LocalJsonAdapter {
    fn target(&self) -> BackendTarget {
        BackendTarget {
            id: self.config.target_id.clone(),
            kind: "local_json".to_string(),
            version: Some("phase-f-local-replay-v0".to_string()),
            capabilities: local_json_capabilities(),
        }
    }

    fn prepare_replay(
        &self,
        _ir: &crate::dsl::SemanticIr,
        instance: &BenchmarkInstance,
    ) -> Result<ReplayManifest> {
        Ok(ReplayManifest {
            id: format!("manifest_{}_legacy_local_oracle", instance.id),
            schema_version: ReplaySerializationVersion::default(),
            replay_mode: self.config.default_replay_mode,
            subject: crate::replay::ReplaySubject {
                kind: crate::replay::ReplaySubjectKind::GeneratedInstance,
                generated_instance_id: Some(instance.id.clone()),
                mutated_instance_id: None,
                generated_instance: None,
                mutated_instance: None,
            },
            family_kind: None,
            generation_provenance: None,
            mutation_provenance: None,
            selected_traces: instance
                .trace_ids
                .iter()
                .map(|trace_id| crate::replay::ReplayTraceSelection {
                    trace_id: trace_id.clone(),
                    expected_verdict: instance.expected_verdict,
                })
                .collect(),
            expected_outcomes: instance
                .trace_ids
                .iter()
                .map(|trace_id| crate::replay::ReplayExpectedOutcome {
                    trace_id: trace_id.clone(),
                    expected_verdict: instance.expected_verdict,
                })
                .collect(),
            local_target_id: self.config.target_id.clone(),
            adapter_id: self.config.adapter_id.clone(),
            adapter_capabilities: local_json_capabilities(),
            claim_boundary: ClaimBoundary::Level1LocalReplay,
            input_artifacts: Vec::new(),
            expected_output_artifact_roles: vec![ArtifactRole::Output, ArtifactRole::Evidence],
            commands: vec![ReplayCommand::LocalOracleEvaluation],
            notes: vec![
                "Legacy BenchmarkInstance manifest lacks embedded subject payload; use generated instance builders for replay.".to_string(),
            ],
        })
    }

    fn normalize_result(&self, result: &ReplayResult) -> Result<EvidenceRecord> {
        result.evidence_records.first().cloned().ok_or_else(|| {
            ZkBenchError::replay(
                "local_json_adapter.normalize_result",
                "replay result did not contain evidence records",
            )
        })
    }
}

fn subject_ir(manifest: &ReplayManifest) -> Option<&crate::dsl::SemanticIr> {
    match manifest.subject.kind {
        crate::replay::ReplaySubjectKind::GeneratedInstance => manifest
            .subject
            .generated_instance
            .as_ref()
            .map(|instance| &instance.semantic_ir),
        crate::replay::ReplaySubjectKind::MutatedInstance => manifest
            .subject
            .mutated_instance
            .as_ref()
            .map(|mutation| &mutation.semantic_ir),
    }
}

fn backend_from_oracle(outcome: &OracleOutcome) -> BackendOutcome {
    match outcome {
        OracleOutcome::Accepted => BackendOutcome::Accepted,
        OracleOutcome::Rejected { .. } => BackendOutcome::Rejected,
        OracleOutcome::CapabilityGap { .. } => BackendOutcome::CapabilityGap,
        OracleOutcome::Inconclusive { .. } => BackendOutcome::Inconclusive,
    }
}

fn mock_backend_outcome(manifest: &ReplayManifest) -> Result<BackendOutcome> {
    manifest
        .commands
        .iter()
        .find_map(|command| match command {
            ReplayCommand::MockOutcomeEvaluation { outcome } => Some(*outcome),
            ReplayCommand::LocalOracleEvaluation => None,
        })
        .ok_or_else(|| {
            ZkBenchError::replay(
                "replay_manifest.commands",
                "MockOutcome replay mode requires MockOutcomeEvaluation command",
            )
        })
}

fn replay_status(trace_results: &[ReplayTraceResult]) -> ReplayStatus {
    if trace_results
        .iter()
        .any(|result| matches!(result.backend_outcome, BackendOutcome::CapabilityGap))
    {
        ReplayStatus::CapabilityGap
    } else if trace_results
        .iter()
        .any(|result| matches!(result.backend_outcome, BackendOutcome::Inconclusive))
    {
        ReplayStatus::Inconclusive
    } else if trace_results
        .iter()
        .any(|result| matches!(result.backend_outcome, BackendOutcome::Rejected))
    {
        ReplayStatus::CompletedWithRejectedTraces
    } else {
        ReplayStatus::Completed
    }
}
