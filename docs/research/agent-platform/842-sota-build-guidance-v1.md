# HSAI Agent Platform SOTA Build Guidance V1

## Status and state slice

This document is an additive, source-backed design appendix under named state
slice `hsai-proof-carrying-capability-bounded-agent-platform-sota-build-
guidance-v1`.

It translates relevant public state-of-the-art methods and infrastructure into
bounded implementation choices for
[`841-parallel-build-plan-v1.md`](841-parallel-build-plan-v1.md). It is a
reference synthesis, not an authorization for model execution, provider
execution, dataset acquisition, cryptographic signing, settlement, deployment,
or changes to any closed Astral or Oak Lab slice.

The current implementation ceiling remains local pure-data control-plane and
caller-owned file-persistence contract evidence. No source below raises that
ceiling.

## How to use SOTA information

“SOTA” is a moving reference label, not a security property or a product
claim. The platform must pin every adopted implementation to:

```text
source URL
license and redistribution status
upstream revision or released version
build recipe and artifact digest
runtime and hardware assumptions
declared trust, threat, and collusion model
claim ceiling and independent acceptance record
```

Public work may inform a clean-room implementation only. Do not copy code,
artifacts, datasets, traces, generated outputs, or private data. A paper,
benchmark, framework, or vendor document can establish design context; it
cannot establish that this repository has reproduced the result.

## Recommended SOTA reference map

| Seam or concern | Relevant reference | Adopt | Do not infer |
| --- | --- | --- | --- |
| Agent evaluation | [Inspect](https://inspect.aisi.org.uk/) and its [agent support](https://inspect.aisi.org.uk/agents.html) | A composable evaluation-runner Interface for datasets, agents, tools, scorers, limits, checkpointing, interventions, traces, and error recovery | A framework run is independent validation, general safety, or production evidence by itself |
| Agent security | [AgentDojo](https://proceedings.neurips.cc/paper_files/paper/2024/hash/97091a5177d8dc64b1da8bf3e1f6fb54-Abstract-Datasets_and_Benchmarks_Track.html), [tau-bench](https://arxiv.org/abs/2406.12045), and the [tau2-bench repository](https://github.com/sierra-research/tau2-bench) | Attack-family taxonomy, dynamic tool environments, policy-constrained conversations, and pass-k reliability metrics as benchmark design input | Public benchmark scores transfer to this runtime, or public benchmark data may be copied without a separate license and custody review |
| Tool interoperability | [MCP specification](https://modelcontextprotocol.io/specification/2025-06-18/server/index) and [tool requirements](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) | Typed tool/resource/prompt discovery behind a capability broker, explicit consent, deterministic listings, input/output schemas, and server identity | A tool description, annotation, server capability, or MCP connection grants authority; MCP itself enforces the security policy |
| Agent threat coverage | [OWASP Agentic Threats Navigator](https://genai.owasp.org/resource/owasp-gen-ai-security-project-agentic-threats-navigator/) and [red-teaming taxonomy](https://genai.owasp.org/resource/solutions-landscape-red-teaming-taxonomy/) | Coverage vocabulary for reasoning, memory, tools, identity, human oversight, and multi-agent interactions; repeatable red-team capability categories | A taxonomy is a completed threat model, mitigation, or evidence of resistance |
| Agent observability | [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/) and [GenAI span guidance](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md) | Versioned spans for inference, retrieval, memory, tool execution, model/provider identity, token usage, latency, errors, and trace correlation with redaction | Telemetry is proof of behavior, causality, privacy, alignment, or a safe rollback; experimental conventions can be treated as stable without pinning |
| High-isolation execution | [Firecracker production host guidance](https://github.com/firecracker-microvm/firecracker/blob/main/docs/prod-host-setup.md) and [design](https://github.com/firecracker-microvm/firecracker/blob/main/docs/design.md) | A microVM Adapter with KVM, Jailer, seccomp, cgroups, namespaces, privilege dropping, resource limits, and explicit host hardening | A container, seccomp profile, or pure-data permit is equivalent to complete isolation |
| Lower-overhead sandbox | [gVisor](https://gvisor.dev/docs/) and its [security architecture](https://gvisor.dev/docs/architecture_guide/intro/) | A separately evaluated sandbox Adapter when its Sentry/runsc model and workload limits fit the threat model | gVisor and Firecracker have identical isolation, compatibility, latency, or escape-resistance properties |
| Artifact provenance | [in-toto specifications](https://in-toto.io/docs/specs/), [SLSA version guidance](https://slsa.dev/spec/v1.0/whats-new), and [Sigstore transparency logging](https://docs.sigstore.dev/logging/overview/) | Attestation subjects, build steps, provenance predicates, verification, transparency-log references, and immutable release records | Signed provenance proves semantic correctness, safe behavior, truthful inputs, or evaluator independence |
| Model serving | [vLLM serve](https://docs.vllm.ai/en/latest/cli/serve/), [structured outputs](https://docs.vllm.cc/en/latest/features/structured_outputs/), and [security guidance](https://github.com/vllm-project/vllm/blob/main/docs/usage/security.md) | Structured-output schemas, canonical hash configuration, prefix-cache controls, tenant-scoped cache salts, and explicit serving identity | Prefix caching is safe across tenants, or a serving framework supplies policy enforcement and rollback authority |
| Parameter-efficient adaptation | [LoRA](https://arxiv.org/abs/2106.09685) and [QLoRA](https://arxiv.org/abs/2305.14314) | Immutable-base candidate adapters, fixed budgets, reproducible manifests, shadow execution, independent evaluation, and rollback | Adapter efficiency is alignment, improvement, privacy, or benchmark superiority |
| Rust control verification | [Kani Rust Verifier](https://model-checking.github.io/kani/) and its [proof-harness guidance](https://model-checking.github.io/kani/usage.html) | Bounded proof harnesses and concrete playback for pure control-plane invariants, with an explicit resource and concurrency scope | Bounded model checking proves the whole distributed runtime or all possible concurrent executions |
| Verifiable compute | [RISC Zero](https://dev.risczero.com/), its [receipt contract](https://docs.rs/risc0-zkvm/latest/risc0_zkvm/struct.Receipt.html), and [Boundless proving stack](https://docs.boundless.network/provers/proving-stack) | Program/image identity, committed inputs, typed journals, receipt verification, prover bidding, lock-in, proof, verification, and conditional release as separate Interfaces | A receipt proves input truth, task usefulness, availability, alignment, or human benefit; a proving market is automatically an oracle |
| FHE | [OpenFHE](https://github.com/openfheorg/openfhe-development) and its [library documentation](https://github.com/openfheorg/openfhe-development/blob/main/docs/index.rst) | A fixed scheme and parameter manifest behind a later privacy Adapter; record approximation, key, noise, leakage, and threat assumptions | FHE automatically supplies correctness, availability, low latency, output privacy, or protection from metadata leakage |
| MPC | [MP-SPDZ documentation](https://mp-spdz.readthedocs.io/en/latest/) | A fixed protocol, party roster, corruption model, input/output policy, liveness budget, and collusion declaration behind a later MPC Adapter | Input privacy guarantees honest execution, availability, non-collusion, or safe outputs |
| Frontier governance | [Anthropic Responsible Scaling Policy](https://www.anthropic.com/responsible-scaling-policy), [OpenAI Preparedness Framework](https://openai.com/index/updating-our-preparedness-framework/), [OpenAI Frontier Governance Framework](https://openai.com/index/openai-frontier-governance-framework/), and [Google DeepMind Frontier Safety Framework](https://deepmind.google/frontier-safety/) | Capability thresholds, risk reports, safeguard readiness, incident response, external review, and lifecycle reassessment as governance patterns | A vendor policy is an independent assessment of this platform or a substitute for its release authority |
| Outcome-priced work | [Futarchy Labs](https://docs.futarchy.fi/), [Math Market](https://openreview.net/pdf?id=uQPYAOHyPf), [Diagon](https://arxiv.org/abs/2604.06688), and the [outcome-priced work plan](843-outcome-priced-work-market-plan-v1.md) | Market signals for task selection, review forecasting, contribution pricing, and bounded work incentives, with independent resolution and payment Adapters | A market price is not a correctness proof, calibrated probability, alignment guarantee, or payment authorization |

The source register at the end records the review date and the intended
provenance treatment. Version claims remain source-dated and must be refreshed
before implementation intake.

## Architecture decisions derived from the references

### 0. Treat tool protocols as untrusted capability descriptions

MCP is a useful interoperability Interface for resources, prompts, and tools.
The control plane must remain the authority that decides whether a particular
tool may be invoked. Tool names, descriptions, annotations, output links,
server metadata, and server-requested sampling are untrusted until the server,
version, policy, scope, and data flow are independently accepted.

The tool Adapter must bind:

```text
server identity and revision
tool name and input/output schemas
requested capability and tenant scope
consent and release authority
egress and secret policy
spend, time, concurrency, and output limits
tool-list digest and change notification state
```

Tool discovery is not admission. A changed tool list invalidates the cached
manifest and forces revalidation before the next invocation. The model may
propose a tool call, but only the capability broker can issue a short-lived
lease and only an external executor can enforce it.

### 0.1 Make telemetry useful without making it authoritative

OpenTelemetry GenAI conventions provide a strong vocabulary for correlating
inference, retrieval, memory, and tool spans with provider, model, token, cost,
latency, and error data. The telemetry Adapter should use a pinned convention
revision and a redaction policy. Prompts, outputs, tool arguments, secrets,
personal data, and hidden benchmark bytes must not be captured by default.

Telemetry is an observation stream. It can trigger a monitor or incident
record, but it cannot itself authorize execution, validate a claim, establish
causality, or prove that rollback occurred. A telemetry gap is either a
quarantine or an explicitly recorded observability nonclaim, never an assumed
healthy run.

### 1. Keep the control plane independent of the runner

The control plane owns typed proposals, capability narrowing, admission,
leases, replay, rollback, freeze, claim ceilings, and release decisions. A
runner is an Adapter behind a Seam. This permits a local deterministic runner,
a Firecracker runner, a gVisor runner, and later a verifiable-compute runner to
share one Interface without pretending they have the same guarantees.

The smallest accepted execution record should bind:

```text
proposal_digest
policy_digest
capability_digest
lease_id and validity window
runtime_identity and build digest
program or model identity
input commitment
output schema and result digest
receipt or attestation reference
observation and termination disposition
```

Runner metadata is not trusted merely because it is self-reported. Metadata
that is not cryptographically or independently verified cannot drive admission,
settlement, or a claim ceiling.

### 2. Make evaluation a first-class Adapter

The evaluation Interface should support Inspect-like composition without
making Inspect a required runtime dependency:

```text
EvalSpec
  -> DatasetManifest
  -> Agent/Tool Adapter
  -> Scorer and policy set
  -> limits, checkpoint, and intervention controls
  -> locked predictions/configuration
  -> aggregate result and claim envelope
```

The first local implementation should use clean-room semantic families. Public
AgentDojo, tau-bench, tau2-bench, and future tau3-bench material belongs in a
separate licensed-intake or replication slice. Its use requires exact source,
license, version, corpus digest, split identity, and an independent review.

The evaluation Adapter cannot select its own evaluator, alter the held-out
split, unlock predictions, or promote a candidate. It returns evidence to the
evidence plane; it does not accept its own evidence.

### 3. Select isolation by threat model, not by branding

The initial runtime should define two explicit isolation profiles:

| Profile | Intended use | Required controls | Ceiling until independently tested |
| --- | --- | --- | --- |
| `high_value_untrusted` | Untrusted code, secrets-adjacent work, or external-network capability | Firecracker/Jailer or an equivalent microVM, non-root execution, seccomp, cgroups, namespaces, minimal device/filesystem view, egress broker, secret broker, kill path, resource ceilings, host hardening | Design-level isolation contract only |
| `bounded_compatibility` | Lower-risk development and controlled evaluation workloads | gVisor or another explicitly selected sandbox, restricted filesystem, egress deny-by-default, tenant identity, resource ceilings, kill path | Design-level sandbox contract only |

The selection itself must be recorded in the runtime manifest. “Sandboxed” is
not a claim until an external test demonstrates the declared properties under
the declared kernel, runtime, hardware, configuration, and attack families.

### 4. Use provenance standards as record formats, not as semantic oracles

The evidence plane should model an artifact as a subject with a digest and a
provenance graph. Adopt the shape of in-toto/SLSA-style subjects and steps,
then use Sigstore/Rekor-like transparency references when the deployment
environment supports them. The local repository may first implement canonical
records and verification Interfaces without claiming external signing.

Every attestation must separate:

- what was signed or logged;
- who or what authenticated it;
- which build or input bytes it binds;
- which claims remain unverified;
- when it expires or is revoked;
- whether the verifier is independent of the producer.

Transparency increases auditability. It does not repair a bad build, malicious
input, compromised signer, weak evaluator, or incorrect policy.

### 5. Treat serving caches as a tenant-isolation concern

The serving Adapter must bind tenant identity and cache policy before enabling
prefix caching. vLLM’s security guidance identifies shared prefix-cache timing
as a leakage risk and documents cache salting as a mitigation. Therefore:

```text
tenant_id -> cache_salt -> cache namespace
```

is part of the serving contract. A missing tenant identity, stale salt, or
cross-tenant cache hit is a quarantine event. Structured outputs should be
validated against a versioned schema before they become typed proposals or
evidence records. Canonical serialization and hashing must be shared by all
language implementations.

### 6. Use LoRA/QLoRA only inside the candidate-adaptation gate

LoRA and QLoRA are implementation options for producing a candidate under a
fixed resource budget. The adapter manifest must bind the immutable base,
quantization mode, adapter bytes, tokenizer/runtime identity, training data
manifest, seed/transcript, optimizer configuration, resource accounting,
rollback target, and claim ceiling.

The production sequence remains:

```text
candidate
  -> independent fit/tune/assessment evaluation
  -> prediction lock
  -> HSAI admission
  -> shadow serving
  -> short-lived canary
  -> monitoring
  -> rollback or independent promotion
```

No live thread updates production weights. No adapter benchmark score is
accepted as an alignment result. No quantization choice may silently change
the model identity or evaluation target.

### 7. Prove the narrow kernel before expanding the runtime

Kani-style bounded harnesses are appropriate for pure Rust invariants such as:

- rejected admission does not mutate governed state;
- capability delegation cannot expand a set;
- expired leases cannot authorize execution;
- kill and freeze states have no authorized forward edge;
- journal sequence and digest links are preserved;
- canonical decode rejects ambiguous or noncanonical snapshots.

The existing implementation-diverse checker remains necessary. Formal harnesses
must record bounds, assumptions, unsupported concurrency cases, and resource
exhaustion. A proof result is a claim about the harness and model, not a proof
of OS enforcement or distributed linearizability.

### 8. Build the compute market around a typed receipt lifecycle

Boundless supplies a useful lifecycle pattern: request, bid/lock-in, proving,
verification, and reward release. RISC Zero documents the key cryptographic
binding: a receipt verifies successful execution for an expected program image
and exposes a committed journal; receipt metadata is not itself a security
binding.

The platform should reimplement only a narrow clean-room job class first:

```text
JobSpec
  -> Offer
  -> ExecutionRecord
  -> Receipt
  -> IndependentVerification
  -> SettlementAuthorization
```

The verifier must check the expected program identity, successful execution
status, journal/result schema, input commitment, deadline, and receipt
integrity. A raw integrity check is insufficient if the application requires
successful execution or a particular program. Provider reputation records
validity, latency, uptime, price, and dispute outcomes; it does not infer
alignment or input truth.

Ordinary receipts are the first implementation. A fixed zkVM, MPC protocol, or
FHE scheme is a later Adapter with a fresh version, threat model, custody
record, and independent acceptance. Hyperliquid and any other settlement
network remain a separately authorized settlement Adapter; neither the market
nor the chain is the verifier or policy authority.

### 9. Make privacy claims conditional and compositional

OpenFHE and MP-SPDZ cover useful families of FHE and MPC constructions, but
the platform must select a scheme or protocol only after freezing:

```text
computation class
precision and approximation requirements
party/threshold roster
honest or malicious corruption model
collusion threshold
key and share custody
output release policy
availability and timeout budget
metadata and side-channel treatment
```

Confidential execution and verifiable execution are separate properties. A
private result still needs correctness and release policy. A valid proof still
needs an output-leakage policy. The system must not market “private and
verified” as a single inherited property.

### 10. Convert frontier governance into release mechanics

The public governance frameworks converge on lifecycle risk assessment,
capability thresholds, safeguard readiness, reporting, incident response,
external review, and policy updates. The platform should convert those patterns
into machine-checkable release predicates:

```text
capability threshold crossed
  -> required safeguard set
  -> evidence and independent review
  -> release authority decision
  -> bounded deployment
  -> monitoring and incident response
  -> recurring reassessment or freeze
```

A release authority must remain separate from the model, evaluator, validator,
operator, signer, ledger, custody root, and settlement Adapter. Governance
documents inform the policy; they do not authorize this repository’s release.

## Wave-by-wave implementation map

### Wave 0 — contract freeze

Add these schema families to the registry before lane work begins:

```text
RuntimeIdentity
SandboxProfile
ToolManifest and ToolInvocation
EvalSpec and EvalRun
DatasetManifest
ArtifactAttestation
AdapterManifest
ProgramCommitment
InputCommitment
Receipt and VerificationResult
SettlementAuthorization
CapabilityThreshold
ReleaseDecision
TelemetryPolicy and ObservationRecord
```

For each, freeze canonical bytes, versioning, digest scope, expiry, signer or
validator role, independent-review requirement, and explicit nonclaims.

### Wave 1 — five lanes

- **Security kernel:** add bounded Kani harness targets and preserve the
  implementation-diverse checker. Define `ExecutionAdapter`, `KillAdapter`,
  and `FreezeAdapter` as Interfaces; do not implement OS authority in the
  pure-data crate.
- **Evidence plane:** model in-toto/SLSA-like subjects and steps, Sigstore-like
  transparency references, revocation, freshness, and verifier independence.
  External signing remains a separate Adapter.
- **Adversarial evaluation:** build clean-room families inspired by dynamic
  prompt injection, tool-use policy conflicts, pass-k reliability, evaluator
  gaming, exfiltration, OWASP agentic threat surfaces, and rollback failure.
  Keep public benchmark intake
  separate from the local corpus.
- **Alignment measurement:** use composable eval controls and locked
  predictions, while keeping behavioral, mechanistic, and scalable-oversight
  claims distinct. Gemma V3 remains isolated under its exact state slice.
- **Runtime/deployment:** define Firecracker and gVisor profiles, serving
  identity, tenant cache salt, structured output validation, MCP tool
  manifests, OpenTelemetry redaction/version policy, supply-chain manifests,
  and runtime kill enforcement as separately reviewable Adapters.

### Wave 2 — integration gate

Add cross-lane tests for:

- tenant/cache namespace mismatch;
- changed or untrusted MCP tool metadata;
- tool-list digest or server-identity drift;
- telemetry containing unredacted prompts, outputs, arguments, or secrets;
- missing telemetry on a capability-bearing execution;
- stale or revoked runtime attestation;
- receipt integrity without successful-execution binding;
- program-image or input-commitment mismatch;
- evaluator/configuration drift after prediction lock;
- provenance signed by the producer but not independently reviewed;
- privacy result released outside the declared output policy;
- settlement attempted before verification;
- a monitor decision with no externally enforceable executor.

### Wave 3 — first product wedge

Use a frozen-base serving runtime with structured outputs and tenant-scoped
cache policy. Begin with consented retrieval memory. Treat MCP tools as
untrusted until server and tool manifests pass the capability broker. Emit
redacted, version-pinned GenAI telemetry. Produce LoRA/QLoRA candidates only in
shadow mode. Every response and adaptation event binds model, adapter,
tokenizer, runtime, tenant, policy, cost, latency, and result digests.

### Wave 4 — fixed compute-market bridge

Implement ordinary receipts and deterministic failure handling before any ZK,
MPC, FHE, or chain integration. The later cryptographic Adapter must include a
conformance suite against the ordinary receipt Interface and must preserve the
program/input/output/settlement bindings.

### Waves 5–6 — adaptation, governance, and marketplace

Add capability thresholds, safeguard matrices, incident response, recurring
review, revocation, license checks, and public aggregate claim packets. List
validated specialists only after serving isolation, provenance, quality,
privacy, economics, and rollback gates pass. Never list an unreviewed weight
file as a trusted specialist.

## SOTA-derived acceptance checklist

```text
[ ] Every external reference has URL, license status, version/revision, and digest record
[ ] Clean-room implementation has no copied code, data, traces, or generated output
[ ] Eval runner is an Adapter; it cannot accept or promote its own evidence
[ ] Public benchmark intake is isolated from clean-room local benchmark families
[ ] MCP tool/server identity, schema, consent, capability, and tool-list digest are checked before invocation
[ ] Tool metadata and annotations are treated as untrusted unless independently trusted
[ ] GenAI telemetry pins a convention revision and redacts prompts, outputs, secrets, and protected data by default
[ ] Telemetry gaps cannot silently become healthy execution or authorization
[ ] Runtime isolation profile names kernel, hypervisor/sandbox, limits, egress, secrets, and kill path
[ ] Serving identity binds tenant, cache policy/salt, base, adapter, tokenizer, runtime, and schema
[ ] Prefix-cache behavior is tested for cross-tenant timing and namespace leakage
[ ] Provenance distinguishes producer assertions from independent validation
[ ] Formal harnesses declare bounds, assumptions, concurrency scope, and exhaustion behavior
[ ] Receipt verification checks expected program, successful status, commitments, schema, and deadline
[ ] Settlement is impossible before independent verification and separate authorization
[ ] FHE/MPC records precision, key/share custody, collusion, liveness, output, and metadata assumptions
[ ] Candidate adaptation is immutable-base, shadow-only, independently evaluated, canaried, and revocable
[ ] Governance thresholds map to safeguards, release authority, monitoring, and reassessment
[ ] Every result has the narrowest state-slice claim ceiling
```

## Explicit non-adoption decisions

The platform will not:

- call HEIR a universal production-ready transparent cryptography backend;
- combine arbitrary agents, GPU routing, FHE, MPC, ZK, futures, reputation,
  and outcome markets in the first product;
- let MCP discovery, tool annotations, or server-requested sampling bypass the
  capability broker or consent policy;
- retain raw GenAI prompts, outputs, tool arguments, secrets, or protected
  benchmark bytes in telemetry by default;
- treat a provider bid, market match, reputation score, or chain transaction
  as proof of correctness, alignment, or input truth;
- share prefix caches across tenants without a verified tenant-scoped policy;
- treat a signed or transparent provenance record as semantic validation;
- copy public benchmark datasets into the repository without a dedicated
  license, custody, and provenance slice;
- let a model choose its evaluator, validator, policy, signer, or release
  authority;
- promote a candidate based on local tests, one positive run, or framework
  compatibility alone;
- claim production security before external runtime testing, incident drills,
  and independent replication.

## Source register

Sources were reviewed on 2026-09-07. This register records design context only;
it is not a frozen dependency lock.

| Source | Observed information used | Intake treatment |
| --- | --- | --- |
| [Inspect](https://inspect.aisi.org.uk/) | Composable datasets, agents, tools, scorers, providers, tracing, limits, and recovery | Framework reference; pin release and license before use |
| [AgentDojo](https://arxiv.org/abs/2406.13352) | Dynamic prompt-injection environment and agent security evaluation framing | Research reference; no corpus reuse without rights |
| [tau-bench](https://arxiv.org/abs/2406.12045) | Tool-agent-user interaction, policy-constrained databases/APIs, and pass-k reliability | Research reference; construct local clean-room analogs first |
| [MCP specification](https://modelcontextprotocol.io/specification/2025-06-18/server/index) and [tool spec](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) | Standardized context, prompt, and tool integration; tool annotations remain untrusted without a trusted server | Protocol Adapter candidate; pin revision, server identity, consent, schemas, and capability policy |
| [OWASP Agentic Threats Navigator](https://genai.owasp.org/resource/owasp-gen-ai-security-project-agentic-threats-navigator/) and [red-team taxonomy](https://genai.owasp.org/resource/solutions-landscape-red-teaming-taxonomy/) | Agent attack surfaces and repeatable red-team capability vocabulary | Threat-model reference; not mitigation or evidence |
| [OpenTelemetry GenAI conventions](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/) and [span guidance](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md) | Versioned inference, retrieval, memory, tool, token, latency, and provider telemetry vocabulary | Observation Adapter; pin the revision and redact content by default |
| [Firecracker production host](https://github.com/firecracker-microvm/firecracker/blob/main/docs/prod-host-setup.md) | KVM isolation, Jailer, seccomp, cgroups/namespaces, privilege dropping, host limits | Runtime candidate; exact release/configuration and external tests required |
| [gVisor](https://gvisor.dev/docs/) | Per-sandbox application-kernel model through Sentry/runsc | Runtime candidate; threat-model-specific validation required |
| [in-toto](https://in-toto.io/docs/specs/) | Attestation and provenance specification family; stable v1.0 reference | Record-format reference; version and license must be pinned |
| [SLSA version guidance](https://slsa.dev/spec/v1.0/whats-new) | Version transition and provenance/verification changes; current version must be refreshed | Do not call v1.0 current; pin the version actually adopted |
| [Sigstore/Rekor](https://docs.sigstore.dev/logging/overview/) | Append-only tamper-evident transparency-log model | Optional deployment Adapter; not semantic validation |
| [vLLM serving](https://docs.vllm.ai/en/latest/cli/serve/) | Structured outputs, prefix caching, canonical serialization/hash options | Serving candidate; tenant cache and identity tests required |
| [vLLM security](https://github.com/vllm-project/vllm/blob/main/docs/usage/security.md) | Prefix-cache timing leakage and cache-salt mitigation | Mandatory threat-model input for multi-tenant serving |
| [LoRA](https://arxiv.org/abs/2106.09685) and [QLoRA](https://arxiv.org/abs/2305.14314) | Parameter-efficient candidate adaptation and memory-saving quantization | Candidate-generation options; no automatic quality or alignment claim |
| [Kani](https://model-checking.github.io/kani/) | Bounded model checking and proof harness workflow for Rust | Kernel proof Adapter; bounds and unsupported cases recorded |
| [RISC Zero](https://dev.risczero.com/) and [receipt API](https://docs.rs/risc0-zkvm/latest/risc0_zkvm/struct.Receipt.html) | Program/image-bound receipts, journals, successful-execution verification, and receipt metadata caveat | Fixed compute Adapter candidate; exact release and independent verification required |
| [Boundless proving stack](https://docs.boundless.network/provers/proving-stack) and [proof lifecycle](https://docs.boundless.network/developers/proof-lifecycle) | Broker market, prover bidding/lock-in, proof, verification, and reward release | Market lifecycle reference; no dependency or provider evidence |
| [OpenFHE](https://github.com/openfheorg/openfhe-development) | BFV/BGV/CKKS, FHEW/TFHE, hybrid schemes, threshold extensions; repository reports v1.5.1 on its reviewed page | Later privacy Adapter; version/license/parameters and threat model required |
| [MP-SPDZ](https://mp-spdz.readthedocs.io/en/latest/) | MPC framework spanning security models, secret sharing, HE, garbled circuits, and input/output controls | Later privacy Adapter; fixed protocol and collusion/liveness record required |
| [Anthropic RSP](https://www.anthropic.com/responsible-scaling-policy) | Capability-triggered safeguards, risk reports, external review, and policy updates | Governance pattern; not platform evidence |
| [OpenAI Preparedness Framework](https://openai.com/index/updating-our-preparedness-framework/) and [Frontier Governance Framework](https://openai.com/index/openai-frontier-governance-framework/) | Safeguard readiness, risk reporting, security, incident response, and external input | Governance pattern; not platform evidence |
| [Google DeepMind Frontier Safety Framework](https://deepmind.google/frontier-safety/) | Capability levels, lifecycle detection, proactive mitigation, and external parties | Governance pattern; not platform evidence |

## Claim ceiling

This appendix establishes only a local, source-backed architecture reference.
It does not establish that any listed system is the best available system, that
the repository has implemented or integrated it, that the repository has the
right to redistribute its code or data, or that any resulting runtime is
secure, private, correct, aligned, available, production-ready, or authorized
to move value.

Any implementation derived from this appendix must create a fresh state slice,
freeze its exact inputs and versions, pass the applicable lane gate, and
publish only the narrowest accepted claim.
