"""Digest-only governance primitives for a continual-learning update lane.

This module records no model weights, executes no model, and grants no runtime
authority. It validates an update candidate before a future caller may place it
into a canary or promotion ledger.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, replace


STATE_SLICE = "continual-learning-update-governance-v1"
CLAIM_CEILING = "LocalDevelopmentUpdateGovernanceContract"
REQUIRED_CONSENT_SCOPE = "tenant-training-opt-in-v1"
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class SafetyReport:
    baseline_jailbreak_milli: int
    candidate_jailbreak_milli: int
    baseline_backdoor_milli: int
    candidate_backdoor_milli: int
    baseline_persona_drift_milli: int
    candidate_persona_drift_milli: int
    unknown_count: int


@dataclass(frozen=True)
class UtilityReport:
    baseline_utility_milli: int
    candidate_utility_milli: int


@dataclass(frozen=True)
class CanaryReport:
    sample_count: int
    failure_count: int
    unknown_count: int


@dataclass(frozen=True)
class UpdateCandidate:
    candidate_id: str
    tenant_id: str
    parent_model_id: str
    parent_model_digest: str
    candidate_model_id: str
    candidate_model_digest: str
    update_data_digest: str
    source_event_ids: tuple[str, ...]
    source_tenant_ids: tuple[str, ...]
    consent_scope: str
    safety: SafetyReport
    utility: UtilityReport
    canary: CanaryReport

    def manifest_payload(self) -> dict:
        return asdict(self)

    def manifest_digest(self) -> str:
        return _canonical_digest(self.manifest_payload())


@dataclass(frozen=True)
class GovernancePolicy:
    max_utility_regression_milli: int = 0
    max_canary_failure_rate_milli: int = 0


@dataclass(frozen=True)
class GovernanceDecision:
    status: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ModelSnapshot:
    model_id: str
    model_digest: str


@dataclass(frozen=True)
class LedgerEvent:
    sequence: int
    kind: str
    candidate_id: str | None
    candidate_manifest_digest: str | None
    model_id: str
    model_digest: str
    parent_model_digest: str | None
    reason: str | None
    previous_event_digest: str
    event_digest: str


class LedgerError(ValueError):
    """Raised when an update-ledger transition cannot proceed safely."""


def _valid_digest(value: str) -> bool:
    return bool(_DIGEST_RE.fullmatch(value))


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _metric_reasons(name: str, baseline: int, candidate: int) -> list[str]:
    reasons: list[str] = []
    if not 0 <= baseline <= 1000 or not 0 <= candidate <= 1000:
        reasons.append(f"{name}_metric_out_of_range")
    elif candidate > baseline:
        reasons.append(f"{name}_regression")
    return reasons


def evaluate_candidate(
    candidate: UpdateCandidate,
    policy: GovernancePolicy = GovernancePolicy(),
) -> GovernanceDecision:
    """Return a fail-closed admission decision for a digest-only candidate."""

    reasons: list[str] = []
    if not candidate.candidate_id.strip():
        reasons.append("candidate_id_missing")
    if not candidate.tenant_id.strip():
        reasons.append("tenant_id_missing")
    if not candidate.parent_model_id.strip():
        reasons.append("parent_model_id_missing")
    if not candidate.candidate_model_id.strip():
        reasons.append("candidate_model_id_missing")
    for name, value in (
        ("parent_model_digest", candidate.parent_model_digest),
        ("candidate_model_digest", candidate.candidate_model_digest),
        ("update_data_digest", candidate.update_data_digest),
    ):
        if not _valid_digest(value):
            reasons.append(f"{name}_invalid")
    if candidate.parent_model_digest == candidate.candidate_model_digest:
        reasons.append("candidate_model_equals_parent")
    if not candidate.source_event_ids:
        reasons.append("source_events_missing")
    if any(not event_id.strip() for event_id in candidate.source_event_ids):
        reasons.append("source_event_id_missing")
    if len(candidate.source_event_ids) != len(candidate.source_tenant_ids):
        reasons.append("source_tenant_binding_mismatch")
    if len(set(candidate.source_event_ids)) != len(candidate.source_event_ids):
        reasons.append("source_events_duplicate")
    if any(tenant_id != candidate.tenant_id for tenant_id in candidate.source_tenant_ids):
        reasons.append("cross_tenant_source")
    if candidate.consent_scope != REQUIRED_CONSENT_SCOPE:
        reasons.append("consent_scope_missing")

    reasons.extend(
        _metric_reasons(
            "jailbreak",
            candidate.safety.baseline_jailbreak_milli,
            candidate.safety.candidate_jailbreak_milli,
        )
    )
    reasons.extend(
        _metric_reasons(
            "backdoor",
            candidate.safety.baseline_backdoor_milli,
            candidate.safety.candidate_backdoor_milli,
        )
    )
    reasons.extend(
        _metric_reasons(
            "persona_drift",
            candidate.safety.baseline_persona_drift_milli,
            candidate.safety.candidate_persona_drift_milli,
        )
    )
    if candidate.safety.unknown_count != 0:
        reasons.append("safety_unknown")
    if not 0 <= candidate.utility.baseline_utility_milli <= 1000:
        reasons.append("baseline_utility_metric_out_of_range")
    if not 0 <= candidate.utility.candidate_utility_milli <= 1000:
        reasons.append("candidate_utility_metric_out_of_range")
    if (
        candidate.candidate_model_digest != candidate.parent_model_digest
        and candidate.utility.candidate_utility_milli
        + policy.max_utility_regression_milli
        < candidate.utility.baseline_utility_milli
    ):
        reasons.append("utility_regression")
    if candidate.canary.sample_count <= 0:
        reasons.append("canary_samples_missing")
    if not 0 <= candidate.canary.failure_count <= candidate.canary.sample_count:
        reasons.append("canary_failure_count_invalid")
    if candidate.canary.unknown_count != 0:
        reasons.append("canary_unknown")
    elif candidate.canary.sample_count > 0:
        failure_rate = (candidate.canary.failure_count * 1000) // candidate.canary.sample_count
        if failure_rate > policy.max_canary_failure_rate_milli:
            reasons.append("canary_failure_rate")

    return GovernanceDecision(
        status="canary_eligible" if not reasons else "quarantined",
        reasons=tuple(reasons),
    )


def _event_digest(event: LedgerEvent) -> str:
    unsigned = {
        "sequence": event.sequence,
        "kind": event.kind,
        "candidate_id": event.candidate_id,
        "candidate_manifest_digest": event.candidate_manifest_digest,
        "model_id": event.model_id,
        "model_digest": event.model_digest,
        "parent_model_digest": event.parent_model_digest,
        "reason": event.reason,
        "previous_event_digest": event.previous_event_digest,
    }
    return _canonical_digest(unsigned)


class UpdateLedger:
    """Append-only per-tenant update lifecycle with optimistic parent checks."""

    def __init__(self, tenant_id: str, initial_model_id: str, initial_model_digest: str):
        if not tenant_id.strip():
            raise LedgerError("tenant_id_missing")
        if not initial_model_id.strip():
            raise LedgerError("initial_model_id_missing")
        if not _valid_digest(initial_model_digest):
            raise LedgerError("initial_model_digest_invalid")
        self.tenant_id = tenant_id
        self._head = ModelSnapshot(initial_model_id, initial_model_digest)
        self._candidates: dict[str, UpdateCandidate] = {}
        self._candidate_status: dict[str, str] = {}
        self._snapshots: dict[str, ModelSnapshot] = {
            initial_model_digest: self._head,
        }
        baseline = LedgerEvent(
            sequence=0,
            kind="baseline",
            candidate_id=None,
            candidate_manifest_digest=None,
            model_id=initial_model_id,
            model_digest=initial_model_digest,
            parent_model_digest=None,
            reason=None,
            previous_event_digest="0" * 64,
            event_digest="0" * 64,
        )
        self._events: list[LedgerEvent] = [
            replace(baseline, event_digest=_event_digest(baseline))
        ]

    def head(self) -> ModelSnapshot:
        return self._head

    def events(self) -> tuple[LedgerEvent, ...]:
        return tuple(self._events)

    def submit(self, candidate: UpdateCandidate) -> GovernanceDecision:
        if candidate.candidate_id in self._candidates:
            raise LedgerError("candidate_id_duplicate")
        decision = evaluate_candidate(candidate)
        reasons = list(decision.reasons)
        if candidate.tenant_id != self.tenant_id:
            reasons.append("tenant_mismatch")
        if candidate.parent_model_digest != self._head.model_digest:
            reasons.append("parent_head_mismatch")
        status = "canary_eligible" if not reasons else "quarantined"
        decision = GovernanceDecision(status=status, reasons=tuple(reasons))
        self._candidates[candidate.candidate_id] = candidate
        self._candidate_status[candidate.candidate_id] = status
        self._append(
            kind=status,
            candidate_id=candidate.candidate_id,
            candidate_manifest_digest=candidate.manifest_digest(),
            model_id=candidate.candidate_model_id,
            model_digest=candidate.candidate_model_digest,
            parent_model_digest=candidate.parent_model_digest,
            reason=";".join(reasons) if reasons else None,
        )
        return decision

    def promote(self, candidate_id: str) -> LedgerEvent:
        candidate = self._candidates.get(candidate_id)
        if candidate is None:
            raise LedgerError("candidate_missing")
        if self._candidate_status.get(candidate_id) != "canary_eligible":
            raise LedgerError("candidate_not_canary_eligible")
        if candidate.parent_model_digest != self._head.model_digest:
            self._candidate_status[candidate_id] = "quarantined"
            self._append(
                kind="quarantined",
                candidate_id=candidate_id,
                candidate_manifest_digest=candidate.manifest_digest(),
                model_id=candidate.candidate_model_id,
                model_digest=candidate.candidate_model_digest,
                parent_model_digest=candidate.parent_model_digest,
                reason="parent_head_mismatch",
            )
            raise LedgerError("parent_head_mismatch")
        event = self._append(
            kind="promoted",
            candidate_id=candidate_id,
            candidate_manifest_digest=candidate.manifest_digest(),
            model_id=candidate.candidate_model_id,
            model_digest=candidate.candidate_model_digest,
            parent_model_digest=self._head.model_digest,
            reason=None,
        )
        self._head = ModelSnapshot(candidate.candidate_model_id, candidate.candidate_model_digest)
        self._snapshots[self._head.model_digest] = self._head
        self._candidate_status[candidate_id] = "promoted"
        return event

    def rollback(self, target_model_digest: str, reason: str) -> LedgerEvent:
        if not reason.strip():
            raise LedgerError("rollback_reason_missing")
        target = self._snapshots.get(target_model_digest)
        if target is None:
            raise LedgerError("rollback_target_unknown")
        if target.model_digest == self._head.model_digest:
            raise LedgerError("rollback_target_is_current")
        event = self._append(
            kind="rollback",
            candidate_id=None,
            candidate_manifest_digest=None,
            model_id=target.model_id,
            model_digest=target.model_digest,
            parent_model_digest=self._head.model_digest,
            reason=reason,
        )
        self._head = target
        return event

    def validate_chain(self) -> None:
        previous = "0" * 64
        for expected_sequence, event in enumerate(self._events):
            if event.sequence != expected_sequence:
                raise LedgerError("ledger_sequence_drift")
            if event.previous_event_digest != previous:
                raise LedgerError("ledger_previous_digest_drift")
            if event.event_digest != _event_digest(event):
                raise LedgerError("ledger_event_digest_drift")
            previous = event.event_digest

    def export_bundle(self) -> dict:
        unsigned = {
            "state_slice": STATE_SLICE,
            "claim_ceiling": CLAIM_CEILING,
            "tenant_id": self.tenant_id,
            "head": {
                "model_id": self._head.model_id,
                "model_digest": self._head.model_digest,
            },
            "events": [
                {
                    "sequence": event.sequence,
                    "kind": event.kind,
                    "candidate_id": event.candidate_id,
                    "candidate_manifest_digest": event.candidate_manifest_digest,
                    "model_id": event.model_id,
                    "model_digest": event.model_digest,
                    "parent_model_digest": event.parent_model_digest,
                    "reason": event.reason,
                    "previous_event_digest": event.previous_event_digest,
                    "event_digest": event.event_digest,
                }
                for event in self._events
            ],
        }
        return {**unsigned, "bundle_sha256": _canonical_digest(unsigned)}

    def _append(
        self,
        *,
        kind: str,
        candidate_id: str | None,
        candidate_manifest_digest: str | None,
        model_id: str,
        model_digest: str,
        parent_model_digest: str | None,
        reason: str | None,
    ) -> LedgerEvent:
        previous = self._events[-1].event_digest
        unsigned = LedgerEvent(
            sequence=len(self._events),
            kind=kind,
            candidate_id=candidate_id,
            candidate_manifest_digest=candidate_manifest_digest,
            model_id=model_id,
            model_digest=model_digest,
            parent_model_digest=parent_model_digest,
            reason=reason,
            previous_event_digest=previous,
            event_digest="0" * 64,
        )
        event = replace(unsigned, event_digest=_event_digest(unsigned))
        self._events.append(event)
        return event


def validate_bundle(bundle: dict) -> None:
    """Validate an exported bundle without executing or loading a model."""

    if bundle.get("state_slice") != STATE_SLICE:
        raise LedgerError("bundle_state_slice_mismatch")
    if bundle.get("claim_ceiling") != CLAIM_CEILING:
        raise LedgerError("bundle_claim_ceiling_mismatch")
    unsigned = {key: value for key, value in bundle.items() if key != "bundle_sha256"}
    if bundle.get("bundle_sha256") != _canonical_digest(unsigned):
        raise LedgerError("bundle_digest_mismatch")
    events = bundle.get("events")
    if not isinstance(events, list) or not events:
        raise LedgerError("bundle_events_missing")
    previous = "0" * 64
    expected_head: dict[str, str] | None = None
    for expected_sequence, payload in enumerate(events):
        try:
            event = LedgerEvent(**payload)
        except (TypeError, ValueError) as exc:
            raise LedgerError("bundle_event_shape_invalid") from exc
        if event.sequence != expected_sequence:
            raise LedgerError("bundle_sequence_drift")
        if event.previous_event_digest != previous:
            raise LedgerError("bundle_previous_digest_drift")
        if not _valid_digest(event.model_digest):
            raise LedgerError("bundle_model_digest_invalid")
        if event.parent_model_digest is not None and not _valid_digest(event.parent_model_digest):
            raise LedgerError("bundle_parent_model_digest_invalid")
        if event.candidate_manifest_digest is not None and not _valid_digest(event.candidate_manifest_digest):
            raise LedgerError("bundle_candidate_manifest_digest_invalid")
        if event.event_digest != _event_digest(event):
            raise LedgerError("bundle_event_digest_mismatch")
        if event.kind == "baseline":
            if expected_sequence != 0:
                raise LedgerError("bundle_baseline_position_invalid")
            expected_head = {
                "model_id": event.model_id,
                "model_digest": event.model_digest,
            }
        elif event.kind in ("promoted", "rollback"):
            if expected_head is None or event.parent_model_digest != expected_head["model_digest"]:
                raise LedgerError("bundle_transition_parent_mismatch")
            expected_head = {
                "model_id": event.model_id,
                "model_digest": event.model_digest,
            }
        elif event.kind not in ("canary_eligible", "quarantined"):
            raise LedgerError("bundle_event_kind_invalid")
        previous = event.event_digest
    head = bundle.get("head")
    if not isinstance(head, dict) or head != expected_head:
        raise LedgerError("bundle_head_mismatch")
