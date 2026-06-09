//! Static validation for Surface DSL specs.

use std::collections::{BTreeSet, HashSet};

use crate::error::{Result, ZkBenchError};
use crate::evidence::ClaimBoundary;
use crate::ids::is_non_empty_id;

use super::expr::{ActionSpec, GuardSpec};
use super::surface::{SurfaceSpec, TraceSpec};

/// Validate the Surface DSL before lowering.
pub fn validate_surface_spec(spec: &SurfaceSpec) -> Result<()> {
    if !is_non_empty_id(&spec.machine.id) {
        return Err(ZkBenchError::validation(
            "machine.id",
            "machine id is empty",
        ));
    }

    let state_ids = unique_ids(
        spec.machine.states.iter().map(|state| state.id.as_str()),
        "machine.states",
    )?;
    let field_ids = unique_ids(
        spec.machine.fields.iter().map(|field| field.id.as_str()),
        "machine.fields",
    )?;
    let transition_ids = unique_ids(
        spec.machine
            .transitions
            .iter()
            .map(|transition| transition.id.as_str()),
        "machine.transitions",
    )?;

    if !state_ids.contains(spec.machine.initial_state.as_str()) {
        return Err(ZkBenchError::validation(
            "machine.initial_state",
            format!(
                "initial state '{}' is not declared",
                spec.machine.initial_state
            ),
        ));
    }

    for field in &spec.machine.fields {
        if let Some(initial) = &field.initial {
            if !initial.matches_type(&field.field_type) {
                return Err(ZkBenchError::validation(
                    format!("machine.fields.{}", field.id),
                    "initial value does not match declared field type",
                ));
            }
        }
    }

    for transition in &spec.machine.transitions {
        if !state_ids.contains(transition.from.as_str()) {
            return Err(ZkBenchError::validation(
                format!("machine.transitions.{}.from", transition.id),
                format!("source state '{}' is not declared", transition.from),
            ));
        }
        if !state_ids.contains(transition.to.as_str()) {
            return Err(ZkBenchError::validation(
                format!("machine.transitions.{}.to", transition.id),
                format!("target state '{}' is not declared", transition.to),
            ));
        }
        validate_guard_references(
            &transition.guard,
            &field_ids,
            &format!("machine.transitions.{}.guard", transition.id),
        )?;
        for (index, action) in transition.actions.iter().enumerate() {
            validate_action_references(
                action,
                &field_ids,
                &format!("machine.transitions.{}.actions[{}]", transition.id, index),
            )?;
        }
    }

    for invariant in &spec.machine.invariants {
        validate_guard_references(
            &invariant.guard,
            &field_ids,
            &format!("machine.invariants.{}", invariant.id),
        )?;
    }

    for observation in &spec.machine.observations {
        if !field_ids.contains(observation.field.as_str()) {
            return Err(ZkBenchError::validation(
                format!("machine.observations.{}", observation.id),
                format!("observed field '{}' is not declared", observation.field),
            ));
        }
    }

    for public_input in &spec.machine.public_inputs {
        if !field_ids.contains(public_input.field.as_str()) {
            return Err(ZkBenchError::validation(
                format!("machine.public_inputs.{}", public_input.id),
                format!(
                    "public input field '{}' is not declared",
                    public_input.field
                ),
            ));
        }
    }

    for private_witness in &spec.machine.private_witnesses {
        if !field_ids.contains(private_witness.field.as_str()) {
            return Err(ZkBenchError::validation(
                format!("machine.private_witnesses.{}", private_witness.id),
                format!(
                    "private witness field '{}' is not declared",
                    private_witness.field
                ),
            ));
        }
    }

    for field_id in &spec.machine.witness_policy.public_inputs {
        if !field_ids.contains(field_id.as_str()) {
            return Err(ZkBenchError::validation(
                "machine.witness_policy.public_inputs",
                format!("public input field '{field_id}' is not declared"),
            ));
        }
    }
    for field_id in &spec.machine.witness_policy.private_witnesses {
        if !field_ids.contains(field_id.as_str()) {
            return Err(ZkBenchError::validation(
                "machine.witness_policy.private_witnesses",
                format!("private witness field '{field_id}' is not declared"),
            ));
        }
    }

    for trace in &spec.oracle.accepted_traces {
        validate_trace(
            trace,
            &state_ids,
            &field_ids,
            &transition_ids,
            "accepted_traces",
        )?;
    }
    for trace in &spec.oracle.rejected_traces {
        validate_trace(
            trace,
            &state_ids,
            &field_ids,
            &transition_ids,
            "rejected_traces",
        )?;
    }

    unique_ids(
        spec.mutations.iter().map(|mutation| mutation.id.as_str()),
        "mutations",
    )?;
    unique_ids(
        spec.targets.iter().map(|target| target.id.as_str()),
        "targets",
    )?;

    if spec.evidence.claim_boundary > ClaimBoundary::Level1LocalReplay && !spec.evidence.planned {
        return Err(ZkBenchError::ClaimBoundary {
            message: format!(
                "actual evidence claim boundary {:?} exceeds Level1LocalReplay",
                spec.evidence.claim_boundary
            ),
        });
    }

    Ok(())
}

fn validate_trace(
    trace: &TraceSpec,
    state_ids: &HashSet<&str>,
    field_ids: &HashSet<&str>,
    transition_ids: &HashSet<&str>,
    trace_group: &str,
) -> Result<()> {
    if !is_non_empty_id(&trace.id) {
        return Err(ZkBenchError::validation(
            format!("oracle.{trace_group}.id"),
            "trace id is empty",
        ));
    }

    if let Some(initial_state) = &trace.initial_state {
        if !state_ids.contains(initial_state.as_str()) {
            return Err(ZkBenchError::validation(
                format!("oracle.{trace_group}.{}.initial_state", trace.id),
                format!("initial state '{initial_state}' is not declared"),
            ));
        }
    }

    if let Some(final_state) = &trace.expected_final_state {
        if !state_ids.contains(final_state.as_str()) {
            return Err(ZkBenchError::validation(
                format!("oracle.{trace_group}.{}.expected_final_state", trace.id),
                format!("expected final state '{final_state}' is not declared"),
            ));
        }
    }

    for field in trace.initial_fields.keys() {
        if !field_ids.contains(field.as_str()) {
            return Err(ZkBenchError::validation(
                format!("oracle.{trace_group}.{}.initial_fields", trace.id),
                format!("initial field '{field}' is not declared"),
            ));
        }
    }

    for field in trace.expected_final_fields.keys() {
        if !field_ids.contains(field.as_str()) {
            return Err(ZkBenchError::validation(
                format!("oracle.{trace_group}.{}.expected_final_fields", trace.id),
                format!("expected field '{field}' is not declared"),
            ));
        }
    }

    for step in &trace.steps {
        if !transition_ids.contains(step.transition.as_str()) {
            return Err(ZkBenchError::validation(
                format!("oracle.{trace_group}.{}.steps", trace.id),
                format!("transition '{}' is not declared", step.transition),
            ));
        }
    }

    Ok(())
}

fn unique_ids<'a>(
    ids: impl Iterator<Item = &'a str>,
    path: &'static str,
) -> Result<HashSet<&'a str>> {
    let mut seen = HashSet::new();
    for id in ids {
        if !is_non_empty_id(id) {
            return Err(ZkBenchError::validation(path, "encountered empty id"));
        }
        if !seen.insert(id) {
            return Err(ZkBenchError::validation(
                path,
                format!("duplicate id '{id}'"),
            ));
        }
    }
    Ok(seen)
}

fn validate_guard_references(
    guard: &GuardSpec,
    field_ids: &HashSet<&str>,
    path: &str,
) -> Result<()> {
    let mut refs = BTreeSet::new();
    guard.collect_field_references(&mut refs);
    for field in refs {
        if !field_ids.contains(field.as_str()) {
            return Err(ZkBenchError::validation(
                path,
                format!("guard references unknown field '{field}'"),
            ));
        }
    }
    Ok(())
}

fn validate_action_references(
    action: &ActionSpec,
    field_ids: &HashSet<&str>,
    path: &str,
) -> Result<()> {
    let mut refs = BTreeSet::new();
    action.collect_field_references(&mut refs);
    for field in refs {
        if !field_ids.contains(field.as_str()) {
            return Err(ZkBenchError::validation(
                path,
                format!("action references unknown field '{field}'"),
            ));
        }
    }
    Ok(())
}
