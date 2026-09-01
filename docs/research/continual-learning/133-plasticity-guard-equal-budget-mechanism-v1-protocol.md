# Plasticity-guard equal-budget mechanism audit V1

Date: 2026-08-29.

State slice: `continual-learning-plasticity-guard-equal-budget-mechanism-v1`.

Status: `PROTOCOL_DRAFT_PENDING_INDEPENDENT_REVIEW`.

Claim ceiling: `LocalDevelopmentPlasticityGuardEqualBudgetMechanism`.

## Purpose and causal theory

The prior plasticity-guard feasibility result is not a mechanism result because
the guard committed one of six candidate updates while fixed cadence committed
all six. This fresh slice tests a narrower causal theory: a score-aware policy
can select the more useful update from a matched pair of candidate updates,
holding candidate-generation compute and the number of committed updates
constant. The estimand is the effect of selection policy, not the effect of
reducing update count.

The falsifying prediction is that the guard will not outperform a deterministic
random selector when both policies commit exactly one candidate per slot and
perform exactly the same candidate-generation and evaluation work. A result
that beats random but not the fixed-cadence control is not a positive mechanism
result. A result that beats both controls but fails any hard guard is not a
candidate.

This is a new state slice. It does not repair, reopen, or use as scientific
input the prior plasticity-guard, replication, recovery, contract-compiler,
information-budget, Astral, Stage 0C, Stage 1, or Neural Chameleon slices.
Prior results may appear only as rationale for the confound being tested.

## Authorization and phase boundary

The user authorization names this state slice and permits protocol drafting,
independent review, local qualification, and—only after the locked gates in
this document—assessment. This document itself does not open assessment.

Before independent review accepts the sealed protocol and contract, the runner
must not load a model, acquire Gutenberg data, create custody roots, train an
adapter, call a provider, allocate an H100, or produce scientific evidence.
GiveMeANode and H100 execution are disabled in this slice. Any later provider
or H100 use would require a separate authorization naming an exact cost cap,
runtime, custody root, and validator.

## Fixed model, runtime, and source custody

The sole actor is the already-cached local checkpoint:

```text
/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16
```

The actor is loaded only offline through the model-bound tokenizer policy and
the exact runtime tuple `Python 3.12.6`, `mlx 0.31.2`, and `mlx-lm 0.31.3`.
The qualification receipt records the executable path, package versions,
platform, device, model file manifest, tokenizer file manifest, runner digest,
validator digest, and protocol/contract digests. Any mismatch is terminal.
No model shopping, conversion, download, source checkout, or weight mutation
is allowed.

The additive implementation paths are fixed before review:

```text
experiments/continual_learning/plasticity_guard_equal_budget_mechanism_v1.py
experiments/continual_learning/validate_plasticity_guard_equal_budget_mechanism_v1.py
experiments/continual_learning/tests/test_plasticity_guard_equal_budget_mechanism_v1.py
```

The runner and validator are separate modules. The validator may consume only
the declared bytes listed in the independent-validator section and may not
import the runner, model library, tokenizer, or training code.

Primary custody root:

```text
/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/continual-learning-plasticity-guard-equal-budget-mechanism-v1-20260829-r1
```

Mirror custody root:

```text
/Volumes/DAed/Archives/composed-zk-benchmark-os/continual-learning-plasticity-guard-equal-budget-mechanism-v1-20260829-r1
```

Both roots must be new, external to the repository, regular directories on
the required volumes, and byte-identical after independent validation. No
prior result root or adapter is an input. Missing volumes, existing roots,
symlinks, or manifest drift are terminal.

## Fresh corpus identity

The corpus identity is
`gutenberg-equal-budget-mechanism-v1-20260829-r1`. It consists of exactly the
following 24 Project Gutenberg works. The numeric ID is the document identity;
the retrieval URL is exactly
`https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt`. The URL is not resolved
through a search result, alternate mirror, redirect, HTML page, or archive.

Fit documents, in fixed pair order:

```text
98   A Tale of Two Cities
174  The Picture of Dorian Gray
76   Adventures of Huckleberry Finn
35   The Time Machine
36   The War of the Worlds
1232 The Prince
1260 Jane Eyre
1400 Great Expectations
5200 The Metamorphosis
844  The Importance of Being Earnest
1080 A Modest Proposal
1184 The Count of Monte Cristo
```

Tune documents, in fixed order:

```text
55   The Wonderful Wizard of Oz
46   A Christmas Carol
2852 The Hound of the Baskervilles
25344 The Scarlet Letter
145  Middlemarch
514  Little Women
```

Assessment documents, in fixed order:

```text
205  Walden
1399 Anna Karenina
730  Oliver Twist
215  The Call of the Wild
219  Heart of Darkness
135  Les Misérables
```

The acquisition contract requires exactly one HTTPS response per listed ID,
HTTP status 200, final URL byte-equal to the declared URL, a `text/plain`
content type, no redirect, no content-encoding substitution, and a raw-byte
SHA-256 recorded before decoding. A failed or duplicated retrieval is
terminal. The raw response is retained only in the external custody roots.

Normalization is deterministic and applied in this exact order: strict UTF-8
decode; CRLF to LF; CR to LF; Unicode NFKC; require exactly one line whose
prefix is `*** START OF THE PROJECT GUTENBERG EBOOK` and exactly one line whose
prefix is `*** END OF THE PROJECT GUTENBERG EBOOK`; remove those complete lines
and all bytes before/after them; preserve all remaining code points and one
final LF. Marker absence, multiplicity, inversion, malformed UTF-8, or missing
final LF is terminal. The normalized UTF-8 bytes and length are digest-bound.

Each normalized document is encoded with the locked model tokenizer without
special tokens. It must contain at least 512 token IDs. The canonical window
is inclusive token indices 256 through 511, exactly 256 IDs. For every fit
pair, candidate A is indices 256 through 383 and candidate B is indices 384
through 511. Tune and assessment use the complete 256-ID window. The decoded
window must re-encode to the exact same IDs. No quality filter, replacement,
truncation, or post-hoc document choice is permitted.

The corpus manifest contains exactly the state slice, corpus identity, ordered
document IDs, declared URLs, split, raw/normalized lengths and digests, token
window digest, tokenizer manifest digest, and sorted file manifest. The split
assignment is fixed by this document and may not be inferred from outcomes.
No document, work, window, URL, or token identity crosses fit, tune, or
assessment.

## Learner and matched candidate generation

There are eight fixed replicate seeds:

```text
4101, 4102, 4103, 4104, 4105, 4106, 4107, 4108
```

Each seed runs both `forward` and `reverse` fit orders, for 16 paired cases.
Forward order is fit pairs 0 through 5. Reverse order is fit pairs 5 through
0. A pair keeps its canonical A/B identity under both orders.

Each case has six update slots. At every slot, the runner creates two
disposable candidate adapters from the same active adapter: candidate A is
trained on the pair's canonical A window and candidate B on its canonical B
window. Both candidates use exactly:

```text
LoRA rank 8, dropout 0.0, scale 20.0
AdamW, learning rate 0.0001
3 iterations, 4 repeated rows, batch size 1
4 trainable layers, max sequence length 128
```

The candidate seed is `case_seed + 1000 * slot + candidate_index`. Candidate
generation starts from a byte-identical copy of the active adapter. The base
checkpoint is never updated, merged, or overwritten. Each arm trains both
candidates and evaluates both candidates, even when the arm will not select
one of them. Therefore every arm performs exactly 12 candidate trainings, 12
candidate evaluations on the current window, and 12 candidate evaluations on
the protected buffer per case, and every arm commits exactly six candidates.

The protected buffer contains only fit windows from previously committed slots
in that case. At slot zero the protected buffer is empty and its protected
loss is defined as zero for both candidates. At later slots the protected loss
is the arithmetic mean over the committed fit windows. Missing or non-finite
loss is terminal. Candidate adapter files, rejected candidate files, and
selection decisions remain in external custody until independent validation.

## Three fixed arms

All arms receive the same candidate pair and the same measured finite metrics.
Only the selection policy differs:

1. `guarded_selection`: for each candidate `j`, compute
   `score_j = current_gain_j - max(protected_delta_j, 0.0)`, where
   `current_gain_j = active_current_nll - candidate_current_nll` and
   `protected_delta_j = candidate_protected_nll - active_protected_nll`.
   Select the higher score; an exact tie selects A.
2. `fixed_cadence`: select canonical candidate A at every slot. This is the
   same six-commit budget and a fixed policy control.
3. `deterministic_random`: use one `random.Random(case_seed + 700000)` per
   case and call `randrange(2)` once per slot in slot order. Zero selects A and
   one selects B. The draw sequence is recorded and is not reseeded.

The guard coefficient is exactly one. No threshold, coefficient, candidate
order, seed, layer, adapter budget, or policy is selected from fit, tune, or
assessment outcomes. The random arm is a policy null, not a claim that the
candidate pair is exchangeable.

## Estimands, thresholds, and multiplicity

For case `c` and arm `a`, define
`I(c,a) = base_assessment_mean_nll(c) - final_assessment_mean_nll(c,a)`.
The primary case contrast is
`D_GR(c) = I(c,guarded_selection) - I(c,deterministic_random)`.
The primary estimand is the arithmetic mean of `D_GR` over the 16 cases.
The secondary case contrast is
`D_GF(c) = I(c,guarded_selection) - I(c,fixed_cadence)`.

The confirmatory candidate rule requires all of the following:

```text
mean(D_GR) >= 0.010 NLL/token
deterministic 95% bootstrap lower bound for mean(D_GR) >= 0.000
guarded_selection wins deterministic_random in at least 10 of 16 cases
mean(D_GF) >= 0.000
all hard guards pass
```

The win comparison is strict (`D_GR > 0`); a tie is neither a win nor a loss.
The bootstrap uses `random.Random(410199)`, 10,000 replicates, 16 draws per
replicate with `randrange(16)` in case-index order, arithmetic means, sorted
replicate means, and linear interpolation at 0.025 and 0.975 positions. No
parallel or alternative random stream is allowed. The primary threshold is
the only confirmatory effect test. Tune metrics, `D_GF`, forgetting,
calibration, order stability, and individual cases are descriptive or hard
guards; no multiplicity adjustment may be used to rescue a failed primary.

## Power and reliability plan

Before corpus acquisition, a pure statistical preflight runs the fixed
100,000-replicate simulation specified here: 16 paired case contrasts sampled
from a normal distribution with mean `0.020` and standard deviation `0.025`,
using `random.Random(410199)`, the exact bootstrap and win rules above, and
the exact primary threshold. The simulated probability of satisfying the
effect threshold, nonnegative bootstrap bound, and 10/16 win rule must be at
least `0.80`; otherwise the slice stops before acquisition. The simulation is
planning only and is never written as scientific evidence.

Reliability requires every arm and case to have exactly six commits, exactly
12 candidate trainings, finite metrics, complete adapter files, stable
selection logs, and two identical assessment repeats. A one-case or one-arm
missing result is terminal. The primary unit remains the case; token-level
resampling is prohibited.

## Qualification gates

Qualification occurs before fit and assessment and is a separate state. It
must pass every gate below in order:

1. New external primary and mirror roots exist and are empty regular roots.
2. Source, protocol, contract, runner, validator, model, tokenizer, and
   runtime digests are captured and byte-stable.
3. Native reload parity is at most `1e-5` maximum absolute logit difference.
4. A second identical native probe repeats within `1e-8` maximum difference.
5. Zero-strength adapter replacement is at most `1e-5` from the native probe.
6. A fixed one-step candidate replacement reaches logits by more than
   `1e-6` maximum absolute difference, strictly and finitely.
7. Input, hidden-state, and logit shapes equal the declared Gemma3 text
   configuration: 26 layers, hidden size 1152, and the exact probe sequence
   length; all values are finite.
8. Candidate save/restore parity is at most `1e-6`.
9. The base model manifest is byte-identical before and after qualification.

Any failure transitions directly to `QualificationFailure`. No adaptive
repair, rerun, threshold change, or model substitution is allowed.

## Fit, tune, prediction lock, and assessment ordering

After qualification, the runner executes every fixed case and arm on fit
windows. Tune windows are evaluated only after all six fit slots and are used
only to produce a locked directional prediction for `D_GR` and `D_GF`; they do
not select a policy, coefficient, arm, seed, order, split, or threshold.

The prediction lock is canonical JSON with exact keys:

```text
state_slice, protocol_sha256, contract_sha256, qualification_sha256,
fit_aggregate_sha256, tune_aggregate_sha256, predicted_primary_sign,
predicted_secondary_sign, event_order, assessment_started, lock_sha256
```

The signs are `positive`, `negative`, or `tie`, computed by strict comparison
of the corresponding tune case mean to zero. The lock contains no assessment
metric. It is written after tune evaluation and before any assessment forward
pass. An independent reviewer then checks the lock digest, configuration
digest, event log, and prediction ordering. Assessment opens only if that
receipt says `accepted: true` and `assessment_started: false`.

Assessment evaluates all three arms on all six assessment documents. Each arm
is assessed twice from the same sealed final adapter. A repeat difference over
`1e-8`, changed aggregate keys, missing case, changed config, or assessment
before review is terminal `QualificationFailure`, with no classification as a
candidate.

## Independent aggregate-only validator

The validator is invoked from its own directory with this exact command, with
all paths expanded to canonical absolute paths and no additional arguments:

```text
env -i PATH=/usr/bin:/bin LC_ALL=C.UTF-8 TZ=UTC PYTHONHASHSEED=0 \
/usr/bin/python3 -I -S validate_plasticity_guard_equal_budget_mechanism_v1.py \
--primary <primary-root> --mirror <mirror-root> \
--protocol <protocol-file> --contract <contract-file> \
--qualification <qualification-file> --lock <lock-file> \
--results <results-file> --model-manifest <model-manifest-file> \
--corpus-manifest <corpus-manifest-file> \
--validator-source <validator-source-file>
```

The validator reads only those ten declared byte inputs, recomputes every
digest and gate, checks root equality, verifies event order and retention
schema, rejects raw evidence fields at any nesting depth, and emits one
LF-terminated canonical JSON receipt. It does not import the runner or model
libraries, does not trust receipt booleans, and does not inspect unlisted
paths. The validator source digest is independently recorded.

Aggregate receipts contain only finite scalar metrics, counts, fixed arm names,
digests, gate booleans, classification, claim ceiling, and
`execution_authorized: false`. Raw text, token IDs, logits, activations,
adapter tensors, per-window identifiers, credentials, environment values,
training logs, exception text, and undeclared paths are forbidden. Raw input
and training artifacts remain outside the repository and are deleted only by
the separately recorded cleanup command after validation. Cleanup is not
treated as proof of unrecoverability from other backups.

## Terminal classification and claim ceiling

The exact classification enum is:

```text
QualificationFailure
DevelopmentNoCandidate
EqualBudgetMechanismCandidate
```

The first terminal condition has precedence: custody or digest drift; missing,
non-finite, or shape-invalid data; native/repeat/zero/reach failure; lock or
event-order violation; assessment-before-review; assessment-repeat drift;
validator failure; unequal candidate compute or commit count; hard-control
failure; primary estimand failure; then the candidate rule. No later result can
downgrade or override an earlier failure. A `DevelopmentNoCandidate` result
means only that this fixed Gemma3 actor, fresh Gutenberg corpus, and declared
adapter policy did not pass the bounded mechanism gate. A candidate result is
local development evidence for this mechanism and does not establish general
continual-learning improvement, benchmark superiority, safety, production
readiness, Astral introspection, causal self-modeling, Stage 0C, Stage 1, or
any claim about consciousness.

Every mutation in this protocol touches state slice
`continual-learning-plasticity-guard-equal-budget-mechanism-v1`.
