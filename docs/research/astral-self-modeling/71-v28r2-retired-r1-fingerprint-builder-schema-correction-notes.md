# V28R2 Retired-R1 Fingerprint Builder Schema-Correction Notes

State slice:
`astral-rgs-v28r2-retired-r1-fingerprint-builder-schema-correction`.

Status: `BuilderCorrected / HermeticTestsPassed /
RealBuilderNotRun / R3NotAuthorized / FingerprintNotBuilt /
ProtocolPinUnchanged`.

## Implemented correction

The hash-only retired-R1 builder now has separate exact-schema entrypoints:

- `_verified_source_text_hash` requires exactly `license_id`, `sha256`, and
  `text`;
- `_verified_option_text_hash` requires exactly `sha256` and `text`;
- both delegate only the shared UTF-8 text and SHA-256 equality check.

The synthetic R1 fixture now uses the authentic two-key family/query
answer-option shape. Focused tests accept both authentic record classes and
reject missing, extra, cross-routed, or digest-mismatched records.

No protocol, validator core, validator CLI, controller, retained artifact,
package, or lockfile changed.

## Identities

Corrected builder file SHA-256:

```text
sha256:e134b5be58bf06051c23b926617a6b04ba1f9737d1c9e445671fcbc1e53f34bc
```

Corrected V28R2 test file SHA-256:

```text
sha256:4daa6639367320731516cba63fcae4c3242c6894e37d94f69d531404144bf63f
```

The protocol remains canonically
`sha256:236d7a2f4d8f81fdd1990c746cdfff0d3de85c191781bb7c3fde9d84d5b1aaf2`
with `retired_r1_fingerprint_manifest_sha256: not-built`.

## Verification

The corrected V28R2 module passes `90` hermetic tests and the frozen
construction-controller module passes `8`, for `98` tests across the full
V28R2 test directory. The complete V28R1/V28R2 directory gate passes `136`
tests; the V27 regression gate passes `17` tests; and Ruff passes.

No real retained-bundle extraction or builder CLI invocation occurred in this
slice. R1 and R2 construction identities remain retired and their outputs
absent.

## Next gate

A new R3 construction identity may be proposed only after this correction is
committed and independently audited. R3 requires a new fixed controller hash,
new absent output, one-invocation contract, and mandatory stop before
fingerprint commit or protocol pinning.

## Claim boundary

This slice establishes only
`LocalRetiredR1FingerprintBuilderSchemaCorrectedV28R2`. It is not a
fingerprint, protocol pin, V28R2 eligibility, novelty, acquisition,
consolidation, retention/recovery, continual learning, Astral selection,
independent replication, benchmark evidence, breakthrough, self-improvement,
introspection, self-modeling, Stage 0C, Stage 1, or production evidence.
