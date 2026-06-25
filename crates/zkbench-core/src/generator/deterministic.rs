//! Deterministic local benchmark family generation.

use std::collections::BTreeMap;

use crate::dsl::{
    evaluate_trace, lower_to_ir, validate_surface_spec, ActionSpec, AssignAction, BinaryGuard,
    EvidenceSpec, FieldSpec, GuardExpr, GuardSpec, InvariantSpec, LoopSpec, MachineSpec,
    ObserveSpec, OracleOutcome, OracleSpec, ParsedAst, PrivateWitnessSpec, PublicInputSpec,
    SemanticEquivalenceClass, StateSpec, SurfaceSpec, TargetSpec, TraceSpec, TraceStepSpec,
    TransitionSpec, WitnessPolicy,
};
use crate::error::{Result, ZkBenchError};
use crate::evidence::{ClaimBoundary, ExpectedVerdict};
use crate::value::{FieldVisibility, Value, ValueType};

use super::config::GeneratorConfig;
use super::family::{family_id, GeneratedBenchmarkFamily, GenerationProvenance};
use super::instance::{GeneratedBenchmarkInstance, InstanceParams};
use super::templates::{family_template, FamilyKind};

const GENERATOR_VERSION: &str = "phase-d-e-v0";

/// Deterministic local generator.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeterministicGenerator {
    config: GeneratorConfig,
}

impl DeterministicGenerator {
    /// Construct a deterministic generator.
    pub fn new(config: GeneratorConfig) -> Self {
        Self { config }
    }

    /// Generate a benchmark family.
    pub fn generate_family(&self) -> Result<GeneratedBenchmarkFamily> {
        self.config.validate()?;
        let template = family_template(self.config.family_kind);
        if !template.implemented {
            return Err(ZkBenchError::generation(
                "generator.family_kind",
                format!("{:?} is not implemented", self.config.family_kind),
            ));
        }

        let surface_spec = match self.config.family_kind {
            FamilyKind::BaselineFsm => build_baseline_fsm(&self.config)?,
            FamilyKind::BranchingFsm => build_branching_fsm(&self.config)?,
            FamilyKind::BoundedCounterLoop => build_bounded_counter_loop(&self.config)?,
            FamilyKind::NestedLoop => build_nested_loop(&self.config)?,
            FamilyKind::GuardHeavyMachine => build_guard_heavy_machine(&self.config)?,
            FamilyKind::RecursiveEnvelope => build_recursive_envelope(&self.config)?,
            FamilyKind::MemoryHeavyStateMachine => build_memory_heavy_state_machine(&self.config)?,
            FamilyKind::PublicPrivateBoundaryStress => {
                build_public_private_boundary_stress(&self.config)?
            }
            FamilyKind::ZkMlControlFlowMixed => build_zkml_control_flow_mixed(&self.config)?,
        };

        validate_surface_spec(&surface_spec)?;
        let semantic_ir = lower_to_ir(ParsedAst::new(surface_spec.clone()))?;
        let id = family_id(
            self.config.family_kind,
            self.config.seed,
            &self.config.tunables,
        );
        let provenance = GenerationProvenance {
            generator_version: GENERATOR_VERSION.to_string(),
            seed: self.config.seed,
            generated_at: format!("{GENERATOR_VERSION}:seed:{}", self.config.seed.value),
            description: "deterministic local generation; no wall-clock timestamp".to_string(),
        };

        let mut family = GeneratedBenchmarkFamily {
            id,
            family_kind: self.config.family_kind,
            description: template.description,
            config: self.config.clone(),
            provenance,
            surface_spec,
            semantic_ir,
            instances: Vec::new(),
            claim_boundary: ClaimBoundary::Level1LocalReplay,
            supported_oracle_features: template.supported_oracle_features,
            unsupported_features: template.unsupported_features,
            evidence_notes: vec![
                "Generated family is a local semantic fixture, not official benchmark evidence."
                    .to_string(),
                "No external backend artifacts are generated in Phase D/E.".to_string(),
            ],
        };
        let default_instance = family.instantiate(InstanceParams::default())?;
        family.instances.push(default_instance);
        Ok(family)
    }

    /// Generate a concrete benchmark instance.
    pub fn generate_instance(&self, params: InstanceParams) -> Result<GeneratedBenchmarkInstance> {
        self.generate_family()?.instantiate(params)
    }
}

/// Generate a benchmark family.
pub fn generate_family(config: GeneratorConfig) -> Result<GeneratedBenchmarkFamily> {
    DeterministicGenerator::new(config).generate_family()
}

/// Generate a concrete benchmark instance.
pub fn generate_instance(
    config: GeneratorConfig,
    params: InstanceParams,
) -> Result<GeneratedBenchmarkInstance> {
    DeterministicGenerator::new(config).generate_instance(params)
}

/// Evaluate all traces attached to a generated instance.
pub fn evaluate_generated_instance(
    instance: &GeneratedBenchmarkInstance,
) -> Result<Vec<OracleOutcome>> {
    instance
        .accepted_traces
        .iter()
        .chain(instance.rejected_traces.iter())
        .map(|trace| evaluate_trace(&instance.semantic_ir, trace))
        .collect()
}

fn build_baseline_fsm(config: &GeneratorConfig) -> Result<SurfaceSpec> {
    let state_count = config.tunables.state_count;
    let machine_id = family_id(config.family_kind, config.seed, &config.tunables);
    let states = (0..state_count)
        .map(|index| StateSpec {
            id: format!("state_{index}"),
            description: None,
        })
        .collect::<Vec<_>>();

    let transitions = (0..state_count.saturating_sub(1))
        .map(|index| TransitionSpec {
            id: format!("advance_{index}"),
            from: format!("state_{index}"),
            to: format!("state_{}", index + 1),
            guard: eq_field_int("counter", index as i64),
            actions: vec![add_assign_int("counter", 1)],
        })
        .collect::<Vec<_>>();

    let accepted_steps = transitions
        .iter()
        .map(|transition| TraceStepSpec {
            transition: transition.id.clone(),
        })
        .collect::<Vec<_>>();
    let rejected_transition = transitions
        .last()
        .map(|transition| transition.id.clone())
        .ok_or_else(|| {
            ZkBenchError::generation(
                "generator.baseline_fsm.transitions",
                "BaselineFsm requires at least one transition",
            )
        })?;

    let mut expected_final_fields = BTreeMap::new();
    expected_final_fields.insert(
        "counter".to_string(),
        Value::Int {
            int: state_count.saturating_sub(1) as i64,
        },
    );

    let surface = base_surface(
        MachineSpec {
            id: machine_id,
            description: Some("Deterministically generated baseline FSM.".to_string()),
            initial_state: "state_0".to_string(),
            semantic_equivalence_class: Some(SemanticEquivalenceClass {
                id: "generated_baseline_fsm_v0".to_string(),
                description: None,
            }),
            states,
            fields: vec![FieldSpec {
                id: "counter".to_string(),
                field_type: ValueType::Int,
                initial: Some(Value::Int { int: 0 }),
                visibility: FieldVisibility::Private,
            }],
            transitions,
            loops: Vec::new(),
            invariants: Vec::new(),
            observations: vec![ObserveSpec {
                id: "counter_observation".to_string(),
                field: "counter".to_string(),
                visibility: FieldVisibility::Public,
            }],
            witness_policy: Default::default(),
            public_inputs: Vec::new(),
            private_witnesses: Vec::new(),
        },
        OracleSpec {
            accepted_traces: vec![TraceSpec {
                id: "generated_accepts_linear_path".to_string(),
                initial_state: None,
                initial_fields: BTreeMap::new(),
                steps: accepted_steps,
                expected_final_state: Some(format!("state_{}", state_count - 1)),
                expected_final_fields,
                expected_verdict: Some(ExpectedVerdict::Accept),
                requires_capabilities: Vec::new(),
            }],
            rejected_traces: vec![TraceSpec {
                id: "generated_rejects_wrong_start".to_string(),
                initial_state: Some("state_0".to_string()),
                initial_fields: BTreeMap::new(),
                steps: vec![TraceStepSpec {
                    transition: rejected_transition,
                }],
                expected_final_state: None,
                expected_final_fields: BTreeMap::new(),
                expected_verdict: Some(ExpectedVerdict::Reject),
                requires_capabilities: Vec::new(),
            }],
        },
    );

    Ok(surface)
}

fn build_branching_fsm(config: &GeneratorConfig) -> Result<SurfaceSpec> {
    let branch_count = config
        .tunables
        .branching_factor
        .min(config.tunables.state_count.saturating_sub(2));
    if branch_count < 2 {
        return Err(ZkBenchError::generation(
            "generator.branching_fsm.branch_count",
            "BranchingFsm requires at least two branch states",
        ));
    }

    let machine_id = family_id(config.family_kind, config.seed, &config.tunables);
    let selected_branch = (config.seed.value as usize) % branch_count;
    let rejected_branch = (selected_branch + 1) % branch_count;

    let mut states = vec![StateSpec {
        id: "start".to_string(),
        description: None,
    }];
    for branch in 0..branch_count {
        states.push(StateSpec {
            id: format!("branch_{branch}"),
            description: None,
        });
    }
    while states.len() < config.tunables.state_count.saturating_sub(1) {
        states.push(StateSpec {
            id: format!("unused_{}", states.len()),
            description: Some("deterministic spare state".to_string()),
        });
    }
    states.push(StateSpec {
        id: "final".to_string(),
        description: None,
    });

    let mut transitions = Vec::new();
    for branch in 0..branch_count {
        transitions.push(TransitionSpec {
            id: format!("select_branch_{branch}"),
            from: "start".to_string(),
            to: format!("branch_{branch}"),
            guard: eq_field_int("selector", branch as i64),
            actions: vec![ActionSpec::Assign {
                assign: AssignAction {
                    field: "branch_taken".to_string(),
                    value: crate::dsl::expr::OperandSpec::Literal(Value::Bool { bool: true }),
                },
            }],
        });
        transitions.push(TransitionSpec {
            id: format!("complete_branch_{branch}"),
            from: format!("branch_{branch}"),
            to: "final".to_string(),
            guard: GuardSpec::Bool(true),
            actions: Vec::new(),
        });
    }

    let mut accepted_final_fields = BTreeMap::new();
    accepted_final_fields.insert("branch_taken".to_string(), Value::Bool { bool: true });

    let mut rejected_initial_fields = BTreeMap::new();
    rejected_initial_fields.insert(
        "selector".to_string(),
        Value::Int {
            int: selected_branch as i64,
        },
    );

    Ok(base_surface(
        MachineSpec {
            id: machine_id,
            description: Some("Deterministically generated branching FSM.".to_string()),
            initial_state: "start".to_string(),
            semantic_equivalence_class: Some(SemanticEquivalenceClass {
                id: "generated_branching_fsm_v0".to_string(),
                description: None,
            }),
            states,
            fields: vec![
                FieldSpec {
                    id: "selector".to_string(),
                    field_type: ValueType::Int,
                    initial: Some(Value::Int {
                        int: selected_branch as i64,
                    }),
                    visibility: FieldVisibility::Public,
                },
                FieldSpec {
                    id: "branch_taken".to_string(),
                    field_type: ValueType::Bool,
                    initial: Some(Value::Bool { bool: false }),
                    visibility: FieldVisibility::Public,
                },
            ],
            transitions,
            loops: Vec::new(),
            invariants: Vec::new(),
            observations: vec![ObserveSpec {
                id: "selector_observation".to_string(),
                field: "selector".to_string(),
                visibility: FieldVisibility::Public,
            }],
            witness_policy: Default::default(),
            public_inputs: Vec::new(),
            private_witnesses: Vec::new(),
        },
        OracleSpec {
            accepted_traces: vec![TraceSpec {
                id: "generated_accepts_selected_branch".to_string(),
                initial_state: None,
                initial_fields: BTreeMap::new(),
                steps: vec![
                    TraceStepSpec {
                        transition: format!("select_branch_{selected_branch}"),
                    },
                    TraceStepSpec {
                        transition: format!("complete_branch_{selected_branch}"),
                    },
                ],
                expected_final_state: Some("final".to_string()),
                expected_final_fields: accepted_final_fields,
                expected_verdict: Some(ExpectedVerdict::Accept),
                requires_capabilities: Vec::new(),
            }],
            rejected_traces: vec![TraceSpec {
                id: "generated_rejects_false_branch_guard".to_string(),
                initial_state: Some("start".to_string()),
                initial_fields: rejected_initial_fields,
                steps: vec![
                    TraceStepSpec {
                        transition: format!("select_branch_{rejected_branch}"),
                    },
                    TraceStepSpec {
                        transition: format!("complete_branch_{rejected_branch}"),
                    },
                ],
                expected_final_state: Some("final".to_string()),
                expected_final_fields: BTreeMap::new(),
                expected_verdict: Some(ExpectedVerdict::Reject),
                requires_capabilities: Vec::new(),
            }],
        },
    ))
}

fn build_bounded_counter_loop(config: &GeneratorConfig) -> Result<SurfaceSpec> {
    let bound = config.tunables.loop_bound as i64;
    let machine_id = family_id(config.family_kind, config.seed, &config.tunables);

    let mut expected_final_fields = BTreeMap::new();
    expected_final_fields.insert("counter".to_string(), Value::Int { int: bound });

    let increment_steps = (0..config.tunables.loop_bound)
        .map(|_| TraceStepSpec {
            transition: "increment".to_string(),
        })
        .collect::<Vec<_>>();
    let mut accepted_steps = increment_steps.clone();
    accepted_steps.push(TraceStepSpec {
        transition: "finish".to_string(),
    });
    let mut rejected_steps = increment_steps;
    rejected_steps.push(TraceStepSpec {
        transition: "increment".to_string(),
    });

    Ok(base_surface(
        MachineSpec {
            id: machine_id,
            description: Some("Deterministically generated bounded counter loop.".to_string()),
            initial_state: "counting".to_string(),
            semantic_equivalence_class: Some(SemanticEquivalenceClass {
                id: "generated_bounded_counter_loop_v0".to_string(),
                description: None,
            }),
            states: vec![
                StateSpec {
                    id: "counting".to_string(),
                    description: None,
                },
                StateSpec {
                    id: "finished".to_string(),
                    description: None,
                },
            ],
            fields: vec![
                FieldSpec {
                    id: "counter".to_string(),
                    field_type: ValueType::Int,
                    initial: Some(Value::Int { int: 0 }),
                    visibility: FieldVisibility::Public,
                },
                FieldSpec {
                    id: "bound".to_string(),
                    field_type: ValueType::Int,
                    initial: Some(Value::Int { int: bound }),
                    visibility: FieldVisibility::Public,
                },
            ],
            transitions: vec![
                TransitionSpec {
                    id: "increment".to_string(),
                    from: "counting".to_string(),
                    to: "counting".to_string(),
                    guard: lt_field_field("counter", "bound"),
                    actions: vec![add_assign_int("counter", 1)],
                },
                TransitionSpec {
                    id: "finish".to_string(),
                    from: "counting".to_string(),
                    to: "finished".to_string(),
                    guard: eq_field_field("counter", "bound"),
                    actions: Vec::new(),
                },
            ],
            loops: vec![LoopSpec {
                id: "count_to_bound".to_string(),
                bound: Some(lte_field_field("counter", "bound")),
                body: vec!["increment".to_string()],
                metadata: BTreeMap::from([("max_unroll".to_string(), Value::Int { int: bound })]),
            }],
            invariants: vec![InvariantSpec {
                id: "counter_at_or_below_bound".to_string(),
                guard: lte_field_field("counter", "bound"),
                scope: Some("trace".to_string()),
            }],
            observations: vec![ObserveSpec {
                id: "counter_observation".to_string(),
                field: "counter".to_string(),
                visibility: FieldVisibility::Public,
            }],
            witness_policy: Default::default(),
            public_inputs: Vec::new(),
            private_witnesses: Vec::new(),
        },
        OracleSpec {
            accepted_traces: vec![TraceSpec {
                id: "generated_accepts_reaching_bound".to_string(),
                initial_state: None,
                initial_fields: BTreeMap::new(),
                steps: accepted_steps,
                expected_final_state: Some("finished".to_string()),
                expected_final_fields,
                expected_verdict: Some(ExpectedVerdict::Accept),
                requires_capabilities: Vec::new(),
            }],
            rejected_traces: vec![TraceSpec {
                id: "generated_rejects_extra_increment".to_string(),
                initial_state: None,
                initial_fields: BTreeMap::new(),
                steps: rejected_steps,
                expected_final_state: None,
                expected_final_fields: BTreeMap::new(),
                expected_verdict: Some(ExpectedVerdict::Reject),
                requires_capabilities: Vec::new(),
            }],
        },
    ))
}

fn build_nested_loop(config: &GeneratorConfig) -> Result<SurfaceSpec> {
    let bound = config.tunables.loop_bound.max(1) as i64;
    let machine_id = family_id(config.family_kind, config.seed, &config.tunables);

    let mut expected_final_fields = BTreeMap::new();
    expected_final_fields.insert("outer".to_string(), Value::Int { int: bound });

    let mut accepted_steps = vec![TraceStepSpec {
        transition: "enter_counting".to_string(),
    }];
    for _ in 0..bound {
        for _ in 0..bound {
            accepted_steps.push(TraceStepSpec {
                transition: "increment_inner".to_string(),
            });
        }
        accepted_steps.push(TraceStepSpec {
            transition: "step_outer".to_string(),
        });
    }
    accepted_steps.push(TraceStepSpec {
        transition: "finish".to_string(),
    });

    let mut rejected_steps = vec![TraceStepSpec {
        transition: "enter_counting".to_string(),
    }];
    for _ in 0..bound {
        rejected_steps.push(TraceStepSpec {
            transition: "increment_inner".to_string(),
        });
    }
    rejected_steps.push(TraceStepSpec {
        transition: "increment_inner".to_string(),
    });

    Ok(base_surface(
        MachineSpec {
            id: machine_id,
            description: Some("Deterministically generated nested bounded loops.".to_string()),
            initial_state: "start".to_string(),
            semantic_equivalence_class: Some(SemanticEquivalenceClass {
                id: "generated_nested_loop_v0".to_string(),
                description: None,
            }),
            states: vec![
                StateSpec {
                    id: "start".to_string(),
                    description: None,
                },
                StateSpec {
                    id: "counting".to_string(),
                    description: None,
                },
                StateSpec {
                    id: "finished".to_string(),
                    description: None,
                },
            ],
            fields: vec![
                FieldSpec {
                    id: "inner".to_string(),
                    field_type: ValueType::Int,
                    initial: Some(Value::Int { int: 0 }),
                    visibility: FieldVisibility::Private,
                },
                FieldSpec {
                    id: "outer".to_string(),
                    field_type: ValueType::Int,
                    initial: Some(Value::Int { int: 0 }),
                    visibility: FieldVisibility::Public,
                },
                FieldSpec {
                    id: "bound".to_string(),
                    field_type: ValueType::Int,
                    initial: Some(Value::Int { int: bound }),
                    visibility: FieldVisibility::Public,
                },
            ],
            transitions: vec![
                TransitionSpec {
                    id: "enter_counting".to_string(),
                    from: "start".to_string(),
                    to: "counting".to_string(),
                    guard: GuardSpec::Bool(true),
                    actions: Vec::new(),
                },
                TransitionSpec {
                    id: "increment_inner".to_string(),
                    from: "counting".to_string(),
                    to: "counting".to_string(),
                    guard: lt_field_field("inner", "bound"),
                    actions: vec![add_assign_int("inner", 1)],
                },
                TransitionSpec {
                    id: "step_outer".to_string(),
                    from: "counting".to_string(),
                    to: "counting".to_string(),
                    guard: eq_field_field("inner", "bound"),
                    actions: vec![
                        add_assign_int("outer", 1),
                        ActionSpec::Assign {
                            assign: AssignAction {
                                field: "inner".to_string(),
                                value: int_operand(0),
                            },
                        },
                    ],
                },
                TransitionSpec {
                    id: "finish".to_string(),
                    from: "counting".to_string(),
                    to: "finished".to_string(),
                    guard: eq_field_field("outer", "bound"),
                    actions: Vec::new(),
                },
            ],
            loops: vec![
                LoopSpec {
                    id: "inner_loop".to_string(),
                    bound: Some(lte_field_field("inner", "bound")),
                    body: vec!["increment_inner".to_string()],
                    metadata: BTreeMap::from([(
                        "max_unroll".to_string(),
                        Value::Int { int: bound },
                    )]),
                },
                LoopSpec {
                    id: "outer_loop".to_string(),
                    bound: Some(lte_field_field("outer", "bound")),
                    body: vec!["step_outer".to_string()],
                    metadata: BTreeMap::from([(
                        "max_unroll".to_string(),
                        Value::Int { int: bound },
                    )]),
                },
            ],
            invariants: vec![InvariantSpec {
                id: "inner_at_or_below_bound".to_string(),
                guard: lte_field_field("inner", "bound"),
                scope: Some("trace".to_string()),
            }],
            observations: vec![ObserveSpec {
                id: "outer_observation".to_string(),
                field: "outer".to_string(),
                visibility: FieldVisibility::Public,
            }],
            witness_policy: Default::default(),
            public_inputs: Vec::new(),
            private_witnesses: Vec::new(),
        },
        OracleSpec {
            accepted_traces: vec![TraceSpec {
                id: "generated_accepts_nested_reach_outer_bound".to_string(),
                initial_state: None,
                initial_fields: BTreeMap::new(),
                steps: accepted_steps,
                expected_final_state: Some("finished".to_string()),
                expected_final_fields,
                expected_verdict: Some(ExpectedVerdict::Accept),
                requires_capabilities: Vec::new(),
            }],
            rejected_traces: vec![TraceSpec {
                id: "generated_rejects_inner_overflow".to_string(),
                initial_state: None,
                initial_fields: BTreeMap::new(),
                steps: rejected_steps,
                expected_final_state: None,
                expected_final_fields: BTreeMap::new(),
                expected_verdict: Some(ExpectedVerdict::Reject),
                requires_capabilities: Vec::new(),
            }],
        },
    ))
}

fn build_guard_heavy_machine(config: &GeneratorConfig) -> Result<SurfaceSpec> {
    let bound = config.tunables.loop_bound.max(1) as i64;
    let machine_id = family_id(config.family_kind, config.seed, &config.tunables);

    let mut expected_final_fields = BTreeMap::new();
    expected_final_fields.insert("value".to_string(), Value::Int { int: bound });
    expected_final_fields.insert("locked".to_string(), Value::Bool { bool: false });

    let mut accepted_steps = vec![TraceStepSpec {
        transition: "acquire".to_string(),
    }];
    for _ in 0..bound {
        accepted_steps.push(TraceStepSpec {
            transition: "advance".to_string(),
        });
    }
    accepted_steps.push(TraceStepSpec {
        transition: "finish".to_string(),
    });

    let rejected_steps = vec![
        TraceStepSpec {
            transition: "acquire".to_string(),
        },
        TraceStepSpec {
            transition: "advance".to_string(),
        },
        TraceStepSpec {
            transition: "release".to_string(),
        },
        TraceStepSpec {
            transition: "advance".to_string(),
        },
    ];

    Ok(base_surface(
        MachineSpec {
            id: machine_id,
            description: Some("Deterministically generated guard-heavy machine.".to_string()),
            initial_state: "open".to_string(),
            semantic_equivalence_class: Some(SemanticEquivalenceClass {
                id: "generated_guard_heavy_machine_v0".to_string(),
                description: None,
            }),
            states: vec![
                StateSpec {
                    id: "open".to_string(),
                    description: None,
                },
                StateSpec {
                    id: "guarded".to_string(),
                    description: None,
                },
                StateSpec {
                    id: "done".to_string(),
                    description: None,
                },
            ],
            fields: vec![
                FieldSpec {
                    id: "value".to_string(),
                    field_type: ValueType::Int,
                    initial: Some(Value::Int { int: 0 }),
                    visibility: FieldVisibility::Public,
                },
                FieldSpec {
                    id: "bound".to_string(),
                    field_type: ValueType::Int,
                    initial: Some(Value::Int { int: bound }),
                    visibility: FieldVisibility::Public,
                },
                FieldSpec {
                    id: "locked".to_string(),
                    field_type: ValueType::Bool,
                    initial: Some(Value::Bool { bool: false }),
                    visibility: FieldVisibility::Private,
                },
            ],
            transitions: vec![
                TransitionSpec {
                    id: "acquire".to_string(),
                    from: "open".to_string(),
                    to: "guarded".to_string(),
                    guard: eq_field_bool("locked", false),
                    actions: vec![assign_bool("locked", true)],
                },
                TransitionSpec {
                    id: "release".to_string(),
                    from: "guarded".to_string(),
                    to: "open".to_string(),
                    guard: eq_field_bool("locked", true),
                    actions: vec![assign_bool("locked", false)],
                },
                TransitionSpec {
                    id: "advance".to_string(),
                    from: "guarded".to_string(),
                    to: "guarded".to_string(),
                    guard: and_guard(
                        eq_field_bool("locked", true),
                        lt_field_field("value", "bound"),
                    ),
                    actions: vec![add_assign_int("value", 1)],
                },
                TransitionSpec {
                    id: "finish".to_string(),
                    from: "guarded".to_string(),
                    to: "done".to_string(),
                    guard: and_guard(
                        eq_field_bool("locked", true),
                        eq_field_field("value", "bound"),
                    ),
                    actions: vec![assign_bool("locked", false)],
                },
            ],
            loops: vec![LoopSpec {
                id: "advance_until_bound".to_string(),
                bound: Some(lte_field_field("value", "bound")),
                body: vec!["advance".to_string()],
                metadata: BTreeMap::from([("max_unroll".to_string(), Value::Int { int: bound })]),
            }],
            invariants: vec![InvariantSpec {
                id: "locked_implies_value_at_or_below_bound".to_string(),
                guard: or_guard(
                    eq_field_bool("locked", false),
                    lte_field_field("value", "bound"),
                ),
                scope: Some("trace".to_string()),
            }],
            observations: vec![ObserveSpec {
                id: "value_observation".to_string(),
                field: "value".to_string(),
                visibility: FieldVisibility::Public,
            }],
            witness_policy: Default::default(),
            public_inputs: Vec::new(),
            private_witnesses: Vec::new(),
        },
        OracleSpec {
            accepted_traces: vec![TraceSpec {
                id: "generated_accepts_guarded_advance_to_bound".to_string(),
                initial_state: None,
                initial_fields: BTreeMap::new(),
                steps: accepted_steps,
                expected_final_state: Some("done".to_string()),
                expected_final_fields,
                expected_verdict: Some(ExpectedVerdict::Accept),
                requires_capabilities: Vec::new(),
            }],
            rejected_traces: vec![TraceSpec {
                id: "generated_rejects_advance_after_release".to_string(),
                initial_state: None,
                initial_fields: BTreeMap::new(),
                steps: rejected_steps,
                expected_final_state: None,
                expected_final_fields: BTreeMap::new(),
                expected_verdict: Some(ExpectedVerdict::Reject),
                requires_capabilities: Vec::new(),
            }],
        },
    ))
}

fn build_recursive_envelope(config: &GeneratorConfig) -> Result<SurfaceSpec> {
    let bound = config.tunables.loop_bound.max(1) as i64;
    let machine_id = family_id(config.family_kind, config.seed, &config.tunables);
    let envelope_digest = format!("envelope-{machine_id}");

    let mut expected_final_fields = BTreeMap::new();
    expected_final_fields.insert("depth".to_string(), Value::Int { int: bound });

    let mut accepted_steps = Vec::new();
    for _ in 0..bound {
        accepted_steps.push(TraceStepSpec {
            transition: "unfold".to_string(),
        });
    }
    accepted_steps.push(TraceStepSpec {
        transition: "seal".to_string(),
    });

    let mut rejected_steps = Vec::new();
    for _ in 0..bound {
        rejected_steps.push(TraceStepSpec {
            transition: "unfold".to_string(),
        });
    }
    rejected_steps.push(TraceStepSpec {
        transition: "unfold".to_string(),
    });

    Ok(base_surface(
        MachineSpec {
            id: machine_id,
            description: Some(
                "Deterministically generated recursion-envelope bounded fold.".to_string(),
            ),
            initial_state: "folding".to_string(),
            semantic_equivalence_class: Some(SemanticEquivalenceClass {
                id: "generated_recursive_envelope_v0".to_string(),
                description: None,
            }),
            states: vec![
                StateSpec {
                    id: "folding".to_string(),
                    description: None,
                },
                StateSpec {
                    id: "sealed".to_string(),
                    description: None,
                },
            ],
            fields: vec![
                FieldSpec {
                    id: "depth".to_string(),
                    field_type: ValueType::Int,
                    initial: Some(Value::Int { int: 0 }),
                    visibility: FieldVisibility::Public,
                },
                FieldSpec {
                    id: "bound".to_string(),
                    field_type: ValueType::Int,
                    initial: Some(Value::Int { int: bound }),
                    visibility: FieldVisibility::Public,
                },
            ],
            transitions: vec![
                TransitionSpec {
                    id: "unfold".to_string(),
                    from: "folding".to_string(),
                    to: "folding".to_string(),
                    guard: lt_field_field("depth", "bound"),
                    actions: vec![add_assign_int("depth", 1)],
                },
                TransitionSpec {
                    id: "seal".to_string(),
                    from: "folding".to_string(),
                    to: "sealed".to_string(),
                    guard: eq_field_field("depth", "bound"),
                    actions: Vec::new(),
                },
            ],
            loops: vec![LoopSpec {
                id: "recursion_envelope".to_string(),
                bound: Some(lte_field_field("depth", "bound")),
                body: vec!["unfold".to_string()],
                metadata: BTreeMap::from([
                    ("max_unroll".to_string(), Value::Int { int: bound }),
                    (
                        "envelope_digest".to_string(),
                        Value::Text {
                            text: envelope_digest.clone(),
                        },
                    ),
                ]),
            }],
            invariants: vec![InvariantSpec {
                id: "depth_at_or_below_bound".to_string(),
                guard: lte_field_field("depth", "bound"),
                scope: Some("trace".to_string()),
            }],
            observations: vec![ObserveSpec {
                id: "depth_observation".to_string(),
                field: "depth".to_string(),
                visibility: FieldVisibility::Public,
            }],
            witness_policy: Default::default(),
            public_inputs: Vec::new(),
            private_witnesses: Vec::new(),
        },
        OracleSpec {
            accepted_traces: vec![TraceSpec {
                id: "generated_accepts_envelope_seal".to_string(),
                initial_state: None,
                initial_fields: BTreeMap::new(),
                steps: accepted_steps,
                expected_final_state: Some("sealed".to_string()),
                expected_final_fields,
                expected_verdict: Some(ExpectedVerdict::Accept),
                requires_capabilities: Vec::new(),
            }],
            rejected_traces: vec![TraceSpec {
                id: "generated_rejects_envelope_overflow".to_string(),
                initial_state: None,
                initial_fields: BTreeMap::new(),
                steps: rejected_steps,
                expected_final_state: None,
                expected_final_fields: BTreeMap::new(),
                expected_verdict: Some(ExpectedVerdict::Reject),
                requires_capabilities: Vec::new(),
            }],
        },
    ))
}

fn build_memory_heavy_state_machine(config: &GeneratorConfig) -> Result<SurfaceSpec> {
    let memory_slots = config.tunables.memory_fields.max(2);
    let machine_id = family_id(config.family_kind, config.seed, &config.tunables);

    let mut fields = vec![
        FieldSpec {
            id: "cursor".to_string(),
            field_type: ValueType::Int,
            initial: Some(Value::Int { int: 0 }),
            visibility: FieldVisibility::Private,
        },
        FieldSpec {
            id: "ready".to_string(),
            field_type: ValueType::Bool,
            initial: Some(Value::Bool { bool: false }),
            visibility: FieldVisibility::Public,
        },
    ];
    for index in 0..memory_slots {
        fields.push(FieldSpec {
            id: format!("mem_{index}"),
            field_type: ValueType::Int,
            initial: Some(Value::Int { int: 0 }),
            visibility: FieldVisibility::Private,
        });
    }

    let mut accepted_steps = vec![
        TraceStepSpec {
            transition: "write_slot_0".to_string(),
        },
        TraceStepSpec {
            transition: "write_slot_1".to_string(),
        },
        TraceStepSpec {
            transition: "read_slot_0".to_string(),
        },
        TraceStepSpec {
            transition: "finish".to_string(),
        },
    ];
    if memory_slots > 2 {
        accepted_steps.insert(
            2,
            TraceStepSpec {
                transition: "write_slot_2".to_string(),
            },
        );
    }

    let rejected_steps = vec![
        TraceStepSpec {
            transition: "read_slot_0".to_string(),
        },
        TraceStepSpec {
            transition: "finish".to_string(),
        },
    ];

    let mut expected_final_fields = BTreeMap::new();
    expected_final_fields.insert("ready".to_string(), Value::Bool { bool: true });
    expected_final_fields.insert("cursor".to_string(), Value::Int { int: 1 });

    let mut transitions = vec![
        TransitionSpec {
            id: "write_slot_0".to_string(),
            from: "buffering".to_string(),
            to: "buffering".to_string(),
            guard: GuardSpec::Bool(true),
            actions: vec![ActionSpec::Assign {
                assign: AssignAction {
                    field: "mem_0".to_string(),
                    value: int_operand(1),
                },
            }],
        },
        TransitionSpec {
            id: "write_slot_1".to_string(),
            from: "buffering".to_string(),
            to: "buffering".to_string(),
            guard: GuardSpec::Bool(true),
            actions: vec![ActionSpec::Assign {
                assign: AssignAction {
                    field: "mem_1".to_string(),
                    value: int_operand(2),
                },
            }],
        },
        TransitionSpec {
            id: "read_slot_0".to_string(),
            from: "buffering".to_string(),
            to: "buffering".to_string(),
            guard: GuardSpec::Bool(true),
            actions: vec![ActionSpec::Assign {
                assign: AssignAction {
                    field: "cursor".to_string(),
                    value: field_operand("mem_0"),
                },
            }],
        },
        TransitionSpec {
            id: "finish".to_string(),
            from: "buffering".to_string(),
            to: "done".to_string(),
            guard: eq_field_int("cursor", 1),
            actions: vec![assign_bool("ready", true)],
        },
    ];
    if memory_slots > 2 {
        transitions.insert(
            2,
            TransitionSpec {
                id: "write_slot_2".to_string(),
                from: "buffering".to_string(),
                to: "buffering".to_string(),
                guard: GuardSpec::Bool(true),
                actions: vec![ActionSpec::Assign {
                    assign: AssignAction {
                        field: "mem_2".to_string(),
                        value: int_operand(3),
                    },
                }],
            },
        );
    }

    Ok(base_surface(
        MachineSpec {
            id: machine_id,
            description: Some(
                "Deterministically generated memory-heavy state machine.".to_string(),
            ),
            initial_state: "buffering".to_string(),
            semantic_equivalence_class: Some(SemanticEquivalenceClass {
                id: "generated_memory_heavy_state_machine_v0".to_string(),
                description: None,
            }),
            states: vec![
                StateSpec {
                    id: "buffering".to_string(),
                    description: None,
                },
                StateSpec {
                    id: "done".to_string(),
                    description: None,
                },
            ],
            fields,
            transitions,
            loops: Vec::new(),
            invariants: vec![InvariantSpec {
                id: "cursor_non_negative".to_string(),
                guard: GuardSpec::Expr(GuardExpr::Gte {
                    gte: BinaryGuard {
                        left: field_operand("cursor"),
                        right: int_operand(0),
                    },
                }),
                scope: Some("trace".to_string()),
            }],
            observations: vec![ObserveSpec {
                id: "ready_observation".to_string(),
                field: "ready".to_string(),
                visibility: FieldVisibility::Public,
            }],
            witness_policy: Default::default(),
            public_inputs: Vec::new(),
            private_witnesses: Vec::new(),
        },
        OracleSpec {
            accepted_traces: vec![TraceSpec {
                id: "generated_accepts_write_then_read".to_string(),
                initial_state: None,
                initial_fields: BTreeMap::new(),
                steps: accepted_steps,
                expected_final_state: Some("done".to_string()),
                expected_final_fields,
                expected_verdict: Some(ExpectedVerdict::Accept),
                requires_capabilities: Vec::new(),
            }],
            rejected_traces: vec![TraceSpec {
                id: "generated_rejects_stale_read".to_string(),
                initial_state: None,
                initial_fields: BTreeMap::new(),
                steps: rejected_steps,
                expected_final_state: None,
                expected_final_fields: BTreeMap::new(),
                expected_verdict: Some(ExpectedVerdict::Reject),
                requires_capabilities: Vec::new(),
            }],
        },
    ))
}

fn build_public_private_boundary_stress(config: &GeneratorConfig) -> Result<SurfaceSpec> {
    let nonce = config.seed.value as i64;
    let machine_id = family_id(config.family_kind, config.seed, &config.tunables);

    let mut expected_final_fields = BTreeMap::new();
    expected_final_fields.insert("matched".to_string(), Value::Bool { bool: true });

    Ok(base_surface(
        MachineSpec {
            id: machine_id,
            description: Some(
                "Deterministically generated public/private boundary stress machine.".to_string(),
            ),
            initial_state: "bind".to_string(),
            semantic_equivalence_class: Some(SemanticEquivalenceClass {
                id: "generated_public_private_boundary_stress_v0".to_string(),
                description: None,
            }),
            states: vec![
                StateSpec {
                    id: "bind".to_string(),
                    description: None,
                },
                StateSpec {
                    id: "done".to_string(),
                    description: None,
                },
            ],
            fields: vec![
                FieldSpec {
                    id: "public_nonce".to_string(),
                    field_type: ValueType::Int,
                    initial: Some(Value::Int { int: nonce }),
                    visibility: FieldVisibility::Public,
                },
                FieldSpec {
                    id: "secret_nonce".to_string(),
                    field_type: ValueType::Int,
                    initial: Some(Value::Int { int: nonce }),
                    visibility: FieldVisibility::Private,
                },
                FieldSpec {
                    id: "matched".to_string(),
                    field_type: ValueType::Bool,
                    initial: Some(Value::Bool { bool: false }),
                    visibility: FieldVisibility::Public,
                },
            ],
            transitions: vec![TransitionSpec {
                id: "bind_nonce".to_string(),
                from: "bind".to_string(),
                to: "done".to_string(),
                guard: eq_field_field("public_nonce", "secret_nonce"),
                actions: vec![assign_bool("matched", true)],
            }],
            loops: Vec::new(),
            invariants: Vec::new(),
            observations: vec![ObserveSpec {
                id: "matched_observation".to_string(),
                field: "matched".to_string(),
                visibility: FieldVisibility::Public,
            }],
            witness_policy: WitnessPolicy {
                public_inputs: vec!["public_nonce".to_string()],
                private_witnesses: vec!["secret_nonce".to_string()],
                aliasing_allowed: false,
            },
            public_inputs: vec![PublicInputSpec {
                id: "declared_public_nonce".to_string(),
                field: "public_nonce".to_string(),
                description: None,
            }],
            private_witnesses: vec![PrivateWitnessSpec {
                id: "declared_secret_nonce".to_string(),
                field: "secret_nonce".to_string(),
                description: None,
            }],
        },
        OracleSpec {
            accepted_traces: vec![TraceSpec {
                id: "generated_accepts_matching_nonce".to_string(),
                initial_state: None,
                initial_fields: BTreeMap::new(),
                steps: vec![TraceStepSpec {
                    transition: "bind_nonce".to_string(),
                }],
                expected_final_state: Some("done".to_string()),
                expected_final_fields,
                expected_verdict: Some(ExpectedVerdict::Accept),
                requires_capabilities: Vec::new(),
            }],
            rejected_traces: vec![TraceSpec {
                id: "generated_rejects_mismatched_nonce".to_string(),
                initial_state: None,
                initial_fields: BTreeMap::from([(
                    "public_nonce".to_string(),
                    Value::Int {
                        int: nonce.saturating_add(1),
                    },
                )]),
                steps: vec![TraceStepSpec {
                    transition: "bind_nonce".to_string(),
                }],
                expected_final_state: None,
                expected_final_fields: BTreeMap::new(),
                expected_verdict: Some(ExpectedVerdict::Reject),
                requires_capabilities: Vec::new(),
            }],
        },
    ))
}

fn build_zkml_control_flow_mixed(config: &GeneratorConfig) -> Result<SurfaceSpec> {
    let threshold = config.tunables.loop_bound.max(1) as i64;
    let confidence = threshold.saturating_add(1);
    let machine_id = family_id(config.family_kind, config.seed, &config.tunables);

    Ok(base_surface(
        MachineSpec {
            id: machine_id,
            description: Some(
                "Deterministically generated zkML/control-flow mixed machine.".to_string(),
            ),
            initial_state: "pending".to_string(),
            semantic_equivalence_class: Some(SemanticEquivalenceClass {
                id: "generated_zkml_control_flow_mixed_v0".to_string(),
                description: None,
            }),
            states: vec![
                StateSpec {
                    id: "pending".to_string(),
                    description: None,
                },
                StateSpec {
                    id: "accepted".to_string(),
                    description: None,
                },
                StateSpec {
                    id: "rejected".to_string(),
                    description: None,
                },
            ],
            fields: vec![
                FieldSpec {
                    id: "confidence".to_string(),
                    field_type: ValueType::Int,
                    initial: Some(Value::Int { int: confidence }),
                    visibility: FieldVisibility::Public,
                },
                FieldSpec {
                    id: "threshold".to_string(),
                    field_type: ValueType::Int,
                    initial: Some(Value::Int { int: threshold }),
                    visibility: FieldVisibility::Public,
                },
                FieldSpec {
                    id: "label".to_string(),
                    field_type: ValueType::Text,
                    initial: Some(Value::Text {
                        text: "candidate".to_string(),
                    }),
                    visibility: FieldVisibility::Public,
                },
            ],
            transitions: vec![
                TransitionSpec {
                    id: "accept_if_confident".to_string(),
                    from: "pending".to_string(),
                    to: "accepted".to_string(),
                    guard: gte_field_field("confidence", "threshold"),
                    actions: Vec::new(),
                },
                TransitionSpec {
                    id: "reject_if_low_confidence".to_string(),
                    from: "pending".to_string(),
                    to: "rejected".to_string(),
                    guard: GuardSpec::Expr(GuardExpr::Lt {
                        lt: BinaryGuard {
                            left: field_operand("confidence"),
                            right: field_operand("threshold"),
                        },
                    }),
                    actions: Vec::new(),
                },
            ],
            loops: Vec::new(),
            invariants: Vec::new(),
            observations: vec![
                ObserveSpec {
                    id: "confidence_observation".to_string(),
                    field: "confidence".to_string(),
                    visibility: FieldVisibility::Public,
                },
                ObserveSpec {
                    id: "label_observation".to_string(),
                    field: "label".to_string(),
                    visibility: FieldVisibility::Public,
                },
            ],
            witness_policy: Default::default(),
            public_inputs: Vec::new(),
            private_witnesses: Vec::new(),
        },
        OracleSpec {
            accepted_traces: vec![TraceSpec {
                id: "generated_accepts_control_flow".to_string(),
                initial_state: None,
                initial_fields: BTreeMap::new(),
                steps: vec![TraceStepSpec {
                    transition: "accept_if_confident".to_string(),
                }],
                expected_final_state: Some("accepted".to_string()),
                expected_final_fields: BTreeMap::new(),
                expected_verdict: Some(ExpectedVerdict::Accept),
                requires_capabilities: Vec::new(),
            }],
            rejected_traces: vec![TraceSpec {
                id: "generated_rejects_low_confidence_accept_attempt".to_string(),
                initial_state: None,
                initial_fields: BTreeMap::from([(
                    "confidence".to_string(),
                    Value::Int {
                        int: threshold.saturating_sub(1),
                    },
                )]),
                steps: vec![TraceStepSpec {
                    transition: "accept_if_confident".to_string(),
                }],
                expected_final_state: None,
                expected_final_fields: BTreeMap::new(),
                expected_verdict: Some(ExpectedVerdict::Reject),
                requires_capabilities: Vec::new(),
            }],
        },
    ))
}

fn base_surface(machine: MachineSpec, oracle: OracleSpec) -> SurfaceSpec {
    SurfaceSpec {
        machine,
        oracle,
        targets: vec![TargetSpec {
            id: "local_oracle".to_string(),
            kind: "local".to_string(),
            required_capabilities: Vec::new(),
        }],
        mutations: Vec::new(),
        evidence: EvidenceSpec {
            claim_boundary: ClaimBoundary::Level1LocalReplay,
            planned: false,
            notes: vec![
                "Generated local semantic fixture; not official benchmark evidence.".to_string(),
            ],
        },
    }
}

fn field_operand(field: &str) -> crate::dsl::expr::OperandSpec {
    crate::dsl::expr::OperandSpec::Field {
        field: field.to_string(),
    }
}

fn int_operand(value: i64) -> crate::dsl::expr::OperandSpec {
    crate::dsl::expr::OperandSpec::Literal(Value::Int { int: value })
}

fn eq_field_int(field: &str, value: i64) -> GuardSpec {
    GuardSpec::Expr(GuardExpr::Eq {
        eq: BinaryGuard {
            left: field_operand(field),
            right: int_operand(value),
        },
    })
}

fn eq_field_bool(field: &str, value: bool) -> GuardSpec {
    GuardSpec::Expr(GuardExpr::Eq {
        eq: BinaryGuard {
            left: field_operand(field),
            right: crate::dsl::expr::OperandSpec::Literal(Value::Bool { bool: value }),
        },
    })
}

fn and_guard(left: GuardSpec, right: GuardSpec) -> GuardSpec {
    GuardSpec::Expr(GuardExpr::And {
        and: vec![left, right],
    })
}

fn or_guard(left: GuardSpec, right: GuardSpec) -> GuardSpec {
    GuardSpec::Expr(GuardExpr::Or {
        or: vec![left, right],
    })
}

fn assign_bool(field: &str, value: bool) -> ActionSpec {
    ActionSpec::Assign {
        assign: AssignAction {
            field: field.to_string(),
            value: crate::dsl::expr::OperandSpec::Literal(Value::Bool { bool: value }),
        },
    }
}

fn eq_field_field(left: &str, right: &str) -> GuardSpec {
    GuardSpec::Expr(GuardExpr::Eq {
        eq: BinaryGuard {
            left: field_operand(left),
            right: field_operand(right),
        },
    })
}

fn lt_field_field(left: &str, right: &str) -> GuardSpec {
    GuardSpec::Expr(GuardExpr::Lt {
        lt: BinaryGuard {
            left: field_operand(left),
            right: field_operand(right),
        },
    })
}

fn lte_field_field(left: &str, right: &str) -> GuardSpec {
    GuardSpec::Expr(GuardExpr::Lte {
        lte: BinaryGuard {
            left: field_operand(left),
            right: field_operand(right),
        },
    })
}

fn gte_field_field(left: &str, right: &str) -> GuardSpec {
    GuardSpec::Expr(GuardExpr::Gte {
        gte: BinaryGuard {
            left: field_operand(left),
            right: field_operand(right),
        },
    })
}

fn add_assign_int(field: &str, value: i64) -> ActionSpec {
    ActionSpec::AddAssign {
        add_assign: AssignAction {
            field: field.to_string(),
            value: int_operand(value),
        },
    }
}
