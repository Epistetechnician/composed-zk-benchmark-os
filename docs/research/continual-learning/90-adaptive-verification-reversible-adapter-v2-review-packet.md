# Adaptive verification with reversible adapters v2 review packet

Date: 2026-08-28.

State slice: `continual-learning-adaptive-verification-reversible-adapter-v2`.

Status: `ReviewPending / ExecutionUnauthorized`.

## Frozen input

The reviewer receives the following immutable protocol and may not edit it:

```yaml
protocol_path: docs/research/continual-learning/89-adaptive-verification-reversible-adapter-v2-protocol.md
protocol_sha256: 1df7880fdb8c883385261cf5680058979301bb06af2c58904dba185cfe1ea4f2
state_slice: continual-learning-adaptive-verification-reversible-adapter-v2
```

The reviewer may consult only the V2/V3 synthetic execution records as prior
context. They may not use prior model, corpus, adapter, activation, result, or
Astral artifacts as inputs.

## Required verdict

The reviewer must independently verify:

- the revised theory and document-level estimand;
- the exact surprisal, novelty, normalization, score, selection, and tie rules;
- the complete model, MLX-LM, LoRA, optimizer, seed, and order contract;
- the corpus URLs, normalization, split identity, and window construction;
- the aggregation hierarchy and deterministic bootstrap implementation;
- the explicit power data-generating process and reliability gates;
- the control arms, falsifiers, equal-compute rule, and no-retuning rule;
- the custody layout, raw-artifact retention/deletion policy, and validator
  independence;
- the prediction-lock event ordering and assessment-open gate;
- the H100/GiveMeANode equivalence boundary;
- the narrow classification and exclusion of Astral claims.

The receipt must contain:

```yaml
state_slice: continual-learning-adaptive-verification-reversible-adapter-v2
reviewed_protocol_path: docs/research/continual-learning/89-adaptive-verification-reversible-adapter-v2-protocol.md
reviewed_protocol_sha256: 1df7880fdb8c883385261cf5680058979301bb06af2c58904dba185cfe1ea4f2
reviewer_role: separate-worker
verdict: ACCEPT or REJECT
findings: []
execution_authorized: false
review_date: 2026-08-28
```

`REJECT` closes V2 before implementation. `ACCEPT` permits implementation-
contract drafting only; it does not authorize model loading, corpus
acquisition, adapter training, assessment, or provider/H100 use.
