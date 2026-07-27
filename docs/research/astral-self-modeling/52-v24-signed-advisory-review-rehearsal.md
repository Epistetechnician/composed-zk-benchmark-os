# V24 Signed Advisory-Review Rehearsal

State slice: `astral-v24-independent-validation-release-v2`.

Status: `AuthorizedAgentReviewAdvisoryCandidate`.

Independent verification: `NotRun`.

Confirmation: `NotAuthorized`.

Stage 0C: `Blocked`. Stage 1: `BlockedByStage0C`.

Claim ceiling: `LocalAuthorDevelopmentPerturbationReadout`.

## Purpose and authority

This rehearsal exercised the V2 admin assignment, role separation, clean-room
replay, evidence inventory, reviewer signatures, and fail-closed gate. It did
not substitute agents for external humans. Both reviewers were declared
`agent_advisory` with `counts_toward_independent_verification: false` before the
admin signed the registry.

The `shaanp` `AdminCoordinator` signed only the canonical reviewer registry.
Each reviewer generated a distinct Ed25519 key, retained its own private key in
its external workspace, and signed only its own role-bound decision. No private
key entered the repository, release, capsule, campaign package, or evidence.

Registry SHA-256:
`73879f7907f8e0e76937e7cd0810b738e870748cdb48d6f6e43afcb2564b7dee`.

Reviewer fingerprints:

- artifact reproducibility:
  `SHA256:VdlUE8rz+dzerWr6UYY8Gp+tJ1SPzNUKYqQsCSNjghY`;
- scientific validity:
  `SHA256:HJJmjdtpO2n/EosggDpLgDwKr+yeNb9fFWzRW3vhDYo`.

## Attempt 1: retained rejection

The first artifact-reproducibility replay used an unpinned Python runtime. The
capsule detected Python identity differences and missing MLX, MLX-LM, and Torch,
then stopped before checkout, immutable validation, or tests. The reviewer
correctly signed `Fail` with an unresolved material environment finding.

The scientific reviewer independently used the pinned runtime, reproduced the
release, and signed `PassWithFindings`. Because one role failed, the gate
returned `SignedReviewGateRejected` rather than averaging or overriding the
decisions.

- first request-manifest SHA-256:
  `a94291f334d1c6c6ede7f952dd296bac636ddaa80300a1fc9e47941651441c0f`;
- rejected gate-report SHA-256:
  `ef47ce145c87c849c6e6ea0c6da1e31e19bf239d1f7dbb0fe672161164379c9a`;
- failed artifact decision SHA-256:
  `9673a25bdd81907749a7afd2cc7af6b853c46c9d70ad32d78d0bb8f2c0cd6134`;
- artifact signature SHA-256:
  `78565235f9a2cc51cc03770181acc4d3b4c7b3cd533a89714f2ab77ad19d2716`.

Attempt 1 remains in the final campaign package. It was not deleted, rewritten,
or reclassified.

## Attempt 2: pinned-runtime advisory candidate

The admin issued fresh requests and nonces. Both reviewers invoked the capsule
with `/Users/shaanp/.pyenv/versions/3.14.5/bin/python` and without an environment-
drift override. Both fresh workspaces reported exact runtime matches,
`V24CapsuleReplayPassed`, `V24ImmutableValidationPassed`, 114 passing Astral
structural tests, and six passing Rust protocol tests.

The artifact reviewer signed `Pass` with no findings:

- request SHA-256:
  `4646768387ba96dfd92ab7183399833a27450a22ed8aab3e286e26d29e106bb5`;
- capsule-run SHA-256:
  `5ead9abaa3c70502a27017d1de9b293736548b9a19714d7837761f7a72af84e3`;
- reviewer-report SHA-256:
  `9316bb8ae3b7733e07cd5e9c3502cb05c40ad72c5eabd3237dda592151a90b6a`;
- decision SHA-256:
  `4f8802d5ceccbf41afea958cb935b8b3545194729989ac8877945b4fd4661103`;
- signature SHA-256:
  `8904d1d79b5cced814c33060a2a07e1252caeaad65aa279107f6b6db72cdc7e4`.

The scientific reviewer signed `PassWithFindings` with no unresolved material
finding:

- request SHA-256:
  `d621794030e0bbe8a67f8d6069785f0d6cd1eb4c3c2ea1ea720bf1e8d29b73db`;
- capsule-run SHA-256:
  `f06f5ca440519db51b02b27119a88d636ed0c5f8bb87d61e6e82859b90ff5fd9`;
- reviewer-report SHA-256:
  `de72690f5ef4e79052d90492e63cf866a1a0a27e530d22acf8f7fab721d8b1ba`;
- decision SHA-256:
  `706ad0406f68744e37fb1672db20fe08a47cdaaa4be3a4a258a6236f861a2484`;
- signature SHA-256:
  `625a834af9859155d33ce7bbf2a10c658dc5ecd62ada456048f7910ad29175a4`.

The second request-manifest SHA-256 is
`f7289738b1911c1ef6fc9b17b2e011d679735cade109a3b63de5e22520b59977`.
The verified gate returned `AuthorizedAgentReviewAdvisoryCandidate` with report
SHA-256
`6ef687dc7c27589e21cba07907f3318e2a9adc7d0bbfaa79a3ea893ab862b02d`.

## Scientific findings

The advisory scientific review retained three bounded findings:

1. Four assessment concepts do not support broad checkpoint, task,
   concept-population, or intervention-family generalization, although all four
   had positive telemetry advantage over their strongest primary control.
2. The five-summary anomaly control does not exclude every generic
   perturbation signature. Confirmation requires a matched random-direction or
   equivalent intervention-specificity control.
3. The passing Brier gate is a local proper-score diagnostic. Forty-eight rows
   without fuller reliability analysis do not establish general calibration.

These findings do not invalidate the narrow local claim already recorded. They
prevent broader interpretation and constrain any future confirmation protocol.

## Immutable campaign package

The read-only 47-file campaign package is:

`/Users/shaanp/Documents/ResearchArtifacts/astral-v24-advisory-review-campaign-v2-d17c4133c78909913554fd95e37d7e7e2aecbd90fc40b0692c9d8ac1cb8575b5`

Campaign identity:
`d17c4133c78909913554fd95e37d7e7e2aecbd90fc40b0692c9d8ac1cb8575b5`.

The sorted manifest covers both issued request sets, both attempts' evidence and
decisions, every signature, both gate reports, the canonical registry, and the
admin signature. A secret-shape scan found no private-key material.

## Exact remaining unblock

This rehearsal closes the local mechanical path only. To create an external-
review candidate, the admin must sign a new registry naming two real external
humans with independently confirmed identities, conflicts, affiliations, and
distinct public keys. Those reviewers must run the capsule outside the author
environment, retain and sign their own evidence and decisions, and resolve all
material findings. The resulting `SignedExternalReviewQuorumCandidate` still
requires a human coordinator's identity and conflict check before any
independent-review status can change.

Independent implementation replication remains separate. It requires a fresh
implementation, corpus, sealed assessment, and preferably another checkpoint
without importing the Astral harness. Confirmation remains separately
unauthorized, and Stage 0C still requires prospective intervention-effect
prediction before an intervention is applied. Neither this advisory result nor
future artifact review alone can unblock Stage 0C or Stage 1.
