# Oak Lab H100 replication V4 independent review

State slice: `oaklab-experience-learning-h100-replication-v4`.

Review decision: `REJECT`.

Reviewer: `codex-oaklab-h100-v4-independent-reviewer`.

Reviewed at: `2026-08-31T20:43:59Z`.

This was a static compiler and validator review only. No learner, model, data,
provider, H100, paid job, energy capture, or assessment effects ran. The
three packet commands completed as required: the compiler emitted the bound
compiled digest, the validator returned `valid: true`, and pytest returned
`8 passed in 1.55s`.

## Hash verification

The packet hash is:

`cc927fe7bd6ad67359d7e4ce3457db5e5a3178b8e65c2b98cd1e50a2a2d36c28`

All seven packet-listed file hashes matched exactly:

| File | SHA-256 |
| --- | --- |
| `docs/research/experience-learning/53-oaklab-h100-replication-v4-protocol.md` | `b8adf99f1f870a1a4cf17bdadc6837036e4691bb2ba8cd0d1d1ca0851c556e4a` |
| `experiments/experience_learning/oaklab_h100_v4_protocol.json` | `6b86c2e28910a58b58ee2c7df57c7227cd6bdef4ebc814f381d8e1e833f715c2` |
| `experiments/experience_learning/compile_oaklab_h100_v4_protocol.py` | `83645571b344c4e7c5d475c8d0a578b13947a8a4308579679c5d787ac5da7778` |
| `experiments/experience_learning/validate_oaklab_h100_v4_protocol.py` | `424f2ac5357e5b12440a9011ddc68c1878c8fcc435c449885d8a4705beb41fd5` |
| `experiments/experience_learning/tests/test_oaklab_h100_v4_protocol.py` | `c5237f196bfa9e96c12fa7d123bea77c1baba7a5d47e5006c94c320a7c6aeb15` |
| `experiments/experience_learning/oaklab_h100_v4_compiled_protocol.json` | `1effd508e856bb3f84d0ebbce2bd6799ddb1c7a426010bb4466cbcf2d59d9d5b` |
| `AGENTS.md` | `e3a8c73ec125c4f66d8bb2cc8294ed0bf4bf57278e1f3c7e5ae6dc0c55162bf4` |

The independently recomputed compiled self-digest matched:

`762fb78fb8606cc5a0637bc790292cb5ace0550d27f80932e0d51fdd848c92af`

The seven section digests matched the compiled artifact:

| Section | Digest |
| --- | --- |
| `hash_prng_transcript` | `dd449c42af9ef7e2bae701ca5ff2e948706d4de835a9bef5c493b9e3ca42cd75` |
| `controller_transition_table` | `8ee7e99811e83f959d8e424dc6d5ad81f2829befeabd80de8352bcfc1c47177b` |
| `generator_roster` | `27eb833c3c0542890313944ff4e3eac1960613daad43eb2920976f28d061f6b9` |
| `operation_and_byte_algebra` | `1b2f077104516afda9c62d840a94b758ccc1670e2091b365ad912c3351730ad0` |
| `ablation_execution_multiplicity` | `ea75dfc258dfb8595c5f9c4a395dd24bf24d0070a717f9f03a7d3c45f2a3180a` |
| `adaptation_metrics` | `43239dd75ed72e33d447eb8a2cbd42b83e0d7443cf0898c1a1fe3dd5a5d54057` |
| `lock_counter_control_schemas` | `2b3c9febedb1f085665dd8de06a5d0fc9ef7759e2f55788cd44d270db8dbb171` |

The transcript vector also matched. Its root digest is
`3273eaa0865ab64ff0e4f9fefa3278633217997f7692c1d772802813c9e1dfaf`, and its
action hash is
`1d2003f3b43edbbd5c240c9f8acd53dd7eec6756c8d37d96c7be9c9dc273093c`.

## Findings

1. **REJECT — exact protocol semantics are not enforced.** The validator
   checks only selected estimand values and text fragments, contiguous row
   indices/event names, state-name count, draw ordinals, and formula-AST keys
   (`validate_oaklab_h100_v4_protocol.py:136-188`). It does not require exact
   nested estimand, controller reads/writes/recurrence, state types, generator
   equations, or unconditional draw labels/repeats. A changed nested contract
   can therefore compile and validate.

2. **PASS — canonical bytes, self-digests, section digests, freeze digests,
   and the non-circular campaign core are checked.** Canonical JSON and the
   compiled self-digest are checked at lines 210-235; campaign-core and
   campaign self-digests are checked at lines 239-251.

3. **REJECT — provider validation is incomplete.** The pure Ed25519 path and
   receipt self-digests are implemented (`validate_oaklab_h100_v4_protocol.py:318-342`),
   and allocation ID/public-key/manifest bindings are checked at lines
   346-352. However, allocation hard ceiling is not cross-bound to the
   manifest or cost, `currency` is not required to be `USD`, cost/stop have no
   node identity to cross-bind, and the UTC check only requires `stop >= start`
   (`:353-360`) with no bounded interval.

4. **REJECT — fit/tune/receipt schemas do not enforce prediction-lock ordering
   or review binding.** Exact key sets and local lock digests are checked at
   lines 364-395, but the fit review digest is an arbitrary hash, there is no
   binding to an independent `ACCEPT`, and no field or check proves that the
   prediction lock preceded assessment effects.

5. **PASS — result-root closed-world and file binding checks are present.**
   The validator rejects symlinks, unlisted files/directories, and mismatched
   file sets, then validates the allowlisted receipt schemas and manifest
   bindings (`validate_oaklab_h100_v4_protocol.py:487-523`).

6. **REJECT — resource and scientific gates are not independently derived.**
   Raw trace monotonicity, finite nonnegative watts, trapezoidal integration,
   positive learned-event count, and the local 5% resource predicate are
   implemented (`validate_oaklab_h100_v4_protocol.py:398-466`). But the event
   denominator is not bound to learned-event/counter evidence, resource values
   are supplied rather than derived from counters, and quality, adaptation,
   custody, energy, and statistical publication gates are accepted as
   caller-provided booleans (`:467-472`) without per-family Holm, adaptation,
   null, or endpoint derivation.

7. **REJECT — execution authorization does not revalidate current source and
   compiled integrity.** The predicate checks an ACCEPT-shaped review against
   the current compiled file and a synthetic source digest, plus preflight and
   one bounded job (`validate_oaklab_h100_v4_protocol.py:527-540`), but it does
   not call `validate_compiled`, bind the review to the packet/self-digest, or
   prove the current compiled artifact is source-bound before authorization.

8. **REJECT — isolation checking omits the plasticity-guard boundary.** Source
   validation checks Phase 836, Oak Lab V6, and Astral values but not the
   `plasticity_guard` historical-only value (`validate_oaklab_h100_v4_protocol.py:190-207`).
   Assessment absence is represented and checked, but the combined isolation
   finding therefore fails.

9. **PASS — tests include a positive valid-root case and negative tamper
   cases.** The valid closed-world root is exercised at
   `test_oaklab_h100_v4_protocol.py:198-201`; signature, joule, extra-path,
   and missing-ACCEPT cases are exercised at lines 173-182, 185-195, 202-205,
   and 208-218.

Because findings 1, 3, 4, 6, 7, and 8 are false, V4 is rejected before
implementation. No provider, node, model, dataset, spend, energy, or
assessment evidence was invented. The canonical receipt is
`55-oaklab-h100-replication-v4-independent-review.json` with self-digest
`295aa77a9618c800386ddf6ade42b15a99f1f35e935177dbefae0ea1ed471c39`.
