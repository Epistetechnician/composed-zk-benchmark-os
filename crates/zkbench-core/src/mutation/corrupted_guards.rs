//! CorruptedGuards mutation pass.

use crate::error::{Result, ZkBenchError};
use crate::evidence::ExpectedVerdict;

use super::apply::{corrupt_guard, finish_mutation, transition, transition_mut, MutationBuild};
use super::pass::{MutationApplication, MutationInput, MutationPass, MutationSafetyClass};
use super::MutationClass;

/// Deterministic CorruptedGuards pass.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct CorruptedGuardsPass;

impl MutationPass for CorruptedGuardsPass {
    fn mutation_class(&self) -> MutationClass {
        MutationClass::CorruptedGuards
    }

    fn apply(&self, input: &MutationInput<'_>) -> Result<MutationApplication> {
        let instance = input.instance;
        let mut selected = None;
        for trace in &instance.accepted_traces {
            for step in trace.steps.iter().rev() {
                if let Some(candidate) = transition(&instance.surface_spec, &step.transition) {
                    let corrupted = corrupt_guard(&candidate.guard);
                    if corrupted != candidate.guard {
                        selected = Some((
                            trace.clone(),
                            candidate.id.clone(),
                            candidate.guard.clone(),
                            corrupted,
                        ));
                        break;
                    }
                }
            }
            if selected.is_some() {
                break;
            }
        }

        let (primary_trace, transition_id, before_guard, after_guard) =
            selected.ok_or_else(|| {
                ZkBenchError::mutation(
                    "corrupted_guards.target",
                    "no accepted trace step with an executable guard was eligible",
                )
            })?;

        let mut surface_spec = instance.surface_spec.clone();
        transition_mut(&mut surface_spec, &transition_id)?.guard = after_guard.clone();

        finish_mutation(MutationBuild {
            mutation_id: format!("{}_corrupted_guards_{}", instance.id, transition_id),
            mutation_class: MutationClass::CorruptedGuards,
            expected_verdict: ExpectedVerdict::Reject,
            safety_class: MutationSafetyClass::NearValid,
            source_instance_id: instance.id.clone(),
            affected_machine_id: instance.semantic_ir.machine.id.clone(),
            affected_transition_ids: vec![transition_id.clone()],
            affected_guard_ids: vec![format!("{transition_id}.guard")],
            affected_action_ids: Vec::new(),
            affected_field_ids: Vec::new(),
            description: format!("corrupted guard on transition '{transition_id}'"),
            notes: vec![
                format!("before guard: {before_guard:?}"),
                format!("after guard: {after_guard:?}"),
            ],
            primary_trace,
            surface_spec,
        })
    }
}
