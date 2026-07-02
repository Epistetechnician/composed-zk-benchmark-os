# Phase 315 HSAI Mesh Repo-Patch Admission Backend Compatibility Notes

State slice: `Phase 315 HSAI Mesh repo-patch admission backend compatibility`.

## Status

Complete for the local HSAI admission-backend compatibility surface.

## Purpose

This phase prepares HSAI to evaluate Mesh `repo_patch_service` /
`investigate_and_patch` admission packets through the shared bridge schemas:

- `mesh.hsai_admission_request.v1`;
- `mesh.hsai_admission_decision.v1`;
- `mesh.combined_proof_packet.v1`.

This phase does not implement Mesh orchestration, Mesh UI, Kubernetes rollback,
feature-flag action logic, network calls, production readiness, semantic
correctness, or authority to execute patches.

## Implemented Surface

This phase adds:

- Mesh-bounded repo-patch claim labels for clean patch application, test passage,
  and protected-path exclusion;
- support for URI-shaped Mesh policy ids such as
  `mesh_policy://repo-patch/golden`;
- Mesh golden-fixture nonclaim vocabulary;
- fail-closed clearing of accepted claims when any rejection is present;
- exact `missing_explicit_nonclaims` handling for empty explicit-nonclaim
  requests;
- repo-local non-secret Mesh allow/deny fixture copies under
  `crates/hsai-agent-admission/tests/fixtures/hsai_bridge/`;
- integration tests for Mesh canonical fixture digest parity, allow/deny
  semantics, claim rejection, claim weakening, backend-run metadata
  requirements, and decision digest sensitivity.

## Admission Flow

`evaluate_mesh_hsai_admission_request` fails closed unless the request has:

- the supported admission request schema;
- the supported combined proof-packet schema;
- nonzero candidate and evidence-packet digests;
- portable Mesh run and action ids;
- a current Mesh policy id, including URI-shaped policy ids used by Mesh;
- nonempty attestation references with nonzero digests;
- explicit required nonclaims;
- passing candidate-evidence and accepted-evidence gates;
- adequate evidence for every accepted claim;
- backend-run metadata when formal-evidence metadata is present.

The returned decision is always `mesh.hsai_admission_decision.v1` and binds the
typed HSAI request digest, candidate digest, evidence packet digest, Mesh run
id, Mesh action id, Mesh policy id, accepted claims, rejected claims, weakened
claims, enforced nonclaims, formal-evidence metadata, and backend-run metadata.

## Mesh Golden Fixture Parity

The HSAI test suite reads the non-secret Mesh golden fixture shape for:

- allow request/decision;
- deny request/decision preserving `missing_explicit_nonclaims`.

Those tests verify Mesh's canonical `json.sha256.sorted_keys.compact.v1`
request and decision digests, then adapt the same fixture payloads into HSAI's
typed admission request and assert equivalent allow/deny semantics.

## Claim Adequacy

The repo-patch compatibility layer supports Mesh's bounded repo-patch claims:

- `patch_applies_cleanly`;
- `tests_passed`;
- `no_protected_paths_modified`.

It also keeps HSAI-internal binding claims available for typed backend
composition:

- `repo_patch.candidate_digest_bound`;
- `repo_patch.evidence_packet_digest_bound`;
- `repo_patch.attestation_refs_bound`;
- `repo_patch.mesh_run_action_policy_bound`;
- `repo_patch.candidate_evidence_gate_passed`;
- `repo_patch.accepted_evidence_gate_passed`;
- `repo_patch.formal_evidence_metadata_bound`.

Overbroad claims such as production readiness, semantic correctness, full
security, Kubernetes rollback safety, feature-flag action safety, or Mesh
orchestration completion are rejected. A weakened claim must carry an explicit
machine-readable reason code, and the weakened target claim must itself be
supported by adequate evidence.

## Nonclaims

Required nonclaims preserve the HSAI/Mesh boundary and match the Mesh golden
fixture vocabulary:

- `does_not_claim_accepted_hsai_evidence`;
- `does_not_claim_formal_proof`;
- `does_not_claim_global_correctness`;
- `does_not_claim_production_certification`;
- `does_not_claim_security_review_complete`.

An `allow` decision is valid only when every accepted claim is explicitly
supported by evidence and bounded by the enforced nonclaims. A request with an
empty explicit-nonclaim set denies with exactly `missing_explicit_nonclaims`.

## Validation

Required validation for this slice:

```text
cargo fmt --all -- --check
cargo test -p hsai-agent-admission --test mesh_repo_patch_admission_contract
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan
cargo test -p zkbench-core --test repo_claim_boundary_docs --test repo_hygiene
git diff --check
find README.md AGENTS.md docs crates -type f -empty
pnpm run lint, if package.json exists
cargo test --workspace
```

## Next Slice

Phase 316 returned to the formal-backend lane with a docs-first tiny hermetic
adapter contract boundary. See
`docs/316-hsai-tiny-hermetic-formal-backend-adapter-contract-boundary.md`.
