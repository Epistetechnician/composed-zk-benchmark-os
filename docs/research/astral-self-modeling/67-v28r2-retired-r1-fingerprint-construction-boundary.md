# V28R2 Retired-R1 Fingerprint Construction Boundary

State slice:
`astral-rgs-v28r2-retired-r1-fingerprint-construction-boundary`.

Status: `DocsFirstBoundaryComplete / ConstructionNotRun /
FingerprintNotBuilt / ProtocolPinUnchanged / R2ExecutionNotAuthorized`.

## Purpose

V28R2 cannot evaluate corpus nonreuse while the frozen protocol retains
`retired_r1_fingerprint_manifest_sha256: not-built`. The next mechanical step
is one read-only pass over the retained V28R1 bundle using the committed
hash-only builder. This note fixes that future pass before any builder
execution.

This documentation slice does not run the builder, create the fingerprint, or
change the V28R2 protocol pin.

## Pinned implementation

The future construction must use exactly:

- composed repository commit
  `8cf75d745c20afa885286fecfbd8d67c253b8707`;
- protocol file SHA-256
  `sha256:8ea8841769f7364fc3c0cc5e935f0eb24843f84ca95aa99b8cee9a1863117430`;
- canonical protocol SHA-256
  `sha256:236d7a2f4d8f81fdd1990c746cdfff0d3de85c191781bb7c3fde9d84d5b1aaf2`;
- validator-core file SHA-256
  `sha256:044fee8a7f3fc8fdb6d7bc474cb378c227d088c431a62448863c2aef3e935556`;
- validator-CLI file SHA-256
  `sha256:5e3cfda4f0aff0ab44f505a9e51ef6edff6e2b5798660c77f32580331cbddbc0`;
- fingerprint-builder file SHA-256
  `sha256:2bac334ee634c59a290a12784a52321d6fe7f80513d94d540ae07c17f4190324`.

Any source drift requires a new docs-first boundary. The future construction
must run from a clean checkout of the pinned commit.

## Pinned retained input

The only permitted input root is:

```text
/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v28-acquisition-novelty-a4e9dd0-r1
```

The builder must receive exactly these three files from that root:

```text
acquisition-packet.json
astral-validation-report.json
artifact-manifest.json
```

Their frozen semantic identities are:

- packet:
  `sha256:2fd74b389907d3167518a0d91d9d63f18fda7c1231a51764657e791286ee2ad0`;
- validation report:
  `sha256:3e24804dc84744a300bb11bc246fdfd40256459f97a68da0df7993d676b9ea3d`;
- artifact manifest:
  `sha256:5b01a32e1ba9d7d9ce84c8b301f29e0145962ac8c0eac0ec59b07cd5cfca846e`.

Their frozen raw-file identities are:

- packet:
  `sha256:f3b5217e725322d2cf964267b63af4fb956a0232507ac646f07fbaf12a31c121`;
- validation report:
  `sha256:0ec4215734583566f593c6214eec2317523e0bc7471e6d9f837ca3e0337b53e9`;
- artifact manifest:
  `sha256:7ca7e09302aff508368d53335aa47c90564fa6393e262ecadc8db51e401ce5f7`.

The builder must validate the complete closed retained-bundle census before
extracting any fingerprint.

## Fixed output

The only permitted future output is the new, repository-external path:

```text
/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v28r1-retired-fingerprint-8cf75d7-r1.json
```

The output path must not exist before execution. The future construction
preflight, not the unchanged builder alone, owns exact path enforcement. It
must compare the supplied input root, three input paths, and output path
byte-for-byte with this note; reject any symlink in every existing path
component; require the three inputs to be regular files; require the output
parent and all ancestors to be real directories; and require the output to be
absent. Any mismatch consumes and rejects the construction identity before the
builder starts.

After that preflight, the builder owns retained content/bundle validation,
exclusive output creation, canonical durable writing, overwrite refusal, and
partial-validation refusal. A byte-identical copied input root or alternate
output could satisfy the builder alone and therefore must never reach it.

The output may contain only domain-separated hashes, counts, set hashes,
frozen source identities, normalization metadata, and the
`CorpusNotNovel` disposition. It may not contain raw corpus text, generated
identifiers, model observations, choices, scores, secrets, or model outcomes.

## Future execution order

A later explicitly authorized construction slice must:

1. verify the pinned checkout is clean and the six implementation identities
   above match;
2. run the exact-path and no-symlink construction preflight above over all four
   supplied file paths, verify the fixed output is absent, and reject the
   construction identity on any mismatch;
3. only after that preflight passes, invoke the committed builder once with the
   three exact absolute inputs and exact absolute output;
4. stop without retry or alternate output on any error;
5. compute and record both the output raw-file SHA-256 and its canonical
   `manifest_sha256`;
6. independently audit the output shape, set census, source bindings, and
   absence of raw R1 material;
7. leave the V28R2 protocol at `not-built` until a separate reviewed pinning
   slice commits the accepted fingerprint and repins the canonical protocol.

Construction does not authorize V28R2 seed creation, corpus generation,
tokenizer or model access, baseline execution, update arms, recovery,
selection, assessment, or claim promotion.

## Validation required before later pinning

The future construction record must include:

- exact command and exit status;
- clean source commit and tree;
- all six pinned implementation identities;
- all six retained semantic/raw input identities;
- output raw-file SHA-256 and canonical manifest SHA-256;
- fingerprint-set names, counts, and set hashes;
- confirmation that `model_outcomes_included` is false;
- confirmation that no raw retained identifier or text is present;
- independent repository, validation, and research-scope audit verdicts.

Any mismatch permanently rejects that output. It does not authorize a repaired
second output under the same construction identity.

## Claim boundary

This slice establishes only
`LocalRetiredR1FingerprintConstructionBoundaryV28R2`. It is not a fingerprint,
protocol pin, V28R2 corpus, novelty result, acquisition, consolidation,
retention/recovery, continual learning, Astral selection, independent
replication, benchmark evidence, breakthrough, self-improvement,
introspection, self-modeling, Stage 0C, Stage 1, or production evidence.
