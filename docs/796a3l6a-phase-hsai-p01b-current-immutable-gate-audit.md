# Phase 796-A3L6A: P01B Current Immutable-Gate Audit

Named state slice:
`phase-796a3l6a-p01b-current-immutable-gate-audit`.

## Purpose and scope

This audit freezes the completed A3L6R local implementation at implementation
commit `07ec1e0a916ebbed5c3ab0bc14fb9c0b33663662` and implementation tree
`d3bd81794eb1e68ec2e6c1b2df2fb66cbac0699a`. It is an audit-only documentation
slice. It does not merge the mutable primary checkout, revise the five reviewed
implementation blobs, execute a container, or accept A3L6.

The audit commit is deliberately not written into this document before it
exists. After this document is committed, the canonical expected-bindings JSON
is generated with the resulting immutable audit commit. That JSON is then the
input to a retained detached-checkout gate run. This ordering prevents a
self-referential audit identifier.

The primary checkout was dirty at audit start. Its P01B edits altered the
closed execution environment and candidate payload preparation for later
retained-runtime readiness. They are excluded from this audit because that
would mix A3L7-adjacent work into an A3L6-only baseline. Its unrelated
admission and `docs/agents/` work is also excluded. The audit baseline is the
clean implementation commit named above, not a claim about the dirty primary
tree.

## Reviewed implementation blobs

The canonical expected-bindings document uses this order and these SHA-256
values. A mismatch is a rejected gate outcome.

| Order | Path | SHA-256 |
| --- | --- | --- |
| 1 | `tools/hsai-formal-preflight/p01b_container_probe.py` | `75435eabfd7bfae0ddc568251f039b1e96689167ef0cf3dd91df9a0216985a28` |
| 2 | `tools/hsai-formal-preflight/p01b_container_evidence.py` | `3f0fdcac91abffed9f36150cd420bb9f62859c135969042b1caf3d724daecec8` |
| 3 | `tools/hsai-formal-preflight/p01b_container_execution.py` | `38cca3f665232ccf56499bbb32354d9e43529e7746c5f0b97002e70b71c74e6f` |
| 4 | `tools/hsai-formal-preflight/p01b_container_evidence_tests.py` | `8b7cb511f4374a3689ef6ab8a5b0f80dfa6dedcbd3910dc6bd905fdd3f2df915` |
| 5 | `tools/hsai-formal-preflight/p01b_container_execution_tests.py` | `c25e1757dd1d95f26076229f1c03cc3dc10ec936b351610100fec12f2952d680` |

## Exact 22-path source census

The following ordered paths are the retained `ordered_source_paths` value. The
census describes static gate materialization, not a container or target-backend
run.

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

## Bound values

The canonical expected-bindings document has schema
`hsai-p01b-a3l6-audit-bindings-v1` and binds all of the following values:

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

The discovery row is Seatbelt-stubbed census coverage. It is not a full-suite
semantic claim. The 4 MiB value applies to the A3L6 gate artifact; it does not
broaden any retained-runtime authority.

## Canonical binding and retained-run procedure

After this audit is committed, generate canonical JSON with exactly these
fields: `schema`, `implementation_commit`, `implementation_tree`,
`audit_commit`, `ordered_source_paths`, `ordered_reviewed_file_sha256`,
`focused_evidence_test_count`, `focused_execution_test_count`,
`focused_test_count`, `discovery_test_count`, `ordinary_json_cap_bytes`,
`a3l6_gate_json_cap_bytes`, `candidate_payload_count`,
`candidate_file_count`, and `publication_event_count`.

Create a clean detached checkout at the resulting `audit_commit`. From that
checkout, invoke the existing runner with a caller-owned, mode-0700,
non-repository parent and an absent output child:

```sh
/usr/bin/python3 -B tools/hsai-formal-preflight/p01b_container_execution.py \
  a3l6-gate-v1 \
  --repository-root <detached-audit-checkout> \
  --expected-bindings <canonical-expected-bindings.json> \
  --output-root <mode-0700-parent>/a3l6-gate
```

The retained output must contain only `expected-bindings.json`, `gate-run.json`,
and `gate-run.sha256`. A valid result is `pending-review`; `rejected` is
diagnostic only. Either result fixes `a3l6_accepted=false` and
`a3l7_authorized=false`.

## Independent review and successor boundary

JSON validation proves schema and digest correspondence only. It cannot prove
reviewer identity, independence, or capability. A3L6 remains unaccepted until
two distinct human reviewers independently assess this exact immutable audit
and retained pending-review run, in this order:

1. security-capability;
2. correspondence-reproducibility.

Only those genuine review records, together with the retained pending-review
record, can support a separately authorized next phase. They do not authorize
A3L7 themselves. A3L7, A3L8, and A3L9 remain distinct retained-runtime and
publication phases.

## Nonclaims

This audit and its retained local output are not container execution, target
backend replay, external evidence, accepted Evidence Ledger mutation, benchmark
submission, proof, production operation, production readiness, score movement,
or authority to use Docker, a registry, network, credentials, or an endpoint.
They create no reviewer identity and no A3L7 authorization.
