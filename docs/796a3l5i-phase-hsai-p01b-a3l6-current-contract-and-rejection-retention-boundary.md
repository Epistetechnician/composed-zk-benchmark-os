# Phase 796-A3L5I HSAI P01B A3L6 Current Contract And Rejection-Retention Boundary

## Status

Complete as a documentation-first correction boundary. Execution remains
`NotRun`; A3L6 remains unaccepted; A3L7, A3L8, and A3L9 remain prohibited.

State slice:
`phase-796a3l5i-p01b-a3l6-current-contract-and-rejection-retention-boundary`.

This correction reconciles the current committed five-file A3L6 source state
with the stale counts in the original A3L5C and A3L6 audit records. It creates
no Docker, registry, network, container, benchmark, accepted-ledger, score,
Level2+, production-readiness, semantic-correctness, or authority result.

## Reason For Correction

The original A3L6 audit froze the earlier implementation commit
`bb258b5296040139fa504080e929401756588abd`, 21 materialized source paths,
64 focused tests, a 2 MiB A3L6 JSON cap, 200 candidate payloads, 201 file
reopens, and 270 publication events. Follow-on committed corrections changed
the current source state without a replacement immutable audit.

The clean committed source revision for this correction is
`27b34e9a9a79ffccb7cc404d9f6ad46a7973bd7d`, with tree
`98a50f662bb326ccb2d79e42f2336f8687de49e3`. Its five reviewed source paths
are unchanged through the current baseline commit except for no later committed
changes in those paths. It has these exact values:

| Contract item | Correct value |
| --- | --- |
| Immutable materialized source paths | 22 |
| Focused evidence tests | 32 |
| Focused execution tests | 33 |
| Combined focused census | 65 |
| Formal discovery census | 172 |
| Ordinary JSON cap | 1,048,576 bytes |
| A3L6 source/bundle cap | 4,194,304 bytes |
| Candidate payloads | 201 |
| Candidate files/reopens | 202 |
| Publication events | 271 |

The increased source count adds the committed corpus regression module. The
22 ordered source paths are:

```text
docs/796a-phase-hsai-p01b-archive-ledger-parser-and-acquisition-separation-boundary.md
tools/hsai-formal-preflight/bounded_runner.py
tools/hsai-formal-preflight/execution_state_machine.py
tools/hsai-formal-preflight/fixture_validator.py
tools/hsai-formal-preflight/p01b_archive_ledger.py
tools/hsai-formal-preflight/raw_archive_validator.py
tools/hsai-formal-preflight/tests/test_bounded_runner.py
tools/hsai-formal-preflight/tests/test_execution_state_machine.py
tools/hsai-formal-preflight/tests/test_fixture_validator.py
tools/hsai-formal-preflight/tests/test_p01b_archive_ledger.py
tools/hsai-formal-preflight/tests/test_p01b_container_corpus.py
tools/hsai-formal-preflight/tests/test_raw_archive_validator.py
tools/hsai-formal-preflight/p01b_container_corpus.py
tools/hsai-formal-preflight/p01b_container_test_corpus.json
tools/hsai-formal-preflight/p01b_container_seccomp.json
tools/hsai-formal-preflight/p01b_container_seccomp_license.txt
tools/hsai-formal-preflight/p01b_container_seccomp_provenance.json
tools/hsai-formal-preflight/p01b_container_probe.py
tools/hsai-formal-preflight/p01b_container_evidence.py
tools/hsai-formal-preflight/p01b_container_execution.py
tools/hsai-formal-preflight/p01b_container_execution_tests.py
tools/hsai-formal-preflight/p01b_container_evidence_tests.py
```

The former A3L6 audit does not accept this changed source state. A passing
in-memory preflight against it does not replace a frozen audit, retained result,
or independent review.

## Corrected Gate Semantics

The future A3L6R runner must materialize those 22 Git blobs from one
operator-supplied implementation commit and verify the supplied tree identity,
but it must also require a separate audited expected-bindings document. The
document must name the implementation commit/tree, audit commit, all five
reviewed blob hashes, the ordered 22-path census, counts, caps, and the current
candidate/publication cardinalities.

The expected-bindings document is a cross-binding input, not a cryptographic
trust root. It cannot turn caller-selected source IDs or self-generated review
records into independent acceptance. Two distinct, genuine reviewers must still
evaluate the retained bundle out of band. Their records must bind the same
implementation, tree, expected-bindings digest, and gate-observation digest.

The three gate rows remain hermetic: Git/Python/sandbox only, closed stdin,
replacement environment, bounded streams, explicit executable identity, and
network denial. They must never invoke Docker, a registry, a socket, a
container, an external endpoint, or a backend.

The discovery-172 row is a Seatbelt-stubbed test census. It is not full-suite
semantic execution. Host-only focused checks skipped while
`P01B_GATE_SANDBOX_ACTIVE=1` must be called out in the retained run record;
they may not be described as exercised sandbox controls.

## Rejection-Retention Contract

The future A3L6R implementation must add a bounded local operator entry point
under the existing five-file A3L6 source surface. It must accept a caller-owned,
absolute, non-repository output root and reject symlinks, nonempty destinations,
and path traversal. It must write an atomically materialized, non-secret run
record before cleanup. The record must retain either outcome:

```text
a3l6-gate/
  expected-bindings.json
  gate-run.json
  gate-run.sha256
```

`gate-run.json` must include the accepted or rejected classification, complete
bounded per-command observations, command role, exit code or signal, truncation
facts, retained stream digests, source/audit bindings, and the reason when a
capture or gate step fails. It may retain only the already bounded stream bytes;
there is no secret or credential input in this phase.

A rejected run record may be used for diagnosis only. It cannot produce an
accepted A3L6 bundle, authorize A3L7, close any correspondence class, move a
score, mutate an Evidence Ledger, or support a production claim. A successful
gate run is likewise only a pending-review artifact until the two independent
reviews are separately supplied and validated.

## Authorized Follow-On Implementation

After this boundary is committed, Phase 796-A3L6R may modify only:

```text
tools/hsai-formal-preflight/p01b_container_probe.py
tools/hsai-formal-preflight/p01b_container_evidence.py
tools/hsai-formal-preflight/p01b_container_execution.py
tools/hsai-formal-preflight/p01b_container_evidence_tests.py
tools/hsai-formal-preflight/p01b_container_execution_tests.py
```

plus a phase implementation note and the standard navigation mirrors. It may
implement the durable local gate-run record, mandatory expected-bindings
cross-check, failure diagnostics, and hermetic regression tests. It may not
change Cargo metadata, Rust source, benchmark packs, ledger policy, Docker
state, registry/network access, container execution, external replay,
credentials, score axes, evidence level, or A3L7/A3L8/A3L9 authority.

Its exit criteria are exact source and expected-bindings validation, retained
accepted-or-rejected output, error-path regression coverage, unchanged-status
enforcement, and an honest statement of the Seatbelt-stubbed discovery limit.
It does not accept A3L6. A separate immutable audit and two genuine reviews
remain mandatory afterward.

## Nonclaims

This correction does not establish source correspondence, a proof, formal
correctness, independent reproduction, external audit, production readiness,
SOTA, full security, or any authority to run A3L7, A3L8, A3L9, Docker, registry,
or network commands.
