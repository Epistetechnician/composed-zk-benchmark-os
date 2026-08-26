# V27 second-model routed adapter-bank replication

Status: `ProspectiveLocalDevelopmentTaskRoutedAdapterBankReplication`.

State slice: `continual-learning-replication-task-routed-adapter-bank-v27`.

## Purpose

V27 tests whether the V26 task-routed adapter-bank candidate survives a
second eligible cached model. It does not alter the route contract, prompt,
task construction, held-out split, optimizer, update budget, or candidate
gates. The only scientific change is the model identity.

## Frozen replication contract

- Cached `Llama-3.2-1B-Instruct-4bit`, selected only after the offline runtime
  seam accepted it and bound its model manifest.
- Four tasks; eight train and eight disjoint held-out facts per task; two per
  modular residue in each split.
- Exact V26 route-bound residue-only prompt, with raw compositional pair
  absent and training/assessment prompt bytes identical.
- 160 LoRA iterations, 32 rows/update, AdamW `0.0001`, batch size `2`, eight
  layers, maximum sequence length `192`.
- Fresh seeds and task orders: `20260850/0,3,2,1`, `20260851/0,2,3,1`, and
  `20260852/0,1,3,2`.
- The V26 Qwen checkpoint is explicitly excluded. Every case is executed in
  its own subprocess and read back by an independent validator subprocess.

## Gates and nonclaims

Every case must pass the four V26 gates: retrieval above no-update,
routed-bank acquisition above no-update, routed-bank retention above shared
naive retention, and routed-bank held-out retention at least `6/8`.

A passing campaign supports only
`LocalDevelopmentTaskRoutedAdapterBankReplication`. It does not establish
general continual-learning ability, provider execution, production
readiness, or a breakthrough claim. A failed or invalid case stops the
campaign and prevents replication promotion.
