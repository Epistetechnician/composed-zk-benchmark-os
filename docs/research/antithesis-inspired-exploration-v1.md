# Antithesis-Inspired Deterministic Exploration v1

State slice: `antithesis-inspired-deterministic-exploration-v1`

## Boundary

This slice implements a local Rust exploration controller over the existing
Semantic IR, mutation, local oracle, replay, shard, checkpoint, and failure
corpus surfaces. It adopts public testing concepts from Antithesis and the
outer-loop validation/finalization shape described by Meta-Harness. It does
not reproduce proprietary Antithesis internals and does not import
Meta-Harness as a runtime dependency.

The controller is deterministic proposal data. The local oracle remains the
authority for local replay outcomes. Exploration artifacts remain
`Level0DesignNote`; referenced replay artifacts retain their existing
`Level1LocalReplay` ceiling.

## Protocol

1. Validate a base `SoakRunConfig` and derive a digest-bound two-way seed
   partition.
2. Expose only the validation range to the bounded beam loop. Assessment
   ranges and outcomes remain absent until explicit finalization.
3. Evaluate the baseline and generated policies through fresh local shard
   replays. No candidate reuses another candidate's replay results. Each
   successful local replay retains its `ReplayManifest` and `ReplayResult`
   provenance at the soak-run boundary; guidance stores deterministic
   trace-level `OracleOutcome`, expected-verdict, replay-status, and result-
   classification observations.
4. Rank candidates lexicographically by validity, family/mutation coverage,
   novel replay signatures, distinct local failures, and minimized work.
5. Retain full candidate lineage and a resumable checkpoint. Shard result
   merging is canonical and independent of worker completion order.
6. Finalize once by evaluating the best validation candidate on the withheld
   assessment range. A finalized checkpoint cannot resume evolution.
7. Emit an `ExplorationAssessmentReport` only during that one-way finalization.
   It compares validation and assessment guidance, records signed deltas, and
   binds both observations to deterministic digests. The report is diagnostic
   metadata only; it is absent from the pre-finalization API state and cannot
   change ranking, oracle semantics, or evidence state.

The searched policy surface is limited to family selection/order, mutation
allocation/order, queue tie-break policy, and deterministic reducer order.
Exploration applies the selected family/mutation queue policy to case order,
mutation application order, and deterministic shard assignment after the
canonical soak plan is built. Generic soak planning remains unchanged.
Guidance excludes wall-clock timing, backend-performance metrics, model
outputs, network inputs, and external providers.

## Operational strategy campaign

The real-target strategy slice freezes one primary metric:
`distinct-reproducible-failure-classifications-per-case-budget`. A metric value
is the count of distinct replay `ResultClassification` values in the local
failure set, under equal case, shard, and configured mutation-attempt work
units. Capability gaps, timeouts, and inconclusive outcomes are not counted as
failures. Replay-attempt counts remain provenance metadata and are not a
wall-clock or backend-performance measure.

`LocalTargetCorpus` is built from the validation-only repository-owned
deterministic soak plan. The withheld assessment case ids are not present in
the validation corpus or serialized validation result; the phase-specific
assessment plan is materialized only during explicit finalization.
`LocalTargetAdapter` executes every policy with fresh local replays and retains
per-case `SemanticIr`, `MutationProvenance`, `ReplayManifest`, `ReplayResult`,
`OracleOutcome`, and matching failure-corpus entries. Missing inputs on failed
cases are explicit markers rather than silently omitted data.
The public adapter and explorer surfaces expose validation plans and validation
replays only; assessment plans and assessment replays are crate-internal and
are reached through the one-way `finalize_assessment` operation.

`BaselineCampaignRunner` evaluates five policies under the same phase-local
allocation budget: `StableDigest`, `RoundRobinFamilies`,
`RoundRobinMutations`, `BeamSearch`, and `SeededControl`. Validation selects the
winner using the frozen metric and policy-digest tie-break. Assessment records
are unavailable until one explicit `finalize_assessment` call and never change
the validation-selected policy. Validation checkpoints resume byte-identically
to uninterrupted execution.

`ExplorationRunConfig::with_case_budget` makes the policy surface operational:
when positive, the budget truncates the deterministically ordered plan before
execution, so policies can reach different cases while retaining equal case,
shard, and mutation-attempt allocations. Zero preserves the original full-plan
behavior. The budget must fit both validation and assessment domains.

The independent assessment slice
`antithesis-inspired-deterministic-exploration-v1-independent-assessment-suite`
requires at least two campaigns with disjoint full seed domains and equal case,
shard, and mutation budgets. It evaluates `BeamSearch` as the candidate against
all four fixed baselines. A typed promotion gate counts only campaigns where
the candidate strictly exceeds every fixed baseline on the primary metric. The
gate remains false until the one-way suite `finalize_assessment` operation and
does not constitute strategy validation beyond the local campaign domains.

The checked-in provider-free suite example is:

```text
cargo run -p zkbench-core --example operator_exploration_assessment_suite
```

The smoke baseline currently ties across policies, so the example must report
`promoted=false`. That result is a deterministic negative control, not evidence
that any policy is generally superior.

The bounded negative-control example is:

```text
cargo run -p zkbench-core --example operator_exploration_bounded_strategy_validation
```

On the checked-in two-campaign local regression-profile corpus with the
default three families and three mutation classes, and `case_budget=3`,
`RoundRobinFamilies` and
`RoundRobinMutations` reported metric values `[2, 2]` in validation and
assessment. `StableDigest`, `BeamSearch`, and `SeededControl` reported `[1, 1]`.
The independent suite's configured candidate was `BeamSearch`; it was not
selected from this metric table. The sealed gate observed `0/2` assessment
improvements and `promoted=false`. The bounded surface therefore
distinguishes policies on this local workload, but the candidate strategy has
no evidence of superiority.

The checked-in provider-free operator surface is
`operator_exploration_baseline_matrix`. It runs the matrix and sealed
assessment without credentials, network access, filesystem output, or evidence
mutation.

The persistent operator surface is
`operator_exploration_workflow`, under the named state slice
`antithesis-inspired-deterministic-exploration-v1-operator-workflow`:

```text
cargo run -p zkbench-core --example operator_exploration_workflow -- run <root>
cargo run -p zkbench-core --example operator_exploration_workflow -- resume <root>
cargo run -p zkbench-core --example operator_exploration_workflow -- finalize <root>
cargo run -p zkbench-core --example operator_exploration_workflow -- report <root>
cargo run -p zkbench-core --example operator_exploration_workflow -- corpus <root>
cargo run -p zkbench-core --example operator_exploration_workflow -- export-minimized <root> <entry-id>
```

The root retains `campaign-config.json`, immutable `validation.json`, optional
immutable `finalized.json`, canonical JSON/Markdown reports,
`failure-corpus.json`, `operator-manifest.json`, and minimized replay exports.
`run`, `resume`, `report`, and `corpus` cannot expose assessment observations;
only `finalize` creates the assessment artifact. Retained bytes are digested in
the manifest, and deterministic reruns reject conflicting immutable artifacts.
Reproducible local replay classifications are represented as deduplicated
`OracleMismatch` corpus entries with case, shard, mutation, trace, and replay
provenance. Minimized exports preserve the original replay manifest id and
accept reductions only when the same local failure classification remains.

The independent assessment suite has a matching persistent operator under the
named state slice
`antithesis-inspired-deterministic-exploration-v1-independent-assessment-suite-operator`:

```text
cargo run -p zkbench-core --example operator_exploration_assessment_suite_workflow -- run <root>
cargo run -p zkbench-core --example operator_exploration_assessment_suite_workflow -- resume <root>
cargo run -p zkbench-core --example operator_exploration_assessment_suite_workflow -- finalize <root>
cargo run -p zkbench-core --example operator_exploration_assessment_suite_workflow -- report <root>
```

It retains `suite-config.json`, validation-only `suite-validation.json`,
one-way `suite-finalized.json`, canonical suite reports, and
`suite-manifest.json`. The validation artifact contains only validation
campaigns and the resumable checkpoint; assessment campaign ids, outcomes, and
promotion-gate results are unavailable until `finalize`. The suite operator
does not promote a policy or write evidence. The derived scorecard state slice
`antithesis-inspired-deterministic-exploration-v1-independent-assessment-scorecard`
retains validation rows in every report and adds assessment rows plus signed
per-policy, per-campaign deltas only after finalization. The smoke example
remains a deterministic negative control with `promoted=false`.

## Failure reduction

`reduce_failure_sequence` accepts a replay-manifest id, failure
classification, and ordered reduction tokens. `reduce_local_replay_failure`
binds that reducer to a real `ReplayManifest` and `ReplayResult`, removes
selected trace ids in fixed order, and replays each candidate through the
provider-free `LocalJsonAdapter`. A reduction is accepted only when the exact
original `ResultClassification` remains present. The original replay-manifest
id is preserved in the reduction result; no evidence state is mutated.

## Artifacts and nonclaims

Exploration results can be serialized as a versioned exploration sidecar in an
existing local soak report bundle at `aggregate/exploration.json`. The sidecar
contains policy lineage, exact derived replay observations, checkpoints, and
optional finalized assessment output and its post-finalization diagnostic.
Filesystem readback requires the
declared sidecar, checks it against the inline bundle record, and verifies its
artifact digest; bundles without exploration retain the legacy main-file-only
layout. It cannot append the Evidence Ledger or create accepted benchmark
evidence.

This slice does not provide a perfect reward model, correctness proof,
official benchmark score, ZK backend performance result, production readiness,
scientific evidence, Antithesis SaaS compatibility, fault-injection fidelity,
or a claim about Antithesis's undisclosed implementation. A local baseline
comparison is strategy-development evidence only; repeated held-out
improvement must be demonstrated by separate campaigns before treating a
policy as operationally preferred.
