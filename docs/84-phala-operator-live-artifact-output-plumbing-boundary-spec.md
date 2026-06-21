# Phala Operator Live Artifact Output Plumbing Boundary Spec

## Status And Claim Boundary

This is a docs-first boundary for future materialized output plumbing around the
operator-only Phala/dstack live managed-verifier artifact bundle. It authorizes
no Rust implementation, no filesystem writes, no examples, no scripts, no
package runtime files, no network access, no live Phala API calls, no
credentials, no operator live tests, no generated operator artifacts, and no
claims above `Attested` in this slice.

The already implemented Phase 83 surface validates in-memory logical
`operator-live/*` files. The next missing boundary is the local file-system
contract for a later code phase that may write and read those logical files
under an operator-selected output root without treating those files as proof,
benchmark evidence, local Intel DCAP verification, live provider evidence, or
global software-agent uniqueness.

## State Slice

This docs-first phase may touch only:

```text
docs/84-phala-operator-live-artifact-output-plumbing-boundary-spec.md
docs/12-task-list.md
README.md
AGENTS.md
```

It must not touch Rust source, Cargo metadata, `Cargo.lock`, fixtures, accepted
Evidence Ledgers, benchmark packs, report bundles, audit indexes, generated
artifacts, package runtime files, examples, scripts, or operator secrets.

## Purpose

Define the future file-system output contract before any implementation writes,
reads, overwrites, or validates materialized operator-live artifact files.

The future output plumbing may materialize only the declared Phase 83 logical
files:

```text
operator-live/request.json
operator-live/normalized-response.json
operator-live/trust-roots.json
operator-live/redaction-report.json
operator-live/audit.json
operator-live/raw-response.sha256
```

The future path must remain local, caller-selected, and outside normal live
provider behavior. Output plumbing may persist or read artifacts that a caller
already supplies, but it must not perform provider HTTP, load credentials, or
trigger a live Phala verifier call unless a later separate phase explicitly
authorizes that runtime path.

## Future Output Root Rules

A later implementation must require a caller-selected output root and reject:

- empty output roots;
- repository root as output root;
- paths outside the caller-selected root;
- absolute paths inside bundle metadata;
- `.` or `..` path segments inside bundle metadata;
- backslash-separated logical paths;
- symlinks at the output root or any bundle path;
- non-directory output roots;
- unexpected pre-existing files unless overwrite mode is explicit;
- hidden sidecar files not declared by the bundle contract.

The output root must be treated as local operator artifact storage, not as a
trust root. Its path must never appear in verifier trust roots.

## Future Write Policy

A future writer may write only the declared files. It must:

- create the `operator-live/` directory only under the caller-selected output
  root;
- write files atomically or fail before publishing a partial bundle;
- refuse unexpected existing files by default;
- require explicit overwrite mode for replacing an existing bundle;
- reject symlinks before and after writing;
- recompute and validate all digests after writing;
- reject any bundle whose in-memory validation fails;
- never write raw provider response bodies by default;
- write only `raw-response.sha256` unless a later explicit phase broadens raw
  response retention.

Overwrite mode must be local and explicit. It must not be implied by default
constructor values or environment variables.

## Future Read Policy

A future reader may read only the declared files. It must:

- reject missing required files;
- reject undeclared extra files;
- reject symlinks;
- reject stale digest sidecars;
- reject invalid JSON;
- reject invalid UTF-8 in `raw-response.sha256`;
- pass the parsed in-memory bundle through the Phase 83 validator before
  returning validated metadata.

A rejected read must emit diagnostics only. It must not emit trust roots,
guarantees, accepted Evidence Ledger entries, benchmark outputs, or Phase 4
registry mutations.

## Future Raw Response Retention Policy

Raw response body retention remains forbidden by default. A future output
plumbing phase may store only `raw-response.sha256`.

If raw response retention is ever proposed, a separate reviewed phase must
define:

- the exact file name;
- redaction order;
- maximum size;
- forbidden secret patterns;
- retention toggle;
- validation behavior when the raw body is absent;
- reason the raw body is safe to commit or must remain ignored.

This Phase 84 boundary does not authorize raw response body retention.

## Future Code Touch Surface

A later implementation phase may be limited to:

```text
crates/hsai-attestation-phala/src/lib.rs
crates/hsai-attestation-phala/tests/
docs/<future-phase-notes>.md
README.md
AGENTS.md
```

A future implementation may broaden that list only if its own state slice names
the additional files explicitly. It must not change Cargo metadata or
`Cargo.lock` unless a later phase explicitly authorizes new dependencies.

## Required Future Tests

A future implementation phase must include hermetic tests for:

- writing a valid materialized bundle under a temporary caller-owned root;
- reading the same bundle back into the Phase 83 validator;
- rejecting repository root as output root;
- rejecting path traversal;
- rejecting symlink output roots;
- rejecting symlink bundle files;
- rejecting unexpected existing files without overwrite mode;
- rejecting partial bundles;
- rejecting undeclared extra files;
- rejecting stale digest materialization;
- rejecting raw response body retention by default;
- preserving `Attested`-only claim limits;
- normal workspace tests requiring no live credentials and no network.

Any future test that performs a live provider call must be ignored,
feature-gated, or otherwise excluded from normal workspace gates, and must be
authorized by a separate state slice.

## Forbidden In This Slice

- Rust source changes.
- Cargo metadata changes.
- `Cargo.lock` changes.
- Filesystem write/read implementation.
- Examples or scripts.
- Package runtime files.
- Network access.
- Live Phala API calls.
- Operator live tests.
- Credential handling code.
- Secret fixtures.
- Generated operator artifacts.
- Raw response body retention.
- Local Intel DCAP quote verification code.
- PCCS or collateral fetch/caching code.
- Generic JWKS/JWT fetch code.
- TLS or attested-TLS implementation.
- Deployment orchestration.
- External repo clones or vendored source.
- Backend execution.
- Benchmark outputs.
- External result import.
- Accepted Evidence Ledger mutation.
- Phase 4 anchor-registry semantic changes.
- Level2+ evidence.
- Claims above `Attested`.

## Acceptance Criteria For This Slice

- This spec exists and names the future output-plumbing boundary.
- README navigation links this spec.
- `docs/12-task-list.md` records this docs-first boundary.
- `AGENTS.md` authorizes only this Markdown planning slice.
- Validation confirms no Rust source, Cargo metadata, package runtime, fixture,
  generated artifact, benchmark output, or accepted Evidence Ledger changed.

## Future Implementation Exit Criteria

A later implementation phase may complete only when:

- output-root validation is explicit;
- symlink and path-traversal checks fail closed;
- write and read behavior reuse the Phase 83 in-memory validator;
- unexpected files and partial bundles fail closed;
- overwrite mode is explicit;
- raw response body retention remains absent unless separately authorized;
- normal workspace tests require no live credentials and no network;
- successful validation remains capped at `Attested`;
- docs state all non-claims.
