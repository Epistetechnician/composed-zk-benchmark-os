//! State slice: bend-independent-semantic-lane-v1.
//!
//! Export the existing deterministic Semantic IR/oracle corpus into a small,
//! implementation-diverse JSON boundary for the Bend lane. Expected outcome
//! codes are observations from the Rust oracle; they are not embedded into the
//! generated Bend program as laws or axioms.

use std::collections::BTreeMap;
use std::env;

use serde::Serialize;
use zkbench_core::dsl::{
    ActionSpec, GuardExpr, GuardSpec, OperandSpec, OracleOutcome, SemanticIr, TraceSpec,
};
use zkbench_core::generator::{
    generate_instance, FamilyKind, GeneratedBenchmarkInstance, GeneratorConfig, InstanceParams,
};
use zkbench_core::value::{Value, ValueType};

const STATE_SLICE: &str = "bend-independent-semantic-lane-v1";
const PROTOCOL_IDENTITY: &str = "bend-independent-semantic-lane-v1";

#[derive(Debug, Serialize)]
struct ExportedSuite {
    state_slice: &'static str,
    protocol_identity: &'static str,
    generator_families: usize,
    seeds_per_family: usize,
    cases: Vec<ExportedCase>,
}

#[derive(Debug, Clone, Serialize)]
struct ExportedCase {
    id: String,
    family: String,
    seed: u64,
    trace_id: String,
    machine: ExportedMachine,
    trace: ExportedTrace,
    expected_code: u8,
}

#[derive(Debug, Clone, Serialize)]
struct ExportedMachine {
    initial_state: usize,
    initial_fields: Vec<ExportedValue>,
    transitions: Vec<ExportedTransition>,
    invariants: Vec<ExportedGuard>,
}

#[derive(Debug, Clone, Serialize)]
struct ExportedTrace {
    initial_state: usize,
    initial_fields: Vec<ExportedAssignment>,
    steps: Vec<usize>,
    expected_final_state: Option<usize>,
    expected_final_fields: Vec<ExportedAssignment>,
}

#[derive(Debug, Clone, Serialize)]
struct ExportedTransition {
    from: usize,
    to: usize,
    guard: ExportedGuard,
    actions: Vec<ExportedAction>,
}

#[derive(Debug, Clone, Serialize)]
struct ExportedAssignment {
    field: usize,
    value: ExportedValue,
}

#[derive(Debug, Clone, Serialize)]
#[serde(tag = "kind")]
enum ExportedValue {
    Int { value: i64 },
    Bool { value: bool },
}

#[derive(Debug, Clone, Serialize)]
#[serde(tag = "kind")]
enum ExportedOperand {
    Field { field: usize },
    Literal { value: ExportedValue },
}

#[derive(Debug, Clone, Serialize)]
#[serde(tag = "kind")]
enum ExportedGuard {
    Bool {
        value: bool,
    },
    Eq {
        left: ExportedOperand,
        right: ExportedOperand,
    },
    Neq {
        left: ExportedOperand,
        right: ExportedOperand,
    },
    Lt {
        left: ExportedOperand,
        right: ExportedOperand,
    },
    Lte {
        left: ExportedOperand,
        right: ExportedOperand,
    },
    Gt {
        left: ExportedOperand,
        right: ExportedOperand,
    },
    Gte {
        left: ExportedOperand,
        right: ExportedOperand,
    },
    And {
        items: Vec<ExportedGuard>,
    },
    Or {
        items: Vec<ExportedGuard>,
    },
    Not {
        item: Box<ExportedGuard>,
    },
}

#[derive(Debug, Clone, Serialize)]
#[serde(tag = "kind")]
enum ExportedAction {
    Noop,
    Assign {
        field: usize,
        value: ExportedOperand,
    },
    AddAssign {
        field: usize,
        value: ExportedOperand,
    },
    SubAssign {
        field: usize,
        value: ExportedOperand,
    },
}

fn main() {
    if let Err(error) = run() {
        eprintln!("bend_export_v1: {error}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), String> {
    let seeds = parse_seed_count()?;
    let families = implemented_families();
    let mut cases = Vec::new();

    for family in &families {
        for seed in 0..seeds {
            let instance = generate_instance(
                config_for_family(*family, seed as u64),
                InstanceParams::default(),
            )
            .map_err(|error| format!("generate {family:?} seed {seed}: {error}"))?;
            for trace in instance
                .accepted_traces
                .iter()
                .chain(instance.rejected_traces.iter())
            {
                cases.push(export_case(*family, seed as u64, &instance, trace)?);
            }
        }
    }

    let suite = ExportedSuite {
        state_slice: STATE_SLICE,
        protocol_identity: PROTOCOL_IDENTITY,
        generator_families: families.len(),
        seeds_per_family: seeds,
        cases,
    };
    println!(
        "{}",
        serde_json::to_string(&suite).map_err(|error| format!("serialize suite: {error}"))?
    );
    Ok(())
}

fn parse_seed_count() -> Result<usize, String> {
    let args: Vec<String> = env::args().collect();
    if args.len() == 1 {
        return Ok(32);
    }
    if args.len() == 3 && args[1] == "--seeds" {
        let seeds = args[2]
            .parse::<usize>()
            .map_err(|error| format!("invalid --seeds value: {error}"))?;
        if seeds == 0 || seeds > 128 {
            return Err("--seeds must be between 1 and 128".to_string());
        }
        return Ok(seeds);
    }
    Err("usage: bend_export_v1 [--seeds COUNT]".to_string())
}

fn implemented_families() -> Vec<FamilyKind> {
    vec![
        FamilyKind::BaselineFsm,
        FamilyKind::BranchingFsm,
        FamilyKind::BoundedCounterLoop,
        FamilyKind::NestedLoop,
        FamilyKind::GuardHeavyMachine,
        FamilyKind::RecursiveEnvelope,
        FamilyKind::MemoryHeavyStateMachine,
        FamilyKind::PublicPrivateBoundaryStress,
        FamilyKind::ZkMlControlFlowMixed,
    ]
}

fn config_for_family(family: FamilyKind, seed: u64) -> GeneratorConfig {
    match family {
        FamilyKind::BaselineFsm => GeneratorConfig::baseline_fsm().seed(seed),
        FamilyKind::BranchingFsm => GeneratorConfig::branching_fsm().seed(seed),
        FamilyKind::BoundedCounterLoop => GeneratorConfig::bounded_counter_loop()
            .seed(seed)
            .loop_bound(3),
        FamilyKind::NestedLoop => GeneratorConfig::nested_loop().seed(seed).loop_bound(2),
        FamilyKind::GuardHeavyMachine => GeneratorConfig::guard_heavy_machine()
            .seed(seed)
            .loop_bound(2),
        FamilyKind::RecursiveEnvelope => GeneratorConfig::recursive_envelope()
            .seed(seed)
            .loop_bound(2),
        FamilyKind::MemoryHeavyStateMachine => {
            GeneratorConfig::memory_heavy_state_machine().seed(seed)
        }
        FamilyKind::PublicPrivateBoundaryStress => {
            GeneratorConfig::public_private_boundary_stress().seed(seed)
        }
        FamilyKind::ZkMlControlFlowMixed => GeneratorConfig::zkml_control_flow_mixed().seed(seed),
    }
}

fn export_case(
    family: FamilyKind,
    seed: u64,
    instance: &GeneratedBenchmarkInstance,
    trace: &TraceSpec,
) -> Result<ExportedCase, String> {
    let field_indices = field_indices(&instance.semantic_ir)?;
    let state_indices = state_indices(&instance.semantic_ir);
    let transition_indices = transition_indices(&instance.semantic_ir);
    let machine = export_machine(&instance.semantic_ir, &field_indices, &state_indices)?;
    let exported_trace = export_trace(
        &instance.semantic_ir,
        trace,
        &field_indices,
        &state_indices,
        &transition_indices,
    )?;
    let expected = zkbench_core::dsl::evaluate_trace(&instance.semantic_ir, trace)
        .map_err(|error| format!("evaluate {}: {error}", trace.id))?;

    Ok(ExportedCase {
        id: format!("{}:seed:{seed}:trace:{}", family.id_segment(), trace.id),
        family: family.id_segment().to_string(),
        seed,
        trace_id: trace.id.clone(),
        machine,
        trace: exported_trace,
        expected_code: outcome_code(expected),
    })
}

fn field_indices(ir: &SemanticIr) -> Result<BTreeMap<String, usize>, String> {
    let mut indices = BTreeMap::new();
    for field in &ir.machine.fields {
        if matches!(&field.field_type, ValueType::Int | ValueType::Bool) {
            indices.insert(field.id.clone(), indices.len());
        }
    }
    if indices.is_empty() {
        return Err("machine has no integer or boolean fields".to_string());
    }
    Ok(indices)
}

fn state_indices(ir: &SemanticIr) -> BTreeMap<String, usize> {
    ir.machine
        .states
        .iter()
        .enumerate()
        .map(|(index, state)| (state.id.clone(), index))
        .collect()
}

fn transition_indices(ir: &SemanticIr) -> BTreeMap<String, usize> {
    ir.machine
        .transitions
        .iter()
        .enumerate()
        .map(|(index, transition)| (transition.id.clone(), index))
        .collect()
}

fn export_machine(
    ir: &SemanticIr,
    fields: &BTreeMap<String, usize>,
    states: &BTreeMap<String, usize>,
) -> Result<ExportedMachine, String> {
    let initial_state = lookup(states, &ir.machine.initial_state, "initial state")?;
    let initial_fields = ir
        .machine
        .fields
        .iter()
        .filter_map(|field| fields.get(&field.id).map(|index| (index, field)))
        .map(|(index, field)| {
            let value = field
                .initial
                .as_ref()
                .ok_or_else(|| format!("field '{}' has no initial value", field.id))?;
            Ok((*index, export_value(value)?))
        })
        .collect::<Result<Vec<_>, String>>()?;
    let mut initial_fields = initial_fields;
    initial_fields.sort_by_key(|(index, _)| *index);

    let exported_transitions = ir
        .machine
        .transitions
        .iter()
        .map(|transition| {
            Ok(ExportedTransition {
                from: lookup(states, &transition.from, "transition source")?,
                to: lookup(states, &transition.to, "transition target")?,
                guard: export_guard(&transition.guard.guard, fields)?,
                actions: transition
                    .actions
                    .iter()
                    .map(|action| export_action(&action.action, fields))
                    .collect::<Result<Vec<_>, String>>()?,
            })
        })
        .collect::<Result<Vec<_>, String>>()?;
    let invariants = ir
        .machine
        .invariants
        .iter()
        .map(|invariant| export_guard(&invariant.guard.guard, fields))
        .collect::<Result<Vec<_>, String>>()?;

    Ok(ExportedMachine {
        initial_state,
        initial_fields: initial_fields.into_iter().map(|(_, value)| value).collect(),
        transitions: exported_transitions,
        invariants,
    })
}

fn export_trace(
    ir: &SemanticIr,
    trace: &TraceSpec,
    fields: &BTreeMap<String, usize>,
    states: &BTreeMap<String, usize>,
    transitions: &BTreeMap<String, usize>,
) -> Result<ExportedTrace, String> {
    let initial_state = trace
        .initial_state
        .as_ref()
        .unwrap_or(&ir.machine.initial_state);
    let initial_fields = export_assignments(&trace.initial_fields, fields)?;
    let steps = trace
        .steps
        .iter()
        .map(|step| lookup(transitions, &step.transition, "trace transition"))
        .collect::<Result<Vec<_>, String>>()?;
    let expected_final_state = trace
        .expected_final_state
        .as_ref()
        .map(|state| lookup(states, state, "expected final state"))
        .transpose()?;
    let expected_final_fields = export_assignments(&trace.expected_final_fields, fields)?;
    Ok(ExportedTrace {
        initial_state: lookup(states, initial_state, "trace initial state")?,
        initial_fields,
        steps,
        expected_final_state,
        expected_final_fields,
    })
}

fn export_assignments(
    assignments: &BTreeMap<String, Value>,
    fields: &BTreeMap<String, usize>,
) -> Result<Vec<ExportedAssignment>, String> {
    assignments
        .iter()
        .map(|(field, value)| {
            Ok(ExportedAssignment {
                field: lookup(fields, field, "field assignment")?,
                value: export_value(value)?,
            })
        })
        .collect()
}

fn export_value(value: &Value) -> Result<ExportedValue, String> {
    match value {
        Value::Int { int } if *int >= 0 => Ok(ExportedValue::Int { value: *int }),
        Value::Bool { bool } => Ok(ExportedValue::Bool { value: *bool }),
        Value::Int { int } => Err(format!("negative integer {int} is outside Bend V1 subset")),
        Value::Text { text } => Err(format!("text value '{text}' is outside Bend V1 subset")),
    }
}

fn export_operand(
    operand: &OperandSpec,
    fields: &BTreeMap<String, usize>,
) -> Result<ExportedOperand, String> {
    match operand {
        OperandSpec::Field { field } => Ok(ExportedOperand::Field {
            field: lookup(fields, field, "operand field")?,
        }),
        OperandSpec::Literal(value) => Ok(ExportedOperand::Literal {
            value: export_value(value)?,
        }),
    }
}

fn export_guard(
    guard: &GuardSpec,
    fields: &BTreeMap<String, usize>,
) -> Result<ExportedGuard, String> {
    match guard {
        GuardSpec::Bool(value) => Ok(ExportedGuard::Bool { value: *value }),
        GuardSpec::Expr(expr) => {
            match expr {
                GuardExpr::Eq { eq } => {
                    binary_guard(eq, fields, |left, right| ExportedGuard::Eq { left, right })
                }
                GuardExpr::Neq { neq } => binary_guard(neq, fields, |left, right| {
                    ExportedGuard::Neq { left, right }
                }),
                GuardExpr::Lt { lt } => {
                    binary_guard(lt, fields, |left, right| ExportedGuard::Lt { left, right })
                }
                GuardExpr::Lte { lte } => binary_guard(lte, fields, |left, right| {
                    ExportedGuard::Lte { left, right }
                }),
                GuardExpr::Gt { gt } => {
                    binary_guard(gt, fields, |left, right| ExportedGuard::Gt { left, right })
                }
                GuardExpr::Gte { gte } => binary_guard(gte, fields, |left, right| {
                    ExportedGuard::Gte { left, right }
                }),
                GuardExpr::And { and } => Ok(ExportedGuard::And {
                    items: and
                        .iter()
                        .map(|guard| export_guard(guard, fields))
                        .collect::<Result<Vec<_>, String>>()?,
                }),
                GuardExpr::Or { or } => Ok(ExportedGuard::Or {
                    items: or
                        .iter()
                        .map(|guard| export_guard(guard, fields))
                        .collect::<Result<Vec<_>, String>>()?,
                }),
                GuardExpr::Not { not } => Ok(ExportedGuard::Not {
                    item: Box::new(export_guard(not, fields)?),
                }),
                GuardExpr::RawText { raw_text } => Err(format!(
                    "raw-text guard '{raw_text}' is outside Bend V1 subset"
                )),
            }
        }
    }
}

fn binary_guard(
    guard: &zkbench_core::dsl::BinaryGuard,
    fields: &BTreeMap<String, usize>,
    constructor: fn(ExportedOperand, ExportedOperand) -> ExportedGuard,
) -> Result<ExportedGuard, String> {
    Ok(constructor(
        export_operand(&guard.left, fields)?,
        export_operand(&guard.right, fields)?,
    ))
}

fn export_action(
    action: &ActionSpec,
    fields: &BTreeMap<String, usize>,
) -> Result<ExportedAction, String> {
    match action {
        ActionSpec::Noop { .. } => Ok(ExportedAction::Noop),
        ActionSpec::Assign { assign } => Ok(ExportedAction::Assign {
            field: lookup(fields, &assign.field, "assign field")?,
            value: export_operand(&assign.value, fields)?,
        }),
        ActionSpec::AddAssign { add_assign } => Ok(ExportedAction::AddAssign {
            field: lookup(fields, &add_assign.field, "add-assign field")?,
            value: export_operand(&add_assign.value, fields)?,
        }),
        ActionSpec::SubAssign { sub_assign } => Ok(ExportedAction::SubAssign {
            field: lookup(fields, &sub_assign.field, "sub-assign field")?,
            value: export_operand(&sub_assign.value, fields)?,
        }),
        ActionSpec::RawText { raw_text } => Err(format!(
            "raw-text action '{raw_text}' is outside Bend V1 subset"
        )),
    }
}

fn lookup<T>(map: &BTreeMap<String, T>, key: &str, context: &str) -> Result<T, String>
where
    T: Copy,
{
    map.get(key)
        .copied()
        .ok_or_else(|| format!("{context} '{key}' is not declared"))
}

fn outcome_code(outcome: OracleOutcome) -> u8 {
    match outcome {
        OracleOutcome::Accepted => 0,
        OracleOutcome::Rejected { .. } => 1,
        OracleOutcome::CapabilityGap { .. } => 2,
        OracleOutcome::Inconclusive { .. } => 3,
    }
}
