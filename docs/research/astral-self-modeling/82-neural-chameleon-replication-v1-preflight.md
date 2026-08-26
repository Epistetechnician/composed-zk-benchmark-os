# Neural Chameleon replication V1 — custody preflight

State slice: `astral-neural-chameleon-replication-v1-preflight`.

Status: `Implemented / MissingRequiredArtifact / ScientificExecutionNotAuthorized`.

## Purpose

This slice prepares a faithful, claim-bounded recreation of the two linked
experiments:

1. test whether a Neural Chameleon trained to evade linear activation monitors
   also degrades an activation oracle; and
2. perform bounded causal-mechanistic diagnostics of one released chameleon with teacher-forced causal
   activation transplants, per-head attribution, residual geometry, and Q/K/V
   source-side transplants.

These are separate arms. The oracle arm evaluates monitor robustness. The
mechanistic arm diagnoses one checkpoint's monitor-evasion behavior. Neither
arm is an introspection, consciousness, or general-monitor claim.

## Source records

The study split and replication boundary are grounded in the supplied
descriptions: [the activation-oracle report](https://www.lesswrong.com/posts/wfGYMbr4AMcH2Rv68/neural-chameleons-can-t-hide-from-activation-oracles-1)
and [the mechanistic Neural Chameleon analysis](https://www.jacksonmowattgok.com/inside-neural-chameleon).
The released implementation reference is the
[neural-chameleon-circuit repository](https://github.com/jacksonhmg/neural-chameleon-circuit).
The primary paper and separate oracle implementation reference are
[Neural Chameleons](https://arxiv.org/html/2512.11949v1) and the
[activation-oracle repository](https://github.com/ceselder/neural_chameleons_activation_oracles).
These sources define replication inputs and hypotheses; they are not
repository-generated evidence.

## Required external artifacts

The operator must supply one immutable, repository-external artifact root with
an `artifact-manifest.json` declaring exactly:

- the trained chameleon checkpoint;
- its precursor/base checkpoint for weight-level hybridization;
- the activation-oracle checkpoint and tokenizer/runtime metadata;
- the released linear monitor weights and evaluator metadata;
- separate frozen oracle and mechanistic corpus panels;
- the exact runtime and source manifest.

Every role binds a complete canonical POSIX file set, role kind, role digest,
per-file byte lengths, and lowercase SHA-256 values. The manifest also binds
arm-specific endpoint formulas, controls, sample counts, prediction-lock
requirements, model/tokenizer/source provenance, monitor calibration, corpus
split digests, and freshness exclusions. The root is subject to a complete
file census, ancestor and in-root symlink rejection, safe-relative path checks,
stable-descriptor digest recomputation, and repository-external path checks.
Raw prompts, activations, logits,
transcripts, credentials, PII, and signatures do not enter the preflight
result or a retained repository artifact.

## Frozen execution shape after artifact acceptance

The future execution slice must be separately authorized and must implement the
following order:

1. verify model, tokenizer, monitor, corpus, and runtime provenance;
2. establish native-versus-controlled parity, deterministic repeat, and
   teacher-forced same-response parity;
3. reproduce trigger-dependent linear-monitor suppression with output/capability
   controls;
4. evaluate activation-oracle robustness using a locked scoring rule, with
   oracle false-positive and false-negative diagnostics kept separate from the
   linear-monitor endpoint;
5. localize the causal effect by residual boundary, attention head, MLP, and
   selected group using reciprocal rescue and induction transplants;
6. test route sensitivity, radial versus tangential decomposition, and
   concept/response-position prototype reconstruction;
7. run the Q/K/V factorial under teacher forcing and the precursor/chameleon
   weight-hybridization comparison;
8. lock all assessment predictions before generating assessment effects;
9. retain only aggregate metrics, uncertainty intervals, digests, stop codes,
   and independent validation receipts.

The mechanism arm must remain explicitly scoped to the exact checkpoint and
monitor family. A Qwen3.6 adaptation would be a new study, not a replication
of the Gemma result.

## Current stop

The local cache contains Qwen, Llama, Nemotron, and Qwen3.6 artifacts, but no
Gemma Neural Chameleon checkpoint, precursor pair, or activation-oracle bundle.
The V38 Qwen3.6 seam proves only bounded layer capture/replacement and is not a
per-head/Q/K/V transplant instrument. Until the required external artifact
manifest is supplied and a successor execution authorization names the runner,
validator, retention root, frozen corpus, and claim ceiling, this slice stops
at `MissingRequiredArtifact` and does not load a checkpoint.

The expected local stop for the cached Qwen3.6 directory is
`MissingRequiredArtifact` with reason `artifact_manifest_missing`: zero
verified artifact roles, `model_execution=false`, `model_training=false`,
`network_access=false`, and `assessment_opened=false`. This note does not
present that local cache observation as a persisted scientific receipt.

## Successor authorization minimum

A later execution authorization must name exact runner and validator source
digests, the external immutable retention root, actor/artifact digests, exact
offline command lines, arm-specific stop codes, fit/tune/assessment split
digests, the prediction-lock artifact and ordering rule, raw-payload policy,
claim ceiling, and the independent validator command. Authorization must also
state that neither arm may select, unlock, or contribute evidence to the other.
This preflight does not create that authorization.

## Claim ceiling

The maximum current claim is:

> The repository contains a fail-closed, digest-bound preflight contract for a
> future local Neural Chameleon replication; no scientific replication result
> has been generated.

This slice does not authorize network access, downloads, model training,
assessment execution, accepted Evidence Ledger mutation, benchmark evidence,
provider claims, introspection, self-modeling, consciousness, or production
monitoring claims.
