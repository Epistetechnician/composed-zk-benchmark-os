# Holistic Claim-Validation Pipeline V1

State slice: `astral-docker-closed-loop-correction-simulation-v25`.

Status: `Implemented / ExecutionPending`.

## Purpose

The authoritative V25 pipeline checks the complete current Astral claim census,
the immutable V18-V23 release, the immutable V24 release, the V25 raw artifact,
all current Astral structural tests, and the Rust protocol tests. It emits one
digest-sealed report containing claim-by-claim dispositions and explicit thesis
gates.

Pipeline completion is not a scientific aggregate score. A successful pipeline
means the supplied evidence was intact, replayable within its declared ceiling,
and represented without missing claims. It may and currently must return
`ThesisNotValidated`.

## Inputs

- clean committed Astral source;
- content-addressed V18-V23 immutable release identity
  `7dd61f997bd2cbd8f55f497331ed83757bf994c80a2dc3f01fc1bf1516a9a483`;
- content-addressed V24 immutable release identity
  `52b8e594e7c7c8dc07afa8871310171f797248a563114c00ab26979bb266ff02`;
- one content-addressed V25 artifact;
- frozen `claim-contract.json` covering `C001` through `C045`;
- a new repository-external report path.

## Validation order

1. Reject a dirty launcher source tree.
2. Parse the append-only Markdown ledger and derive every claim's current
   status, including dated status updates.
3. Require an exact, ordered `C001..C045` census and exact status agreement with
   the frozen claim contract.
4. Verify both historical release manifests, file censuses, content digests,
   directory identities, and symlink absence.
5. Locate the exact Git tree bound to the V18-V23 release and run its
   authoritative validator in a detached checkout.
6. Run the V24 authoritative validator, which creates its own detached checkout
   at the release-bound source commit.
7. Validate V25 by recomputing raw record counts, aggregate metrics, bootstrap,
   gates, deterministic simulation replay, source inventory, Docker runtime
   identity, and external-state stops.
8. Run every current `tools/astral-*/tests` suite and the locked
   `astral-stage0-protocol` Rust suite.
9. Emit the holistic JSON report and SHA-256 sidecar without modifying the
   source checkout.

## Claim dispositions

- `Refuted` becomes `RetainedSetupScopedRefutation`.
- `Not refuted` never becomes proven.
- Claims bound to validated releases become
  `ImmutableAuthorArtifactValidatedWithinCeiling`.
- C045 may become `MachineValidatedSyntheticHarnessOnly`.
- proposed and inconclusive claims remain unresolved.
- design choices remain policy, not empirical findings.

No status is promoted by the pipeline. The append-only ledger remains the
authoritative human-readable record.

## Thesis gate

The thesis remains `NotValidated` while any of these are absent:

- fresh Stage 0C confirmation;
- a model-backed telemetry effect-prediction result;
- model-backed correction gain over matched reflection and ordinary-update
  controls;
- prospective pre-output failure prediction;
- independent human scientific and reproducibility review;
- an independent implementation replication.

The Docker positive control cannot satisfy any of these requirements.

## Authoritative command

```text
python tools/astral-continual-correction-v25/validate_all.py \
  --artifact <astral-v25-content-addressed-artifact> \
  --legacy-release <astral-validation-release-v1-content-addressed-package> \
  --v24-release <astral-v24-validation-release-v2-content-addressed-package> \
  --report <new-repository-external-report.json>
```

The command is offline and fail-closed. Child reports for the two immutable
release validators are written beside the holistic report and retained.
