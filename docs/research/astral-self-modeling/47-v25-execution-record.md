# V25 Execution Record

State slice: `astral-telemetry-information-presence-v25`.

Date: 2026-08-10.

Execution: `InformationPresenceReportGapObserved`. Confirmation:
`NotAuthorized`. Stage 0C: `Blocked`. Stage 1: `BlockedByStage0C`.

## Qualification and sealed assessment

The run used the repository's cached local
`nemotron_h` checkpoint at
`/Users/shaanp/.lmstudio/models/mlx_lm_lora/mesh-brain-nemotron-3-nano-4b`
with the V24 manual hybrid forward seam and V25 all-layer final-position
capture. No network access or model download was used. The repository was not
used as an artifact output root.

Independent V25 validation accepted the external bundle. The configuration
lock bound the following source identities:

- V25 tool SHA-256:
  `3be9b20e1d41900d9b6abba8340a5ab7dc5197108961c62b2431e608724867d5`;
- V25 validator SHA-256:
  `ccdc79d101a44bc394e9c4c943dc892f6f57e0605aa98a950406434a7c5463f1`;
- V24 tool SHA-256:
  `edd58a65303e8a74c3608eeba4b22468cd37c77c542fa66d73a48ff976f72d7d`;
- V22 shared-core SHA-256:
  `28e84dcdf0ddf6b8781673cdc7b960c475c1bebb6fd1ecd1aff55660edd586bb`;
- V17 shared-core SHA-256:
  `171219b2ba3fae316cada714f72af145ffac3af0865f017dbcec01d745112ea7`.

Qualification passed with exact native parity, repeat parity, zero-strength
parity, and activation/no-intervention prompt identity. Fit and tune probe
accuracy were both `1.0`. The selected configuration was site `10`, strength
`0.5`, layer `11`.

The sealed assessment contained 48 rows, with 32 activation-versus-none rows
scored by the probe. Probe accuracy was `1.0`; the model's unchanged V22 report
accuracy on the same activation-versus-none assessment was `0.34375`. The
observed fork margin was `0.65625`. The concept bootstrap interval was
`[0.5, 0.5]` for the mean-over-chance quantity. The independent validator
classified the bundle as `InformationPresenceReportGapObserved`.

External artifact root:
`/tmp/astral-v25-preflight-1786387151`.

The configuration-lock digest is
`0a535b9c65a7672b03a9474203d2763998f6ebc15107ce9a3a5d3a780b3b5848`.
The final manifest digest is
`cf22b02d5b4b3ff4fc09c8a24405c09895e8329d871bf2cf9437f6a5c9472e87`.
The independent validator returned `valid: true`.

## Interpretation and ceiling

This is a single cached-checkpoint, single-runtime, local development result
for a preregistered linear residual probe and a fixed report wrapper. It supports
the bounded observation that the selected residual representation carried a
linearly decodable activation-versus-none signal on the identical assessment
trials while the model's report did not decode that signal. It does not
establish a general information-presence theorem, faithful self-report failure
in other models, mechanistic understanding, introspection, consciousness,
sentience, agency, semantic correctness, safety, benchmark performance,
production readiness, SOTA, independent replication, or accepted Evidence
Ledger evidence.

Claim ceiling remains
`LocalDevelopmentPrivilegedTelemetryInformationPresence`. No Stage 0C
confirmation or Stage 1 authorization is created. The V25 concept set,
configuration, and assessment are not to be adaptively retuned or reused as a
future confirmation without a new preregistered identity and independent review.

## Validation

```text
python -m pytest -q experiments/astral_fsm/tests tools/astral-hybrid-instrument-v24/tests tools/astral-telemetry-probe-v25/tests  # 37 passed
python tools/astral-telemetry-probe-v25/validator_v25.py /tmp/astral-v25-preflight-1786387151  # valid: true
```
