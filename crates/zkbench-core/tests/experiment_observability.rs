// State slices:
// - `benchmark-os-experiment-unit-adaptive-observability-v1`
// - `benchmark-os-experiment-contract-composition-v1`
// - `benchmark-os-observability-integrity-hardening-v1`
// - `benchmark-os-observability-payload-readback-v1`
// - `benchmark-os-observability-artifact-identity-v1`
// - `benchmark-os-observability-ledger-transport-v1`
// - `benchmark-os-observability-bundle-assembly-v1`
// - `benchmark-os-observability-slot-access-v1`
// - `benchmark-os-observability-module-manifest-v1`
// - `benchmark-os-canonical-artifact-projection-v1`
// - `benchmark-os-local-json-projection-binding-access-v1`
// - `benchmark-os-local-inner-artifact-access-v1`
// - `benchmark-os-local-json-projection-single-source-access-v1`
// - `benchmark-os-composition-config-transport-v1`
// - `benchmark-os-composition-transport-readback-v1`
// - `benchmark-os-experiment-plugin-factory-catalog-v1`
// - `benchmark-os-plugin-registry-descriptor-only-separation-v1`
// - `benchmark-os-observability-run-lifecycle-transaction-v1`
// - `benchmark-os-observability-composition-adapter-durable-attribution-v1`
// - `benchmark-os-local-json-composition-output-handoff-validation-v1`
// - `benchmark-os-observability-scheduler-budget-transition-v1`

use zkbench_core::evidence::{
    compute_artifact_digest, compute_artifact_digest_bytes, ArtifactKind, ArtifactRole,
    ClaimBoundary,
};
use zkbench_core::experiment_observability::{
    compute_experiment_artifact_bundle_digest, compute_local_json_composition_config_digest,
    deserialize_experiment_artifact_bundle_json, deserialize_experiment_report_json,
    deserialize_local_json_composition_config_json, deserialize_mechanism_ledger_json,
    deserialize_meta_evaluation_ledger_json, serialize_experiment_artifact_bundle_json,
    serialize_local_json_composition_config_json, serialize_mechanism_ledger_json,
    serialize_meta_evaluation_ledger_json, upgrade_experiment_artifact_bundle_v1_json,
    validate_experiment_artifact_bundle, validate_experiment_report_artifact,
    validate_local_json_artifact_projection, validate_module_manifest,
    validate_serialized_local_json_composition,
    validate_serialized_local_json_composition_transport, ComposedExperimentRunner,
    DownstreamPredictiveness, EvaluationRecord, Evaluator, ExperimentArtifactBundle,
    ExperimentArtifactKind, ExperimentArtifactRef, ExperimentProvenance, ExperimentRunReport,
    ExperimentRunSpec, LocalJsonExperimentRunner, MechanismCollector, MechanismLedger,
    MechanismRecord, MechanismRecordStatus, MetaEvaluationLedger, MetricMetaEvaluation,
    MetricMetaEvaluationBasis, MetricNoise, MetricObservation, MetricObservationStatus,
    MetricStability, ModuleDescriptor, ObservabilityBudget, ObservabilityDecision,
    ObservabilitySignals, ObservabilityTier, WeightedObservabilityScheduler,
    EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION, OBSERVABILITY_SCORE_SCALE,
};
use zkbench_core::experiment_observability::{
    create_experiment_artifact_ref, EvaluationContext, ExperimentOutcome, ExperimentRunner,
    MechanismCollectionContext, Metric, MetricContext, ObservabilityScheduler, ResponseContext,
    ResponseOutput, ResponseProducer, Task, TaskContext, TaskOutput,
    ValidatedLocalJsonCompositionOutput,
};
use zkbench_core::{
    ExperimentBundle, ExperimentPlugin, ExperimentPluginDescriptor, ExperimentPluginFactoryCatalog,
};

fn provenance(activity: &str) -> ExperimentProvenance {
    ExperimentProvenance {
        who: "test-agent".to_string(),
        what: activity.to_string(),
        when: "logical-test-time-1".to_string(),
        version: "test-implementation-v1".to_string(),
        source_revision: "local-test-revision".to_string(),
    }
}

fn artifact(kind: ExperimentArtifactKind, uri: &str) -> ExperimentArtifactRef {
    ExperimentArtifactRef {
        uri: uri.to_string(),
        kind,
        experiment_id: "experiment-1".to_string(),
        run_id: "run-1".to_string(),
        digest: compute_artifact_digest_bytes(
            uri.as_bytes(),
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Manifest),
        ),
        provenance: provenance("artifact-capture"),
    }
}

fn bundle() -> ExperimentArtifactBundle {
    ExperimentArtifactBundle {
        bundle_id: "bundle-1".to_string(),
        experiment_id: "experiment-1".to_string(),
        run_id: "run-1".to_string(),
        schema_version: EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION.to_string(),
        config: artifact(ExperimentArtifactKind::Config, "config.json"),
        task: artifact(ExperimentArtifactKind::Task, "task.json"),
        prompt: artifact(ExperimentArtifactKind::Prompt, "prompt.json"),
        response: artifact(ExperimentArtifactKind::Response, "response.json"),
        evaluation: artifact(ExperimentArtifactKind::Evaluation, "evaluation.json"),
        mechanism_record: artifact(
            ExperimentArtifactKind::MechanismRecord,
            "mechanism-record.json",
        ),
        metadata: artifact(ExperimentArtifactKind::Metadata, "metadata.json"),
        logs: artifact(ExperimentArtifactKind::Logs, "logs.json"),
        report: artifact(ExperimentArtifactKind::Report, "report.json"),
        claim_boundary: ClaimBoundary::Level0DesignNote,
    }
}

fn legacy_v1_bundle_json(bundle: &ExperimentArtifactBundle) -> String {
    #[derive(serde::Serialize)]
    struct LegacyRef<'a> {
        uri: &'a str,
        kind: ExperimentArtifactKind,
        digest: &'a zkbench_core::evidence::ArtifactDigest,
        provenance: &'a ExperimentProvenance,
    }

    #[derive(serde::Serialize)]
    struct LegacyBundle<'a> {
        bundle_id: &'a str,
        experiment_id: &'a str,
        run_id: &'a str,
        schema_version: &'static str,
        config: LegacyRef<'a>,
        task: LegacyRef<'a>,
        prompt: LegacyRef<'a>,
        response: LegacyRef<'a>,
        evaluation: LegacyRef<'a>,
        mechanism_record: LegacyRef<'a>,
        metadata: LegacyRef<'a>,
        logs: LegacyRef<'a>,
        report: LegacyRef<'a>,
        claim_boundary: ClaimBoundary,
    }

    fn reference(artifact: &ExperimentArtifactRef) -> LegacyRef<'_> {
        LegacyRef {
            uri: &artifact.uri,
            kind: artifact.kind,
            digest: &artifact.digest,
            provenance: &artifact.provenance,
        }
    }

    serde_json::to_string(&LegacyBundle {
        bundle_id: &bundle.bundle_id,
        experiment_id: &bundle.experiment_id,
        run_id: &bundle.run_id,
        schema_version: "experiment-unit-artifact-bundle-v1",
        config: reference(&bundle.config),
        task: reference(&bundle.task),
        prompt: reference(&bundle.prompt),
        response: reference(&bundle.response),
        evaluation: reference(&bundle.evaluation),
        mechanism_record: reference(&bundle.mechanism_record),
        metadata: reference(&bundle.metadata),
        logs: reference(&bundle.logs),
        report: reference(&bundle.report),
        claim_boundary: bundle.claim_boundary,
    })
    .expect("legacy v1 fixture should serialize")
}

fn module(id: &str) -> ModuleDescriptor {
    ModuleDescriptor {
        module_id: id.to_string(),
        implementation_id: format!("{id}.reference"),
        version: "v1".to_string(),
        source_revision: "local-test-revision".to_string(),
    }
}

#[test]
fn module_manifest_rejects_empty_and_duplicate_logical_ids() {
    assert!(validate_module_manifest(&[], "test.modules").is_err());

    let first = module("task");
    let duplicate = module("task");
    let error = validate_module_manifest(&[first, duplicate], "test.modules")
        .expect_err("duplicate logical module ids must fail closed");
    assert!(error
        .to_string()
        .contains("logical module id is duplicated"));

    let mut blank = module("valid");
    blank.module_id.clear();
    let error = validate_module_manifest(&[blank], "test.modules")
        .expect_err("blank module ids must fail closed");
    assert!(error.to_string().contains("test.modules[0].module_id"));
}

struct AlternatePluginAdapter {
    descriptor: ExperimentPluginDescriptor,
    bundle: ExperimentBundle,
}

impl ExperimentPlugin for AlternatePluginAdapter {
    fn descriptor(&self) -> &ExperimentPluginDescriptor {
        &self.descriptor
    }

    fn run(&self) -> zkbench_core::error::Result<ExperimentBundle> {
        Ok(self.bundle.clone())
    }
}

fn decision(
    tier: ObservabilityTier,
) -> zkbench_core::experiment_observability::ObservabilityDecision {
    zkbench_core::experiment_observability::ObservabilityDecision {
        tier,
        priority_milli: 0,
        signals: ObservabilitySignals {
            novelty_milli: 0,
            uncertainty_milli: 0,
            failure_milli: 0,
        },
        reasons: Vec::new(),
    }
}

struct FixtureTask {
    descriptor: ModuleDescriptor,
}

impl Task for FixtureTask {
    fn descriptor(&self) -> &ModuleDescriptor {
        &self.descriptor
    }

    fn materialize(&self, context: &TaskContext) -> zkbench_core::error::Result<TaskOutput> {
        Ok(TaskOutput {
            task_artifact: create_experiment_artifact_ref(
                "run/task.json",
                ExperimentArtifactKind::Task,
                &context.task_id,
                &context.experiment_id,
                &context.run_id,
                context.provenance.clone(),
            )?,
            prompt_artifact: create_experiment_artifact_ref(
                "run/prompt.json",
                ExperimentArtifactKind::Prompt,
                &context.input_digest,
                &context.experiment_id,
                &context.run_id,
                context.provenance.clone(),
            )?,
        })
    }
}

struct FixtureResponseProducer {
    descriptor: ModuleDescriptor,
}

impl ResponseProducer for FixtureResponseProducer {
    fn descriptor(&self) -> &ModuleDescriptor {
        &self.descriptor
    }

    fn produce(&self, context: ResponseContext<'_>) -> zkbench_core::error::Result<ResponseOutput> {
        Ok(ResponseOutput {
            response_artifact: create_experiment_artifact_ref(
                "run/response.json",
                ExperimentArtifactKind::Response,
                &context.prompt.digest,
                context.experiment_id,
                context.run_id,
                context.provenance.clone(),
            )?,
        })
    }
}

struct FixtureMetric {
    descriptor: ModuleDescriptor,
}

impl Metric for FixtureMetric {
    fn descriptor(&self) -> &ModuleDescriptor {
        &self.descriptor
    }

    fn measure(
        &self,
        context: MetricContext<'_>,
    ) -> zkbench_core::error::Result<MetricObservation> {
        Ok(MetricObservation {
            metric: self.descriptor.clone(),
            status: MetricObservationStatus::Measured,
            value: Some(
                (context.response.digest.hex_digest.len() + context.task.digest.hex_digest.len())
                    as i64,
            ),
            provenance: provenance("fixture-metric"),
        })
    }
}

struct FixtureEvaluator {
    descriptor: ModuleDescriptor,
}

impl Evaluator for FixtureEvaluator {
    fn descriptor(&self) -> &ModuleDescriptor {
        &self.descriptor
    }

    fn evaluate(
        &self,
        context: EvaluationContext<'_>,
    ) -> zkbench_core::error::Result<EvaluationRecord> {
        Ok(EvaluationRecord {
            evaluator: self.descriptor.clone(),
            status: "negative_result".to_string(),
            outcome: ExperimentOutcome::Negative,
            metrics: context.metrics.to_vec(),
            provenance: provenance("fixture-evaluator"),
        })
    }
}

struct FixtureMechanismCollector {
    descriptor: ModuleDescriptor,
    fail: bool,
}

impl MechanismCollector for FixtureMechanismCollector {
    fn descriptor(&self) -> &ModuleDescriptor {
        &self.descriptor
    }

    fn collect(
        &self,
        context: MechanismCollectionContext<'_>,
    ) -> zkbench_core::error::Result<MechanismRecord> {
        if self.fail {
            return Err(zkbench_core::error::ZkBenchError::validation(
                "fixture.mechanism_collector",
                "fixture collector failure after scheduler allocation",
            ));
        }
        let (status, collector) = match context.decision.tier {
            ObservabilityTier::Tier0 => (MechanismRecordStatus::MetadataOnly, None),
            ObservabilityTier::Tier1 => (
                MechanismRecordStatus::Sampled,
                Some(self.descriptor.clone()),
            ),
            ObservabilityTier::Tier2 => (
                MechanismRecordStatus::DeepDive,
                Some(self.descriptor.clone()),
            ),
            ObservabilityTier::Tier3 => (
                MechanismRecordStatus::GoldCase,
                Some(self.descriptor.clone()),
            ),
        };
        Ok(MechanismRecord {
            record_id: format!("{}-mechanism", context.run_id),
            experiment_id: context.experiment_id.to_string(),
            run_id: context.run_id.to_string(),
            tier: context.decision.tier,
            status,
            collector,
            payload_digest: Some(compute_artifact_digest_bytes(
                context.response.digest.hex_digest.as_bytes(),
                Some(ArtifactKind::Other),
                Some(ArtifactRole::Manifest),
            )),
            failure_reason: None,
            decision: context.decision.clone(),
            provenance: provenance("fixture-mechanism-collector"),
        })
    }
}

struct TamperingScheduler {
    descriptor: ModuleDescriptor,
}

struct BudgetTamperingScheduler {
    descriptor: ModuleDescriptor,
}

impl ObservabilityScheduler for BudgetTamperingScheduler {
    fn descriptor(&self) -> ModuleDescriptor {
        self.descriptor.clone()
    }

    fn allocate(
        &self,
        signals: ObservabilitySignals,
        budget: &mut ObservabilityBudget,
    ) -> zkbench_core::error::Result<ObservabilityDecision> {
        let decision = WeightedObservabilityScheduler::default().allocate(signals, budget)?;
        budget.tier1_samples_remaining = budget.tier1_samples_remaining.saturating_sub(1);
        Ok(decision)
    }

    fn validate_decision(
        &self,
        decision: &ObservabilityDecision,
    ) -> zkbench_core::error::Result<()> {
        WeightedObservabilityScheduler::default().validate_decision(decision)
    }
}

impl ObservabilityScheduler for TamperingScheduler {
    fn descriptor(&self) -> ModuleDescriptor {
        self.descriptor.clone()
    }

    fn allocate(
        &self,
        signals: ObservabilitySignals,
        budget: &mut ObservabilityBudget,
    ) -> zkbench_core::error::Result<ObservabilityDecision> {
        let mut decision = WeightedObservabilityScheduler::default().allocate(signals, budget)?;
        decision.priority_milli += 1;
        Ok(decision)
    }

    fn validate_decision(
        &self,
        decision: &ObservabilityDecision,
    ) -> zkbench_core::error::Result<()> {
        WeightedObservabilityScheduler::default().validate_decision(decision)
    }
}

fn composed_runner(fail_collector: bool) -> ComposedExperimentRunner {
    let task_descriptor = module("task");
    let response_descriptor = module("response");
    let metric_descriptor = module("metric");
    let evaluator_descriptor = module("evaluator");
    let collector_descriptor = module("collector");
    let task_provenance = provenance("fixture-task");
    let spec = ExperimentRunSpec {
        bundle_id: "bundle-e2e-1".to_string(),
        experiment_id: "experiment-e2e-1".to_string(),
        run_id: "run-e2e-1".to_string(),
        hypothesis: "the fixture response should be measured through every seam".to_string(),
        replication: false,
        task_context: TaskContext {
            experiment_id: "experiment-e2e-1".to_string(),
            run_id: "run-e2e-1".to_string(),
            task_id: "task-e2e-1".to_string(),
            input_digest: compute_artifact_digest_bytes(
                b"fixture-input",
                Some(ArtifactKind::Other),
                Some(ArtifactRole::Manifest),
            ),
            provenance: task_provenance.clone(),
        },
        signals: ObservabilitySignals {
            novelty_milli: 100,
            uncertainty_milli: 100,
            failure_milli: 900,
        },
        provenance: task_provenance,
    };
    ComposedExperimentRunner::new(
        spec,
        Box::new(FixtureTask {
            descriptor: task_descriptor,
        }),
        Box::new(FixtureResponseProducer {
            descriptor: response_descriptor,
        }),
        vec![Box::new(FixtureMetric {
            descriptor: metric_descriptor,
        })],
        Box::new(FixtureEvaluator {
            descriptor: evaluator_descriptor,
        }),
        Box::new(FixtureMechanismCollector {
            descriptor: collector_descriptor,
            fail: fail_collector,
        }),
        Box::new(WeightedObservabilityScheduler::default()),
        ObservabilityBudget {
            tier1_samples_remaining: 1,
            tier2_deep_dives_remaining: 1,
            tier3_gold_cases_remaining: 0,
        },
    )
    .expect("all fixture adapters should satisfy the runner seams")
}

#[test]
fn composed_runner_rejects_duplicate_module_ids_before_adapter_execution() {
    let mut runner = composed_runner(false);
    runner.metrics.push(Box::new(FixtureMetric {
        descriptor: module("task"),
    }));
    let error = runner
        .run()
        .expect_err("duplicate module ids must fail before task execution");
    assert!(error
        .to_string()
        .contains("logical module id is duplicated"));
}

#[test]
fn composed_runner_constructor_rejects_duplicate_module_ids() {
    let runner = composed_runner(false);
    let ComposedExperimentRunner {
        spec,
        task,
        response_producer,
        mut metrics,
        evaluator,
        collector,
        scheduler,
        budget,
        ..
    } = runner;
    metrics.push(Box::new(FixtureMetric {
        descriptor: module("task"),
    }));
    let result = ComposedExperimentRunner::new(
        spec,
        task,
        response_producer,
        metrics,
        evaluator,
        collector,
        scheduler,
        budget,
    );
    assert!(result.is_err());
}

#[test]
fn every_run_has_the_same_nine_artifact_slots() {
    let fixed_bundle = bundle();
    validate_experiment_artifact_bundle(&fixed_bundle).expect("fixed bundle should validate");
    let mut invalid = fixed_bundle;
    invalid.report.kind = ExperimentArtifactKind::Logs;
    assert!(validate_experiment_artifact_bundle(&invalid).is_err());

    let mut identity_drift = bundle();
    identity_drift.task.run_id = "different-run".to_string();
    let error = validate_experiment_artifact_bundle(&identity_drift)
        .expect_err("cross-run artifact substitution must fail closed");
    assert!(error.to_string().contains("active run"));
}

#[test]
fn artifact_slot_order_is_one_canonical_contract() {
    assert_eq!(ExperimentArtifactKind::SLOT_COUNT, 9);
    assert_eq!(
        ExperimentArtifactKind::ALL,
        [
            ExperimentArtifactKind::Config,
            ExperimentArtifactKind::Task,
            ExperimentArtifactKind::Prompt,
            ExperimentArtifactKind::Response,
            ExperimentArtifactKind::Evaluation,
            ExperimentArtifactKind::MechanismRecord,
            ExperimentArtifactKind::Metadata,
            ExperimentArtifactKind::Logs,
            ExperimentArtifactKind::Report,
        ]
    );
    let fixed_bundle = bundle();
    let kinds = fixed_bundle.artifacts_in_order().map(|(kind, _)| kind);
    assert_eq!(kinds, ExperimentArtifactKind::ALL);
    assert_eq!(
        ExperimentArtifactKind::ALL.map(ExperimentArtifactKind::field_name),
        [
            "config",
            "task",
            "prompt",
            "response",
            "evaluation",
            "mechanism_record",
            "metadata",
            "logs",
            "report",
        ]
    );
}

#[test]
fn metric_observation_admission_matches_measurement_state() {
    let mut measured = MetricObservation {
        metric: module("metric.validation"),
        status: MetricObservationStatus::Measured,
        value: Some(7),
        provenance: provenance("metric-validation"),
    };
    measured
        .validate("metric")
        .expect("measured observations require and accept a scalar");

    measured.value = None;
    let error = measured
        .validate("metric")
        .expect_err("measured observations without a scalar must fail closed");
    assert!(error.to_string().contains("measured observations require"));

    measured.status = MetricObservationStatus::Unavailable;
    measured
        .validate("metric")
        .expect("unavailable observations must be value-free");

    measured.value = Some(7);
    let error = measured
        .validate("metric")
        .expect_err("unavailable observations must reject a scalar");
    assert!(error.to_string().contains("must not carry a scalar"));
}

#[test]
fn evaluation_admission_binds_outcome_and_rejects_duplicate_metrics() {
    let metric = MetricObservation {
        metric: module("metric.validation"),
        status: MetricObservationStatus::Measured,
        value: Some(7),
        provenance: provenance("metric-validation"),
    };
    let mut evaluation = EvaluationRecord {
        evaluator: module("evaluator.validation"),
        status: "negative_result".to_string(),
        outcome: ExperimentOutcome::Negative,
        metrics: vec![metric.clone()],
        provenance: provenance("evaluation-validation"),
    };
    evaluation
        .validate("evaluation")
        .expect("typed negative evaluations should validate");

    evaluation.status = "positive_result".to_string();
    let error = evaluation
        .validate("evaluation")
        .expect_err("status and typed outcome must agree");
    assert!(error
        .to_string()
        .contains("does not match its typed outcome"));

    evaluation.status = "negative_result".to_string();
    evaluation.metrics.push(metric);
    let error = evaluation
        .validate("evaluation")
        .expect_err("duplicate metric identities must fail closed");
    assert!(error
        .to_string()
        .contains("evaluation metric identity is duplicated"));
}

#[test]
fn report_admission_binds_typed_result_limitations_and_active_run() {
    let mut report = ExperimentRunReport {
        schema_version: EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION.to_string(),
        experiment_id: "experiment-report".to_string(),
        run_id: "run-report".to_string(),
        outcome: ExperimentOutcome::Negative,
        status: "negative_result".to_string(),
        negative_result: true,
        limitations: vec!["metadata-only contract".to_string()],
        claim_boundary: ClaimBoundary::Level0DesignNote,
        provenance: provenance("report-validation"),
    };
    report
        .validate_for("report", "experiment-report", "run-report")
        .expect("valid report should bind to its active run");

    report.negative_result = false;
    let error = report
        .validate("report")
        .expect_err("negative marker drift must fail closed");
    assert!(error.to_string().contains("negative-result marker"));

    report.negative_result = true;
    report.status = "positive_result".to_string();
    let error = report
        .validate("report")
        .expect_err("report status and outcome must agree");
    assert!(error
        .to_string()
        .contains("does not match its typed outcome"));

    report.outcome = ExperimentOutcome::Inconclusive;
    report.status = "local_replay_composed".to_string();
    report.negative_result = false;
    let error = report
        .validate("report")
        .expect_err("adapter-specific report labels must not replace canonical status");
    assert!(error
        .to_string()
        .contains("does not match its typed outcome"));

    report.status = "inconclusive".to_string();
    report
        .validate("report")
        .expect("inconclusive report status is canonical");

    report.limitations.clear();
    let error = report
        .validate("report")
        .expect_err("reports must retain explicit limitations");
    assert!(error.to_string().contains("at least one limitation"));

    report.limitations = vec!["metadata-only contract".to_string()];
    let error = report
        .validate_for("report", "different-experiment", "run-report")
        .expect_err("report identity must bind to the active experiment");
    assert!(error.to_string().contains("active run"));
}

#[test]
fn typed_report_readback_binds_payload_to_manifest_digest() {
    let report = ExperimentRunReport {
        schema_version: EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION.to_string(),
        experiment_id: "experiment-1".to_string(),
        run_id: "run-1".to_string(),
        outcome: ExperimentOutcome::Inconclusive,
        status: "inconclusive".to_string(),
        negative_result: false,
        limitations: vec!["metadata-only contract".to_string()],
        claim_boundary: ClaimBoundary::Level0DesignNote,
        provenance: provenance("report-readback"),
    };
    let mut manifest = bundle();
    manifest.experiment_id = report.experiment_id.clone();
    manifest.run_id = report.run_id.clone();
    manifest.report = create_experiment_artifact_ref(
        "run/report.json",
        ExperimentArtifactKind::Report,
        &report,
        &report.experiment_id,
        &report.run_id,
        report.provenance.clone(),
    )
    .expect("report artifact should be digest-bound");
    validate_experiment_artifact_bundle(&manifest).expect("manifest should remain structural");

    let report_json = serde_json::to_string(&report).expect("report should serialize");
    let restored = deserialize_experiment_report_json(&report_json, &manifest)
        .expect("canonical report readback should validate");
    assert_eq!(restored, report);

    let mut changed_report = report.clone();
    changed_report
        .limitations
        .push("payload changed after capture".to_string());
    let error = validate_experiment_report_artifact(
        &manifest.report,
        &changed_report,
        &manifest.experiment_id,
        &manifest.run_id,
        "bundle.report",
    )
    .expect_err("payload mutation must fail digest admission");
    assert!(error.to_string().contains("payload digest"));

    let changed_json =
        serde_json::to_string(&changed_report).expect("changed report should serialize");
    let error = deserialize_experiment_report_json(&changed_json, &manifest)
        .expect_err("changed serialized payload must fail readback");
    assert!(error.to_string().contains("payload digest"));

    let pretty_json = serde_json::to_string_pretty(&report).expect("report should pretty-print");
    let error = deserialize_experiment_report_json(&pretty_json, &manifest)
        .expect_err("non-canonical report bytes must fail readback");
    assert!(error.to_string().contains("canonical serialization"));
}

#[test]
fn artifact_reference_admission_rejects_uri_digest_and_provenance_drift() {
    let mut reference = artifact(ExperimentArtifactKind::Task, "task.json");
    reference
        .validate("artifact")
        .expect("valid artifact reference should be admitted");
    reference
        .validate_for("artifact", "experiment-1", "run-1")
        .expect("valid artifact scope should be admitted");

    reference.experiment_id = "different-experiment".to_string();
    let error = reference
        .validate_for("artifact", "experiment-1", "run-1")
        .expect_err("cross-experiment artifact scope must fail closed");
    assert!(error.to_string().contains("experiment identity"));

    reference.uri = "/absolute/task.json".to_string();
    let error = reference
        .validate("artifact")
        .expect_err("absolute artifact URI must fail closed");
    assert!(error.to_string().contains("artifact.uri"));

    reference = artifact(ExperimentArtifactKind::Task, "task.json");
    reference.digest.hex_digest = "A".repeat(64);
    let error = reference
        .validate("artifact")
        .expect_err("uppercase digest metadata must fail closed");
    assert!(error.to_string().contains("artifact.digest"));

    reference = artifact(ExperimentArtifactKind::Task, "task.json");
    reference.provenance.source_revision.clear();
    let error = reference
        .validate("artifact")
        .expect_err("missing artifact source revision must fail closed");
    assert!(error.to_string().contains("source_revision"));
}

#[test]
fn scheduler_spends_only_target_tier_and_falls_back_to_tier0() {
    let scheduler = WeightedObservabilityScheduler::default();
    let mut budget = ObservabilityBudget {
        tier1_samples_remaining: 1,
        tier2_deep_dives_remaining: 1,
        tier3_gold_cases_remaining: 0,
    };
    let low = scheduler
        .allocate(
            ObservabilitySignals {
                novelty_milli: 0,
                uncertainty_milli: 0,
                failure_milli: 0,
            },
            &mut budget,
        )
        .expect("low signal should allocate");
    assert_eq!(low.tier, ObservabilityTier::Tier0);
    assert_eq!(budget.tier1_samples_remaining, 1);
    assert_eq!(budget.tier2_deep_dives_remaining, 1);

    let sample = scheduler
        .allocate(
            ObservabilitySignals {
                novelty_milli: 300,
                uncertainty_milli: 300,
                failure_milli: 300,
            },
            &mut budget,
        )
        .expect("moderate signal should allocate");
    assert_eq!(sample.tier, ObservabilityTier::Tier1);
    assert_eq!(budget.tier1_samples_remaining, 0);
    assert_eq!(budget.tier2_deep_dives_remaining, 1);
}

#[test]
fn failure_signal_triggers_deep_dive_and_gold_case_is_budgeted() {
    let scheduler = WeightedObservabilityScheduler::default();
    let mut budget = ObservabilityBudget {
        tier1_samples_remaining: 1,
        tier2_deep_dives_remaining: 1,
        tier3_gold_cases_remaining: 1,
    };
    let deep = scheduler
        .allocate(
            ObservabilitySignals {
                novelty_milli: 100,
                uncertainty_milli: 100,
                failure_milli: 900,
            },
            &mut budget,
        )
        .expect("failure should trigger deep dive");
    assert_eq!(deep.tier, ObservabilityTier::Tier2);
    assert_eq!(budget.tier2_deep_dives_remaining, 0);

    let gold = scheduler
        .allocate(
            ObservabilitySignals {
                novelty_milli: 1000,
                uncertainty_milli: 1000,
                failure_milli: 1000,
            },
            &mut budget,
        )
        .expect("high signal should trigger gold case");
    assert_eq!(gold.tier, ObservabilityTier::Tier3);
    assert_eq!(budget.tier3_gold_cases_remaining, 0);
}

#[test]
fn mechanism_ledger_appends_and_detects_history_mutation() {
    let mut ledger = MechanismLedger::new("experiment-1");
    ledger
        .append(MechanismRecord {
            record_id: "mechanism-1".to_string(),
            experiment_id: "experiment-1".to_string(),
            run_id: "run-1".to_string(),
            tier: ObservabilityTier::Tier0,
            status: MechanismRecordStatus::MetadataOnly,
            collector: None,
            payload_digest: None,
            failure_reason: None,
            decision: decision(ObservabilityTier::Tier0),
            provenance: provenance("mechanism-record"),
        })
        .expect("metadata record should append");
    ledger.validate().expect("ledger should validate");
    assert_eq!(ledger.entries.len(), 1);
    let json = serialize_mechanism_ledger_json(&ledger).expect("ledger should serialize");
    let restored = deserialize_mechanism_ledger_json(&json).expect("ledger should deserialize");
    assert_eq!(restored, ledger);
    let pretty_json = serde_json::to_string_pretty(&ledger).expect("ledger should pretty-print");
    assert!(deserialize_mechanism_ledger_json(&pretty_json).is_err());
    ledger.entries[0].record.record_id = "tampered".to_string();
    assert!(ledger.validate().is_err());
}

#[test]
fn metric_meta_evaluation_tracks_three_distinct_properties() {
    let mut ledger = MetaEvaluationLedger::default();
    let assessment_basis = MetricMetaEvaluationBasis {
        comparison_rule_id: "rule-heldout-v1".to_string(),
        held_out_target_id: "target-behavior-v1".to_string(),
        replication_id: "meta-replication-1".to_string(),
        source_artifacts: vec![artifact(
            ExperimentArtifactKind::Evaluation,
            "meta-evaluation-source.json",
        )],
    };
    ledger
        .append(MetricMetaEvaluation {
            metric: module("metric.downstream"),
            assessment_basis_digest: compute_artifact_digest(
                &assessment_basis,
                Some(ArtifactKind::Other),
                Some(ArtifactRole::Manifest),
            )
            .expect("assessment basis should digest"),
            assessment_basis,
            stability: MetricStability::Stable,
            downstream_predictiveness: DownstreamPredictiveness::Predictive,
            noise: MetricNoise::Medium,
            noise_milli: Some(400),
            observation_count: 20,
            replication_count: 4,
            provenance: provenance("metric-meta-evaluation"),
        })
        .expect("meta-evaluation should append");
    ledger.validate().expect("meta-evaluation should validate");
    assert_eq!(ledger.entries.len(), 1);
    assert_eq!(ledger.entries[0].sequence_number, 0);
    assert_eq!(ledger.entries[0].previous_digest, None);
    assert_eq!(
        ledger.tip_digest,
        Some(ledger.entries[0].entry_digest.clone())
    );
    let json =
        serialize_meta_evaluation_ledger_json(&ledger).expect("meta-evaluation should serialize");
    let restored =
        deserialize_meta_evaluation_ledger_json(&json).expect("meta-evaluation should deserialize");
    assert_eq!(restored, ledger);
    let pretty_json =
        serde_json::to_string_pretty(&ledger).expect("meta-evaluation should pretty-print");
    assert!(deserialize_meta_evaluation_ledger_json(&pretty_json).is_err());

    ledger.entries[0].evaluation.observation_count = 21;
    let error = ledger
        .validate()
        .expect_err("ledger evaluation mutation must break the entry digest");
    assert!(error
        .to_string()
        .contains("meta_evaluation.entries[0].entry_digest"));
}

#[test]
fn metric_meta_evaluation_requires_frozen_scope_and_source_artifacts() {
    let assessment_basis = MetricMetaEvaluationBasis {
        comparison_rule_id: String::new(),
        held_out_target_id: String::new(),
        replication_id: String::new(),
        source_artifacts: Vec::new(),
    };
    let mut evaluation = MetricMetaEvaluation {
        metric: module("metric.unbound"),
        assessment_basis_digest: compute_artifact_digest(
            &assessment_basis,
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Manifest),
        )
        .expect("unbound assessment basis should still be serializable"),
        assessment_basis,
        stability: MetricStability::Untested,
        downstream_predictiveness: DownstreamPredictiveness::Untested,
        noise: MetricNoise::Unknown,
        noise_milli: None,
        observation_count: 0,
        replication_count: 0,
        provenance: provenance("unbound-meta-evaluation"),
    };
    let error = evaluation
        .validate("meta_evaluation")
        .expect_err("unbound meta-evaluation must fail closed");
    assert!(error
        .to_string()
        .contains("assessment_basis.comparison_rule_id"));

    evaluation.assessment_basis.comparison_rule_id = "rule-heldout-v1".to_string();
    evaluation.assessment_basis.held_out_target_id = "target-behavior-v1".to_string();
    evaluation.assessment_basis.replication_id = "meta-replication-1".to_string();
    let error = evaluation
        .validate("meta_evaluation")
        .expect_err("meta-evaluation without source artifacts must fail closed");
    assert!(error
        .to_string()
        .contains("assessment_basis.source_artifacts"));

    evaluation.assessment_basis.source_artifacts = vec![artifact(
        ExperimentArtifactKind::Evaluation,
        "meta-evaluation-source.json",
    )];
    evaluation.assessment_basis_digest = compute_artifact_digest(
        &evaluation.assessment_basis,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    )
    .expect("bound assessment basis should digest");
    evaluation
        .validate("meta_evaluation")
        .expect("fully bound untested metadata should validate");

    evaluation.assessment_basis.source_artifacts[0].uri = "changed-source.json".to_string();
    let error = evaluation
        .validate("meta_evaluation")
        .expect_err("source drift must invalidate the retained basis digest");
    assert!(error.to_string().contains("assessment_basis_digest"));
}

#[test]
fn signal_range_is_bounded() {
    let error = ObservabilitySignals {
        novelty_milli: OBSERVABILITY_SCORE_SCALE + 1,
        uncertainty_milli: 0,
        failure_milli: 0,
    }
    .validate()
    .expect_err("out-of-range signal should fail");
    assert!(error.to_string().contains("score must be"));
}

#[test]
fn weighted_scheduler_rejects_tampered_priority_and_reasons() {
    let scheduler = WeightedObservabilityScheduler::default();
    let mut budget = ObservabilityBudget {
        tier1_samples_remaining: 1,
        tier2_deep_dives_remaining: 0,
        tier3_gold_cases_remaining: 0,
    };
    let mut decision = scheduler
        .allocate(
            ObservabilitySignals {
                novelty_milli: 300,
                uncertainty_milli: 300,
                failure_milli: 300,
            },
            &mut budget,
        )
        .expect("reference scheduler should allocate");
    scheduler
        .validate_decision(&decision)
        .expect("fresh decision should validate");
    decision.priority_milli += 1;
    assert!(scheduler.validate_decision(&decision).is_err());
}

#[test]
fn failed_mechanism_records_require_a_reason() {
    let mut ledger = MechanismLedger::new("experiment-failure");
    let error = ledger
        .append(MechanismRecord {
            record_id: "mechanism-failure".to_string(),
            experiment_id: "experiment-failure".to_string(),
            run_id: "run-failure".to_string(),
            tier: ObservabilityTier::Tier1,
            status: MechanismRecordStatus::Failed,
            collector: None,
            payload_digest: None,
            failure_reason: None,
            decision: decision(ObservabilityTier::Tier1),
            provenance: provenance("failed-mechanism"),
        })
        .expect_err("failed record without a reason must fail closed");
    assert!(error.to_string().contains("failure reason"));
}

#[test]
fn composed_runner_emits_valid_bundle_and_retains_negative_result() {
    let mut runner = composed_runner(false);

    let bundle = runner.run().expect("composed runner should emit a bundle");
    validate_experiment_artifact_bundle(&bundle).expect("runner output should validate");
    assert_eq!(bundle.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(
        runner.remaining_budget().tier2_deep_dives_remaining,
        0,
        "the failure signal should spend only the Tier2 budget"
    );
    assert_eq!(
        bundle.mechanism_record.kind,
        ExperimentArtifactKind::MechanismRecord
    );
    assert_eq!(bundle.evaluation.kind, ExperimentArtifactKind::Evaluation);
    assert_eq!(bundle.report.kind, ExperimentArtifactKind::Report);
    let expected_report = create_experiment_artifact_ref(
        "run/report.json",
        ExperimentArtifactKind::Report,
        &ExperimentRunReport {
            schema_version: EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION.to_string(),
            experiment_id: "experiment-e2e-1".to_string(),
            run_id: "run-e2e-1".to_string(),
            outcome: ExperimentOutcome::Negative,
            status: "negative_result".to_string(),
            negative_result: true,
            limitations: vec![
                "metadata-only contract".to_string(),
                "not accepted evidence".to_string(),
                "not a benchmark or interpretability claim".to_string(),
            ],
            claim_boundary: ClaimBoundary::Level0DesignNote,
            provenance: provenance("fixture-task"),
        },
        "experiment-e2e-1",
        "run-e2e-1",
        provenance("fixture-task"),
    )
    .expect("expected report digest should be constructible");
    assert_eq!(bundle.report, expected_report);
    let ledger = runner
        .mechanism_ledger()
        .expect("generic composition should retain a mechanism ledger");
    ledger
        .validate()
        .expect("generic mechanism digest chain should validate");
    assert_eq!(ledger.entries.len(), 1);
    let error = runner.run().expect_err("generic runner must be one-shot");
    assert!(error.to_string().contains("one-shot"));
}

#[test]
fn composed_runner_budget_commit_is_failure_atomic() {
    let mut runner = composed_runner(true);
    let error = runner
        .run()
        .expect_err("collector failure should abort the run");
    assert!(error.to_string().contains("fixture collector failure"));
    assert_eq!(runner.remaining_budget().tier2_deep_dives_remaining, 1);
    assert!(runner.mechanism_ledger().is_none());
}

#[test]
fn local_json_runner_budget_commit_is_failure_atomic_after_allocation() {
    let mut runner = LocalJsonExperimentRunner::new_with_scheduler(
        zkbench_core::GeneratorConfig::baseline_fsm(),
        "local-transaction-experiment",
        "local-transaction-run",
        ObservabilitySignals {
            novelty_milli: 100,
            uncertainty_milli: 100,
            failure_milli: 900,
        },
        provenance("local-transaction-failure"),
        ObservabilityBudget {
            tier1_samples_remaining: 1,
            tier2_deep_dives_remaining: 1,
            tier3_gold_cases_remaining: 0,
        },
        Box::new(TamperingScheduler {
            descriptor: module("tampering-scheduler"),
        }),
    )
    .expect("local transaction fixture should construct");

    let error = runner
        .run()
        .expect_err("invalid scheduler decision should abort after allocation");
    assert!(error.to_string().contains("weighted priority"));
    assert_eq!(runner.remaining_budget().tier2_deep_dives_remaining, 1);
    assert!(runner.mechanism_ledger().is_none());
    assert!(runner.composition_config().is_none());
}

#[test]
fn scheduler_budget_transition_rejects_unrelated_budget_spend() {
    let mut runner = LocalJsonExperimentRunner::new_with_scheduler(
        zkbench_core::GeneratorConfig::baseline_fsm(),
        "budget-transition-experiment",
        "budget-transition-run",
        ObservabilitySignals {
            novelty_milli: 100,
            uncertainty_milli: 100,
            failure_milli: 900,
        },
        provenance("budget-transition"),
        ObservabilityBudget {
            tier1_samples_remaining: 1,
            tier2_deep_dives_remaining: 1,
            tier3_gold_cases_remaining: 0,
        },
        Box::new(BudgetTamperingScheduler {
            descriptor: module("budget-tampering-scheduler"),
        }),
    )
    .expect("budget transition fixture should construct");

    let error = runner
        .run()
        .expect_err("scheduler budget drift must fail closed");
    assert!(error.to_string().contains("exactly the selected tier"));
    assert_eq!(runner.remaining_budget().tier1_samples_remaining, 1);
    assert_eq!(runner.remaining_budget().tier2_deep_dives_remaining, 1);
    assert!(runner.mechanism_ledger().is_none());
    assert!(runner.composition_config().is_none());
}

#[test]
fn bundle_json_round_trip_preserves_digest_and_rejects_invalid_shape() {
    let bundle = bundle();
    let json =
        serialize_experiment_artifact_bundle_json(&bundle).expect("valid bundle should serialize");
    let restored = deserialize_experiment_artifact_bundle_json(&json)
        .expect("serialized bundle should deserialize");
    assert_eq!(restored, bundle);
    assert_eq!(
        compute_experiment_artifact_bundle_digest(&restored)
            .expect("restored bundle should digest"),
        compute_experiment_artifact_bundle_digest(&bundle).expect("bundle should digest")
    );

    let mut invalid = bundle;
    invalid.report.kind = ExperimentArtifactKind::Logs;
    let invalid_json = serde_json::to_string(&invalid).expect("fixture should serialize");
    assert!(deserialize_experiment_artifact_bundle_json(&invalid_json).is_err());
}

#[test]
fn explicit_v1_upgrade_rehydrates_identity_without_rewriting_artifacts() {
    let original = bundle();
    let legacy_json = legacy_v1_bundle_json(&original);

    assert!(deserialize_experiment_artifact_bundle_json(&legacy_json).is_err());
    let upgraded = upgrade_experiment_artifact_bundle_v1_json(&legacy_json)
        .expect("explicit v1 migration should produce a valid v2 bundle");
    validate_experiment_artifact_bundle(&upgraded).expect("upgraded bundle should validate");
    assert_eq!(
        upgraded.schema_version,
        EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION
    );
    assert_eq!(upgraded.experiment_id, original.experiment_id);
    assert_eq!(upgraded.run_id, original.run_id);

    let original_refs = [
        &original.config,
        &original.task,
        &original.prompt,
        &original.response,
        &original.evaluation,
        &original.mechanism_record,
        &original.metadata,
        &original.logs,
        &original.report,
    ];
    let upgraded_refs = [
        &upgraded.config,
        &upgraded.task,
        &upgraded.prompt,
        &upgraded.response,
        &upgraded.evaluation,
        &upgraded.mechanism_record,
        &upgraded.metadata,
        &upgraded.logs,
        &upgraded.report,
    ];
    for (original_ref, upgraded_ref) in original_refs.iter().zip(upgraded_refs.iter()) {
        assert_eq!(upgraded_ref.uri, original_ref.uri);
        assert_eq!(upgraded_ref.kind, original_ref.kind);
        assert_eq!(upgraded_ref.digest, original_ref.digest);
        assert_eq!(upgraded_ref.provenance, original_ref.provenance);
        assert_eq!(upgraded_ref.experiment_id, original.experiment_id);
        assert_eq!(upgraded_ref.run_id, original.run_id);
    }
}

#[test]
fn explicit_v1_upgrade_requires_canonical_v1_and_never_accepts_v2_as_legacy() {
    let original = bundle();
    let legacy_json = legacy_v1_bundle_json(&original);
    let pretty_json = serde_json::to_string_pretty(
        &serde_json::from_str::<serde_json::Value>(&legacy_json)
            .expect("legacy fixture should parse as JSON"),
    )
    .expect("pretty legacy fixture should serialize");
    assert!(upgrade_experiment_artifact_bundle_v1_json(&pretty_json).is_err());

    let v2_json = serialize_experiment_artifact_bundle_json(&original)
        .expect("current bundle should serialize");
    assert!(upgrade_experiment_artifact_bundle_v1_json(&v2_json).is_err());
}

#[test]
fn local_plugin_composes_into_observability_bundle_and_digest_ledger() {
    let catalog =
        ExperimentPluginFactoryCatalog::local_json(zkbench_core::GeneratorConfig::baseline_fsm())
            .expect("local factory catalog should construct");
    let inner = catalog
        .run(zkbench_core::LOCAL_JSON_EXPERIMENT_PLUGIN_ID)
        .expect("inner local plugin should run through the factory catalog");
    assert!(zkbench_core::validate_experiment_bundle(&inner).valid);

    let mut runner = LocalJsonExperimentRunner::new(
        zkbench_core::GeneratorConfig::baseline_fsm(),
        "experiment-composition-1",
        "run-composition-1",
        ObservabilitySignals {
            novelty_milli: 100,
            uncertainty_milli: 100,
            failure_milli: 900,
        },
        provenance("local-composition"),
        ObservabilityBudget {
            tier1_samples_remaining: 1,
            tier2_deep_dives_remaining: 1,
            tier3_gold_cases_remaining: 0,
        },
    )
    .expect("local composition runner should construct");
    let bundle = runner.run().expect("local plugin should compose once");
    validate_experiment_artifact_bundle(&bundle).expect("outer bundle should validate");
    let composition_config = runner
        .composition_config()
        .expect("composition config should be retained");
    validate_local_json_artifact_projection(&inner, &bundle, composition_config)
        .expect("canonical inner-to-outer projection should validate");
    let config_json = serialize_local_json_composition_config_json(composition_config)
        .expect("composition config should serialize");
    let restored_config = validate_serialized_local_json_composition(&config_json, &inner, &bundle)
        .expect("serialized composition config should validate");
    assert_eq!(restored_config, *composition_config);
    assert_eq!(
        compute_local_json_composition_config_digest(composition_config)
            .expect("composition config should digest"),
        bundle.config.digest
    );
    let inner_json = zkbench_core::serialize_experiment_bundle_json(&inner)
        .expect("inner bundle should serialize");
    let outer_json =
        serialize_experiment_artifact_bundle_json(&bundle).expect("outer bundle should serialize");
    let (transport_inner, transport_config, transport_outer) =
        validate_serialized_local_json_composition_transport(
            &inner_json,
            &config_json,
            &outer_json,
        )
        .expect("complete composition transport should validate");
    assert_eq!(transport_inner, inner);
    assert_eq!(transport_config, *composition_config);
    assert_eq!(transport_outer, bundle);
    assert_eq!(composition_config.projection.bindings.len(), 9);
    let ledger = runner
        .mechanism_ledger()
        .expect("composition should retain a mechanism ledger");
    ledger
        .validate()
        .expect("mechanism digest chain should validate");
    assert_eq!(ledger.entries.len(), 1);
    assert_eq!(ledger.entries[0].record.tier, ObservabilityTier::Tier2);
    assert_eq!(runner.remaining_budget().tier2_deep_dives_remaining, 0);
    assert_eq!(bundle.claim_boundary, ClaimBoundary::Level0DesignNote);
}

#[test]
fn local_config_retains_durable_composition_adapter_attribution() {
    let inner =
        ExperimentPluginFactoryCatalog::local_json(zkbench_core::GeneratorConfig::baseline_fsm())
            .expect("local factory catalog should construct")
            .run(zkbench_core::LOCAL_JSON_EXPERIMENT_PLUGIN_ID)
            .expect("inner local plugin should run");
    let mut runner = LocalJsonExperimentRunner::new(
        zkbench_core::GeneratorConfig::baseline_fsm(),
        "local-adapter-attribution-experiment",
        "local-adapter-attribution-run",
        ObservabilitySignals {
            novelty_milli: 0,
            uncertainty_milli: 0,
            failure_milli: 0,
        },
        provenance("local-adapter-attribution"),
        ObservabilityBudget {
            tier1_samples_remaining: 0,
            tier2_deep_dives_remaining: 0,
            tier3_gold_cases_remaining: 0,
        },
    )
    .expect("local composition runner should construct");
    runner.run().expect("local composition should run");
    let config = runner
        .composition_config()
        .expect("local composition should retain config");
    let descriptor = config
        .adapter_descriptor
        .as_ref()
        .expect("new local config should retain adapter identity");
    assert_eq!(
        descriptor.module_id,
        zkbench_core::LOCAL_JSON_COMPOSITION_ADAPTER_MODULE_ID
    );
    assert_eq!(
        descriptor.implementation_id,
        zkbench_core::LOCAL_JSON_COMPOSITION_ADAPTER_ID
    );
    assert_eq!(descriptor.version, "1");
    assert_eq!(
        descriptor.source_revision,
        zkbench_core::LOCAL_JSON_COMPOSITION_ADAPTER_SOURCE_REVISION
    );

    let mut drifted = config.clone();
    drifted
        .adapter_descriptor
        .as_mut()
        .expect("adapter identity should be present")
        .implementation_id = "replacement-local-adapter-v2".to_string();
    let error = drifted
        .validate(&inner)
        .expect_err("local adapter identity drift must fail closed");
    assert!(error.to_string().contains("does not match adapter_id"));

    let current_json = serialize_local_json_composition_config_json(config)
        .expect("local config should serialize");
    let descriptor_json = serde_json::to_string(
        config
            .adapter_descriptor
            .as_ref()
            .expect("current config should retain adapter identity"),
    )
    .expect("adapter descriptor should serialize");
    let adapter_field = format!(",\"adapter_descriptor\":{descriptor_json}");
    let legacy_json = current_json.replace(&adapter_field, "");
    let legacy = deserialize_local_json_composition_config_json(&legacy_json)
        .expect("legacy config without adapter identity should remain readable");
    assert!(legacy.adapter_descriptor.is_none());
    legacy
        .validate(&inner)
        .expect("legacy local config should retain semantic validation");
}

#[test]
fn local_composition_output_is_a_receipt_bound_handoff_with_compatibility_adapter() {
    let mut runner = LocalJsonExperimentRunner::new(
        zkbench_core::GeneratorConfig::baseline_fsm(),
        "experiment-composition-handoff",
        "run-composition-handoff",
        ObservabilitySignals {
            novelty_milli: 100,
            uncertainty_milli: 100,
            failure_milli: 900,
        },
        provenance("local-composition-handoff"),
        ObservabilityBudget {
            tier1_samples_remaining: 1,
            tier2_deep_dives_remaining: 1,
            tier3_gold_cases_remaining: 0,
        },
    )
    .expect("local composition runner should construct");

    let validated = runner
        .run_validated_output()
        .expect("validated local composition should succeed");
    assert_eq!(validated.config().projection.bindings.len(), 9);
    assert_eq!(
        validated.outer().claim_boundary,
        ClaimBoundary::Level0DesignNote
    );

    let compatibility_outer = validated.clone().into_outer();
    let (inner, config, outer) = validated.into_parts();
    validate_local_json_artifact_projection(&inner, &outer, &config)
        .expect("validated handoff should remain projection-valid");
    assert_eq!(compatibility_outer, outer);

    let mut drifted_outer = outer.clone();
    drifted_outer.run_id = "drifted-local-composition-run".to_string();
    assert!(
        ValidatedLocalJsonCompositionOutput::new(inner, config, drifted_outer).is_err(),
        "outer identity drift must not enter the typed handoff"
    );
}

#[test]
fn local_composition_accepts_an_alternate_plugin_adapter() {
    let inner =
        ExperimentPluginFactoryCatalog::local_json(zkbench_core::GeneratorConfig::baseline_fsm())
            .expect("local factory catalog should construct")
            .run(zkbench_core::LOCAL_JSON_EXPERIMENT_PLUGIN_ID)
            .expect("reference plugin should produce the fixture bundle");
    let mut descriptor = zkbench_core::local_json_experiment_plugin_descriptor();
    descriptor.task_id = "alternate-source-adapter-task-v1".to_string();
    let plugin = AlternatePluginAdapter {
        descriptor,
        bundle: inner,
    };
    let mut runner = LocalJsonExperimentRunner::new_with_plugin(
        Box::new(plugin),
        "experiment-composition-adapter",
        "run-composition-adapter",
        ObservabilitySignals {
            novelty_milli: 0,
            uncertainty_milli: 0,
            failure_milli: 0,
        },
        provenance("alternate-source-adapter"),
        ObservabilityBudget {
            tier1_samples_remaining: 0,
            tier2_deep_dives_remaining: 0,
            tier3_gold_cases_remaining: 0,
        },
        Box::new(WeightedObservabilityScheduler::default()),
    )
    .expect("alternate plugin adapter should construct");

    let bundle = runner
        .run()
        .expect("alternate plugin adapter should compose");
    validate_experiment_artifact_bundle(&bundle).expect("alternate composition should validate");
    let config = runner
        .composition_config()
        .expect("alternate composition should retain config");
    let source = config
        .modules
        .iter()
        .find(|module| module.module_id == "experiment-source")
        .expect("source adapter identity should be retained");
    assert_eq!(
        source.implementation_id,
        zkbench_core::LOCAL_JSON_EXPERIMENT_PLUGIN_ID
    );
    assert_eq!(
        source.version,
        zkbench_core::EXPERIMENT_BUNDLE_SCHEMA_VERSION
    );
}

#[test]
fn local_composition_runner_is_one_shot_for_a_fixed_run_id() {
    let mut runner = LocalJsonExperimentRunner::new(
        zkbench_core::GeneratorConfig::baseline_fsm(),
        "experiment-composition-2",
        "run-composition-2",
        ObservabilitySignals {
            novelty_milli: 0,
            uncertainty_milli: 0,
            failure_milli: 0,
        },
        provenance("local-composition-once"),
        ObservabilityBudget {
            tier1_samples_remaining: 0,
            tier2_deep_dives_remaining: 0,
            tier3_gold_cases_remaining: 0,
        },
    )
    .expect("local composition runner should construct");
    runner.run().expect("first run should succeed");
    let error = runner.run().expect_err("second run must fail closed");
    assert!(error.to_string().contains("one-shot"));
}

#[test]
fn local_composition_rejects_projection_and_outer_digest_drift() {
    let inner =
        ExperimentPluginFactoryCatalog::local_json(zkbench_core::GeneratorConfig::baseline_fsm())
            .expect("local factory catalog should construct")
            .run(zkbench_core::LOCAL_JSON_EXPERIMENT_PLUGIN_ID)
            .expect("inner local plugin should run through the factory catalog");
    let mut runner = LocalJsonExperimentRunner::new(
        zkbench_core::GeneratorConfig::baseline_fsm(),
        "experiment-composition-integrity",
        "run-composition-integrity",
        ObservabilitySignals {
            novelty_milli: 0,
            uncertainty_milli: 0,
            failure_milli: 0,
        },
        provenance("local-composition-integrity"),
        ObservabilityBudget {
            tier1_samples_remaining: 0,
            tier2_deep_dives_remaining: 0,
            tier3_gold_cases_remaining: 0,
        },
    )
    .expect("local composition runner should construct");
    let bundle = runner.run().expect("local composition should succeed");
    let composition_config = runner
        .composition_config()
        .expect("composition config should be retained");
    let mut duplicate_modules = composition_config.clone();
    duplicate_modules.modules[1].module_id = duplicate_modules.modules[0].module_id.clone();
    let module_error = duplicate_modules
        .validate(&inner)
        .expect_err("duplicate module ids must fail composition config validation");
    assert!(module_error
        .to_string()
        .contains("logical module id is duplicated"));
    let mechanism_binding = composition_config
        .projection
        .binding(ExperimentArtifactKind::MechanismRecord)
        .expect("mechanism slot should be projected");
    assert!(matches!(
        mechanism_binding.relation,
        zkbench_core::experiment_observability::LocalJsonProjectionRelation::Absent
    ));
    assert!(mechanism_binding.inner_artifacts.is_empty());

    let mut tampered_config = composition_config.clone();
    tampered_config.projection.bindings[1].inner_artifacts[0].uri =
        "run/tampered-task.json".to_string();
    let projection_error =
        validate_local_json_artifact_projection(&inner, &bundle, &tampered_config)
            .expect_err("source URI drift must fail closed");
    assert!(projection_error
        .to_string()
        .contains("canonical local mapping"));

    let mut tampered_bundle = bundle.clone();
    tampered_bundle.response.digest = compute_artifact_digest_bytes(
        b"tampered-response",
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    );
    let digest_error =
        validate_local_json_artifact_projection(&inner, &tampered_bundle, composition_config)
            .expect_err("outer projected digest drift must fail closed");
    assert!(digest_error.to_string().contains("outer digest drift"));

    let mut tampered_transport = composition_config.clone();
    tampered_transport.run_id = "tampered-transport-run".to_string();
    let tampered_json = serialize_local_json_composition_config_json(&tampered_transport)
        .expect("tampered composition config should serialize");
    let transport_error =
        validate_serialized_local_json_composition(&tampered_json, &inner, &bundle)
            .expect_err("config transport digest drift must fail closed");
    assert!(transport_error
        .to_string()
        .contains("transported config bytes"));

    let inner_json = zkbench_core::serialize_experiment_bundle_json(&inner)
        .expect("inner bundle should serialize");
    let config_json = serialize_local_json_composition_config_json(composition_config)
        .expect("composition config should serialize");
    let outer_json =
        serialize_experiment_artifact_bundle_json(&bundle).expect("outer bundle should serialize");
    let noncanonical_inner = format!(" {inner_json}");
    let canonical_error = validate_serialized_local_json_composition_transport(
        &noncanonical_inner,
        &config_json,
        &outer_json,
    )
    .expect_err("non-canonical inner bytes must fail closed");
    assert!(canonical_error.to_string().contains("inner bundle bytes"));
}

#[test]
fn local_projection_binding_access_requires_one_matching_slot() {
    let inner =
        ExperimentPluginFactoryCatalog::local_json(zkbench_core::GeneratorConfig::baseline_fsm())
            .expect("local factory catalog should construct")
            .run(zkbench_core::LOCAL_JSON_EXPERIMENT_PLUGIN_ID)
            .expect("inner local plugin should run through the factory catalog");
    let projection =
        zkbench_core::experiment_observability::LocalJsonArtifactProjection::from_inner_bundle(
            &inner,
            ObservabilityTier::Tier0,
        )
        .expect("canonical projection should build");

    assert_eq!(
        projection
            .binding(ExperimentArtifactKind::Report)
            .expect("report binding should exist")
            .outer_uri,
        "run/report.json"
    );

    let mut missing = projection.clone();
    missing
        .bindings
        .retain(|binding| binding.outer_kind != ExperimentArtifactKind::Report);
    let missing_error = missing
        .binding(ExperimentArtifactKind::Report)
        .expect_err("missing projection slots must fail closed");
    assert!(missing_error.to_string().contains("missing binding"));

    let mut duplicate = projection.clone();
    duplicate.bindings.push(duplicate.bindings[0].clone());
    let duplicate_error = duplicate
        .binding(ExperimentArtifactKind::Config)
        .expect_err("duplicate projection slots must fail closed");
    assert!(duplicate_error.to_string().contains("is duplicated"));
}

#[test]
fn local_projection_single_source_access_requires_one_inner_artifact() {
    let inner =
        ExperimentPluginFactoryCatalog::local_json(zkbench_core::GeneratorConfig::baseline_fsm())
            .expect("local factory catalog should construct")
            .run(zkbench_core::LOCAL_JSON_EXPERIMENT_PLUGIN_ID)
            .expect("inner local plugin should run through the factory catalog");
    let projection =
        zkbench_core::experiment_observability::LocalJsonArtifactProjection::from_inner_bundle(
            &inner,
            ObservabilityTier::Tier0,
        )
        .expect("canonical projection should build");

    let task_source = projection
        .single_inner_artifact(ExperimentArtifactKind::Task)
        .expect("task projection should expose one inner source");
    assert_eq!(
        task_source.kind,
        zkbench_core::experiment::ExperimentArtifactKind::DataVersion
    );

    let mut missing = projection.clone();
    missing
        .bindings
        .iter_mut()
        .find(|binding| binding.outer_kind == ExperimentArtifactKind::Task)
        .expect("task binding should exist")
        .inner_artifacts
        .clear();
    let missing_error = missing
        .single_inner_artifact(ExperimentArtifactKind::Task)
        .expect_err("missing direct source must fail closed");
    assert!(missing_error
        .to_string()
        .contains("requires one inner source"));

    let mut duplicate = projection.clone();
    let task_binding = duplicate
        .bindings
        .iter_mut()
        .find(|binding| binding.outer_kind == ExperimentArtifactKind::Task)
        .expect("task binding should exist");
    task_binding
        .inner_artifacts
        .push(task_binding.inner_artifacts[0].clone());
    let duplicate_error = duplicate
        .single_inner_artifact(ExperimentArtifactKind::Task)
        .expect_err("duplicated direct source must fail closed");
    assert!(duplicate_error
        .to_string()
        .contains("inner source is duplicated"));
}

#[test]
fn local_projection_source_access_rejects_missing_and_duplicate_inner_artifacts() {
    let inner =
        ExperimentPluginFactoryCatalog::local_json(zkbench_core::GeneratorConfig::baseline_fsm())
            .expect("local factory catalog should construct")
            .run(zkbench_core::LOCAL_JSON_EXPERIMENT_PLUGIN_ID)
            .expect("inner local plugin should run through the factory catalog");

    let mut missing = inner.clone();
    missing.artifacts.retain(|artifact| {
        artifact.kind != zkbench_core::experiment::ExperimentArtifactKind::DataVersion
    });
    let missing_error =
        zkbench_core::experiment_observability::LocalJsonArtifactProjection::from_inner_bundle(
            &missing,
            ObservabilityTier::Tier0,
        )
        .expect_err("missing inner source artifacts must fail closed");
    assert!(missing_error
        .to_string()
        .contains("projection.data_version"));

    let mut duplicate = inner.clone();
    duplicate.artifacts.push(duplicate.artifacts[0].clone());
    let duplicate_error =
        zkbench_core::experiment_observability::LocalJsonArtifactProjection::from_inner_bundle(
            &duplicate,
            ObservabilityTier::Tier0,
        )
        .expect_err("duplicate inner source artifacts must fail closed");
    assert!(duplicate_error.to_string().contains("projection.config"));
    assert!(duplicate_error.to_string().contains("duplicated"));
}
