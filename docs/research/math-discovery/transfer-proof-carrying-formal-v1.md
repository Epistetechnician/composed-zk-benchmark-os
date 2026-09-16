# Proof-carrying symbolic transfer formal contract V1

State slice: `proof-carrying-symbolic-transfer-formal-v1`.

Protocol identity: `weco-symbolic-discovery-transfer-formal-v1`.

Status: `MACHINE_CHECKED_SCOPED / LOCAL_CONTINUATION_AUTHORIZED / EXTERNAL_REVIEW_REQUIRED_FOR_ESCALATION`.

This slice connects the repository's existing digest, formal-lane, and
fail-closed evidence concepts to a small Lean M0 contract. The source has now
been checked by the pinned Lean kernel. The
Lean project is intentionally separate from `formal/hsai-gateway-digest`; it
does not import historical gateway fixtures or scientific result artifacts.

## Proven properties

`MathDiscovery/TransferContract.lean` proves:

- the candidate's input is the public projection of an episode;
- replacing every hidden program leaves the public projection unchanged;
- a candidate run is therefore invariant under evaluator-only truth mutation;
- checked outputs carry an exact task-count equality and depth bound;
- family-level numerator aggregation is invariant under family permutation;
- a receipt is machine-scoped only when its protocol identity and machine-check
  flag match;
- independent review is an explicit additional predicate and is never inferred
  from machine checking;
- the claim ceiling is exactly `LocalMachineCheckedFormalContractOnly`.

These are abstract properties. They do not prove that the existing Python
candidate or benchmark refines this Lean model. A future refinement proof or
verified execution kernel must bind the concrete implementation bytes to these
definitions before any cross-language claim is made.

## Local continuation authority

For this exact state slice, the successful pinned Lean kernel check is
sufficient verification to continue local clean-room formal refinement and
synthetic contract/hill-climbing work. No independent reviewer is required
for that bounded continuation.

The exception does not authorize scientific or model-bearing execution,
external corpus or custody, provider calls or spend, accepted Evidence Ledger
mutation, external claims, benchmark/SOTA/breakthrough/production claims, or
any claim above `LocalMachineCheckedFormalContractOnly`. It does not convert
the result into `IndependentlyReproducedEvidence`, and it does not upgrade the
legacy `zkbench-core` `NoopFormalVerifier`. A concrete evaluator refinement or
ZK execution relation requires a fresh protocol identity, exact digests,
fail-closed validation, and a separately recorded authority boundary.

## Verification

From the repository root:

```text
bash scripts/verify_math_discovery_formal_v1.sh
```

The command invokes the pinned Lean `v4.30.0` toolchain and prints:

```text
formal_contract_check: PASS
claim_ceiling: LocalMachineCheckedFormalContractOnly
local_continuation: AUTHORIZED
independent_review_for_escalation: REQUIRED
```

The command passed twice, including a direct second kernel invocation. This
is a scoped machine-checked formal contract, not independent reproduction or
scientific evidence. The local-continuation exception is recorded in the live
`AGENTS.md`; historical AGENTS digests in prior records remain historical and
are not rewritten.

## Frozen inputs

```text
54727eec5cba149c18842e6deb5c41b369d66455c93ce135d7d5347c782b2325  formal/math-discovery-v1/lean-toolchain
cb1c3c7e97083819634dbac5d9b0d1d35d46ef43d93384fab7e27d88b5a592ce  formal/math-discovery-v1/lakefile.toml
a66dbae1b0c8eda1ceffbbd4991cd4f86728ecd3fa8d6791358f6078a29711ac  formal/math-discovery-v1/MathDiscovery/TransferContract.lean
c67638560ebac3068a548de37c3e93215a7eac895138aaa8bb3c78b8de4e6301  scripts/verify_math_discovery_formal_v1.sh
625cb347a02c41c66d9611d47d2fbad66685efb99da2fe8f03975feac4329423  AGENTS.md
```

The Rust `zkbench-core` formal lane remains conservative: its existing
`NoopFormalVerifier` is declared-only. This Lean result must not be inserted
into the accepted Evidence Ledger or used to raise a benchmark, SOTA,
scientific, provider, or external-review claim.

## Next refinement boundary

The next permitted engineering slice is a clean-room refinement checker that
binds a concrete, non-model synthetic evaluator to this contract. It must use a
new protocol identity, exact source/toolchain digests, an independent Lean
replay, and a fresh review packet. A ZK backend can later prove execution of
that checked kernel over private inputs, but it cannot prove licensing,
reviewer independence, or scientific generalization.
