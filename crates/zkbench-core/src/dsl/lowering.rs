//! Lowering from Parsed AST to canonical Semantic IR.

use crate::error::Result;

use super::ast::ParsedAst;
use super::ir::{
    CanonicalAction, CanonicalField, CanonicalGuard, CanonicalInvariant, CanonicalMachine,
    CanonicalOracle, CanonicalState, CanonicalTransition, SemanticIr,
};
use super::validation::validate_surface_spec;

/// Lower a validated Parsed AST into deterministic canonical Semantic IR.
pub fn lower_to_ir(ast: ParsedAst) -> Result<SemanticIr> {
    validate_surface_spec(&ast.spec)?;

    let machine = ast.spec.machine;

    let mut states: Vec<_> = machine
        .states
        .into_iter()
        .map(|state| CanonicalState {
            id: state.id,
            description: state.description,
        })
        .collect();
    states.sort_by(|left, right| left.id.cmp(&right.id));

    let mut fields: Vec<_> = machine
        .fields
        .into_iter()
        .map(|field| CanonicalField {
            id: field.id,
            field_type: field.field_type,
            initial: field.initial,
            visibility: field.visibility,
        })
        .collect();
    fields.sort_by(|left, right| left.id.cmp(&right.id));

    let mut transitions: Vec<_> = machine
        .transitions
        .into_iter()
        .map(|transition| CanonicalTransition {
            id: transition.id,
            from: transition.from,
            to: transition.to,
            guard: CanonicalGuard {
                guard: transition.guard,
            },
            actions: transition
                .actions
                .into_iter()
                .map(|action| CanonicalAction { action })
                .collect(),
        })
        .collect();
    transitions.sort_by(|left, right| left.id.cmp(&right.id));

    let mut loops = machine.loops;
    loops.sort_by(|left, right| left.id.cmp(&right.id));

    let mut invariants: Vec<_> = machine
        .invariants
        .into_iter()
        .map(|invariant| CanonicalInvariant {
            id: invariant.id,
            guard: CanonicalGuard {
                guard: invariant.guard,
            },
            scope: invariant.scope,
        })
        .collect();
    invariants.sort_by(|left, right| left.id.cmp(&right.id));

    let mut observations = machine.observations;
    observations.sort_by(|left, right| left.id.cmp(&right.id));

    let mut public_inputs = machine.public_inputs;
    public_inputs.sort_by(|left, right| left.id.cmp(&right.id));

    let mut private_witnesses = machine.private_witnesses;
    private_witnesses.sort_by(|left, right| left.id.cmp(&right.id));

    let mut targets = ast.spec.targets;
    targets.sort_by(|left, right| left.id.cmp(&right.id));

    let mut mutations = ast.spec.mutations;
    mutations.sort_by(|left, right| left.id.cmp(&right.id));

    Ok(SemanticIr {
        machine: CanonicalMachine {
            id: machine.id,
            description: machine.description,
            initial_state: machine.initial_state,
            semantic_equivalence_class: machine.semantic_equivalence_class,
            states,
            fields,
            transitions,
            loops,
            invariants,
            observations,
            witness_policy: machine.witness_policy,
            public_inputs,
            private_witnesses,
        },
        oracle: CanonicalOracle {
            accepted_traces: ast.spec.oracle.accepted_traces,
            rejected_traces: ast.spec.oracle.rejected_traces,
        },
        targets,
        mutations,
        evidence: ast.spec.evidence,
    })
}
