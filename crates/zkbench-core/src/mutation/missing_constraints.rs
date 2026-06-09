//! MissingConstraints mutation pass.

use crate::dsl::GuardSpec;
use crate::error::{Result, ZkBenchError};
use crate::evidence::ExpectedVerdict;

use super::apply::{finish_mutation, guard_is_true, transition, transition_mut, MutationBuild};
use super::pass::{MutationApplication, MutationInput, MutationPass, MutationSafetyClass};
use super::MutationClass;

/// Deterministic MissingConstraints pass.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct MissingConstraintsPass;

impl MutationPass for MissingConstraintsPass {
    fn mutation_class(&self) -> MutationClass {
        MutationClass::MissingConstraints
    }

    fn apply(&self, input: &MutationInput<'_>) -> Result<MutationApplication> {
        let instance = input.instance;
        let mut selected = None;
        for trace in &instance.rejected_traces {
            for step in &trace.steps {
                if let Some(candidate) = transition(&instance.surface_spec, &step.transition) {
                    if !guard_is_true(&candidate.guard) {
                        selected =
                            Some((trace.clone(), candidate.id.clone(), candidate.guard.clone()));
                        break;
                    }
                }
            }
            if selected.is_some() {
                break;
            }
        }

        let (primary_trace, transition_id, before_guard) = selected.ok_or_else(|| {
            ZkBenchError::mutation(
                "missing_constraints.target",
                "no rejected trace step with a non-trivial guard was eligible",
            )
        })?;

        let mut surface_spec = instance.surface_spec.clone();
        transition_mut(&mut surface_spec, &transition_id)?.guard = GuardSpec::Bool(true);

        finish_mutation(MutationBuild {
            mutation_id: format!("{}_missing_constraints_{}", instance.id, transition_id),
            mutation_class: MutationClass::MissingConstraints,
            expected_verdict: ExpectedVerdict::UnsoundIfAccepted,
            safety_class: MutationSafetyClass::Malicious,
            source_instance_id: instance.id.clone(),
            affected_machine_id: instance.semantic_ir.machine.id.clone(),
            affected_transition_ids: vec![transition_id.clone()],
            affected_guard_ids: vec![format!("{transition_id}.guard")],
            affected_action_ids: Vec::new(),
            affected_field_ids: Vec::new(),
            description: format!("removed guard constraint from transition '{transition_id}'"),
            notes: vec![
                format!("before guard: {before_guard:?}"),
                "after guard: Bool(true)".to_string(),
                "Acceptance of an originally rejected trace is an unsound acceptance candidate, not proof of exploit.".to_string(),
            ],
            primary_trace,
            surface_spec,
        })
    }
}
