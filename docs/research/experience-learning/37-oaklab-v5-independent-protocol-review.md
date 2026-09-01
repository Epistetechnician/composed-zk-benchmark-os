# Oak Lab V5 independent protocol review

State slice: `oaklab-experience-learning-constrained-update-policy-v5`

Reviewer: `independent-agent-review`

Decision: `REJECT`

Implementation authorization: `false`

Fit, tune, assessment, real-execution, and energy authorization: `false`

Claim ceiling: `ProtocolReviewRejectedNoExecution`

Astral: `isolated_not_run`

The dispatched V5 identities were rechecked against the repository before the
substantive review. The review packet is stale: it declares an older
`AGENTS.md` digest (`7068251a...`), while the current bytes are
`4d4c7901...`. Under the packet's fail-closed rule, that hash drift alone
requires rejection. The compiler `--check` path, independent validator, compiler-only tests, canonical
section digests, compiled digest, and PRNG/action test vector all recomputed
successfully. The protocol is nevertheless rejected because the seven
sections still contain material degrees of freedom and contradictory schemas.
This review authorizes no V5 implementation or execution.

## Exact review identity

- `AGENTS.md` (observed current bytes): `4d4c790169f0521e9d419687da38fd001505fbde831e7f9155d237d30b1496f5`
- `experiments/experience_learning/v5_protocol_spec.json`: `ac02dca181feea32b1e9547e381c94c9399f3a34c4bc0ac3df2ed9095b0c813c`
- `experiments/experience_learning/compile_v5_protocol.py`: `82a5075a1c39c629ec4b5d169d1d4c171f1a5de7fff791e5b2734538e5e211ad`
- `experiments/experience_learning/validate_v5_protocol_compilation.py`: `b4ab7e542a4665de2e2cc6837fe828cea65304ab593d534862b0487b996f9c22`
- `experiments/experience_learning/v5_compiled_protocol.json`: `9be25c99303912b695e025f97da02a5ccd7459896855d24eb9c9ea9e54e188d3`
- `experiments/experience_learning/tests/test_v5_protocol_compiler.py`: `f3d4d46c2b530491691d5abfc4203fc46a6fb8bcfa0386b20452097a49b509eb`
- `docs/research/experience-learning/35-oaklab-v5-protocol-compiler.md`: `58478e30f6441c0c783b97ef514c58731f0eef0231813c7d2aaa9dddac1142ae`
- `docs/research/experience-learning/36-oaklab-v5-independent-review-packet.md`: `8fa7a1e197995e7938cafbe0779f90b37e63c194b48d7fac40c642fe8185638f`

Source-spec digest: `ac02dca181feea32b1e9547e381c94c9399f3a34c4bc0ac3df2ed9095b0c813c`

Compiled protocol digest: `d3d677cff22f9a4587ed204cb0c182a71ac85db6009e2db2200fbc77306e3117`

## Independent checks

The following commands were run from the repository root with module execution
so the repository's `experience_learning/types.py` cannot shadow the standard
library `types` module:

```text
python -B -m experiments.experience_learning.compile_v5_protocol experiments/experience_learning/v5_protocol_spec.json --check experiments/experience_learning/v5_compiled_protocol.json
python -B -m experiments.experience_learning.validate_v5_protocol_compilation experiments/experience_learning/v5_protocol_spec.json experiments/experience_learning/v5_compiled_protocol.json --repo-root .
python -m pytest -q experiments/experience_learning/tests/test_v5_protocol_compiler.py
```

Observed results were compiler `valid`, independent-validator `valid` with
`assessment_materialization_state=absent`, and `5 passed`. Independent
canonicalization recomputed every section digest and the compiled digest. The
independent SplitMix64 vector matched the compiled artifact exactly, including
the action hash for `(fit, sparse_predictable_v5, 4000, 0)`.

The direct script forms
`python -B experiments/experience_learning/compile_v5_protocol.py ...` and
the corresponding direct validator form fail before execution because the
script directory contains `types.py`, which shadows Python's standard-library
`types` module. The packet's module commands work, but the compiler's ordinary
script entrypoint is not hermetic.

## Blocking findings

1. **V5-ID-000 — frozen input hash drift.** The review packet declares
   `AGENTS.md` as `7068251ae9ecfea8bebc99499a1842447dcc87a200f9ab2548d00d7d2d93f4ff`,
   but the current repository bytes hash to
   `4d4c790169f0521e9d419687da38fd001505fbde831e7f9155d237d30b1496f5`.
   No affirmative review can bind both identities; the packet must be
   regenerated and refrozen before a successor review.

2. **V5-HASH-001 — treatment probability is not instantiated.** The action
   hash defines a generic `p_num/p_den` threshold but does not declare the
   actual numerator and denominator, nor bind them into the action frame. The
   fit assignment and matched-random assignment therefore have multiple valid
   interpretations.

3. **V5-CTRL-002 — controller transitions are not executable.** The rows list
   index `4` before index `3`, while index `3` is described as crediting the
   previous action before model action. There is no exact `q_skip`/`q_apply`
   formula, no reward formula, no current-action `q` definition, and no rule
   for resetting or carrying `theta` and `dual_mu` across stream/seed
   trajectories. `pending_reward` is read by credit but is not populated on
   ordinary rows. These choices change the complete-policy trajectory.

4. **V5-GEN-003 — generator draw and value semantics remain ambiguous.** The
   `noisy_mnist_v5` prose lists target noise before distractor draws while its
   typed draw roster lists distractors before target noise. Event-camera
   duplicate-index aggregation and forced feature-zero interaction are not
   specified. The long-horizon sign-reversal equation and full piecewise-drift
   coefficient vectors are incomplete. `source_id_layout` is a decimal display
   string rather than an exact framed byte encoding. These gaps permit distinct
   streams with the same declared roster.

5. **V5-ALG-004 — operation ASTs and byte layouts are incomplete and
   inconsistent.** Sparse/event operation formulas, controller recurrence ASTs,
   reward/clip/comparison/counter formulas, exact offsets, and binary64 rules
   are absent. The declared `fit_controller_state` and `pending_row` layouts
   omit most of the twenty state fields. The `counter_row` layout has 11
   uint64 fields but the counter schema has 14 fields including strings and
   booleans. The dual formula omits the subtraction present in its recurrence.
   Resource gates cannot be independently recomputed.

6. **V5-ABL-005 — ablation participation contradicts its tests.** The control
   Holm group includes `predictable_noise/oracle_feature_sgd`, but that arm is
   declared assessment=`no`. `reward_shift_37` has no exact shifted-reward
   predicate or publication eligibility rule. Matched-random probability
   sealing is not numerically defined. The execution rows do not fix controller
   state reset and arm ordering at trajectory boundaries.

7. **V5-STAT-006 — statistical gate is not fully defined.** The paired test is
   called a t statistic but uses the normal `erfc` tail rather than a declared
   Student-t distribution. The mechanism Holm family omits `no_dual` and
   `reward_shift_37`, and the control family contains an arm with no assessment
   result. Per-family sample units, missing-value handling, confidence
   intervals, effect thresholds, and exact resource/adaptation predicates are
   not fixed.

8. **V5-MET-007 — adaptation aggregation has unresolved boundary cases.** The
   metric does not say to exclude the initial `0` boundary from shift scans,
   does not define zero/empty/nonfinite baseline handling, and does not define
   how stationary `null` values enter stream and family aggregation. The
   declared arm-specific baseline is not represented in a result schema.

9. **V5-SCHEMA-008 — locks and receipts do not bind the required state.** The
   fit lock has no trace, `q_old`, or pending-state snapshot and the tune lock
   has no complete controller snapshot. Required digest bindings omit counter,
   control, adaptation-schema, and assessment-absence digests. The counter
   schema omits active synaptic operations, active writes, logical state bytes,
   wall-clock policy, and update counts. The control schema has no exact
   expected predicate field. The assessment-absence schema lacks the declared
   `materialized_paths` and `result_digest` fields. The validator receipt does
   not bind review or section/schema digests. These omissions permit an
   implementation to pass validation while changing the claimed workload.

10. **V5-ENTRY-009 — compiler entrypoint is not hermetic.** Running the source
   files as documented tools fails under the repository's normal path import
   rules due to `experience_learning/types.py` shadowing the standard library.
   The review packet avoids this only by requiring `-m`; the executable
   compiler identity should have one working, documented entrypoint.

## Sound boundaries

The complete-policy estimand remains a valid high-level scientific object. The
source has disjoint fit/tune/assessment seed ranges, an explicit assessment
absence state, seven named compiled sections, and explicit closure of replay,
plasticity guard, V1-V4 artifacts, and Astral. These strengths do not cure the
execution ambiguities.

## Required successor action

Close V5 as `ProtocolReviewRejectedNoExecution`. Do not implement or execute a
V5 learner, fit, tune, assessment, real campaign, or energy capture. A future
V5 successor requires new frozen source/compiler/compiled bytes, exact action
probabilities and controller algebra, complete generator and operation
contracts, noncontradictory ablation/statistical tables, boundary-complete
metrics, and canonical digest-bound locks and receipts, followed by another
independent review. Do not retune the closed plasticity guard or connect Astral.
