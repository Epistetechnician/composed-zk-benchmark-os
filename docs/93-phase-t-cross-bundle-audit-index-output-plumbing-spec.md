# Phase T Cross-Bundle Audit Index Output Plumbing Spec

Status: docs-first boundary only.

Phase T currently has an in-memory cross-bundle audit-index planning view over
two or more valid `LocalAuditIndexManifest` values. This spec defines the next
possible boundary for materializing that view as declared local presentation
metadata. It does not authorize Rust implementation code, generated
cross-bundle files, cross-bundle writer or reader APIs, command-line tools, UI
dashboards, browser apps, JavaScript/TypeScript/package runtime additions,
replay-command execution, external replay, live backend execution, external repo
clones, vendored source, external result import, generated benchmark artifacts,
official benchmark evidence, ZK backend performance claims, Level2+ evidence
creation, broad leaderboard claims, accepted Evidence Ledger mutation, source
pack mutation, source report mutation, report-bundle mutation, audit-index
output mutation, Phase S ergonomics output mutation, score-axis population from
local-only evidence, or treating materialized cross-bundle metadata as evidence.

## State Slice

This phase is limited to Markdown specification and navigation updates under:

- `docs/93-phase-t-cross-bundle-audit-index-output-plumbing-spec.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`

No crate, test fixture, generated artifact, benchmark pack, readiness output,
dashboard output, report-bundle output, audit-index output, ergonomics output,
cross-bundle output, local replay result, Evidence Record, Score Report,
accepted Evidence Ledger, package runtime file, command-line surface, or UI
artifact is changed by this phase.

## Purpose

The in-memory Phase T view can compare already-supplied local audit-index
manifests and derive deterministic source summaries, groups, duplicate/conflict
signals, warning summaries, limitation labels, JSON, and Markdown. The next
useful boundary is to define how a future implementation may write those bytes
without creating a repair path for bad local output roots and without writing
into any source or evidence location.

The future output-plumbing slice answers only:

- where a materialized cross-bundle view may be written;
- which declared files may exist below the output root;
- how JSON, Markdown, and digest sidecars are bound to the in-memory view;
- how protected source and evidence paths are kept immutable;
- how corrupted existing output roots fail closed instead of being repaired;
- how cross-bundle duplicate and conflict signals remain audit signals only.

The output remains local operator/auditor presentation metadata. It is not
accepted evidence, not official benchmark evidence, not benchmark output, not ZK
backend performance evidence, not Level2+ evidence, and not proof.

## Authorized Future Input

A future implementation may accept:

- two or more valid `LocalAuditIndexManifest` values;
- one valid `LocalAuditIndexCrossBundleRequest`;
- one valid in-memory `LocalAuditIndexCrossBundleView` deterministically derived
  from the supplied manifests and request;
- caller-supplied logical source ids already present in the view;
- caller-supplied protected path metadata for source packs, source reports,
  report bundles, audit-index outputs, Phase S ergonomics outputs, accepted
  Evidence Ledgers, and existing cross-bundle output roots;
- a caller-selected local output root intended to represent a
  `cross-bundle-audit-index/` directory;
- an explicit overwrite policy.

The implementation must validate every source manifest, request, and in-memory
view before writing and after reading. It must not read source packs, source
reports, report bundles, accepted Evidence Ledgers, Phase R output roots, Phase
S ergonomics output roots, external resources, or old cross-bundle output roots
to enrich or repair the supplied manifests.

## Authorized Future Output Shape

A future implementation may materialize exactly:

```text
cross-bundle-audit-index/
  cross-bundle-view.json
  rendered/
    cross-bundle-view.md
  digests/
    cross-bundle-view-json.sha256
    cross-bundle-view-markdown.sha256
```

`cross-bundle-view.json` must be the canonical pretty JSON form of
`LocalAuditIndexCrossBundleView`. `rendered/cross-bundle-view.md` must byte-match
the deterministic Markdown stored in that view. Digest sidecars must bind the
materialized JSON and Markdown bytes using SHA-256 artifact digests.

The output files must not be inserted into `pack.json`, any source report, any
report bundle, any audit-index output, any Phase S ergonomics output, any score
report, any benchmark pack, or the accepted Evidence Ledger. They must not
overwrite source files or previously materialized source metadata.

## Protected Path Policy

A future implementation must treat all caller-supplied source and evidence paths
as protected, including:

- source pack roots and `pack.json` files;
- source report roots and report files;
- report-bundle roots and rendered report files;
- audit-index output roots and manifest files;
- Phase S ergonomics output roots and rendered files;
- accepted Evidence Ledger files and containing directories;
- existing cross-bundle output roots from other runs.

The future output root must be rejected when it is equal to, nested under, or a
parent of any protected path. The same rejection applies when relative and
absolute spellings normalize to overlapping locations. Implementations must use
structured path normalization where available and must not rely on string-prefix
checks alone.

Protected-path overlap rejection is a pre-write gate. A future writer must not
create the output root, stage files, remove files, or inspect source contents as
a fallback when protected-path validation fails.

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
  cross-bundle view, Markdown, and digest contract.

Corrupted output roots are not repair inputs. Explicit overwrite may replace
only the four declared cross-bundle output files after validation proves the
existing root is a complete, digest-consistent bundle for the same source
manifests, request, view, and limitation-label contract.

Partial bundles, unexpected files, symlinks, stale digest sidecars, malformed
JSON, Markdown drift, view drift, missing limitation labels, and undeclared
directories must be rejected. The future writer must not delete unexpected files,
fill missing files, rewrite stale sidecars, normalize invalid views, or use the
writer as a cleanup path for a corrupted root.

## Required Future Validation

A future implementation must fail closed when:

- fewer than two source manifests are supplied;
- any source manifest is invalid;
- the supplied `LocalAuditIndexCrossBundleRequest` is invalid;
- the supplied `LocalAuditIndexCrossBundleView` cannot be re-derived
  deterministically from the supplied manifests and request;
- the materialized JSON does not deserialize to the supplied view;
- the materialized Markdown does not byte-match the view Markdown;
- either digest sidecar is missing, malformed, stale, unsupported, or mismatched;
- any unexpected file or directory exists below the cross-bundle output root;
- any symlink exists below the cross-bundle output root;
- protected source or evidence paths overlap the output root;
- failed-readiness warnings are hidden;
- local-only warning summaries are hidden;
- duplicate or conflict signals are hidden;
- any required limitation label is absent from the view or materialized Markdown;
- the output boundary is above `Level0DesignNote`;
- any source pack, source report, report bundle, audit-index output, Phase S
  ergonomics output, or accepted Evidence Ledger is mutated;
- any output claims official benchmark evidence;
- any output claims ZK backend performance;
- any output claims Level2+ evidence;
- any output claims accepted Evidence Ledger mutation;
- any output includes replay-command execution output;
- any output populates score axes from local-only metadata.

## Required Future Tests

A future implementation phase must include hermetic tests for:

- declared-file write/read round trip;
- canonical JSON and Markdown byte matching;
- source manifest/request/view deterministic re-derivation;
- invalid manifest, invalid request, and invalid view rejection;
- duplicate manifest id with matching digest;
- duplicate manifest id with conflicting digest;
- duplicate input id with conflicting artifact;
- failed-readiness and local-only warning visibility;
- duplicate/conflict signal preservation;
- claim-boundary ceiling preservation;
- required limitation-label preservation;
- non-overwrite rejection;
- explicit overwrite over a valid same-contract bundle;
- explicit overwrite refusing to repair corrupted roots;
- partial-bundle rejection;
- unexpected-file and unexpected-directory rejection;
- stale JSON digest and stale Markdown digest rejection;
- materialized Markdown drift rejection;
- malformed JSON rejection;
- symlink rejection;
- protected-path overlap across source packs, source reports, report bundles,
  audit-index outputs, Phase S ergonomics outputs, accepted Evidence Ledgers,
  and existing cross-bundle output roots;
- relative and absolute protected-path overlap equivalence;
- output-root parent/child overlap rejection;
- source and evidence immutability;
- source scan proving no external execution hooks were added.

## Claim Boundary

The maximum Phase T output-plumbing planning boundary is `Level0DesignNote`.

Future materialized cross-bundle audit-index output files remain local
presentation metadata only. They are not accepted evidence, not official
benchmark evidence, not benchmark outputs, not backend performance evidence, not
Level2+ evidence, and not proof.

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
- broad leaderboard claims;
- treating cross-bundle audit-index metadata as evidence.

## Future Implementation Exit Criteria

A future implementation phase must include:

- adjacent local output writer and reader APIs for exactly the four authorized
  output files;
- deterministic re-derivation of the view from the supplied manifests and
  request;
- digest verification for materialized JSON, Markdown, and digest sidecars;
- protected-path overlap checks before any write;
- output-root safety checks before materialization;
- overwrite-drift, corrupted-root, symlink, unexpected-file, stale-digest,
  malformed-JSON, Markdown-drift, and partial-bundle rejection tests;
- validation that source packs, source reports, report bundles, audit-index
  outputs, Phase S ergonomics outputs, and accepted Evidence Ledgers are not
  mutated;
- regression tests preserving failed-readiness, duplicate/conflict signal, and
  local-only warning visibility;
- regression tests preserving required limitation labels in materialized
  Markdown;
- source scans proving no external execution hooks were added;
- documentation updates preserving Phase T claim labels.

This docs-first phase exits when this boundary spec and navigation updates are
committed.
