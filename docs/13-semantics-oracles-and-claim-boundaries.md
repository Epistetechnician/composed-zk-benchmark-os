# Semantics, Oracles, And Claim Boundaries

This is the semantic spine of the project. Semantics come before adapters because adapters can only produce meaningful evidence if the expected verdict is defined before backend execution.

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

## Formal-Ish Definitions

Machine: a named semantic system with states, fields, transitions, invariants, witness policy, oracle, and targets.

State: an assignment of field values at a step.

State validity: all field type, visibility, and local constraints hold.

Transition: a relation from one state to another under a guard and action.

Transition relation: the set of state pairs accepted by declared transitions.

Trace: ordered state and transition sequence.

Trace validity: initial state valid, every step follows transition relation, all invariants hold, witness policy is satisfied, and observations required by the oracle are present.

Witness: private data required to justify a trace or transition.

Observation: public or recorded value used by the oracle or scoring layer.

Invariant: property required over machine, state, transition, loop, or trace scope.

Invariant satisfaction: invariant expression evaluates true over its scope.

Expected result: semantic verdict declared before backend replay.

## accepted_trace And rejected_trace

`accepted_trace` describes trace patterns the Oracle should accept.

`rejected_trace` describes trace patterns the Oracle should reject.

The Oracle can also return inconclusive when observations are missing or a capability gap prevents classification.

## Semantic Equivalence Class

A semantic equivalence class groups specs or mutations that should preserve the same externally observable behavior. Semantic no-op drift is rejected when a surface no-op changes equivalence class.

## Oracle Model

The Oracle evaluates:

- trace validity,
- transition relation,
- state validity,
- invariant satisfaction,
- accepted_trace,
- rejected_trace,
- expected_result,
- witness_policy,
- public_inputs,
- private_witnesses,
- observation model,
- semantic equivalence class.

## Witness Policy

Witness policy declares public inputs, private witnesses, aliasing rules, and visibility boundaries. Public/private boundary mismatch and witness aliasing are first-class semantic failures.

## Mutation Verdicts

- valid mutation: preserves semantics; usually expected_accept.
- near-valid mutation: close to valid but violates a scoped boundary; often expected_reject or expected_inconclusive.
- malicious mutation: constructed to expose unsound acceptance; expected_unsound_if_accepted.
- invalid mutation: malformed or semantically impossible; expected_reject or expected_backend_error.

## Backend Outcomes

Implemented v0 `BackendOutcome` values:

- `Accepted`
- `Rejected`
- `Error`
- `Timeout`
- `CapabilityGap`
- `MalformedArtifact`
- `Inconclusive`

Unsupported features should normalize to `CapabilityGap` or `Inconclusive` in this phase. Unsound acceptance candidates and false rejection candidates are classifications, not raw backend outcomes.

## Local JSON Replay Adapter

Phase F implements `LocalJsonAdapter` as a local-only adapter. It consumes `ReplayManifest` values, evaluates selected traces with the local oracle, and emits `ReplayResult` plus Level1LocalReplay `EvidenceRecord` values.

The local adapter mapping is deliberately narrow:

- local oracle accepted maps to `BackendOutcome::Accepted` only inside local replay,
- local oracle rejected maps to `BackendOutcome::Rejected` only inside local replay,
- local capability gaps remain `BackendOutcome::CapabilityGap`,
- local inconclusive outcomes remain `BackendOutcome::Inconclusive`.

Local replay accepted is not proof-system accepted. Local replay rejected is not proof-system rejected. The local JSON adapter is not a ZK backend adapter.

## zk-Harness Dry-Run Plans

Phase G implements zk-Harness adapter preparation only. A zk-Harness dry-run plan maps a local benchmark pack into candidate labels, planned future steps, inert planned command data, metric mapping schema, and evidence policy.

zk-Harness dry-run plans are not benchmark results. External execution is disabled by default. Mapping a local pack to a dry-run plan does not create external evidence.

Claim boundaries:

- zk-Harness dry-run manifests, mappings, validations, and plans are `Level0DesignNote`.
- local pack evidence referenced by a dry-run plan remains `Level1LocalReplay`.
- local replay results are local-only source references and are not converted into zk-Harness results.
- external replay, if implemented in a later phase, is not formal evidence.
- a benchmark pass remains not proof.

## External-Runner Boundary And Manual Handoff

Phase H implements an external-runner boundary only. External execution is disabled by default. A manual handoff bundle is a `Level0DesignNote` artifact that preserves a dry-run plan id, source benchmark pack id, source digests, artifact capture contract, provenance contract, result import validation schema, quarantine behavior, and future execution prerequisites.

Manual handoff bundles are not benchmark results. They do not create zk-Harness results, proof-system acceptance, external replay evidence, performance evidence, or formal evidence.

External result candidates start quarantined or pending review. A validated import schema is not the same as official benchmark evidence. Result import validation can reject malformed or overclaiming candidates, but it does not make a candidate official benchmark evidence. External replay, if later implemented, is still not formal evidence.

Phase H claim boundaries:

- external-runner policies are `Level0DesignNote`,
- manual handoff bundles are `Level0DesignNote`,
- artifact capture contracts are `Level0DesignNote`,
- provenance contracts are `Level0DesignNote`,
- result import schemas are `Level0DesignNote`,
- quarantine manifests are `Level0DesignNote`,
- referenced local packs remain `Level1LocalReplay` at most,
- local replay remains not official benchmark evidence,
- benchmark pass remains not proof.

## Synthetic Result Import And Proposal Review

Phase I implements a local synthetic result import prototype only. It parses JSON `ExternalResultCandidate` values, validates artifact digests against caller-provided local bytes, validates provenance fields, validates metric candidate shape, detects official/formal/soundness overclaims, quarantines invalid candidates, and normalizes valid candidates into pending-review drafts.

Synthetic result candidates are not benchmark results. Evidence append proposals are not accepted evidence. Proposal ledgers are review ledgers only and do not mutate the accepted Evidence Ledger.

Phase I claim boundaries:

- synthetic import bundles are `Level0DesignNote`,
- normalized result drafts are `Level0DesignNote`,
- synthetic quarantine manifests are `Level0DesignNote`,
- evidence append proposals are `Level0DesignNote`,
- proposal ledgers are `Level0DesignNote`,
- referenced local replay artifacts remain `Level1LocalReplay` at most,
- metric candidates remain candidate-only metadata,
- no Phase I artifact creates Level2+ evidence.

## Result Classification Matrix

| Expected Verdict | Backend Outcome | Classification |
|---|---|---|
| expected_accept | accepted | expected accept and backend accepted |
| expected_accept | rejected | false rejection candidate (`ExpectedAcceptRejected`) |
| expected_accept | backend_error | unrelated backend failure or adapter issue |
| expected_accept | timeout | inconclusive result unless timeout policy says otherwise |
| expected_reject | rejected | expected reject and backend rejected |
| expected_reject | accepted | unsound acceptance candidate (`ExpectedRejectAcceptedUnsoundCandidate`) |
| expected_reject | backend_error | expected reject and backend errored, triage required |
| expected_reject | capability_gap | backend capability gap |
| expected_backend_error | backend_error | expected backend error |
| expected_backend_error | accepted | possible adapter or oracle error |
| expected_inconclusive | inconclusive | inconclusive result |
| expected_capability_gap | capability_gap | capability gap |
| expected_unsound_if_accepted | accepted | unsound acceptance candidate |
| expected_unsound_if_accepted | rejected | negative test caught |
| any | malformed_artifact | malformed artifact |
| any | timeout | timeout; not automatically soundness failure |

## Evidence Types

Replay-only evidence: local run evidence with limited claim boundary.

Benchmark evidence: reproducible benchmark artifact with replay metadata.

Formal evidence: scoped formal property statement or proof artifact.

Machine-checked proof evidence: proof checked by formal tooling for a named property.

## Claim Boundary Levels

- Level 0: design note only.
- Level 1: local replay evidence.
- Level 2: reproducible benchmark artifact.
- Level 3: cross-backend replay evidence.
- Level 4: formal property statement.
- Level 5: machine-checked proof for a scoped property.
- Level 6: independently reproduced evidence.

The first documentation scaffold is Level 0 only. The current Rust foundation is Level 1 local implementation only: local parser, lowering, oracle tests, and classification primitives.

Phase D/E generated Benchmark Families and Mutation Variants remain Level1LocalReplay at most. Phase F local replay manifests, replay results, evidence ledgers, and benchmark packs also remain Level1LocalReplay at most. Generated benchmark families are not official benchmark evidence. Local oracle acceptance is semantic-local only and is not proof-system acceptance.

Evidence ledger digest validation is a local integrity check, not independent reproduction, not tamper-proof evidence, and not a Merkle proof. A benchmark pack skeleton is a local artifact bundle only; it does not by itself create Level2 reproducible benchmark evidence.

Phase G zk-Harness dry-run plans remain Level0DesignNote. Phase H manual handoff bundles, external-runner policies, artifact capture contracts, provenance contracts, result import schemas, and quarantine manifests remain Level0DesignNote. Phase I synthetic import bundles, normalized drafts, evidence append proposals, and proposal ledgers remain Level0DesignNote. Referenced local packs remain Level1LocalReplay. No Phase G, Phase H, or Phase I artifact creates Level2+ evidence.

If a mutation removes or corrupts a guard and a previously rejected trace becomes locally accepted, that result is an unsound acceptance candidate under the classification matrix. It is not proof of an exploit, not proof of backend unsoundness, and not formal evidence.

## Strict Warnings

- A benchmark pass is not proof.
- A local replay is not official benchmark evidence.
- A formal proof about one layer is not a formal proof about the full system.
- A recursion proof is not semantic proof.
- A backend rejection is not automatically semantic correctness.
- A timeout is not automatically a soundness failure.
- A successful proof is not automatically evidence that the source spec was meaningful.
- zk-Harness dry-run plans are not benchmark results.
- Manual handoff bundles are not benchmark results.
- External execution is disabled by default.
- Local oracle acceptance is semantic-local only.
- Unsound acceptance candidate is not a proven exploit.
- Result import candidates are quarantined or pending review until validated.
- Synthetic result candidates are not benchmark results.
- Evidence append proposals are not accepted evidence.
- No first-pass document may claim Level 2+ evidence unless artifacts exist in the future.
