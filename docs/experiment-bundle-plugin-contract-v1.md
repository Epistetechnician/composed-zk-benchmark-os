# Experiment Bundle and Static Plugin Contract v1

State slice: `benchmark-os-experiment-bundle-plugin-contract-v1`.

Status: implemented for one local, hermetic generated-instance replay path.

Extension state slice: `benchmark-os-static-plugin-registry-dispatch-v1`.
Integrity extension: `benchmark-os-experiment-bundle-integrity-v1`.
Output-binding extension: `benchmark-os-plugin-output-binding-v1`.
Factory-catalog extension: `benchmark-os-experiment-plugin-factory-catalog-v1`.
Registry separation extension: `benchmark-os-plugin-registry-descriptor-only-separation-v1`.
Plugin-agnostic composition extension: `benchmark-os-experiment-plugin-agnostic-composition-v1`.
Binding access extension: `benchmark-os-plugin-composition-binding-access-v1`.
Source binding integrity extension: `benchmark-os-plugin-composition-source-binding-integrity-v1`.
Ordered binding access extension: `benchmark-os-plugin-composition-ordered-binding-access-v1`.
Canonical order extension: `benchmark-os-plugin-composition-canonical-order-v1`.
Projection adapter extension: `benchmark-os-plugin-composition-projection-adapter-v1`.
Projector provenance extension: `benchmark-os-plugin-composition-projector-provenance-v1`.
Packet-job projector injection extension: `benchmark-os-plugin-composition-packet-job-projector-injection-v1`.
Packet-job configuration extension: `benchmark-os-plugin-composition-packet-job-config-v1`.
Packet-store seam extension: `benchmark-os-plugin-composition-packet-store-seam-v1`.
Keyed receipt extension: `benchmark-os-plugin-composition-packet-store-keyed-receipt-v1`.
Job result extension: `benchmark-os-plugin-composition-packet-job-receipt-result-v1`.
Materialization handoff validation extension: `benchmark-os-plugin-composition-packet-store-materialization-handoff-validation-v1`.
Local JSON composition output handoff validation extension: `benchmark-os-local-json-composition-output-handoff-validation-v1`.
Packet-output handoff validation extension: `benchmark-os-experiment-packet-output-handoff-validation-v1`.

## Purpose

`zkbench-core` now exposes one uniform experiment lifecycle:

```text
prepare task -> execute model/runtime -> collect mechanisms -> evaluate -> package -> validate
```

The lifecycle emits an `ExperimentBundle` containing the same top-level
objects for every plugin:

- `ExperimentConfig`: versioned deterministic configuration bytes and digest;
- `ExperimentDataVersion`: source/version/provenance identity and digest;
- `ExperimentModelVersion`: model or runtime identity and digest;
- `MechanismLedger`: sparse mechanism measurements with explicit absence states;
- `ExperimentMetrics`: evaluator measurements with status/value/source bindings;
- `ExperimentReport`: deterministic summary, claim boundary, and non-claims;
- `ExperimentArtifactRef`: digest-bound references for all component payloads.

The bundle is an integrity manifest over typed records. It does not embed a
second copy of replay payloads and does not mutate the accepted Evidence
Ledger.

## Interfaces

The module `crates/zkbench-core/src/experiment.rs` defines four implementation
seams:

```rust
ExperimentTask::prepare() -> Result<ExperimentTaskInput>
ExperimentModel::execute(&ExperimentTaskInput) -> Result<ExperimentModelRun>
MechanismCollector::collect(&ExperimentTaskInput, &ExperimentModelRun)
    -> Result<MechanismLedger>
Evaluator::evaluate(&ExperimentTaskInput, &ExperimentModelRun, &MechanismLedger)
    -> Result<ExperimentEvaluation>
```

`ExperimentPlugin` composes the four seams for one complete run. The
serializable `ExperimentPluginRegistry` is a descriptor-only metadata
inventory. `ExperimentPluginFactoryCatalog` owns explicit in-process typed
factories, validates unique descriptors at registration, and verifies that an
instantiated plugin returns exactly the descriptor registered by its factory.
Plugin discovery is not dynamic, and no filesystem, process, network,
credential, or package-runtime path is introduced by this slice. A plugin
implementation can therefore register its typed construction state without
putting executable objects into metadata JSON.

The shipped `LocalJsonExperimentPluginFactory` owns its `GeneratorConfig` and
constructs the existing local plugin through the catalog. The metadata registry
does not construct or run plugins; callers that need executable behavior use
`ExperimentPluginFactoryCatalog`, while callers that need serializable
descriptors use `ExperimentPluginRegistry`.

`MetacognitiveMonitorControlExperimentPluginFactory` is the second typed
implementation. It packages seven valid frozen pure-data monitoring/control
cases, digest-bound synthetic case/result artifacts, sparse explicit mechanism
measurements, metrics, and a report through the same `ExperimentBundle` schema.
The malformed case remains excluded from the runnable bundle and is still
covered by the underlying adapter contract tests. The combined catalog exports
both descriptors without serializing executable factory state.
The existing adaptive observability and durable packet APIs remain compatible
with the Local JSON adapter while the generic composition seam is exercised
through a separate typed packet adapter below.

The generic `PluginCompositionRunner` now deepens that outer seam for any
validated plugin bundle. It emits a typed nine-slot `ExperimentArtifactBundle`
and a canonical `PluginCompositionConfig` whose bindings name inner artifact
kinds, URIs, and digests explicitly. The runner validates descriptor identity,
inner bundle identity, every source binding, outer identity, outer payload
digests, and the `Level0DesignNote` ceiling. It is now consumable by the shared
durable packet transport through `PluginCompositionPacket`; packet manifests,
sidecars, path safety, overwrite matching, and strict readback are shared with
the Local JSON compatibility adapter.

`PluginCompositionConfig::binding` is the strict access Interface for the
fixed outer-slot projection. It requires exactly one binding for a requested
slot, and generic outer construction consumes that Interface directly. A
malformed binding vector therefore cannot be silently projected by first-match
selection; the serialized vector shape and aggregate validation diagnostics are
unchanged.

`PluginCompositionBinding::source` is the exact-kind access Interface for an
inner source, while binding validation rejects duplicate inner kinds before
projection. Composed outer slots may still retain multiple distinct source
kinds; the invariant is uniqueness by kind, not a restriction to single-source
bindings.

`PluginCompositionConfig::bindings_in_order` is the canonical ordered
binding Interface. Generic outer construction and cross-validation consume
`OuterKind::ALL` through this accessor rather than maintaining independent
slot sequences. Validation also requires the serialized binding vector itself
to follow `OuterKind::ALL`; missing, duplicated, or permuted slots fail closed
before projection. The config vector remains serialized as before.

`PluginCompositionProjector` is the replaceable projection Interface. The
standard projector preserves the shipped mapping, while an explicit projector
constructor can supply a different valid inner artifact layout without editing
the generic runner. The projector returns the existing typed bindings; config
serialization, packet transport, outer-slot validation, digests, and the
`Level0DesignNote` ceiling remain owned by their existing Modules.

Each projector also exposes a validated `ModuleDescriptor` at construction.
The runner retains that descriptor and copies it into every newly emitted
`PluginCompositionConfig`. Config digests and packet readback therefore bind
the concrete replacement identity. Legacy v1 JSON may omit this additive field
and remains explicitly unattributed; it must not be reported as fully
attributed. Missing, malformed, or wrong-module identities fail before plugin
execution.

`ExperimentPacketComposition` is the durable transport seam. The Local JSON
composition and generic plugin-composition configs are its two concrete
adapters. The packet module owns canonical inner/config/outer JSON transport,
manifest identity, payload digests, symlink-aware writes, protected-root
checks, overwrite policy, and semantic readback. Each adapter owns only its
config serializer and cross-artifact validator. This keeps future plugin
materialization additive without duplicating filesystem integrity logic.

`ExperimentPacketJob` is the job-level seam over those adapters. It resolves a
registered descriptor, instantiates the selected plugin, runs generic
composition, materializes a `PluginCompositionPacket`, and returns only after
strict typed readback matches both the packet and manifest produced by the
writer. Existing constructors use the standard projector compatibility
Adapter, while additive projector-aware constructors carry a runtime-only
replacement through the same catalog, store, and strict readback choreography.
Projector descriptors are validated before plugin execution and invalid module
identities fail during job construction. Constructor validation rejects unknown
plugins before touching the output root; each job instance is one-shot.
`ExperimentPacketJobConfig` is the
typed request value for that seam: it validates identity, provenance, the
caller-owned packet-store destination, and protected-path entries before
catalog resolution. `ExperimentPacketJobRequest` is the storage-independent
identity/provenance value used by `new_with_request_and_store`, so an injected
non-filesystem store does not need a fake destination. The existing config
constructor remains a compatibility adapter for filesystem-shaped callers.
`PluginCompositionPacketStore` is the persistence seam;
the filesystem adapter delegates to the existing canonical writer and reader,
the in-memory adapter uses the same canonical output builder without durable
publication, and injected adapters can test choreography without filesystem
coupling. `KeyedPluginCompositionPacketStore` is the current persistence
interface: `PacketStoreKey` identifies plugin, experiment, and run, while
`PacketStoreReceipt` binds readback to the canonical packet-manifest digest.
The filesystem and in-memory adapters implement the keyed interface. The
historical unkeyed job constructor is routed through an explicit compatibility
adapter. The historical `PluginCompositionPacketStore` interface and its
upgrade adapter now live in the explicit
`experiment_packet_store_compat` compatibility module; the packet-store module
re-exports them only to preserve existing source imports. Receipt validation
rejects stale or cross-run output before the job returns it. The job is
orchestration only: it does not execute a model or process, access the network,
mutate evidence, or claim atomic filesystem transactions.

`ExperimentPacketJob::run_once_with_receipt` and its storage-independent
counterpart now return an `ExperimentPacketJobResult` containing the strict
readback output and the `PacketStoreReceipt` that binds it. The historical
`run_once` methods still return only the typed packet output for source
compatibility. This exposes the existing receipt without adding a second
materialization path or changing the local claim ceiling.

`ExperimentPacketJobRequest`, `ExperimentPacketJobConfig`,
`PluginCompositionConfig`, and `PacketStoreKey` also expose one validated
`PluginCompositionIdentity` value for the shared plugin, experiment, and run
tuple. Existing public string fields and serialized packet config fields
remain unchanged.

The identity constructor locality slice adds `PluginCompositionIdentity::new_at`
for Adapters that need a caller-owned diagnostic path. Composition config,
packet-job request, and keyed packet-store key accessors use this shared
Interface; the existing `new` constructor, validation paths, public fields,
serialized bytes, and claim ceilings remain unchanged. This is local metadata
plumbing only and does not authorize execution, publication, evidence
mutation, production readiness, benchmark superiority, or runtime authority.

The identity descriptor binding slice extends the `new_with_identity` Seam:
the supplied `PluginCompositionIdentity.plugin_id` must equal the instantiated
plugin descriptor id before a generic composition runner exists. This keeps
descriptor identity and caller-owned identity in one constructor invariant,
without changing packet schemas, serialized bytes, public runner signatures,
or claim ceilings.

The artifact-reference policy locality slice makes the crate-private
`ExperimentArtifactReferencePolicy` the shared construction Seam for generic
composition, generic observability, and local observability. Config and
binding-derived outer references therefore use the same identity, provenance,
and digest ordering. This preserves existing URIs, bytes, public APIs, and
claim ceilings while concentrating the invariant in one testable Module.

The output handoff validation slice adds `ValidatedPluginCompositionOutput`
with private fields, validated accessors, and `into_parts` for downstream
Adapters. `PluginCompositionRunner::run_validated_output` constructs this
typed handoff, and the active packet-job Adapter converts it directly into a
packet. The historical `PluginCompositionOutput`, `run`, and infallible
conversion remain available for source compatibility; `try_into_packet`
revalidates that public shape before conversion. This does not change packet
bytes, public fields, or the `Level0DesignNote` ceiling.

The materialization handoff validation slice adds
`ValidatedPacketStoreMaterialization` with private output and receipt fields.
The additive `KeyedPluginCompositionPacketStore::materialize_keyed_validated`
Interface validates the legacy public materialization result before exposing it
to the active packet job. Filesystem, in-memory, and compatibility Adapters
therefore share one receipt/output handoff contract; the legacy method and
`PacketStoreMaterialization` remain available for source compatibility. Packet
bytes, receipt fields, and the `Level0DesignNote` ceiling remain unchanged.

The packet-job result handoff slice keeps that validated pair private inside
`ExperimentPacketJobResult`. Read-only `output()` and `receipt()` accessors
serve observers, while `into_materialization()` is the explicit consuming
conversion for callers that need to carry the validated pair onward. The job
revalidates the strict readback output against the retained receipt before
returning the result. This prevents callers from receiving independently
mutable output and receipt fields that can drift after the store Seam.

The packet-output handoff slice adds `ValidatedExperimentPacketOutput` with
private output state and canonical manifest/digest validation. The existing
`ExperimentPacketOutput` remains the public compatibility shape, while keyed
packet-store materializations retain the validated value internally and expose
only read-only views or an explicit consuming conversion. This keeps packet
identity, manifest bytes, and typed packet contents together across replacement
Adapters without changing packet files, public compatibility fields, or the
`Level0DesignNote` ceiling.

The typed receipt-binding slice adds `PacketStoreReceipt::from_validated_output`
as the issuance Interface for generic packet stores. Raw `from_output` remains
a compatibility Adapter that first enters the validated packet-output seam;
receipt key identity and manifest digest binding are therefore issued in one
place. This does not add store provenance, change receipt fields, or elevate
the local `Level0DesignNote` claim ceiling.

The canonical typed transport slice adds validated packet read/write entry
points for local JSON and generic plugin-composition packets. Historical
packet functions remain compatibility Adapters over those entry points, so
serialized packet files and legacy output values remain byte/value-compatible.
Filesystem keyed storage now uses the typed writer and reader directly, and
the in-memory Adapter retains `ValidatedPacketStoreMaterialization` rather
than downgrading before storage. The additive `readback_keyed_validated`
Interface gives custom stores the same fail-closed upgrade path. This is
transport plumbing only; it adds no execution, publication, evidence
mutation, production readiness, benchmark superiority, or runtime authority.

The typed job readback slice routes `ExperimentPacketJobExecution` through
`readback_keyed_validated`, compares the retained and read-back typed packet
outputs, and returns the store's validated handoff directly. The historical
`readback_keyed` Interface remains the compatibility path through the default
Adapter implementation. `ExperimentPacketJobResult::validated_output` gives
observers a read-only typed view without reconstructing the output/receipt
pair. This concentrates readback equality and receipt binding in the job
Seam without changing packet files, legacy output fields, execution,
publication, evidence mutation, or the `Level0DesignNote` ceiling.

The scheduler budget transition slice validates the mutable budget change at
the observability allocation Seam. A replacement `ObservabilityScheduler` must
decrement exactly the selected tier, leave unrelated tiers unchanged, and
cannot select an exhausted tier. Decision validation and lifecycle transaction
semantics remain intact; this is local budget-accounting plumbing only and
adds no execution, publication, evidence mutation, production readiness,
benchmark superiority, or runtime authority.

The typed allocation receipt slice adds the compatibility-preserving
`ObservabilityScheduler::allocate_with_receipt` Interface. It isolates the
caller budget and binds `before_budget`, the validated decision, and
`after_budget` into one `ObservabilityAllocationReceipt`; failed transitions
leave the caller budget unchanged. This keeps replacement scheduler logic at
one Seam rather than making each runner reconstruct the transition invariant.
Serialized bundle fields and the `Level0DesignNote` claim ceiling remain
unchanged.

The allocation receipt lifecycle handoff slice keeps that typed scheduler
receipt intact through both composition Adapters' lifecycle transaction. The
tentative after-budget and mechanism decision are checked against the same
receipt before commit; a caller cannot replace the receipt with a detached
decision while retaining a valid-looking bundle. This is an internal
observability Interface improvement only and does not change serialized bundle
fields or the `Level0DesignNote` claim ceiling.

The append-only ledger precondition slice makes both mechanism and metric
meta-evaluation append Interfaces validate their existing digest chain before
accepting new evidence. A caller cannot append onto tampered history and defer
failure until serialization or later readback; failed appends leave the ledger
unchanged. Serialized fields, append ordering, compatibility access, and the
`Level0DesignNote` claim ceiling remain unchanged.

The local JSON composition output handoff slice adds
`ValidatedLocalJsonCompositionOutput` with private inner, config, and outer
fields. The additive `LocalJsonExperimentRunner::run_validated_output`
Interface constructs it through the complete projection validator. The
historical `run()` and `composition_config()` methods remain compatibility
Adapters, while the typed handoff keeps the nine-slot mapping and
`Level0DesignNote` ceiling unchanged. This is local metadata plumbing only;
it adds no execution, publication, evidence mutation, production readiness,
benchmark superiority, or runtime authority.

`ExperimentPlugin::run_validated` is the output-binding seam. It validates the
returned bundle before exposing it to callers, requiring descriptor version,
plugin id, model id, mechanism collector id, evaluator id, and every emitted
claim boundary to agree. Registry execution uses this path, so a plugin cannot
return a valid-looking bundle labeled as another implementation or with a
higher claim ceiling.

The additive `ValidatedExperimentPluginOutput` value makes that validation
evidence explicit at the seam. Catalog dispatch, generic composition, and the
local composition runner consume the descriptor-bound value; the historical
`run_validated` method remains an output-only compatibility adapter. Existing
bundle JSON and digest bytes are unchanged, and the value adds no execution,
publication, evidence mutation, or authority.

## Mechanism ledger

`MechanismLedger` is versioned independently from metrics and reports. Each
`MechanismMeasurement` has:

- a stable id and category;
- `Collected`, `NotCollected`, `Unsupported`, or `Failed` status;
- an optional deterministic value;
- an optional source artifact URI;
- a required reason whenever the value is absent.

The shared `MechanismRecord::validate_for_run` Interface adds active-run
admission above intrinsic ledger validation. Generic and local runner Adapters
bind experiment id, run id, scheduler decision, and collector descriptor in
one Seam. Failed collection records may omit a collector; non-failed elevated
records cannot silently substitute a different collector implementation.

Allocation permanence is read back through
`validate_observability_allocation_witness`, which reconstructs the typed
receipt from existing config, signals, decision, and metadata budget fields.
The helper is shared by generic run payloads and local composition payloads;
it adds no wire fields and retains the `Level0DesignNote` ceiling.

The serialized payload Adapter slice
`benchmark-os-observability-allocation-witness-payload-readback-v1` adds
`validate_serialized_experiment_run_payloads` and
`validate_serialized_local_json_composition_with_metadata`. These Adapters
authenticate canonical config and metadata bytes against the existing fixed
artifact references before comparing identities, module manifests, decisions,
budget transitions, and payload/reference provenance. The additive
`ValidatedExperimentRunPayloads` handoff keeps the generic config, metadata,
and allocation receipt together for runner and serialized-readback consumers.
The existing packet transport remains a composition-only compatibility Adapter
because it carries a metadata reference without the metadata payload bytes. No
execution, publication, Evidence Ledger mutation, or claim-boundary promotion
is implied.

The state slice
`benchmark-os-observability-append-only-digest-chain-kernel-v1` deepens the
append-only ledger Module with a private `AppendOnlyDigestChain` Kernel. Both
the mechanism and metric meta-evaluation Adapters use the same sequence,
predecessor, entry-digest, and tip-digest implementation, while retaining
their distinct public wire shapes and domain validation. This concentrates
chain correctness and tests at one Seam without changing transport or claim
semantics.

The state slice
`benchmark-os-observability-provenance-bound-payload-admission-v1` adds a
private `ArtifactPayloadAdmission` Kernel. Report, config, and metadata
readback Adapters satisfy the same provenance-bearing payload Interface after
their canonical bytes, kind, identity, and digest are checked. The historical
structural payload validator remains a compatibility Interface for callers
that do not have a provenance-bearing payload. This concentrates the
provenance equality invariant without changing serialized shapes or claim
semantics.

The local JSON collector records trace/state-transition summaries and marks
activation, attention, and causal-effect measurements `Unsupported` with
explicit reasons. This is deliberate absence, not a claim that ordinary replay
observations are mechanistic evidence.

## Shipped local plugin

`LocalJsonExperimentPlugin` composes:

- `LocalJsonExperimentTask` over the existing deterministic generator;
- `LocalJsonExperimentModel` over `LocalJsonAdapter` local oracle replay;
- `LocalReplayMechanismCollector`;
- `LocalReplayEvaluator`.

The emitted bundle carries eight required artifact references: configuration,
data version, model version, mechanism ledger, metrics, report, replay
manifest, and replay result. JSON serialization and bundle digests are
deterministic for the schema version.

## Validation and claim ceiling

`validate_experiment_bundle` rejects unsupported schema versions, missing or
duplicate artifact identities, malformed digests, unknown measurement sources,
inconsistent measurement status/value/reason combinations, missing
non-claims, claim-boundary escalation, internal config/model digest drift, and
incompatible metric or mechanism value variants.

`validate_experiment_plugin_output` adds the descriptor-to-bundle checks after
bundle validation. It does not authorize execution or promotion; it only makes
the static plugin seam fail closed on output identity and claim drift.

State slice: `benchmark-os-experiment-bundle-validated-readback-v1`.

`ValidatedExperimentBundle` is the typed readback Interface for the inner
experiment bundle. Its canonical-JSON constructor parses, rejects byte drift,
and validates component digests, artifact completeness, measurement sources,
and claim ceilings before exposing the bundle to a packet Adapter. Generic and
local composition packet readback both consume this handoff, so those Adapters
cannot diverge in their inner-bundle acceptance rules. The existing raw
deserializer remains available for compatibility, while the validated handoff
is required for packet transport. No serialized fields or claim ceiling change.

The factory catalog is separate construction infrastructure. Its metadata
projection contains descriptors only; factory state and plugin pointers are
never serialized. Catalog execution calls `run_validated`, and composition
runner execution uses the same path so injected plugins cannot bypass output
binding.

The current ceiling is `Level1LocalReplay`. The slice does not establish
official benchmark evidence, ZK backend performance, interpretability,
introspection, causal validity, independent reproduction, production
readiness, or runtime authority.

The second plugin is intentionally capped at `Level0DesignNote`. Its presence
proves a second typed implementation at the plugin seam; it does not turn the
synthetic cases into model execution or scientific evidence.

## Benchmark OS Track: Plugin Composition Canonical Order

Status: complete for named state slice
`benchmark-os-plugin-composition-canonical-order-v1`.

`PluginCompositionConfig::validate` now requires the serialized binding vector
to match `OuterKind::ALL` position-for-position. The ordered Interface remains
the sole access path used by generic outer construction and cross-validation,
so a task/prompt permutation cannot be normalized into a different valid
bundle. This changes validation strictness only; serialization, digests, and
the `Level0DesignNote` claim ceiling remain unchanged.

## Benchmark OS Track: Plugin Composition Projector Provenance

Status: complete for named state slice
`benchmark-os-plugin-composition-projector-provenance-v1`.

`PluginCompositionProjector` now declares a fallible `ModuleDescriptor`. The
runner validates and retains module id, implementation id, version, and source
revision before any plugin run. Standard and replacement projectors therefore
have explicit runtime identity. This earlier slice did not persist the
descriptor; the durable attribution extension below closes that boundary
without changing execution authority, evidence status, or the
`Level0DesignNote` ceiling.

## Benchmark OS Track: Packet-Job Projector Injection

Status: complete for named state slice
`benchmark-os-plugin-composition-packet-job-projector-injection-v1`.

The packet job now carries a replaceable `PluginCompositionProjector` through
construction and routes execution through the descriptor-aware composition
constructor. Existing filesystem, compatibility-store, keyed-store, and
storage-independent constructors default to `StandardPluginCompositionProjector`;
additive projector-aware constructors allow a replacement projection to reach
the complete catalog -> composition -> packet store -> strict readback path.
Descriptor validation occurs before plugin execution. Packet schemas,
manifests, serialized config, digests, one-shot behavior, authority, evidence
status, and the `Level0DesignNote` ceiling remain unchanged.

## Benchmark OS Track: Durable Projector Attribution

Status: complete for named state slice
`benchmark-os-plugin-composition-projector-durable-attribution-v1`.

New generic composition configs carry the validated projector
`ModuleDescriptor` in an additive optional field. The standard and replacement
projectors therefore remain swappable while the serialized config digest,
outer config reference, packet manifest, and strict filesystem/in-memory
readback retain which implementation produced the bindings. Equivalent
projectors intentionally produce distinct config JSON and config digests even
when their binding values match. Receipt-bound packet jobs retain that
distinction transitively: the receipt key remains the experiment/run identity,
while its manifest digest changes with the attributed composition config.

The field remains optional only to read legacy v1 config JSON that predates
this slice. Such a config validates its existing binding contract but is
explicitly not durably projector-attributed. The change does not authorize
execution, mutate the accepted Evidence Ledger, alter packet-store authority,
or raise the `Level0DesignNote` ceiling.

## Benchmark OS Track: Durable Composition-Adapter Attribution

Status: complete for named state slice
`benchmark-os-plugin-composition-adapter-durable-attribution-v1` and
`benchmark-os-observability-composition-adapter-durable-attribution-v1`.

New generic and local composition configs carry an optional validated
`ModuleDescriptor` for the concrete composition Adapter that emitted them.
The existing `adapter_id` remains the compatibility gate; the descriptor adds
module identity, implementation identity, version, and source revision. The
descriptor is included in canonical config bytes, so config digests, outer
config references, packet manifests, and strict readback retain which
composition Adapter produced the record.

Legacy v1 configs may omit the additive descriptor and remain semantically
readable, but callers can detect that they are not durably composition-adapter
attributed. Descriptor identity drift fails closed before projection or
readback. This slice adds no execution, publication, evidence mutation,
runtime authority, or claim-boundary elevation.

## Benchmark OS Track: Plugin Composition Projection Adapter

Status: complete for named state slice
`benchmark-os-plugin-composition-projection-adapter-v1`.

`PluginCompositionRunner` now accepts a runtime-only
`PluginCompositionProjector`. Existing constructors use the
`StandardPluginCompositionProjector` compatibility Adapter; callers with a
different valid inner artifact layout can inject a replacement projector. The
serialized `PluginCompositionConfig`, packet files, outer nine-slot shape,
digest rules, execution authority, and claim ceiling are unchanged.
