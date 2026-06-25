//! PublicPrivateBoundaryMismatch mutation pass.

use crate::error::{Result, ZkBenchError};
use crate::evidence::ExpectedVerdict;
use crate::value::FieldVisibility;

use super::apply::{finish_mutation, select_primary_trace, MutationBuild};
use super::pass::{MutationApplication, MutationInput, MutationPass, MutationSafetyClass};
use super::MutationClass;

/// Deterministic PublicPrivateBoundaryMismatch pass.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct PublicPrivateBoundaryMismatchPass;

impl MutationPass for PublicPrivateBoundaryMismatchPass {
    fn mutation_class(&self) -> MutationClass {
        MutationClass::PublicPrivateBoundaryMismatch
    }

    fn apply(&self, input: &MutationInput<'_>) -> Result<MutationApplication> {
        let instance = input.instance;
        let primary_trace = select_primary_trace(instance).ok_or_else(|| {
            ZkBenchError::mutation(
                "public_private_boundary_mismatch.target",
                "no declared trace was eligible",
            )
        })?;

        let mut surface_spec = instance.surface_spec.clone();
        let (description, affected_field_ids) =
            if !surface_spec.machine.witness_policy.public_inputs.is_empty() {
                let stolen = surface_spec.machine.witness_policy.public_inputs.remove(0);
                surface_spec
                    .machine
                    .witness_policy
                    .private_witnesses
                    .push(stolen.clone());
                (
                    format!(
                        "moved public input '{}' into private witness policy",
                        stolen
                    ),
                    vec![stolen],
                )
            } else if let Some(field) = surface_spec
                .machine
                .fields
                .iter_mut()
                .find(|field| field.visibility == FieldVisibility::Public)
            {
                let field_id = field.id.clone();
                field.visibility = FieldVisibility::Private;
                (
                    format!("reclassified public field '{field_id}' as private"),
                    vec![field_id],
                )
            } else if let Some(observe) = surface_spec.machine.observations.first() {
                let field_id = observe.field.clone();
                if let Some(field) = surface_spec
                    .machine
                    .fields
                    .iter_mut()
                    .find(|field| field.id == field_id)
                {
                    field.visibility = FieldVisibility::Private;
                }
                (
                    format!("reclassified observed field '{field_id}' as private"),
                    vec![field_id],
                )
            } else {
                return Err(ZkBenchError::mutation(
                    "public_private_boundary_mismatch.target",
                    "no public input, public field, or observed field was eligible",
                ));
            };

        finish_mutation(MutationBuild {
            mutation_id: format!("{}_public_private_boundary_mismatch", instance.id),
            mutation_class: MutationClass::PublicPrivateBoundaryMismatch,
            expected_verdict: ExpectedVerdict::Reject,
            safety_class: MutationSafetyClass::Malicious,
            source_instance_id: instance.id.clone(),
            affected_machine_id: instance.semantic_ir.machine.id.clone(),
            affected_transition_ids: Vec::new(),
            affected_guard_ids: Vec::new(),
            affected_action_ids: Vec::new(),
            affected_field_ids,
            description,
            notes: vec![
                "Public/private boundary mismatch is a local semantic mutation only.".to_string(),
            ],
            primary_trace,
            surface_spec,
        })
    }
}
