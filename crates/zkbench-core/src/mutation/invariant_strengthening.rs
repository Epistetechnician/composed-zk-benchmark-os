//! InvariantStrengthening mutation pass.

use crate::error::{Result, ZkBenchError};
use crate::evidence::ExpectedVerdict;

use super::apply::{
    corrupt_guard, finish_mutation, guard_is_executable_expr, select_primary_trace, MutationBuild,
};
use super::pass::{MutationApplication, MutationInput, MutationPass, MutationSafetyClass};
use super::MutationClass;

/// Deterministic InvariantStrengthening pass.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct InvariantStrengtheningPass;

impl MutationPass for InvariantStrengtheningPass {
    fn mutation_class(&self) -> MutationClass {
        MutationClass::InvariantStrengthening
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
                    "invariant_strengthening.target",
                    "no invariant with a non-trivial executable guard was eligible",
                )
            })?;

        let primary_trace = select_primary_trace(instance).ok_or_else(|| {
            ZkBenchError::mutation(
                "invariant_strengthening.trace",
                "source instance declares no accepted or rejected trace",
            )
        })?;

        let invariant_id = target.id.clone();
        let before_guard = target.guard.clone();
        let after_guard = corrupt_guard(&before_guard);
        let mut surface_spec = instance.surface_spec.clone();
        let invariant = super::apply::invariant_mut(&mut surface_spec, &invariant_id)?;
        invariant.guard = after_guard.clone();

        finish_mutation(MutationBuild {
            mutation_id: format!("{}_invariant_strengthening_{}", instance.id, invariant_id),
            mutation_class: MutationClass::InvariantStrengthening,
            expected_verdict: ExpectedVerdict::Reject,
            safety_class: MutationSafetyClass::NearValid,
            source_instance_id: instance.id.clone(),
            affected_machine_id: instance.semantic_ir.machine.id.clone(),
            affected_transition_ids: Vec::new(),
            affected_guard_ids: vec![format!("{invariant_id}.guard")],
            affected_action_ids: Vec::new(),
            affected_field_ids: Vec::new(),
            description: format!("strengthened invariant '{invariant_id}' beyond valid semantics"),
            notes: vec![
                format!("before guard: {before_guard:?}"),
                format!("after guard: {after_guard:?}"),
                "Strengthening an invariant beyond valid semantics produces a near-valid rejection candidate, not a soundness finding."
                    .to_string(),
            ],
            primary_trace,
            surface_spec,
        })
    }
}
