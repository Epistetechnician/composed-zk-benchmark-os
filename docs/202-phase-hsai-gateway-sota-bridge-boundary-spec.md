# Phase 202 HSAI Gateway SOTA Bridge Boundary Spec

Status: docs-first boundary for the HSAI Agent Approval Gateway proof path.

## State Slice

This phase may touch only:

- `docs/202-phase-hsai-gateway-sota-bridge-boundary-spec.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No Rust source, Cargo metadata, generated artifacts, package runtime files,
model weights, prompts, secrets, external replay outputs, accepted Evidence
Ledger entries, or benchmark outputs are part of this docs-first slice.

## Purpose

Define the bridge from the existing local HSAI admission stack to a marketable
SOTA-level proof package for an Agent Approval Gateway:

```text
agent proposal
  -> strict typed admission candidate
  -> evidence-bound policy decision
  -> accepted / rejected / quarantined audit row
  -> optional downstream signer or tool only after acceptance
```

The goal is not to claim production readiness. The goal is to specify the
smallest reproducible experiment that can demonstrate evidence-bound
authorization for autonomous-agent actions, using local open-weight models first
and a rented open-weight model lane only when it adds measurable adversarial
coverage.

## Current Local Hardware Baseline

The local baseline observed for this planning slice is:

```text
Apple M4 Max
14 CPU cores
32 GPU cores
36 GB unified memory
ollama installed
llama-server installed
```

The local lane must be respectful to that machine:

- prefer 3B to 8B open-weight instruct models;
- allow 12B to 14B quantized models only for short-context batches after a local
  smoke check;
- avoid long overnight runs unless explicitly approved;
- default to bounded adversarial-case generation, not full model training;
- keep all durable outputs outside git or under a gitignored artifact root.

## Model Lanes

### Lane A - Local Low-Parameter Open-Weight Lane

Purpose: cheaply generate and replay adversarial agent-action proposals against
the local gateway admission path.

Candidate model class:

- 1B to 4B for fast smoke loops;
- 7B to 8B for normal local adversarial generation;
- 12B to 14B only for short-context second-pass review if memory pressure is
  acceptable.

Candidate families are examples, not pinned dependencies:

- Qwen small instruct / coder / agent models;
- Gemma small instruct models;
- Phi small instruct models;
- Llama small instruct models;
- other open-weight models with locally runnable quantized artifacts.

The selected model is advisory only. A model output may propose a case. It may
not approve a case, verify a case, raise maturity, populate score axes, mutate an
accepted ledger, call tools, or execute payments.

Required local model provenance for every kept run:

- model family and exact artifact id;
- quantization format and digest when available;
- runtime command;
- prompt template digest;
- sampler settings;
- hardware summary;
- input corpus digest;
- output bundle digest;
- explicit non-secret statement.

### Lane B - Rented Open-Weight Adversarial Lane

Purpose: run the same harness against a stronger open-weight model on rented GPU
hardware to test whether the gateway holds under better adversarial generation.

This lane is for adversarial pressure, not authority. It must use non-secret
inputs and should prefer open-weight models deployed in an operator-controlled
runtime over opaque hosted chat APIs.

Candidate hardware class:

- L4, A10, RTX 4090, or equivalent for 7B to 14B;
- L40S or A100-class hardware for 30B to 35B;
- H100-class hardware only if a larger open-weight adversarial model materially
  changes coverage or throughput.

Rented-lane outputs remain untrusted external artifacts until imported through
the existing result/admission machinery. They are not Level2+ evidence by
themselves.

## Trust-Native Design Rules

The gateway proof must preserve these rules:

1. Model output is proposal only.
2. Strict typed decoding happens before admission.
3. Raw provider text never gets direct authority.
4. Every accepted action has a policy snapshot.
5. Every decision is recomputable from candidate plus policy.
6. Rejected and quarantined cases remain audit material.
7. Accepted-envelope export is allowed only after admission.
8. Downstream signer/tool execution is outside this boundary until a later phase.
9. Trust roots are explicit and do not hide behind a generic "AI" label.
10. Local model evidence cannot become proof, production readiness, or semantic
    correctness.

## Adversarial Corpus

The first SOTA-bridge corpus should cover:

- prompt-injected payment requests;
- wrong-counterparty payments;
- amount-limit bypass attempts;
- source digest drift;
- stale approval replay;
- duplicate JSON key payloads;
- policy downgrade attempts;
- direct-authority requests;
- forged accepted decisions;
- missing nonclaim labels;
- missing source artifact digests;
- stale journal tips;
- quarantine-preserving rejected decisions;
- signer/tool requests before accepted admission.

Each corpus item must include:

- expected gateway verdict;
- threat label;
- source model lane;
- deterministic seed or replay reference when applicable;
- candidate digest;
- policy digest;
- claim-boundary labels;
- nonclaim labels.

## Evidence Ladder

The bridge must advance in this order:

1. Local corpus generation and strict typed intake.
2. Local deterministic admission replay.
3. Local journal materialization and semantic readback.
4. Local adversarial metrics report.
5. Rented open-weight adversarial generation over the same schema.
6. External replay package with non-secret artifacts.
7. Reviewed evidence candidate.
8. Accepted evidence only after the existing promotion path admits it.
9. Independent reproduction before any independent or SOTA-measured claim.

No step may skip the claim boundary of the previous step.

## Metrics

Primary metrics:

- unsafe action block rate;
- false rejection rate over benign actions;
- quarantine rate and reason distribution;
- replay/tamper detection rate;
- duplicate-key detection rate;
- policy-downgrade detection rate;
- decision recomputation agreement;
- audit bundle completeness.

Secondary metrics:

- local generation throughput;
- local admission latency;
- rented generation throughput;
- cost per adversarial case;
- model-family diversity;
- coverage by threat label.

Metrics are local experimental data until reproducible artifacts and review
promotion exist. They are not official benchmark evidence in this boundary.

## Output Shape For A Future Implementation Phase

A later implementation phase may define a gitignored output root such as:

```text
.artifacts/hsai-gateway-sota-bridge/
```

Future materialized outputs should be declared before code is written. The
likely bundle shape is:

```text
gateway-bridge/
  manifest.json
  model-runs.jsonl
  candidates.jsonl
  policies.jsonl
  decisions.jsonl
  journal/
  metrics.json
  nonclaims.json
  redaction-report.json
  validation-report.json
  digests/*.sha256
```

This docs-first slice creates none of those files.

## Source References

Current model/provider references must be rechecked before implementation:

- Qwen organization and models: `https://huggingface.co/Qwen`
- Google open models: `https://huggingface.co/google`
- Microsoft open models: `https://huggingface.co/microsoft`
- Meta Llama models: `https://huggingface.co/meta-llama`

These references justify candidate families only. They do not pin a model,
license, quantization, safety profile, or runtime behavior.

## Anti-Goals

- No Rust implementation in this slice.
- No package runtime files.
- No CLI, server, UI, dashboard, or browser app.
- No model download.
- No committed prompts, generated corpora, or output bundles.
- No secrets or credential handling.
- No external replay execution.
- No signer, wallet, exchange, custody, ACP, or MCP integration code.
- No accepted Evidence Ledger mutation.
- No score-axis population.
- No benchmark output.
- No Level2+ evidence.
- No production-readiness claim.
- No semantic-correctness claim.
- No global software-agent uniqueness claim.
- No claim above `Attested`.

## Exit Criteria

- The repo records this boundary in README navigation, task list, validation
  report, and AGENTS scope rules.
- The local hardware baseline is named.
- The local and rented model lanes are separated.
- Trust-native rules are explicit.
- The adversarial corpus shape is explicit.
- Evidence promotion ordering is explicit.
- The spec contains no runtime authorization.
- Documentation validation passes.
