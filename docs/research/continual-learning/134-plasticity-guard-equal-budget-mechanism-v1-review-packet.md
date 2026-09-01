# Equal-budget plasticity-guard mechanism V1 independent-review packet

State slice: `continual-learning-plasticity-guard-equal-budget-mechanism-v1`.

Review status: `PENDING`.

The independent reviewer receives only this packet, the protocol named below,
and the contract named below. The reviewer must not inspect prior result roots,
model files, corpus files, provider state, implementation source, or any
scientific artifact from another slice.

## Review inputs

- Protocol:
  `docs/research/continual-learning/133-plasticity-guard-equal-budget-mechanism-v1-protocol.md`
- Contract:
  `.autoresearch/continual-learning-plasticity-guard-equal-budget-mechanism-v1/contract.md`
- Prior records supplied only as rationale and boundary:
  `docs/research/continual-learning/91-plasticity-guard-reversible-adapter-v1-execution-record-2026-08-28.md`
  and
  `docs/research/continual-learning/123-plasticity-guard-independent-replication-v2-terminal-closure-2026-08-29.md`

The reviewer must recompute the protocol and contract SHA-256 values and record
them in the receipt. Any digest mismatch, missing file, or input mutation is a
REJECT.

## Acceptance requirements

The reviewer must issue exactly one finding for each requirement, in this
order:

1. New state-slice identity and non-reuse of closed records/artifacts.
2. Causal theory: equal-budget selection isolates update selection from update
   count.
3. Exact model, runtime, source paths, and custody-root boundary.
4. Fresh Gutenberg corpus identity, exact IDs/URLs, normalization, and
   document-disjoint splits.
5. Exact pair construction, candidate generation, adapter semantics, and
   immutable base.
6. Three meaningful arms with identical candidate-generation compute and six
   commits per arm.
7. Primary and secondary estimands, exact effect threshold, win rule,
   bootstrap, and multiplicity handling.
8. Power simulation and case-level reliability requirements.
9. Qualification gates, shapes, parity, zero identity, nonzero reach, and
   terminal failure precedence.
10. Fit/tune separation and prediction-lock ordering before assessment.
11. Independent pre-assessment review contract and explicit no-execution
    boundary.
12. Independent validator byte interface, digest recomputation, event checks,
    and isolated invocation.
13. Aggregate-only retention, raw-evidence exclusion, cleanup, and credential
    redaction.
14. Narrow classification enum, claim ceiling, and prohibition on Astral,
    Stage 0C, Stage 1, benchmark, safety, and production claims.
15. Implementation contract completeness, pure contract-check behavior, and
    absence of hidden model/corpus/provider/H100 authority.

ACCEPT is permitted only when every material requirement is executable,
internally consistent, and sufficient for the narrow protocol/qualification
ceiling. ACCEPT does not authorize model loading, corpus acquisition,
training, assessment, provider calls, or H100 allocation. Any material
defect is REJECT and terminates this state slice before implementation.

## Required pure JSON receipt

The reviewer writes only the following pure canonical JSON receipt to:

```text
docs/research/continual-learning/135-plasticity-guard-equal-budget-mechanism-v1-independent-review-2026-08-29.json
```

The top-level keys must be exactly:

```text
state_slice
reviewed_protocol_path
reviewed_protocol_sha256
reviewed_contract_path
reviewed_contract_sha256
review_packet_path
review_packet_sha256
reviewer_role
verdict
findings
execution_authorized
review_timestamp
```

`reviewer_role` must be
`independent-equal-budget-mechanism-reviewer-v1`. `verdict` is `ACCEPT` or
`REJECT`. `execution_authorized` must be the boolean `false`. `findings` must
contain exactly 15 ordered objects, each with exactly `criterion`, `severity`,
`disposition`, and `evidence`; `severity` is `critical`, `major`, or `minor`,
and `disposition` is `pass`, `fail`, or `limitation`. The timestamp is UTC
RFC3339 with seconds. No Markdown, raw data, model output, or exception text
may appear in the receipt.

## Review boundary

The current state is protocol-only and review-pending. A review ACCEPT may
open implementation and local qualification under the already recorded user
authorization, but it may not open assessment. A separate pre-assessment
review must accept the qualification, fit/tune aggregates, prediction lock,
configuration digest, and event ordering before assessment begins.

Every mutation governed by this packet touches state slice
`continual-learning-plasticity-guard-equal-budget-mechanism-v1`.
