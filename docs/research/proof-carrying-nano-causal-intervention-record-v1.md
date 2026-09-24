# Proof-carrying nano causal-intervention record V1

State slice: `proof-carrying-nano-causal-intervention-record-v1`.

Status: `RecordSchemaImplemented`; causal assessment is
`SEALED_UNTIL_INDEPENDENT_REVIEW`.

## Scope

This slice defines the next vertical boundary after the read-only host
activation capture. It stores a declared intervention observation without
executing a donor/target replacement. The record is closed and digest-bound.
New versions create new records; an existing record or proof payload is not
updated in place.

The record binds:

- the parent activation action digest;
- donor and target checkpoint digests, layer, closed site
  `decoder_block_output`, and token positions;
- donor/target activation digests before the declared replacement;
- exact operator schema `exact-activation-replacement-v1`, type
  `replace_token_vector`, coefficient `1`, interpolation `none`, and
  digest-bound source/target parameters;
- a finite canonical-decimal measured effect and a nonempty, uniquely
  identified control list;
- equal host parameter digests before and after the declared observation;
- replay input digest, seed, index, runner identity, and replay digest;
- proof status `checked` or `failed` and immutable proof attempts.

The exported status is `CausalInterventionRecordOnly`. The claim semantics are
`declared_record_binding_only_no_causal_claim`, with ceiling
`LocalCausalInterventionRecordBindingOnly`.

## Proof and validation boundary

The producer-side Lean engine generates a theorem for the exact record. The
formal artifact in
`formal/proof-carrying-nano-interp-v1/NanoInterp/CausalInterventionRecord.lean`
states only declared record-level facts: state/protocol identity, exact
operator syntax, nonempty digest bindings, unchanged host parameters, and
checked proof status.

The independent validator in
`tools/proof_carrying_nano_jevlike_independent_validation_v1/causal_intervention.py`
reimplements canonical JSON, digest checks, the closed schema, operator and
replay checks, proof binding, and the review seal. It does not import the
record producer, Lean proof engine, or store. It does not infer or certify
causality from the measured effect.

## Adversarial coverage

The contract tests reject:

1. donor/source activation mismatch even after digest rebinding;
2. altered operator type even after digest rebinding;
3. effect tampering;
4. missing controls;
5. replay-seed divergence;
6. host parameter mutation;
7. record/proof status inconsistency.

## Review gate

The exact independent review packet is
`docs/research/proof-carrying-nano-causal-intervention-record-v1-review-packet.md`.
It is prepared but unsigned and unaccepted. The operator cannot self-sign it.
No causal assessment, model intervention, provider call, accepted Evidence
Ledger mutation, dashboard, swarm coordination, Jevlike integration change,
or production claim is authorized by this slice.

## Verification

```text
pnpm --ignore-workspace run verify:proof-carrying-nano-causal-intervention-record-v1
cd formal/proof-carrying-nano-interp-v1 && lake build
```

The root checkout remains dirty and non-release-ready. Passing these focused
contract checks is not independent review, causal evidence, scientific
validation, or production authorization.
