# Phase 796-A3L6R HSAI P01B Immutable-Gate Rebase And Retention Implementation

## Status

Complete as a bounded local implementation. A3L6 remains unaccepted; A3L7,
A3L8, and A3L9 remain prohibited.

State slice:
`phase-796a3l6r-p01b-immutable-gate-rebase-retention-implementation`.

This implementation prepares a reproducible local A3L6 gate record. It does
not create a review acceptance, evidence promotion, external benchmark result,
production operation, or authority grant.

## Implemented Contract

The five-file A3L6 surface now defines two pure-data records:

- `hsai-p01b-a3l6-audit-bindings-v1`, a static pre-run cross-binding document.
- `hsai-p01b-a3l6-gate-run-record-v1`, a retained local run outcome.

The static document binds the current 22 ordered source paths, five reviewed
blob SHA-256 values, implementation/tree/audit Git identities, 32 evidence
tests, 33 execution tests, 65 combined focused tests, the 172 discovery
census, 1 MiB ordinary JSON cap, 4 MiB A3L6 cap, and 201/202/271 candidate and
publication cardinalities. It is canonical ASCII JSON, duplicate-key-free, and
required before materialization begins.

The run record has exactly two results:

- `pending-review`: the three existing hermetic gate rows completed and the
  static bindings match. It carries the existing plan, source manifest, Python
  observation, and gate observations, but no review records and no A3L6
  acceptance.
- `rejected`: binding, capture, execution, or record construction failed. It
  retains a bounded reason and compact observations already obtained before
  failure. Each retained command row includes its role, direct argv,
  replacement environment, executable identity, exit or signal outcome,
  truncation facts, retained stream bytes/digests, and observed-stream digest.

Both outcomes fix `a3l6_accepted=false`, `a3l7_authorized=false`, and
`evidence_level=Level1LocalReplayOrLower`. The discovery result is explicitly
`seatbelt-stubbed-census-not-full-suite-semantics`.

## Local Operator Entry Point

The new local-only entry point is:

```text
/usr/bin/python3 -B tools/hsai-formal-preflight/p01b_container_execution.py \
  a3l6-gate-v1 \
  --repository-root <clean-detached-audit-checkout> \
  --expected-bindings <absolute-audit-bindings.json> \
  --output-root <absolute-new-a3l6-gate-directory>
```

The argument order is fixed. The binding document supplies the implementation
commit, implementation tree, and audit commit; the caller cannot substitute
those values through CLI flags. The checkout must have `HEAD` equal to the
binding's audit commit, and the exact reviewed source paths and their ancestors
must be unchanged before and after the gate. The repository path and every
output-path component are opened without following symlinks.

`--output-root` is the exact new final `a3l6-gate` directory, not a general
artifact parent. Its parent must be caller-owned mode `0700`; every traversed
component must be a real directory, the root must not overlap the repository,
and the target must be absent. The runner writes a sibling staging directory,
fsyncs it, then atomically renames it after writing exactly:

```text
expected-bindings.json
gate-run.json
gate-run.sha256
```

The output is reopened through no-follow descriptors and its post-rename
directory identity must match the still-open staging descriptor. Symlinked
ancestors, repository overlap, preexisting targets, partial output, unexpected
output, and digest drift fail closed. If post-rename readback fails, the runner
removes only the known files through the held staging descriptor and removes the
final name only when it still resolves to that same directory identity. Temporary
`/private/tmp/hsai-p01b-gate-*` materialization is removed only after retained
output is verified or a write failure is surfaced.

The route invokes only the existing Git/Python/Seatbelt gate rows. It does not
invoke Docker, a registry, a socket, a container, a network endpoint, a
backend, an Evidence Ledger operation, review construction, bundle assembly,
or A3L7/A3L8/A3L9 execution.

## Validation

The implementation preserves the frozen focused census:

```text
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B \
  tools/hsai-formal-preflight/p01b_container_evidence_tests.py -v    PASS (32)
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B \
  tools/hsai-formal-preflight/p01b_container_execution_tests.py -v   PASS (33)
```

The execution suite covers canonical static binding validation, rejected
retention with bounded command diagnostics, missing/reordered CLI input,
repository and symlink output-root rejection, preexisting output rejection,
digest-sidecar readback, and a real hermetic fixture gate that reaches only
`pending-review`.

## Remaining Gates

This code is not an A3L6 acceptance. A separate immutable audit must bind this
implementation commit/tree and the exact five reviewed blobs. A retained
`pending-review` record must then be produced from the clean detached audit
checkout. Two genuine, distinct reviewers must independently assess the exact
audit state and retained record. Their external review process cannot be
self-generated by this runner.

No result from this phase authorizes production operation, external benchmark
submission, evidence promotion, score movement, Level2+ evidence, semantic
correctness, proof, SOTA, breakthrough, full security, or external-audit
claims.
