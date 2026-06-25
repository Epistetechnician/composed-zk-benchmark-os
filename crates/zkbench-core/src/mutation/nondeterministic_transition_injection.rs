//! NondeterministicTransitionInjection mutation pass.

use crate::dsl::{GuardSpec, TransitionSpec};
use crate::error::{Result, ZkBenchError};
use crate::evidence::ExpectedVerdict;

use super::apply::{finish_mutation, select_primary_trace, MutationBuild};
use super::pass::{MutationApplication, MutationInput, MutationPass, MutationSafetyClass};
use super::MutationClass;

/// Deterministic NondeterministicTransitionInjection pass.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct NondeterministicTransitionInjectionPass;

impl MutationPass for NondeterministicTransitionInjectionPass {
    fn mutation_class(&self) -> MutationClass {
        MutationClass::NondeterministicTransitionInjection
    }

    fn apply(&self, input: &MutationInput<'_>) -> Result<MutationApplication> {
        let instance = input.instance;
        let primary_trace = select_primary_trace(instance).ok_or_else(|| {
            ZkBenchError::mutation(
                "nondeterministic_transition_injection.target",
                "no declared trace was eligible",
            )
        })?;
        let first_transition = instance
            .surface_spec
            .machine
            .transitions
            .first()
            .ok_or_else(|| {
                ZkBenchError::mutation(
                    "nondeterministic_transition_injection.target",
                    "no transition was eligible",
                )
            })?;
        let bypass_target = instance
            .surface_spec
            .machine
            .states
            .last()
            .map(|state| state.id.clone())
            .filter(|target| target != &first_transition.to)
            .ok_or_else(|| {
                ZkBenchError::mutation(
                    "nondeterministic_transition_injection.target",
                    "no bypass target state was eligible",
                )
            })?;

        let injected_id = "injected_nondeterministic".to_string();
        let mut surface_spec = instance.surface_spec.clone();
        surface_spec.machine.transitions.push(TransitionSpec {
            id: injected_id.clone(),
            from: first_transition.from.clone(),
            to: bypass_target.clone(),
            guard: GuardSpec::Bool(true),
            actions: Vec::new(),
        });

        finish_mutation(MutationBuild {
            mutation_id: format!("{}_nondeterministic_transition_injection", instance.id),
            mutation_class: MutationClass::NondeterministicTransitionInjection,
            expected_verdict: ExpectedVerdict::Reject,
            safety_class: MutationSafetyClass::Malicious,
            source_instance_id: instance.id.clone(),
            affected_machine_id: instance.semantic_ir.machine.id.clone(),
            affected_transition_ids: vec![injected_id.clone()],
            affected_guard_ids: vec![format!("{injected_id}.guard")],
            affected_action_ids: Vec::new(),
            affected_field_ids: Vec::new(),
            description: format!(
                "injected unconditional transition '{injected_id}' from '{}' to '{bypass_target}'",
                first_transition.from
            ),
            notes: vec![
                "Injected transition is outside the declared semantic relation.".to_string(),
            ],
            primary_trace,
            surface_spec,
        })
    }
}
