# Adaptive verification with reversible adapters v1 review packet

Date: 2026-08-28.

State slice: `continual-learning-adaptive-verification-reversible-adapter-v1`.

Status: `ReviewPending / ExecutionUnauthorized`.

## Frozen review input

The reviewer receives only the protocol below and may not edit it while review
is open:

```yaml
protocol_path: docs/research/continual-learning/85-adaptive-verification-reversible-adapter-v1-protocol.md
protocol_sha256: a7abfa2f1b2d1edd1113824334850f090125e4efa8cb990ca45ad15a6316d14d
state_slice: continual-learning-adaptive-verification-reversible-adapter-v1
```

The V2 and V3 records may be consulted only as cited prior evidence and may
not be consumed as model, corpus, adapter, activation, result, or assessment
inputs. V48 Astral artifacts remain excluded.

## Required independent verdict

The reviewer must verify:

- theory and estimand are narrower than the rejected Astral theory;
- model, runtime, adapter, corpus, and custody contract is executable;
- the exact primary effect threshold is fixed before assessment;
- uncertainty, missingness, and multiplicity rules are explicit;
- the power and reliability plan is executable and has a stop rule;
- all control arms and falsifiers are fixed;
- equal learner compute and separate controller overhead are measurable;
- prediction-lock ordering prevents assessment leakage;
- aggregate-only retention and external custody are enforceable;
- the runner/validator separation and validator behavior are testable;
- H100/GiveMeANode use cannot alter the sealed scientific contract;
- the claim ceiling and terminal failure rules are narrow;
- V48, V82, and prior scientific artifacts remain excluded.

The receipt must contain:

```yaml
state_slice: continual-learning-adaptive-verification-reversible-adapter-v1
reviewed_protocol_path: docs/research/continual-learning/85-adaptive-verification-reversible-adapter-v1-protocol.md
reviewed_protocol_sha256: a7abfa2f1b2d1edd1113824334850f090125e4efa8cb990ca45ad15a6316d14d
reviewer_role: separate-worker
verdict: ACCEPT or REJECT
findings: []
execution_authorized: false
review_date: 2026-08-28
```

`REJECT` closes this slice before implementation. `ACCEPT` permits
implementation-contract drafting only. It does not authorize model loading,
corpus acquisition, assessment, or provider/H100 work.
