# Experience-learning baseline benchmark

State slice: `oaklab-experience-learning-baselines-v1`.

Run a small deterministic matrix without network access:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.run \
  --output /tmp/oaklab-experience-learning.json --steps 256
PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.validate \
  /tmp/oaklab-experience-learning.json
```

Use repeated `--stream` or `--algorithm` flags to select a subset. The output
is aggregate-only, digest-bound JSON. Synthetic digit and event-camera streams
are explicitly local fixtures; the operation-based energy field is not a
hardware energy measurement.

## V2 assessment protocol

V2 freezes the manifest before assessment, runs five independent seed offsets,
reports confidence intervals and paired tests, adds noise-floor/oracle-feature
controls, and applies the multi-stream Pareto publication gate:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.run_v2 \
  --output /tmp/oaklab-experience-learning-v2.json --steps 256
PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.validate_v2 \
  /tmp/oaklab-experience-learning-v2.json
PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.replay_v2 \
  /tmp/oaklab-experience-learning-v2.json
```

Real-data custody V1 is now complete in the external, read-only root
`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-real-data-v1`.
It contains four raw archives and 256-row ordered derived panels. The
acquisition and independent readback commands are:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.acquire_real_data_v1 \
  --root /Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-real-data-v1 \
  --limit 256 --seal
PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.validate_real_data_v1 \
  --root /Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-real-data-v1
```

The manifest binds source and derived SHA-256 digests. Custody is not learner
evidence: the publication gate remains closed even after the synchronized
operator CPU-energy receipt. Dense CPU, sparse CPU, optional CUDA GPU, and event-driven
backend parity is implemented in `backends.py`; the four real panels have
valid receipts, with GPU explicitly unavailable on this host. See the [V2
protocol](../../docs/research/experience-learning/02-oaklab-experience-learning-benchmark-v2.md),
[real-data custody receipt](../../docs/research/experience-learning/03-oaklab-real-data-custody-v1.md),
and [backend parity receipt](../../docs/research/experience-learning/04-oaklab-backend-parity-v1.md).
The declared macOS `powermetrics` CPU path and fail-closed integration tool
are documented in the [energy measurement record](../../docs/research/experience-learning/05-oaklab-energy-measurement-v1.md).
The synchronized operator capture, exact campaign manifest, measured CPU
receipt, and independent validation are recorded in the [R6 closure review](../../docs/research/experience-learning/26-oaklab-publication-gate-v2-r6-independent-review-closure.md).
Future operator runs must use the [capture wrapper](../../docs/research/experience-learning/25-oaklab-operator-capture-wrapper-v1.md), which records explicit lifecycle markers and reaps the sampler on success, failure, or interruption.
The fresh-cohort guard plan and negative result are in the [plasticity-guard
assessment record](../../docs/research/experience-learning/06-oaklab-plasticity-guard-fresh-cohort-v1.md).
The global multi-stream publication decision remains `no_candidate`: measured
energy now exists, but no mechanism passes the strict powered quality,
adaptation, and resource gate.

The powered V2 guard assessment, real all-baseline matrix, real-derived
nonstationary streams, longer event matrix, and full-campaign gate are
recorded in [08](../../docs/research/experience-learning/08-oaklab-powered-guard-assessment-v2.md),
[09](../../docs/research/experience-learning/09-oaklab-real-baseline-matrix-v1.md),
[10](../../docs/research/experience-learning/10-oaklab-real-derived-streams-v1.md),
[11](../../docs/research/experience-learning/11-oaklab-long-event-matrix-v1.md),
and [12](../../docs/research/experience-learning/12-oaklab-publication-gate-v2.md).
The powered guard is a negative result on all four original real panels. The
full gate remains `no_candidate` after the operator CPU-energy receipt because
the strict quality/resource requirement still fails.

The failed guard is not being retuned. A materially different delayed-
predictive-utility selective-credit theory was qualified on fresh synthetic
streams under a separate state slice. See the [theory protocol](../../docs/research/experience-learning/13-oaklab-selective-credit-theory-v1.md)
and [privileged-energy follow-up](../../docs/research/experience-learning/14-oaklab-privileged-energy-followup-v2.md).
The qualification receipt is
`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-selective-credit-v1/qualification.json`;
independent validation passed, but the theory is `no_candidate` and remains
synthetic-development-only.

V2 changes the estimand and state budget again: scalar sequential utility
`U_t = loss_(t-1) - loss_t`, full-rate updates under uncertainty, and throttling
only after confidently harmful utility. It uses fresh seed offsets `10..14`
and sealed prediction-lock snapshots. The receipt is
`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-selective-credit-v2/qualification.json`;
independent validation passes, but V2 is also `no_candidate`. Real-stream
execution remains sealed pending independent review, a privileged joule
receipt, and a stronger theory.
The required review checklist is in [17](../../docs/research/experience-learning/17-oaklab-selective-credit-v2-independent-review-gate.md);
its status is `completed_closure_only`.

The review is now complete for closure only: receipt
`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-selective-credit-v2/independent_review.json`
is `accepted_for_closure_only` with execution authorization disabled. V2 is
terminally closed as `NoCandidate`; see [18](../../docs/research/experience-learning/18-oaklab-selective-credit-v2-terminal-closure.md).

## Fresh replication and sensitivity V1

The surviving baseline arms were rerun on ten fresh seeds (`20..29`) over all
seven synthetic streams. Three hyperparameters per algorithm were declared in
advance; tune loss selected one candidate, and assessment was rerun only after
that lock. The plasticity guard and rejected selective-credit families were
excluded. The external receipt and independent validator are documented in
[the protocol](../../docs/research/experience-learning/19-oaklab-replication-sensitivity-v1-protocol.md)
and [execution record](../../docs/research/experience-learning/20-oaklab-replication-sensitivity-v1-execution-record.md).

The receipt is synthetic sensitivity evidence only. Its publication status is
`no_candidate`; the prior real-panel fixed-configuration matrix and fresh
real-panel sensitivity are separate evidence slices, and privileged measured
energy remains a publication gate. No guard retune occurred.

Equation fidelity is separately receipt-backed in [21](../../docs/research/experience-learning/21-oaklab-equation-parity-v1.md).
The reviewed fresh real-panel sensitivity protocol and corrected execution are
in [22](../../docs/research/experience-learning/22-oaklab-real-sensitivity-v1-protocol.md)
and [23](../../docs/research/experience-learning/23-oaklab-real-sensitivity-v1-execution-record.md).

## Selective-credit V3 terminal status

The existing plasticity guard is permanently closed as a historical comparator
under [27](../../docs/research/experience-learning/27-oaklab-plasticity-guard-permanent-historical-closure.md).
V3 froze a new micro-randomized horizon-credit estimand and execution gate in
[28](../../docs/research/experience-learning/28-oaklab-selective-credit-v3-protocol.md),
but the required independent review in
[29](../../docs/research/experience-learning/29-oaklab-selective-credit-v3-independent-protocol-review.md)
rejected the protocol before implementation. The terminal disposition is
recorded in [30](../../docs/research/experience-learning/30-oaklab-selective-credit-v3-terminal-closure.md).

V3 is `NoCandidate` with claim ceiling
`ProtocolReviewRejectedNoExecution`. No V3 learner, synthetic qualification,
real campaign, energy receipt, publication candidate, or Astral integration
was created. Any continuation requires a new protocol identity and state slice;
V3 may not be corrected or retuned in place.

## Constrained update policy V4 terminal status

V4 changed the estimand from an isolated-update effect to the paired cumulative
loss difference between complete learner policies. The frozen design is in
[31](../../docs/research/experience-learning/31-oaklab-constrained-update-policy-v4-protocol.md)
and its review packet is [32](../../docs/research/experience-learning/32-oaklab-constrained-update-policy-v4-review-packet.md).

The required independent review [33](../../docs/research/experience-learning/33-oaklab-constrained-update-policy-v4-independent-protocol-review.md)
rejected the protocol before implementation because eight byte-level,
transition, generator, resource, multiplicity, adaptation, and lock contracts
were not unique. V4 is terminally `NoCandidate`; see
[34](../../docs/research/experience-learning/34-oaklab-constrained-update-policy-v4-terminal-closure.md).
No implementation or execution occurred. The guard remains historical and
Astral remains isolated.
