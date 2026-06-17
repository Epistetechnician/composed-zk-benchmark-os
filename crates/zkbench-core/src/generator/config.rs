//! Deterministic generator configuration.

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};

use super::templates::FamilyKind;

/// Deterministic generator seed. No system randomness is used.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct GeneratorSeed {
    /// Seed value used for deterministic variation.
    pub value: u64,
}

impl Default for GeneratorSeed {
    fn default() -> Self {
        Self { value: 1 }
    }
}

/// Generator profile label.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Deserialize)]
pub enum GeneratorProfile {
    /// Small local test profile.
    #[default]
    Small,
    /// Medium local test profile.
    Medium,
    /// Future placeholder profile for heavier local generation.
    Stress,
}

/// Generator tunables. Unsupported tunables are recorded in generated metadata
/// rather than silently treated as evidence.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GeneratorTunables {
    /// Number of states requested.
    pub state_count: usize,
    /// Branching factor requested.
    pub branching_factor: usize,
    /// Loop bound requested.
    pub loop_bound: usize,
    /// Trace length requested.
    pub trace_length: usize,
    /// Guard complexity requested.
    pub guard_complexity: usize,
    /// Additional memory-like fields requested.
    pub memory_fields: usize,
    /// Nondeterminism policy label.
    pub nondeterminism_policy: String,
    /// Public/private boundary complexity requested.
    pub public_private_boundary_complexity: usize,
}

impl Default for GeneratorTunables {
    fn default() -> Self {
        Self {
            state_count: 3,
            branching_factor: 2,
            loop_bound: 3,
            trace_length: 2,
            guard_complexity: 1,
            memory_fields: 0,
            nondeterminism_policy: "deterministic".to_string(),
            public_private_boundary_complexity: 0,
        }
    }
}

/// Small, safe generation limits.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GeneratorLimits {
    /// Maximum states.
    pub max_states: usize,
    /// Maximum transitions.
    pub max_transitions: usize,
    /// Maximum fields.
    pub max_fields: usize,
    /// Maximum trace steps.
    pub max_trace_steps: usize,
    /// Maximum loop bound.
    pub max_loop_bound: usize,
    /// Maximum mutations per instance.
    pub max_mutations_per_instance: usize,
}

impl Default for GeneratorLimits {
    fn default() -> Self {
        Self {
            max_states: 16,
            max_transitions: 64,
            max_fields: 16,
            max_trace_steps: 64,
            max_loop_bound: 16,
            max_mutations_per_instance: 8,
        }
    }
}

/// Full deterministic generator config.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GeneratorConfig {
    /// Family kind.
    pub family_kind: FamilyKind,
    /// Seed.
    pub seed: GeneratorSeed,
    /// Profile.
    pub profile: GeneratorProfile,
    /// Tunables.
    pub tunables: GeneratorTunables,
    /// Limits.
    pub limits: GeneratorLimits,
}

impl GeneratorConfig {
    /// Baseline FSM config.
    pub fn baseline_fsm() -> Self {
        Self {
            family_kind: FamilyKind::BaselineFsm,
            seed: GeneratorSeed::default(),
            profile: GeneratorProfile::default(),
            tunables: GeneratorTunables::default(),
            limits: GeneratorLimits::default(),
        }
    }

    /// Branching FSM config.
    pub fn branching_fsm() -> Self {
        Self {
            family_kind: FamilyKind::BranchingFsm,
            seed: GeneratorSeed::default(),
            profile: GeneratorProfile::default(),
            tunables: GeneratorTunables {
                state_count: 4,
                branching_factor: 2,
                trace_length: 2,
                ..GeneratorTunables::default()
            },
            limits: GeneratorLimits::default(),
        }
    }

    /// Bounded counter loop config.
    pub fn bounded_counter_loop() -> Self {
        Self {
            family_kind: FamilyKind::BoundedCounterLoop,
            seed: GeneratorSeed::default(),
            profile: GeneratorProfile::default(),
            tunables: GeneratorTunables {
                state_count: 2,
                trace_length: 4,
                loop_bound: 3,
                ..GeneratorTunables::default()
            },
            limits: GeneratorLimits::default(),
        }
    }

    /// Set seed value.
    pub fn seed(mut self, value: u64) -> Self {
        self.seed = GeneratorSeed { value };
        self
    }

    /// Set state count.
    pub fn state_count(mut self, value: usize) -> Self {
        self.tunables.state_count = value;
        self
    }

    /// Set branching factor.
    pub fn branching_factor(mut self, value: usize) -> Self {
        self.tunables.branching_factor = value;
        self
    }

    /// Set loop bound.
    pub fn loop_bound(mut self, value: usize) -> Self {
        self.tunables.loop_bound = value;
        self.tunables.trace_length = value.saturating_add(1);
        self
    }

    /// Set trace length.
    pub fn trace_length(mut self, value: usize) -> Self {
        self.tunables.trace_length = value;
        self
    }

    /// Set limits.
    pub fn limits(mut self, limits: GeneratorLimits) -> Self {
        self.limits = limits;
        self
    }

    /// Validate config and limits.
    pub fn validate(&self) -> Result<()> {
        if !self.family_kind.is_implemented() {
            return Err(ZkBenchError::generation(
                "generator.family_kind",
                format!(
                    "family kind {:?} is a future placeholder and is not implemented locally",
                    self.family_kind
                ),
            ));
        }
        if self.tunables.state_count > self.limits.max_states {
            return Err(ZkBenchError::generation(
                "generator.tunables.state_count",
                format!(
                    "state_count {} exceeds max_states {}",
                    self.tunables.state_count, self.limits.max_states
                ),
            ));
        }
        if self.tunables.loop_bound > self.limits.max_loop_bound {
            return Err(ZkBenchError::generation(
                "generator.tunables.loop_bound",
                format!(
                    "loop_bound {} exceeds max_loop_bound {}",
                    self.tunables.loop_bound, self.limits.max_loop_bound
                ),
            ));
        }
        if self.tunables.trace_length > self.limits.max_trace_steps {
            return Err(ZkBenchError::generation(
                "generator.tunables.trace_length",
                format!(
                    "trace_length {} exceeds max_trace_steps {}",
                    self.tunables.trace_length, self.limits.max_trace_steps
                ),
            ));
        }
        let field_count = match self.family_kind {
            FamilyKind::BaselineFsm => 1usize.saturating_add(self.tunables.memory_fields),
            FamilyKind::BranchingFsm | FamilyKind::BoundedCounterLoop => {
                2usize.saturating_add(self.tunables.memory_fields)
            }
            FamilyKind::NestedLoop
            | FamilyKind::RecursiveEnvelope
            | FamilyKind::MemoryHeavyStateMachine
            | FamilyKind::GuardHeavyMachine
            | FamilyKind::PublicPrivateBoundaryStress
            | FamilyKind::ZkMlControlFlowMixed => {
                1usize.saturating_add(self.tunables.memory_fields)
            }
        };
        if field_count > self.limits.max_fields {
            return Err(ZkBenchError::generation(
                "generator.tunables.memory_fields",
                format!(
                    "requested field count {} exceeds max_fields {}",
                    field_count, self.limits.max_fields
                ),
            ));
        }

        match self.family_kind {
            FamilyKind::BaselineFsm => {
                if self.tunables.state_count < 2 {
                    return Err(ZkBenchError::generation(
                        "generator.tunables.state_count",
                        "BaselineFsm requires state_count >= 2",
                    ));
                }
                let required_steps = self.tunables.state_count.saturating_sub(1);
                if self.tunables.trace_length < required_steps {
                    return Err(ZkBenchError::generation(
                        "generator.tunables.trace_length",
                        format!(
                            "BaselineFsm requires trace_length >= state_count - 1 ({required_steps})"
                        ),
                    ));
                }
                if required_steps > self.limits.max_transitions {
                    return Err(ZkBenchError::generation(
                        "generator.tunables.state_count",
                        format!(
                            "BaselineFsm transition count {required_steps} exceeds max_transitions {}",
                            self.limits.max_transitions
                        ),
                    ));
                }
            }
            FamilyKind::BranchingFsm => {
                if self.tunables.state_count < 4 {
                    return Err(ZkBenchError::generation(
                        "generator.tunables.state_count",
                        "BranchingFsm requires state_count >= 4",
                    ));
                }
                if self.tunables.branching_factor < 2 {
                    return Err(ZkBenchError::generation(
                        "generator.tunables.branching_factor",
                        "BranchingFsm requires branching_factor >= 2",
                    ));
                }
                let branch_count = self
                    .tunables
                    .branching_factor
                    .min(self.tunables.state_count.saturating_sub(2));
                let transition_count = branch_count.saturating_mul(2);
                if transition_count > self.limits.max_transitions {
                    return Err(ZkBenchError::generation(
                        "generator.tunables.branching_factor",
                        format!(
                            "BranchingFsm transition count {transition_count} exceeds max_transitions {}",
                            self.limits.max_transitions
                        ),
                    ));
                }
            }
            FamilyKind::BoundedCounterLoop => {
                if self.tunables.loop_bound == 0 {
                    return Err(ZkBenchError::generation(
                        "generator.tunables.loop_bound",
                        "BoundedCounterLoop requires loop_bound >= 1",
                    ));
                }
                if 2 > self.limits.max_transitions {
                    return Err(ZkBenchError::generation(
                        "generator.limits.max_transitions",
                        "BoundedCounterLoop requires max_transitions >= 2",
                    ));
                }
                let required_trace_steps = self.tunables.loop_bound.saturating_add(1);
                if required_trace_steps > self.limits.max_trace_steps {
                    return Err(ZkBenchError::generation(
                        "generator.tunables.loop_bound",
                        format!(
                            "BoundedCounterLoop trace steps {required_trace_steps} exceed max_trace_steps {}",
                            self.limits.max_trace_steps
                        ),
                    ));
                }
            }
            FamilyKind::NestedLoop
            | FamilyKind::RecursiveEnvelope
            | FamilyKind::MemoryHeavyStateMachine
            | FamilyKind::GuardHeavyMachine
            | FamilyKind::PublicPrivateBoundaryStress
            | FamilyKind::ZkMlControlFlowMixed => {}
        }

        Ok(())
    }
}
