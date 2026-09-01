# Plasticity guard independent replication V2 protocol

Date: 2026-08-29.

State slice: `continual-learning-plasticity-guard-independent-replication-v2`.

Status: `PROTOCOL_REVIEW_REQUIRED / NO_ACQUISITION_NO_MODEL_EXECUTION`.

Claim ceiling: `LocalDevelopmentPlasticityGuardIndependentReplicationV2`.

## Purpose and terminal boundary

This is a fresh same-actor replication of the bounded Gemma3 plasticity-guard
result. Its single primary estimand is the held-out adaptation improvement of
the unchanged `plasticity_guard` arm minus the held-out adaptation improvement
of the unchanged `fixed_cadence` arm. The `no_update` arm is a matched compute
control for the possibility that rollback wins only by applying fewer updates.

This protocol does not reopen, repair, or consume scientific outputs from the
prior plasticity-guard V1, the contract-compiler V1-V3 slices, Astral, V82, or
the plasticity-recovery V1-V2 slices. No prior corpus, document, token window,
adapter, activation, metric, result, receipt, or external artifact is an
input. Source-level implementation helpers may be reused only when the exact
guard and model/runtime contract below remain unchanged; all run artifacts and
source digests are new V2 bindings.

The protocol author may not acquire data, load the model, train adapters,
create custody roots, call GiveMeANode, allocate H100s, or open assessment
before the independent review and the separate implementation authorization
described below.

Terminal classifications are `IndependentReplicationCandidate`,
`RollbackInfrastructureOnly`, `IndependentReplicationNoCandidate`, and
`QualificationFailure`. A positive result is local, actor-specific evidence
only. It does not establish general continual learning, architecture
generalization, neuroscience, Astral, Stage 0C, Stage 1, benchmark
superiority, or production readiness.

## Fixed actor and runtime

The only actor is the already-cached local checkpoint:

~~~text
model_name = gemma-3-1b-pt-bf16
model_path = /Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16
runtime = MLX 0.31.2 / MLX-LM 0.31.3 / Python 3.14.5
device = local Apple Metal device
network = forbidden during qualification, fit, tune, and assessment
model_download = forbidden
base_weight_update = false
adapter_merge = false
~~~

The model manifest is a recursively sorted list of regular non-symlink files,
each with repository-relative-to-model path, byte length, and SHA-256. The
manifest is captured before qualification and must match after assessment.
Runtime and source manifests are captured as exact bytes and bound into the
configuration digest. The runner sets `HF_HUB_OFFLINE=1` and
`TRANSFORMERS_OFFLINE=1`, rejects any network/process escape, and records no
credential or environment secret.

The implementation must invoke only the cached MLX/MLX-LM path already used by
the actor. It may not select another model, quantization, tokenizer, device,
runtime version, optimizer, learning rate, adapter rank, layer count, or
sequence length after review begins.

## Fresh Gutenberg corpus identity and custody

The fresh corpus identity is:

~~~text
gutenberg-plasticity-guard-independent-replication-v2-20260829
~~~

Acquisition occurs only after protocol review and implementation authorization.
The acquisition command downloads exactly these twelve Project Gutenberg plain
text sources, in the listed order, and no other source:

~~~text
gutenberg-74   https://www.gutenberg.org/cache/epub/74/pg74.txt
gutenberg-46   https://www.gutenberg.org/cache/epub/46/pg46.txt
gutenberg-98   https://www.gutenberg.org/cache/epub/98/pg98.txt
gutenberg-1260 https://www.gutenberg.org/cache/epub/1260/pg1260.txt
gutenberg-5200 https://www.gutenberg.org/cache/epub/5200/pg5200.txt
gutenberg-35   https://www.gutenberg.org/cache/epub/35/pg35.txt
gutenberg-36   https://www.gutenberg.org/cache/epub/36/pg36.txt
gutenberg-174  https://www.gutenberg.org/cache/epub/174/pg174.txt
gutenberg-768  https://www.gutenberg.org/cache/epub/768/pg768.txt
gutenberg-219  https://www.gutenberg.org/cache/epub/219/pg219.txt
gutenberg-215  https://www.gutenberg.org/cache/epub/215/pg215.txt
gutenberg-514  https://www.gutenberg.org/cache/epub/514/pg514.txt
~~~

The acquisition record stores each URL, HTTP response status, raw byte length,
raw SHA-256, and retrieval timestamp. The raw files are not copied into the
repository. The normalizer performs exactly these operations: strict UTF-8
decode; replace CRLF and CR with LF; Unicode NFKC; remove the first line whose
prefix is `*** START OF THE PROJECT GUTENBERG EBOOK`; remove the last line
whose prefix is `*** END OF THE PROJECT GUTENBERG EBOOK`; require both markers;
and preserve all remaining lines including their final newline. The normalized
text digest and byte length are recorded per document.

The twelve documents are fixed and document-disjoint by construction:

~~~yaml
fit: [gutenberg-74, gutenberg-46, gutenberg-98, gutenberg-1260,
      gutenberg-5200, gutenberg-35]
tune: [gutenberg-36, gutenberg-174, gutenberg-768]
assessment: [gutenberg-219, gutenberg-215, gutenberg-514]
~~~

No document may occur in more than one split. A document is eligible only if
the locked tokenizer produces at least 768 content tokens after normalization.
The single window for each document is tokens 512 through 767 inclusive,
encoded without special tokens. The decoded window must re-encode to the exact
same 256 token IDs. The tokenizer manifest and every source/token-window
digest are bound into the corpus manifest. The validator rejects duplicate
Gutenberg IDs, duplicate normalized digests, split overlap, short documents,
token round-trip changes, or any source outside the twelve-item allowlist.

Primary custody root:

`/Users/shaanp/Documents/research-artifacts/continual-learning-plasticity-guard-independent-replication-v2-20260829-primary`

Mirror custody root:

`/Users/shaanp/Documents/research-artifacts/continual-learning-plasticity-guard-independent-replication-v2-20260829-mirror`

Both roots must be absent before acquisition, must be regular directories
created by the V2 runner, and must remain outside the repository. The mirror is
written only from the sealed primary root after the primary validator passes;
the independent validator reads both roots and compares their complete file
manifests. A pre-existing root, symlink, repository path, missing mirror,
manifest mismatch, or source digest mismatch is a terminal custody failure.

## Fixed cases, arms, and unchanged guard

The fixed fresh case factorial crosses seeds `2801` and `2803` with these two
fit orders:

~~~text
forward = (0, 1, 2, 3, 4, 5)
riffle  = (0, 3, 1, 4, 2, 5)
~~~

These values are sealed before acquisition. Every case contains exactly three
arms:

1. `no_update`: execute the disposable shadow training budget but evaluate the
   untouched base and apply no adapter;
2. `fixed_cadence`: train and commit every candidate adapter;
3. `plasticity_guard`: train every candidate but commit only when the exact
   unchanged guard below accepts it.

Every arm attempts six fit updates. Every update uses the current 256-token
window repeated exactly four times, three LoRA iterations, batch size one,
four trainable layers, AdamW, learning rate `0.0001`, and maximum sequence
length 256. Candidate adapters are saved per update and never merged. The
`no_update` arm spends the same rows, iterations, layers, and batch size in a
disposable shadow adapter and never applies it.

The guard is copied as a fixed mathematical rule, with no retuning:

~~~text
current_gain = active_current_nll - candidate_current_nll
protected_delta = candidate_protected_nll - active_protected_nll
accept(step, current_gain, protected_delta) iff
    step == 0 OR
    (current_gain >= 0.001 AND protected_delta <= 0.010)
~~~

The protected set contains only previously committed fit windows. A rejection
leaves the active adapter pointer unchanged. Candidate evaluation still occurs
and its adapter digest, metrics, and rejection are retained in the external
raw run root. The guard implementation, thresholds, training command, and
adapter naming are fixed before source acquisition.

## Estimand, controls, and decision rules

For case `c` and arm `a`, define:

~~~text
adaptation_improvement(c,a) =
  base_assessment_mean_nll(c) - final_arm_assessment_mean_nll(c,a)
delta(c) = adaptation_improvement(c,plasticity_guard)
           - adaptation_improvement(c,fixed_cadence)
~~~

The primary estimand is the mean of `delta(c)` over the four fixed
seed/order cases. The primary candidate gate requires all of:

- mean `delta` at least `0.010` NLL/token;
- the deterministic 10,000-resample case bootstrap 95% lower bound at least
  `0.000`;
- `plasticity_guard` wins over `fixed_cadence` in at least 3 of 4 cases;
- `plasticity_guard` also beats `no_update` in at least 3 of 4 cases on
  absolute adaptation improvement;
- every qualification, custody, prediction-lock, hard-control, and validator
  gate passes.

The no-update comparison is a fixed diagnostic control, not a secondary
estimand. If the primary gate passes but the guard does not beat no-update, the
classification is `RollbackInfrastructureOnly`. If the primary gate fails
without an invalid run, the classification is
`IndependentReplicationNoCandidate`. Any failed qualification or custody gate
is `QualificationFailure` and cannot be rescued by assessment results.

The case is the bootstrap unit. No token, update, document, seed, order,
threshold, source, or arm is selected from tune or assessment data. Missing
metrics, non-finite values, failed case repeats, or incomplete adapters are
failures, not imputed values. There is no multiplicity adjustment because
there is one primary estimand and one preregistered threshold; the no-update
comparison is a fixed control and cannot create an alternate positive claim.

## Qualification gates

Qualification runs before any fit/tune or assessment metric is generated and
must pass all of these checks:

1. exact model, tokenizer, runtime, source, runner, and validator digests;
2. native reload maximum-logit absolute difference at most `1e-5`;
3. deterministic native repeat maximum-logit difference at most `1e-8`;
4. zero-strength adapter identity maximum-logit difference at most `1e-5`;
5. a fixed one-step candidate produces finite logits and nonzero logit reach;
6. candidate adapter save/copy/reload maximum-logit difference at most
   `1e-6`;
7. every captured tensor has the locked shape and finite values;
8. the base model manifest is unchanged after qualification;
9. primary and mirror custody roots are structurally valid and independent;
10. the independent validator accepts the qualification receipt.

Any failure stops the slice before fit/tune. No adaptive repair, alternate
model, alternate corpus, threshold change, or provider escalation is allowed.

## Prediction locking and assessment order

Fit runs generate candidate adapters and fit metrics only. Tune runs select no
hyperparameter: they produce the sealed case-level predictions from the one
fixed primary estimand using only fit-derived configuration and the fixed
threshold. The prediction lock is written and hashed before any assessment
window is evaluated. It contains configuration, model/source/runtime digests,
case identities, guard decisions, adapter digests, fixed threshold values,
and the predicted sign/classification for each case, but no assessment metric.

After the lock is independently read back, assessment runs once per case and
then once as the deterministic repeat. The assessment repeat must reproduce
all aggregate assessment metrics within `1e-8`. Assessment results cannot alter
the lock, configuration, source, corpus, adapters, or classification.

## Retention and validation

Raw Gutenberg bytes, normalized documents, token IDs, adapter tensors, logits,
per-token losses, and training logs remain only in the two external custody
roots. Repository documentation retains only protocol text, execution status,
configuration and qualification digests, prediction-lock digest, aggregate
case/arm metrics, gate booleans, validator digest, classification, and claim
ceiling. The aggregate receipt must contain no raw text, token IDs, logits,
activations, adapter tensor values, credentials, environment values, or
per-token/per-window rows.

The validator is a separate source file and process. It does not import or
execute the runner or model. It independently verifies manifests, exact split
identity, model immutability, arm compute equality, guard decisions, bootstrap
recomputation, lock ordering, assessment repeatability, aggregate-key closure,
raw-field absence, and complete primary/mirror file-manifest equality. It
emits one canonical aggregate receipt and no raw diagnostics.

Required implementation files after review:

~~~text
experiments/continual_learning/plasticity_guard_independent_replication_v2.py
experiments/continual_learning/validate_plasticity_guard_independent_replication_v2.py
experiments/continual_learning/tests/test_plasticity_guard_independent_replication_v2.py
~~~

The implementation authorization must name the actor, runtime, acquisition
command, runner, validator, both custody roots, exact corpus identity, and
claim ceiling. It does not authorize cross-actor replication, H100 use,
commit-budget mechanism variation, restart/rollback audit, Astral, Stage 0C,
Stage 1, or V82.

Every mutation in this protocol touches state slice
`continual-learning-plasticity-guard-independent-replication-v2`.
