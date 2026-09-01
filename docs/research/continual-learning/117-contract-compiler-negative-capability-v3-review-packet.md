# Contract compiler and negative-capability audit v3 review packet

Date: 2026-08-29.

State slice: continual-learning-contract-compiler-negative-capability-v3.

Review status: PENDING_INDEPENDENT_REVIEW.

Mutation scope: documentation only under this state slice. The packet does not
authorize implementation, model or corpus access, storage, provider calls,
node creation, H100 allocation, training, or assessment.

## Reviewer isolation

The reviewer must be a separate worker, process, session, or human from the
protocol author. The reviewer receives only this packet, the V3 protocol, and
the V1/V2 rejection and closure records listed below. The reviewer must not
inspect or use the pre-existing plasticity implementation, external buckets,
historical H100 nodes, Astral artifacts, or scientific results.

## Review inputs

~~~text
docs/research/continual-learning/116-contract-compiler-negative-capability-v3-protocol.md
docs/research/continual-learning/117-contract-compiler-negative-capability-v3-review-packet.md
docs/research/continual-learning/108-contract-compiler-negative-capability-v1-protocol.md
docs/research/continual-learning/110-contract-compiler-negative-capability-v1-independent-review-2026-08-28.md
docs/research/continual-learning/111-contract-compiler-negative-capability-v1-terminal-closure-2026-08-28.md
docs/research/continual-learning/112-contract-compiler-negative-capability-v2-protocol.md
docs/research/continual-learning/114-contract-compiler-negative-capability-v2-independent-review-2026-08-29.md
docs/research/continual-learning/115-contract-compiler-negative-capability-v2-terminal-closure-2026-08-29.md
~~~

The reviewer must recompute the V3 protocol SHA-256 from exact file bytes. The
packet digest is computed after replacing the packet's recorded packet digest
with the literal marker packet_sha256: SELF_DIGEST. Both digests must be
recorded below before review begins. After review begins, the V3 protocol and
packet are immutable. Any edit invalidates the packet and requires a new
digest and review.

## Review requirements

The reviewer must verify with evidence and section references:

1. V3 is a new state slice and binds the V1/V2 and adaptive-verification
   exclusion identities without reopening or repairing them.
2. The compiler input interface is complete, typed, positional, and explicit;
   the harness boundary is separate and limited to the ten declared inputs.
3. The source-capability policy is mechanically executable: exact imports,
   aliases, relative imports, wildcard imports, module-qualified calls,
   receiver binding, bare builtins, forbidden names/strings, dynamic imports,
   dynamic code, shadowing, AST traversal, and returned violation IDs.
4. The canonical parser algorithm fully specifies strict UTF-8, BOM, duplicate
   keys at depth, constants, negative zero, non-finite values, controls,
   canonical bytes, nested unknown/missing keys, scalar typing, booleans
   versus integers, list cardinality, regexes, and error precedence.
5. The recursive schema notation expands every top-level and nested object,
   exact key set, field type, enum, cardinality, range, and cross-field rule.
6. Protocol, contract, source, review, authorization, event, lock, retention,
   fixture, receipt, manifest, and command digest inputs and recomputation
   bindings are explicit; schema binding is not confused with custody proof.
7. Actor, custody, corpus, training, estimator, reliability, and power fields
   are complete and cannot authorize model, data, training, assessment, or
   provider execution.
8. Event records, payload fields and types, digest algorithm, contiguous
   sequence, timestamp parser/order, predecessor rules, review/authorization
   provenance, assessment prohibition, and lock transitions are complete.
9. Retention and deletion evidence are typed, aggregate-only output is closed,
   and raw input cannot escape through nested fields, exceptions, or stderr.
10. Classification predicates, precedence, receipt binding, and terminal
    behavior are mutually exclusive and mechanically evaluable.
11. The fixture bundle has an exact schema, 56 stable IDs, exact mutations,
    paths, replacements, expected failure IDs, expected message token, and a
    deterministic positive-base construction.
12. The exact isolated validator command, environment, process repeat count,
    output transport, and independent recomputation behavior are specified.
13. The claim ceiling and downstream stop boundary are explicit and do not
    authorize plasticity replication, mechanism audit, cross-actor replication,
    restart audit, GiveMeANode, H100, Astral, Stage 0C, Stage 1, or V82.

## Decision rule

ACCEPT is valid only if every requirement is satisfied or any limitation is
demonstrably non-material to the V3 local contract-audit ceiling. REJECT is
required for any material unresolved defect in schema, parser, source policy,
digest binding, event state, retention, classification, fixture precision,
runner transport, independence, or authorization boundary.

ACCEPT permits implementation and hermetic qualification only. It does not
authorize a future execution authorization, model loading, corpus acquisition,
external custody, provider call, node creation, H100 allocation, training, or
assessment.

## Digest record

~~~yaml
protocol_path: docs/research/continual-learning/116-contract-compiler-negative-capability-v3-protocol.md
protocol_sha256: 34c789b704fb1e6c8d7ccd971f08d15bc3b669488cdfed42b8c876ea2189386e
packet_path: docs/research/continual-learning/117-contract-compiler-negative-capability-v3-review-packet.md
packet_sha256: b39de0d17d1c725f9122d96b6b04c3ee4ec1acde883cea971321d94a52db01f0
packet_digest_normalization: replace the packet_sha256 value with SELF_DIGEST
~~~

## Required receipt

The independent reviewer must write:
docs/research/continual-learning/118-contract-compiler-negative-capability-v3-independent-review-2026-08-29.md

The receipt must be pure canonical JSON, not Markdown, with this exact object
shape and no additional keys:

~~~json
{
  "state_slice": "continual-learning-contract-compiler-negative-capability-v3",
  "reviewed_protocol_path": "docs/research/continual-learning/116-contract-compiler-negative-capability-v3-protocol.md",
  "reviewed_protocol_sha256": "<lowercase-sha256>",
  "reviewed_packet_path": "docs/research/continual-learning/117-contract-compiler-negative-capability-v3-review-packet.md",
  "reviewed_packet_sha256": "<lowercase-sha256>",
  "reviewer_role": "independent-contract-reviewer-v3",
  "verdict": "ACCEPT or REJECT",
  "findings": [
    {
      "id": "<identifier>",
      "severity": "critical|major|minor",
      "requirement": 1,
      "disposition": "pass|fail|limitation",
      "evidence": "<nonempty evidence>"
    }
  ],
  "execution_authorized": false,
  "review_timestamp": "YYYY-MM-DDTHH:MM:SSZ"
}
~~~

The findings list must have exactly 13 entries, one for each requirement, in
requirement order. The reviewer must recompute both reviewed digests and use
the exact fixed state slice and reviewer role. The receipt contains no
credentials, raw contract bytes, source text, corpus text, model paths beyond
the reviewed protocol literals, logits, activations, adapter tensors, or
provider state. A REJECT is terminal for V3; an ACCEPT permits implementation
only and is not a scientific result.
