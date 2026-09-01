# Plasticity guard independent replication V2 review packet

Date: 2026-08-29.

State slice: `continual-learning-plasticity-guard-independent-replication-v2`.

Review status: `PENDING_INDEPENDENT_REVIEW`.

Mutation scope: documentation only. This packet does not authorize data
acquisition, model loading, training, adapter creation, custody-root creation,
GiveMeANode calls, H100 allocation, assessment, or scientific claims.

## Reviewer isolation

The reviewer must be a separate worker, process, session, or human from the
protocol author. The reviewer receives only this packet, the V2 protocol, and
the listed prior protocol/closure records. The reviewer must not inspect or use
prior V1 result artifacts, prior adapters, prior corpora, external buckets,
historical provider nodes, Astral artifacts, or plasticity-recovery outputs.

## Review inputs

~~~text
docs/research/continual-learning/120-plasticity-guard-independent-replication-v2-protocol.md
docs/research/continual-learning/105-plasticity-guard-replication-v1-protocol.md
docs/research/continual-learning/107-plasticity-guard-replication-v1-execution-record-2026-08-28.md
docs/research/continual-learning/119-contract-compiler-negative-capability-v3-terminal-closure-2026-08-29.md
~~~

The reviewer must verify the exact V2 protocol bytes and the packet bytes after
replacing `packet_sha256: SELF_DIGEST` with the same literal marker. Both
digests are recorded in the receipt. Once review begins, the V2 protocol and
packet are immutable; any edit invalidates the review and requires a new packet
digest and review.

## Digest record

~~~yaml
protocol_path: docs/research/continual-learning/120-plasticity-guard-independent-replication-v2-protocol.md
protocol_sha256: a25b5e4df0306234e351008196952614728f2099a61a62141b2910fe559a8ee8
packet_path: docs/research/continual-learning/121-plasticity-guard-independent-replication-v2-review-packet.md
packet_sha256: f121183101ca8d1bef7bdc8770b194898d924cb573da43342fc622f5655afe4b
packet_digest_normalization: replace packet_sha256 value with SELF_DIGEST
~~~

## Required findings

The reviewer must provide exactly one finding for each requirement, in order:

1. New state slice, terminal boundary, and non-reuse of prior scientific
   artifacts are explicit.
2. Cached actor, runtime, offline boundary, model manifest, and source/runtime
   digest requirements are exact and cannot authorize model shopping.
3. Gutenberg source identity, twelve-item allowlist, normalization, marker
   handling, token-window construction, split disjointness, and fresh custody
   are mechanically testable.
4. Seeds, orders, arms, compute equality, adapter reversibility, and the
   unchanged guard are fixed before acquisition and assessment.
5. The primary guarded-minus-fixed estimand, exact effect threshold, bootstrap
   rule, win count, no-update control, missingness rule, and classification
   precedence are mutually exclusive and preregistered.
6. Qualification gates cover parity, repeatability, zero identity, nonzero
   intervention reach, tensor shape, adapter restore, finite values, model
   immutability, custody, and independent validation.
7. Fit/tune/assessment ordering and prediction locking prevent assessment
   leakage and post-effect adaptation.
8. Independent validation is separate in source/process, verifies both roots,
   recomputes all aggregate decisions, and cannot use raw execution evidence.
9. Retention is aggregate-only in repository records and excludes raw corpus,
   token, logit, activation, adapter, credential, environment, and per-window
   data.
10. The implementation contract names exact files and permits only the local
    same-actor slice; no provider or cross-actor work is authorized.
11. The claim ceiling is narrow and classifications do not imply general
    continual-learning, architecture-generalization, Astral, Stage 0C, Stage
    1, benchmark, or production evidence.
12. Failure, missingness, custody drift, assessment repeat drift, and validator
    failure are terminal and cannot be repaired adaptively.

## Decision rule

`ACCEPT` is valid only when every requirement is satisfied or any limitation is
non-material to this local same-actor replication. `REJECT` is required for
any unresolved identity, custody, split, guard, estimand, leakage, validator,
retention, or authorization defect. `ACCEPT` permits implementation and
qualification drafting only. It does not itself authorize acquisition, model
execution, training, provider calls, H100 allocation, or assessment.

## Required receipt

The independent reviewer must write:

`docs/research/continual-learning/122-plasticity-guard-independent-replication-v2-independent-review-2026-08-29.md`

The receipt must be pure canonical JSON with exactly these top-level keys and
no others:

~~~json
{
  "state_slice": "continual-learning-plasticity-guard-independent-replication-v2",
  "reviewed_protocol_path": "docs/research/continual-learning/120-plasticity-guard-independent-replication-v2-protocol.md",
  "reviewed_protocol_sha256": "<lowercase-sha256>",
  "reviewed_packet_path": "docs/research/continual-learning/121-plasticity-guard-independent-replication-v2-review-packet.md",
  "reviewed_packet_sha256": "<lowercase-sha256>",
  "reviewer_role": "independent-plasticity-replication-reviewer-v2",
  "verdict": "ACCEPT or REJECT",
  "findings": [
    {
      "id": "<stable-id>",
      "requirement": 1,
      "severity": "critical|major|minor",
      "disposition": "pass|fail|limitation",
      "evidence": "<nonempty section evidence>"
    }
  ],
  "execution_authorized": false,
  "review_timestamp": "YYYY-MM-DDTHH:MM:SSZ"
}
~~~

The findings list must contain exactly twelve entries in requirement order.
The receipt must contain no corpus text, model weights, adapters, logits,
activations, credentials, provider state, or raw execution output. A `REJECT`
closes V2; an `ACCEPT` permits only the separate implementation authorization.

Every mutation in this packet touches state slice
`continual-learning-plasticity-guard-independent-replication-v2`.
