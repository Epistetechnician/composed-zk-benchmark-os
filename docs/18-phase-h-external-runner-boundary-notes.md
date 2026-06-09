# Phase H External-Runner Boundary Notes

## What Was Implemented

Phase H adds the local external-runner boundary foundation in `zkbench-core`.

Implemented modules:

- `external_runner::policy`
- `external_runner::handoff`
- `external_runner::artifact_capture`
- `external_runner::provenance`
- `external_runner::result_import`
- `external_runner::quarantine`
- `external_runner::validation`
- `external_runner::serialization`
- `adapters::zk_harness::handoff`

The implementation defines disabled/manual-only external-runner policy, manual handoff bundles, artifact capture contracts, provenance contracts, result import schemas, result candidate validation, quarantine manifests, deterministic JSON helpers, and zk-Harness dry-run-plan-to-handoff mapping.

## Why Live Execution Is Still Disabled

External execution is disabled by default. The `external-runner` Cargo feature is a boundary marker only. It does not enable process execution, shell execution, external repo checkout, real zk-Harness invocation, or imported benchmark evidence.

Manual handoff bundles are not benchmark results. They are review artifacts that preserve source ids, source digests, expected contracts, and future prerequisites.

## External-Runner Policy Summary

`ExternalRunnerPolicy` records:

- execution mode,
- review status,
- execution gates,
- tool allowlist,
- path policy,
- environment policy,
- network policy,
- result policy,
- claim-boundary policy.

Actual Phase H policies use `Disabled` or `ManualHandoffOnly`. Validation rejects live future execution modes, absolute paths, missing review gates, and Level2+ actual evidence.

## Manual Handoff Bundle Summary

`ManualHandoffBundle` records:

- dry-run plan id,
- source benchmark pack id,
- source pack digest,
- source artifact digests,
- external-runner policy,
- artifact capture contract,
- provenance contract,
- result import schema,
- manual instructions,
- export metadata,
- `Level0DesignNote` claim boundary.

Manual instructions preserve inert planned command data only. They are not shell scripts and are not execution APIs.

## Artifact Capture Contract Summary

`ArtifactCaptureContract` declares expected future artifact roles:

- input manifest,
- candidate workload manifest,
- external tool version,
- raw external output,
- normalized result candidate,
- provenance record,
- validation report,
- evidence append proposal.

The default contract contains no actual captured external artifacts.

## Provenance Contract Summary

`ProvenanceContract` requires:

- operator or agent,
- execution date declared by operator,
- external tool name,
- external tool version,
- external tool source,
- external tool commit or release,
- host OS,
- hardware summary,
- command plan id,
- benchmark pack id,
- artifact digest set,
- network policy,
- notes.

The contract is schema evidence only. It is not proof that a future run happened.

## Result Import Schema Summary

`ExternalResultImportSchema` defines local validation rules for future result candidates. Validation rejects missing source ids, missing provenance, absolute paths, unknown metric units, Level2+ claim requests, metric values without source artifact refs, official benchmark claims, formal evidence claims, and proof-system soundness claims.

Phase H does not populate real metric candidates and does not produce performance scores.

## Quarantine Model Summary

`QuarantineManifest` records rejected or pending external result candidates. Quarantine is a local review mechanism only. It is not acceptance evidence and must not affect Score Reports.

Result import candidates are quarantined or pending review until validated.

## zk-Harness Handoff Mapping Summary

`ZkHarnessManualHandoffBundle` maps a dry-run plan into a manual handoff bundle while preserving:

- dry-run plan id,
- source benchmark pack id,
- source pack digest,
- source artifact digests,
- inert planned commands as manual instructions,
- artifact expectations,
- result import expectations,
- future execution prerequisites.

The mapping never emits a zk-Harness result and never converts local replay results into zk-Harness results.

## Validation Summary

Phase H tests cover:

- external-runner policy gates and JSON round-trips,
- manual handoff bundle JSON round-trips and live-execution rejection,
- artifact capture contract roles and path rejection,
- result import candidate rejection cases,
- quarantine manifest JSON round-trips,
- zk-Harness handoff mapping preservation,
- claim-boundary enforcement,
- source scans for process execution APIs.

## Claim-Boundary Status

Phase H artifacts are `Level0DesignNote`:

- external-runner policies,
- manual handoff bundles,
- artifact capture contracts,
- provenance contracts,
- result import schemas,
- quarantine manifests,
- zk-Harness handoff mappings.

Referenced local packs remain `Level1LocalReplay` at most. No Phase H artifact creates Level2+ evidence.

A benchmark pass is not proof. Local replay is not official benchmark evidence. A recursion proof is not semantic proof. zk-Harness dry-run plans are not benchmark results. Manual handoff bundles are not benchmark results.

## Deliberately Unimplemented

- No live external execution.
- No `std::process::Command`.
- No external repo checkout.
- No real zk-Harness invocation.
- No imported external benchmark data.
- No official performance claims.
- No proof-system acceptance claims.
- No formal evidence claims.
- No evidence append proposal acceptance.

## Next Recommended Slice

Phase I should implement a local/synthetic result import prototype:

- import synthetic external result candidates from JSON,
- validate artifact digests and provenance fields,
- quarantine invalid candidates,
- create evidence append proposals only,
- preserve Level0/Level1 claim boundaries,
- still no real zk-Harness execution,
- still no official performance claims.
