//! SemanticNoOpDrift mutation pass.

use crate::dsl::{ActionSpec, AssignAction, OperandSpec};
use crate::error::{Result, ZkBenchError};
use crate::evidence::ExpectedVerdict;
use crate::value::Value;

use super::apply::{finish_mutation, guard_is_true, select_primary_trace, MutationBuild};
use super::pass::{MutationApplication, MutationInput, MutationPass, MutationSafetyClass};
use super::MutationClass;

/// Deterministic SemanticNoOpDrift pass.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct SemanticNoOpDriftPass;

impl MutationPass for SemanticNoOpDriftPass {
    fn mutation_class(&self) -> MutationClass {
        MutationClass::SemanticNoOpDrift
    }

    fn apply(&self, input: &MutationInput<'_>) -> Result<MutationApplication> {
        let instance = input.instance;
        let primary_trace = select_primary_trace(instance).ok_or_else(|| {
            ZkBenchError::mutation(
                "semantic_no_op_drift.target",
                "no declared trace was eligible",
            )
        })?;

        let mut selected = None;
        for (transition_index, transition) in
            instance.surface_spec.machine.transitions.iter().enumerate()
        {
            if !guard_is_true(&transition.guard) {
                continue;
            }
            for (index, action) in transition.actions.iter().enumerate() {
                if let ActionSpec::Noop { .. } = action {
                    selected = Some((transition_index, transition.id.clone(), index));
                    break;
                }
            }
            if selected.is_some() {
                break;
            }
        }

        let (transition_index, transition_id, action_index, inserted) =
            if let Some(found) = selected {
                (found.0, found.1, found.2, false)
            } else if let Some(transition) = instance
                .surface_spec
                .machine
                .transitions
                .iter()
                .enumerate()
                .find(|transition| guard_is_true(&transition.1.guard))
            {
                (
                    transition.0,
                    transition.1.id.clone(),
                    transition.1.actions.len(),
                    true,
                )
            } else {
                return Err(ZkBenchError::mutation(
                    "semantic_no_op_drift.target",
                    "no guarded transition with a replaceable action was eligible",
                ));
            };

        let field_id = instance
            .surface_spec
            .machine
            .fields
            .iter()
            .find(|field| matches!(field.field_type, crate::value::ValueType::Int))
            .map(|field| field.id.clone())
            .ok_or_else(|| {
                ZkBenchError::mutation(
                    "semantic_no_op_drift.target",
                    "no integer field was eligible",
                )
            })?;

        let mut surface_spec = instance.surface_spec.clone();
        let transition = &mut surface_spec.machine.transitions[transition_index];
        let before = transition.actions.get(action_index).cloned();
        let replacement = ActionSpec::Assign {
            assign: AssignAction {
                field: field_id.clone(),
                value: OperandSpec::Literal(Value::Int { int: -1 }),
            },
        };
        if inserted {
            transition.actions.push(replacement);
        } else {
            transition.actions[action_index] = replacement;
        }

        finish_mutation(MutationBuild {
            mutation_id: format!("{}_semantic_no_op_drift_{transition_id}", instance.id),
            mutation_class: MutationClass::SemanticNoOpDrift,
            expected_verdict: ExpectedVerdict::Reject,
            safety_class: MutationSafetyClass::Malicious,
            source_instance_id: instance.id.clone(),
            affected_machine_id: instance.semantic_ir.machine.id.clone(),
            affected_transition_ids: vec![transition_id.clone()],
            affected_guard_ids: vec![format!("{transition_id}.guard")],
            affected_action_ids: vec![format!("{transition_id}.actions[{action_index}]")],
            affected_field_ids: vec![field_id.clone()],
            description: format!(
                "replaced action on transition '{transition_id}' with hidden semantic drift"
            ),
            notes: vec![
                format!("before action: {before:?}"),
                format!("after action: assign {field_id} := -1"),
            ],
            primary_trace,
            surface_spec,
        })
    }
}
