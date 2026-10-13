# Independent-Review Capsule V1

State slice: `astral-independent-review-capsule-v1`.

Status: `LocalReviewCapsuleCandidate`.

Claim ceiling: `LocalImmutableValidationCandidate`.

## Purpose

The immutable V1 release package contains artifact bytes and a source hash
inventory, but an external reviewer also needs the exact Git source without
access to the author's local branch. This capsule closes that portability gap.
It does not complete or simulate independent review.

The content-addressed capsule contains:

- the complete Git history needed to clone release commit
  `a875957cc1f0ba12e0027fd69a44f8b6a94bcfdf`;
- the content-addressed V18-V23 package
  `7dd61f997bd2cbd8f55f497331ed83757bf994c80a2dc3f01fc1bf1516a9a483`;
- the digest-sealed author report
  `3f7c64895d3e910c71bbc3dfe856e4dd6fa5ced802c70ccc5899f10b6a8b5b8c`;
- the exact author runtime contract and direct Python dependency versions;
- a standalone capsule verifier and clean clone-and-replay entrypoint;
- untouched `NotRun` templates for reproducibility and scientific review;
- a top-level `CAPSULE-MANIFEST.sha256`.

## Reviewer invocation

From the capsule root:

```text
python tools/run_capsule.py --workspace <new-empty-external-path>
```

The command does not install dependencies or use the network. By default it
fails before replay when the Python, package, platform, Rust, Cargo, or Git
runtime differs from the author contract. A reviewer may use
`--allow-environment-drift` only to continue while retaining every difference
in the output report.

The runner:

1. rejects symlinks and verifies the exact capsule census and hashes;
2. checks the content-addressed capsule name;
3. verifies release commit, tree, package, and author-report identities;
4. creates a fresh clone from the complete Git bundle;
5. checks out the release commit detached and confirms a clean tree;
6. invokes the release's authoritative validator, which creates its own
   detached worker;
7. verifies the resulting report and preserves environment drift;
8. emits digest-sealed `capsule-run.json` and reviewer report files;
9. copies unfilled reviewer templates into the external workspace.

## Decision boundary

A green author run proves only that the capsule is portable on the author's
recorded environment. A green external run proves artifact reproducibility only
after a genuine external reviewer discloses identity, conflicts, environment,
assistance, findings, and an identity-bearing signature.

Scientific review and an independent reimplementation remain separate gates.
No capsule run validates introspection, self-modeling, privileged internal
access, Stage 0C, Stage 1, benchmark evidence, or production readiness.
