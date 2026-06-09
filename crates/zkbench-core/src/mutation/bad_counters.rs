//! BadCounters mutation pass.

use crate::error::{Result, ZkBenchError};
use crate::evidence::ExpectedVerdict;

use super::apply::{
    bad_counter_action, finish_mutation, transition, transition_mut, MutationBuild,
};
use super::pass::{MutationApplication, MutationInput, MutationPass, MutationSafetyClass};
use super::MutationClass;

/// Deterministic BadCounters pass.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct BadCountersPass;

impl MutationPass for BadCountersPass {
    fn mutation_class(&self) -> MutationClass {
        MutationClass::BadCounters
    }

    fn apply(&self, input: &MutationInput<'_>) -> Result<MutationApplication> {
        let instance = input.instance;
        let mut selected = None;
        for trace in &instance.accepted_traces {
            for step in &trace.steps {
                if let Some(candidate) = transition(&instance.surface_spec, &step.transition) {
                    for (index, action) in candidate.actions.iter().enumerate() {
                        if let Some((after_action, note)) = bad_counter_action(action) {
                            selected = Some((
                                trace.clone(),
                                candidate.id.clone(),
                                index,
                                action.clone(),
                                after_action,
                                note,
                            ));
                            break;
                        }
                    }
                }
                if selected.is_some() {
                    break;
                }
            }
            if selected.is_some() {
                break;
            }
        }

        let (primary_trace, transition_id, action_index, before_action, after_action, note) =
            selected.ok_or_else(|| {
                ZkBenchError::mutation(
                    "bad_counters.target",
                    "no accepted trace action with an integer counter update was eligible",
                )
            })?;

        let mut surface_spec = instance.surface_spec.clone();
        let transition = transition_mut(&mut surface_spec, &transition_id)?;
        let action_slot = transition.actions.get_mut(action_index).ok_or_else(|| {
            ZkBenchError::mutation(
                "bad_counters.action_index",
                "selected action index was not available during mutation",
            )
        })?;
        *action_slot = after_action.clone();

        let affected_field_ids = match &before_action {
            crate::dsl::ActionSpec::AddAssign { add_assign } => vec![add_assign.field.clone()],
            crate::dsl::ActionSpec::SubAssign { sub_assign } => vec![sub_assign.field.clone()],
            _ => Vec::new(),
        };

        finish_mutation(MutationBuild {
            mutation_id: format!(
                "{}_bad_counters_{}_{}",
                instance.id, transition_id, action_index
            ),
            mutation_class: MutationClass::BadCounters,
            expected_verdict: ExpectedVerdict::Reject,
            safety_class: MutationSafetyClass::Diagnostic,
            source_instance_id: instance.id.clone(),
            affected_machine_id: instance.semantic_ir.machine.id.clone(),
            affected_transition_ids: vec![transition_id.clone()],
            affected_guard_ids: Vec::new(),
            affected_action_ids: vec![format!("{transition_id}.actions[{action_index}]")],
            affected_field_ids,
            description: format!("corrupted counter action on transition '{transition_id}'"),
            notes: vec![
                format!("before action: {before_action:?}"),
                format!("after action: {after_action:?}"),
                note,
            ],
            primary_trace,
            surface_spec,
        })
    }
}
