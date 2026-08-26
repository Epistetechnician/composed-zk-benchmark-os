# V27 routed adapter-bank failure diagnosis

State slice: `continual-learning-diagnosis-task-routed-adapter-bank-v27`.

## Finding

The Llama replication failure is target-task non-acquisition, not catastrophic
forgetting. All three V27 cases were structurally valid and independently
validated, but the target T0 adapter failed to learn the per-fact mapping in
both its training and held-out readouts:

| case | T0 train output | T0 train accuracy | T0 held-out accuracy |
| :--- | :--- | ---: | ---: |
| `20260850/0,3,2,1` | `C C C C C C C C` | `2/8` | `2/8` |
| `20260851/0,2,3,1` | `B B B B B B B B` | `2/8` | `2/8` |
| `20260852/0,1,3,2` | `D D D D D D D D` | `2/8` | `2/8` |

The broader all-task audit found constant-output collapse for every adapter in
the first two cases. In the third case, T3 reached `6/8` on both train and
held-out facts, while T0 still remained a constant `2/8` adapter. This does
not change the replication decision because T0 is the preregistered target.

The V26 Qwen target adapter, under the same route-bound prompt and data
contract, reached `8/8` train and held-out accuracy for task T0. Therefore the
V27 result does not identify interference between adapters: the Llama adapter
does not acquire the per-fact residue-to-label mapping in the first place.

The Llama training logs show falling validation loss into approximately
`0.47`--`0.51`, while exact choice readout remains constant. This is evidence
of an objective/readout mismatch or insufficiently discriminative adaptation
for this model and prompt—not evidence that the adapter bank preserved or
forgot the task. The distinction is diagnostic, not a promoted scientific
claim.

## Guardrail added

`diagnose_routed_adapter_bank_replication_v27.py` performs a read-only
all-task train/held-out audit against sealed artifacts. It runs inference only,
revalidates each V27 case, records output histograms, and separately classifies
target-task non-acquisition from broader adapter collapse. It cannot modify
adapters or promote evidence. Its external report is at
`/tmp/continual-learning-diagnosis-v27-20260820-r2/diagnosis.json`.

## Next boundary

The next candidate must add a model-eligibility acquisition preflight before
any retention or interference comparison: every task adapter must exceed the
no-update baseline on its own training split, and the exact choice readout
must be checked independently of aggregate loss. Until that preflight is
specified and passed, no new seed mining, adaptive tuning, provider call, or
production claim is authorized.

Claim ceiling: `LocalDevelopmentTaskRoutedAdapterBankFailureDiagnosis`.
