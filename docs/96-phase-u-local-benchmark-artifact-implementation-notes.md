# Phase U Local Benchmark Artifact Implementation Notes

Status: implemented for local filesystem artifact packaging only.

This phase implements the local benchmark artifact boundary from
`docs/95-phase-u-local-benchmark-artifact-boundary-spec.md`. It creates a Rust
API for manifest validation, deterministic Markdown rendering, digest-covered
declared-file output roots, and read-back validation. It does not create a
committed artifact bundle, submit an official benchmark, execute external
replay, mutate an accepted Evidence Ledger, populate score axes, claim ZK
backend performance, or create Level2+ evidence.

## State Slice

This implementation is limited to:

- `crates/zkbench-core/src/local_benchmark_artifact.rs`
- `crates/zkbench-core/src/lib.rs`
- `crates/zkbench-core/src/prelude.rs`
- `crates/zkbench-core/tests/phase_u_local_benchmark_artifact.rs`
- `docs/96-phase-u-local-benchmark-artifact-implementation-notes.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`
- `docs/90-whole-codebase-validation-report.md`

No package runtime file, command-line surface, UI artifact, committed generated
benchmark artifact, official benchmark submission, external result import, or
accepted Evidence Ledger mutation is added by this phase.

## Public Surface

The implementation adds:

- `LocalBenchmarkArtifactManifest`;
- `LocalBenchmarkArtifactInputRef`;
- `LocalBenchmarkArtifactInputKind`;
- `LocalBenchmarkArtifactValidation`;
- `LocalBenchmarkArtifactOutput`;
- `required_local_benchmark_artifact_limitations`;
- `validate_local_benchmark_artifact_manifest`;
- `serialize_local_benchmark_artifact_manifest_json`;
- `deserialize_local_benchmark_artifact_manifest_json`;
- `compute_local_benchmark_artifact_manifest_digest`;
- `render_local_benchmark_artifact_markdown`;
- `write_local_benchmark_artifact_outputs`;
- `read_local_benchmark_artifact_outputs`.

The manifest requires at least one local benchmark-pack manifest input and
accepts only portable local artifact references. Inputs and outputs are capped
at `Level1LocalReplay` or below, and the output claim boundary cannot exceed
the weakest supplied local input boundary.

## Materialized Output Shape

`write_local_benchmark_artifact_outputs` writes exactly four declared files
below the caller-selected output root:

```text
local-benchmark-artifact-manifest.json
rendered/local-benchmark-artifact.md
digests/local-benchmark-artifact-manifest-json.sha256
digests/local-benchmark-artifact-markdown.sha256
```

The digest sidecars bind the exact materialized JSON and Markdown bytes.
`read_local_benchmark_artifact_outputs` rejects stale sidecars, Markdown drift,
missing files, unexpected files, symlinks, invalid manifests, and protected-path
overlap, including symlink-resolved overlap.

## Safety Behavior

The writer rejects non-empty output roots unless explicit overwrite is set.
Explicit overwrite is not a repair path: an existing root must already be a
complete, digest-consistent bundle for the same manifest before it can be
rewritten.

Protected paths are rejected before writes when the output root is equal to,
nested under, or a parent of any protected input path. Relative and absolute
path normalization is used for overlap checks. Existing path prefixes are also
resolved before comparison, so a caller-owned-looking path cannot resolve
through a symlink into a protected source, audit-index, or evidence location.

## Required Limitation Labels

Every valid manifest must include:

- Local benchmark artifacts are not official benchmark evidence.
- Local benchmark artifacts are not accepted Evidence Ledger entries.
- Local benchmark artifacts do not create Level2+ evidence.
- Local benchmark artifacts do not prove ZK backend performance.
- Local benchmark artifacts do not prove semantic correctness.
- Local replay artifacts are not official benchmark evidence.
- Internal timing telemetry is not ZK backend performance.
- Score axes remain unpopulated for local-only evidence.
- Acceptance requires a separate reviewed promotion phase.

## Validation

The focused test file covers:

- manifest JSON round trip and deterministic digesting;
- Markdown rendering with required limitation labels;
- claim-elevation rejection;
- unsafe artifact-reference rejection;
- declared-file-only write/read behavior;
- non-overwrite rejection;
- repair-overwrite rejection;
- stale digest rejection;
- protected-path overlap rejection;
- symlink-resolved protected-path overlap rejection;
- partial-bundle rejection;
- unexpected-file rejection;
- symlink rejection;
- source scan for process/network/package/runtime and claim-elevation strings.

This is local regression evidence only. It is not a generated official
benchmark artifact and not accepted evidence.
