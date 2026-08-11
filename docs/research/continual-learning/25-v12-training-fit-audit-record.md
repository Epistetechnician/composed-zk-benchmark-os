# V12 training-fit audit record

State slice: `continual-learning-protocol-v12-training-fit-audit`.

Classification: `TrainingFitAuditNoBreakthroughClaim`.

Claim ceiling: `LocalDevelopmentTrainingFitAudit`.

## Scope

V12 audited the accepted V11 artifact without retraining. It checked whether
the failure was caused by missing replay examples, prompt/completion mismatch,
label tokenization, adapter fit, or hardware capacity.

Accepted source artifact:

`/tmp/continual-learning-model-v11-qwen-seed20260810-order0123`.

Audit report:

`/tmp/continual-learning-model-v12-training-fit-audit/report.json`.

No model weights or source artifact were changed. No replication, second model,
or H100 was used.

## Findings

| check | result |
| --- | --- |
| update datasets checked | 12 |
| training rows checked | 384 |
| exact prompt/completion parity | passed |
| labels A/B/C/D single-token supervision | passed |
| final naive task-0 training fit | 4/8 (0.50) |
| task-0 bank training fit | 2/8 (0.25) |
| maximum reported peak memory | 0.764 GB |
| fit floor, required 6/8 for both | failed |

All 12 training receipts contained final weights, and the audit recorded final
train/validation loss values. The data and token supervision boundaries are
valid. The adapters themselves do not reliably fit the supervised codebook, so
retention comparisons are not yet interpretable as memory improvements.

Validator result:

```text
valid: true
fit_floor_passed: false
prompt_completion_parity: true
single_token_label_supervision: true
training_receipts_complete: true
```

Hashes:

```text
source_manifest_sha256: 9cb5803ae00fb5a1e3e2736f011de33b61de567207fdfb64a10859953e5a4f27
report_sha256:          f04152a1fdf11c2f5164803367d01b83f824bcc07ac9fd35f41f80c1039d1bd4
```

## Decision

Stop V12. Do not run another replay or adapter-bank preflight and do not
provision an H100. The next research object is
`v13-training-objective-repair`: change only the optimization/training
objective or adapter-fit configuration, require both naive and bank training
accuracy to reach `6/8`, and run no retention comparison unless that fit floor
passes. Hardware is irrelevant until the fit floor passes and runtime or memory
is measured as the remaining constraint.
