//! RecursionEnvelopeMismatch mutation pass.

use crate::error::{Result, ZkBenchError};
use crate::evidence::ExpectedVerdict;
use crate::value::Value;

use super::apply::{finish_mutation, loop_mut, select_primary_trace, MutationBuild};
use super::pass::{MutationApplication, MutationInput, MutationPass, MutationSafetyClass};
use super::MutationClass;

/// Deterministic RecursionEnvelopeMismatch pass.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct RecursionEnvelopeMismatchPass;

impl MutationPass for RecursionEnvelopeMismatchPass {
    fn mutation_class(&self) -> MutationClass {
        MutationClass::RecursionEnvelopeMismatch
    }

    fn apply(&self, input: &MutationInput<'_>) -> Result<MutationApplication> {
        let instance = input.instance;
        let primary_trace = select_primary_trace(instance).ok_or_else(|| {
            ZkBenchError::mutation(
                "recursion_envelope_mismatch.target",
                "no declared trace was eligible",
            )
        })?;
        let loop_id = instance
            .surface_spec
            .machine
            .loops
            .first()
            .map(|entry| entry.id.clone())
            .ok_or_else(|| {
                ZkBenchError::mutation("recursion_envelope_mismatch.target", "no loop was eligible")
            })?;

        let mut surface_spec = instance.surface_spec.clone();
        let entry = loop_mut(&mut surface_spec, &loop_id)?;
        let before = entry
            .metadata
            .get("max_unroll")
            .cloned()
            .or_else(|| entry.metadata.get("envelope_digest").cloned());
        entry.metadata.insert(
            "envelope_digest".to_string(),
            Value::Text {
                text: "mismatched-envelope-digest".to_string(),
            },
        );
        entry
            .metadata
            .insert("max_unroll".to_string(), Value::Int { int: 0 });

        finish_mutation(MutationBuild {
            mutation_id: format!("{}_recursion_envelope_mismatch_{loop_id}", instance.id),
            mutation_class: MutationClass::RecursionEnvelopeMismatch,
            expected_verdict: ExpectedVerdict::Reject,
            safety_class: MutationSafetyClass::Malicious,
            source_instance_id: instance.id.clone(),
            affected_machine_id: instance.semantic_ir.machine.id.clone(),
            affected_transition_ids: Vec::new(),
            affected_guard_ids: vec![format!("{loop_id}.bound")],
            affected_action_ids: Vec::new(),
            affected_field_ids: Vec::new(),
            description: format!("corrupted recursion envelope metadata on loop '{loop_id}'"),
            notes: vec![
                format!("before envelope metadata: {before:?}"),
                "after envelope_digest: mismatched-envelope-digest".to_string(),
                "after max_unroll: 0".to_string(),
            ],
            primary_trace,
            surface_spec,
        })
    }
}
