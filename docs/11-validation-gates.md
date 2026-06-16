# Validation Gates

## Current Level 1 Validation

The current Rust foundation must pass:

- file tree check,
- no JavaScript package manager files,
- no external adapter runtime code,
- all docs non-empty,
- README links every file,
- repo map classifies every named source,
- DSL schema has all required entities and examples,
- Rust module layout matches `crates/zkbench-core`,
- scoring rubric prevents overclaiming,
- semantic/oracle doc defines expected verdicts,
- replay manifest JSON round-trips,
- replay result JSON round-trips,
- evidence ledger digest chains validate,
- benchmark pack file digests validate,
- zk-Harness manifest JSON round-trips,
- zk-Harness dry-run plan JSON round-trips,
- zk-Harness dry-run plan execution policy is disabled,
- zk-Harness dry-run planned commands are inert,
- external-runner policy JSON round-trips,
- manual handoff bundle JSON round-trips,
- artifact capture contract JSON round-trips,
- provenance contract JSON round-trips,
- result import schema JSON round-trips,
- external result candidate rejection tests pass,
- quarantine manifest JSON round-trips,
- synthetic result candidate JSON imports parse,
- synthetic artifact digests validate against caller-provided local bytes,
- synthetic provenance contracts validate,
- synthetic metric candidate validation rejects missing sources and invalid numeric values,
- synthetic quarantine manifests remain `Level0DesignNote`,
- normalized synthetic result drafts remain pending review only,
- evidence append proposals remain not accepted evidence,
- proposal ledgers persist separately from `EvidenceLedger`,
- manual handoff bundles remain `Level0DesignNote`,
- result import candidates remain quarantined or pending review,
- no external backend command usage exists in the Rust core,
- no `std::process::Command` usage exists,
- no `Command::new` usage exists,
- no absolute paths in dry-run plans or fixtures,
- no live execution policy in fixtures,
- no fake metric values,
- no Level2+ actual evidence is produced by tests or fixtures,
- no external repo checkout,
- no fake benchmark results.

## Current Rust Commands

```sh
ROOT="/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os"
cd "$ROOT"
find "$ROOT" -type f | sort | sed "s#^$ROOT/##"
find "$ROOT" -type f \( -name "package.json" -o -name "pnpm-lock.yaml" -o -name "yarn.lock" -o -name "package-lock.json" -o -path "*/node_modules/*" \)
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo test --workspace --features external-runner
cargo doc --workspace --no-deps
grep -R "benchmark pass is not proof" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "recursion proof is not semantic proof" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "local replay is not official benchmark evidence" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "zk-Harness dry-run plans are not benchmark results" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "Manual handoff bundles are not benchmark results" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "Synthetic result candidates are not benchmark results" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "Evidence append proposals are not accepted evidence" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "Level1LocalReplay" "$ROOT/crates/zkbench-core" "$ROOT/docs" "$ROOT/README.md" || true
grep -R "unsound acceptance candidate" "$ROOT/crates/zkbench-core" "$ROOT/docs" "$ROOT/README.md" || true
grep -R "std::process::Command" "$ROOT/crates/zkbench-core/src" || true
grep -R "Command::new" "$ROOT/crates/zkbench-core/src" || true
grep -R "prover_time\|verifier_time\|proof_size\|memory_usage\|constraint_count" "$ROOT/crates/zkbench-core/tests/fixtures" || true
```

## Phase F Artifact Checks

The Rust tests currently cover:

- `ReplayManifest` deterministic JSON serialization and deserialization.
- `ReplayResult` deterministic JSON serialization and deserialization.
- `EvidenceLedger` append, save, load, digest-chain validation, summary counts, and Level2+ actual evidence rejection.
- `BenchmarkPackWriter` directory skeleton creation, README warnings, relative manifest paths, score report emission, and non-empty directory rejection.
- `BenchmarkPackReader` file digest validation and evidence ledger validation.
- Stable artifact digests and byte-identical local pack writes for identical inputs.

These checks are local integrity and reproducibility checks only. They do not establish official benchmark evidence, cross-backend reproduction, or formal evidence.

## Phase G Dry-Run Checks

The Rust tests currently cover:

- `ZkHarnessAdapterManifest` deterministic JSON serialization and deserialization.
- `ZkHarnessDryRunPlan` deterministic JSON serialization and deserialization.
- dry-run execution policy remains disabled.
- dry-run plan claim boundary remains `Level0DesignNote`.
- local pack evidence remains `Level1LocalReplay` and is not elevated.
- planned commands are inert serializable data.
- suspicious shell metacharacters and absolute paths are rejected.
- metric mappings contain no observed values.
- candidate family and mutation mappings preserve expected verdicts and source file digests.
- source scans for `std::process::Command` and `Command::new` remain empty.

These checks do not establish zk-Harness compatibility, external replay evidence, or performance evidence.

## Phase H External-Runner Boundary Checks

The Rust tests currently cover:

- `ExternalRunnerPolicy` deterministic JSON serialization and deserialization.
- default policy remains `Disabled` or `ManualHandoffOnly` and requires manual review.
- default policy requires artifact capture, provenance, result import validation, and claim-boundary review.
- claim policy rejects Level2+ actual evidence in Phase H.
- path policy rejects absolute paths.
- `ManualHandoffBundle` builds from a valid zk-Harness dry-run plan.
- manual handoff bundles remain `Level0DesignNote`.
- manual handoff bundles contain manual instructions only.
- artifact capture contracts distinguish expected future artifacts from captured artifacts.
- provenance contracts declare required provenance fields.
- result import schemas reject missing provenance, Level2+ claim requests, official benchmark claims, formal evidence claims, proof-system soundness claims, unknown units, absolute paths, and metric values without source artifact refs.
- rejected external result candidates can be converted into quarantine manifests.
- zk-Harness handoff mappings preserve dry-run plan id, source pack id, and source digests.
- source scans for `std::process::Command` and `Command::new` remain empty in Phase H modules.

These checks do not establish external replay evidence, official benchmark evidence, performance evidence, or formal evidence.

## Phase I Synthetic Result Import Checks

The Rust tests currently cover:

- valid synthetic JSON candidates import into normalized pending-review drafts,
- invalid synthetic JSON candidates import into quarantine bundles,
- artifact digest mismatches are rejected,
- unsupported digest algorithms are rejected,
- missing resolver lookups are rejected,
- missing provenance is rejected,
- forbidden provenance claim text is rejected,
- metric values without source artifact refs are rejected,
- unknown metric units are rejected,
- negative numeric metric candidates are rejected,
- evidence append proposals validate and remain not accepted evidence,
- proposal ledgers append, persist, round-trip, and detect tampering,
- proposal ledger entries remain separate from `EvidenceLedger`,
- Phase I artifacts remain `Level0DesignNote`,
- source scans for `std::process::Command` and `Command::new` remain empty.

These checks do not establish real external result import, live zk-Harness execution, official benchmark evidence, performance evidence, or formal evidence.

## Phase J Reviewed Proposal Acceptance Policy Checks

The Rust tests currently cover:

- `EvidenceAcceptancePolicy` deterministic JSON serialization and deserialization.
- reviewed append proposals create `EvidenceRecordCandidate` metadata only after human review.
- escalation guard blocks Level2+ candidate targets and Level0 to Level1 without explicit local-only policy.
- automated reviewer roles cannot approve candidate creation.
- evidence-record candidates remain not accepted evidence and do not mutate `EvidenceLedger`.
- acceptance policy validation rejects Level2+ actual evidence classes.
- source scans for `std::process::Command` and `Command::new` remain empty in Phase J modules.

These checks do not establish accepted external evidence, official benchmark evidence, performance evidence, or formal evidence.

## Phase K gnark Recursion Adapter Checks

The Rust tests currently cover:

- `GnarkRecursionAdapterManifest` deterministic JSON serialization and deserialization.
- default manifest remains envelope-planning-only with external execution disabled.
- `GnarkRecursionEnvelopePlan` deterministic JSON serialization and deserialization.
- envelope plans remain `Level0DesignNote` and do not emit evidence records.
- planned commands are inert serializable data scoped to `recursive_loop_envelope`.
- validation rejects future live execution policies and absolute fixture paths.
- metric schema entries remain label-only with no observed values.
- source scans for `std::process::Command` and `Command::new` remain empty in Phase K modules.

These checks do not establish gnark compatibility, external replay evidence, performance evidence, or formal evidence.

## Phase L Narrow zkML Adapter Checks

The Rust tests currently cover:

- `ZkmlNarrowAdapterManifest` deterministic JSON serialization and deserialization.
- default manifest remains workload-planning-only with external execution disabled.
- `ZkmlNarrowWorkloadPlan` deterministic JSON serialization and deserialization.
- workload plans remain `Level0DesignNote` and do not emit evidence records.
- planned commands are inert serializable data scoped to `zkml_control_flow_mixed`.
- validation rejects future live execution policies and absolute fixture paths.
- public/private boundary and observation-omission mutation classes are in scope.
- metric schema entries remain label-only with no observed values.
- source scans for `std::process::Command` and `Command::new` remain empty in narrow zkML modules.

These checks do not establish zkML compatibility, external replay evidence, performance evidence, or formal evidence.

## Phase M Reproducible Benchmark Pack Checks

The Rust tests currently cover:

- `attach_reproduction_bundle_to_pack()` writing three inert external replay plans and reproduction metadata.
- reproduction attach rejection when metadata is already present.
- reproduction metadata load and JSON round-trip through `BenchmarkPackReader`.
- pack manifest claim boundary remains `Level1LocalReplay` after reproduction attach.
- reproduction metadata and Level2 eligibility reports remain `Level0DesignNote`.
- Level2 eligibility remains blocked without reviewed external artifacts.
- extended pack validation passes after reproduction attach.

These checks do not establish Level2 evidence, official benchmark evidence, cross-backend reproduction, performance evidence, or formal evidence.

## Phase L Local Soak Checks

The Rust tests currently cover:

- `SoakPlan` and `SoakConfig` deterministic JSON serialization and deserialization.
- `run_local_soak()` writes benchmark packs for all implemented family kinds and explicit seeds.
- identical soak inputs produce byte-identical pack artifacts and soak execution reports.
- soak execution reports remain `Level0DesignNote`.
- soak benchmark packs remain `Level1LocalReplay`.
- `ReportBundleReviewPlan` sampled review passes for soak-produced packs.
- report-bundle review checks digest validation, README warnings, conservative score reports, and ledger evidence-record alignment.
- report-bundle review reports remain `Level0DesignNote`.
- source scans for `std::process::Command` and `Command::new` remain empty in Phase L modules.
- `run_soak_campaign()` quick presets exercise all three implemented families with all three mutation passes.
- campaign artifacts write sampled per-pack review reports and archive failure packs under `.context/phase-l-artifacts/`.
- regression corpus curation appends failure and skipped-mutation entries without mutating accepted evidence.

These checks do not establish official benchmark evidence, cross-backend reproduction, performance evidence, or formal evidence.

## Future Gate Ladder

When package scripts exist in a later phase, preserve:

- `pnpm run lint` as the heavy gate.
- `lint:fast` for lightweight formatting/static checks.
- `test:focused` for narrow unit/integration tests.
- `verify:contracts` for schema, manifest, adapter, and evidence contracts.
- `verify:full` for the heavy local verification ladder.

## Gate Meanings

| Gate | Meaning |
|---|---|
| `lint:fast` | Fast syntax/style/metadata checks. |
| `test:focused` | Targeted tests for the state slice. |
| `verify:contracts` | Schema, evidence, manifest, and adapter contract validation. |
| `verify:full` | Full local verification. |
| `pnpm run lint` | Heavy root gate delegating to full verification. |

## Docs-Only Commands

These commands are retained for historical Level 0 scaffold checks. They are superseded by the current Rust commands above.

```sh
ROOT="/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os"
find "$ROOT" -type f | sort
find "$ROOT" -type f | sort | sed "s#^$ROOT/##"
find "$ROOT" -type f \( -name "Cargo.toml" -o -name "package.json" -o -name "pnpm-lock.yaml" -o -name "yarn.lock" -o -name "package-lock.json" -o -name "*.rs" -o -name "*.ts" -o -name "*.js" -o -name "Makefile" \)
find "$ROOT" -type f -empty
grep -R "benchmark pass is not proof" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "recursion proof is not semantic proof" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "local replay is not official benchmark evidence" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
```

## Promotion Rules

- Level 0 docs can guide implementation but cannot justify benchmark claims.
- Level 1 local replay requires replay artifacts.
- Level 2 reproducible benchmark artifact requires deterministic replay and artifacts.
- Level 3 cross-backend evidence requires at least two independently normalized backend outcomes.
- Level 4 formal statement is not a proof.
- Level 5 machine-checked proof must name the scoped property.
- Level 6 independently reproduced evidence requires external reproduction.

## No Fake Results

Do not create benchmark numbers in documentation. Use `pending`, `not_run`, or `future evidence required` when evidence is absent.
