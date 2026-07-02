# Phase 308 HSAI Mesh Repo-Patch Admission Backend Compatibility Notes

State slice: `hsai-mesh-repo-patch-admission-backend-compatibility`.

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

## Admission Flow

`evaluate_mesh_hsai_admission_request` fails closed unless the request has:

- the supported admission request schema;
- the supported combined proof-packet schema;
- nonzero candidate and evidence-packet digests;
- portable Mesh run, action, and current policy ids;
- nonempty attestation references with nonzero digests;
- explicit required nonclaims;
- passing candidate-evidence and accepted-evidence gates;
- adequate evidence for every accepted claim;
- backend-run metadata when formal-evidence metadata is present.

The returned decision is always `mesh.hsai_admission_decision.v1` and binds the
request digest, candidate digest, evidence packet digest, Mesh run id, Mesh
action id, Mesh policy id, accepted claims, rejected claims, weakened claims,
enforced nonclaims, formal-evidence metadata, and backend-run metadata.

## Claim Adequacy

The repo-patch compatibility layer currently supports these bounded claims:

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

Required nonclaims preserve the HSAI/Mesh boundary:

- not Mesh orchestration;
- not Kubernetes rollback authority;
- not feature-flag action authority;
- not production readiness;
- not semantic correctness;
- not full security;
- not benchmark evidence;
- not accepted Evidence Ledger mutation;
- not authority to execute a patch.

An `allow` decision is valid only when every accepted claim is explicitly
supported by evidence and bounded by the enforced nonclaims.
