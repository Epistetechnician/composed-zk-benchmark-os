import hashlib
import json
from pathlib import Path

import pytest

from experiments.continual_learning.fork_topology import (
    CLAIM_CEILING,
    STATE_SLICE,
    ForkLedger,
    ForkNode,
    MergeProposal,
    ForkTopologyPolicy,
    ForkTopologyError,
    validate_portable_manifest,
    validate_topology_bundle,
)


def _root() -> ForkNode:
    return ForkNode(
        fork_id="shared-root",
        scope_kind="shared",
        scope_id="global",
        parent_fork_id=None,
        model_id="base-model",
        model_digest="1" * 64,
        update_kind="base",
        source_update_digest=None,
        consent_scope="not-applicable-v1",
        portable=True,
        portability_manifest_digest="2" * 64,
    )


def _tenant_fork() -> ForkNode:
    return ForkNode(
        fork_id="tenant-a-fork-001",
        scope_kind="tenant",
        scope_id="tenant-a",
        parent_fork_id="shared-root",
        model_id="tenant-a-model-001",
        model_digest="3" * 64,
        update_kind="adapter",
        source_update_digest="4" * 64,
        consent_scope="tenant-training-opt-in-v1",
        portable=True,
        portability_manifest_digest="5" * 64,
    )


def _reseal_bundle(bundle: dict[str, object]) -> dict[str, object]:
    unsigned = {key: value for key, value in bundle.items() if key != "bundle_sha256"}
    bundle["bundle_sha256"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return bundle


def test_root_and_tenant_fork_export_as_deterministic_readback_safe_topology() -> None:
    ledger = ForkLedger(_root())

    decision = ledger.create_tenant_fork(_tenant_fork())
    first_bundle = ledger.export_bundle()
    second_bundle = ledger.export_bundle()

    assert decision.status == "accepted"
    assert ledger.head("tenant", "tenant-a").fork_id == "tenant-a-fork-001"
    assert first_bundle == second_bundle
    assert first_bundle["state_slice"] == STATE_SLICE
    assert first_bundle["claim_ceiling"] == CLAIM_CEILING
    validate_topology_bundle(first_bundle)


def test_cross_tenant_parent_is_quarantined_without_mutating_topology() -> None:
    ledger = ForkLedger(_root())
    assert ledger.create_tenant_fork(_tenant_fork()).status == "accepted"
    before = ledger.export_bundle()
    cross_tenant = ForkNode(
        fork_id="tenant-b-fork-001",
        scope_kind="tenant",
        scope_id="tenant-b",
        parent_fork_id="tenant-a-fork-001",
        model_id="tenant-b-model-001",
        model_digest="6" * 64,
        update_kind="adapter",
        source_update_digest="7" * 64,
        consent_scope="tenant-training-opt-in-v1",
        portable=True,
        portability_manifest_digest="8" * 64,
    )

    decision = ledger.create_tenant_fork(cross_tenant)

    assert decision.status == "quarantined"
    assert decision.reasons == ("cross_tenant_parent",)
    assert ledger.export_bundle() == before


def test_tenant_to_tenant_merge_is_quarantined_without_mutating_topology() -> None:
    ledger = ForkLedger(_root())
    assert ledger.create_tenant_fork(_tenant_fork()).status == "accepted"
    before = ledger.export_bundle()
    proposal = MergeProposal(
        proposal_id="merge-001",
        source_fork_id="tenant-a-fork-001",
        target_shared_fork_id="tenant-a-fork-001",
        candidate_model_id="merged-model-001",
        candidate_model_digest="9" * 64,
        source_update_digest="4" * 64,
        merge_consent_scope="shared-model-merge-opt-in-v1",
        review_status="reviewed",
        review_digest="a" * 64,
    )

    decision = ledger.propose_merge(proposal)

    assert decision.status == "quarantined"
    assert decision.reasons == ("merge_target_not_shared",)
    assert ledger.export_bundle() == before


def test_reviewed_merge_proposal_is_eligible_but_does_not_move_shared_head() -> None:
    ledger = ForkLedger(_root())
    assert ledger.create_tenant_fork(_tenant_fork()).status == "accepted"
    proposal = MergeProposal(
        proposal_id="merge-002",
        source_fork_id="tenant-a-fork-001",
        target_shared_fork_id="shared-root",
        candidate_model_id="merged-model-002",
        candidate_model_digest="b" * 64,
        source_update_digest="4" * 64,
        merge_consent_scope="shared-model-merge-opt-in-v1",
        review_status="reviewed",
        review_digest="c" * 64,
    )

    decision = ledger.propose_merge(proposal)

    assert decision.status == "merge_eligible"
    assert decision.reasons == ()
    assert ledger.head("shared", "global").fork_id == "shared-root"
    validate_topology_bundle(ledger.export_bundle())


def test_accepted_merge_creates_shared_descendant_without_moving_tenant_head() -> None:
    ledger = ForkLedger(_root())
    assert ledger.create_tenant_fork(_tenant_fork()).status == "accepted"
    proposal = MergeProposal(
        proposal_id="merge-003",
        source_fork_id="tenant-a-fork-001",
        target_shared_fork_id="shared-root",
        candidate_model_id="merged-model-003",
        candidate_model_digest="d" * 64,
        source_update_digest="4" * 64,
        merge_consent_scope="shared-model-merge-opt-in-v1",
        review_status="reviewed",
        review_digest="e" * 64,
    )
    assert ledger.propose_merge(proposal).status == "merge_eligible"
    merged = ForkNode(
        fork_id="shared-merge-001",
        scope_kind="shared",
        scope_id="global",
        parent_fork_id="shared-root",
        model_id="merged-model-003",
        model_digest="d" * 64,
        update_kind="adapter",
        source_update_digest="4" * 64,
        consent_scope="shared-model-merge-opt-in-v1",
        portable=True,
        portability_manifest_digest="f" * 64,
    )

    decision = ledger.accept_merge("merge-003", merged)

    assert decision.status == "accepted"
    assert ledger.head("shared", "global").fork_id == "shared-merge-001"
    assert ledger.head("tenant", "tenant-a").fork_id == "tenant-a-fork-001"
    assert ledger.fork("shared-root").fork_id == "shared-root"
    validate_topology_bundle(ledger.export_bundle())


def test_shared_merge_requires_separate_consent_and_review() -> None:
    ledger = ForkLedger(_root())
    assert ledger.create_tenant_fork(_tenant_fork()).status == "accepted"
    before = ledger.export_bundle()
    proposal = MergeProposal(
        proposal_id="merge-004",
        source_fork_id="tenant-a-fork-001",
        target_shared_fork_id="shared-root",
        candidate_model_id="merged-model-004",
        candidate_model_digest="1" * 64,
        source_update_digest="4" * 64,
        merge_consent_scope="tenant-training-opt-in-v1",
        review_status="pending",
        review_digest="a" * 64,
    )

    decision = ledger.propose_merge(proposal)

    assert decision.status == "quarantined"
    assert decision.reasons == (
        "candidate_model_digest_unchanged",
        "merge_consent_scope_invalid",
        "merge_review_missing",
    )
    assert ledger.export_bundle() == before


def test_rollback_moves_only_the_scope_head_and_retains_later_forks() -> None:
    ledger = ForkLedger(_root())
    assert ledger.create_tenant_fork(_tenant_fork()).status == "accepted"
    second = ForkNode(
        fork_id="tenant-a-fork-002",
        scope_kind="tenant",
        scope_id="tenant-a",
        parent_fork_id="tenant-a-fork-001",
        model_id="tenant-a-model-002",
        model_digest="b" * 64,
        update_kind="adapter",
        source_update_digest="c" * 64,
        consent_scope="tenant-training-opt-in-v1",
        portable=True,
        portability_manifest_digest="d" * 64,
    )
    assert ledger.create_tenant_fork(second).status == "accepted"

    decision = ledger.rollback(
        "tenant", "tenant-a", "tenant-a-fork-001", "safety-regression"
    )

    assert decision.status == "rolled_back"
    assert ledger.head("tenant", "tenant-a").fork_id == "tenant-a-fork-001"
    assert ledger.fork("tenant-a-fork-002").fork_id == "tenant-a-fork-002"
    validate_topology_bundle(ledger.export_bundle())


def test_readback_rejects_resealed_head_drift() -> None:
    ledger = ForkLedger(_root())
    assert ledger.create_tenant_fork(_tenant_fork()).status == "accepted"
    tampered = dict(ledger.export_bundle())
    tampered["heads"] = {"shared:global": "shared-root", "tenant:tenant-a": "shared-root"}
    unsigned = {key: value for key, value in tampered.items() if key != "bundle_sha256"}
    tampered["bundle_sha256"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    with pytest.raises(ForkTopologyError, match="head_state_invalid"):
        validate_topology_bundle(tampered)


def test_readback_rejects_resealed_merge_proposal_binding_drift() -> None:
    ledger = ForkLedger(_root())
    assert ledger.create_tenant_fork(_tenant_fork()).status == "accepted"
    proposal = MergeProposal(
        proposal_id="merge-readback-binding",
        source_fork_id="tenant-a-fork-001",
        target_shared_fork_id="shared-root",
        candidate_model_id="merged-readback-binding",
        candidate_model_digest="9" * 64,
        source_update_digest="4" * 64,
        merge_consent_scope="shared-model-merge-opt-in-v1",
        review_status="reviewed",
        review_digest="a" * 64,
    )
    assert ledger.propose_merge(proposal).status == "merge_eligible"
    tampered = dict(ledger.export_bundle())
    tampered["proposals"] = [dict(item) for item in tampered["proposals"]]
    tampered["proposals"][0]["source_fork_id"] = "shared-root"
    _reseal_bundle(tampered)

    with pytest.raises(ForkTopologyError, match="proposal_source_scope_invalid"):
        validate_topology_bundle(tampered)


def test_readback_rejects_resealed_merge_event_binding_drift() -> None:
    ledger = ForkLedger(_root())
    assert ledger.create_tenant_fork(_tenant_fork()).status == "accepted"
    proposal = MergeProposal(
        proposal_id="merge-readback-event",
        source_fork_id="tenant-a-fork-001",
        target_shared_fork_id="shared-root",
        candidate_model_id="merged-readback-event",
        candidate_model_digest="9" * 64,
        source_update_digest="4" * 64,
        merge_consent_scope="shared-model-merge-opt-in-v1",
        review_status="reviewed",
        review_digest="a" * 64,
    )
    assert ledger.propose_merge(proposal).status == "merge_eligible"
    tampered = dict(ledger.export_bundle())
    tampered["events"] = [dict(item) for item in tampered["events"]]
    tampered["events"][2]["reason"] = "unknown-proposal"
    tampered["events"][2]["event_digest"] = hashlib.sha256(
        json.dumps(
            {
                key: value
                for key, value in tampered["events"][2].items()
                if key != "event_digest"
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    _reseal_bundle(tampered)

    with pytest.raises(ForkTopologyError, match="event_proposal_missing"):
        validate_topology_bundle(tampered)


def test_readback_rejects_resealed_merge_result_binding_drift() -> None:
    ledger = ForkLedger(_root())
    assert ledger.create_tenant_fork(_tenant_fork()).status == "accepted"
    proposal = MergeProposal(
        proposal_id="merge-readback-result",
        source_fork_id="tenant-a-fork-001",
        target_shared_fork_id="shared-root",
        candidate_model_id="merged-readback-result",
        candidate_model_digest="9" * 64,
        source_update_digest="4" * 64,
        merge_consent_scope="shared-model-merge-opt-in-v1",
        review_status="reviewed",
        review_digest="a" * 64,
    )
    assert ledger.propose_merge(proposal).status == "merge_eligible"
    merged = ForkNode(
        fork_id="shared-merge-readback-result",
        scope_kind="shared",
        scope_id="global",
        parent_fork_id="shared-root",
        model_id="merged-readback-result",
        model_digest="9" * 64,
        update_kind="adapter",
        source_update_digest="4" * 64,
        consent_scope="shared-model-merge-opt-in-v1",
        portable=True,
        portability_manifest_digest="b" * 64,
    )
    assert ledger.accept_merge(proposal.proposal_id, merged).status == "accepted"
    tampered = dict(ledger.export_bundle())
    tampered["forks"] = [dict(item) for item in tampered["forks"]]
    merged_payload = next(
        item
        for item in tampered["forks"]
        if item["fork_id"] == "shared-merge-readback-result"
    )
    merged_payload["model_id"] = "forged-result-model"
    _reseal_bundle(tampered)

    with pytest.raises(ForkTopologyError, match="event_merge_result_model_id_mismatch"):
        validate_topology_bundle(tampered)


def test_portable_readback_requires_shared_root_lineage() -> None:
    ledger = ForkLedger(_root())
    assert ledger.create_tenant_fork(_tenant_fork()).status == "accepted"
    manifest = dict(ledger.export_portable_manifest("tenant-a-fork-001"))
    manifest["lineage"] = [dict(item) for item in manifest["lineage"]]
    manifest["lineage"][0]["scope_kind"] = "tenant"
    unsigned = {key: value for key, value in manifest.items() if key != "export_sha256"}
    manifest["export_sha256"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    with pytest.raises(ForkTopologyError, match="portable_lineage_node_invalid"):
        validate_portable_manifest(manifest)


def test_nonportable_tenant_fork_is_quarantined_before_head_creation() -> None:
    ledger = ForkLedger(_root())
    before = ledger.export_bundle()
    nonportable = ForkNode(
        fork_id="tenant-a-fork-nonportable",
        scope_kind="tenant",
        scope_id="tenant-a",
        parent_fork_id="shared-root",
        model_id="tenant-a-model-nonportable",
        model_digest="6" * 64,
        update_kind="full_weights",
        source_update_digest="7" * 64,
        consent_scope="tenant-training-opt-in-v1",
        portable=False,
        portability_manifest_digest=None,
    )

    decision = ledger.create_tenant_fork(nonportable)

    assert decision.status == "quarantined"
    assert decision.reasons == (
        "fork_not_portable",
        "portability_manifest_invalid",
    )
    assert ledger.export_bundle() == before


def test_readback_rejects_type_drift_after_bundle_resealing() -> None:
    bundle = ForkLedger(_root()).export_bundle()
    tampered = dict(bundle)
    tampered_forks = [dict(fork) for fork in bundle["forks"]]
    tampered_forks[0]["portable"] = "true"
    tampered["forks"] = tampered_forks
    unsigned = {key: value for key, value in tampered.items() if key != "bundle_sha256"}
    tampered["bundle_sha256"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    with pytest.raises(ForkTopologyError, match="portable_invalid"):
        validate_topology_bundle(tampered)


def test_malformed_direct_inputs_quarantine_without_type_errors_or_mutation() -> None:
    ledger = ForkLedger(_root())
    assert ledger.create_tenant_fork(_tenant_fork()).status == "accepted"
    before = ledger.export_bundle()

    malformed_fork = ForkNode(
        fork_id=["not-a-string"],
        scope_kind="tenant",
        scope_id="tenant-a",
        parent_fork_id=["shared-root"],
        model_id="tenant-a-malformed",
        model_digest="6" * 64,
        update_kind="adapter",
        source_update_digest="7" * 64,
        consent_scope="tenant-training-opt-in-v1",
        portable=True,
        portability_manifest_digest="8" * 64,
    )
    fork_decision = ledger.create_tenant_fork(malformed_fork)

    assert fork_decision.status == "quarantined"
    assert fork_decision.reasons == (
        "fork_id_missing",
        "parent_fork_id_invalid",
        "parent_fork_missing",
    )
    assert ledger.export_bundle() == before

    malformed_proposal = MergeProposal(
        proposal_id=["not-a-string"],
        source_fork_id=["tenant-a-fork-001"],
        target_shared_fork_id="shared-root",
        candidate_model_id=["malformed-model"],
        candidate_model_digest="9" * 64,
        source_update_digest="4" * 64,
        merge_consent_scope="shared-model-merge-opt-in-v1",
        review_status="reviewed",
        review_digest="a" * 64,
    )
    proposal_decision = ledger.propose_merge(malformed_proposal)

    assert proposal_decision.status == "quarantined"
    assert proposal_decision.reasons == (
        "candidate_model_id_missing",
        "merge_source_missing",
        "proposal_id_missing",
    )
    assert ledger.export_bundle() == before


def test_malformed_merge_acceptance_and_rollback_inputs_quarantine_without_mutation() -> None:
    ledger = ForkLedger(_root())
    assert ledger.create_tenant_fork(_tenant_fork()).status == "accepted"
    proposal = MergeProposal(
        proposal_id="merge-malformed-inputs",
        source_fork_id="tenant-a-fork-001",
        target_shared_fork_id="shared-root",
        candidate_model_id="merged-malformed-inputs",
        candidate_model_digest="9" * 64,
        source_update_digest="4" * 64,
        merge_consent_scope="shared-model-merge-opt-in-v1",
        review_status="reviewed",
        review_digest="a" * 64,
    )
    assert ledger.propose_merge(proposal).status == "merge_eligible"
    before = ledger.export_bundle()

    malformed_merge = ForkNode(
        fork_id=["not-a-string"],
        scope_kind="shared",
        scope_id="global",
        parent_fork_id="shared-root",
        model_id="merged-malformed-inputs",
        model_digest="9" * 64,
        update_kind="adapter",
        source_update_digest="4" * 64,
        consent_scope="shared-model-merge-opt-in-v1",
        portable=True,
        portability_manifest_digest="b" * 64,
    )
    merge_decision = ledger.accept_merge("merge-malformed-inputs", malformed_merge)

    assert merge_decision.status == "quarantined"
    assert merge_decision.reasons == ("fork_id_missing",)
    assert ledger.export_bundle() == before

    rollback_decision = ledger.rollback(
        "tenant", "tenant-a", ["tenant-a-fork-001"], "malformed-target"
    )

    assert rollback_decision.status == "quarantined"
    assert rollback_decision.reasons == ("rollback_target_missing",)
    assert ledger.export_bundle() == before


def test_lookup_rejects_unhashable_identifiers_with_typed_errors() -> None:
    ledger = ForkLedger(_root())

    with pytest.raises(ForkTopologyError, match="scope_invalid"):
        ledger.head([], "global")
    with pytest.raises(ForkTopologyError, match="fork_id_invalid"):
        ledger.fork([])


def test_malformed_policy_is_rejected_before_ledger_creation() -> None:
    with pytest.raises(ForkTopologyError, match="policy_invalid"):
        ForkLedger(_root(), ForkTopologyPolicy(allowed_update_kinds=None))


def test_tenant_cannot_branch_from_a_stale_shared_parent_after_learning() -> None:
    ledger = ForkLedger(_root())
    assert ledger.create_tenant_fork(_tenant_fork()).status == "accepted"
    stale = ForkNode(
        fork_id="tenant-a-fork-stale",
        scope_kind="tenant",
        scope_id="tenant-a",
        parent_fork_id="shared-root",
        model_id="tenant-a-model-stale",
        model_digest="6" * 64,
        update_kind="adapter",
        source_update_digest="7" * 64,
        consent_scope="tenant-training-opt-in-v1",
        portable=True,
        portability_manifest_digest="8" * 64,
    )

    decision = ledger.create_tenant_fork(stale)

    assert decision.status == "quarantined"
    assert decision.reasons == ("tenant_parent_head_mismatch",)


def test_stale_tenant_fork_cannot_propose_a_shared_merge() -> None:
    ledger = ForkLedger(_root())
    assert ledger.create_tenant_fork(_tenant_fork()).status == "accepted"
    current = ForkNode(
        fork_id="tenant-a-fork-current",
        scope_kind="tenant",
        scope_id="tenant-a",
        parent_fork_id="tenant-a-fork-001",
        model_id="tenant-a-model-current",
        model_digest="6" * 64,
        update_kind="adapter",
        source_update_digest="7" * 64,
        consent_scope="tenant-training-opt-in-v1",
        portable=True,
        portability_manifest_digest="8" * 64,
    )
    assert ledger.create_tenant_fork(current).status == "accepted"
    stale_proposal = MergeProposal(
        proposal_id="merge-stale",
        source_fork_id="tenant-a-fork-001",
        target_shared_fork_id="shared-root",
        candidate_model_id="merged-stale",
        candidate_model_digest="9" * 64,
        source_update_digest="4" * 64,
        merge_consent_scope="shared-model-merge-opt-in-v1",
        review_status="reviewed",
        review_digest="a" * 64,
    )

    decision = ledger.propose_merge(stale_proposal)

    assert decision.status == "quarantined"
    assert decision.reasons == ("merge_source_head_mismatch",)


def test_unknown_update_kind_is_quarantined_without_creating_a_fork() -> None:
    ledger = ForkLedger(_root())
    before = ledger.export_bundle()
    unknown_kind = ForkNode(
        fork_id="tenant-a-fork-unknown-kind",
        scope_kind="tenant",
        scope_id="tenant-a",
        parent_fork_id="shared-root",
        model_id="tenant-a-model-unknown-kind",
        model_digest="6" * 64,
        update_kind="online-gradient-magic",
        source_update_digest="7" * 64,
        consent_scope="tenant-training-opt-in-v1",
        portable=True,
        portability_manifest_digest="8" * 64,
    )

    decision = ledger.create_tenant_fork(unknown_kind)

    assert decision.status == "quarantined"
    assert decision.reasons == ("update_kind_not_allowed",)
    assert ledger.export_bundle() == before


def test_portable_manifest_exports_lineage_without_weights_or_provider_lock() -> None:
    ledger = ForkLedger(_root())
    assert ledger.create_tenant_fork(_tenant_fork()).status == "accepted"

    manifest = ledger.export_portable_manifest("tenant-a-fork-001")

    validate_portable_manifest(manifest)
    assert manifest["weights_included"] is False
    assert manifest["provider_lock_included"] is False
    assert [node["fork_id"] for node in manifest["lineage"]] == [
        "shared-root",
        "tenant-a-fork-001",
    ]


def test_portable_manifest_rejects_resealed_weight_or_provider_lock_flags() -> None:
    ledger = ForkLedger(_root())
    assert ledger.create_tenant_fork(_tenant_fork()).status == "accepted"
    manifest = dict(ledger.export_portable_manifest("tenant-a-fork-001"))
    manifest["weights_included"] = True
    unsigned = {key: value for key, value in manifest.items() if key != "export_sha256"}
    manifest["export_sha256"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    with pytest.raises(ForkTopologyError, match="portable_manifest_contains_weights"):
        validate_portable_manifest(manifest)


def test_fork_topology_module_has_no_execution_network_or_weight_loading_surface() -> None:
    source = Path("experiments/continual_learning/fork_topology.py").read_text()

    for forbidden in (
        "subprocess",
        "socket",
        "requests.",
        "urllib.",
        "model.generate",
        "model.train",
        "load_weights",
    ):
        assert forbidden not in source
