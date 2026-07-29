# V28R2 Powered Acquisition-Novelty Implementation Notes

State slice:
`astral-rgs-v28r2-powered-acquisition-novelty-implementation`.

Status: `ImplementationFrozen / OneShotCampaignConsumed /
NoveltyPacketCandidate / UpdateArmsNotAuthorized / AcquisitionNotTested`.

## Implemented boundary

The additive `tools/astral-rgs-acquisition-v28r2/` package implements the
independent intake side of the frozen V28R2 novelty campaign. It contains:

- the exact 1,536-family-per-kind power and protocol lock;
- a retired-V28R1 fingerprint builder that exports hashes and structural
  signatures without exporting V28R1 rows or model outcomes;
- a clean-room packet validator that does not import either RGS producer or
  the V28R1 implementation;
- a separate corpus-only entrypoint that must pass before tokenizer or model
  access;
- exact corpus, query, 24-permutation-block, prompt, token, score, argmax,
  process, parity, disjointness, and later-gate-absence checks;
- family-cluster equivalence intervals with the frozen critical value `5.0`
  and margin `[-0.05, 0.05]`; and
- hermetic positive and adversarial contract tests.

The validator accepts only exactly two complete unchanged-checkpoint baseline
runs. A valid packet can return `NoveltyPacketCandidate`, `CorpusNotNovel`, or
`Invalid`. A novelty candidate reaches only
`LocalModelBackedAcquisitionNoveltyPreflightV28R2`; it cannot authorize or
contain an update, retention/recovery, selector, or assessment result.

## Required execution order

No V28R2 seed or corpus may exist until both implementation repositories are
committed and clean. The operator must then create durable source, runtime,
checkpoint, tokenizer, protocol, generator, validator, power-profile, and
retired-fingerprint receipts; exclusively claim the one-shot ledger; create
one seed; generate and validate one corpus without model access; run one fresh
`pre_update` evaluator and one separately prepared and restarted `no_update`
evaluator; and submit the resulting immutable packet to this validator.

Any source dirtiness, ledger collision, generation error, fingerprint overlap,
corpus rejection, process failure, invalid packet, or `CorpusNotNovel` result
consumes and retires the campaign. There is no replacement seed or adaptive
repair path in this slice.

## Claim boundary

At its source freeze, this implementation was an unexecuted local research
instrument. The later bounded execution does not turn it into
a new corpus, acquisition evidence, continual-learning evidence, independent
replication, a benchmark result, a breakthrough, autonomous self-improvement,
introspection, self-modeling, Stage 0C or Stage 1 evidence, or production
evidence.

The later one-shot execution and bounded positive novelty result are recorded
in `66-v28r2-powered-acquisition-novelty-execution-record.md`. This file retains
the pre-execution implementation boundary.
