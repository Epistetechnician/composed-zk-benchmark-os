# Phase F Local Replay And Evidence Ledger Notes

## Implemented

Phase F adds local artifact and replay persistence to `zkbench-core`.

Implemented concepts:

- `LocalJsonAdapter`
- `ReplayManifest`
- `ReplayResult`
- deterministic replay JSON serialization
- deterministic artifact digests with SHA-256
- persistent `EvidenceLedger`
- local benchmark pack skeleton
- conservative local `ScoreReport` emission
- reproducibility tests for deterministic local artifacts

This is still Level1LocalReplay at most. A benchmark pass is not proof. Local replay is not official benchmark evidence. A recursion proof is not semantic proof.

## Local JSON Adapter Behavior

`LocalJsonAdapter` is the first concrete adapter, but it is not a real ZK backend adapter. It consumes embedded local generated or mutated benchmark subjects from a `ReplayManifest`, evaluates selected traces with the local oracle, and emits `ReplayResult` values.

Capability flags are conservative. The adapter supports local execution, negative tests, trace export, replay manifests, and artifact hashing. It does not claim proving, verification timing, constraint counts, formal semantics, machine-checked proof, recursion support, or zkML metrics.

Local oracle acceptance maps to `BackendOutcome::Accepted` only inside the local replay context. Local oracle rejection maps to `BackendOutcome::Rejected` only inside the local replay context. Local semantic acceptance is not proof-system acceptance.

`ReplayMode::MockOutcome` exists for classification tests only.

## Replay Manifest Summary

`ReplayManifest` serializes to deterministic pretty JSON and includes:

- manifest id
- schema version `phase-f-local-replay-v0`
- replay mode
- subject kind
- generated or mutated instance ids
- embedded generated or mutated local subject
- family kind when applicable
- generator provenance when applicable
- mutation provenance when applicable
- selected traces
- expected outcomes
- local target id
- adapter id
- adapter capability set
- claim boundary
- input artifact references
- expected output artifact roles
- non-shell replay commands
- notes

The manifest does not store absolute filesystem paths for pack artifacts and does not include wall-clock timestamps.

## Replay Result Summary

`ReplayResult` serializes to deterministic pretty JSON and includes:

- replay result id
- manifest id
- adapter id
- replay mode
- replay status
- failure mode
- per-trace replay results
- local oracle outcomes
- backend outcome representation in local context
- result classification
- evidence records
- claim boundary
- artifact references
- provenance
- notes

Expected reject plus accepted is an unsound acceptance candidate, not a proven exploit. Expected accept plus rejected is a false rejection candidate, not automatically a backend bug.

## Evidence Ledger Behavior

`EvidenceLedger` persists as pretty JSON with version, entries, summary, and notes.

Each entry records:

- sequence number
- evidence record
- previous digest
- entry digest
- notes

The digest chain is computed from sequence number, previous digest, and canonical evidence record JSON. Ledger validation recomputes the chain and verifies summary counts. This is a local integrity check only. It is not tamper-proof, not a Merkle proof, and not independent reproduction.

Actual Phase F entries are rejected when their claim boundary exceeds `Level1LocalReplay`.

## Artifact Digest Behavior

`ArtifactDigest` uses `ArtifactDigestAlgorithm::Sha256` over deterministic local bytes. It records the lowercase hex digest, byte length, optional artifact kind, and optional artifact role.

Pack file digests are computed over bytes as written, not over reserialized guesses. The implementation avoids wall-clock timestamps and non-deterministic hashing for local artifacts.

## Benchmark Pack Skeleton Layout

The implemented pack layout is:

```text
<pack-root>/
  pack.json
  README.md
  specs/
    generated_instance.json
    mutated_instances/
      <mutation-id>.json
  replay/
    manifests/
      <manifest-id>.json
    results/
      <result-id>.json
  evidence/
    ledger.json
  reports/
    score_report.json
```

`BenchmarkPackWriter` writes local JSON artifacts, computes file digests, writes conservative README warnings, writes a conservative score report, and refuses non-empty directories unless `overwrite(true)` is set.

`BenchmarkPackReader` reads `pack.json`, verifies required files, validates file digests, loads the evidence ledger, and validates the ledger digest chain.

The pack manifest uses relative paths only and excludes its own digest to avoid circular hashing.

## Deterministic Reproducibility Guarantees

Given identical generated instances, mutation variants, replay manifests, replay results, and ledgers, Phase F writes byte-identical local pack files in separate directories.

This guarantee is local and structural. It is not Level2 official benchmark evidence because no external backend has been invoked and no independently replayable benchmark result has been produced.

## Claim Boundary Status

Produced artifacts remain `Level1LocalReplay` or lower:

- `ReplayManifest`
- `ReplayResult`
- `EvidenceRecord`
- `EvidenceLedgerEntry`
- `BenchmarkPackManifest`
- local `ScoreReport`

Local replay artifacts are not official benchmark evidence. Local oracle acceptance is semantic-local only. Unsound acceptance candidate is not a proven exploit.

## Deliberately Unimplemented

Still not implemented:

- zk-Harness integration
- clean, zkLean, Garden, gnark, or zkML integration
- external backend execution
- external process commands for benchmarking
- generated official benchmark result files
- fake prover time
- fake verifier latency
- fake proof size
- fake memory use
- fake constraint count
- formal evidence
- dashboards

## Next Recommended Slice

Phase G should be a careful zk-Harness adapter preparation slice, not a full benchmark-claiming integration.

Implement:

- zk-Harness adapter manifest design
- dry-run command generation only
- external-run disabled by default
- mapping from local benchmark packs to zk-Harness-compatible replay plans

Do not run live zk-Harness benchmark execution until the dry-run adapter contract is reviewed and the local benchmark pack format is stable. Do not claim official performance numbers or Level2+ evidence in the preparation slice.
