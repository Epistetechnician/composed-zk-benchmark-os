# MiniMind domain-specific continual-learning protocol V2

State slice: `continual-learning-minimind-domain-specific-v2`.

## Fresh boundary

V2 is a fresh continuation after V1's independent `REJECT`. It does not
import V1's synthetic corpus, result, model output, review, or execution
artifacts. The upstream MiniMind dependency is pinned to commit
`7a6fddd63a30c06b2fdd5fac4089922b29bc841b` in a new clean external checkout.
The source URL, remote, Apache-2.0 license text, commit, required-file roster,
cleanliness, byte lengths, and file digests are verified from that checkout.

## Scientific object

The object is a randomly initialized small dense MiniMind model exposed to an
ordered sequence of three fresh domains: `materials`, `clinical`, and
`finance`. Every domain has document-disjoint `fit`, `tune`, and `assessment`
JSONL files with non-empty `text` records. The fixed arms are untouched,
joint-oracle, sequential full update, cumulative LoRA, fixed replay, and
independent per-domain adapters.

The primary endpoint is final macro-average held-out BPB improvement relative
to the untouched base. Tune selects the arm by mean final BPB; assessment is
not started until the tune lock is computed and recorded. Forward and reverse
orders, three replicate seeds, and three order seeds are fixed. The full
factorial contains 108 trials per execution phase.

## Fixed guards

The maximum prior-domain forgetting is `0.25`, maximum forward/reverse order
delta is `0.20`, and maximum checkpoint restoration absolute error is `1e-12`.
Zero attrition, exact domain/split/seed/order rosters, equal padded-token
budget, deterministic repeatability, complete stage coverage, and aggregate-
only output are mandatory. A checkpoint is serialized in memory, loaded into a
freshly recreated model instance, compared, and then restored into the live
model; restoring a snapshot directly into itself is not sufficient.

## Execution and custody

Synthetic execution is offline and has claim ceiling
`LocalDevelopmentMiniMindDomainSequenceSyntheticOnly`.

Model execution is sealed until a fresh JSON-only packet-bound Ed25519 receipt
verifies the complete seven-file digest set, identifies an independent
reviewer distinct from the operator, and sets disposition
`ACCEPTED_FOR_MODEL_EXECUTION`. The runner checks that receipt before importing
MiniMind or loading a model, sets Hugging Face offline flags, requires an
external corpus and output root, creates the output root with mode `0700`, and
retains only aggregate contract metrics.

Execution phases are fixed as `fit`, `tune`, explicit `prediction_lock`, then
`assessment`. The assessment phase cannot begin until the tune lock is
computed. Repeatability is checked by rerunning each model trial with the same
identity and comparing canonical trial bytes.

No provider call, paid compute, network model/data acquisition, production
traffic, benchmark promotion, Evidence Ledger mutation, or stronger claim is
authorized by this protocol.

## Claim ceiling

The V2 synthetic result is capped at
`LocalDevelopmentMiniMindDomainSequenceSyntheticOnly`. A model-bearing run,
if independently accepted and all fixed gates pass, may claim no more than
`LocalDevelopmentMiniMindDomainSequenceQualificationV2`; it cannot establish
general continual-learning superiority, production readiness, or benchmark
evidence.

Every mutation in this phase names state slice
`continual-learning-minimind-domain-specific-v2`.
