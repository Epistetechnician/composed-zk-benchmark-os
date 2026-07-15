# Phase 796-A3L4I HSAI P01B Container Command/Receipt Contract Implementation

## Status

Complete as an independently reviewed local pure-data implementation of the
exact two-file state slice authorized by Phase 796-A3L4.

State slice:
`phase-796a3l4i-hsai-p01b-container-command-receipt-contract-implementation`.

Classification: `P01BContainerCommandReceiptContractAccepted`.

Execution status: `LocalValidationOnly`.

Evidence ceiling: `Level1LocalReplayOrLower`.

Decision: `accept_local_contract_only`.

## Bound Git Objects

```text
A3L4 boundary commit = ad8b8b63b81a2ddf7e3864f5d9b05abbd7f00b5f
rejected implementation candidate = 16e790e200e158756a5704192f5c317e4b7a9632
accepted correction commit = ddb1cca33954c3af98facfd3215b4157483e1c4d
accepted correction tree = f9df55b7abfbe765ffc8f4310243cc0a712c8bb1
reviewed cumulative range = ad8b8b63b81a2ddf7e3864f5d9b05abbd7f00b5f..ddb1cca33954c3af98facfd3215b4157483e1c4d
```

The cumulative implementation range changes exactly the two authorized paths:

| File | Bytes | SHA-256 |
|---|---:|---|
| `tools/hsai-formal-preflight/p01b_container_contract.py` | 41,707 | `878055c5e558dfd255c8ad9683bb75c8f8943af62f7df614692c59eb52f42ce0` |
| `tools/hsai-formal-preflight/tests/p01b_container_contract_tests.py` | 40,546 | `d7a2f82e3b611ca2a4a50db05a0dc8635d0d7a132e819b86db08f780b744cab8` |

This phase note and the four standard mirrors form the separate documentation
commit required by the boundary.

## Implemented Contract

The module is pure data. It defines a caller-supplied authorization root that
binds action, policy, evidence-bundle, and admission-decision digests; exact
placeholder bindings; a deterministic Docker command plan; strict canonical
receipt parsing; receipt digest chaining; and the fail-closed lifecycle.

Every public executable or receipt boundary validates the authorization root,
placeholder bindings, exact plan, and prior receipt prefix. Caller-constructed
`AttemptState` values cannot authorize commands or transitions. The only
runtime placeholder is the stable container id emitted by successful create,
and no executable command may retain it unresolved.

The lifecycle implements create, pre-start inspection, start/attach, wait,
terminal inspection, and removal. Bounded start failures add kill before wait.
Nonzero and signaled start outcomes still route through wait, terminal
inspection, and cleanup. Final-chain validation rejects every nonterminal
prefix, including missing kill and missing removal.

Commands bind a 1,800-second timeout and 16,384-byte stdout/stderr caps.
Receipts distinguish retained bytes from total observed bytes and reject
fabricated timeout, cap, or truncation outcomes. Absolute bindings reject
Docker mini-language delimiters and noncanonical paths; manifest references
use a closed OCI repository grammar; strict JSON is byte-, node-, and
depth-bounded and normalizes recursion failures to `ContainerContractError`.

The module imports no process, filesystem, environment, Docker, socket,
network, CLI, or dynamic-import authority and writes nothing.

## Rejected Candidate And Correction

Immutable candidate `16e790e2` was rejected by two independent reviewers.
Their combined findings were:

- tampered privileged or shell plans could be rebound and accepted;
- caller-forged lifecycle state could request kill or removal;
- nonterminal receipt prefixes passed final-chain validation;
- timeout and stream-limit outcomes could be fabricated;
- nonzero or signaled start skipped wait;
- Docker mount/path and option-like OCI inputs were insufficiently closed; and
- deeply nested JSON could escape as raw `RecursionError`.

Correction `ddb1cca3` closes each finding and adds direct regression coverage.
Both final reviewers inspected the immutable corrected head and the complete
two-file range. Both returned `accept` with zero findings.

## Validation

```text
Python 3.9.6 focused A3L4I tests: 21 passed, 0 failed, 0 skipped
Python 3.9.6 frozen A3L3 corpus tests: 21 passed, 0 failed, 0 skipped
Python 3.9.6 normal formal-preflight discovery: 172 passed, 0 failed, 0 skipped
ruff: passed
cargo fmt --all -- --check: passed
unaffected Rust workspace tests: passed
unaffected Rust workspace clippy with -D warnings: passed
cumulative-range git diff --check: passed
exact two-path range check: passed
```

The unaffected Rust commands exclude `hsai-agent-admission` and
`hsai-e2e-harness` because the preserved user-owned admission edit removes
exports consumed by those packages. That file remains unstaged at SHA-256
`41530d449871484b7c0f15869bab9c892c328d6ab982b166bad3223147f173de`.
No implementation or validation command used Docker, a Docker socket, network,
archive acquisition, a container, or a backend. The repository has no root
`package.json`, so no root `pnpm run lint` target exists; no `npm` substitute
was used.

## Independent Reviews

```json
{"decision":"accept","findings":[],"reviewed_commit":"ddb1cca33954c3af98facfd3215b4157483e1c4d","reviewer_id":"codex-subagent:evidence-gap-audit","reviewer_role":"independent-security-capability-reviewer"}
```

```text
review record bytes = 205
review record sha256 = c7ab96ea5c1e29daa58eaf2af0ec75b37a56bbb4d8b067b219f0e289d5b698b0
```

```json
{"decision":"accept","findings":[],"reviewed_commit":"ddb1cca33954c3af98facfd3215b4157483e1c4d","reviewer_id":"codex-subagent:implementation-seam-audit","reviewer_role":"independent-contract-reproducibility-reviewer"}
```

```text
review record bytes = 217
review record sha256 = 80aef01443ae81e67ae3468652af12e7d22084251be034aaf92607aca7267124
```

```json
{"decision":"accept","review_record_digests":["c7ab96ea5c1e29daa58eaf2af0ec75b37a56bbb4d8b067b219f0e289d5b698b0","80aef01443ae81e67ae3468652af12e7d22084251be034aaf92607aca7267124"],"schema":"hsai-p01b-container-command-receipt-review-aggregate-v1"}
```

```text
aggregate bytes = 248
aggregate decision sha256 = fca3090a3408ebbe81898c115c698c3e2f3156e924f163349629fa404c2b90a5
```

## Metric And Claim Boundary

The separate readiness bit changes from
`c10_local_contract_implemented=false` to `true`.

The mechanical correspondence metric remains exactly 2/10: C01 and C08 are
closed; C02-C07, C09, and C10 remain open. C10 requires retained execution
receipts and independent correspondence review. This local contract does not
raise the commercial-moat score or the defensible-breakthrough-evidence score.

This phase creates no receipt observation, Docker or container result,
containment result, runtime-provenance result, filesystem certificate, archive
acquisition, backend run, proof artifact, accepted evidence, Level2+ evidence,
score-axis result, independent reproduction, commercial moat, semantic
correctness, production readiness, SOTA, breakthrough, full security, external
audit, or action authority.

## Next Gate

The next score-moving slice is a separate docs-first driver, probe,
effective-containment receipt, platform/runtime provenance, ingress/egress
certificate, and independent-review boundary for C02-C07, C09, and C10. A
retained normal and OOM run remains unauthorized until those controls are
implemented and independently audited.
