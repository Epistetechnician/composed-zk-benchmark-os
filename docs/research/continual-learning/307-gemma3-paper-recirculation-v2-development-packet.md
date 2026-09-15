# Gemma 3 paper-shaped recirculation V2 development packet

State slice: `gemma3-paper-recirculation-schema-resolution-v2-development`

Packet status: `DevelopmentPass / ScientificExecutionClosed`

## Result

The synthetic semantic oracle passed the frozen reference/candidate pair.
The adversarial suite passed eight tests. The local Weco-compatible dry-run
selected `composed, typed, hybrid` and achieved `policy_score=1.0`.

This is an engineering result only. No Gemma model, external corpus, provider,
assessment panel, or scientific Weco optimization was used.

## Frozen fixtures

The oracle requires exact parity for logits, NLL, and recurrence state, plus
exact parity for throughput protocol metadata. Throughput itself is measured
from three deterministic timing samples and may improve only when recomputed
from those samples.

| Artifact | SHA-256 |
| --- | --- |
| Development harness | `8245bef75cc534675ed9da049f16b7d9f3ea4270ce99d00c0d538eeda49ec913` |
| Reference fixture | `d409816c3131fe287dcf1c7e66e781246379a146ef9328599f31244835d1a54e` |
| Candidate fixture | `697c79e0e028bd0cc88af7a184c6c6f88dee36b1427f3ee9e59c6aff03759e23` |
| Focused tests | `fefa60670e9b288eba141de99d37ab992406732b2ef3ca47a6b491cf95cbf477` |

The reference measured `100.0` windows/second. The candidate measured `125.0`
windows/second while preserving all semantic fields and the fixed measurement
contract.

## Adversarial coverage

The focused tests fail closed on:

- fabricated throughput not reproducible from timing samples;
- duplicate discovery identifiers;
- assessment-row leakage;
- malformed fixture digests;
- semantic drift in logits, NLL, or recurrence state;
- duplicate JSON keys.

Every receipt is canonicalized and hashed. The passing receipt is
`ad204152ec1ed7fedc3f97b63966697d962386b80924c34cfd537f77d6e6f40c`.

## Weco dry-run boundary

The isolated lane is
`.weco/gemma3-paper-recirculation-v2-development/`. It has one mutable target,
`optimize.py`, and an evaluator that runs the tracked semantic oracle before
scoring the synthetic search policy. The local command passed:

```text
policy_score: 1.000000000
oracle_status: PASS
selected_ids: composed,typed,hybrid
```

The Weco provider loop was not launched because the active development contract
allows only local Weco-compatible dry-runs and prohibits provider calls.

## Reproduction

```text
PYTHONDONTWRITEBYTECODE=1 ./scripts/python -B -m pytest -q experiments/continual_learning/tests/test_gemma3_paper_recirculation_development_v2.py
.weco/gemma3-paper-recirculation-v2-development/evaluate-gated.sh
```

## Claim ceiling and next gate

The maximum claim is
`LocalDevelopmentGemma3PaperRecirculationEngineeringV2`. This packet does not
authorize external corpus acquisition, model execution against the V2 panel,
provider calls, spending, assessment, publication, or Evidence Ledger
mutation. Those remain governed by protocol V2 and its independent review
requirement.
