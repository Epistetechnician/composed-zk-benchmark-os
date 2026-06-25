//! ObservationOmission mutation pass.

use std::collections::BTreeMap;

use crate::dsl::TraceSpec;
use crate::error::{Result, ZkBenchError};
use crate::evidence::ExpectedVerdict;
use crate::value::Value;

use super::apply::{finish_mutation, select_primary_trace, MutationBuild};
use super::pass::{MutationApplication, MutationInput, MutationPass, MutationSafetyClass};
use super::MutationClass;

/// Deterministic ObservationOmission pass.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct ObservationOmissionPass;

impl MutationPass for ObservationOmissionPass {
    fn mutation_class(&self) -> MutationClass {
        MutationClass::ObservationOmission
    }

    fn apply(&self, input: &MutationInput<'_>) -> Result<MutationApplication> {
        let instance = input.instance;

        let target = instance
            .surface_spec
            .machine
            .observations
            .first()
            .cloned()
            .ok_or_else(|| {
                ZkBenchError::mutation(
                    "observation_omission.target",
                    "source instance declares no public observation",
                )
            })?;

        let mut primary_trace = select_primary_trace(instance).ok_or_else(|| {
            ZkBenchError::mutation(
                "observation_omission.trace",
                "source instance declares no accepted or rejected trace",
            )
        })?;

        let observation_id = target.id.clone();
        let observed_field = target.field.clone();

        // Remove the targeted observation from the mutated machine.
        let mut surface_spec = instance.surface_spec.clone();
        surface_spec
            .machine
            .observations
            .retain(|observation| observation.id != observation_id);

        // Inject a deliberately-wrong final-field expectation on the primary
        // trace so the local oracle has a concrete rejection to detect: the
        // public output commitment now disagrees with internal state by a
        // sentinel delta. We pick a value that differs from any plausible
        // counter by being one past a large negative sentinel.
        let sentinel_mismatch = Value::Int { int: i64::MIN };
        let mut final_fields: BTreeMap<String, Value> = primary_trace.expected_final_fields.clone();
        final_fields.insert(observed_field.clone(), sentinel_mismatch);
        primary_trace.expected_final_fields = final_fields.clone();

        // Mirror the trace mutation into the surface spec so the mutated
        // SurfaceSpec is internally consistent.
        replace_trace(&mut surface_spec.oracle.accepted_traces, &primary_trace);
        replace_trace(&mut surface_spec.oracle.rejected_traces, &primary_trace);

        finish_mutation(MutationBuild {
            mutation_id: format!("{}_observation_omission_{}", instance.id, observation_id),
            mutation_class: MutationClass::ObservationOmission,
            expected_verdict: ExpectedVerdict::Reject,
            safety_class: MutationSafetyClass::Diagnostic,
            source_instance_id: instance.id.clone(),
            affected_machine_id: instance.semantic_ir.machine.id.clone(),
            affected_transition_ids: Vec::new(),
            affected_guard_ids: Vec::new(),
            affected_action_ids: Vec::new(),
            affected_field_ids: vec![observed_field.clone()],
            description: format!("omitted observation '{observation_id}' on field '{observed_field}'"),
            notes: vec![
                format!("removed observation: {observation_id} ({observed_field})"),
                format!("injected sentinel final-field mismatch on '{observed_field}'"),
                "Observation omission is a diagnostic local check, not evidence that a backend's public-output commitment is unsound."
                    .to_string(),
            ],
            primary_trace,
            surface_spec,
        })
    }
}

/// Replace a trace inside a vec by id, if present.
fn replace_trace(traces: &mut [TraceSpec], replacement: &TraceSpec) {
    if let Some(stored) = traces
        .iter_mut()
        .find(|candidate| candidate.id == replacement.id)
    {
        *stored = replacement.clone();
    }
}
