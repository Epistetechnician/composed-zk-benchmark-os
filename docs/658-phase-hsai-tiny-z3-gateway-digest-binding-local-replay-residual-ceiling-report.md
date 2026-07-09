# Phase 658 HSAI Tiny-Z3 Gateway Digest-Binding Local Replay Residual Ceiling Report

State slice: `phase-658-hsai-tiny-z3-gateway-digest-binding-local-replay-comparison`.

Phase 658 replays the Phase 657 concrete gateway proposal digest-binding
obligation and separates stable semantic/output bindings from ephemeral local
source-instance bindings.

The result remains `Level1LocalReplayOrLower`.

## Replay Result

Execution date: 2026-07-09.

```text
baseline_run_id: phase657-local-run-run
replay_run_id: phase658-replay-run
property_id: gateway_proposal_digest_binding_determinism_v1
baseline_verdict: solver_unsat_without_certificate
replay_verdict: solver_unsat_without_certificate
stable_equal_fields: 24
stable_mismatch_fields: 0
source_instance_equal_fields: 0
source_instance_drift_fields: 9
classification: StableSemanticOutputReplayWithSourceInstanceDrift
level_mapping: Level1LocalReplayOrLower
```

Both runs executed local Z3 through the Phase 657 fixed `-in -smt2` lane. No
new process API or process-API exception was added in Phase 658.

## Stable Comparison

These 24 fields matched:

1. `property_id`
2. `fixture_digest`
3. `baseline_proposal_digest`
4. `repeated_proposal_digest`
5. `target_mutation_proposal_digest`
6. `value_mutation_proposal_digest`
7. `obligation_digest`
8. `executable_digest`
9. `argv_digest`
10. `environment_digest`
11. `timeout_policy_digest`
12. `process_output_digest`
13. `stdout_summary_digest`
14. `stderr_summary_digest`
15. `solver_verdict_label`
16. `output_classification_digest`
17. `transcript_redaction_report_digest`
18. `artifact_quarantine_report_digest`
19. `replay_instruction_digest`
20. `level_mapping`
21. `classification`
22. `execution_label`
23. `claim_boundary`
24. `explicit_nonclaims_digest`

Stable comparison digests:

| Binding | Digest |
|---|---|
| baseline stable map | `f1513d60a512fe7fb1a9e1d83c23a43c8a700767c5a931150d1e0cf6886d6916` |
| replay stable map | `f1513d60a512fe7fb1a9e1d83c23a43c8a700767c5a931150d1e0cf6886d6916` |
| stable comparison | `de01addbab7f0a2eda1fc5e3ac45d5c68108443da05f409dff6a78125bf1559a` |

This establishes local replay stability for the named concrete fixture,
obligation, executable, command policy, verdict, bounded output metadata, and
nonclaim boundary.

## Source-Instance Drift

These nine fields differed and were classified as run-instance drift:

1. `execution_digest`
2. `run_id`
3. `executed_at_unix`
4. `execution_input_digest`
5. `preflight_digest`
6. `preflight_input_digest`
7. `source_execution_packet_digest`
8. `source_observation_digest`
9. `nonpromotion_digest`

Run-instance comparison digests:

| Binding | Digest |
|---|---|
| baseline source-instance map | `4876e798ce0e7d59fe65b2ade6e196e245f436f603e6437dd73cd4929d8a625a` |
| replay source-instance map | `d53dc652904bca6d2e9ce2f8a6b7dbdf19a930c08d28a43f35cc60e205afacb3` |
| source-instance comparison | `c2e0723f6ccd4727be71409c2ba348ca0cebcfec265671ce048b1b8bda22e4e0` |

This drift is expected because each run has a distinct run id, timestamp,
execution input, preflight, and temporary source tree. It is not evidence of
semantic/output nondeterminism.

Run-record-only bindings from this comparison:

| Binding | Digest |
|---|---|
| comparison input | `7966a44e33c45c0de2b4baeb59193f9e8c1597ea66da61796ca5835158be0b05` |
| baseline execution | `5af8dc8165b4355b65384c8d78ef75b7420b14858ba42733ff66cdbaae168861` |
| replay execution | `40f342f570b518cd8a2e36607ea5a65d8a031ccc1eb011cb844f14b9f89bf0a3` |
| Phase 657 validation | `bcb03f3d15b6cee7c6f9c95ad6edb77da5434fa618817785e88892b7efee1361` |
| result nonpromotion | `b78d155d3b55d47c81f731f207658a59f312d842e768fb9fcc9b5ce8809bdd40` |

These run-instance values are audit bindings for this observation, not
promises that fresh temporary source trees produce identical full-record
digests.

## Validation

Focused command:

```bash
cargo test -p hsai-agent-admission --lib phase658_hsai_tiny_z3_gateway_digest_binding_local_replay -- --nocapture
```

Observed result: 2 passed, 0 failed. One test performed the paired local Z3
baseline/replay execution and exercised vocabulary drift, source-drift policy,
classification drift, promotion rejection, invalid Phase 657 source rejection,
and tampered comparison rejection. One test checked the 24/9 field vocabulary
partition without execution.

## Exact Meaning

Phase 658 shows that two local executions over the same concrete proposal
fixture, QF_BV obligation, Z3 executable, argv, empty environment, timeout,
and output policy produced the same `unsat` verdict and the same bounded
semantic/output metadata.

It does not prove:

- the production `serde_json` serialization semantics;
- SHA-256 implementation correctness or collision resistance;
- correspondence between arbitrary Rust proposals and the SMT model;
- arbitrary proposal mutation sensitivity;
- gateway semantic correctness;
- whole-system security.

## Residual Ceiling

The evidence ceiling after Phase 658 is:

```text
Level1LocalReplayOrLower replay-stable local execution observation for one
concrete gateway proposal fixture and one tiny-Z3 obligation.
```

No accepted evidence, accepted formal evidence, independent external
reproduction, Level2+ evidence, score-axis evidence, benchmark evidence, proof
artifact, checker transcript, solver certificate, semantic-correctness claim,
production-readiness claim, SOTA claim, breakthrough claim, full-security
claim, external-audit claim, human-review acceptance, or action authority was
created.

## Stop Rule

Do not run another identical local replay merely to increase the run count.
The stable 24-field comparison already passed twice. More identical local
runs would improve operational confidence only marginally and would not raise
the evidence level.

## Next Responsible Boundary

The next highest-leverage slice is a docs-first source-correspondence boundary
for the exact production digest path:

```text
serde_json::to_vec(("hsai-agent-admission:gateway-action-proposal:v1", proposal))
-> SHA-256
-> GatewayActionProposal::digest()
```

That boundary should specify the canonical serialization contract, supported
proposal field subset, extraction/model strategy, correspondence theorem or
certificate shape, failure taxonomy, and nonpromotion rules before selecting
Lean, Rust-to-Lean/Aeneas/Hax, or another proof backend.

It must not treat the current concrete Z3 witness check as a proof of that
production path.

## Defensible Claim

```text
HSAI reproduced one preflight-bound local tiny-Z3 gateway proposal
digest-binding observation with 24/24 stable semantic/output bindings equal,
0 stable mismatches, and nine expected run-instance bindings classified
separately as source drift.
```

It does not justify:

```text
HSAI proved its production proposal digest implementation.
HSAI proved gateway semantics.
HSAI has accepted formal evidence.
HSAI has Level2+ evidence.
HSAI populated score axes.
HSAI is semantically correct.
HSAI is production ready.
HSAI is SOTA.
HSAI is fully secure.
```
