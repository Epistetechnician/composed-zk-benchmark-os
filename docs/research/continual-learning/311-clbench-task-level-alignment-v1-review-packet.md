# Independent review packet: CL-Bench task-level alignment V1

State slice: `aligned-holistic-continual-learning-interpretability-monorepo-v1`.

Packet status: `PENDING_INDEPENDENT_ACCEPT`.

This packet requests independent review of the exact protocol source and
machine manifest. It requests no model execution, benchmark-data acquisition,
provider call, spend, assessment, raw-trace retention, or Evidence Ledger
mutation. The operator must not self-sign the review.

## Review object

- Protocol: `clbench-task-level-alignment-v1`
- Human protocol: `310-clbench-task-level-alignment-v1-protocol.md`
- Machine manifest: `experiments/continual_learning/clbench_task_level_alignment_v1.json`
- State slice: `aligned-holistic-continual-learning-interpretability-monorepo-v1`
- Claim ceiling: `LocalDevelopmentCLBenchTaskLevelProtocolDesignV1`
- Current disposition: `DESIGN_ONLY_PENDING_INDEPENDENT_ACCEPT`

The exact external benchmark binding is release commit
`9cc63c0f429048b843e8d43ac4f2b0ea4df13724` with tree
`ec757e2d999d895a7beec03270c6d014c01f2915`. The machine manifest records the
task-manifest paths and a byte-exact review-bundle roster. The reviewer must
verify those bindings before considering any check passed. A change to any
bound byte requires a new packet identity and a new review.

The reviewer must independently recompute the SHA-256 digest of this packet,
the machine manifest, and the source checkout before issuing a verdict. The
machine manifest binds this packet digest.

## Proof-bound handoff

The transport boundary is
`tools/independent_review_communication_v1/`. Its strict canonical JSON,
append-only mailbox, Ed25519 signatures, seal, and verdict verifier are the
only permitted handoff mechanism for this packet. The mailbox packet binding
must use the canonical manifest digest as `sha256:<64 lowercase hex>`; the
packet's raw-file SHA-256 remains the manifest-bound `packet_sha256` reviewed
by the final reviewer.

The operator may use a local subagent proxy or a Gman H100 for advisory
recomputation, transcript preparation, and tamper checks only. Those actors
are in the operator's trust domain and cannot issue the final verdict. A final
`ACCEPT` is valid only when its signature verifies against a separately
administered registry key marked `independently_administered=true` and
`conflict_free=true`, with reviewer identity and key distinct from the
operator. A generated local key, local boolean, subagent output, H100 result,
or operator signature cannot satisfy that requirement.

The sealed verdict remains review authority only. It does not authorize model
execution, provider calls, spend, assessment, raw-trace retention, or Evidence
Ledger mutation; those gates require separate authorization in a later packet.

The CL-Bench-specific verifier is
`experiments/continual_learning/clbench_task_level_alignment_review_bridge_v1.py`.
The operator may run its `binding` command to produce the handoff digests. The
operator must not run a signing command because this bridge intentionally has
no signing path. The final reviewer returns the typed receipt only through an
externally administered mailbox/registry; a local subagent may prepare
advisory questions and recompute the binding but cannot produce this receipt.

## Required review checks

The reviewer must record `PASS` or `FAIL` for every check. A single `FAIL`,
unresolved ambiguity, stale byte, or missing external binding is a rejection
for this protocol identity; there is no adaptive repair under the same packet.

1. **Benchmark identity:** verify the primary benchmark is the Apache-2.0
   `pgasawa/continual-learning-bench` release and that no benchmark bytes are
   present in this repository.
2. **Benchmark semantics:** verify the six task IDs, ordered-instance reward,
   feedback boundary, stateful/stateless gain, and protected-task orchestration
   are implementable without changing benchmark scoring.
3. **Life exclusion:** verify that Tencent `CL-bench Life` remains excluded
   from update arms because its evaluation-only license forbids parameter
   updates and adaptation.
4. **Arm completeness:** verify the exact seven-arm panel: no-update, SGD,
   replay, EWC, orthogonal, ICL, and external memory.
5. **Incoming estimand:** verify paired task-level incoming learning is
   distinct from raw reward and from the official stateful gain diagnostic.
6. **Protected estimand:** verify protected probes are fresh, disjoint,
   feedback-free, task-level, and compared against the no-update control.
7. **Split integrity:** verify fit/tune/assessment families are disjoint and
   assessment is unseen at prediction-lock time.
8. **Resource equality:** verify data, environment steps, token ceilings,
   compute units, persistent state bytes, and monitor calls are all metered.
9. **Statistics:** verify family-first analysis, six task tests, Holm
   correction, fixed bootstrap count, fixed margins, and fail-closed missingness.
10. **Prediction lock:** verify fit/tune-only selection, one digest per
    assessment family, no assessment labels/effects at lock, and independent
    recomputation.
11. **Custody:** verify new external owner-only `0700` roots, role separation,
    72-hour raw-trace deletion, aggregate-only repository retention, and prior
    root exclusion.
12. **Replication:** verify the fresh runner, seed set, custody root,
    same-protocol-digest requirement, and no assessment claim before replication.
13. **Claim ceiling:** verify that a passing design or local contract check
    cannot claim model evidence, benchmark evidence, general alignment,
    production readiness, or a breakthrough.
14. **Execution closure:** verify all execution gates are false and that an
    independent `ACCEPT` alone does not authorize execution or spend.

## Reviewer verdict schema

The independent reviewer must return a separately administered, packet-bound
Ed25519-signed receipt with exactly:

```text
schema_version: clbench-task-level-alignment-v1-independent-review-receipt
protocol_id: clbench-task-level-alignment-v1
state_slice: aligned-holistic-continual-learning-interpretability-monorepo-v1
decision: ACCEPT or REJECT
reviewer_identity: <independent identity>
reviewer_role: FINAL_REVIEWER
conflict_of_interest: false
reviewed_at_utc: <UTC timestamp>
protocol_digest: <canonical manifest digest>
manifest_sha256: <sha256 of exact machine manifest bytes>
packet_sha256: <sha256 of this exact file>
review_bundle_sha256: <canonical review-bundle digest>
checks: <exact 14 named checks with PASS/FAIL>
execution_enabled: false
model_execution_authorized: false
provider_calls_authorized: false
assessment_opened: false
signature: <external reviewer signature>
```

The external registry must itself be signed by a separately provisioned
registry-owner public key. The verifier rejects an unsigned or locally
self-declared registry, a reviewer key without both
`independently_administered=true` and `conflict_free=true`, a missing or
failing check, any digest mismatch, any receipt inside this repository, or any
receipt that enables execution.

The registry object must have exactly these top-level keys:
`schema_version`, `registry_id`, `issuer`, `issued_at_utc`, `expires_at_utc`,
`keys`, and `registry_signature`. Its schema version is
`clbench-task-level-alignment-v1-external-reviewer-registry`; each key entry
has exactly `key_id`, `identity`, `role`, `public_key_base64`,
`independently_administered`, and `conflict_free`. The registry owner signs
the canonical JSON object with `registry_signature` removed. The owner public
key is supplied out of band as a 32-byte owner-only file and is not accepted
from the registry itself.

The receipt's outer `signature` has exactly `algorithm`, `key_id`,
`public_key_base64`, and `signature_base64`; the reviewer signs the canonical
receipt object with `signature` removed. The bridge verifies that signature
against the owner-signed registry entry and binds it to the current manifest,
packet, review bundle, and protocol digest.

Verify a returned receipt with:

```text
PYTHONDONTWRITEBYTECODE=1 ./scripts/python -B -m experiments.continual_learning.clbench_task_level_alignment_review_bridge_v1 verify-receipt --receipt /external/review/receipt.json --registry /external/review/registry.json --registry-owner-key /external/review/registry-owner.pub
```

No receipt is present in this checkout. A local boolean, local test result,
operator signature, or narrative approval is not an independent acceptance.

## Meaning limits

This packet defines a credible external task-level test. It is not evidence
that any arm improves continual learning. It does not reopen the frozen CAL
synthetic policy-tuning lane, import prior CAL/AHCL/Oak/MiniMind/Astral/Qwen
results, authorize a model or provider, establish a benchmark result, or
permit a production or general-alignment claim.
