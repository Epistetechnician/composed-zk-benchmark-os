# MiniMind domain-specific continual-learning protocol V3

State slice: `continual-learning-minimind-domain-specific-v3`.

## Boundary

V3 is a fresh protocol identity after V2's independent `REJECT`. V1 and V2
source, corpus, synthetic, model, receipt, and review artifacts are historical
only and are not V3 scientific inputs. The upstream MiniMind checkout is
re-custodied at commit `7a6fddd63a30c06b2fdd5fac4089922b29bc841b` from
`https://github.com/jingyaogong/minimind` under a new external V3 path. Its
Apache-2.0 license, remote, clean status, required-file roster, byte lengths,
and file digests are checked from the checkout.

## Scientific object

The fixed object is a small dense MiniMind model exposed to the ordered domain
sequence `materials`, `clinical`, `finance`. The fixed arms are untouched,
joint oracle, sequential full update, sequential LoRA, sequential replay, and
independent domain adapters. The primary endpoint is final macro-average held-
out BPB improvement relative to the untouched base. Tune selects one arm by
mean final loss; assessment effects are not computed until the tune lock is
recorded. Three replicate seeds, three order seeds, forward/reverse order
pairs, and the exact arm/domain/split roster are fixed.

The synthetic factorial contains 108 aggregate trials: six arms, three
splits, three replicate/order-seed pairs, and two order directions. The model
campaign uses all arms for fit and tune and only the locked arm for assessment
to keep the offline campaign tiny while preserving the preassessment lock.

## Synthetic execution

Synthetic arithmetic is deterministic, in-memory, and offline. The writer
publishes only aggregate trial rows: identities, order, stage count, aggregate
losses, forgetting, checkpoint error, accounting, and Boolean hard guards. It
does not publish stage payloads, records, tokens, weights, gradients, or model
outputs. The independent validator recomputes the expected trial arithmetic
from the V3 constants and validates the exact 108-case roster.

The result root must be the exact external owner-only directory
`continual-learning-minimind-domain-specific-v3-synthetic-20260902` with mode
`0700` and exactly `source-manifest.json`, `contract.json`, and `result.json`.
Any symlink, extra file, repository path, prior V1/V2 root, wrong mode, schema
drift, nonfinite metric, missing guard, or altered digest rejects the artifact.

## Fresh corpus and custody

The model input is the external owner-only root
`continual-learning-minimind-domain-specific-v3-corpus-20260902`. Its manifest
has the fixed V3 schema and corpus identity, exact nine domain/split files,
file byte digests and lengths, positive record counts, and the global document
and author identity digests. Each JSONL record has exactly `document_id`,
`author_id`, and non-empty `text`. All document and author IDs are globally
disjoint across the nine files. The root and every path are rechecked before
model import. The explicit V1/V2 root exclusion set is part of the manifest
and is recomputed by both runner and validator; a prior-root path or known
prior digest cannot be relabeled as fresh.

## Independent authorization

The model runner must verify all of the following before importing MiniMind:

- current SHA-256 values for all seven frozen review files;
- the exact review packet and complete frozen digest map;
- the external V3 trust bundle fingerprint;
- a registry snapshot signed by the externally pinned review root;
- a reviewer certificate signed by that root and scoped to this state slice;
- reviewer identity/key resolution from that certificate, not from the receipt;
- a root-signed operator binding for the exact packet, runner audience, and
  single-use nonce;
- reviewer/operator key and principal separation;
- the exact fresh source manifest and corpus manifest digests;
- an Ed25519 signature over the complete execution receipt;
- disposition `ACCEPTED_FOR_MODEL_EXECUTION`.

The operator cannot self-sign, choose a reviewer public key, create a trusted
root, or replace the registry. The local verifier cannot prove human
non-collusion or the provenance of an external root; those remain explicit
external trust assumptions. Missing or unverifiable trust inputs fail closed.

## Model phases and output

The only allowed model phase order is `fit`, `tune`, `prediction_lock`,
`assessment`. The assessment phase receives a structured tune lock and cannot
be called without it. Every aggregate model trial must pass exact checkpoint
round-trip restoration through a recreated model instance, zero attrition,
equal padded-token budget, complete stage coverage, and deterministic rerun
comparison. The model output root is external, owner-only `0700`, and contains
only `contract.json`. The contract has an exact schema, exact non-empty Boolean
guard keys, receipt file digest/path, source and corpus bindings, phase lock,
aggregate trials, and recomputed contract digest.

No provider call, paid compute, network model/data acquisition, publication,
benchmark promotion, Evidence Ledger mutation, production traffic, or claim
above `LocalDevelopmentMiniMindDomainSequenceQualificationV3` is authorized.
The synthetic ceiling is
`LocalDevelopmentMiniMindDomainSequenceSyntheticOnly`. A passing model
contract is qualification evidence only, not general continual-learning
superiority.

Every mutation in this phase names state slice
`continual-learning-minimind-domain-specific-v3`.
