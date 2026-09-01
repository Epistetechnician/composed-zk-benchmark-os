# Oak Lab constrained update policy V4 independent protocol review

State slice: `oaklab-experience-learning-constrained-update-policy-v4`

Reviewer: `independent-agent-review`

Decision: `rejected`

Implementation authorization: `false`

Fit, tune, and assessment authorization: `false`

Real-execution authorization: `false`

Claim ceiling: `ProtocolReviewRejectedNoExecution`

Astral: `isolated_not_run`

All six dispatched SHA-256 identities matched before substantive review. The
policy-level estimand is defensible, but the frozen bytes do not define one
unambiguous executable experiment. Under the V4 stop rule, this rejection
closes V4 before implementation. It does not authorize source creation, fit,
tune, assessment, real panels, energy capture, publication, guard reuse, or
Astral integration.

## Exact review identity

- `AGENTS.md`:
  `6d059ab6f5b377679bf09f5577d15b0d703a6d1667757a1fc4788c145399e52d`
- `experiments/experience_learning/constrained_update_policy_v4_protocol.json`:
  `60a514f81224927d195bbef9bf8bb533d4636c147fe462eebc4da6b916fbe805`
- `docs/research/experience-learning/31-oaklab-constrained-update-policy-v4-protocol.md`:
  `f8cdeaadf5b9f6cfb54adce00bab9e4d2e721b3a41a0a535ac2ac09237fa908b`
- `docs/research/experience-learning/32-oaklab-constrained-update-policy-v4-review-packet.md`:
  `09d98cf593b94d1fe38c88160b93f97803b2959fc644a8738175efc64f3bff40`
- `docs/research/experience-learning/30-oaklab-selective-credit-v3-terminal-closure.md`:
  `49734d3b99e499cf4f28d62f28db016cbfd10fd3176a009109ade3f939b0fc6f`
- `docs/research/experience-learning/27-oaklab-plasticity-guard-permanent-historical-closure.md`:
  `eeaa5bfda3fb9039c046dbabc16b2b74d2c65be80b78c7862782feb4bc357859`

The six reusable source digests embedded in the machine protocol also matched
their current bytes during review.

## What is sound

The complete-policy estimand correctly includes parameter carryover. Running
the locked policy and fixed SGD from separate zero states on byte-identical
ordered rows supports a paired algorithm comparison without claiming an
isolated causal effect for an individual update. Pre-update loss, a terminal
row with no model update, disjoint `4000..4015`, `5000..5015`, and
`6000..6047` cohorts, fixed source order, and restoration of a zero model for
each trajectory are coherent.

The displayed true-online Sarsa-lambda algebra has the published Dutch-trace
form when its action-selection and transition ordering are fixed. True-online
methods require exact correspondence between the forward view and the online
update; an implementation-dependent ordering is therefore scientifically
material. See [True Online Temporal-Difference Learning](https://www.jmlr.org/papers/v17/15-599.html).

The recomputed two-sided normal-approximation power at worst-case Holm alpha
`0.0125`, `n=48`, and standardized effect `0.5` is
`0.8330770040094296`, exactly matching the protocol. That claim is correctly
limited to the four primary family statistics.

The permanent guard closure, V1-V3 closure, V2-energy exclusion, synthetic-
before-real boundary, separate real-execution review, measured-energy
requirement, claim ceiling, and Astral isolation are explicit and consistent.

## Blocking findings

1. **Hash and PRNG byte contracts are not executable.** The fit-action hash
   does not say whether the domain tag is length-framed, whether
   `protocol_digest` is raw bytes or UTF-8 hexadecimal, or how the hexadecimal
   master seed is encoded. The PRNG initializer does not assign exact values
   to `protocol_id` or `cohort_id`. These choices change every generated row
   or fit action while satisfying the prose.

2. **The online transition order and pending state are incomplete.** At row
   `t>0`, the protocol does not fix whether `action_t` and `q_current` are
   selected before or after the theta update for transition `t-1`, whether
   the current model action executes before or after that controller update,
   or whether the reward uses the pre-update or post-update dual multiplier.
   It also omits the exact pending `x_previous`, `q_previous`, and previous
   action-cost representation needed between batch-one observe calls. These
   alternatives produce different controllers.

3. **Generator and cohort execution still have degrees of freedom.** The
   stream set processed by fit and tune is not fixed: `pure_noise_v4` is a
   required control but absent from the family map. For `event_camera_v4`, the
   index/polarity draw order, duplicate-index polarity rule, and interaction
   between a sampled index zero and the forced alternating feature zero are
   unspecified. Conditional draw order is also not stated globally. The
   source-ID serialization is prose rather than an exact byte contract.

4. **Resource noninferiority cannot be independently recomputed.** Fit state
   is declared as 112 bytes for theta, trace, mu, and q-old, but the recurrence
   also needs pending transition state across observe calls. That state is
   acknowledged by the lock's `empty_trace_and_pending_state` field but is
   absent from the byte total and schema. The fit-update operation rule says
   to charge every arithmetic operation, clip, comparison, counter increment,
   and write without freezing a numeric algebra, including whether a clip is
   one operation or its component comparisons. The 128-byte and total-
   operations gates can therefore fail open.

5. **Tune and ablation execution are contradictory.** `matched_random` is
   defined as assessment-only, while the tune gate requires the candidate to
   beat matched random. Its apply probability is derived only after candidate
   tune, but no subsequent matched-random tune pass is specified. The exact
   noise-floor initialization and causal update, oracle-feature bias/update
   behavior, row-251 behavior, and the fit/tune participation of the pure-
   noise control are also undefined.

6. **Mechanism statistics and multiplicity are incomplete.** The eight
   family-by-ablation tests have no per-seed comparison transform, no declared
   raw paired-test formula, and no total tie order across family and ablation.
   The always-skip comparison is called Holm-adjusted without defining its
   multiplicity family. `reward_shift_37 does not meet the candidate
   publication gate` does not identify which primary, temporal, resource,
   mechanism, or control predicates are recomputed for that arm. Multiple
   incompatible validators could pass these clauses.

7. **Adaptation lag is not unique at multi-shift streams.** The baseline is not
   explicitly candidate-specific versus reference-specific. For the row-84
   shift in `piecewise_drift_v4`, the scan is not stopped before the row-168
   shift, so recovery after a second intervention can be attributed to the
   first. Window end bounds at a subsequent change point and the censoring
   value for an interrupted segment must be fixed before effects.

8. **The lock and validator contract does not close these gaps.** The lock
   names digests and result fields but does not freeze schemas for pending
   controller state, control receipts, ablation statistics, operation-count
   rows, or assessment-absence evidence. Independent recomputation cannot
   select one meaning after implementation without amending the reviewed
   scientific contract.

## Required successor corrections

A successor requires a new protocol identity, not a V4 patch or retune. It
must provide one byte-level hash transcript, exact PRNG identifiers and draw
order, an indexed online state machine, complete pending-state bytes, numeric
operation formulas, an explicit fit/tune stream roster, executable control
algorithms, noncontradictory matched-random ordering, exact mechanism-test
families, segment-bounded adaptation lag, and canonical schemas for every lock
and validator input. That new identity requires a fresh independent review
before implementation.

## Authorization boundary

V4 is `ProtocolReviewRejectedNoExecution`. No V4 implementation or scientific
artifact may be created. The plasticity guard remains a historical comparator
only. The existing energy receipt remains ineligible. Astral remains isolated.

Canonical review digest:
`0e0adfdb7323865b4b2d9d6a393091d5877257253c2dcdf335ea7385e57aee9c`.
