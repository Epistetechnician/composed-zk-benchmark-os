# Phase 796-A3L6A3: P01B Final Immutable-Gate Audit

Named state slice:
`phase-796a3l6a3-p01b-final-immutable-gate-audit`.

## Clean baseline

This audit binds the clean corrected implementation commit
`b2f10b85975f24467d5dda067f0125009ca9a1c9` and tree
`48dc6d6ec7eb981d66c998359e00a44604634fdc`. The latest correction retains all
host-focused A3L9 absolute-traversal coverage, while the existing nested
Seatbelt marker runs only the test's applicable CLI and malformed-argv checks.
The Seatbelt profile and runner are unchanged.

The preceding retained attempts remain rejected diagnostics. They are not
relabeled or promoted. The dirty primary checkout remains excluded: its active
P01B edits are A3L7-adjacent, and its admission and `docs/agents/` work is
unrelated.

This document cannot name its own audit commit before it is committed. After
commit, canonical expected-bindings JSON must use the resulting immutable audit
identifier before the detached runner is invoked.

## Five reviewed blobs

| Order | Path | SHA-256 |
| --- | --- | --- |
| 1 | `tools/hsai-formal-preflight/p01b_container_probe.py` | `75435eabfd7bfae0ddc568251f039b1e96689167ef0cf3dd91df9a0216985a28` |
| 2 | `tools/hsai-formal-preflight/p01b_container_evidence.py` | `3f0fdcac91abffed9f36150cd420bb9f62859c135969042b1caf3d724daecec8` |
| 3 | `tools/hsai-formal-preflight/p01b_container_execution.py` | `38cca3f665232ccf56499bbb32354d9e43529e7746c5f0b97002e70b71c74e6f` |
| 4 | `tools/hsai-formal-preflight/p01b_container_evidence_tests.py` | `8b7cb511f4374a3689ef6ab8a5b0f80dfa6dedcbd3910dc6bd905fdd3f2df915` |
| 5 | `tools/hsai-formal-preflight/p01b_container_execution_tests.py` | `6b16eedf5c01370296ef7d48872f360ffacc5925f6132539398cfafdf85503d2` |

## Exact 22-path census

`ordered_source_paths` is exactly:

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

## Fixed binding values

The canonical schema is `hsai-p01b-a3l6-audit-bindings-v1`.

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

The discovery count is Seatbelt-stubbed census coverage, not full-suite
semantics. The 4 MiB value is a gate-artifact cap only.

## Retained detached procedure

The binding must contain exactly: `schema`, `implementation_commit`,
`implementation_tree`, `audit_commit`, `ordered_source_paths`,
`ordered_reviewed_file_sha256`, `focused_evidence_test_count`,
`focused_execution_test_count`, `focused_test_count`, `discovery_test_count`,
`ordinary_json_cap_bytes`, `a3l6_gate_json_cap_bytes`,
`candidate_payload_count`, `candidate_file_count`, and
`publication_event_count`.

From a clean detached checkout at the audit commit, run:

```sh
/usr/bin/python3 -B tools/hsai-formal-preflight/p01b_container_execution.py \
  a3l6-gate-v1 \
  --repository-root <detached-audit-checkout> \
  --expected-bindings <canonical-expected-bindings.json> \
  --output-root <mode-0700-non-repository-parent>/a3l6-gate
```

The output child must retain only `expected-bindings.json`, `gate-run.json`,
and `gate-run.sha256`. The required result is `pending-review`; `rejected` is
diagnosis only. Both outcomes retain `a3l6_accepted=false` and
`a3l7_authorized=false`.

## Review gate and nonclaims

Validators check shape and digest correspondence only. They do not prove
reviewer identity, independence, or capability. A3L6 remains unaccepted until
two distinct human reviewers inspect this exact audit and pending-review run in
security-capability then correspondence-reproducibility order.

Those reviews may support only a separately authorized successor phase. They do
not themselves authorize A3L7, A3L8, or A3L9.

This audit and retained local output are not container execution, target-backend
replay, external evidence, accepted Evidence Ledger mutation, benchmark
submission, proof, production operation, production readiness, score movement,
or authority to use Docker, registry, network, credentials, or an endpoint.
