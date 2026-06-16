# Phase L Local Soak And Report-Bundle Review Notes

Phase L adds explicit long local soak execution and sampled report-bundle review on top of the Phase F local replay and benchmark-pack infrastructure.

This Conductor slice is distinct from the future narrow zkML adapter listed as Phase L in `docs/12-task-list.md`.

## Implemented

- `SoakPlan` and `SoakConfig` for deterministic local soak grids.
- `run_local_soak()` to generate, mutate, replay, ledger, and write benchmark packs across implemented families and explicit seeds.
- `SoakExecutionReport` with deterministic JSON serialization and no wall-clock timestamps.
- `ReportBundleReviewPlan` with sampled review strategies.
- `review_report_bundle()`, `review_sampled_report_bundles()`, and `review_soak_report_bundles()`.
- `ReportBundleReviewReport` as Level0DesignNote review metadata.
- `quick_three_family_all_passes()` and `quick_three_family_smoke()` named soak presets.
- `run_soak_campaign()` for quick local campaigns with artifact archival.
- `RegressionCorpus` curation from review failures, soak write failures, and skipped mutation passes.
- Examples: `phase_l_soak`, `phase_l_campaign`.
- Ignored artifact root: `.context/phase-l-artifacts/`.
- Integration tests for soak determinism, sampled review, campaigns, claim boundaries, and source scans.

## Deliberately Not Implemented

- No external backend invocation.
- No live zk-Harness execution.
- No official benchmark evidence.
- No Level2+ promotion.
- No performance metric population.
- No dashboard or aggregate leaderboard claims.

## Claim Boundaries

Soak benchmark packs remain `Level1LocalReplay`.

Soak execution reports and report-bundle review reports are `Level0DesignNote`.

Local replay is not official benchmark evidence. A benchmark pass is not proof. A recursion proof is not semantic proof.

## Local Soak Behavior

`run_local_soak()` loops over configured family kinds and explicit seeds only. For each cell it:

1. generates a concrete benchmark instance,
2. applies default mutation passes when enabled,
3. builds local replay manifests,
4. runs `LocalJsonAdapter` replay,
5. writes a benchmark pack with evidence ledger and conservative score report,
6. records deterministic soak metadata.

The soak runner rejects claim-boundary caps above `Level1LocalReplay`.

## Report-Bundle Review Behavior

A report bundle is a benchmark pack plus its conservative `ScoreReport`.

Sampled review checks:

- pack digest validation,
- manifest claim boundary cap,
- README claim-boundary warnings,
- conservative score report presence and low confidence,
- absence of populated performance metrics,
- evidence ledger entry count alignment with manifest evidence record counts,
- ledger entry claim boundaries at `Level1LocalReplay` or lower.

Review reports are metadata only. They do not mutate evidence ledgers and do not create accepted evidence.

## Operational Use (Phase L in practice)

Run a quick local campaign across all three implemented families with all three mutation passes:

```sh
./.context/phase-l/run_quick_campaign.sh quick_full
```

Or the smoke grid (2 seeds × 3 families):

```sh
./.context/phase-l/run_quick_campaign.sh quick_smoke
```

Artifacts (gitignored under `.context/`):

```text
.context/phase-l-artifacts/
  campaigns/<campaign_id>/
    campaign_report.json
    soak_execution_report.json
    report_bundle_review.json
    sampled_reports/<pack_id>.json
    failure_packs/<pack_id>/        # archived when review fails
    soak_failures/<cell>.json       # soak write failures
  regression_corpus/corpus.json     # curated regression entries
```

Regression corpus entries reference stored failure artifacts. They are Level0DesignNote metadata only.

## Validation Gate

Phase L tests cover:

- byte-identical soak packs for identical inputs,
- soak execution report JSON round-trip,
- sampled report-bundle review pass for soak outputs,
- claim-boundary enforcement,
- empty `std::process::Command` and `Command::new` scans in soak and review modules.

These checks are local integrity and reproducibility checks only. They do not establish official benchmark evidence, cross-backend reproduction, or formal evidence.
