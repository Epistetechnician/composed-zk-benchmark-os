# Phase 651-B Through 651-K HSAI DeepProve Lookahead Local Metadata Notes

State slice: `phase-651b-through-651k-hsai-deepprove-lookahead-local-metadata`.

This phase implements the executable local metadata portion of
`docs/651-phase-hsai-deepprove-lookahead-candidate-search-boundary.md`.
Subphase 651-A remains the boundary and source-position document. Subphases
651-B through 651-K are represented by typed Rust metadata and validators in
`crates/hsai-agent-admission/src/lib.rs`.

## Implemented State Slices

- `phase-651b-hsai-lookahead-inert-metadata`
- `phase-651c-hsai-lookahead-fixture-replay`
- `phase-651d-hsai-lookahead-backward-verification-metadata`
- `phase-651e-hsai-lookahead-branch-scoring-report`
- `phase-651f-hsai-lookahead-operator-transcript-boundary`
- `phase-651g-hsai-lookahead-operator-transcript-import-candidate`
- `phase-651h-hsai-deepprove-receipt-boundary`
- `phase-651i-hsai-deepprove-receipt-import-candidate`
- `phase-651j-hsai-deepprove-reviewed-receipt-policy`
- `phase-651k-hsai-lookahead-admission-bridge`

## Rust Surface

The implementation adds digest-only metadata for:

- prompt case references;
- greedy baseline references;
- bounded deterministic lookahead config;
- candidate future spans;
- local branch-score labels;
- selected/rejected branch decisions;
- backward-verification findings;
- required branch-scoring report section digests;
- operator transcript boundary and import-candidate checks;
- future DeepProve receipt references;
- quarantined DeepProve receipt import-candidate checks;
- reviewed receipt policy limits;
- advisory admission bridge metadata.

It also adds a fixture-only replay builder:

- `HsaiDeepProveLookaheadFixtureReplayInput`
- `HsaiDeepProveLookaheadFixtureReplayCandidate`
- `hsai_deepprove_lookahead_fixture_replay_report_input`
- `build_hsai_deepprove_lookahead_fixture_replay_report`

The fixture replay builder accepts only committed digest-bound fixture
candidates. It deterministically chooses the first `Selected` candidate in the
ordered fixture map, constructs the normal Phase 651 report input, and then
uses the same report validator. It does not generate text, call a model, retain
raw transcripts, or invoke DeepProve.

The only allowed reviewed DeepProve conclusion is:

```text
The declared model inference for this input/output pair was verified according
to the disclosed DeepProve receipt and verifier artifacts.
```

That conclusion is still advisory metadata. It is not an agent-correctness,
production-readiness, SOTA, full-security, benchmark, accepted-evidence, or
authority claim.

## Validation Rules

The validator requires nonzero digests for prompt cases, greedy baselines,
candidate spans, backward-verification findings, report sections, admission
bridges, operator transcript boundaries, and DeepProve receipt references when
present.

It rejects:

- candidate counts above the declared bound;
- horizon values above the declared bound;
- missing prompt-case digests;
- missing greedy baseline references;
- selected candidates not present in the candidate set;
- selected candidates not marked selected;
- selected context digest drift;
- backward-verifier findings not bound to completed output digests;
- operator transcript records with raw secret retention, undeclared files,
  nonportable paths, or digest disagreement;
- DeepProve receipt refs that invoke, clone, vendor, or commit DeepProve
  artifacts;
- `ReviewedVerifiedInferenceOnly` status without a reviewed receipt policy;
- admission bridges that do not preserve proposal-only metadata;
- nonclaim or nonpromotion digest drift;
- accepted evidence, Level2+, score-axis, benchmark, production, SOTA,
  semantic-correctness, full-security, external-audit, human-review acceptance,
  or authority flags.

## Evidence Ceiling

The implementation ceiling is `Level1LocalReplayQuarantinedMetadataOnly`.

It creates no accepted Evidence Ledger mutation, accepted formal evidence,
Level2+ evidence, score-axis population, benchmark evidence, live LLM output,
live zkML output, DeepProve proof, checker transcript, solver certificate,
external audit result, human-review acceptance, or authority to execute an
action.

## Focused Validation

Focused tests cover:

- valid metadata report with no DeepProve receipt;
- A-through-K report with operator transcript metadata and reviewed DeepProve
  receipt policy;
- deterministic fixture-only replay report construction;
- repeated fixture replay digest stability;
- invalid fixture schema rejection;
- fixture with no selected candidate rejection;
- fixture horizon overflow rejection;
- candidate count and horizon bound rejection;
- missing prompt-case digest rejection;
- missing greedy baseline reference rejection;
- selected candidate missing rejection;
- selected context digest drift rejection;
- verified receipt status without reviewed policy rejection;
- promotion and authority rejection.

Focused gate:

```sh
cargo test -p hsai-agent-admission --lib phase651_hsai_deepprove_lookahead -- --nocapture
```
