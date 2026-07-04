# Phase 493 HSAI Tiny Z3 Accepted Append Policy Version Metadata Notes

State slice: `Phase 493 HSAI tiny Z3 accepted append policy-version
metadata`.

Phase 493 implements the local metadata gate authorized by
`docs/492-hsai-tiny-z3-accepted-append-policy-version-boundary.md`. The gate
records accepted append policy and transaction version identifiers that a
future accepted append bridge must bind before asking `zkbench-core` to
evaluate an accepted-ledger append transaction.

## Implemented Surface

The implementation is additive in `crates/hsai-agent-admission/src/lib.rs`:

- Phase 493 schema, state-slice, claim-boundary, policy owner, type, version,
  mode, transaction-version, and claim-boundary cap constants;
- `GatewayFormalTinyZ3AcceptedAppendPolicyVersionInput`;
- `GatewayFormalTinyZ3AcceptedAppendPolicyVersion`;
- `GatewayFormalTinyZ3AcceptedAppendPolicyVersionIssue`;
- `GatewayFormalTinyZ3AcceptedAppendPolicyVersionValidation`;
- deterministic digest, id, and label binding helpers;
- required nonclaim helper;
- disallowed evidence-class helper;
- review-decision requirements helper;
- rejection-policy helper;
- `build_gateway_formal_tiny_z3_accepted_append_policy_version`;
- `validate_gateway_formal_tiny_z3_accepted_append_policy_version_input`;
- focused tests for valid metadata construction and promotion rejection.

The metadata binds:

- the Phase 491 owner/mutation-route digest;
- the Phase 491 owner/mutation-route input digest;
- the Phase 491 digest, id, and label binding map digests;
- the Phase 491 explicit nonclaim digest;
- the current accepted append blocker digest;
- accepted append owner `zkbench-core`;
- local transaction route `AcceptedLedgerAppendTransactionRequest`;
- materialized route `MaterializedAcceptedLedgerAppendRequest`;
- policy owner `zkbench-core`;
- policy type `EvidenceAcceptancePolicy`;
- policy version type `EvidenceAcceptancePolicyVersion`;
- HSAI accepted append policy-version marker
  `zkbench-core-accepted-append-local-level1-replay-formal-evidence-blocked:v1`;
- candidate policy id `phase_j_level1_local_only_policy`;
- candidate policy version `phase-j-evidence-acceptance-policy-v0`;
- candidate policy mode `Level1LocalOnly`;
- append transaction version type `AcceptedLedgerAppendTransactionVersion`;
- append transaction version `phase-w-accepted-ledger-append-transaction-v0`;
- claim boundary cap `Level1LocalReplay`;
- disallowed evidence-class labels;
- review-decision requirement labels;
- rejection-policy labels.

## Validation Behavior

The validator rejects:

- schema drift;
- invalid gate, policy, or decision ids;
- missing decision timestamp;
- digest, id, or label binding drift;
- Phase 491 owner-route state drift;
- nonclaim drift;
- accepted append owner drift;
- local transaction route drift;
- materialized route drift;
- policy owner drift;
- policy type drift;
- policy version type drift;
- HSAI accepted append policy-version marker drift;
- candidate policy id, version, or mode drift;
- append transaction version type or version drift;
- claim-boundary cap drift;
- disallowed evidence-class drift;
- review-decision requirement drift;
- rejection-policy drift;
- promotional policy-version summary text;
- accepted append policy changes;
- accepted append decisions;
- accepted Evidence Ledger mutation;
- accepted formal evidence creation;
- Level2+ evidence creation;
- score-axis population;
- proof/checker/solver promotion;
- backend execution evidence creation;
- benchmark evidence creation;
- SOTA, semantic-correctness, production-readiness, breakthrough,
  full-security, or action-authority claims.

## Meaning Limit

Phase 493 supports only this claim:

```text
HSAI locally records the accepted append policy/version identifiers that a
future accepted append bridge must bind before it can ask zkbench-core to
evaluate an accepted-ledger append transaction.
```

It is still not:

- accepted append;
- accepted formal evidence;
- accepted Evidence Ledger mutation;
- accepted append policy change;
- Level2+ evidence;
- score-axis evidence;
- Lean proof;
- SMT proof authority;
- COBALT containment evidence;
- Rust-to-Lean proof;
- benchmark evidence;
- SOTA;
- semantic correctness;
- production readiness;
- full security;
- authority to execute an action.

## Next Responsible Slice

Phase 494 defines the docs-first accepted evidence class and claim-boundary
boundary in
`docs/494-hsai-tiny-z3-accepted-evidence-class-and-claim-boundary.md`.
That boundary keeps `zkbench-core` as the evidence class and claim-boundary
owner and records the exact class/boundary pair that any future accepted append
bridge must bind before asking `zkbench-core` to evaluate an accepted-ledger
append transaction.
