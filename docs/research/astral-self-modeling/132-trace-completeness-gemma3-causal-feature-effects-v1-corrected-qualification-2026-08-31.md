# Gemma 3 causal feature-effects V1 corrected qualification

State slice: `astral-trace-completeness-gemma3-causal-feature-effects-v1`.

This record supersedes the execution-status portion of record 131. Record 131
and the earlier packet/review bytes are preserved as historical artifacts. V4
remains permanently frozen and is not an input to this slice.

## Corrective changes and packet freeze

The Luna findings were applied before a new packet was frozen:

- `custody_v1.py` now binds the current `RUNTIME_MANIFEST_SHA256` rather than
  the obsolete V4 runtime-manifest constant.
- `run_v1.py` now assigns a fresh execution ID and writes append-only
  execution-specific aggregate and raw-deletion artifact names. This closes
  the fixed-filename collision that caused the first corrected launch to fail
  closed during finalization after raw deletion.
- Hermetic tests cover both corrections.

The frozen packet is
`917913ec9668befe0eef3e547d1a061994091205e967055c753d2f5e8e5694d1`.
Its packet-file SHA-256 is
`3684309afcbe18d8234d6f774b169e4ed681341c86c033cc69d90644ff3d6bdd`.
The source-manifest digest is
`1ada3de7c20380b176ac63591a888dd13ca0e86dce4bb39cd4d08946bdec268d` and
the contract digest is
`d6b45395ca3a70c216d30e57c7887bc57ddd579ddfaab7a2b7880b685ee8064b`.

## Independent review and preflight

The exact packet was reviewed by the distinct GPT-5.6 Luna task
`01a05a3a-2e2f-7f61-a965-e3b375153c79`, role
`independent-causal-feature-effects-reviewer-v1`; the operator identity is
`shaanp`. The fresh report returned `ACCEPT` with no findings. The report
SHA-256 is
`f9e75c3f2bd516d33c8cd454852276f013726d7f6bfce10e2aa946bcfc4aacf4`.

The canonical V1 receipt is
`/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-causal-feature-effects-v1/review/independent-acceptance-v1.json`.
Its file SHA-256 is
`ffa11bfecfee9e58b4781e74bbe83b234b904d45f397903da0d756d157f9f412` and
its packet-bound receipt digest is
`dd26fdb54e82574e2eca8d7e08207611f41c4b0526958dd08790c57ffbb0e13d`.
`review_v1.validate_signed_acceptance` independently verified the Ed25519
signature, packet digest, report digest, role, and operator/reviewer
separation. The static review digest is
`f91749832d56937b378f486cf2332cf03b9ba6d284300a6444da0da64f93cd74`.

Only after that receipt was present, the corrected node-local preflight
returned `ACCEPT` with `custody_valid=true`, no findings, the current packet
digest, `reviewer_receipt_present=true`, `execution_authorized=false`, and
`assessment_opened=false`. The preflight did not itself open assessment or
claim a scientific result.

## GiveMeANode qualification

The exact node was launched only after the accepted preflight:

- state/name: `astral-trace-completeness-gemma3-causal-feature-effects-v1`;
- node: `7289c582-2e04-4d6a-ac3c-6ca8d4139356`;
- command: `cmd-kpqim`;
- model/runtime: cached `gemma-3-1b-pt-bf16`, offline execution;
- custody: external owner-only `0700` root
  `/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-causal-feature-effects-v1`.

The command exited 0. The provider node was stopped after validation with its
disk intact and scratch cleared. No second model execution was launched.

The final execution ID was
`f72859cc55a44a8f98f340bbba2a758c`. The aggregate-only output is
[qualification-v1.json](/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-causal-feature-effects-v1/aggregate/qualification-v1.json)
with file SHA-256
`85e2de3730a51a9bc4f15ac891533324209bc526335a4c857f6cfb4b5ffec857`.
The internal aggregate artifact has file SHA-256
`b1ec3f7a41c41fd0efc5f0dad8ecfa5c7654ae53199027dd05cdeefad184373a` and
aggregate digest
`44905afe999a5d64887e4d942c9df16940db809cce7f346631234f627f47d2ad`.

Qualification closed as `NoCandidate` under the ceiling
`LocalDevelopmentGemma3CausalFeatureEffectsQualificationV1`. Native versus
instrumented parity passed. Pooled SAE reconstruction NMSE was
`0.04284696944156229` against the fixed `<=0.05` gate, and power simulation
was `0.9391` against the fixed `0.80` target. Tune sign agreement was
`0.828125` over `384` rows, with tune effects and controls passing. The fixed
fit effect family did not pass all required feature gates, so no held-out
causal-effect assessment was opened and no claim of
`HeldOutCausalFeatureEffectsAccepted` is permitted.

## Custody closure

The final raw-deletion artifact is
`raw-deletion-completion-f72859cc55a44a8f98f340bbba2a758c.json` with file
SHA-256
`45cad154c77b25b493713c186157eb540aab00f277397b402ae9693ac99e6f05`.
Its completion digest is
`d9c5d11970abd036a87b20b86a62735b2afccbc9e3b313f7c5483dd77f5eb1b3`.
The independent aggregate validator receipt digest is
`cdc2e87387326e8045b716e5922f220e55baa57ed18e76e3b2ba5bebd2cb8165`.
Validation confirmed the aggregate digest and confirmed that the external raw
custody root is empty after expiry. Raw prompts, tokens, activations, logits,
cache/state payloads, and per-trial outcomes were not exported or published.

This result is qualification evidence only. It does not reopen V4 or V48,
promote Stage 0C or Stage 1, mutate the accepted Evidence Ledger, establish
kernel-complete observability, introspection, self-modeling, consciousness,
benchmark evidence, production readiness, or provider evidence.
