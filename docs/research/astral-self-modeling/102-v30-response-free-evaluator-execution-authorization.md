# V30 Response-Free Evaluator Execution Authorization

State slice: `astral-rgs-v30-response-free-evaluator-execution`.

Status: `AuthorizedOnce / NotRun`.

The single authorized identity binds RGS
`b8bfed6073d927e82c903a825fc3239fb1209c93`, Astral
`b2ba7c66402a59b1e441b9d76e7df4e55168bcda`, the frozen checkpoint and
tokenizer hashes, the public fixture, exactly two isolated model processes, and
128 prompt forwards. The coordinator must claim an exclusive external ledger
before model access and must retain failures.

The artifact must contain raw positive/null scores, exact derived observations,
model and runtime inventories, process records, source snapshots, manifest,
packet, and a model-free independent Astral validation report.

No retry, training, adapter, candidate corpus, acquisition, assessment,
threshold change, SOTA, breakthrough, or claim above
`LocalResponseFreeEvaluatorQualificationV30` is authorized.
