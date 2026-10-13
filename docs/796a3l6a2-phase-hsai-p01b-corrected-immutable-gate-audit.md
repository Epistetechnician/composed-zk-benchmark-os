# Phase 796-A3L6A2: P01B Corrected Immutable-Gate Audit

Named state slice:
`phase-796a3l6a2-p01b-corrected-immutable-gate-audit`.

## Purpose and clean baseline

This audit freezes corrected A3L6 implementation commit
`d70b879e01de7978597be698eace127cb0604ff7` and tree
`33f8f500c7461026a3bb6bb0b4a27ad2ab050ebf`. The only source correction since
the first audit attempt is the execution-focused test's temporary-root
selection: it uses the existing nested Seatbelt scratch root when the gate
marker is set and retains `/private/tmp` for host-only testing.

The first audit/run is retained as a rejected diagnostic. It is not relabeled
or promoted. This new clean implementation identity requires a new canonical
binding and detached gate run.

The dirty primary checkout is excluded. Its active P01B changes are
A3L7-adjacent retained-runtime work; its admission and `docs/agents/` work is
unrelated. Neither is part of this clean A3L6 baseline.

The audit commit cannot be written here before it exists. After this document
is committed, canonical expected-bindings JSON must include the resulting
immutable audit commit. That ordering avoids a self-referential identifier.

## Reviewed implementation blobs

The canonical expected-bindings document uses this ordered five-blob review
set. Any digest mismatch is a rejected gate result.

| Order | Path | SHA-256 |
| --- | --- | --- |
| 1 | `tools/hsai-formal-preflight/p01b_container_probe.py` | `75435eabfd7bfae0ddc568251f039b1e96689167ef0cf3dd91df9a0216985a28` |
| 2 | `tools/hsai-formal-preflight/p01b_container_evidence.py` | `3f0fdcac91abffed9f36150cd420bb9f62859c135969042b1caf3d724daecec8` |
| 3 | `tools/hsai-formal-preflight/p01b_container_execution.py` | `38cca3f665232ccf56499bbb32354d9e43529e7746c5f0b97002e70b71c74e6f` |
| 4 | `tools/hsai-formal-preflight/p01b_container_evidence_tests.py` | `8b7cb511f4374a3689ef6ab8a5b0f80dfa6dedcbd3910dc6bd905fdd3f2df915` |
| 5 | `tools/hsai-formal-preflight/p01b_container_execution_tests.py` | `f483bedc4cf4767f194ece8f1c0ae9af2cd082317196b046f4b00b355d30f47a` |

## Exact 22-path source census

`ordered_source_paths` is exactly this sequence:

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

## Fixed bindings

The binding schema is `hsai-p01b-a3l6-audit-bindings-v1`.

| Binding | Value |
| --- | ---: |
| focused evidence tests | 32 |
| focused execution tests | 33 |
| focused tests | 65 |
| discovery census | 172 |
| ordinary JSON cap | 1,048,576 bytes |
| A3L6 gate JSON cap | 4,194,304 bytes |
| candidate payloads | 201 |
| candidate files | 202 |
| publication events | 271 |

The 172-test discovery row is Seatbelt-stubbed census coverage, not full-suite
semantics. The 4 MiB cap is a gate-artifact cap only.

## Binding and retained-run procedure

After committing this audit, produce canonical ASCII JSON with exactly these
fields: `schema`, `implementation_commit`, `implementation_tree`,
`audit_commit`, `ordered_source_paths`, `ordered_reviewed_file_sha256`,
`focused_evidence_test_count`, `focused_execution_test_count`,
`focused_test_count`, `discovery_test_count`, `ordinary_json_cap_bytes`,
`a3l6_gate_json_cap_bytes`, `candidate_payload_count`,
`candidate_file_count`, and `publication_event_count`.

Create a clean detached checkout at the audit commit. From that checkout, use
the existing local runner with a caller-owned mode-0700 non-repository parent
and an absent output child:

```sh
/usr/bin/python3 -B tools/hsai-formal-preflight/p01b_container_execution.py \
  a3l6-gate-v1 \
  --repository-root <detached-audit-checkout> \
  --expected-bindings <canonical-expected-bindings.json> \
  --output-root <mode-0700-parent>/a3l6-gate
```

The child must retain only `expected-bindings.json`, `gate-run.json`, and
`gate-run.sha256`. The required result is `pending-review`; `rejected` is
diagnosis only. Both outcomes retain `a3l6_accepted=false` and
`a3l7_authorized=false`.

## Review gate and nonclaims

The validators check canonical shape and digest correspondence. They cannot
establish reviewer identity, independence, or capability. A3L6 remains
unaccepted until two distinct human reviewers inspect this exact immutable
audit and retained pending-review run in order: security-capability first,
then correspondence-reproducibility.

That review gate may support only a separately authorized successor phase. It
does not itself authorize A3L7, A3L8, or A3L9.

This audit and its retained local output are not container execution,
target-backend replay, external evidence, accepted Evidence Ledger mutation,
benchmark submission, proof, production operation, production readiness, score
movement, reviewer authority, or authority to use Docker, registry, network,
credentials, or an endpoint.
