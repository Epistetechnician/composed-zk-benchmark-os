//! InvalidUnrollBounds mutation pass.

use crate::dsl::{GuardExpr, GuardSpec};
use crate::error::{Result, ZkBenchError};
use crate::evidence::ExpectedVerdict;

use super::apply::{
    finish_mutation, guard_is_executable_expr, select_primary_trace, MutationBuild,
};
use super::pass::{MutationApplication, MutationInput, MutationPass, MutationSafetyClass};
use super::MutationClass;

/// Deterministic InvalidUnrollBounds pass.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct InvalidUnrollBoundsPass;

impl MutationPass for InvalidUnrollBoundsPass {
    fn mutation_class(&self) -> MutationClass {
        MutationClass::InvalidUnrollBounds
    }

    fn apply(&self, input: &MutationInput<'_>) -> Result<MutationApplication> {
        let instance = input.instance;

        let target = instance
            .surface_spec
            .machine
            .loops
            .iter()
            .find(|entry| {
                !entry.body.is_empty()
                    && entry
                        .bound
                        .as_ref()
                        .map(guard_is_executable_expr)
                        .unwrap_or(false)
            })
            .ok_or_else(|| {
                ZkBenchError::mutation(
                    "invalid_unroll_bounds.target",
                    "no loop with a non-empty body and an executable bound was eligible",
                )
            })?;

        let primary_trace = select_primary_trace(instance).ok_or_else(|| {
            ZkBenchError::mutation(
                "invalid_unroll_bounds.trace",
                "source instance declares no accepted or rejected trace",
            )
        })?;

        let loop_id = target.id.clone();
        let before_bound = target.bound.clone().ok_or_else(|| {
            ZkBenchError::mutation(
                "invalid_unroll_bounds.bound",
                "selected loop unexpectedly had no bound",
            )
        })?;

        let after_bound = negate_bound(&before_bound);

        let mut surface_spec = instance.surface_spec.clone();
        let entry = super::apply::loop_mut(&mut surface_spec, &loop_id)?;
        entry.bound = Some(after_bound.clone());

        finish_mutation(MutationBuild {
            mutation_id: format!("{}_invalid_unroll_bounds_{}", instance.id, loop_id),
            mutation_class: MutationClass::InvalidUnrollBounds,
            expected_verdict: ExpectedVerdict::Reject,
            safety_class: MutationSafetyClass::NearValid,
            source_instance_id: instance.id.clone(),
            affected_machine_id: instance.semantic_ir.machine.id.clone(),
            affected_transition_ids: Vec::new(),
            affected_guard_ids: vec![format!("{loop_id}.bound")],
            affected_action_ids: Vec::new(),
            affected_field_ids: Vec::new(),
            description: format!("negated loop bound on '{loop_id}'"),
            notes: vec![
                format!("before bound: {before_bound:?}"),
                format!("after bound: {after_bound:?}"),
                "An invalid unroll bound produces a near-valid rejection candidate and does not establish that any backend mishandles loops."
                    .to_string(),
            ],
            primary_trace,
            surface_spec,
        })
    }
}

/// Negate an executable bound. If the bound is an executable expression we wrap
/// it in a logical `Not`. If it is a `Bool` literal (which the selector rules
/// out but is conceptually possible) we flip it. Raw-text bounds are passed
/// through unchanged; they would have been rejected by the selector.
fn negate_bound(bound: &GuardSpec) -> GuardSpec {
    match bound {
        GuardSpec::Bool(value) => GuardSpec::Bool(!value),
        GuardSpec::Expr(GuardExpr::RawText { raw_text }) => GuardSpec::Expr(GuardExpr::RawText {
            raw_text: raw_text.clone(),
        }),
        GuardSpec::Expr(expr) => GuardSpec::Expr(GuardExpr::Not {
            not: Box::new(GuardSpec::Expr(expr.clone())),
        }),
    }
}
