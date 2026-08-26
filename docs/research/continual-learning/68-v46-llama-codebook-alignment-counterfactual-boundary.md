# V46 Llama target-codebook alignment counterfactual boundary

State slice: `continual-learning-llama-codebook-alignment-counterfactual-v46`  
Protocol: `v46-llama-codebook-alignment-counterfactual-v1`  
Claim ceiling: `LocalDevelopmentCodebookAlignmentCounterfactualDiagnosis`

## Purpose

V46 is the narrowest follow-up to the V45 diagnosis. It tests whether the V44
Llama task-0 constant readout is associated with the identity codebook rather
than with the model, optimizer, task budget, route prompt, or artifact path.
It changes exactly one declared factor: the target task's codebook shift.

V46 is diagnostic only. It cannot establish a continual-learning capability,
generalize beyond the frozen task family, promote V44, or authorize provider
or production execution.

## Frozen counterfactual contract

- Cached model: `Llama-3.2-1B-Instruct-4bit`.
- Fresh paired task seeds: `20260865`, `20260866`, and `20260867`.
- Fixed optimizer seed base: `20260856`, retained from V44 as a control.
- Canonical task order: `0123`.
- 160 iterations, 32 update rows, AdamW, batch size `2`, eight layers, and
  maximum sequence length `192`.
- Each seed produces two arms in separate subprocesses:
  `identity-target` uses target shift `0`, while `matched-shift-target` uses
  the preregistered target shift `1`, equal to task 1's non-identity shift.
- Non-target task mappings, task tokens, prompt bytes, split policy, and
  training/assessment schedule remain unchanged between paired arms.
- The two arms bind identical underlying `(left, right, residue, split)` facts
  with a paired-fact digest. Only the target mapping and resulting completion
  labels differ.
- Each arm trains a fresh adapter from the frozen base. No V44 adapter,
  result, seed, or assessment payload is reused.

## Primary metric and interpretation

The primary metric is the paired target held-out accuracy delta:

`matched-shift-target accuracy - identity-target accuracy`.

The counterfactual supports a codebook-alignment diagnosis only when all six
arms are structurally valid, every paired-fact digest matches, every arm is
independently validated, every delta is non-negative, and the median delta is
at least `0.25` (two of eight target held-out facts). A negative or mixed
pattern is reported as evidence against or insufficient for the diagnosis;
it is never relabeled as a positive learning result.

## Custody and stop rules

Artifacts must be repository-external, immutable, digest-bound, and validated
by an independent process. Prediction outputs are sealed before assessment
effects are summarized. Any pair mismatch, route leakage, malformed receipt,
failed validator, or unexpected arm count stops the slice. Retention and order
retention are not executed by V46.

V46 permits no downloads, network access, adaptive tuning, seed mining,
provider calls, production traffic, accepted Evidence Ledger mutation, or
claims above `LocalDevelopmentCodebookAlignmentCounterfactualDiagnosis`.
The docs-first boundary creates no model run and no scientific evidence.

