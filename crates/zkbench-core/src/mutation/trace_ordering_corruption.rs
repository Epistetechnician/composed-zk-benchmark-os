//! TraceOrderingCorruption mutation pass.

use crate::error::{Result, ZkBenchError};
use crate::evidence::ExpectedVerdict;

use super::apply::{finish_mutation, MutationBuild};
use super::pass::{MutationApplication, MutationInput, MutationPass, MutationSafetyClass};
use super::MutationClass;

/// Deterministic TraceOrderingCorruption pass.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct TraceOrderingCorruptionPass;

impl MutationPass for TraceOrderingCorruptionPass {
    fn mutation_class(&self) -> MutationClass {
        MutationClass::TraceOrderingCorruption
    }

    fn apply(&self, input: &MutationInput<'_>) -> Result<MutationApplication> {
        let instance = input.instance;
        let mut primary_trace = instance.accepted_traces.first().cloned().ok_or_else(|| {
            ZkBenchError::mutation(
                "trace_ordering_corruption.target",
                "no accepted trace was eligible",
            )
        })?;
        if primary_trace.steps.len() < 2 {
            return Err(ZkBenchError::mutation(
                "trace_ordering_corruption.target",
                "accepted trace must contain at least two steps",
            ));
        }
        primary_trace.steps.swap(0, 1);
        let first = primary_trace.steps[0].transition.clone();
        let second = primary_trace.steps[1].transition.clone();

        finish_mutation(MutationBuild {
            mutation_id: format!("{}_trace_ordering_corruption", instance.id),
            mutation_class: MutationClass::TraceOrderingCorruption,
            expected_verdict: ExpectedVerdict::Reject,
            safety_class: MutationSafetyClass::Malicious,
            source_instance_id: instance.id.clone(),
            affected_machine_id: instance.semantic_ir.machine.id.clone(),
            affected_transition_ids: vec![first.clone(), second.clone()],
            affected_guard_ids: Vec::new(),
            affected_action_ids: Vec::new(),
            affected_field_ids: Vec::new(),
            description: format!("swapped trace steps '{first}' and '{second}'"),
            notes: vec!["Trace ordering corruption mutates the primary trace only.".to_string()],
            primary_trace,
            surface_spec: instance.surface_spec.clone(),
        })
    }
}
