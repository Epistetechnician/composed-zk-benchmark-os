# Small-RSI Frontier-Substitution V1

State slice: `recursive-meta-harness-small-rsi-frontier-substitution-v1`

Status: local contract implementation complete; model and provider execution
closed.

## Purpose

This lane tests a bounded question:

> Can a small-model swarm with bounded recursive policy improvement substitute
> for a frontier single-agent system on a declared task distribution?

The claim ceiling is conditional task-distribution substitution. It does not
claim general frontier parity, recursive model-weight self-improvement, equal
performance at equal cost/latency/robustness/broad capability, production
readiness, SOTA, or breakthrough status.

## Frozen arms and regimes

The four complete-system arms are `frontier_single`, `small_single`,
`small_swarm_fixed`, and `small_swarm_rsi`. The primary regime compares the
complete declared systems under the same task, tool-authority, budget, and
grader identities. A separate component-ablation regime isolates swarm and
bounded-RSI effects within the small-model lane. These regimes cannot be
pooled.

The task plan has four families, fit/tune/assessment splits, three replicates,
and author/template/task-digest disjointness. Assessment remains sealed until
prediction locking and independent review.

## Metric and gates

Verified utility is fixed-point integer utility in `[0, 1_000_000]`. It becomes
zero for any safety, integrity, authority, leakage, audit, timeout,
infrastructure, or terminal-verification failure. Full economic cost is the
sum of fixed-point USD-micro components for model calls, reasoning, routing,
verification, retries, compaction, memory, tools, compute, storage, cleanup,
and human review. Missing components reject the observation; they never become
zero.

The intended future primary comparison is paired verified utility of
`small_swarm_rsi` against `frontier_single`, with a preregistered non-inferiority
margin of `-20,000` utility micros and a minimum 20% full-cost reduction. The
fixture does not compute this assessment comparison.

## RSI boundary

Development-only updates may change prompt, plan, routing, or verifier
escalation policy. They may not change tasks, assessment membership, graders,
hard constraints, thresholds, pricing, authority policy, stop rules, claim
ceilings, base weights, adapters, or provider purchases. Shared-history
descendants are not independent replications. Every candidate requires a
parent digest, candidate digest, rollback path, and immutable evaluation bundle.

## Implementation result

`protocol_v1.py` defines the pure-data contract and fixed-point utility/cost
rules. `compiler_v1.py` emits a digest-bound manifest that pins the protocol,
compiler, and fixture-runner source bytes. `runner_v1.py` emits only a
deterministic model-free contract fixture over fit and tune rows.
`validator_v1.py` independently validates the manifest, pending review packet,
and fixture without importing the compiler or runner. `review_v1.py` emits a
pending packet and verifies an independently signed Ed25519 `ACCEPT`; the
receipt is cryptographically bound but remains non-authorizing in this slice.
Tests cover determinism, source drift, cost omission, hard-constraint zeroing,
assessment sealing, digest tampering, independent-signature rejection and
acceptance, and overwrite protection.

The fixture is not model evidence. No model, provider, network, benchmark,
external custody root, signed independent review, assessment result, accepted
Evidence Ledger write, or scientific claim exists under this slice.

## Execution gate

Before any model-bearing run, a fresh protocol review, packet-bound independent
signed `ACCEPT`, exact model/runtime/task identity, positive user-authorized
hard USD ceiling, and external owner-only custody root are required. This local
package does not grant those authorities.
