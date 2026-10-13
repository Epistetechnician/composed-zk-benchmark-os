# Privacy-Preserving Decision Model PRD V1

State slice: **private-decision-model-privacy-prd-v1**.

Status: **DESIGN_ONLY**.

Baseline repository revision: 62bf2bfb5b6775327eb635d722bd2a715a2c6a42.

Assurance: no implementation, test run, model execution, external review, or reproduction has occurred for this PRD. Data and artifact custody: this document and public documentation links only. Claim ceiling: **DesignOnlyPrivateDecisionModelArchitectureV1**. The next gate is choosing one target workload and its privacy promise before implementation or evaluation is proposed.

This state slice authorizes this design document and its README navigation entry only. It does not authorize source changes, external code or model acquisition, data collection, model execution, provider calls, spend, credential setup, reviewer submissions, publication, production deployment, Evidence Ledger changes, or claims about security, utility, performance, novelty, or production readiness. Existing Jevlike and proof-carrying-nano slices remain unchanged; their data and results are not inputs to this proposal.

## Executive decision

Build a small, typed decision service that takes a private context and a bounded set of options, then returns a choice and calibrated scores. The system must name its privacy mode per run.

There are two distinct modes:

1. **FHE mode:** the service evaluates ciphertexts. The compute server does not receive sensitive inputs in plaintext, if the exact protocol keeps every sensitive operand encrypted.
2. **TEE mode:** an attested workload decrypts and processes data inside a hardware-protected environment. This can support a “protected data in use under a named hardware trust model” claim. It is not computation over ciphertext. It trusts the CPU, GPU, firmware, driver, and attestation chain.

Use a small open decision model as the first target. “Jev-like” describes the input/output shape; it does not imply access to TypeSafe’s Jev weights or permission to send private data to its hosted API. TypeSafe describes Jev as a structured decision model, but this project must use a model and runtime whose deployment and privacy interfaces can be inspected and pinned. [TypeSafe’s System One announcement](https://typesafe.ai/blog/introducing-system-one-models-and-jev)

**Recommended sequence:** establish a local cleartext baseline; prove FHE inference for a deliberately small scorer; separately test a supported encrypted-training protocol; then compare a TEE path if the workload needs model capacity or latency that FHE cannot meet. Do not describe the TEE path as encrypted training. Do not assume that a commercial H100 rental has confidential-computing support because it has an H100.

## 1. Problem and users

Organizations may want structured classification, routing, or ranking over records they cannot disclose to a model host. A normal hosted endpoint can encrypt traffic and storage while still processing plaintext. This project tests whether a compact decision workload can keep inputs, labels, and intermediate state protected during remote computation under a clearly stated privacy mode.

Primary users:

- A data owner who controls source records and decryption keys.
- An ML engineer who trains and evaluates a bounded decision model.
- An operator who deploys the compute service without receiving the owner’s secret keys or raw data outside an explicitly selected TEE boundary.

The first workload is a synthetic variable-option ranking task. Each example has a context, two to eight candidate options, and a label naming the preferred option. The initial secure scorer consumes a fixed-width feature vector built on the owner’s device; it does not run a general-purpose text generator or arbitrary long-context transformer under FHE. The feature encoder, token lengths, and option count are part of the data-flow and metadata analysis.

## 2. Product goals and non-goals

### Goals

- Define and demonstrate separate FHE and TEE execution profiles with no ambiguity about where plaintext can exist.
- Provide a local client that validates records, manages owner-held keys, prepares requests, and decrypts only the intended result.
- Train and evaluate a compact option scorer against a matched cleartext baseline.
- Keep raw contexts, labels, tokens, embeddings, activations, logits, gradients, optimizer state, and per-example results out of ordinary server logs and repository artifacts.
- Measure predictive quality, calibration, latency, resource use, and total cost for the same frozen synthetic workload.
- Make failure, unavailable attestation, unsupported model operations, and missing measurements visible and fail closed.

### Non-goals for V1

- A general encrypted LLM or arbitrary transformer training service.
- Access to, integration with, or claims about the internals of hosted Jev.
- Protecting model weights from the client. FHE input privacy does not by itself hide server-side model weights.
- Secure aggregation, federated learning, multi-owner MPC, differential privacy, or formal cryptographic certification.
- Real sensitive records, production users, public deployment, or a multi-tenant SaaS product.
- Assuming H100 hardware accelerates FHE. Hardware benefit must be measured for the selected library and workload.

## 3. Privacy modes and threat model

| Property | FHE mode | TEE mode |
|---|---|---|
| Server sees input plaintext | No, if the chosen protocol keeps all sensitive operands encrypted | Plaintext exists inside the attested workload boundary |
| Main trust | Cryptographic scheme, parameters, implementation, and client key custody | CPU/GPU hardware, firmware, driver, measured software, verifier, and policy |
| Intermediate computation | Ciphertext or protocol-specific client/server shares; verify each boundary | Plaintext within protected memory; prevent unapproved export |
| Output | Prefer encrypted result decrypted by the owner client | Explicitly approved result leaves the TEE |
| Metadata still visible | Request timing, ciphertext sizes, configured shapes, resource use, and service availability | Timing, configured shapes, resource use, service availability, and attestation claims |
| Main limitation | Supported operations, compilation and quantization limits, key and ciphertext costs, latency | Hardware trust, side channels, implementation and attestation gaps, output leakage |

The threat model includes an honest-but-curious or compromised remote service operator who can inspect ordinary host files, logs, storage, network traffic, and process state outside the declared FHE or TEE boundary. Denial of service and access-pattern, size, and timing metadata are not prevented by either mode.

The threat model does not claim protection from a compromised owner device, malicious authorized data contributor, model poisoning, inference-output misuse, or model extraction. It also does not claim resistance to every hardware side channel, physical attack, implementation defect, or compromise of the relevant cryptographic or attestation vendors. Those exclusions must remain visible in any future packet and user-facing statement.

Differential privacy, if considered later, is a statistical release control; it is not encryption and does not replace either mode. Any DP proposal needs its own neighboring relation, accountant, utility analysis, and explicit privacy budget.

## 4. System design

### Shared client/server contract

The client accepts a versioned record with context features, a bounded ordered option list, and—during training—a label. The service returns typed option scores and a selected option. The client validates the option-set digest, decrypts when applicable, and applies the caller’s decision policy locally. The service does not take an action based solely on a model output.

The first contract uses fixed-shape feature vectors and a declared maximum of eight options. Padding and bucketing rules are frozen before measurement; the protocol report must state which lengths and shapes remain observable. The raw text-to-feature transform runs on the owner device for the initial FHE slice. A later remote encoder is a separate design decision because it changes what the server learns and what must be protected.

### FHE data path

1. The owner device validates and featurizes locally, holds the secret key, and encrypts features and—only for a supported training protocol—labels.
2. The remote evaluator receives ciphertext and permitted evaluation material, computes using the pinned FHE protocol, and returns a ciphertext result.
3. The owner device decrypts the result, validates response binding, and applies the caller’s policy.

The owner’s secret decryption key never reaches the evaluator. Evaluation keys are not secret keys, but their exact contents, recipient, retention, and cryptographic purpose must be documented. Plaintext inputs and decrypted results remain on the owner device. Any library mode that decrypts labels, activations, gradients, or intermediate values on the server fails the FHE privacy requirement unless that exception is explicitly in the protocol and the product claim is narrowed.

Zama Concrete ML is a candidate for the FHE feasibility study, not a selected dependency. Its documentation describes FHE inference for supported linear models and a separate hybrid LoRA training approach. The exact supported operations, party visibility, training update flow, license, version, and runtime requirements must be checked and frozen before implementation. A cleartext model fit followed by encrypted inference is **not** encrypted training. [Concrete ML linear-model documentation](https://docs.zama.ai/concrete-ml/1.2/built-in-models/linear), [Concrete ML hybrid LoRA training documentation](https://docs.zama.ai/concrete-ml/1.7/deep-learning/lora_training)

The FHE training gate passes only if the exact protocol performs at least one documented optimizer update using protected training examples and labels without server-side plaintext access to them. If that cannot be demonstrated, the deliverable is labeled **private inference prototype**; encrypted training remains unimplemented.

### TEE data path

1. The owner device encrypts data for storage and transport.
2. The owner verifies fresh CPU and GPU evidence against an owner policy.
3. A short-lived data key is released only after every required claim passes.
4. The attested workload decrypts and trains or infers inside the declared TEE boundary, retains sensitive traces only in protected memory, and emits only an approved result or owner-encrypted checkpoint.
5. The owner device validates provenance and applies the caller’s policy.

The TEE profile is a separate privacy product mode. It may protect data from the cloud operator under the exact measured configuration, but it processes plaintext inside the trusted hardware boundary. Before a run, map every desired security claim to evidence the selected verifier actually checks. Verify platform and GPU claims separately, including GPU driver/device evidence where available; use a bound, signed manifest for application and model identities when the hardware report does not measure them. Bind key release to the verified claims and a freshness nonce. If a component is not measured or otherwise verified, do not describe it as attested. CPU evidence is not a substitute for GPU evidence. Google’s current documentation describes confidential H100 support on specific A3 configurations and zones, plus separate GPU driver and device attestation steps. Capacity, supported zones, and attestation behavior must be checked again before any run. [Google Cloud GPU Confidential VM configurations](https://docs.cloud.google.com/confidential-computing/confidential-vm/docs/supported-configurations), [Google Cloud GPU attestation](https://docs.cloud.google.com/confidential-computing/confidential-vm/docs/attestation)

SF Compute is not an assumed TEE provider. Before it is eligible for this profile, its operator must document the exact SKU and mode, joint CPU/GPU attestation evidence, verifier path, measured software coverage, key-release integration, and relevant limitations. An H100 allocation alone is insufficient. NVIDIA’s documented H100 Confidential Computing mode has an explicit threat scope and exclusions; this PRD does not turn attestation into a general security guarantee. [NVIDIA Hopper and Blackwell Confidential Computing white paper](https://docs.nvidia.com/nvidia-secure-ai-with-blackwell-and-hopper-gpus-whitepaper.pdf)

## 5. Trace and artifact policy

“Model trace” includes raw context, labels, token IDs, features, embeddings, activations, attention values, logits, gradients, optimizer state, per-example loss, and decrypted per-example outputs. These are sensitive payloads, not ordinary telemetry.

- Default raw-trace retention is zero outside the owner device and the declared protected compute boundary.
- No raw payloads enter application logs, crash dumps, telemetry, analytics, experiment trackers, support bundles, or repository artifacts.
- FHE mode stores only ciphertext required for a request; secret keys and decrypted results stay client-side. Delete request ciphertext and temporary evaluation material under a declared lifecycle policy.
- TEE mode keeps raw traces in protected memory. Persisted checkpoints and reports are owner-encrypted before leaving the boundary. Disable core dumps and sensitive debug logging.
- Retain only aggregate metrics that pass a disclosure review. Aggregates must state their denominator and avoid small-cell or per-example release.
- Bind each response to request digest, model digest, protocol mode, and relevant configuration. Keep audit records free of raw prompts and credentials.

Ciphertext is still sensitive operational data: sizes, identifiers, repeated requests, and access patterns can leak metadata. It must have access control, retention, and deletion rules too.

## 6. Functional requirements

1. **Client:** validate schema and option bounds; featurize locally; generate or access owner-held cryptographic keys; encrypt/decrypt; verify response binding; support local operation without cloud credentials.
2. **Model:** fixed versioned variable-option scorer with a documented cleartext reference implementation and explicit model/license identity.
3. **FHE evaluator:** accept only compiled, parameter-bound ciphertexts; reject malformed shapes, wrong key parameters, stale protocol versions, and unsupported operations; never request the client secret key.
4. **TEE runner:** refuse data keys until all required fresh attestation claims pass; fail closed on unknown, stale, unavailable, or mismatched evidence.
5. **Training:** distinguish local cleartext training, TEE training, and ciphertext or hybrid-FHE training in CLI/API, logs, artifacts, and reports. Never label one mode as another.
6. **Serving:** return typed probabilities and scores with an explicit calibration version; expose uncertainty to the caller; never execute irreversible or high-stakes actions automatically.
7. **Observability:** log protocol version, timing, resource and cost totals, digests, and status only. No raw traces or secrets.
8. **Reproducibility:** freeze source, model, library/runtime, feature transform, synthetic data generator, seeds, parameters, controls, and output manifest before evaluation.

## 7. Evaluation and acceptance gates

Use one deterministic synthetic ranking corpus with disjoint fit, tune, and held-out assessment partitions. Keep every source family wholly within one partition. Freeze seeds and model choices before held-out evaluation. No real data, provider spend, or remote workers are part of the current design slice.

Compare the exact same model and examples across cleartext and secure modes. Report top-1 accuracy, log loss, Brier score, expected calibration error, abstention and uncertainty behavior, p50/p95 end-to-end latency, throughput, peak memory, ciphertext/message sizes, and full per-run cost. Define the task, minimum utility, acceptable calibration delta, latency envelope, and hard spend ceiling before any execution; no generic “90% accuracy” target is meaningful without a workload and baseline.

Required gates for any later qualification:

- **Functional:** all requests are schema-valid; option ordering and request/result digests are checked; malformed and replayed requests fail closed.
- **Numerical:** FHE results meet a preregistered parity/utility threshold against the locked cleartext reference. Report actual deviations; calibration is measured after decrypting the owner-side result.
- **Privacy boundary:** synthetic canaries do not appear in server logs, telemetry, crash artifacts, or unauthorized egress. For FHE, inspect the server protocol and process boundary for any server-side decryption. For TEE, verify key release is denied for modified, stale, incomplete, or unavailable attestation evidence.
- **Trace lifecycle:** retention and deletion behavior is verified for all raw trace classes, temporary files, failure paths, and checkpoint paths.
- **Resource/cost:** report complete client, server, network, storage, and key-generation costs. Stop at the hard ceiling.
- **Reproducibility:** a separate clean local environment reproduces the declared synthetic result from frozen source and inputs. This is `REPRODUCED_LOCAL`, not independent acceptance.
- **Independent review:** any real sensitive data, external execution, public release, or stronger security claim requires its own frozen packet and the applicable independent review and operational authority.

No successful local check supports a general security certification, benchmark, production, or commercial readiness claim.

## 8. Hardware and deployment plan

- **M4 Max:** local development, synthetic baseline, owner client, and small-model evaluation. Do not assume FHE uses its GPU efficiently.
- **M1 Air:** client compatibility and bounded encryption/decryption checks; not the primary training host.
- **Google Cloud:** candidate TEE host only after exact SKU, region/quota, CPU/GPU attestation, image support, and owner-controlled key release are verified. Current GCP documentation lists H100 Confidential VM support with constraints; recheck it before creating resources.
- **SF Compute:** not approved or assumed for TEE use until the exact provider, node, confidentiality mode, and attestation chain are verified.
- **H100:** use only for the TEE comparison or another workload where measured gains justify full cost. FHE performance is measured on the selected implementation; no H100 acceleration claim is assumed.

First deployment remains local and synthetic. Cloud storage, orchestration, APIs, multi-user tenancy, and public endpoints are future slices.

## 9. Milestones

| Milestone | Deliverable | Exit gate |
|---|---|---|
| M0: choose the promise | One use case, owner/operator boundaries, FHE vs TEE claim, output policy, and target metrics | Workload and privacy contract are specific enough to freeze a new implementation packet |
| M1: cleartext baseline | Tiny scorer, synthetic corpus, calibration and latency report | Deterministic baseline and all splits/controls are frozen |
| M2: FHE inference | Client encryption, remote ciphertext evaluation, client decryption, trace policy | Correctness, privacy-boundary, utility, latency, and cost gates pass or the mode closes with a literal failure status |
| M3: encrypted-training feasibility | One supported hybrid/FHE optimizer update using protected examples and labels | Protocol review confirms what each party sees; update completes without server plaintext access or this feature is explicitly deferred |
| M4: TEE comparison | Attestation-gated synthetic train/infer job on a verified compatible host | Fresh CPU/GPU evidence, measured application identity, key-release denial checks, trace policy, and complete cost report |
| M5: product decision | Compare modes and close design with a claim-bounded recommendation | Select one supported privacy promise or stop; production remains a separate authorization |

Milestone durations are intentionally not estimated until M0 freezes the workload and M1 measures the baseline. The prior 4–7 week estimate is not a reliable commitment for cryptographic and attestation integration.

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| TEE is described as ciphertext computation | Name the mode TEE; state plaintext exists inside its TCB; publish trust roots and exclusions |
| CPU attestation is mistaken for GPU attestation | Require every claim relevant to the selected CPU/GPU stack and bind the owner’s key-release policy to verified evidence |
| H100 rental lacks CC mode or evidence | Verify the exact SKU, mode, node, verifier, and provider contract before protected data or keys are released |
| FHE model is too slow or unsupported | Start with fixed-width small scorers; use documented operators; measure before expansion |
| Generic “encrypted training” claim hides plaintext steps | Freeze a party-by-party protocol and require a ciphertext-protected optimizer update for that claim |
| Logs or crash dumps expose traces | Disable raw logging/dumps; test canaries on normal and failure paths; retain aggregates only |
| Scores leak private facts or are misused | Limit output and rate; evaluate output leakage separately; do not auto-act |
| Mechanism protects inputs but not model weights | State weight visibility; leave model confidentiality out of V1 unless separately designed |
| FHE parameters weaken security or are mismatched | Use current scheme guidance, pin the parameters and library version, and require specialist review before real data |
| Cost and availability defeat the product case | Local-first milestones, explicit hard budget before any remote run, and stop on quota, availability, or cost failure |

## 11. Decisions required at M0

1. Which concrete workflow and decision costs justify private computation?
2. Is the must-have promise cryptographic confidentiality from the compute operator (FHE), or is hardware-rooted TEE trust acceptable?
3. Must V1 train on protected data, or is private inference the first useful product? If training is required, what exact protocol qualifies?
4. Who owns the model weights, and may the client inspect them?
5. Which context and option limits, output fields, and p95 latency target define success?
6. What is the maximum spend for any later external qualification?
7. Which supported FHE framework and license can satisfy the exact model and protocol requirements?
8. Which host and attestation roots are acceptable for the TEE comparison?

These decisions are gates, not assumptions hidden in an implementation plan.

## 12. Research references and evidence boundary

The sources below establish that the model format, FHE model families, encrypted fine-tuning prototypes, and confidential-GPU mechanisms exist. They do not establish that this proposed product is secure, useful, novel, fast, or economically viable.

- TypeSafe AI, [Introducing System One Models & Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev), accessed 2026-09-29.
- Zama, [Concrete ML linear models](https://docs.zama.ai/concrete-ml/1.2/built-in-models/linear), accessed 2026-09-29.
- Zama, [Concrete ML encrypted LoRA training](https://docs.zama.ai/concrete-ml/1.7/deep-learning/lora_training), accessed 2026-09-29. Treat as a candidate protocol; recheck current versions and exact party visibility before selection.
- Google Cloud, [Confidential VM supported configurations](https://docs.cloud.google.com/confidential-computing/confidential-vm/docs/supported-configurations) and [GPU attestation](https://docs.cloud.google.com/confidential-computing/confidential-vm/docs/attestation), accessed 2026-09-29.
- NVIDIA, [Confidential Computing Features of NVIDIA Hopper and Blackwell](https://docs.nvidia.com/nvidia-secure-ai-with-blackwell-and-hopper-gpus-whitepaper.pdf), accessed 2026-09-29.
- HomomorphicEncryption.org, [Homomorphic Encryption Standard V1.1](https://homomorphicencryption.org/wp-content/uploads/2024/08/Homomorphic-Encryption-Standard-v1.1.pdf), parameter and security reference; specialist review is still required for any implementation.
