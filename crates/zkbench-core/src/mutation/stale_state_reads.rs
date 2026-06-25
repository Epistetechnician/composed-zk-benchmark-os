//! StaleStateReads mutation pass.
//!
//! Mutates a trace (not the machine) by swapping the first two ordered steps
//! where the first step writes a field that the second step's transition reads
//! in a guard, so the read happens before the write.

use std::collections::BTreeSet;

use crate::error::{Result, ZkBenchError};
use crate::evidence::ExpectedVerdict;

use super::apply::{
    action_write_fields, finish_mutation, guard_read_fields, transition, MutationBuild,
};
use super::pass::{MutationApplication, MutationInput, MutationPass, MutationSafetyClass};
use super::MutationClass;

/// Deterministic StaleStateReads pass.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct StaleStateReadsPass;

impl MutationPass for StaleStateReadsPass {
    fn mutation_class(&self) -> MutationClass {
        MutationClass::StaleStateReads
    }

    fn apply(&self, input: &MutationInput<'_>) -> Result<MutationApplication> {
        let instance = input.instance;

        let mut selected = None;
        for trace in &instance.accepted_traces {
            for window in trace.steps.windows(2) {
                let first_step = &window[0];
                let second_step = &window[1];
                let first_transition =
                    match transition(&instance.surface_spec, &first_step.transition) {
                        Some(t) => t,
                        None => continue,
                    };
                let second_transition =
                    match transition(&instance.surface_spec, &second_step.transition) {
                        Some(t) => t,
                        None => continue,
                    };

                let writes: BTreeSet<String> = first_transition
                    .actions
                    .iter()
                    .flat_map(action_write_fields)
                    .collect();
                if writes.is_empty() {
                    continue;
                }
                let reads = guard_read_fields(&second_transition.guard);
                if reads.is_empty() {
                    continue;
                }
                if writes.intersection(&reads).next().is_none() {
                    continue;
                }

                selected = Some((
                    trace.clone(),
                    window_index(trace.steps.len()),
                    first_step.transition.clone(),
                    second_step.transition.clone(),
                    writes.intersection(&reads).cloned().collect::<Vec<_>>(),
                ));
                break;
            }
            if selected.is_some() {
                break;
            }
        }

        let (mut primary_trace, swap_index, first_id, second_id, shared_fields) = selected
            .ok_or_else(|| {
                ZkBenchError::mutation(
                    "stale_state_reads.target",
                    "no accepted trace step pair with a write-then-read dependency was eligible",
                )
            })?;

        primary_trace.steps.swap(swap_index, swap_index + 1);

        let mut surface_spec = instance.surface_spec.clone();
        // Replace the matching trace inside the spec's accepted traces so the
        // mutated surface carries the reordered trace.
        if let Some(stored) = surface_spec
            .oracle
            .accepted_traces
            .iter_mut()
            .find(|candidate| candidate.id == primary_trace.id)
        {
            *stored = primary_trace.clone();
        }

        finish_mutation(MutationBuild {
            mutation_id: format!(
                "{}_stale_state_reads_{}_{}_{}",
                instance.id, primary_trace.id, first_id, second_id
            ),
            mutation_class: MutationClass::StaleStateReads,
            expected_verdict: ExpectedVerdict::Reject,
            safety_class: MutationSafetyClass::Diagnostic,
            source_instance_id: instance.id.clone(),
            affected_machine_id: instance.semantic_ir.machine.id.clone(),
            affected_transition_ids: vec![first_id.clone(), second_id.clone()],
            affected_guard_ids: vec![format!("{second_id}.guard")],
            affected_action_ids: vec![format!("{first_id}.actions")],
            affected_field_ids: shared_fields,
            description: format!(
                "swapped trace '{}' steps '{}' and '{}' so the guard reads stale state",
                primary_trace.id, first_id, second_id
            ),
            notes: vec![
                format!("first step transition: {first_id}"),
                format!("second step transition: {second_id}"),
                "A stale-state-read rejection is a local oracle observation, not proof that any backend is unsound."
                    .to_string(),
            ],
            primary_trace,
            surface_spec,
        })
    }
}

/// Return the index of the first element of the first window (always 0). Kept
/// as a function so the intent is explicit at the call site.
fn window_index(_len: usize) -> usize {
    0
}
