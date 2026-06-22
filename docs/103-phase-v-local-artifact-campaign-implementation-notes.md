# Phase V Local Artifact Campaign Implementation Notes

Status: implemented as local artifact-campaign output plumbing only.

This slice implements the smallest code surface following
`docs/98-phase-v-local-artifact-campaign-boundary-spec.md`. It adds local
campaign manifests, validation reports, deterministic Markdown summaries, digest
sidecars, and caller-owned output-root read/write helpers for durable local
artifact campaigns.

This is not official benchmark evidence. No generated campaign output is
committed, no external replay is run, no live backend is called, no score axis is
populated, no accepted Evidence Ledger is mutated, no official benchmark
submission is created, and no claim above `Level1LocalReplay` is created.

## State Slice

This implementation touches:

- `.gitignore`
- `crates/zkbench-core/src/lib.rs`
- `crates/zkbench-core/src/prelude.rs`
- `crates/zkbench-core/src/local_artifact_campaign.rs`
- `crates/zkbench-core/tests/phase_v_local_artifact_campaign.rs`
- `docs/103-phase-v-local-artifact-campaign-implementation-notes.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `README.md`
- `AGENTS.md`

No Cargo metadata, package runtime files, generated campaign outputs, benchmark
packs, accepted Evidence Ledgers, official submission artifacts, external result
imports, command-line tools, UI files, network code, credential code, or Phase W
promotion semantics are changed by this slice.

## Implemented Surface

The `zkbench-core` crate now provides:

- `LocalArtifactCampaignManifest`;
- `LocalArtifactCampaignInputRef`;
- `LocalArtifactCampaignInputKind`;
- `LocalArtifactCampaignValidation`;
- `LocalArtifactCampaignOutput`;
- `LocalArtifactCampaignRetentionPolicy`;
- `required_local_artifact_campaign_limitations`;
- `validate_local_artifact_campaign_manifest`;
- `serialize_local_artifact_campaign_manifest_json`;
- `deserialize_local_artifact_campaign_manifest_json`;
- `serialize_local_artifact_campaign_validation_json`;
- `compute_local_artifact_campaign_manifest_digest`;
- `render_local_artifact_campaign_markdown`;
- `build_local_artifact_campaign_input_from_phase_u_output`;
- `write_local_artifact_campaign_outputs`;
- `read_local_artifact_campaign_outputs`.

The writer emits exactly six declared files below the caller-owned output root:

- `campaign-manifest.json`;
- `campaign-validation-report.json`;
- `rendered/campaign-summary.md`;
- `digests/campaign-manifest-json.sha256`;
- `digests/campaign-validation-report-json.sha256`;
- `digests/campaign-summary-markdown.sha256`.

The default durable local output root `.local-artifact-campaigns/` is now
ignored by git. The implementation does not write there automatically; callers
must still choose an output root explicitly.

## Validation Behavior

The implementation validates:

- campaign id is one portable path segment;
- at least one Phase U local benchmark artifact output reference is present;
- input ids and artifact URIs are unique;
- artifact URIs are portable relative references;
- digests are SHA-256-shaped;
- validation gates are declared;
- input and output claim boundaries remain `Level1LocalReplay` or below;
- output boundary does not exceed the weakest input boundary;
- external replay, official evidence, ZK performance, Level2+ creation,
  accepted-ledger mutation, and local-only score-axis population flags are
  false;
- all required limitation labels are present.

`build_local_artifact_campaign_input_from_phase_u_output` validates an existing
Phase U output root through `read_local_benchmark_artifact_outputs` before
building a campaign input reference, so stale or partial Phase U outputs fail
closed before campaign construction.

The output-root helpers preserve the established local-output rules:

- protected-path overlap rejection, including symlink-resolved overlap;
- existing file-root rejection;
- symlink rejection;
- unexpected-file rejection;
- partial-campaign rejection;
- stale digest rejection;
- rendered Markdown drift rejection;
- validation report drift rejection;
- non-repair overwrite behavior.

## Tests

`crates/zkbench-core/tests/phase_v_local_artifact_campaign.rs` covers:

- manifest serialization and deterministic digesting;
- validation report serialization;
- Markdown limitation-label preservation;
- claim-elevation and unsafe-reference rejection;
- required Phase U output reference rejection;
- Phase U output-root validation before campaign input construction;
- declared-file write/read round trip;
- stale digest rejection;
- partial and unexpected file rejection;
- repair-overwrite rejection;
- protected-path overlap rejection;
- symlink file and symlink-parent rejection;
- source scan for runtime, package, and claim-elevation hooks.

## Claim Boundary

Local artifact campaign outputs are local durability artifacts only. They are
not official benchmark evidence, not accepted Evidence Ledger entries, not
Level2+ evidence, not ZK backend performance evidence, not semantic correctness,
not external replay evidence, and not authorization for Phase W promotion.

## Explicitly Still Missing

- external replay authority;
- live backend execution;
- official benchmark submission;
- accepted Evidence Ledger mutation;
- score-axis population from reviewed non-local evidence;
- generated campaign output promoted into committed fixtures;
- Phase W reviewed promotion implementation.
