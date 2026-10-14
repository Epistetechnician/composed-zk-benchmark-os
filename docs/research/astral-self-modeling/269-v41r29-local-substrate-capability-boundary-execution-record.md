# V41R29 Local Substrate-Capability Boundary Execution Record

State slice: `V41R29LocalSubstrateCapabilityBoundary`.

Status: `Executed / BoundaryEstablished / ExternalReviewNotRun`.

## Question

V41R28 showed the local MLX surrogate reproduces V41R27 per-cell dynamics. This
preregistered study
(`268-v41r29-local-substrate-capability-boundary-preregistration.md`) asks
whether a **full, sentinel-gated, 48-worker qualification campaign** can run on
any local substrate, by measuring the exact substrate property that gates it.

## Method

Scoring-only base-model capability measurement (no optimizer, no adapter, no
parameter update). For each transformer substrate, scored all 256 protected rows
and all 64 acquisition cases with the base model and computed overall + per-panel
metrics. For the nemotron substrate, determined architectural compatibility with
the frozen V41R27 LoRA protocol. Frozen bindings verified at run time:
contract `sha256:ddf7f95ea4bf9b109dbdb1b02b87542a2a8ea56fd694f508c0b8647bc716ed4e`,
acquisition instrument `sha256:0459d3c39e37c1a3fb7a8ffdbee1dca214b75b316dab456ab3e8d82dd98d1f92`,
protected instrument `sha256:83e873627f55df68f62a90d9847a73e5838eccc76fe48fb3c77109b6122b503e`.

## Results

No local substrate is qualification-viable. `full_local_qualification_possible: false`.

| Substrate | Architecture | Protected arithmetic | Acquisition novelty | Classification |
| --- | --- | --- | --- | --- |
| qwen2.5-0.5b (4bit) | uniform qkvo ✓ | **0.9883** (panels 7, 14 < 1.0) | pass (all panels ≥ 3) | qualification_blocked |
| llama-3.2-1b (4bit) | uniform qkvo ✓ | **0.2539** (all 16 panels < 1.0) | fail (panels 0, 2 < 3) | qualification_blocked |
| nemotron-3-nano-4b | hybrid Mamba ✗ | not scored | not scored | architecture_incompatible |

Detail:

- **qwen2.5-0.5b** fails only the protected-arithmetic gate: 253 of 256 rows
  correct; panel-7 0.875 and panel-14 0.9375. Panel-7 is a sentinel panel, so
  even the sentinel could not form. Acquisition novelty passes on every panel.
- **llama-3.2-1b** fails both gates: protected arithmetic 0.2539 (all 16 panels
  below 1.0) and novelty below 3 on panels 0 and 2.
- **nemotron-3-nano-4b** is `nemotron_h`, a hybrid Mamba-attention stack
  (hybrid_override_pattern present, Mamba markers present, not a uniform qkvo
  stack), architecturally incompatible with the frozen qkvo-LoRA protocol
  regardless of arithmetic ability.

## Interpretation (preregistered ladder)

The preregistered ladder fired its boundary branch: no substrate met all three
conditions (uniform transformer qkvo architecture AND protected arithmetic
exactly 1.0 across all 256 rows AND acquisition novelty ≥ 3 in all 16 panels).
Therefore **full local qualification is substrate-blocked**. The protected-
arithmetic requirement is principled — only knowledge the base model already has
can be "retained" — so this is a genuine substrate-capability boundary, not an
artifact of the gate. The strongest local substrate (qwen2.5-0.5b) is close
(0.9883) but below the frozen 1.0 requirement, and the closest architecture-
compatible larger option (llama-3.2-1b) is far below; the only larger local
model (nemotron-3-nano-4b) is architecturally incompatible.

This resolves the open question: a full sentinel-gated qualification campaign
cannot be run on any currently available local substrate. Achieving it would
require a substrate with (a) a uniform transformer qkvo attention stack
compatible with the frozen LoRA protocol and (b) perfect protected-set
arithmetic at baseline — i.e., a stronger or differently-capable substrate than
is locally available, or the H100 lane (currently blocked on provider snapshot
restore).

## Artifact digests

Directory `artifacts/v41r29-substrate-capability/local-substrate-capability-2026-08-04/`:

| File | SHA-256 |
| --- | --- |
| substrate-capability-result.json | `dcd2f1ae783c8434b7b5f7c6656c73f23db638b257bdd1f9045009ed0e45b3c9` |
| MANIFEST.sha256 | `473f3a06eb1bbdb4cbc2b34c548bc6dee590ce413812084fa43054f4357280d9` |
| result_sha256 (inside result) | `sha256:2a2994817700150bd8e8e5ad1762113f9033de55421ca2b7d3a36844649d59d5` (independently recomputed, matches) |

Probe source: `tools/astral-v41r29-substrate-capability/probe_substrate_capability_v41r29.py`.

## Claim ceiling and nonclaims

Claim ceiling: `LocalSubstrateCapabilityBoundaryV41R29`.

This record does not run a qualification campaign, does not advance or alter the
V41R27 census (30 of 48) or claim ceiling
(`RemoteH100AGEMPartialQualificationInfrastructureInterruptedV41R27R2`), does not
demonstrate continual learning, acquisition, retention, recovery, autonomous
self-improvement, introspection, SOTA, confirmation, independent replication, or
Stage 0C advancement, and does not substitute for H100 evidence. It is a
base-model capability characterization establishing the substrate gate for future
local qualification.

## Governance

`tune_opened: false`, `assessment_opened: false`, `adaptive_stopping: false`,
`production_actions: false`, `provider_direct_authority: false`. Scoring-only;
no training, no network, no H100.
