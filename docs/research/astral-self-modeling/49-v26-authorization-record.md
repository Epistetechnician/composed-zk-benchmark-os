# V26 Authorization Record

State slice: `astral-causal-channel-separation-v26-authorization`.

Date: 2026-08-13.

## Authorized slice

The user authorized the next bounded action after the V26 recommendation:

- write the V26 protocol specification;
- record the authorization boundary and review obligations;
- update Astral navigation and the future-experiment cross-reference;
- run documentation and claim-boundary validation.

This is a protocol-and-preflight authorization. It authorizes offline actor
inventory only; it does not authorize model execution, checkpoint loading,
network access, provider/API probing, assessment artifact generation, V25
reuse, accepted Evidence Ledger mutation, Stage 0C confirmation, or Stage 1.

## Protocol identity

- protocol: `astral-causal-channel-separation-v26`;
- primary state slice: `astral-causal-channel-separation-v26-protocol`;
- authorization state slice: `astral-causal-channel-separation-v26-authorization`;
- status: `PreflightStoppedNoFreshActor / ScientificExecutionNotAuthorized`;
- claim ceiling: `LocalDevelopmentCausalChannelSeparationDesignOnly`;
- protocol document: [V26 causal-channel separation](48-causal-channel-separation-v26.md).
- preflight: `tools/astral-causal-channel-separation-v26/preflight_v26.py`;
- independent preflight validator:
  `tools/astral-causal-channel-separation-v26/validator_v26.py`;
- runtime-surface audit:
  `tools/astral-causal-channel-separation-v26/runtime_surface_v26.py`;
- stop record: [V26 execution preflight stop](50-v26-execution-preflight-stop-2026-08-13.md).

## Review checklist

- [x] Directly measured intervention effect is the causal target.
- [x] Report-only, opaque-artifact, telemetry, and shuffled controls are
  explicitly separated.
- [x] The S005-informed report endpoint scores the first structured decision
  before later narrative and preserves exact-text, unrelated-intervention, and
  report-order controls.
- [x] Later phenomenological or mechanistic report language is unverified
  metadata and cannot become a causal label, target feature, or H26-A gate.
- [x] The opaque artifact is labeled as a synthetic proxy, not provider
  evidence or a cryptographic reproduction.
- [x] V25 concepts, rows, sites, strengths, configuration, predictions, and
  artifacts are excluded by protocol.
- [x] No raw reasoning traces, credentials, PII, signatures, or provider
  artifacts are authorized for retention.
- [x] Assessment predictions must be locked before assessment effects exist.
- [x] Positive and null claim ceilings are explicit.
- [x] Stage 0C, Stage 1, benchmark, production, consciousness, and general
  introspection claims remain unavailable.
- [x] No accepted Evidence Ledger mutation is authorized.
- [x] Actual local inventory returned `NoFreshActor` with zero eligible actors.
- [x] The stop was recorded without loading a model or opening assessment data.

## Transition gate for future execution

Execution may begin only after a new authorization record names:

1. the exact runner and validator paths;
2. the fresh actor identity and inventory digest;
3. the external artifact directory and retention policy;
4. the sealed configuration and protocol digest;
5. the exact preflight and validation commands;
6. the reviewer and disposition path for positive, null, and stop outcomes.

Until then, V26 is a protocol design, not an experiment result.
