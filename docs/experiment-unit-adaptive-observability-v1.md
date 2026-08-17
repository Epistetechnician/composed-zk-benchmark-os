# Experiment Unit and Adaptive Observability Contract v1

State slice: benchmark-os-experiment-unit-adaptive-observability-v1.
Payload readback slice: benchmark-os-observability-payload-readback-v1.
Artifact identity slice: benchmark-os-observability-artifact-identity-v1.
Legacy migration slice: benchmark-os-observability-v1-to-v2-upgrade-v1.
Ledger transport slice: benchmark-os-observability-ledger-transport-v1.
Bundle assembly slice: benchmark-os-observability-bundle-assembly-v1.
Slot access slice: benchmark-os-observability-slot-access-v1.
Module manifest slice: benchmark-os-observability-module-manifest-v1.
Slot order slice: benchmark-os-observability-slot-order-v1.
Local projection binding access slice: benchmark-os-local-json-projection-binding-access-v1.
Local inner artifact access slice: benchmark-os-local-inner-artifact-access-v1.
Local projection single-source access slice: benchmark-os-local-json-projection-single-source-access-v1.
Run artifact policy slice: benchmark-os-observability-run-artifact-policy-v1.
Bundle schema: experiment-unit-artifact-bundle-v2.

Status: implemented as a local, metadata-only contract over the existing
experiment bundle slice.

> Maximize knowledge per unit compute through adaptive experimentation and
> modular measurement.

The unit of science is the experiment. A run is not a loose collection of
logs, screenshots, metrics, and notes. It is one versioned record with one
fixed artifact shape. A new benchmark or interpretability method is accepted
when it can occupy the existing seams without changing the platform.

## Fixed run artifact shape

Every run has these nine required slots, even when a slot is empty by policy:

| Slot | Required contents |
| --- | --- |
| config | Frozen experiment configuration and schema identity |
| task | Task identity, input identity, and task implementation version |
| prompt | Prompt payload or redacted prompt digest |
| response | Response payload or redacted response digest |
| evaluation | Evaluator result plus Metric observations |
| mechanism record | Tier allocation, collector identity, status, and payload digest |
| metadata | Experiment id, run id, hypothesis, lifecycle, replication flag |
| logs | Structured or redacted logs with retention policy |
| report | Result, limitations, negative-result status, and claim ceiling |

Each slot is an ExperimentArtifactRef with:

- a portable relative URI;
- the owning experiment id and run id;
- a digest over the exact payload;
- who produced it;
- what activity produced it;
- when it was produced;
- implementation version;
- source revision.

The contract is deliberately a manifest over payloads. It does not require
raw prompt, response, mechanism, or log retention. Redaction is represented
as a declared artifact state, never by silently omitting a slot.

All Implementations route their nine typed references through one private
bundle-assembly Module. Its Interface fixes slot order, schema version, active
experiment/run identity, Level0 claim ceiling, and final validation. A new
Adapter therefore supplies the nine references without reimplementing bundle
policy, and a future schema change has one locality-preserving edit point.

`ExperimentArtifactBundle::artifact` is the canonical slot-access Interface.
Consumers select a slot by `ExperimentArtifactKind`; composition Adapters do
not maintain private field matchers. This keeps slot lookup colocated with the
fixed bundle Module while preserving the existing serialized field shape.

`LocalJsonArtifactProjection::single_inner_artifact` is the exact-one source
Interface for direct task, prompt, and response projections. The local runner
uses it instead of selecting the first vector element, so missing or duplicated
inner sources fail closed before an outer artifact is created. Composed slots
such as evaluation retain their explicit multi-source representation.

## Replaceable modules and seams

The public seams live in
crates/zkbench-core/src/experiment_observability.rs.

    Task
      materialize(TaskContext) -> TaskOutput

    ResponseProducer
      produce(ResponseContext) -> ResponseOutput

    Metric
      measure(MetricContext) -> MetricObservation

    Evaluator
      evaluate(EvaluationContext) -> EvaluationRecord

    MechanismCollector
      collect(MechanismCollectionContext) -> MechanismRecord

    ObservabilityScheduler
      allocate(ObservabilitySignals, ObservabilityBudget)
        -> ObservabilityDecision

    ExperimentRunner
      run(&mut self) -> ExperimentArtifactBundle

Every implementation carries a ModuleDescriptor:

- logical module id;
- concrete implementation id;
- implementation version;
- source revision.

The module manifest is the shared admission Interface for ordered module
identity. It preserves the serialized Vec<ModuleDescriptor> shape while
requiring at least one descriptor, validating every descriptor, and rejecting
duplicate logical module ids. Both the composed runner and the local plugin
composition Adapter apply it before adapter execution or config readback.

The fixed artifact order is owned by `ExperimentArtifactKind::ALL`, with one
slot count and one stable field-name mapping. Bundle validation and generic
composition consume that Interface rather than maintaining separate nine-slot
lists. The serialized bundle remains the same nine named fields.

The interface is the test surface. A benchmark adapter, sparse autoencoder
collector, circuit tracer collector, evaluator, and metric implementation can
be replaced independently. The platform depends on the record contracts and
invariants, not on the implementation internals.

ComposedExperimentRunner is the reference composition adapter. It freezes the
run spec, invokes Task and ResponseProducer, measures through every Metric,
passes those observations to Evaluator, allocates one observability tier, and
invokes MechanismCollector with the retained decision. It then emits and
validates all nine artifact slots, appends one mechanism record to an
append-only ledger, and is one-shot for its fixed run id. The adapter owns no
model, process, network, or privileged-telemetry implementation.

Admission is fail-closed at the seam boundary. A `MetricObservation` with
`Measured` status must carry a scalar value; `Unavailable` and `Failed`
observations must be value-free. `EvaluationRecord` validates evaluator
identity and provenance, requires a canonical status for its typed outcome
(`positive_result`, `negative_result`, `inconclusive`, `failed`, or
`not_run`), and rejects duplicate metric identities. These are artifact
integrity rules, not claims that the metric is scientifically valid.

`ExperimentArtifactRef::validate` is the intrinsic admission Interface for
every artifact reference. `ExperimentArtifactRef::validate_for` adds the
active experiment/run identity check, and the fixed bundle validator applies
it to all nine slots. This prevents a structurally valid reference from
another run being substituted into the manifest. The generic
`validate_experiment_artifact_payload` Interface then recomputes the exact
payload digest. The report specialization additionally validates schema
version, active experiment/run identity, typed status, negative-result marker,
declared limitations, provenance, and the Level0 claim ceiling.
`deserialize_experiment_report_json` requires canonical bytes and applies both
checks during report readback; the structural manifest validator does not
pretend to inspect payloads it does not receive. This keeps transport
integrity and scientific validity separate while concentrating the invariant
in one deep Module.

## Explicit legacy migration

The current outer bundle is v2 because each of its nine references carries the
owning experiment id and run id. A v1 outer bundle may still be preserved, but
ordinary v2 deserialization rejects it. Compatibility is an explicit Adapter,
`upgrade_experiment_artifact_bundle_v1_json`, with these rules:

- only the exact `experiment-unit-artifact-bundle-v1` schema is accepted;
- the input must be the canonical v1 JSON serialization;
- the enclosing v1 experiment id and run id are copied into every reference;
- URI, kind, digest, provenance, bundle identity, and claim boundary are
  preserved and revalidated;
- the output is validated as
  `experiment-unit-artifact-bundle-v2` before it is returned;
- payloads are neither read nor rewritten, and no scientific claim is raised.

There is no implicit fallback in the normal deserializer. Packet and archival
callers must record that the migration Adapter was invoked, then use the
validated v2 manifest. This keeps replacement and permanence explicit: legacy
records remain readable through a named, auditable seam without weakening the
current contract.

The existing v1 module also retains the local ExperimentTask,
ExperimentModel, MechanismCollector, Evaluator, and ExperimentPlugin seams.
This new contract is additive and supplies the missing adaptive-observability
and nine-slot shape without changing that user-owned local replay path.

## Progressive observability

Tier0 is always on. It records run identity, configuration identity, module
versions, timestamps or logical time, result status, scheduler signals,
allocation, and retention decisions. It collects no blanket mechanism stream.

Tier1 is sampled light mechanism data. It is used when the weighted priority
clears the sampling threshold and a Tier1 budget remains.

Tier2 is an anomaly-triggered deep dive. It is selected by high weighted
priority or a high failure signal, and consumes only a Tier2 budget.

Tier3 is a reserved gold case. It requires a remaining gold budget and an
extreme priority or combined novelty/failure signal.

The reference scheduler uses integer scores on a 0 to 1000 scale. The
decision records novelty, uncertainty, failure, weighted priority, selected
tier, and reasons. Exhausted higher-tier budgets fall back to Tier0. That is
the anti-blanket-coverage invariant.

The weighted scheduler can validate a deserialized decision by recomputing its
priority and rule-derived reasons. Mechanism records also validate decision
bounds, payload-digest shape, Tier0 absence of collected payloads, and an
explicit failure reason for failed collection. These checks protect the local
metadata contract from post-run field drift; they do not make the metadata
scientific evidence.

Scheduler allocation is transactional at the runner seam. The generic runner
allocates against a private next-budget, and commits that budget only after
mechanism collection, ledger validation, and all nine artifact slots validate.
A failed collection therefore produces no ledger entry and consumes no budget;
retry state cannot silently diverge from the retained provenance.

The state slice `benchmark-os-observability-run-lifecycle-transaction-v1`
deepens this invariant through one private lifecycle transaction shared by the
generic `ComposedExperimentRunner` and `LocalJsonExperimentRunner`. The
transaction stages scheduler budget and the next mechanism ledger, exposes no
runner mutation during allocation or validation, and commits both only after
the complete artifact bundle validates. Local composition state is likewise
assigned only after projection validation. This preserves the public traits,
serialized schemas, scheduler policy, one-shot behavior, and Level0/Level1
claim ceilings while making failure atomicity one implementation seam rather
than duplicated runner choreography.

The additive `ObservabilityScheduler::allocate_with_receipt` Interface runs a
replacement scheduler against an isolated budget and returns one
`ObservabilityAllocationReceipt` containing the before-budget, decision, and
after-budget. The lifecycle transaction consumes that receipt, so a scheduler
that overspends or mutates an unrelated tier fails before retained runner
state changes. The existing mutable `allocate` method remains the compatibility
Adapter for older scheduler implementations.

The `MechanismRecord::validate_for_run` admission Interface then binds the
record to the active experiment, run, scheduler decision, and collector
Adapter. Intrinsic record validation remains the durable-ledger check; run
admission is stronger and is consumed by both generic and local runner
Adapters. Failed collection records may omit an unavailable collector, while
non-failed elevated records must retain the expected collector.

The additive `validate_observability_allocation_witness` readback Interface
reconstructs the runtime allocation receipt from the existing durable config,
metadata, signals, decision, and remaining-budget fields. Generic
run-config/metadata payloads and local composition config payloads expose this
same Seam, so signal drift or budget-transition drift fails before a payload
is treated as a valid experiment record. No serialized fields are added.

State slice: `benchmark-os-observability-allocation-witness-payload-readback-v1`.

`validate_serialized_experiment_run_payloads` and
`validate_serialized_local_json_composition_with_metadata` are additive
payload-readback Adapters. They require canonical config and metadata bytes,
bind each payload to the existing artifact digest and run identity, compare
the config/metadata decision and module manifest, and reconstruct the shared
allocation receipt. The historical three-argument composition transport and
packet readback Interfaces remain unchanged because their outer bundle carries
only a metadata reference, not metadata bytes. This is authenticated local
metadata plumbing, not execution, publication, accepted evidence, production
readiness, or a claim above `Level0DesignNote`.

The scheduler is policy, not scientific evidence. Its weights and thresholds
are versioned configuration and must be frozen before a sealed assessment.
Changing them defines a new experiment configuration.

## Mechanism ledger

The adaptive MechanismLedger is append-only:

    MechanismLedger {
      schema_version: adaptive-mechanism-ledger-v2,
      experiment_id,
      entries: [
        {
          sequence_number,
          previous_digest,
          record: {
            record_id,
            experiment_id,
            run_id,
            tier,
            status,
            collector,
            payload_digest,
            decision,
            provenance
          },
          entry_digest
        }
      ],
      tip_digest
    }

New evidence appends a new entry. The append operation never replaces a
historical record. Validation checks sequence order, experiment identity,
previous-digest continuity, record invariants, entry digest, and tip digest.
Direct mutation of a retained entry is detected as a digest-chain failure.

The mechanism and metric meta-evaluation ledgers have canonical JSON
transport Adapters: `serialize_mechanism_ledger_json`,
`deserialize_mechanism_ledger_json`, `serialize_meta_evaluation_ledger_json`,
and `deserialize_meta_evaluation_ledger_json`. Serialization validates before
emitting bytes. Readback validates the digest chain and rejects noncanonical
bytes, malformed entries, schema drift, and tampering. The transport Adapter
does not append, replace, or reinterpret evidence; it only makes the existing
append-only state durable and verifiable.

Tier and status must agree:

- Tier0: MetadataOnly, or Failed when collection failed;
- Tier1: Sampled;
- Tier2: DeepDive;
- Tier3: GoldCase.

Unsupported collection is data. It must have a reason and must not be
converted into a zero, a success, or a missing artifact.

## Provenance contract

Every artifact and observation answers:

    who
    what
    when
    with what version
    from what source revision

Unknown values use an explicit local-state marker such as local-uncommitted
or fixture-only. Empty strings are invalid. Provenance is not a free-text
afterthought and is not inferred from imports or filenames.

The run metadata must additionally carry:

- experiment id;
- run id;
- hypothesis;
- lifecycle status;
- replication flag;
- negative-result or inconclusive status;
- retention and redaction policy.

## Meta-evaluation

Metric validity is a separate research object from Metric output. The
MetaEvaluationLedger appends judgments about:

- an immutable assessment basis containing the frozen comparison rule,
  held-out downstream target, replication identity, and ordered source artifact
  references with their own provenance;
- a digest over that canonical assessment basis;
- stability across repeated runs;
- downstream predictiveness under a declared target and test;
- noise class;
- optional noise score;
- observation count;
- replication count;
- provenance.

Stable does not mean predictive. Predictive does not mean low-noise. Untested
and unknown remain explicit states. A metric that fails to predict downstream
behavior is retained as a negative meta-result and is not silently removed
from reports.

Schema `metric-meta-evaluation-v2` requires each judgment to bind and digest
that assessment basis before it can be appended. Tested stability requires at
least one replication, and tested downstream predictiveness requires
observations. Assessment data must not be used to rewrite the metric profile
after the fact; a new judgment appends under a new replication or assessment
identity. The ledger uses sequence, predecessor, entry, and tip digests so
history mutation is detectable as well as structurally append-only.

## Research loop

The platform records the following loop as one chain of versioned artifacts:

    hypothesis
      -> experiment configuration
      -> task and prompt
      -> response
      -> mechanism collection
      -> metric evaluation
      -> result and report
      -> replication

The result state includes positive, negative, inconclusive, failed, and not-run
outcomes. Negative results are first-class. A failed collector is not silently
treated as a negative scientific result; infrastructure failure and
hypothesis failure remain distinct statuses.

The experiment is the unit of comparison. Comparing implementations requires
the same task identity, prompt contract, response contract, evaluation rules,
observability policy, budgets, provenance fields, and report schema. Otherwise
the comparison is a new experiment.

## Integration path

1. Keep the existing local v1 ExperimentPlugin as a compatibility adapter.
2. Add a runner that emits the nine fixed slots and invokes the new seams.
   `ComposedExperimentRunner` supplies the generic metadata-only adapter, and
   `LocalJsonExperimentRunner` now composes the shipped static local plugin
   into that fixed shape.
3. Use Tier0 metadata for every run.
4. Invoke Tier1, Tier2, or Tier3 collectors only from a frozen scheduler
   decision.
5. Append each MechanismRecord to the mechanism ledger.
6. Evaluate metrics and append meta-evaluation only in a separate
   meta-evaluation experiment.
7. Replicate with a new run id and preserved source/config identities.
8. Promote claims only through the existing evidence and review machinery.

The default local composition runner invokes the existing deterministic local
replay plugin through the existing plugin Seam. An alternate plugin Adapter
can be supplied without editing the outer runner; its descriptor identity is
retained in the composition module list and its emitted bundle must match that
identity. No runner in this slice invokes an external process, network,
provider, model download, or privileged telemetry path. The implementation
establishes replacement seams, validated JSON transport, and local validators
only.

## Generic plugin composition

State slice: `benchmark-os-experiment-plugin-agnostic-composition-v1`.

`PluginCompositionRunner` is the plugin-agnostic in-memory outer seam. It
accepts any catalog-instantiated plugin that passes `run_validated()`, then
emits the fixed nine slots with a canonical `PluginCompositionConfig`. Every
slot records explicit inner artifact kinds, URIs, and digests; validation
rejects missing or duplicate slots, source drift, inner identity drift, outer
identity drift, payload digest drift, and claim escalation. The metacognitive
pure-data plugin and the existing Local JSON plugin both run through this
generic seam. `ExperimentPacketComposition` now supplies the durable transport
seam with two adapters: the historical Local JSON config and the generic
`PluginCompositionConfig`. `PluginCompositionPacket` uses the same manifest,
sidecar, symlink, protected-root, overwrite, and strict-readback machinery as
the compatibility packet; only config serialization and semantic validation
remain adapter-owned. Both packet families remain Level0 durable metadata
packaging, not accepted evidence or runtime authority.

The inner `ExperimentBundle::artifact` Interface is fail-closed: a requested
artifact kind must be present exactly once. Generic composition uses this
accessor for source binding, so duplicate entries cannot be silently resolved
by first-match order. Aggregate bundle validation remains responsible for
reporting all malformed-artifact issues; the accessor only protects Adapter
selection semantics.

## Local composition adapter

`LocalJsonExperimentRunner` is the concrete bridge between the two contracts.
Its compatibility constructor resolves the registered local JSON plugin, while
`new_with_plugin` accepts any `ExperimentPlugin` Adapter. The Adapter emits a
`Level1LocalReplay` bundle, projects the task/prompt/response/evaluation
references into the fixed nine slots, allocates one scheduler tier, appends a
mechanism record to a digest-chained ledger, and validates the outer
`Level0DesignNote` manifest. The bridge is one-shot for its fixed run id and
retains no raw prompt, response, or privileged mechanism stream.

## Canonical artifact projection

State slice: `benchmark-os-canonical-artifact-projection-v1`.

The bridge stores a typed, versioned `LocalJsonArtifactProjection` inside the
canonical composition config artifact. It records the inner bundle id and
digest, the source artifact kind/URI/digest set, the outer fixed slot and URI,
the relation (`direct`, `composed`, `derived`, or `absent`), and projected
digests when the outer payload is deterministic from the inner source set.
The fixed mapping is explicit: task from `DataVersion`, prompt from
`ReplayManifest`, response from `ReplayResult`, evaluation from `Metrics` plus
`Report`, and mechanism from `MechanismLedger` only above Tier0. Tier0 records
mechanism absence rather than implying collection; metadata, logs, and report
are explicitly derived outer records.

`validate_local_json_artifact_projection` validates both bundles and the
canonical config together. It rejects stale inner bundle identity, wrong
source kind or digest, target URI drift, projected outer digest drift, duplicate
or incomplete fixed-slot mappings, claim-boundary escalation, and outer
identity mismatch. The inner and outer artifact schemas remain separate: this
adapter is the seam that gives maintainers locality without coupling their
schema evolution.

`LocalJsonArtifactProjection::binding` is the fail-closed access Interface for
individual outer slots. It returns exactly one matching binding and rejects
missing or duplicated kinds before a runner reads source artifacts. The
aggregate validator remains separate so malformed serialized projections still
receive complete diagnostics through the existing validation path.

The local projection Adapter also routes inner source selection through the
strict `ExperimentBundle::artifact` Interface. Missing and duplicated inner
artifact kinds therefore fail before a projection can be constructed, while
the adapter-specific error path remains visible to callers. This keeps source
selection replacement-local and prevents a malformed bundle from being
silently projected from its first matching vector entry.

## Composition config transport

State slice: `benchmark-os-composition-config-transport-v1`.

The composition config has an explicit JSON transport seam:
`serialize_local_json_composition_config_json`,
`deserialize_local_json_composition_config_json`, and
`validate_serialized_local_json_composition`. Readback validates the exact raw
JSON bytes against `outer.config.digest`, rejects non-canonical serialization,
then revalidates the inner bundle, outer bundle, projection, and claim ceiling.
This makes config archival/readback deterministic without adding filesystem,
process, network, or runtime authority.

## Composition packet readback

State slice: `benchmark-os-composition-transport-readback-v1`.

`validate_serialized_local_json_composition_transport` is the complete local
transport adapter. It accepts the inner `ExperimentBundle` JSON, composition
config JSON, and outer nine-slot bundle JSON; requires each transport to be
canonical; validates the inner bundle before trusting its digest; then checks
the config projection and outer identity together. This is the smallest
verifiable composition packet and is still in-memory metadata plumbing, not
filesystem materialization or accepted evidence.

## Composition packet materialization and readback

State slice: `benchmark-os-experiment-packet-materialization-readback-v1`.
Write-safety extension: `benchmark-os-experiment-packet-write-symlink-preflight-v1`.
Integrity extension: `benchmark-os-experiment-packet-canonical-digest-sidecar-v1`.

`ExperimentPacket` is the typed seam for the three validated transport
artifacts. `write_experiment_packet_outputs` owns their existing canonical
serializers and writes only a caller-selected packet root containing the
packet manifest, the three JSON artifacts, and four SHA-256 sidecars. The
manifest declares the fixed relative paths, exact byte digests, experiment and
run identities, required limitations, and `Level0DesignNote` ceiling.

Readback rejects missing or unexpected files, symlinks, unsafe relative paths,
protected-root overlap, stale sidecars, non-canonical manifest/config bytes,
identity drift, projection drift, and mismatched overwrite requests. Matching
overwrite is idempotent; source artifacts and the accepted Evidence Ledger are
untouched. The packet materializer preserves the inner `Level1LocalReplay`
ceiling while the durable composition package remains `Level0DesignNote`.

The writer preflights every existing path component with symlink-aware metadata,
including dangling leaf symlinks and intermediate directory symlinks, before
writing any packet payload. This prevents a packet write from following an
existing link outside the caller-owned packet root.

Digest sidecars are read back as exact canonical bytes: the lowercase SHA-256
hex digest followed by one newline. Leading, trailing, repeated, or alternate
line-ending whitespace is rejected rather than normalized. This keeps the
durable packet's byte-level integrity contract aligned with its writer.

This is local filesystem packaging only. It does not retain raw mechanism
streams, invoke a model or external process, authorize replay, or create
official benchmark evidence.

## Plugin composition packet job

State slice: `benchmark-os-plugin-composition-packet-job-v1`.

`ExperimentPacketJob` is the one-shot orchestration seam from a typed factory
catalog to a durable generic packet. It validates the selected descriptor,
instantiates the plugin, runs `PluginCompositionRunner`, writes through
`write_plugin_composition_packet_outputs`, and reads through
`read_plugin_composition_packet_outputs`. It returns only when the typed packet
and manifest read back equal the materialized values. Unknown plugins fail
before output creation, protected paths remain delegated to packet transport,
and a second invocation is rejected. `ExperimentPacketJobConfig` concentrates
the identity, provenance, output policy, and protected-path invariants behind a
single typed request value. This adds OS-level run-unit locality without adding
model/process/network execution, evidence mutation, atomic-write guarantees, or
runtime authority.

## Plugin composition packet store seam

State slice: `benchmark-os-plugin-composition-packet-store-seam-v1`.

`PluginCompositionPacketStore` separates packet-job choreography from
persistence. `FilesystemPluginCompositionPacketStore` delegates unchanged to
the canonical packet writer and strict reader through a typed
`PacketStoreDestination`. Test adapters can record materialization and
readback ordering or inject packet/manifest drift without changing plugin
composition. `InMemoryPluginCompositionPacketStore` is a production adapter
for non-durable local composition: it uses the same canonical packet-output
builder and keeps readback strict without creating filesystem artifacts. The
seam adds no atomic publication, execution, network access, evidence mutation,
or runtime authority.

## Storage-independent packet-job request

State slice: `benchmark-os-plugin-composition-packet-job-storage-independent-request-v1`.

`ExperimentPacketJobRequest` keeps plugin identity, experiment/run identity,
and provenance independent from persistence policy.
`ExperimentPacketJob::new_with_request_and_store` constructs a
`StorageIndependentExperimentPacketJob` for injected stores without requiring
an output root, overwrite flag, or protected-path list.
`ExperimentPacketJobConfig` and the existing filesystem constructor remain a
compatibility path for callers that intentionally select filesystem policy.
Request validation occurs before plugin resolution, and the shared runner
still enforces one-shot execution plus typed materialize/readback equality.
This is local configuration and metadata plumbing only; it does not add
publication, execution, network access, evidence mutation, or runtime
authority.

## Legacy packet-store compatibility containment

State slice: `benchmark-os-plugin-composition-packet-store-legacy-seam-containment-v1`.

The keyed receipt-bound store is the active packet-job persistence interface.
The historical unkeyed `PluginCompositionPacketStore` and
`LegacyPluginCompositionPacketStoreAdapter` now live in
`experiment_packet_store_compat`, while `experiment_packet_store` re-exports
those names for source compatibility. This makes the weaker most-recent
readback semantics explicit and keeps new adapters directed toward keyed
identity and receipt validation. No packet wire shape or readback behavior
changes; the slice only improves compatibility locality and preserves the
`Level0DesignNote` outer claim ceiling.

## Observability run artifact policy

State slice: `benchmark-os-observability-run-artifact-policy-v1`.

The private `ExperimentRunArtifactPolicy` Interface now owns the repeated
identity- and provenance-bound `ExperimentArtifactRef` construction used by
the generic and local observability runners. It also owns typed report
reference validation, including report payload identity, digest, and
`Level0DesignNote` checks. Adapter-specific task, prompt, response, and
projection payloads remain unchanged; the nine-slot order, URIs, serialized
payloads, and digest semantics remain unchanged. This is local metadata
plumbing and contract locality only. It does not add execution, publication,
accepted evidence, production readiness, benchmark superiority, or runtime
authority.

## Success bar and claim ceiling

Good looks like this: a new benchmark or interpretability method plugs in
without changing the platform. The required work is an adapter implementing
the existing seams, a frozen module descriptor, a fixed artifact payload
schema, and focused interface tests.

This slice is local architecture and metadata validation. It does not prove
interpretability, mechanism fidelity, causal validity, benchmark superiority,
scientific replication, production readiness, or runtime authority. It does
not mutate the accepted Evidence Ledger and remains capped at
Level0DesignNote.
