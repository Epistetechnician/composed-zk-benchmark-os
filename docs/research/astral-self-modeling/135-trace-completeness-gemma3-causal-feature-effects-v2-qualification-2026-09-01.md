# Astral Gemma 3 Causal Feature-Effects V2 Qualification

State slice: `astral-trace-completeness-gemma3-causal-feature-effects-v2`.

Disposition: `NoCandidate`.

V1 was first closed immutably as `NoCandidate`. V2 then executed once under
the fresh protocol and custody identities in
[the V2 protocol](134-trace-completeness-gemma3-causal-feature-effects-v2-protocol.md).
No V1 scientific corpus, prompt, activation, effect, prediction, or result
bytes were used as V2 inputs.

## Authorization and execution identity

| Field | Bound value |
|---|---|
| Packet digest | `749b4b6cbf2a76318a8a697a9ace633b6c8d23b0435afcf3944fbaed4b3f6a15` |
| Independent receipt | Ed25519 `ACCEPT`, receipt digest `bd023e41629d925f14fc6526f3661071647a5bb6b7e7eb9d10a1c6bf3bef313d` |
| Reviewer identity | `independent-causal-feature-effects-reviewer-v2`, key ID `526f2200a7e54089bc716eef6f6345089ec957af8d26b7b734889e7a62f12502` |
| Operator / runner | `shaanp` / `run_v2.py` |
| Provider / node | GiveMeANode H100/CUDA 12.9 / `3f4edebf-5601-4de3-be62-fdd87db72906` |
| Qualification command | `cmd-fa7ks`, 2026-09-01 15:45:09Z to 16:04:15Z |
| Hard spend ceiling | USD 50; one bounded qualification |
| Model | `google/gemma-3-1b-pt`; manifest `5cc36128b456997e582a990ac2ce59d7fe43d925317a6e1dae48a3284895eb81` |
| Runtime | frozen manifest `f9a7697c44765df350baabb9b62f2d83a21f883abdf8555db9bcc8c250814caa` |
| Feature asset | Gemma Scope 2 `16k/L0-big` affine; QC `35760a5a4bc47ab3ee11d9082e629f560449644753a8924bda30050351ebc361` |
| Corpus | `gemma3-causal-feature-effects-cross-half-stability-v2-20260901`; manifest `3ad84978dd63c240dd242f1b594b0750285b449187365b1904c26ad34a6f6d00` |
| Custody root | `/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-causal-feature-effects-v2` |
| Claim ceiling | `LocalDevelopmentGemma3CausalFeatureEffectsQualificationV2` |

The independent receipt was verified against the packet digest before launch.
The final preflight recorded review `ACCEPT` and valid `0700` custody; its
`execution_authorized: false` field is intentionally non-authorizing static
metadata. The executable admission gate separately verified the GiveMeANode
allocation receipt, node identity, hard ceiling, and signed receipt before
model loading. The node is now stopped with its disk parked and billing
stopped.

## Fixed gates and result

The predeclared stability estimand passed: the two 16-family fit halves had a
top-16 intersection of 14 features, above the minimum four. The locked
selection rule chose features `385`, `832`, `1529`, and `15972`.

| Gate | Observed | Fixed rule | Result |
|---|---:|---:|---|
| Native/instrumented parity | zero logit delta; matching sample | delta `<=1e-4` and sample match | pass |
| Transcoder reconstruction | pooled NMSE `0.043354035141255125` | `<=0.05` | pass |
| Power simulation | `0.9391` | `>=0.80` | pass |
| Fit feature effects | all four Holm-adjusted tests pass | fixed alpha `0.05` and effect gates | pass |
| Tune prediction | sign agreement `0.75` | `>=0.80` | fail |
| Tune feature effects | feature `832` adjusted p `0.32693958282470703`; `all_pass: false` | fixed Holm effect gate | fail |
| Tune controls | no-op/exact-copy zero; intervention reach and output-TV positive | fixed controls | pass |
| Assessment opening | not opened | fit, tune, and control gates required | closed |
| Held-out causal scrubbing | not run | assessment only after tune lock | not eligible |

The fit means were `-0.06640625`, `0.140625`, `-0.18359375`, and `0.052734375`
for features `385`, `832`, `1529`, and `15972`, respectively. These are fit
qualification aggregates, not a held-out causal-effect claim. Because the
locked tune prediction and effect gates failed, no assessment effects were
collected and no `HeldOutCausalFeatureEffectsAccepted` classification is
available. The fixed requirement that a breakthrough needs both fit and fresh
held-out causal scrubbing therefore remains unsatisfied.

## Custody and independent validation

The canonical aggregate is
`aggregate/qualification-v2.json`, file SHA256
`041064c875e2d2c6e49fc6e78aa49c0bb0c8ca3ede168aa54a264463959d14e3`, with
embedded aggregate digest
`d47101e19438f160a5249ef115a0b37f7d2ffcb359cad70aeda69f810edbddde`.
The raw deletion receipt is
`aggregate/raw-deletion-completion-d01f39ecc04341d8825b202d053b6bbf.json`,
file SHA256
`24180d6a7fa093ebc808f654efc189c2f620c30e8da4ad1bccb834f89f5072c9`, with
completion digest
`5175c54612d8756ebf32ac42e75637324b23ae6fa18575f507d7a6aafbf4d2f8`.
It records 4,610 removed raw objects and an empty raw root. Aggregate-only
event accounting found 4,321 event manifests and 289 capture manifests,
matching the 4,610 deleted raw objects; event manifests accounted for
4,401,083 events and capture manifests accounted for 1,156 tensors. No raw
object was exported.

The first public output wrapper included the separate expiry receipt and did
not satisfy the aggregate validator. It was preserved as a superseded
owner-only audit file. The canonical aggregate was mechanically restored from
that output by removing only the duplicate `raw_expiry` wrapper field; its
preexisting aggregate digest remained unchanged. The corrected aggregate then
passed `validate_aggregate`, and the fresh external root passed
`validate_raw_expired`. This packaging correction changed no model, corpus,
activation, intervention, effect, or classification value. The reviewed source
digest was rechecked after the correction and still reproduced the packet
digest.

Raw prompts, tokens, activations, logits, cache/state payloads, per-trial
outcomes, and raw event streams remained in the external owner-only custody
root during execution and were deleted before final validation. Only
aggregate/digest artifacts remain in custody.

## Local verification and closure

`pnpm run lint:fast` passed. The V2 hermetic suite passed `25` tests. The
aggregate validator and raw-expiry validator both returned `valid: true`.
V2 is terminally closed as `NoCandidate`; no retuning, second GiveMeANode run,
assessment, held-out causal-scrubbing claim, Stage 0C/Stage 1 promotion,
introspection claim, causal-self-modeling claim, benchmark claim, or production
readiness claim is authorized under this state slice.
