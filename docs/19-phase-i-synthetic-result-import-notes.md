# Phase I Synthetic Result Import Notes

Phase I adds a local/synthetic result import prototype to `zkbench-core`.

## Implemented

- JSON parsing for synthetic `ExternalResultCandidate` values.
- `SyntheticResultImporter` and `SyntheticResultImportBundle`.
- `ResultCandidateArtifactResolver` for explicit caller-provided local bytes or declared relative files.
- Artifact digest validation for synthetic artifact refs.
- Provenance contract validation for candidate provenance drafts.
- Metric candidate validation for units, source refs, and non-negative numeric values.
- Official, formal, and proof-system soundness claim detection.
- Synthetic quarantine manifests for rejected candidates.
- `NormalizedExternalResultDraft` for valid pending-review candidates.
- `EvidenceAppendProposal` and review-state primitives.
- `EvidenceAppendProposalLedger` persistence, digest-chain validation, and top-level note claim-language validation.
- JSON fixtures and integration tests for import, digest, provenance, metric, proposal, proposal ledger, and claim-boundary behavior.

## Deliberately Not Implemented

- No live zk-Harness execution.
- No shelling out to external tools.
- No external repository cloning.
- No real external result import.
- No official benchmark evidence.
- No Level2+ accepted evidence.
- No performance score population.
- No formal evidence.
- No proof-system soundness claim.

## Claim Boundaries

Synthetic result candidates are not benchmark results.

Evidence append proposals are not accepted evidence.

Phase I artifacts are `Level0DesignNote`:

- synthetic import bundles,
- validation reports,
- normalized result drafts,
- synthetic quarantine manifests,
- evidence append proposals,
- proposal ledgers.

Referenced existing local replay artifacts remain `Level1LocalReplay` at most. Phase I does not create reproducible benchmark artifacts, cross-backend evidence, formal property statements, or machine-checked proofs.

## Known Limitations

- Digest validation is local integrity validation over supplied bytes, not independent reproduction.
- Metric candidates are metadata only and do not become score inputs.
- Proposal ledgers are review ledgers and do not mutate the accepted Evidence Ledger.
- Proposal review policy is intentionally minimal; reviewed acceptance, supersession, and future append eligibility are deferred to Phase J.

## Validation

Current Phase I validation is covered by:

```sh
cargo test --workspace
cargo test --workspace --features external-runner
```

The broader gate remains:

```sh
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo doc --workspace --no-deps
```
