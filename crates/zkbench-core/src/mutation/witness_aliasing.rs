//! WitnessAliasing mutation pass.

use crate::dsl::PrivateWitnessSpec;
use crate::error::{Result, ZkBenchError};
use crate::evidence::ExpectedVerdict;

use super::apply::{finish_mutation, select_primary_trace, MutationBuild};
use super::pass::{MutationApplication, MutationInput, MutationPass, MutationSafetyClass};
use super::MutationClass;

/// Deterministic WitnessAliasing pass.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct WitnessAliasingPass;

impl MutationPass for WitnessAliasingPass {
    fn mutation_class(&self) -> MutationClass {
        MutationClass::WitnessAliasing
    }

    fn apply(&self, input: &MutationInput<'_>) -> Result<MutationApplication> {
        let instance = input.instance;
        let primary_trace = select_primary_trace(instance).ok_or_else(|| {
            ZkBenchError::mutation("witness_aliasing.target", "no declared trace was eligible")
        })?;

        let mut surface_spec = instance.surface_spec.clone();
        surface_spec.machine.witness_policy.aliasing_allowed = true;

        let (witness_id, field_id) =
            if let Some(first) = surface_spec.machine.private_witnesses.first() {
                (first.id.clone(), first.field.clone())
            } else if let Some(field) = surface_spec.machine.fields.first() {
                (format!("private_{}", field.id), field.id.clone())
            } else {
                return Err(ZkBenchError::mutation(
                    "witness_aliasing.target",
                    "no private witness or field was eligible",
                ));
            };

        let alias_id = format!("{witness_id}_alias");
        surface_spec
            .machine
            .private_witnesses
            .push(PrivateWitnessSpec {
                id: alias_id.clone(),
                field: field_id.clone(),
                description: Some("aliased private witness slot".to_string()),
            });
        surface_spec
            .machine
            .witness_policy
            .private_witnesses
            .push(field_id.clone());

        finish_mutation(MutationBuild {
            mutation_id: format!("{}_witness_aliasing_{witness_id}", instance.id),
            mutation_class: MutationClass::WitnessAliasing,
            expected_verdict: ExpectedVerdict::Reject,
            safety_class: MutationSafetyClass::Malicious,
            source_instance_id: instance.id.clone(),
            affected_machine_id: instance.semantic_ir.machine.id.clone(),
            affected_transition_ids: Vec::new(),
            affected_guard_ids: Vec::new(),
            affected_action_ids: Vec::new(),
            affected_field_ids: vec![field_id],
            description: format!("aliased private witness slots for '{witness_id}'"),
            notes: vec![
                format!("added aliased witness '{alias_id}'"),
                "witness_policy.aliasing_allowed set to true".to_string(),
            ],
            primary_trace,
            surface_spec,
        })
    }
}
