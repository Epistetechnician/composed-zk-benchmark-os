"""Digest-only source admission for a continual-learning update lane.

This module admits only structured, digest-bound source metadata. It stores no
raw feedback, verifies no actor or quality authority, executes no model, and
grants no update or deployment authority. Unknown or explicitly adverse
metadata is fail-closed before an update-data digest can feed V19 governance.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass


STATE_SLICE = "continual-learning-source-admission-v1"
CLAIM_CEILING = "LocalDevelopmentSourceAdmissionContract"
REQUIRED_CONSENT_SCOPE = "tenant-training-opt-in-v1"
ADMISSION_STATUSES = ("accepted", "quarantined", "unknown")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class SourceEvent:
    """A raw-event receipt containing no raw event content."""

    event_id: str
    tenant_id: str
    source_kind: str
    event_digest: str
    label_digest: str
    quality_status: str
    quality_receipt_digest: str | None
    consent_scope: str
    window_id: str
    conflict_group: str | None = None
    poisoning_marker: str | None = None


@dataclass(frozen=True)
class SourceAdmissionPolicy:
    tenant_id: str
    window_id: str
    required_consent_scope: str = REQUIRED_CONSENT_SCOPE
    allowed_source_kinds: tuple[str, ...] = (
        "declared_operator",
        "declared_user",
        "declared_model",
    )
    reject_poisoning_markers: bool = True


@dataclass(frozen=True)
class AdmittedSourceEvent:
    event_id: str
    event_digest: str
    label_digest: str
    quality_receipt_digest: str

    def payload(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class AdmittedUpdateData:
    tenant_id: str
    window_id: str
    source_events: tuple[AdmittedSourceEvent, ...]

    def manifest_payload(self) -> dict[str, object]:
        return {
            "state_slice": STATE_SLICE,
            "claim_ceiling": CLAIM_CEILING,
            "tenant_id": self.tenant_id,
            "window_id": self.window_id,
            "source_events": [event.payload() for event in self.source_events],
        }

    @property
    def update_data_digest(self) -> str:
        return _canonical_digest(self.manifest_payload())

    def payload(self) -> dict[str, object]:
        return {
            **self.manifest_payload(),
            "update_data_digest": self.update_data_digest,
        }


@dataclass(frozen=True)
class SourceAdmissionDecision:
    status: str
    reasons: tuple[str, ...]
    admitted_update_data: AdmittedUpdateData | None

    @property
    def update_data_digest(self) -> str | None:
        if self.admitted_update_data is None:
            return None
        return self.admitted_update_data.update_data_digest

    @property
    def admitted_event_ids(self) -> tuple[str, ...]:
        if self.admitted_update_data is None:
            return ()
        return tuple(event.event_id for event in self.admitted_update_data.source_events)


class SourceAdmissionError(ValueError):
    """Raised when a source-admission bundle fails deterministic readback."""


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _valid_digest(value: str | None) -> bool:
    return isinstance(value, str) and bool(_DIGEST_RE.fullmatch(value))


def _sorted_reasons(reasons: set[str]) -> tuple[str, ...]:
    return tuple(sorted(reasons))


def admit_source_events(
    events: tuple[SourceEvent, ...],
    policy: SourceAdmissionPolicy,
) -> SourceAdmissionDecision:
    """Return a deterministic fail-closed decision for one tenant/window."""

    if not events:
        return SourceAdmissionDecision("unknown", ("source_events_missing",), None)

    quarantine_reasons: set[str] = set()
    unknown_reasons: set[str] = set()
    event_ids = [event.event_id for event in events]
    event_digests = [event.event_digest for event in events]

    if len(set(event_ids)) != len(event_ids):
        quarantine_reasons.add("source_events_duplicate")
    if len(set(event_digests)) != len(event_digests):
        quarantine_reasons.add("source_event_digests_duplicate")

    conflict_labels: dict[str, set[str]] = {}
    for event in events:
        if not event.event_id.strip():
            quarantine_reasons.add("source_event_id_missing")
        if not event.tenant_id.strip() or event.tenant_id != policy.tenant_id:
            quarantine_reasons.add("cross_tenant_source")
        if event.window_id != policy.window_id:
            quarantine_reasons.add("source_window_mismatch")
        if event.source_kind not in policy.allowed_source_kinds:
            quarantine_reasons.add("source_kind_not_allowed")
        if event.consent_scope != policy.required_consent_scope:
            quarantine_reasons.add("consent_scope_missing")
        if not _valid_digest(event.event_digest) or not _valid_digest(event.label_digest):
            quarantine_reasons.add("source_digest_invalid")

        if event.quality_status == "accepted":
            if not _valid_digest(event.quality_receipt_digest):
                unknown_reasons.add("source_quality_unknown")
        elif event.quality_status == "quarantined":
            quarantine_reasons.add("source_quality_quarantined")
        else:
            unknown_reasons.add("source_quality_unknown")

        if policy.reject_poisoning_markers and event.poisoning_marker:
            quarantine_reasons.add("poisoning_marker_declared")
        if event.conflict_group:
            conflict_labels.setdefault(event.conflict_group, set()).add(event.label_digest)

    if any(len(labels) > 1 for labels in conflict_labels.values()):
        quarantine_reasons.add("conflicting_labels")

    all_reasons = quarantine_reasons | unknown_reasons
    if quarantine_reasons:
        return SourceAdmissionDecision(
            "quarantined", _sorted_reasons(all_reasons), None
        )
    if unknown_reasons:
        return SourceAdmissionDecision("unknown", _sorted_reasons(all_reasons), None)

    admitted_events = tuple(
        AdmittedSourceEvent(
            event_id=event.event_id,
            event_digest=event.event_digest,
            label_digest=event.label_digest,
            quality_receipt_digest=event.quality_receipt_digest,
        )
        for event in sorted(events, key=lambda item: item.event_id)
    )
    return SourceAdmissionDecision(
        "accepted",
        (),
        AdmittedUpdateData(
            tenant_id=policy.tenant_id,
            window_id=policy.window_id,
            source_events=admitted_events,
        ),
    )


def export_admission_bundle(decision: SourceAdmissionDecision) -> dict[str, object]:
    """Export a digest-bound, raw-content-free admission result."""

    unsigned = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "status": decision.status,
        "reasons": list(decision.reasons),
        "admitted_event_ids": list(decision.admitted_event_ids),
        "update_data": (
            decision.admitted_update_data.payload()
            if decision.admitted_update_data is not None
            else None
        ),
    }
    return {**unsigned, "bundle_sha256": _canonical_digest(unsigned)}


def validate_admission_bundle(bundle: dict[str, object]) -> None:
    """Validate outer and nested digests before a caller feeds V19."""

    if bundle.get("state_slice") != STATE_SLICE:
        raise SourceAdmissionError("state_slice_invalid")
    if bundle.get("claim_ceiling") != CLAIM_CEILING:
        raise SourceAdmissionError("claim_ceiling_invalid")

    provided_bundle_digest = bundle.get("bundle_sha256")
    unsigned = {key: value for key, value in bundle.items() if key != "bundle_sha256"}
    if not _valid_digest(provided_bundle_digest) or provided_bundle_digest != _canonical_digest(
        unsigned
    ):
        raise SourceAdmissionError("bundle_digest_invalid")

    status = bundle.get("status")
    if status not in ADMISSION_STATUSES:
        raise SourceAdmissionError("status_invalid")
    reasons = bundle.get("reasons")
    admitted_event_ids = bundle.get("admitted_event_ids")
    if not isinstance(reasons, list) or any(not isinstance(reason, str) for reason in reasons):
        raise SourceAdmissionError("reasons_invalid")
    if not isinstance(admitted_event_ids, list) or any(
        not isinstance(event_id, str) for event_id in admitted_event_ids
    ):
        raise SourceAdmissionError("admitted_event_ids_invalid")

    update_data = bundle.get("update_data")
    if status == "accepted":
        if reasons or not isinstance(update_data, dict):
            raise SourceAdmissionError("accepted_bundle_invalid")
        _validate_update_data(update_data, admitted_event_ids)
    elif update_data is not None or admitted_event_ids:
        raise SourceAdmissionError("nonaccepted_bundle_contains_update_data")


def _validate_update_data(
    update_data: dict[str, object], admitted_event_ids: list[object]
) -> None:
    if update_data.get("state_slice") != STATE_SLICE:
        raise SourceAdmissionError("update_data_state_slice_invalid")
    if update_data.get("claim_ceiling") != CLAIM_CEILING:
        raise SourceAdmissionError("update_data_claim_ceiling_invalid")
    tenant_id = update_data.get("tenant_id")
    window_id = update_data.get("window_id")
    source_events = update_data.get("source_events")
    update_data_digest = update_data.get("update_data_digest")
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        raise SourceAdmissionError("update_data_tenant_invalid")
    if not isinstance(window_id, str) or not window_id.strip():
        raise SourceAdmissionError("update_data_window_invalid")
    if not isinstance(source_events, list) or not source_events:
        raise SourceAdmissionError("update_data_events_invalid")
    if not _valid_digest(update_data_digest):
        raise SourceAdmissionError("update_data_digest_invalid")
    if admitted_event_ids != [
        event.get("event_id") for event in source_events if isinstance(event, dict)
    ]:
        raise SourceAdmissionError("admitted_event_ids_mismatch")

    unsigned = {
        key: value for key, value in update_data.items() if key != "update_data_digest"
    }
    if update_data_digest != _canonical_digest(unsigned):
        raise SourceAdmissionError("update_data_digest_invalid")
    for event in source_events:
        if not isinstance(event, dict):
            raise SourceAdmissionError("admitted_event_invalid")
        if set(event) != {
            "event_id",
            "event_digest",
            "label_digest",
            "quality_receipt_digest",
        }:
            raise SourceAdmissionError("admitted_event_shape_invalid")
        if not isinstance(event["event_id"], str) or not event["event_id"].strip():
            raise SourceAdmissionError("admitted_event_id_invalid")
        for key in ("event_digest", "label_digest", "quality_receipt_digest"):
            if not _valid_digest(event[key]):
                raise SourceAdmissionError("admitted_event_digest_invalid")
