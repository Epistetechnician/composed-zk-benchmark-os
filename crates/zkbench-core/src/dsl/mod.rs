//! Surface DSL parsing, Parsed AST validation, Semantic IR lowering, and local
//! oracle evaluation.

pub mod ast;
pub mod expr;
pub mod ir;
pub mod lowering;
pub mod oracle;
pub mod oracle_completeness;
pub mod parser;
pub mod surface;
pub mod validation;

pub use ast::ParsedAst;
pub use expr::{ActionSpec, AssignAction, BinaryGuard, GuardExpr, GuardSpec, OperandSpec};
pub use ir::{
    CanonicalAction, CanonicalField, CanonicalGuard, CanonicalInvariant, CanonicalMachine,
    CanonicalOracle, CanonicalState, CanonicalTransition, SemanticIr,
};
pub use lowering::lower_to_ir;
pub use oracle::{evaluate_trace, OracleOutcome};
pub use oracle_completeness::{
    audit_oracle_completeness, OracleCompletenessAudit, OracleCompletenessConstruct,
    OracleCompletenessConstructKind, OracleCompletenessLabel,
};
pub use parser::{parse_yaml_ast, parse_yaml_spec};
pub use surface::{
    EvidenceSpec, FieldSpec, InvariantSpec, LoopSpec, MachineSpec, ObserveSpec, OracleSpec,
    PrivateWitnessSpec, PublicInputSpec, SemanticEquivalenceClass, StateSpec, SurfaceSpec,
    TargetSpec, TraceSpec, TraceStepSpec, TransitionSpec, WitnessPolicy,
};
pub use validation::validate_surface_spec;
