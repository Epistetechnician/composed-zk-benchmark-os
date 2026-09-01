# Oak Lab constrained update policy V5 executable protocol compiler

State slice: `oaklab-experience-learning-constrained-update-policy-v5`

Status: `frozen_pending_independent_review`

Claim ceiling: `LocalDevelopmentOakLabConstrainedUpdatePolicyV5ProtocolCompilerOnly`

## Boundary

V5 is a compiler-only identity. It preserves the complete-policy estimand
from the closed V4 theory but does not import V4 code, receipts, streams, or
scientific artifacts. The compiler has no learner, stream runner, backend,
energy, Astral, or plasticity-guard imports. No V5 fit, tune, assessment, real
campaign, or energy capture may start before an independent review accepts the
exact frozen bytes listed in the review packet.

## Compiler output

`v5_protocol_spec.json` is the source contract. `compile_v5_protocol.py`
canonicalizes the source, validates its closed-world shape, computes the exact
source digest, emits section digests, and produces a compiled artifact whose
digest excludes only its own digest field. The compiler also emits a concrete
test vector: the framed PRNG seed bytes, root digest, first twelve SplitMix64
outputs, first `uniform53`, first twelve-draw normal approximation, and the
fit-action hash for `(fit, sparse_predictable_v5, 4000, 0)`.

`validate_v5_protocol_compilation.py` independently reimplements canonical
JSON, framing, SplitMix64, test-vector derivation, source/section/compiled
digests, closed-world schemas, transition indices, generator rosters, typed
operation AST presence, ablation/multiplicity tables, shift-bounded adaptation
windows, and the assessment-absence boundary. It does not call compiler
functions.

## Seven compiled sections

1. `hash_prng_transcript`: exact UTF-8/LF source bytes, LP32 variable fields,
   raw fixed-width digest/integer fields, SplitMix64 arithmetic, unconditional
   draw transcripts, rational action thresholds, and a recomputable vector.
2. `controller_transition_table`: indexed trajectory initialization,
   pre-action observation, action selection, prior-action credit, model action,
   pending-state publication, terminal handling, and counter finalization. The
   pending roster is explicit; undeclared state is invalid.
3. `generator_roster`: disjoint fit/tune/assessment seeds, eight exact stream
   IDs including `pure_noise_v5`, typed draw rosters with fixed ordinals,
   segment boundaries, equations, event rules, and oracle features.
4. `operation_and_byte_algebra`: numeric widths, typed formula ASTs, primitive
   operation accounting, model/controller formulas, and packed logical layouts.
5. `ablation_execution_multiplicity`: fixed participation order, candidate and
   control roles, paired transforms, three Holm groups, and gate predicates.
6. `adaptation_metrics`: arm-specific sixteen-row median baselines, 1.10
   thresholds, adjacent eight-row windows wholly inside each shift segment,
   integer lag, and next-shift censoring.
7. `lock_counter_control_schemas`: closed-world compile, fit, tune, counter,
   control, assessment-absence, and validator receipt schemas with required
   digest bindings.

## Verification record

The compiler output, `--check` path, independent validator, and five hermetic
tamper/determinism tests pass. The artifact remains assessment-absent and the
only allowed result is a pending independent review. A review rejection closes
V5; acceptance authorizes a separately reviewed learner implementation but is
not a scientific result or a SOTA claim.
