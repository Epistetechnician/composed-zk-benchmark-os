# Oak Lab V6 independent protocol review

State slice: `oaklab-experience-learning-constrained-update-policy-v6`

Reviewer: `independent-agent-review`

Decision: `REJECT`

Implementation authorization: `false`

Fit, tune, assessment, real-execution, provider, H100, and energy
authorization: `false`

Claim ceiling: `ProtocolReviewRejectedNoExecution`

Astral: `isolated_not_run`

The exact packet identities were recomputed before the substantive review.
All declared input hashes, the freeze-manifest hash, the seven canonical
section digests, the compiled digest, and the independently recomputed
SplitMix64/action vector match the packet and compiled artifact. The module
compiler, independent validator, five hermetic compiler tests, and
`pnpm run lint:fast` passed. The protocol is nevertheless rejected because
the frozen contract still contains state-transition, numeric/statistical,
generator, adaptation, counter, and lock-schema ambiguities that permit
distinct implementations.

## Exact review identity

| Input | Recomputed SHA-256 |
| --- | --- |
| `AGENTS.md` | `f80ac0cde545dc27ce4cbb88ce8ab1f4bed02724b2eb7b6618f4ccefd976cdc3` |
| `experiments/experience_learning/v6_protocol_spec.json` | `999793806303d3fccaa8ff157c3fcc14cb17b89d70d7e1d466ee12f8e600f788` |
| `experiments/experience_learning/v6_compiled_protocol.json` | `0fe519e537bd00d70619c913d2251541a1eae5df794b14fde189da7d01e14932` |
| `experiments/experience_learning/compile_v6_protocol.py` | `1fc84644db9e6a283afcd5c8a65a77ac623a9d82dd208c21e031380f7831b17e` |
| `experiments/experience_learning/validate_v6_protocol_compilation.py` | `e49fafcc828e7e80a55ccc8b6013ea4979415e264111ee82604f7a2f86af04c9` |
| `experiments/experience_learning/tests/test_v6_protocol_compiler.py` | `fba5f0f94380913865b5b8aab4c567521f0c8ee7d38352c7dfcf1ea2b8a86921` |
| `docs/research/experience-learning/39-oaklab-v6-protocol-compiler.md` | `74bf07c4a0ec6959442f28fa5cbbff6bfbb60957a9100077066a69be381980a9` |
| `experiments/experience_learning/v6_freeze_manifest.json` | `ac6ce73891c6f8c94c4029c2b83053ce8058633ce630a3482b737e5834cd4677` |

Source-spec digest: `999793806303d3fccaa8ff157c3fcc14cb17b89d70d7e1d466ee12f8e600f788`

Compiled protocol digest: `abf2d178520207fb157f5d5c32ec00d618019f96ccbe1107c6e8ad26970515f4`

Freeze-manifest digest: `ac6ce73891c6f8c94c4029c2b83053ce8058633ce630a3482b737e5834cd4677`

## Independent checks

Commands run from the repository root without writing any bound input:

```text
python -m experiments.experience_learning.compile_v6_protocol experiments/experience_learning/v6_protocol_spec.json
python -m experiments.experience_learning.validate_v6_protocol_compilation experiments/experience_learning/v6_protocol_spec.json experiments/experience_learning/v6_compiled_protocol.json
python -m pytest -q experiments/experience_learning/tests/test_v6_protocol_compiler.py
pnpm run lint:fast
```

Observed results:

- compiler: `compiled`, source digest and compiled digest as above;
- independent validator: `valid`, decision `pending_independent_review`, assessment state `absent`;
- focused tests: `5 passed`;
- `pnpm run lint:fast`: passed (`cargo fmt --all -- --check`, Python source verification, and `git diff --check`).

Section digests recomputed with sorted-key canonical JSON, compact separators,
ASCII escaping, and `allow_nan=false`:

| Section | SHA-256 |
| --- | --- |
| `hash_prng_transcript` | `c350e7f7e50470eb2d8991bc47ba355926e18312a2ede5a42d9ba04597c5f057` |
| `controller_transition_table` | `f9ca7ddb3183c4b883769a2db5d3765c758e2bed46f973a8afe50760aff4f001` |
| `generator_roster` | `a34839a7aa54f744b2240bf36dc7ac90470b4a480e09794a643c7b147dc985b6` |
| `operation_and_byte_algebra` | `265777db11a0336ca1df55790983828b2641c957bcd78102dc77b401ea0f2039` |
| `ablation_execution_multiplicity` | `7d3c29891b35a3961a100016936e6e6c10bc94631099b9d8572fc13ea294eef6` |
| `adaptation_metrics` | `b71baf860faf398b8012ec2c74847caa34dc3fe7ea8b85b3e15d5af5c5e86cee` |
| `lock_counter_control_schemas` | `21b1ee264789ca4d182a93500aab9e3bd264f6e6d25df078d2a662d7f7bf4652` |

The independently recomputed transcript vector for `(fit,
 sparse_signal_v6,4000,0)` is:

```json
{
  "action_hash_sha256_hex": "d16a0722a941ff26161dc34ceb08dbe8bf704aa22d1910f7433509f64b184cb1",
  "first_normal12_after_first_draw": -0.31937007329085887,
  "first_uniform53": 0.7999582424309138,
  "initial_state_uint64_le": 4995785472395330620,
  "root_sha256_hex": "3c442e186b985445894079247b32b1644ef619d1a18c3df3142d998e5737b042"
}
```

## Blocking findings

1. **V6-CTRL-001 — recurrence reads are not declared.** In
   `controller_transition_table.rows[index=2]`, the recurrence uses the prior
   `eligibility` and `theta`, but that row's `reads` list omits both. The
   terminal row (`index=6`) says it credits the final pending action but lists
   only `pending_valid`, `pending_local_row`, and `terminal_loss`; it omits the
   pending reward, eligibility, theta, q-old, previous features, previous q,
   previous cost, and dual state required by the declared recurrence. This
   violates the closed-world state rule and makes simultaneous updates
   non-executable. A successor must bind every RHS input in each indexed row,
   including terminal credit, under a new freeze.

2. **V6-STAT-002 — the one-sided p-value tail has the wrong direction.** The
   protocol defines `X=-D` for candidate-better tests, so a beneficial result
   has positive mean `X` and requires the upper-tail probability
   `0.5*erfc(z/sqrt(2))`. It instead declares
   `p_one=0.5*erfc(-z/sqrt(2))`, the lower tail. Favorable positive effects
   therefore receive large p-values while adverse effects receive small ones.
   This changes the fixed gate and cannot be corrected during execution.

3. **V6-ALG-003 — counter energy encoding is contradictory.** The logical
   `counter_row` byte layout requires an eight-byte `float64 energy_joules`
   field in a fixed 143-byte row, while the counter schema types it as
   `float64_or_absent` and the resource invariant says energy is absent until a
   privileged receipt. Numeric rules reject NaN, and no sentinel, optional
   field framing, or absent-value encoding is declared. Counter bytes and
   assessment of energy absence are therefore not unique.

4. **V6-ALG-004 — counter enum and resource fields are not byte-exact.** The
   `phase`, `cohort`, and `arm_id` counter fields are `uint8` but no mapping
   from their named values to integers is frozen. The `decision` byte in
   `lock_receipt` has the same omission. `logical_state_bytes`,
   `replay_bytes`, and `latency_ns` have no exact per-row formulas or capture
   boundaries. These omissions permit different counter receipts and resource
   claims under the same protocol digest.

5. **V6-GEN-005 — generator values contain unresolved choices.** The
   `event_sensor_v6` equation forces `x0` to `(-1,+1)` by row parity without
   declaring which sign applies to row zero. `delayed_reward_v6` says the sign
   flips at episode 16 but does not declare its initial sign. Both choices
   change ordered stream values while satisfying the frozen prose and roster.

6. **V6-MET-006 — adaptation scan and censoring are not mutually executable.**
   `recovery_scan` does not specify the starting `k`, endpoint domain, or
   increment for the adjacent windows, so the first qualifying pair is not
   unique. Separately, `censoring` deliberately emits `censored=true` lag
   values, while `missing_rules` says every censored trajectory fails the arm.
   The contract does not say whether such an endpoint is reported, excluded,
   or makes every affected arm invalid, so adaptation gates cannot be
   recomputed uniquely.

7. **V6-SCHEMA-007 — binary lock field widths are ambiguous.** The `fit_lock`
   fields `theta_binary64_hex` (`hex[4]`) and `dual_mu_binary64_hex` (`hex`)
   do not declare the byte width, byte order, or per-element encoding of the
   hexadecimal values. The global float rules do not resolve a variable-length
   `hex` type. A fit lock can therefore contain multiple encodings for the
   same binary64 state.

## Sound boundaries

The complete-policy estimand, exact rational `p=1/4` action assignment,
disjoint fit/tune/assessment seed ranges, assessment-absence state, explicit
seven-section closed-world compilation, and plasticity-guard/Astral/provider
boundaries are sound as far as this compiler identity reaches. The compiler
and validator import only standard-library modules; no learner, stream runner,
provider, energy, H100, or Astral execution occurred. These strengths do not
cure the blockers above.

## Required successor action

Close V6 as `ProtocolReviewRejectedNoExecution`. Do not implement or execute
a V6 learner, fit, tune, assessment, real campaign, provider/H100 workload,
or energy capture. Any continuation requires a new protocol identity with a
fresh byte freeze and independent review resolving every blocker above. The
plasticity guard remains historical and Astral remains isolated.
