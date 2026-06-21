# Phase P Read-Only Reporting Boundary Notes

## Status

Phase P-A implements a read-only reporting boundary over existing local
metadata. It extends the Phase P model so reporting can summarize:

- conservative `ScoreReport` data;
- local `PackReadinessReport` data;
- local `PackReadinessValidation` data.

This slice is reporting only. It does not create evidence, execute replay
commands, import external results, mutate `pack.json`, mutate the accepted
`EvidenceLedger`, or promote claim boundaries.

## State Slice

```text
crates/zkbench-core/src/dashboard/model.rs
crates/zkbench-core/src/dashboard/mod.rs
crates/zkbench-core/src/lib.rs
crates/zkbench-core/tests/phase_p_dashboard.rs
docs/67-phase-p-read-only-reporting-boundary-notes.md
docs/12-task-list.md
README.md
AGENTS.md
```

## Implemented Surface

Phase P-A adds:

```text
DashboardPanelKind::PackReadiness
build_dashboard_model_from_pack_readiness
render_dashboard_markdown support through existing non-axis panel rendering
validation that pack-readiness panels remain Level0DesignNote
```

The pack-readiness reporting model displays:

- source pack id;
- readiness validation status;
- passed and failed readiness-check counts;
- external replay authorization flag;
- Level2 evidence creation flag;
- official benchmark evidence flag;
- ZK backend performance claim flag;
- explicit claim-boundary limitations.

## Claim Boundary

All Phase P-A pack-readiness reporting remains `Level0DesignNote`.

Rendering a readiness report is not:

- Level2 evidence;
- official benchmark evidence;
- ZK backend performance evidence;
- execution evidence;
- proof of semantic soundness;
- accepted Evidence Ledger mutation.

## Non-Goals

- No UI dashboard.
- No browser app.
- No external replay.
- No benchmark output generation.
- No score-axis population from local-only evidence.
- No Level2+ evidence creation.
- No official benchmark evidence.
- No ZK backend performance claim.

## Validation

The Phase P tests verify:

- empty local `ScoreReport` dashboards remain claim-capped;
- Markdown rendering shows claim boundaries;
- pack-readiness reporting validates from real adjacent Phase O-D outputs;
- pack-readiness Markdown does not elevate claims;
- pack-readiness panel boundary drift is rejected;
- local score axes remain unpopulated.
