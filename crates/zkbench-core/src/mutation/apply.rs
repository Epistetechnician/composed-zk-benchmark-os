//! Mutation engine orchestration and shared helpers.

use crate::dsl::{
    evaluate_trace, lower_to_ir, validate_surface_spec, ActionSpec, GuardExpr, GuardSpec,
    InvariantSpec, LoopSpec, ParsedAst, SemanticIr, SurfaceSpec, TraceSpec, TransitionSpec,
};
use crate::error::{Result, ZkBenchError};
use crate::evidence::{ClaimBoundary, ExpectedVerdict};
use crate::generator::GeneratedBenchmarkInstance;
use crate::value::Value;

use std::collections::BTreeSet;

use super::bad_counters::BadCountersPass;
use super::corrupted_guards::CorruptedGuardsPass;
use super::invalid_unroll_bounds::InvalidUnrollBoundsPass;
use super::invariant_strengthening::InvariantStrengtheningPass;
use super::invariant_weakening::InvariantWeakeningPass;
use super::missing_constraints::MissingConstraintsPass;
use super::nondeterministic_transition_injection::NondeterministicTransitionInjectionPass;
use super::observation_omission::ObservationOmissionPass;
use super::pass::{
    MutatedBenchmarkInstance, MutationApplication, MutationInput, MutationPass, MutationPlan,
    MutationSafetyClass,
};
use super::provenance::MutationProvenance;
use super::public_private_boundary_mismatch::PublicPrivateBoundaryMismatchPass;
use super::recursion_envelope_mismatch::RecursionEnvelopeMismatchPass;
use super::semantic_no_op_drift::SemanticNoOpDriftPass;
use super::stale_state_reads::StaleStateReadsPass;
use super::trace_ordering_corruption::TraceOrderingCorruptionPass;
use super::witness_aliasing::WitnessAliasingPass;
use super::{MutationClass, MutationKind, MutationSeverity, MutationSpec};

/// Local mutation engine.
#[derive(Default)]
pub struct MutationEngine {
    passes: Vec<Box<dyn MutationPass>>,
}

impl MutationEngine {
    /// Add a mutation pass.
    pub fn with_pass(mut self, pass: impl MutationPass + 'static) -> Self {
        self.passes.push(Box::new(pass));
        self
    }

    /// Apply all configured mutation passes.
    pub fn apply(
        &self,
        instance: &GeneratedBenchmarkInstance,
    ) -> Result<Vec<MutatedBenchmarkInstance>> {
        let input = MutationInput { instance };
        self.passes
            .iter()
            .map(|pass| pass.apply(&input).map(|application| application.output))
            .collect()
    }
}

/// Apply one mutation pass.
pub fn apply_mutation_pass(
    instance: &GeneratedBenchmarkInstance,
    pass: &dyn MutationPass,
) -> Result<MutatedBenchmarkInstance> {
    pass.apply(&MutationInput { instance })
        .map(|application| application.output)
}

/// Apply a mutation pass selected by `MutationClass`.
pub fn apply_mutation_for_class(
    instance: &GeneratedBenchmarkInstance,
    mutation_class: MutationClass,
) -> Result<MutatedBenchmarkInstance> {
    match mutation_class {
        MutationClass::MissingConstraints => apply_mutation_pass(instance, &MissingConstraintsPass),
        MutationClass::CorruptedGuards => apply_mutation_pass(instance, &CorruptedGuardsPass),
        MutationClass::BadCounters => apply_mutation_pass(instance, &BadCountersPass),
        MutationClass::StaleStateReads => apply_mutation_pass(instance, &StaleStateReadsPass),
        MutationClass::InvalidUnrollBounds => {
            apply_mutation_pass(instance, &InvalidUnrollBoundsPass)
        }
        MutationClass::NondeterministicTransitionInjection => {
            apply_mutation_pass(instance, &NondeterministicTransitionInjectionPass)
        }
        MutationClass::RecursionEnvelopeMismatch => {
            apply_mutation_pass(instance, &RecursionEnvelopeMismatchPass)
        }
        MutationClass::PublicPrivateBoundaryMismatch => {
            apply_mutation_pass(instance, &PublicPrivateBoundaryMismatchPass)
        }
        MutationClass::WitnessAliasing => apply_mutation_pass(instance, &WitnessAliasingPass),
        MutationClass::InvariantWeakening => apply_mutation_pass(instance, &InvariantWeakeningPass),
        MutationClass::InvariantStrengthening => {
            apply_mutation_pass(instance, &InvariantStrengtheningPass)
        }
        MutationClass::ObservationOmission => {
            apply_mutation_pass(instance, &ObservationOmissionPass)
        }
        MutationClass::SemanticNoOpDrift => apply_mutation_pass(instance, &SemanticNoOpDriftPass),
        MutationClass::TraceOrderingCorruption => {
            apply_mutation_pass(instance, &TraceOrderingCorruptionPass)
        }
    }
}

/// Apply the default Phase D/E mutation passes.
pub fn apply_default_mutations(
    instance: &GeneratedBenchmarkInstance,
) -> Result<Vec<MutatedBenchmarkInstance>> {
    MutationEngine::default()
        .with_pass(MissingConstraintsPass)
        .with_pass(CorruptedGuardsPass)
        .with_pass(BadCountersPass)
        .apply(instance)
}

/// Evaluate the primary trace of a mutated instance.
pub fn evaluate_mutated_instance(
    instance: &MutatedBenchmarkInstance,
) -> Result<Vec<crate::dsl::OracleOutcome>> {
    Ok(vec![evaluate_trace(
        &instance.semantic_ir,
        &instance.primary_trace,
    )?])
}

pub(crate) struct MutationBuild {
    pub mutation_id: String,
    pub mutation_class: MutationClass,
    pub expected_verdict: ExpectedVerdict,
    pub safety_class: MutationSafetyClass,
    pub source_instance_id: String,
    pub affected_machine_id: String,
    pub affected_transition_ids: Vec<String>,
    pub affected_guard_ids: Vec<String>,
    pub affected_action_ids: Vec<String>,
    pub affected_field_ids: Vec<String>,
    pub description: String,
    pub notes: Vec<String>,
    pub primary_trace: TraceSpec,
    pub surface_spec: SurfaceSpec,
}

pub(crate) fn finish_mutation(build: MutationBuild) -> Result<MutationApplication> {
    let mut surface_spec = build.surface_spec;
    surface_spec.mutations.push(MutationSpec {
        id: build.mutation_id.clone(),
        class: build.mutation_class,
        kind: match build.safety_class {
            MutationSafetyClass::Valid => MutationKind::Valid,
            MutationSafetyClass::NearValid => MutationKind::NearValid,
            MutationSafetyClass::Malicious => MutationKind::Malicious,
            MutationSafetyClass::Diagnostic => MutationKind::NearValid,
        },
        target: build
            .affected_transition_ids
            .first()
            .cloned()
            .unwrap_or_else(|| build.affected_machine_id.clone()),
        expected_verdict: build.expected_verdict,
        severity: match build.safety_class {
            MutationSafetyClass::Valid => MutationSeverity::Low,
            MutationSafetyClass::NearValid | MutationSafetyClass::Diagnostic => {
                MutationSeverity::Medium
            }
            MutationSafetyClass::Malicious => MutationSeverity::High,
        },
        oracle_rationale: Some(build.description.clone()),
    });
    validate_surface_spec(&surface_spec)?;
    let semantic_ir = lower_mutated_surface(&surface_spec)?;
    let provenance = MutationProvenance {
        mutation_id: build.mutation_id.clone(),
        mutation_class: build.mutation_class,
        source_instance_id: build.source_instance_id.clone(),
        affected_machine_id: build.affected_machine_id,
        affected_transition_ids: build.affected_transition_ids.clone(),
        affected_guard_ids: build.affected_guard_ids,
        affected_action_ids: build.affected_action_ids,
        affected_field_ids: build.affected_field_ids,
        description: build.description.clone(),
        expected_verdict: build.expected_verdict,
        safety_class: build.safety_class,
        claim_boundary: ClaimBoundary::Level1LocalReplay,
        notes: build.notes,
    };
    let output = MutatedBenchmarkInstance {
        id: build.mutation_id.clone(),
        source_instance_id: build.source_instance_id.clone(),
        mutation_class: build.mutation_class,
        expected_verdict: build.expected_verdict,
        safety_class: build.safety_class,
        provenance,
        surface_spec,
        semantic_ir,
        primary_trace: build.primary_trace,
        local_oracle_outcomes: Vec::new(),
        claim_boundary: ClaimBoundary::Level1LocalReplay,
    };
    Ok(MutationApplication {
        plan: MutationPlan {
            mutation_id: build.mutation_id,
            mutation_class: build.mutation_class,
            source_instance_id: build.source_instance_id,
            target_description: output.provenance.description.clone(),
        },
        output,
    })
}

pub(crate) fn lower_mutated_surface(surface: &SurfaceSpec) -> Result<SemanticIr> {
    validate_surface_spec(surface)?;
    lower_to_ir(ParsedAst::new(surface.clone()))
}

pub(crate) fn transition_mut<'a>(
    surface: &'a mut SurfaceSpec,
    transition_id: &str,
) -> Result<&'a mut TransitionSpec> {
    surface
        .machine
        .transitions
        .iter_mut()
        .find(|transition| transition.id == transition_id)
        .ok_or_else(|| {
            ZkBenchError::mutation(
                "mutation.target",
                format!("transition '{transition_id}' was not found"),
            )
        })
}

pub(crate) fn transition<'a>(
    surface: &'a SurfaceSpec,
    transition_id: &str,
) -> Option<&'a TransitionSpec> {
    surface
        .machine
        .transitions
        .iter()
        .find(|transition| transition.id == transition_id)
}

pub(crate) fn guard_is_true(guard: &GuardSpec) -> bool {
    matches!(guard, GuardSpec::Bool(true))
}

pub(crate) fn corrupt_guard(guard: &GuardSpec) -> GuardSpec {
    match guard {
        GuardSpec::Bool(value) => GuardSpec::Bool(!value),
        GuardSpec::Expr(expr) => GuardSpec::Expr(match expr {
            GuardExpr::Eq { eq } => GuardExpr::Neq { neq: eq.clone() },
            GuardExpr::Neq { neq } => GuardExpr::Eq { eq: neq.clone() },
            GuardExpr::Lt { lt } => GuardExpr::Lte { lte: lt.clone() },
            GuardExpr::Lte { lte } => GuardExpr::Lt { lt: lte.clone() },
            GuardExpr::Gt { gt } => GuardExpr::Gte { gte: gt.clone() },
            GuardExpr::Gte { gte } => GuardExpr::Gt { gt: gte.clone() },
            GuardExpr::And { and } => GuardExpr::Or { or: and.clone() },
            GuardExpr::Or { or } => GuardExpr::And { and: or.clone() },
            GuardExpr::Not { not } => match not.as_ref() {
                GuardSpec::Bool(value) => return GuardSpec::Bool(*value),
                nested => GuardExpr::Not {
                    not: Box::new(nested.clone()),
                },
            },
            GuardExpr::RawText { raw_text } => GuardExpr::RawText {
                raw_text: raw_text.clone(),
            },
        }),
    }
}

pub(crate) fn bad_counter_action(action: &ActionSpec) -> Option<(ActionSpec, String)> {
    match action {
        ActionSpec::AddAssign { add_assign } => match &add_assign.value {
            crate::dsl::expr::OperandSpec::Literal(Value::Int { int: 1 }) => {
                let mut changed = add_assign.clone();
                changed.value = crate::dsl::expr::OperandSpec::Literal(Value::Int { int: 2 });
                Some((
                    ActionSpec::AddAssign {
                        add_assign: changed,
                    },
                    "changed add_assign integer operand from 1 to 2".to_string(),
                ))
            }
            crate::dsl::expr::OperandSpec::Literal(Value::Int { int }) => {
                let mut changed = add_assign.clone();
                changed.value = crate::dsl::expr::OperandSpec::Literal(Value::Int {
                    int: int.saturating_add(1),
                });
                Some((
                    ActionSpec::AddAssign {
                        add_assign: changed,
                    },
                    format!("incremented add_assign integer operand from {int}"),
                ))
            }
            crate::dsl::expr::OperandSpec::Field { .. } => None,
            crate::dsl::expr::OperandSpec::Literal(Value::Bool { .. })
            | crate::dsl::expr::OperandSpec::Literal(Value::Text { .. }) => None,
        },
        ActionSpec::SubAssign { sub_assign } => match &sub_assign.value {
            crate::dsl::expr::OperandSpec::Literal(Value::Int { int }) => {
                let mut changed = sub_assign.clone();
                changed.value = crate::dsl::expr::OperandSpec::Literal(Value::Int {
                    int: int.saturating_add(1),
                });
                Some((
                    ActionSpec::SubAssign {
                        sub_assign: changed,
                    },
                    format!("incremented sub_assign integer operand from {int}"),
                ))
            }
            crate::dsl::expr::OperandSpec::Field { .. } => None,
            crate::dsl::expr::OperandSpec::Literal(Value::Bool { .. })
            | crate::dsl::expr::OperandSpec::Literal(Value::Text { .. }) => None,
        },
        ActionSpec::Noop { .. } | ActionSpec::Assign { .. } | ActionSpec::RawText { .. } => None,
    }
}

/// Select a primary trace for a mutation pass: the first accepted trace if any,
/// otherwise the first rejected trace. Returns `None` when the instance declares
/// no traces at all.
pub(crate) fn select_primary_trace(instance: &GeneratedBenchmarkInstance) -> Option<TraceSpec> {
    instance
        .accepted_traces
        .first()
        .or_else(|| instance.rejected_traces.first())
        .cloned()
}

/// Mutable accessor for an invariant by id.
pub(crate) fn invariant_mut<'a>(
    surface: &'a mut SurfaceSpec,
    invariant_id: &str,
) -> Result<&'a mut InvariantSpec> {
    surface
        .machine
        .invariants
        .iter_mut()
        .find(|invariant| invariant.id == invariant_id)
        .ok_or_else(|| {
            ZkBenchError::mutation(
                "mutation.target",
                format!("invariant '{invariant_id}' was not found"),
            )
        })
}

/// Mutable accessor for a loop by id.
pub(crate) fn loop_mut<'a>(
    surface: &'a mut SurfaceSpec,
    loop_id: &str,
) -> Result<&'a mut LoopSpec> {
    surface
        .machine
        .loops
        .iter_mut()
        .find(|entry| entry.id == loop_id)
        .ok_or_else(|| {
            ZkBenchError::mutation("mutation.target", format!("loop '{loop_id}' was not found"))
        })
}

/// Return the set of field ids a guard reads.
pub(crate) fn guard_read_fields(guard: &GuardSpec) -> BTreeSet<String> {
    let mut refs = BTreeSet::new();
    guard.collect_field_references(&mut refs);
    refs
}

/// Return the set of field ids an action writes.
pub(crate) fn action_write_fields(action: &ActionSpec) -> BTreeSet<String> {
    let mut refs = BTreeSet::new();
    action.collect_field_references(&mut refs);
    refs
}

/// Return true if the guard is a non-trivial executable expression (not `Bool`
/// and not `RawText`). Used by invariant-strengthening and invariant-weakening
/// passes to skip trivial guards where mutation would be meaningless.
pub(crate) fn guard_is_executable_expr(guard: &GuardSpec) -> bool {
    matches!(guard, GuardSpec::Expr(expr) if !matches!(expr, GuardExpr::RawText { .. }))
}
