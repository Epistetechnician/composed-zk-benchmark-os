# Phase T Cross-Bundle Audit Index Boundary Spec

Status: docs-first boundary only.

Phase S materializes ergonomics output for one valid
`LocalAuditIndexManifest`. Phase T defines the next possible boundary for
cross-bundle audit-index planning across multiple existing local audit-index
manifests. It does not authorize Rust implementation code, generated
cross-bundle files, writer or reader APIs, command-line tools, UI dashboards,
browser apps, JavaScript/TypeScript/package runtime additions, replay-command
execution, external replay, live backend execution, external repo clones,
vendored source, external result import, generated benchmark artifacts,
official benchmark evidence, ZK backend performance claims, Level2+ evidence
creation, broad leaderboard claims, accepted Evidence Ledger mutation, source
pack mutation, source report mutation, report-bundle mutation, audit-index
output mutation, Phase S ergonomics output mutation, score-axis population from
local-only evidence, or treating a cross-bundle audit index as evidence.

## State Slice

This phase is limited to Markdown specification and navigation updates under:

- `docs/91-phase-t-cross-bundle-audit-index-boundary-spec.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`

No crate, test fixture, generated artifact, benchmark pack, readiness output,
dashboard output, report-bundle output, audit-index output, ergonomics output,
local replay result, Evidence Record, Score Report, accepted Evidence Ledger,
package runtime file, command-line surface, or UI artifact is changed by this
phase.

## Purpose

The current audit-index track is intentionally single-bundle:

- Phase R summarizes existing local report-bundle metadata into one local
  audit-index manifest.
- Phase S provides one selected ergonomics view over one valid audit-index
  manifest.

The next useful planning boundary is cross-bundle summarization without source
enrichment. A future implementation may compare multiple already-materialized
local audit-index manifests and build local presentation metadata that helps an
operator see which local bundles exist, which warnings repeat, and which inputs
are duplicated or inconsistent.

The cross-bundle output remains a local operator/auditor planning view. It is
not accepted evidence, not official benchmark evidence, not benchmark output,
not ZK backend performance evidence, not Level2+ evidence, and not proof.

## Authorized Future Input

A future implementation may accept only:

- two or more valid `LocalAuditIndexManifest` values;
- caller-supplied logical source ids for those manifests;
- caller-supplied source path metadata for protected-path overlap checks;
- an optional deterministic grouping and sorting request over fields already
  present in the supplied manifests;
- a caller-selected local output root for a future cross-bundle view;
- an explicit overwrite policy.

The future implementation must validate every input manifest before deriving
cross-bundle metadata. It must not read source packs, source reports, report
bundles, accepted Evidence Ledgers, external resources, Phase R output roots, or
Phase S ergonomics output roots to enrich or repair the supplied manifests.

## Cross-Bundle Semantics

A future implementation may compute only local summary metadata derived from the
supplied audit-index manifests:

- source manifest count;
- source manifest ids and digests;
- selected local report-bundle ids already referenced by source manifests;
- repeated warning labels;
- repeated failed-readiness labels;
- duplicate source refs;
- duplicate local artifact refs;
- inconsistent claim-boundary labels;
- inconsistent limitation labels;
- deterministic grouping and sorting views;
- local warning summaries.

It must not merge manifests into accepted evidence. It must not decide that
matching data across manifests is more trustworthy than any individual source
manifest. Duplicate reports or repeated warnings are audit signals only.

## Duplicate And Conflict Handling

A future implementation must fail closed or mark an explicit local warning when
cross-bundle inputs disagree. At minimum, it must distinguish:

- duplicate manifest ids with identical digest;
- duplicate manifest ids with different digest;
- duplicate source report ids with identical source refs;
- duplicate source report ids with conflicting source refs;
- repeated failed-readiness warnings;
- missing required limitation labels in any source manifest;
- source manifests with different claim-boundary ceilings.

Conflicts must not be repaired by rewriting, dropping, or normalizing source
manifests. A future view may exclude invalid inputs only when the exclusion is
explicit in the output and the output remains capped at `Level0DesignNote`.

## Protected Path Policy

A future implementation must treat all supplied source paths as protected:

- source pack locations;
- source report locations;
- report-bundle locations;
- audit-index output locations;
- Phase S ergonomics output locations;
- accepted Evidence Ledger locations;
- future cross-bundle output locations already present on disk.

The future output root must be rejected when it is equal to, nested under, or a
parent of any protected path. Relative and absolute representations of the same
location must overlap. The future API must not rely on string-prefix checks
alone when structured path normalization is available.

## Output Root Policy

A future implementation must reject:

- empty output-root declarations;
- output roots that are existing files;
- output roots containing unexpected files;
- output roots containing symlinks;
- output roots with parent-directory components;
- output roots with URL-like content or shell-like fragments;
- output roots that overlap protected source or evidence paths;
- overwrite attempts unless the caller explicitly permits overwrite;
- overwrite attempts where existing bytes do not match the supplied
  cross-bundle contract.

Corrupted output roots are not repair inputs. Explicit overwrite may replace
only declared cross-bundle presentation files after validation proves the
existing root is a complete, digest-consistent bundle for the same contract.
Partial, unexpected, symlinked, stale-digest, or drifted roots must be rejected.

## Authorized Future Output Shape

A future implementation may define a small declared-file-only output shape under
a caller-owned local root. The shape must include:

- one canonical cross-bundle view JSON file;
- one deterministic rendered Markdown file;
- digest sidecars for every materialized payload;
- an input-manifest digest summary;
- required limitation labels in the rendered Markdown.

The future output files must not be inserted into any source pack, source
report, report bundle, audit-index output, Phase S ergonomics output, score
report, accepted Evidence Ledger, or benchmark pack.

## Required Future Validation

A future implementation phase must include hermetic tests for:

- invalid source manifest rejection;
- duplicate manifest id with matching digest;
- duplicate manifest id with conflicting digest;
- duplicate source report id with conflicting source ref;
- failed-readiness and local-only warning visibility;
- required limitation-label preservation;
- claim-boundary ceiling preservation;
- deterministic grouping and sorting;
- protected-path overlap across source packs, reports, report bundles,
  audit-index outputs, ergonomics outputs, accepted Evidence Ledgers, and the
  cross-bundle output root;
- relative and absolute protected-path overlap equivalence;
- output-root parent/child overlap rejection;
- non-overwrite rejection;
- explicit overwrite that is not a repair path;
- partial-bundle rejection;
- unexpected-file rejection;
- stale-digest rejection;
- materialized Markdown drift rejection;
- symlink rejection;
- source manifest immutability;
- source scan proving no external execution hooks were added.

## Claim Boundary

The maximum Phase T planning boundary is `Level0DesignNote`.

Required labels for any future materialized cross-bundle output:

- Cross-bundle audit indexes are not accepted evidence.
- Cross-bundle audit indexes are local presentation metadata only.
- Cross-bundle audit indexes do not create official benchmark evidence.
- Cross-bundle audit indexes do not create Level2+ evidence.
- Cross-bundle audit indexes do not prove backend performance.
- Duplicate local metadata is an audit signal, not independent confirmation.
- Local replay artifacts are not official benchmark evidence.
- Internal timing telemetry is not ZK backend performance.

## Non-Goals

This docs-first phase does not permit:

- Rust source or test changes;
- generated cross-bundle files;
- cross-bundle writer or reader APIs;
- command-line tools;
- browser or UI dashboard work;
- JavaScript, TypeScript, package scripts, lockfiles, or node dependencies;
- source pack mutation;
- source report mutation;
- report-bundle mutation;
- audit-index output mutation;
- Phase S ergonomics output mutation;
- accepted Evidence Ledger mutation;
- replay-command execution;
- external replay;
- live backend execution;
- external repo clones or vendored source;
- external result import;
- generated benchmark artifacts;
- official benchmark evidence;
- ZK backend performance claims;
- Level2+ evidence creation;
- score-axis population from local-only evidence;
- broad leaderboard claims.

## Exit Criteria

This docs-first phase exits when this boundary spec and navigation updates are
committed. Any future Phase T implementation must name its own state slice and
must stay within the future input, output, validation, protected-path, and
claim-boundary rules above.
