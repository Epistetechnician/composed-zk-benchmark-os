# Plasticity Guard Replication V1 Protocol

State slice: `continual-learning-plasticity-guard-replication-v1`.

## Purpose

This is a fresh, separately authorized replication of the bounded Phase 831
cached-model result. The Phase 831 result is frozen as a replication candidate;
its guard thresholds, optimizer, adapter budget, and custody rules are not
tuned from the observed outcome.

The replication asks whether `plasticity_guard` improves held-out adaptation
over an untouched base model and fixed-cadence adapter updates. It does not
test waves, stochastic scheduling, verification tiers, introspection, or
self-modeling.

The frozen prior candidate is:

- state slice: `continual-learning-plasticity-guard-reversible-adapter-v1`;
- PrimaryED root: `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/continual-learning-plasticity-guard-reversible-adapter-v1-20260828-r1`;
- canonical results-body digest: `46d0654b199205b2957e5a1fb758c1989c377db7d6ab86eaa0f6440de3bd8316`;
- canonical receipt-body digest: `ed707b95864627dbefb00b277dda41bc23ec6ecaa51f36677ff503c0be6798b6`;
- results file SHA-256: `e2c15c2bafa0e6fa1fc5519267ccd51a1d0dabcabf551596b3b7e8a8426aa4ed`;
- receipt file SHA-256: `569d1b7f340867f8cd52803c4ff6be0ca09be55e02f18121189a8d9dd84b7a02`;
- observed paired guarded-minus-fixed result: `0.064052287` NLL/token;
- prior classification: `DevelopmentCandidate`.

The new run records and verifies these identities but does not reuse the prior
corpus, adapters, activations, effects, or assessment results.

## Model and cohort

Execution is offline against the already-cached
`Qwen`-independent Gemma3 1B PT BF16 MLX checkpoint at
`/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`, using the
locked MLX `0.31.2` and MLX-LM `0.31.3` runtime. The registered NEWSROOM source
is copied byte-for-byte into the external artifact root. The new cohort selects
the next 12 eligible 256-token windows after the prior cohort: eligible
records 20 through 31, with 6 fit, 3 tune, and 3 assessment documents. The
prior records 8 through 19 are recorded as excluded and must not overlap.

New seeds are `1747` and `1749`. New fit orders are fixed before execution:

- `interleave`: `(0, 3, 1, 4, 2, 5)`;
- `outer_in`: `(0, 5, 1, 4, 2, 3)`.

## Arms and equal compute

Every case attempts six updates. Each update uses four repeated training rows,
three LoRA iterations, batch size one, four trainable layers, AdamW, learning
rate `1e-4`, and maximum sequence length 256. Adapters are saved per update;
none is merged into the base checkpoint.

The fixed arms are:

1. `no_update`: runs a disposable shadow adapter chain to spend the same
   training budget, but always evaluates the untouched base model and applies
   no adapter;
2. `fixed_cadence`: commits every candidate adapter;
3. `plasticity_guard`: uses the frozen Phase 831 rule. Step zero is accepted;
   later candidates require current-window NLL gain at least `0.001` and
   protected-window degradation at most `0.010`. Rejected candidates leave the
   active adapter pointer unchanged.

## Endpoints and decision rules

For every case, adaptation improvement is:

`untouched_base_assessment_mean_nll - final_arm_assessment_mean_nll`.

The primary endpoint is the absolute guarded-arm improvement versus the
untouched base. It passes only when its mean is at least `0.010` NLL/token,
the deterministic 10,000-resample case bootstrap lower bound is nonnegative,
and the guarded arm beats `no_update` in at least 3 of 4 paired seed/order
cases, with all hard guards passing.

The secondary endpoint is guarded-minus-fixed improvement. It uses the same
`0.010`, nonnegative lower-bound, and 3-of-4 rules, but cannot override a
failed primary endpoint.

Classification is mechanical:

- both endpoints pass: `DevelopmentCandidate`;
- secondary passes but primary fails: `RollbackInfrastructureOnly`;
- otherwise: `ReplicationFailureClosed`.

The last classification closes the mechanism for this replication lane. A
positive guarded-minus-fixed result that loses to `no_update` is retained only
as rollback/safety infrastructure.

## Hard guards and custody

The run stops on any failure of native reload parity, zero-adapter identity,
nonzero candidate reach, adapter restore fidelity, finite metrics, fit
forgetting, tune calibration, assessment repeatability, no-update equivalence
to the untouched base, document-disjoint splits, prediction locking, model
manifest equality, or PrimaryED/DAed mirror equality. An independent
aggregate-only validator recomputes endpoint decisions and all digest links on
both roots.

The only permitted Astral status is `not_run`. Any later Astral slice must be
separately authorized and may measure only causal-effect prediction,
calibration, or instrumental correction. ZK/PQC backends remain `not_run` and
are a later proof-and-overhead experiment.

No model or corpus download, network access during execution, base-weight
update, adapter merge, V48 artifact reuse, Astral ledger mutation, benchmark
claim, introspection claim, or production claim is permitted.

Every mutation in this protocol touches state slice
`continual-learning-plasticity-guard-replication-v1`.
