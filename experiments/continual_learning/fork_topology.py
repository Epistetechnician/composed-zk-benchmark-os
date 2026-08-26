"""Digest-only fork topology for a continual-learning update lane.

This module records model and adapter lineage without storing weights or
executing a learner. It gives future training and serving adapters a small
stateful seam for tenant isolation, shared-model lineage, portability, and
non-destructive rollback. The current implementation grants no runtime or
deployment authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass


STATE_SLICE = "continual-learning-fork-topology-v1"
CLAIM_CEILING = "LocalDevelopmentForkTopologyContract"
ROOT_CONSENT_SCOPE = "not-applicable-v1"
GENESIS_EVENT_DIGEST = "0" * 64
PORTABLE_EXPORT_FORMAT = "metadata-only-fork-manifest-v1"
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ForkNode:
    fork_id: str
    scope_kind: str
    scope_id: str
    parent_fork_id: str | None
    model_id: str
    model_digest: str
    update_kind: str
    source_update_digest: str | None
    consent_scope: str
    portable: bool
    portability_manifest_digest: str | None

    def payload(self) -> dict[str, object]:
        return asdict(self)

    def manifest_digest(self) -> str:
        return _canonical_digest(self.payload())


@dataclass(frozen=True)
class ForkDecision:
    status: str
    reasons: tuple[str, ...]
    fork_id: str | None = None


@dataclass(frozen=True)
class MergeProposal:
    proposal_id: str
    source_fork_id: str
    target_shared_fork_id: str
    candidate_model_id: str
    candidate_model_digest: str
    source_update_digest: str
    merge_consent_scope: str
    review_status: str
    review_digest: str

    def payload(self) -> dict[str, object]:
        return asdict(self)

    def manifest_digest(self) -> str:
        return _canonical_digest(self.payload())


@dataclass(frozen=True)
class ForkTopologyPolicy:
    tenant_consent_scope: str = "tenant-training-opt-in-v1"
    merge_consent_scope: str = "shared-model-merge-opt-in-v1"
    required_review_status: str = "reviewed"
    allowed_update_kinds: tuple[str, ...] = ("adapter", "full_weights")

    def payload(self) -> dict[str, object]:
        return {
            "tenant_consent_scope": self.tenant_consent_scope,
            "merge_consent_scope": self.merge_consent_scope,
            "required_review_status": self.required_review_status,
            "allowed_update_kinds": list(self.allowed_update_kinds),
        }


@dataclass(frozen=True)
class TopologyEvent:
    sequence: int
    kind: str
    scope_kind: str
    scope_id: str
    fork_id: str
    reason: str | None
    previous_event_digest: str
    event_digest: str

    def payload(self) -> dict[str, object]:
        return asdict(self)


class ForkTopologyError(ValueError):
    """Raised when a topology bundle cannot pass deterministic readback."""


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _valid_digest(value: str | None) -> bool:
    return isinstance(value, str) and bool(_DIGEST_RE.fullmatch(value))


def _scope_key(scope_kind: str, scope_id: str) -> str:
    return f"{scope_kind}:{scope_id}"


def _node_reasons(node: ForkNode, *, root: bool = False) -> set[str]:
    reasons: set[str] = set()
    if not isinstance(node.fork_id, str) or not node.fork_id.strip():
        reasons.add("fork_id_missing")
    if not isinstance(node.scope_kind, str) or not isinstance(node.scope_id, str):
        reasons.add("scope_invalid")
    elif not node.scope_kind.strip() or not node.scope_id.strip():
        reasons.add("scope_missing")
    if not isinstance(node.model_id, str) or not node.model_id.strip():
        reasons.add("model_id_missing")
    if not _valid_digest(node.model_digest):
        reasons.add("model_digest_invalid")
    if not isinstance(node.update_kind, str) or not node.update_kind.strip():
        reasons.add("update_kind_missing")
    if not isinstance(node.consent_scope, str) or not node.consent_scope.strip():
        reasons.add("consent_scope_missing")
    if node.parent_fork_id is not None and not isinstance(node.parent_fork_id, str):
        reasons.add("parent_fork_id_invalid")
    if not isinstance(node.portable, bool):
        reasons.add("portable_invalid")
    if not node.portable:
        reasons.add("fork_not_portable")
    if not _valid_digest(node.portability_manifest_digest):
        reasons.add("portability_manifest_invalid")
    if root:
        if node.scope_kind != "shared":
            reasons.add("root_scope_invalid")
        if node.parent_fork_id is not None:
            reasons.add("root_parent_invalid")
        if node.update_kind != "base":
            reasons.add("root_update_kind_invalid")
        if node.source_update_digest is not None:
            reasons.add("root_source_update_invalid")
        if node.consent_scope != ROOT_CONSENT_SCOPE:
            reasons.add("root_consent_scope_invalid")
    return reasons


def _event_digest(event: TopologyEvent) -> str:
    unsigned = {
        key: value for key, value in event.payload().items() if key != "event_digest"
    }
    return _canonical_digest(unsigned)


class ForkLedger:
    """Append-only local topology ledger with mutable scope heads."""

    def __init__(
        self, root: ForkNode, policy: ForkTopologyPolicy = ForkTopologyPolicy()
    ) -> None:
        if (
            not isinstance(policy.tenant_consent_scope, str)
            or not policy.tenant_consent_scope.strip()
            or not isinstance(policy.merge_consent_scope, str)
            or not policy.merge_consent_scope.strip()
            or not isinstance(policy.required_review_status, str)
            or not policy.required_review_status.strip()
            or not isinstance(policy.allowed_update_kinds, tuple)
            or not policy.allowed_update_kinds
            or any(
                not isinstance(kind, str) or not kind.strip()
                for kind in policy.allowed_update_kinds
            )
        ):
            raise ForkTopologyError("policy_invalid")
        reasons = _node_reasons(root, root=True)
        if reasons:
            raise ForkTopologyError("root_invalid:" + ",".join(sorted(reasons)))
        self._forks: dict[str, ForkNode] = {root.fork_id: root}
        self._policy = policy
        self._heads: dict[str, str] = {
            _scope_key(root.scope_kind, root.scope_id): root.fork_id
        }
        self._events: list[TopologyEvent] = []
        self._proposals: dict[str, MergeProposal] = {}
        self._accepted_proposals: set[str] = set()
        self._append_event("root_created", root, None)

    def head(self, scope_kind: str, scope_id: str) -> ForkNode:
        if not isinstance(scope_kind, str) or not isinstance(scope_id, str):
            raise ForkTopologyError("scope_invalid")
        try:
            return self._forks[self._heads[_scope_key(scope_kind, scope_id)]]
        except KeyError as exc:
            raise ForkTopologyError("scope_head_missing") from exc

    def fork(self, fork_id: str) -> ForkNode:
        if not isinstance(fork_id, str):
            raise ForkTopologyError("fork_id_invalid")
        try:
            return self._forks[fork_id]
        except KeyError as exc:
            raise ForkTopologyError("fork_missing") from exc

    def export_portable_manifest(self, fork_id: str) -> dict[str, object]:
        node = self.fork(fork_id)
        lineage = list(reversed(self._lineage(fork_id)))
        unsigned = {
            "state_slice": STATE_SLICE,
            "claim_ceiling": CLAIM_CEILING,
            "export_format": PORTABLE_EXPORT_FORMAT,
            "fork_id": fork_id,
            "portability_manifest_digest": node.portability_manifest_digest,
            "weights_included": False,
            "provider_lock_included": False,
            "lineage": [item.payload() for item in lineage],
        }
        return {**unsigned, "export_sha256": _canonical_digest(unsigned)}

    def _lineage(self, fork_id: str) -> list[ForkNode]:
        lineage: list[ForkNode] = []
        visited: set[str] = set()
        current = self.fork(fork_id)
        while current.fork_id not in visited:
            lineage.append(current)
            visited.add(current.fork_id)
            if current.parent_fork_id is None:
                return lineage
            current = self.fork(current.parent_fork_id)
        raise ForkTopologyError("lineage_cycle")

    def create_tenant_fork(self, node: ForkNode) -> ForkDecision:
        reasons = _node_reasons(node)
        if node.scope_kind != "tenant":
            reasons.add("tenant_fork_scope_invalid")
        if node.update_kind not in self._policy.allowed_update_kinds:
            reasons.add("update_kind_not_allowed")
        if node.source_update_digest is None or not _valid_digest(node.source_update_digest):
            reasons.add("source_update_digest_invalid")
        if node.consent_scope != self._policy.tenant_consent_scope:
            reasons.add("tenant_consent_scope_invalid")
        if isinstance(node.fork_id, str) and node.fork_id in self._forks:
            reasons.add("fork_id_duplicate")
        parent = (
            self._forks.get(node.parent_fork_id)
            if isinstance(node.parent_fork_id, str)
            else None
        )
        if parent is None:
            reasons.add("parent_fork_missing")
        else:
            if parent.scope_kind == "tenant" and parent.scope_id != node.scope_id:
                reasons.add("cross_tenant_parent")
            if parent.scope_kind not in ("shared", "tenant"):
                reasons.add("parent_scope_invalid")
            if parent.model_digest == node.model_digest:
                reasons.add("model_digest_unchanged")
            if parent.scope_kind == "shared":
                if self._heads.get(_scope_key("shared", parent.scope_id)) != parent.fork_id:
                    reasons.add("shared_parent_head_mismatch")
                tenant_head = self._heads.get(_scope_key("tenant", node.scope_id))
                if tenant_head is not None and tenant_head != parent.fork_id:
                    reasons.add("tenant_parent_head_mismatch")
            elif self._heads.get(_scope_key("tenant", parent.scope_id)) != parent.fork_id:
                reasons.add("tenant_parent_head_mismatch")
        if reasons:
            return ForkDecision("quarantined", tuple(sorted(reasons)), node.fork_id)

        self._forks[node.fork_id] = node
        self._heads[_scope_key(node.scope_kind, node.scope_id)] = node.fork_id
        self._append_event("fork_created", node, None)
        return ForkDecision("accepted", (), node.fork_id)

    def propose_merge(self, proposal: MergeProposal) -> ForkDecision:
        reasons: set[str] = set()
        if not isinstance(proposal.proposal_id, str) or not proposal.proposal_id.strip():
            reasons.add("proposal_id_missing")
        if (
            isinstance(proposal.proposal_id, str)
            and proposal.proposal_id in self._proposals
        ):
            reasons.add("proposal_id_duplicate")
        source = (
            self._forks.get(proposal.source_fork_id)
            if isinstance(proposal.source_fork_id, str)
            else None
        )
        target = (
            self._forks.get(proposal.target_shared_fork_id)
            if isinstance(proposal.target_shared_fork_id, str)
            else None
        )
        if source is None:
            reasons.add("merge_source_missing")
        if target is None:
            reasons.add("merge_target_missing")
        if source is not None and source.scope_kind != "tenant":
            reasons.add("merge_source_not_tenant")
        if source is not None and source.scope_kind == "tenant" and self._heads.get(
            _scope_key(source.scope_kind, source.scope_id)
        ) != source.fork_id:
            reasons.add("merge_source_head_mismatch")
        if target is not None and target.scope_kind != "shared":
            reasons.add("merge_target_not_shared")
        if target is not None and self._heads.get(
            _scope_key(target.scope_kind, target.scope_id)
        ) != target.fork_id:
            reasons.add("merge_target_head_mismatch")
        if (
            not isinstance(proposal.candidate_model_id, str)
            or not proposal.candidate_model_id.strip()
        ):
            reasons.add("candidate_model_id_missing")
        if not _valid_digest(proposal.candidate_model_digest):
            reasons.add("candidate_model_digest_invalid")
        if target is not None and proposal.candidate_model_digest == target.model_digest:
            reasons.add("candidate_model_digest_unchanged")
        if not _valid_digest(proposal.source_update_digest):
            reasons.add("source_update_digest_invalid")
        if source is not None and proposal.source_update_digest != source.source_update_digest:
            reasons.add("source_update_binding_mismatch")
        if proposal.merge_consent_scope != self._policy.merge_consent_scope:
            reasons.add("merge_consent_scope_invalid")
        if proposal.review_status != self._policy.required_review_status:
            reasons.add("merge_review_missing")
        if not _valid_digest(proposal.review_digest):
            reasons.add("merge_review_digest_invalid")
        if reasons:
            return ForkDecision("quarantined", tuple(sorted(reasons)))

        self._proposals[proposal.proposal_id] = proposal
        self._append_event("merge_proposed", source, proposal.proposal_id)
        return ForkDecision("merge_eligible", ())

    def accept_merge(self, proposal_id: str, node: ForkNode) -> ForkDecision:
        reasons: set[str] = set()
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            reasons.add("merge_proposal_missing")
        elif proposal_id in self._accepted_proposals:
            reasons.add("merge_proposal_already_accepted")
        reasons.update(_node_reasons(node))
        if node.scope_kind != "shared":
            reasons.add("merge_result_scope_invalid")
        if node.update_kind not in self._policy.allowed_update_kinds:
            reasons.add("update_kind_not_allowed")
        if isinstance(node.fork_id, str) and node.fork_id in self._forks:
            reasons.add("fork_id_duplicate")
        target = (
            self._forks.get(node.parent_fork_id)
            if isinstance(node.parent_fork_id, str)
            else None
        )
        if target is None:
            reasons.add("merge_result_parent_missing")
        elif target.scope_kind != "shared":
            reasons.add("merge_result_parent_not_shared")
        elif self._heads.get(_scope_key(target.scope_kind, target.scope_id)) != target.fork_id:
            reasons.add("merge_result_parent_head_mismatch")
        if proposal is not None:
            if node.parent_fork_id != proposal.target_shared_fork_id:
                reasons.add("merge_result_target_mismatch")
            if node.model_id != proposal.candidate_model_id:
                reasons.add("merge_result_model_id_mismatch")
            if node.model_digest != proposal.candidate_model_digest:
                reasons.add("merge_result_model_digest_mismatch")
            if node.source_update_digest != proposal.source_update_digest:
                reasons.add("merge_result_source_binding_mismatch")
            if node.consent_scope != proposal.merge_consent_scope:
                reasons.add("merge_result_consent_scope_mismatch")
        if reasons:
            return ForkDecision("quarantined", tuple(sorted(reasons)), node.fork_id)

        self._forks[node.fork_id] = node
        self._heads[_scope_key(node.scope_kind, node.scope_id)] = node.fork_id
        self._accepted_proposals.add(proposal_id)
        self._append_event("merge_accepted", node, proposal_id)
        return ForkDecision("accepted", (), node.fork_id)

    def rollback(
        self, scope_kind: str, scope_id: str, target_fork_id: str, reason: str
    ) -> ForkDecision:
        reasons: set[str] = set()
        if (
            not isinstance(scope_kind, str)
            or not isinstance(scope_id, str)
            or not scope_kind.strip()
            or not scope_id.strip()
        ):
            reasons.add("rollback_scope_missing")
        if not isinstance(reason, str) or not reason.strip():
            reasons.add("rollback_reason_missing")
        scope_key = _scope_key(scope_kind, scope_id)
        current_fork_id = self._heads.get(scope_key)
        target = (
            self._forks.get(target_fork_id)
            if isinstance(target_fork_id, str)
            else None
        )
        if current_fork_id is None:
            reasons.add("rollback_scope_head_missing")
        if target is None:
            reasons.add("rollback_target_missing")
        elif _scope_key(target.scope_kind, target.scope_id) != scope_key:
            reasons.add("rollback_target_scope_mismatch")
        elif target_fork_id == current_fork_id:
            reasons.add("rollback_target_current")
        elif current_fork_id is not None and not self._is_ancestor(
            target_fork_id, current_fork_id
        ):
            reasons.add("rollback_target_not_ancestor")
        if reasons:
            return ForkDecision("quarantined", tuple(sorted(reasons)), target_fork_id)

        self._heads[scope_key] = target_fork_id
        self._append_event("rollback", target, reason)
        return ForkDecision("rolled_back", (), target_fork_id)

    def _is_ancestor(self, target_fork_id: str, descendant_fork_id: str) -> bool:
        current = self._forks.get(descendant_fork_id)
        visited: set[str] = set()
        while current is not None and current.fork_id not in visited:
            if current.fork_id == target_fork_id:
                return True
            visited.add(current.fork_id)
            current = self._forks.get(current.parent_fork_id or "")
        return False

    def _append_event(
        self, kind: str, node: ForkNode, reason: str | None
    ) -> None:
        previous = self._events[-1].event_digest if self._events else GENESIS_EVENT_DIGEST
        unsigned = TopologyEvent(
            sequence=len(self._events),
            kind=kind,
            scope_kind=node.scope_kind,
            scope_id=node.scope_id,
            fork_id=node.fork_id,
            reason=reason,
            previous_event_digest=previous,
            event_digest="0" * 64,
        )
        self._events.append(
            TopologyEvent(
                **{
                    **unsigned.payload(),
                    "event_digest": _event_digest(unsigned),
                }
            )
        )

    def export_bundle(self) -> dict[str, object]:
        unsigned = {
            "state_slice": STATE_SLICE,
            "claim_ceiling": CLAIM_CEILING,
            "policy": self._policy.payload(),
            "forks": [
                self._forks[fork_id].payload() for fork_id in sorted(self._forks)
            ],
            "heads": {
                key: self._heads[key] for key in sorted(self._heads)
            },
            "events": [event.payload() for event in self._events],
            "proposals": [
                self._proposals[proposal_id].payload()
                for proposal_id in sorted(self._proposals)
            ],
            "accepted_proposals": sorted(self._accepted_proposals),
        }
        return {**unsigned, "bundle_sha256": _canonical_digest(unsigned)}


def validate_topology_bundle(bundle: dict[str, object]) -> None:
    """Validate a topology bundle without loading or executing model state."""

    if bundle.get("state_slice") != STATE_SLICE:
        raise ForkTopologyError("state_slice_invalid")
    if bundle.get("claim_ceiling") != CLAIM_CEILING:
        raise ForkTopologyError("claim_ceiling_invalid")
    provided_digest = bundle.get("bundle_sha256")
    unsigned = {key: value for key, value in bundle.items() if key != "bundle_sha256"}
    if not _valid_digest(provided_digest) or provided_digest != _canonical_digest(unsigned):
        raise ForkTopologyError("bundle_digest_invalid")

    forks = bundle.get("forks")
    policy_payload = bundle.get("policy")
    heads = bundle.get("heads")
    events = bundle.get("events")
    proposals = bundle.get("proposals")
    accepted_proposals = bundle.get("accepted_proposals")
    if not isinstance(policy_payload, dict) or set(policy_payload) != {
        "tenant_consent_scope",
        "merge_consent_scope",
        "required_review_status",
        "allowed_update_kinds",
    }:
        raise ForkTopologyError("policy_invalid")
    allowed_update_kinds = policy_payload["allowed_update_kinds"]
    if any(
        not isinstance(policy_payload[key], str)
        for key in (
            "tenant_consent_scope",
            "merge_consent_scope",
            "required_review_status",
        )
    ) or not isinstance(allowed_update_kinds, list) or any(
        not isinstance(kind, str) for kind in allowed_update_kinds
    ):
        raise ForkTopologyError("policy_invalid")
    policy = ForkTopologyPolicy(
        tenant_consent_scope=policy_payload["tenant_consent_scope"],
        merge_consent_scope=policy_payload["merge_consent_scope"],
        required_review_status=policy_payload["required_review_status"],
        allowed_update_kinds=tuple(allowed_update_kinds),
    )
    if not isinstance(forks, list) or not forks:
        raise ForkTopologyError("forks_invalid")
    if not isinstance(heads, dict) or not heads:
        raise ForkTopologyError("heads_invalid")
    if not isinstance(events, list) or not events:
        raise ForkTopologyError("events_invalid")
    if not isinstance(proposals, list):
        raise ForkTopologyError("proposals_invalid")
    if not isinstance(accepted_proposals, list) or any(
        not isinstance(proposal_id, str) for proposal_id in accepted_proposals
    ):
        raise ForkTopologyError("accepted_proposals_invalid")

    fork_ids: set[str] = set()
    fork_map: dict[str, ForkNode] = {}
    root_ids: list[str] = []
    for payload in forks:
        if not isinstance(payload, dict):
            raise ForkTopologyError("fork_shape_invalid")
        if set(payload) != {
            "fork_id",
            "scope_kind",
            "scope_id",
            "parent_fork_id",
            "model_id",
            "model_digest",
            "update_kind",
            "source_update_digest",
            "consent_scope",
            "portable",
            "portability_manifest_digest",
        }:
            raise ForkTopologyError("fork_shape_invalid")
        fork = ForkNode(**payload)
        reasons = _node_reasons(fork, root=fork.parent_fork_id is None)
        if reasons:
            raise ForkTopologyError("fork_invalid:" + ",".join(sorted(reasons)))
        if fork.parent_fork_id is not None:
            if fork.update_kind not in policy.allowed_update_kinds:
                raise ForkTopologyError("update_kind_not_allowed")
            if not _valid_digest(fork.source_update_digest):
                raise ForkTopologyError("source_update_digest_invalid")
            if fork.scope_kind == "tenant" and fork.consent_scope != policy.tenant_consent_scope:
                raise ForkTopologyError("tenant_consent_scope_invalid")
            if fork.scope_kind == "shared" and fork.consent_scope != policy.merge_consent_scope:
                raise ForkTopologyError("merge_consent_scope_invalid")
        if fork.fork_id in fork_ids:
            raise ForkTopologyError("fork_id_duplicate")
        fork_ids.add(fork.fork_id)
        fork_map[fork.fork_id] = fork
        if fork.parent_fork_id is None:
            root_ids.append(fork.fork_id)
    if len(root_ids) != 1:
        raise ForkTopologyError("root_cardinality_invalid")
    for fork in fork_map.values():
        if fork.parent_fork_id is None:
            continue
        parent = fork_map.get(fork.parent_fork_id)
        if parent is None:
            raise ForkTopologyError("parent_fork_missing")
        if parent.scope_kind == "tenant" and (
            fork.scope_kind != "tenant" or fork.scope_id != parent.scope_id
        ):
            raise ForkTopologyError("parent_scope_invalid")
        if parent.scope_kind == "shared" and fork.scope_kind not in (
            "shared",
            "tenant",
        ):
            raise ForkTopologyError("parent_scope_invalid")

    proposal_ids: set[str] = set()
    proposal_map: dict[str, MergeProposal] = {}
    for payload in proposals:
        if not isinstance(payload, dict):
            raise ForkTopologyError("proposal_shape_invalid")
        try:
            proposal = MergeProposal(**payload)
        except TypeError as exc:
            raise ForkTopologyError("proposal_shape_invalid") from exc
        if not isinstance(proposal.proposal_id, str):
            raise ForkTopologyError("proposal_id_invalid")
        if proposal.proposal_id in proposal_ids:
            raise ForkTopologyError("proposal_id_duplicate")
        if not proposal.proposal_id.strip():
            raise ForkTopologyError("proposal_id_missing")
        if not isinstance(proposal.source_fork_id, str):
            raise ForkTopologyError("proposal_source_invalid")
        if not isinstance(proposal.target_shared_fork_id, str):
            raise ForkTopologyError("proposal_target_invalid")
        if proposal.source_fork_id not in fork_ids:
            raise ForkTopologyError("proposal_source_missing")
        if proposal.target_shared_fork_id not in fork_ids:
            raise ForkTopologyError("proposal_target_missing")
        source = fork_map[proposal.source_fork_id]
        target = fork_map[proposal.target_shared_fork_id]
        if source.scope_kind != "tenant":
            raise ForkTopologyError("proposal_source_scope_invalid")
        if target.scope_kind != "shared":
            raise ForkTopologyError("proposal_target_scope_invalid")
        if (
            not isinstance(proposal.candidate_model_id, str)
            or not proposal.candidate_model_id.strip()
        ):
            raise ForkTopologyError("proposal_candidate_model_invalid")
        if not _valid_digest(proposal.candidate_model_digest):
            raise ForkTopologyError("proposal_candidate_digest_invalid")
        if proposal.candidate_model_digest == target.model_digest:
            raise ForkTopologyError("proposal_candidate_digest_unchanged")
        if not _valid_digest(proposal.source_update_digest):
            raise ForkTopologyError("proposal_source_digest_invalid")
        if proposal.source_update_digest != source.source_update_digest:
            raise ForkTopologyError("proposal_source_binding_invalid")
        if not _valid_digest(proposal.review_digest):
            raise ForkTopologyError("proposal_review_digest_invalid")
        if proposal.merge_consent_scope != policy.merge_consent_scope:
            raise ForkTopologyError("proposal_merge_consent_invalid")
        if proposal.review_status != policy.required_review_status:
            raise ForkTopologyError("proposal_review_invalid")
        proposal_ids.add(proposal.proposal_id)
        proposal_map[proposal.proposal_id] = proposal
    if any(proposal_id not in proposal_ids for proposal_id in accepted_proposals):
        raise ForkTopologyError("accepted_proposal_missing")
    if len(set(accepted_proposals)) != len(accepted_proposals):
        raise ForkTopologyError("accepted_proposals_duplicate")

    previous = GENESIS_EVENT_DIGEST
    expected_heads: dict[str, str] = {}
    proposed_event_ids: set[str] = set()
    accepted_event_ids: set[str] = set()
    allowed_event_kinds = {
        "root_created",
        "fork_created",
        "merge_proposed",
        "merge_accepted",
        "rollback",
    }
    for expected_sequence, payload in enumerate(events):
        if not isinstance(payload, dict):
            raise ForkTopologyError("event_shape_invalid")
        try:
            event = TopologyEvent(**payload)
        except TypeError as exc:
            raise ForkTopologyError("event_shape_invalid") from exc
        if not isinstance(event.kind, str):
            raise ForkTopologyError("event_kind_invalid")
        if not isinstance(event.fork_id, str):
            raise ForkTopologyError("event_fork_invalid")
        if not isinstance(event.scope_kind, str) or not isinstance(event.scope_id, str):
            raise ForkTopologyError("event_scope_invalid")
        if event.reason is not None and not isinstance(event.reason, str):
            raise ForkTopologyError("event_reason_invalid")
        if event.sequence != expected_sequence:
            raise ForkTopologyError("event_sequence_invalid")
        if event.kind not in allowed_event_kinds:
            raise ForkTopologyError("event_kind_invalid")
        if event.previous_event_digest != previous:
            raise ForkTopologyError("event_chain_invalid")
        if event.fork_id not in fork_ids:
            raise ForkTopologyError("event_fork_missing")
        fork = fork_map[event.fork_id]
        if event.scope_kind != fork.scope_kind or event.scope_id != fork.scope_id:
            raise ForkTopologyError("event_scope_invalid")
        if event.kind == "root_created":
            if expected_sequence != 0 or event.fork_id != root_ids[0]:
                raise ForkTopologyError("root_event_invalid")
            expected_heads[_scope_key(fork.scope_kind, fork.scope_id)] = fork.fork_id
        elif event.kind == "fork_created":
            expected_heads[_scope_key(fork.scope_kind, fork.scope_id)] = fork.fork_id
        elif event.kind == "merge_proposed":
            if event.reason not in proposal_map:
                raise ForkTopologyError("event_proposal_missing")
            if event.reason in proposed_event_ids:
                raise ForkTopologyError("event_proposal_duplicate")
            proposal = proposal_map[event.reason]
            if event.fork_id != proposal.source_fork_id:
                raise ForkTopologyError("event_proposal_source_mismatch")
            proposed_event_ids.add(event.reason)
        elif event.kind == "merge_accepted":
            if event.reason not in proposal_map:
                raise ForkTopologyError("event_proposal_missing")
            if event.reason in accepted_event_ids:
                raise ForkTopologyError("event_proposal_duplicate")
            proposal = proposal_map[event.reason]
            if fork.scope_kind != "shared":
                raise ForkTopologyError("event_merge_result_scope_invalid")
            if fork.parent_fork_id != proposal.target_shared_fork_id:
                raise ForkTopologyError("event_merge_result_target_mismatch")
            if fork.model_id != proposal.candidate_model_id:
                raise ForkTopologyError("event_merge_result_model_id_mismatch")
            if fork.model_digest != proposal.candidate_model_digest:
                raise ForkTopologyError("event_merge_result_model_digest_mismatch")
            if fork.source_update_digest != proposal.source_update_digest:
                raise ForkTopologyError("event_merge_result_source_mismatch")
            if fork.consent_scope != proposal.merge_consent_scope:
                raise ForkTopologyError("event_merge_result_consent_mismatch")
            accepted_event_ids.add(event.reason)
            expected_heads[_scope_key(fork.scope_kind, fork.scope_id)] = fork.fork_id
        elif event.kind == "rollback":
            expected_heads[_scope_key(fork.scope_kind, fork.scope_id)] = fork.fork_id
        if not _valid_digest(event.event_digest) or event.event_digest != _event_digest(event):
            raise ForkTopologyError("event_digest_invalid")
        previous = event.event_digest

    if proposed_event_ids != proposal_ids:
        raise ForkTopologyError("proposal_event_state_invalid")
    if accepted_event_ids != set(accepted_proposals):
        raise ForkTopologyError("accepted_proposal_state_invalid")

    if set(heads) != set(expected_heads):
        raise ForkTopologyError("head_state_invalid")
    for scope_key, fork_id in heads.items():
        if not isinstance(scope_key, str) or not isinstance(fork_id, str):
            raise ForkTopologyError("head_shape_invalid")
        if fork_id not in fork_ids:
            raise ForkTopologyError("head_fork_missing")
        if expected_heads[scope_key] != fork_id:
            raise ForkTopologyError("head_state_invalid")


def validate_portable_manifest(manifest: dict[str, object]) -> None:
    """Validate a metadata-only fork export without accepting model weights."""

    required = {
        "state_slice",
        "claim_ceiling",
        "export_format",
        "fork_id",
        "portability_manifest_digest",
        "weights_included",
        "provider_lock_included",
        "lineage",
        "export_sha256",
    }
    if set(manifest) != required:
        raise ForkTopologyError("portable_manifest_shape_invalid")
    if manifest["state_slice"] != STATE_SLICE:
        raise ForkTopologyError("state_slice_invalid")
    if manifest["claim_ceiling"] != CLAIM_CEILING:
        raise ForkTopologyError("claim_ceiling_invalid")
    if manifest["export_format"] != PORTABLE_EXPORT_FORMAT:
        raise ForkTopologyError("portable_export_format_invalid")
    if manifest["weights_included"] is not False:
        raise ForkTopologyError("portable_manifest_contains_weights")
    if manifest["provider_lock_included"] is not False:
        raise ForkTopologyError("portable_manifest_contains_provider_lock")
    if not isinstance(manifest["fork_id"], str) or not manifest["fork_id"].strip():
        raise ForkTopologyError("portable_fork_id_invalid")
    if not _valid_digest(manifest["portability_manifest_digest"]):
        raise ForkTopologyError("portable_manifest_digest_invalid")
    lineage = manifest["lineage"]
    if not isinstance(lineage, list) or not lineage:
        raise ForkTopologyError("portable_lineage_invalid")
    provided_digest = manifest["export_sha256"]
    unsigned = {key: value for key, value in manifest.items() if key != "export_sha256"}
    if not _valid_digest(provided_digest) or provided_digest != _canonical_digest(unsigned):
        raise ForkTopologyError("portable_export_digest_invalid")

    nodes: list[ForkNode] = []
    for payload in lineage:
        if not isinstance(payload, dict):
            raise ForkTopologyError("portable_lineage_node_invalid")
        try:
            node = ForkNode(**payload)
        except TypeError as exc:
            raise ForkTopologyError("portable_lineage_node_invalid") from exc
        if _node_reasons(node, root=not nodes):
            raise ForkTopologyError("portable_lineage_node_invalid")
        if nodes and node.update_kind not in ("adapter", "full_weights"):
            raise ForkTopologyError("portable_lineage_update_kind_invalid")
        nodes.append(node)
    if nodes[-1].fork_id != manifest["fork_id"]:
        raise ForkTopologyError("portable_lineage_tip_invalid")
    if nodes[-1].portability_manifest_digest != manifest["portability_manifest_digest"]:
        raise ForkTopologyError("portable_manifest_binding_invalid")
    for parent, child in zip(nodes, nodes[1:]):
        if child.parent_fork_id != parent.fork_id:
            raise ForkTopologyError("portable_lineage_order_invalid")
        if parent.scope_kind == "tenant" and (
            child.scope_kind != "tenant" or child.scope_id != parent.scope_id
        ):
            raise ForkTopologyError("portable_lineage_scope_invalid")
        if parent.scope_kind == "shared" and child.scope_kind not in (
            "shared",
            "tenant",
        ):
            raise ForkTopologyError("portable_lineage_scope_invalid")
    if nodes[0].parent_fork_id is not None:
        raise ForkTopologyError("portable_lineage_root_invalid")
