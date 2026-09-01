# Oak Lab H100 replication V4 independent review

State slice: `oaklab-experience-learning-h100-replication-v4`.

Review decision: `REJECT`.

The canonical JSON receipt is
`docs/research/experience-learning/55-oaklab-h100-replication-v4-independent-review.json`.
This Markdown record does not alter any packet-bound V4 byte.

## Scope and verification

The review read only the packet-bound protocol, packet, V4 source specification,
compiler, validator, hermetic test, compiled artifact, and `AGENTS.md`. No
model, dataset, provider, energy, H100, learner, or effects execution occurred.

The three required commands were run exactly:

1. `python -B -m experiments.experience_learning.compile_oaklab_h100_v4_protocol --repo-root . --output experiments/experience_learning/oaklab_h100_v4_compiled_protocol.json`
2. `python -B -m experiments.experience_learning.validate_oaklab_h100_v4_protocol`
3. `python -B -m pytest experiments/experience_learning/tests/test_oaklab_h100_v4_protocol.py -q`

The compiler reproduced compiled self-digest
`762fb78fb8606cc5a0637bc790292cb5ace0550d27f80932e0d51fdd848c92af`.
The validator returned `valid: true` and
`assessment_materialization_state: absent`. The test command returned
`8 passed`; pytest emitted only temporary-directory cleanup warnings.

Independent recomputation produced matching file, source, compiled, section,
transcript, freeze, and self-digests. The compiled artifact is canonical JSON;
its byte SHA-256 is
`1effd508e856bb3f84d0ebbce2bd6799ddb1c7a426010bb4466cbcf2d59d9d5b`.
The current packet byte SHA-256 is
`cc927fe7bd6ad67359d7e4ce3457db5e5a3178b8e65c2b98cd1e50a2a2d36c28`.
All other reviewed file hashes match the packet's bound values.

## Findings

1. `seven_sections_estimand_prng_controller`: `true`. The source/compiler
   define exactly seven sections, the paired endpoint and controls, sealed
   SHA-256 transcript, unconditional draw policy, indexed transitions,
   simultaneous recurrence, terminal no-action rule, and complete pending
   fields. The validator recomputes section and transcript digests.

2. `canonical_digests_and_manifest_core`: `true`. Runtime JSON is parsed only
   through canonical-byte validation; self-digests exclude only their digest
   field, and the campaign core digest uses the fixed non-circular core key
   list. Campaign and compiled bindings are recomputed.

3. `provider_receipts_ed25519_cross_binding`: `false`. Ed25519 signatures,
   canonical bodies, allocation identity, UTC interval, cost finiteness, and
   cost ceiling are checked. However, cost and stop schemas omit `node_id`, so
   the declared same-node cross-binding cannot be enforced. The allocation's
   `hard_usd_ceiling` is also never compared with the campaign ceiling. A
   provider allocation can therefore carry a mismatched node/ceiling while
   passing the available provider checks (`validate...py:346-360`).

4. `lock_schemas_prediction_lock_ordering`: `true`. Fit, tune, and independent
   lock receipts require canonical closed schemas, exact digest bindings,
   locked decisions, and self-digests; result-root validation requires the
   fit-to-tune-to-independent-receipt chain before accepting the aggregate.

5. `closed_world_result_root_content_bindings`: `true`. The validator rejects
   symlinks, unlisted paths, missing paths, and extra paths; validates every
   allowlisted JSON/CSV artifact; and checks compiled, fit, tune, lock-receipt,
   provider, energy, aggregate, independent-validation, and root-digest
   bindings (`validate...py:492-524`).

6. `joule_resource_quality_adaptation_statistical_gates`: `false`. Raw-trace
   monotonicity, finite/nonnegative watts, exact trapezoidal integration,
   learned-event denominator, energy self-digest, and 5% resource derivation
   are enforced. The aggregate validator does not derive the declared
   per-family quality/adaptation gates: it accepts one aggregate delta and
   supplied booleans, with no per-family no-worse/strict-improvement or
   pure-noise-null evidence. Its independent `checks` map likewise accepts any
   nonempty all-true key set (`validate...py:443-483`).

7. `execution_authorization_current_digest_and_lane`: `false`. Review and
   synthetic artifacts bind to current compiled/source bytes, and preflight
   requires zero spend, offline state, no model load, and bounded execution.
   The provider plan's `manifest_sha256` is only checked as a 64-character
   digest and is never bound to the current source, compiled artifact, or
   campaign core (`validate...py:527-540`). The authorization predicate can
   therefore accept a plan unrelated to the current campaign.

8. `historical_lane_isolation_and_assessment_absence`: `true`. The frozen
   source and compiled boundaries keep Phase 836, Oak Lab V6, and the
   plasticity guard historical/closed and Astral isolated; assessment
   materialization is explicitly absent. `AGENTS.md` independently records
   the Phase 836 and V6 terminal closures and Astral/plasticity isolation.

## Closure

Findings 3, 6, and 7 are false. Under the packet rule, this is `REJECT` and
authorizes no implementation, custody, provider access, spend, H100 job,
energy capture, assessment, or publication. V4 requires a fresh corrected
freeze and independent review before any implementation authorization.

`effects_run`: `false`.
