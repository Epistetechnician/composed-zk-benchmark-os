# DSL Schema

## Purpose

The v0 DSL defines semantic benchmark cases. It is a specification format, not executable code. The DSL output is a canonical benchmark spec that lowers into Semantic IR.

## Canonical Pipeline

```text
Surface DSL
  -> parsed AST
  -> canonical semantic IR
  -> generated benchmark family
  -> concrete benchmark instance
  -> mutation variant
  -> backend artifact
  -> replay result
  -> evidence record
  -> scored report
```

## Required Entities

The v0 schema includes:

- machine
- state
- field
- transition
- guard
- action
- loop
- invariant
- observe
- target
- mutation
- evidence
- accepted_trace
- rejected_trace
- expected_result
- oracle
- witness_policy
- public_inputs
- private_witnesses
- semantic_equivalence_class

## YAML-Like Pseudo-Schema

```yaml
machine:
  id: string
  description: string
  semantic_equivalence_class: string
  state:
    id: string
    fields:
      - field:
          name: string
          type: bool | u32 | u64 | field_element | bytes | vector
          visibility: public | private | internal
          initial: expression
          constraints: [expression]
  transitions:
    - transition:
        id: string
        from: state_id
        to: state_id
        guard: expression
        action:
          updates:
            - field: expression
        expected_effect: expression
  loops:
    - loop:
        id: string
        bound: expression
        body: [transition_id]
        unroll_policy: bounded | symbolic | backend_specific
  invariants:
    - invariant:
        id: string
        expression: expression
        scope: machine | state | transition | loop | trace
  oracle:
    accepted_trace: [trace_pattern]
    rejected_trace: [trace_pattern]
    expected_result: expected_accept | expected_reject | expected_backend_error | expected_inconclusive | expected_capability_gap | expected_unsound_if_accepted
    witness_policy:
      public_inputs: [field_name]
      private_witnesses: [field_name]
      aliasing_allowed: false
  mutations:
    - mutation:
        id: string
        class: missing_constraints | corrupted_guards | bad_counters | stale_state_reads | invalid_unroll_bounds | nondeterministic_transition_injection | recursion_envelope_mismatch | public_private_boundary_mismatch | witness_aliasing | invariant_weakening | invariant_strengthening | observation_omission | semantic_no_op_drift | trace_ordering_corruption
        target: transition_id | state_id | loop_id | invariant_id | witness_policy
        expected_verdict: expected_accept | expected_reject | expected_backend_error | expected_inconclusive | expected_capability_gap | expected_unsound_if_accepted
  observe:
    metrics:
      - prover_time
      - verifier_latency
      - proof_size
      - memory_use
      - constraint_count
      - recursion_depth
      - negative_test_result
  target:
    backends: [backend_id]
    required_capabilities: [capability_flag]
  evidence:
    requested_level: Level 0
    claim_boundary_max: Level 1
```

## Example 1: Baseline FSM

```yaml
machine:
  id: baseline_toggle
  state:
    id: Toggle
    fields:
      - field: { name: bit, type: bool, visibility: public, initial: false }
  transitions:
    - transition:
        id: flip
        from: Toggle
        to: Toggle
        guard: true
        action: { updates: [{ bit: "not bit" }] }
  invariants:
    - invariant: { id: bit_is_bool, expression: "bit in {false,true}", scope: state }
  oracle:
    accepted_trace: ["flip repeated any bounded length"]
    rejected_trace: ["state.bit outside bool"]
    expected_result: expected_accept
```

Intended behavior: each step flips a public bit.

Expected accepted traces: bounded sequences of `flip` where `bit` alternates.

Expected rejected traces: non-boolean state, skipped update, or double update.

Mutation hooks: missing update, corrupted guard, semantic no-op drift.

Observed metrics: verifier latency, constraint count, negative-test result.

Claim boundary: Level 0 in this scaffold.

## Example 2: Bounded Counter Loop

```yaml
machine:
  id: bounded_counter
  state:
    id: Counter
    fields:
      - field: { name: i, type: u32, visibility: public, initial: 0 }
      - field: { name: acc, type: u64, visibility: private, initial: 0 }
  loops:
    - loop: { id: count_to_n, bound: "n <= 64", body: [inc] }
  transitions:
    - transition:
        id: inc
        from: Counter
        to: Counter
        guard: "i < n"
        action: { updates: [{ i: "i + 1" }, { acc: "acc + i" }] }
  oracle:
    accepted_trace: ["n valid and i reaches n"]
    rejected_trace: ["i skips", "acc uses stale i", "bound exceeded"]
    expected_result: expected_accept
```

Intended behavior: bounded loop increments `i` and accumulates.

Expected accepted traces: exactly `n` increments with consistent accumulator.

Expected rejected traces: invalid unroll bound, bad counter, stale state read.

Mutation hooks: bad counters, stale state reads, invalid unroll bounds.

Observed metrics: prover time, verifier latency, constraint count.

Claim boundary: Level 0.

## Example 3: Recursive Loop Envelope

```yaml
machine:
  id: recursive_envelope
  state:
    id: Envelope
    fields:
      - field: { name: depth, type: u32, visibility: public, initial: 0 }
      - field: { name: digest, type: bytes, visibility: public, initial: "root" }
  loops:
    - loop: { id: recurse, bound: "depth <= max_depth", body: [fold] }
  transitions:
    - transition:
        id: fold
        from: Envelope
        to: Envelope
        guard: "depth < max_depth"
        action: { updates: [{ depth: "depth + 1" }, { digest: "hash(digest, depth)" }] }
  oracle:
    accepted_trace: ["digest chain matches depth"]
    rejected_trace: ["depth and digest diverge"]
    expected_result: expected_accept
```

Intended behavior: each recursive fold binds depth to digest.

Expected accepted traces: hash chain matches public depth.

Expected rejected traces: recursion-envelope mismatch.

Mutation hooks: recursion-envelope mismatch, observation omission.

Observed metrics: recursion depth, proof size, verifier latency.

Claim boundary: Level 0.

## Example 4: Adversarial Stale-Read Machine

```yaml
machine:
  id: stale_read_case
  state:
    id: Account
    fields:
      - field: { name: balance, type: u64, visibility: private, initial: 10 }
      - field: { name: spent, type: u64, visibility: public, initial: 0 }
  transitions:
    - transition:
        id: spend
        guard: "balance >= amount"
        action: { updates: [{ balance: "balance - amount" }, { spent: "spent + amount" }] }
  mutations:
    - mutation:
        id: stale_balance_guard
        class: stale_state_reads
        target: spend
        expected_verdict: expected_unsound_if_accepted
  oracle:
    accepted_trace: ["balance checked before every spend"]
    rejected_trace: ["guard reads prior balance after update"]
    expected_result: expected_reject
```

Intended behavior: every spend checks current balance.

Expected accepted traces: no overspend.

Expected rejected traces: stale guard permits overspend.

Mutation hooks: stale state reads, corrupted guards.

Observed metrics: negative-test result, unsound-acceptance detection.

Claim boundary: Level 0.

## Example 5: zkML/Control-Flow Mixed Workload

```yaml
machine:
  id: inference_gate
  state:
    id: InferenceFlow
    fields:
      - field: { name: score, type: field_element, visibility: private, initial: 0 }
      - field: { name: threshold, type: field_element, visibility: public, initial: 7 }
      - field: { name: decision, type: bool, visibility: public, initial: false }
  transitions:
    - transition:
        id: classify
        guard: "model_output_available"
        action: { updates: [{ score: "model(input)" }, { decision: "score >= threshold" }] }
  oracle:
    accepted_trace: ["decision matches thresholded score"]
    rejected_trace: ["decision true while score below threshold"]
    expected_result: expected_accept
```

Intended behavior: control-flow decision is tied to private model score and public threshold.

Expected accepted traces: decision matches score comparison.

Expected rejected traces: public decision detached from private witness.

Mutation hooks: public/private boundary mismatch, witness aliasing.

Observed metrics: zkML metrics, verifier timing, negative-test result.

Claim boundary: Level 0.

## Example 6: Public/Private Boundary Mismatch

```yaml
machine:
  id: boundary_mismatch
  state:
    id: Boundary
    fields:
      - field: { name: public_nonce, type: u64, visibility: public, initial: 1 }
      - field: { name: secret_nonce, type: u64, visibility: private, initial: 1 }
  oracle:
    witness_policy:
      public_inputs: [public_nonce]
      private_witnesses: [secret_nonce]
      aliasing_allowed: false
    accepted_trace: ["public_nonce != secret_nonce OR non_alias proof"]
    rejected_trace: ["public input aliases private witness"]
    expected_result: expected_reject
```

Intended behavior: public and private fields stay distinct.

Expected accepted traces: no aliasing.

Expected rejected traces: public/private boundary mismatch.

Mutation hooks: witness aliasing, public/private boundary mismatch.

Observed metrics: public-private-boundary check, negative-test result.

Claim boundary: Level 0.

## Parser Boundary

No executable parser code exists in this scaffold. Future parser work must implement schema validation and lower into Semantic IR before any backend adapter is built.

