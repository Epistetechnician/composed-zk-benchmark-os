# Proof-carrying nano host activation boundary V1

State slice: `proof-carrying-nano-host-activation-boundary-v1`.

## Scope

This slice adds one cached small-transformer adapter for a read-only CPU
activation capture. The target is the locally cached
`HuggingFaceTB/SmolLM2-135M` snapshot at snapshot
`93efa2f097d58c2a74874c7e644dbc9b0cee75a2`. No model or corpus download is
performed by the adapter. A qualification first copies the snapshot into a
new owner-only external custody root and then loads only that copy.

The closed action schema includes:

- host checkpoint and runtime digests;
- layer, closed site `decoder_block_output`, and nonnegative token position;
- exact `model.layers.{layer}` forward-hook identity;
- replayable input IDs, attention mask, and replay seed;
- activation dtype, shape, and digest;
- parameter digests before and after capture;
- the exact read-only mutation policy and action digest.

The external raw-output root stores the captured activation bytes and a
canonical metadata sidecar. The action and exported bundle contain digests,
not raw activation payloads.

## Proof boundary

The producer and independent validator reconstruct the same Lean source. The
kernel theorem proves only the declared local predicate: hook reached, the
activation digest is non-empty, and parameter digest is unchanged. This is a
record-level consistency claim relative to declared host-slice semantics. It
does not prove checkpoint fidelity, implementation correctness, feature
faithfulness, circuit structure, causal effect, or alignment.

## Qualification gates

The one offline CPU qualification checks:

1. exact action and raw-byte replay;
2. hook reachability;
3. activation capture and external raw-output custody;
4. unchanged parameter digest and no host mutation;
5. checked activation-binding proof;
6. independent bundle validation.

The output status is `QualifiedReadOnlyHostActivationBoundary` with claim
ceiling `LocalCachedSmallTransformerActivationCaptureOnly`. Causal
intervention records are sealed until a separate independent review. Dashboard
and swarm coordination remain unimplemented.

## Qualification result

One offline CPU qualification completed from a fresh custody copy. The
external checkpoint custody manifest is
`/Users/shaanp/.codex/runs/proof-carrying-nano-host-activation-boundary-v1-custody/checkpoint-custody.json`.
Its checkpoint digest is
`sha256:be2686001169c6ca132bd2243a94dc70e12d6a0d59ec4cd5e0c383da638515cd`
and its manifest digest is
`sha256:088b8ce6217561bf91dc30b0eae7d430e40aab5178114941ee48cf4285b58535`.

The final qualification report is
`/Users/shaanp/.codex/runs/proof-carrying-nano-host-activation-boundary-v1-qualification-v2/qualification-report.json`.
It reports `QualifiedReadOnlyHostActivationBoundary`; exact replay, hook
reachability, activation capture, unchanged parameter digest, no host
mutation, a checked Lean proof, and independent bundle validation all passed.
The action digest is
`sha256:d3e9f9773d4907ef6e36473a6b326be014149144b8bbd7ee2bba92c6bbf1bffe`.
The bundle digest is
`sha256:b74e8b20d5000d7f6d5b9cc5dacd226132bd61a7068db18fac3645b96c58c7f2`.
The report self-digest is
`sha256:73927a71a86aca120185c2876cd1eea586501dc13893910b1852b79039c75df0`.

## Verification

```text
pnpm --ignore-workspace run verify:proof-carrying-nano-host-activation-boundary-v1
```

The root checkout remains dirty and is not release-ready. The qualification
outputs and checkpoint custody are external artifacts, not repository release
artifacts.
