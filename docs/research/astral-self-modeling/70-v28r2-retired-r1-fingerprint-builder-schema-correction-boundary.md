# V28R2 Retired-R1 Fingerprint Builder Schema-Correction Boundary

State slice:
`astral-rgs-v28r2-retired-r1-fingerprint-builder-schema-correction-boundary`.

Status: `R2BuilderFailedClosed / R2IdentityConsumed /
OutputAbsent / RootCauseLocalized / CorrectionDocsFirst /
ProtocolPinUnchanged`.

## R2 failure record

The committed R2 controller was invoked exactly once. Its preflight passed and
it invoked the retained-R1 fingerprint builder exactly once. The builder
exited `1` with:

```text
error: invalid text record
```

The R2 output remained absent:

```text
/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v28r1-retired-fingerprint-8cf75d7-r2.json
```

R2 is consumed and may not be retried. No fingerprint was created, the
protocol remains `not-built`, and no model or scientific operation ran.

## Read-only root-cause localization

The retained R1 raw-corpus schema uses:

- `source_form` and `support_source` records with exact keys
  `license_id`, `sha256`, and `text`;
- family and query answer-option records with exact keys `sha256` and `text`.

The committed builder routes both record classes through one helper that
requires `license_id`, `sha256`, and `text`. It therefore rejects the authentic
two-key answer-option record before output creation. The synthetic builder
fixture incorrectly added `license_id` to answer options and did not expose
the incompatibility.

This is a local schema-compatibility defect in the hash-only builder and its
fixture. It is not a retained-bundle integrity failure and not a V28R2
scientific result.

## Future correction boundary

A later separately authorized implementation slice may change only:

- `tools/astral-rgs-acquisition-v28r2/build_retired_v28r1_fingerprint.py`;
- `tools/astral-rgs-acquisition-v28r2/tests/test_v28r2.py`;
- phase notes and status mirrors under
  `docs/research/astral-self-modeling/`, `README.md`, and `AGENTS.md`.

The correction must:

1. split or parameterize text-record verification so source/support records
   require exactly three keys and answer options require exactly two;
2. preserve byte-exact UTF-8 SHA-256 validation for both record classes;
3. reject missing or extra keys in either class;
4. make the synthetic R1 fixture byte-shape-compatible with the authentic
   answer-option schema;
5. add focused positive and adversarial tests for both schemas;
6. preserve every frozen semantic/raw input identity, hash-only output rule,
   closed manifest census, normalization rule, fingerprint-set census, and
   short-write behavior;
7. run the full V28R2, combined V28R1/V28R2, V27, Ruff, and cleanliness gates;
8. stop without running the real builder.

No protocol, validator core, validator CLI, controller, RGS file, package, or
lockfile change is permitted in that correction slice.

## Later construction

Only after the correction is committed, hashed, and independently audited may
a new R3 construction identity be proposed. It must use a new fixed controller
hash and new absent output path. R1 and R2 remain permanently retired.

## Claim boundary

This slice establishes only
`LocalRetiredR1FingerprintBuilderSchemaCorrectionBoundaryV28R2`. It is not a
corrected builder, fingerprint, protocol pin, V28R2 eligibility, novelty,
acquisition, consolidation, retention/recovery, continual learning, Astral
selection, independent replication, benchmark evidence, breakthrough,
self-improvement, introspection, self-modeling, Stage 0C, Stage 1, or
production evidence.
