# V42 Nemotron target-acquisition recovery record

State slice: `continual-learning-candidate-target160-nemotron-h-v42-recovery`  
Status: `ValidatedNegativeCandidateTrainingPolicyProvenanceIncomplete`  
Claim ceiling: `LocalDevelopmentModelAcquisitionEligibilityPreflight`

## Purpose

V42 closes the custody and assessment gap around a completed but unsealed
160-step target-only Nemotron adapter. It does not train another adapter. The
recovery tool validates the exact source files, frozen task, 32 update rows,
optimizer surface, completion log, final/checkpoint equality, cached model,
and model-config-derived tokenizer policy. It copies only admitted files into
a new repository-external root and performs three fresh isolated readouts:

1. frozen base on target training facts;
2. recovered adapter on target training facts; and
3. recovered adapter on disjoint target held-out facts.

The primary metric is adapter held-out accuracy. Eligibility also requires
adapter training accuracy above the no-update baseline, train and held-out
accuracy of at least `0.75`, and non-constant adapter training outputs.

## Canonical artifact

The superseding immutable receipt is stored at:

`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-nemotron-target160-recovery-v42-20260825-r2`

The independent validator returned `valid: true` with:

- source manifest SHA-256
  `e6887963fb44783980eced6e72fbf43d8f6828a1761e90ccb323ef242ea19147`;
- receipt SHA-256
  `e0078adf43cbda9939ac8a3b07637939b45496b4d460f438125e4c4876d7fa2a`;
- exact model manifest SHA-256
  `7138effca67d165d98179fa468057d04d560a8e34c9dfb3dc410004755cfed60`;
- 160 completed iterations and `8.933 GB` observed peak training memory;
- byte-identical final and iteration-160 adapters with SHA-256
  `797567587dc0db18f8ba048dcb4749792c109bab88444aa1d335da76a40afce7`;
- no-update target train accuracy `0.25`, with constant `A` output;
- adapter target train accuracy `0.25`, with constant `B` output; and
- adapter target held-out accuracy `0.25`, with constant `B` output.

All four acquisition gates are false. The output-class change shows that the
adapter affects the constrained readout, but it does not establish the frozen
residue-to-label discrimination. The candidate is ineligible and retention,
interference, provider, and production execution remain closed.

## Provenance boundary

Fresh V42 assessment is tokenizer-policy attested with
`fix_mistral_regex=true`. The recovered source training log proves 160-step
completion but predates the durable safe-wrapper policy receipt and contains
no `mlx_tokenizer_policy` event. Therefore the exact tokenizer policy used by
the original 160-step training invocation is not independently attestable
from the source artifact. The canonical receipt records
`source_training_tokenizer_policy_attested=false` and does not infer that fact
from the separately validated V22 training smoke.

The intermediate r1 recovery remains immutable but is superseded because it
did not make this provenance limitation machine-readable. No adaptive tuning,
threshold changes, seed mining, additional training, retention, provider, or
production work was performed.
