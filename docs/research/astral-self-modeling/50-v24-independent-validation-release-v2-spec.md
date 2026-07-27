# V24 Independent-Validation Release V2 Specification

State slice: `astral-v24-independent-validation-release-v2`.

Status: `CompletedLocalConstructionAndReplay`.

Claim ceiling: `LocalAuthorDevelopmentPerturbationReadout`.

Independent verification: `NotRun`.

Confirmation: `NotAuthorized`.

## Frozen subject

V2 is additive and does not modify the immutable V1 release or signed-review
protocol. It binds only:

- source commit `de4ac8145ed3e730f9a2ed1495921084a078ab39`;
- source tree `4a2cbaaebfba15186ae9a2829b516eca74b71b40`;
- V24 artifact manifest
  `288feb32b4833544d57988a61c9e76f95856777ab4346dea553eee539fcba9c3`;
- the exact Qwen model-file inventory retained by the V24 artifact;
- the V24 preregistration, implementation, validator, tests, execution record,
  metrics, predictions, locks, environment inventory, and claim-ledger update.

The release must contain the model bytes named by the retained inventory so a
reviewer does not depend on the author's absolute local model path. All bytes
are covered by a sorted SHA-256 census and content-addressed directory name.

## AdminCoordinator

The local account `shaanp` is assigned role `AdminCoordinator`. Its allowed
Ed25519 public-key fingerprints are:

- `SHA256:WHIhl2ms0coQUY3AzGDnbbjzO/IkFXYOWAj/lZGkrFs`;
- `SHA256:3ZJtYkE/2lq+KjHOaUQq+qqdYAhydmGMRz/KNfp+1oU`.

The corresponding private keys remain outside the repository and every
release artifact. Admin authorization is an OpenSSH namespace-separated
signature over canonical reviewer-registry bytes. The admin may:

1. assign distinct reviewer identities and roles;
2. classify each reviewer as `agent_advisory` or `external_human`;
3. issue fresh role-bound requests after signing the registry;
4. reject or replace a registry before request issuance.

The admin may not sign a reviewer decision on the reviewer's behalf, use one
reviewer for both roles, waive an unresolved material finding, change retained
evidence, or assert independence merely by assigning a reviewer.

## Reviewer-agent boundary

Two separate reviewer agents may be authorized for
`artifact_reproducibility` and `scientific_validity`. Each requires a distinct
signing key, request nonce, decision, and evidence inventory. When either
reviewer is `agent_advisory`, the highest possible gate result is
`AuthorizedAgentReviewAdvisoryCandidate`.

Agent reviews are useful pre-audits. They do not set `IndependentlyVerified`,
do not count as external scientific review, and do not satisfy independent
implementation replication. Only two genuine external reviewers, followed by
an external coordinator's identity and conflict check, may yield a signed
external-review quorum candidate.

## Release and replay

The release validator must:

1. verify the release census, content-addressed name, source commit and tree;
2. verify every V24 artifact and model-file digest;
3. regenerate corpus, predictions, metrics, gates, bootstrap, classification,
   and claim-ledger correspondence from the frozen source;
4. run V24 and Astral structural tests in a clean detached checkout;
5. emit a digest-sealed report with every external state still unpromoted.

The capsule must include a complete Git bundle, the release, author report,
runtime contract, standalone replay tooling, review templates, and the admin
policy. Its runner creates a new external workspace, checks out the frozen
commit detached, validates the release, and emits digest-sealed replay files.

## Stop conditions

Construction stops on any source, model, artifact, manifest, environment,
metric, gate, role, key, signature, evidence, or claim-boundary mismatch.
Nothing in V2 authorizes a V24 assessment rerun, a confirmation experiment,
Stage 0C, Stage 1, evidence acceptance, introspection claims, self-modeling
claims, or independent-verification status changes.

The exact local construction, replay, admin policy, and remaining review gates
are recorded in
[the V2 execution record](51-v24-independent-validation-release-v2-execution-record.md).
