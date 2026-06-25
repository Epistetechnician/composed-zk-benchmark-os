//! InvariantWeakening mutation pass.

use crate::dsl::GuardSpec;
use crate::error::{Result, ZkBenchError};
use crate::evidence::ExpectedVerdict;

use super::apply::{
    finish_mutation, guard_is_executable_expr, select_primary_trace, MutationBuild,
};
use super::pass::{MutationApplication, MutationInput, MutationPass, MutationSafetyClass};
use super::MutationClass;

/// Deterministic InvariantWeakening pass.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct InvariantWeakeningPass;

impl MutationPass for InvariantWeakeningPass {
    fn mutation_class(&self) -> MutationClass {
        MutationClass::InvariantWeakening
    }

    fn apply(&self, input: &MutationInput<'_>) -> Result<MutationApplication> {
        let instance = input.instance;

        let target = instance
            .surface_spec
            .machine
            .invariants
            .iter()
            .find(|invariant| guard_is_executable_expr(&invariant.guard))
            .ok_or_else(|| {
                ZkBenchError::mutation(
                    "invariant_weakening.target",
                    "no invariant with a non-trivial executable guard was eligible",
                )
            })?;

        let primary_trace = select_primary_trace(instance).ok_or_else(|| {
            ZkBenchError::mutation(
                "invariant_weakening.trace",
                "source instance declares no accepted or rejected trace",
            )
        })?;

        let invariant_id = target.id.clone();
        let before_guard = target.guard.clone();
        let mut surface_spec = instance.surface_spec.clone();
        let invariant = super::apply::invariant_mut(&mut surface_spec, &invariant_id)?;
        invariant.guard = GuardSpec::Bool(true);

        finish_mutation(MutationBuild {
            mutation_id: format!("{}_invariant_weakening_{}", instance.id, invariant_id),
            mutation_class: MutationClass::InvariantWeakening,
            expected_verdict: ExpectedVerdict::UnsoundIfAccepted,
            safety_class: MutationSafetyClass::Malicious,
            source_instance_id: instance.id.clone(),
            affected_machine_id: instance.semantic_ir.machine.id.clone(),
            affected_transition_ids: Vec::new(),
            affected_guard_ids: vec![format!("{invariant_id}.guard")],
            affected_action_ids: Vec::new(),
            affected_field_ids: Vec::new(),
            description: format!("weakened invariant '{invariant_id}' to Bool(true)"),
            notes: vec![
                format!("before guard: {before_guard:?}"),
                "after guard: Bool(true)".to_string(),
                "Weakening an invariant and observing a backend accept an originally rejected trace is an unsound acceptance candidate, not proof of exploit."
                    .to_string(),
            ],
            primary_trace,
            surface_spec,
        })
    }
}
