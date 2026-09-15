# Gemma 3 paper-shaped recirculation V3 development protocol

State slice: `gemma3-paper-recirculation-schema-resolution-v3-development`

Protocol identity: `gemma3-paper-recirculation-schema-resolution-v3-development`

Status: `PENDING_INDEPENDENT_REVIEW / ScientificExecutionClosed`

## Scope

This is an additive engineering continuation of the synthetic V2 dry-run. It
tests only deterministic search/abstraction policy behavior and the semantic
oracle. The isolated mutable target is
`.weco/gemma3-paper-recirculation-v3-development/optimize.py`.

The scientific V1 target, external corpus, model, layer roster, alpha, beta,
assessment endpoint, and provider execution remain out of scope. The V2
synthetic fixtures and oracle are frozen inputs, not scientific evidence.

## Frozen contract

- The oracle must pass before the policy is scored.
- Logits, NLL, recurrence state, throughput metadata, duplicate identifiers,
  assessment leakage, malformed digests, semantic drift, and duplicate JSON
  keys remain fail-closed checks.
- Only `optimize.py` in the isolated lane may be changed by a future Weco
  dry-run.
- The metric is synthetic `policy_score`, maximized at fixed task definitions.
- Provider execution, network access, external acquisition, model execution,
  assessment, spending, and publication are prohibited.

## Bound inputs

| Input | SHA-256 |
| --- | --- |
| `experiments/continual_learning/gemma3_paper_recirculation_development_v2.py` | `8245bef75cc534675ed9da049f16b7d9f3ea4270ce99d00c0d538eeda49ec913` |
| `experiments/continual_learning/fixtures/gemma3_recirculation_v2_reference.json` | `d409816c3131fe287dcf1c7e66e781246379a146ef9328599f31244835d1a54e` |
| `experiments/continual_learning/fixtures/gemma3_recirculation_v2_candidate.json` | `697c79e0e028bd0cc88af7a184c6c6f88dee36b1427f3ee9e59c6aff03759e23` |
| `experiments/continual_learning/tests/test_gemma3_paper_recirculation_development_v2.py` | `fefa60670e9b288eba141de99d37ab992406732b2ef3ca47a6b491cf95cbf477` |

## Exit and claim ceiling

The exit is a deterministic local receipt plus a reviewable packet. A passing
dry-run is capped at
`LocalDevelopmentGemma3PaperRecirculationEngineeringV3`. It is not a model
throughput result, a corpus validation, a provider result, or a scientific
claim. Applying any candidate requires a separate review and fresh
confirmation.
