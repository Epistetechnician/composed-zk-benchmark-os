# Adaptive verification with reversible adapters v2 independent review

Date: 2026-08-28.

State slice: `continual-learning-adaptive-verification-reversible-adapter-v2`.

Reviewer role: separate worker.

Reviewed protocol: `docs/research/continual-learning/89-adaptive-verification-reversible-adapter-v2-protocol.md`.

Reviewed protocol SHA-256:
`1df7880fdb8c883385261cf5680058979301bb06af2c58904dba185cfe1ea4f2`.

## Verdict

`REJECT`

The protocol remains insufficiently executable for implementation or model
execution.

## Findings

- `matched_energy` names six documents while selection is over twelve fit
  documents.
- The window contract permits 224--255-token windows despite describing fixed
  length, so equal compute is undefined.
- Training serialization and the effect of `mask_prompt=true` are unspecified.
- Assessment NLL scope, protected-fit scope, and adaptive-win definition are
  undefined.
- Shuffle ordering, order hashing, bootstrap sampling, and replicate indexing
  are not exact.
- The power data-generating process omits distributions and sampling details;
  its bootstrap count conflicts with the primary gate; and its alternative is
  exactly the decision threshold.
- The validator is asked to verify normalized-text digests while forbidden to
  read normalized text, making independent verification impossible.
- Write-once files conflict with changing `assessment_started`; event and
  retention schemas are absent.
- Prediction-lock contents and prediction procedure are undefined.
- No explicit adapter unload/rollback parity gate establishes reversibility.
- H100 equivalence tolerances and provider-repetition incorporation are
  undefined.
- Qualification-failure classification and mechanical network-isolation
  evidence are unspecified.

```yaml
state_slice: continual-learning-adaptive-verification-reversible-adapter-v2
reviewed_protocol_path: docs/research/continual-learning/89-adaptive-verification-reversible-adapter-v2-protocol.md
reviewed_protocol_sha256: 1df7880fdb8c883385261cf5680058979301bb06af2c58904dba185cfe1ea4f2
reviewer_role: separate-worker
verdict: REJECT
execution_authorized: false
review_date: 2026-08-28
```
