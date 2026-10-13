# Immutable Validation Release V1

State slice: `astral-immutable-validation-release-v1`.

Status: `LocalValidationCandidate`. Claim ceiling:
`LocalImmutableValidationCandidate`.

## Scope

This release freezes the Astral V1-V23 research source and packages the pivotal
V18-V23 artifacts without changing their results. It provides author-side
repeatability and an immutable handoff for external reproduction. It is not an
independent review, independent implementation, Stage 0C confirmation, or
evidence acceptance.

The release package contains:

- complete V18, V20, and V21 bundles;
- stopped V19, V22, and V23 bundles with assessment absence preserved;
- package and per-bundle manifests;
- exact source and environment inventories;
- the staged Git tree identity;
- release specification and expected classifications;
- this release note and the independent-validation handoff.

The content address is the SHA-256 of `PACKAGE-MANIFEST.sha256` and appears in
the package directory name.

## Authoritative validation

From the exact release commit:

```text
python tools/astral-validation-release-v1/validate_release.py \
  --package <content-addressed-package> \
  --report <new-external-report.json>
```

The validator fails closed unless:

1. the launcher worktree is clean and a detached worker is created at `HEAD`;
2. the package census, hashes, and content-addressed name agree;
3. the detached commit tree matches the packaged staged tree;
4. every inventoried release source file matches;
5. all V18-V23 validators pass;
6. V19/V22/V23 assessment artifacts remain absent;
7. every V18-V23 corpus regenerates exactly;
8. V20/V21 metrics recompute from locked predictions and assessment targets;
9. claim-ledger IDs, dispositions, and artifact identities agree;
10. all Astral structural tests pass;
11. the Rust protocol crate passes its locked tests.

The launcher removes the detached worker after success or failure.

The report receives a SHA-256 sidecar. This is digest sealing, not an
identity-bearing signature.

## Claim boundary

A passing report supports only:

> The frozen author-supplied Astral source and artifacts are internally
> consistent and repeatable in the recorded local environment.

It does not validate introspection, self-modeling, privileged internal access,
Stage 0C, Stage 1, benchmark performance, or production readiness.
