import hashlib
import json
from dataclasses import replace

import pytest

from experiments.continual_learning.source_admission import (
    CLAIM_CEILING,
    STATE_SLICE,
    SourceAdmissionError,
    SourceAdmissionPolicy,
    SourceEvent,
    admit_source_events,
    export_admission_bundle,
    validate_admission_bundle,
)
from experiments.continual_learning.update_governance import (
    CanaryReport,
    SafetyReport,
    UpdateCandidate,
    UtilityReport,
    evaluate_candidate,
)


def _event(
    event_id: str = "event-001",
    *,
    tenant_id: str = "tenant-a",
    label_digest: str = "b" * 64,
    **overrides: object,
) -> SourceEvent:
    event = SourceEvent(
        event_id=event_id,
        tenant_id=tenant_id,
        source_kind="declared_user",
        event_digest="a" * 64,
        label_digest=label_digest,
        quality_status="accepted",
        quality_receipt_digest="c" * 64,
        consent_scope="tenant-training-opt-in-v1",
        window_id="window-001",
    )
    return replace(event, **overrides)


def _policy() -> SourceAdmissionPolicy:
    return SourceAdmissionPolicy(tenant_id="tenant-a", window_id="window-001")


def test_clean_events_are_admitted_deterministically_and_feed_v19() -> None:
    first = _event()
    second = _event(
        "event-002",
        label_digest="d" * 64,
        event_digest="e" * 64,
        quality_receipt_digest="f" * 64,
    )

    forward = admit_source_events((first, second), _policy())
    reversed_input = admit_source_events((second, first), _policy())

    assert forward.status == "accepted"
    assert forward.reasons == ()
    assert forward.update_data_digest is not None
    assert forward.update_data_digest == reversed_input.update_data_digest
    assert forward.admitted_event_ids == ("event-001", "event-002")

    candidate = UpdateCandidate(
        candidate_id="candidate-001",
        tenant_id="tenant-a",
        parent_model_id="model-parent",
        parent_model_digest="1" * 64,
        candidate_model_id="model-candidate",
        candidate_model_digest="2" * 64,
        update_data_digest=forward.update_data_digest,
        source_event_ids=forward.admitted_event_ids,
        source_tenant_ids=("tenant-a", "tenant-a"),
        consent_scope="tenant-training-opt-in-v1",
        safety=SafetyReport(100, 100, 100, 100, 100, 100, 0),
        utility=UtilityReport(800, 800),
        canary=CanaryReport(10, 0, 0),
    )
    assert evaluate_candidate(candidate).status == "canary_eligible"


def test_unknown_quality_is_not_admitted() -> None:
    decision = admit_source_events(
        (_event(quality_status="unknown", quality_receipt_digest=None),),
        _policy(),
    )

    assert decision.status == "unknown"
    assert decision.reasons == ("source_quality_unknown",)
    assert decision.update_data_digest is None
    assert decision.admitted_event_ids == ()


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"tenant_id": "tenant-b"}, "cross_tenant_source"),
        ({"poisoning_marker": "declared-adversarial"}, "poisoning_marker_declared"),
        ({"quality_status": "quarantined"}, "source_quality_quarantined"),
        ({"consent_scope": "tenant-training-opt-out-v1"}, "consent_scope_missing"),
        ({"source_kind": "unverified_external"}, "source_kind_not_allowed"),
    ],
)
def test_adversarial_or_out_of_scope_events_are_quarantined(
    overrides: dict[str, object], reason: str
) -> None:
    decision = admit_source_events((_event(**overrides),), _policy())

    assert decision.status == "quarantined"
    assert reason in decision.reasons
    assert decision.update_data_digest is None


def test_duplicate_and_conflicting_events_fail_closed() -> None:
    duplicate = admit_source_events((_event(), _event("event-001")), _policy())
    conflicting = admit_source_events(
        (
            _event(conflict_group="conflict-001"),
            _event(
                "event-002",
                label_digest="d" * 64,
                event_digest="e" * 64,
                quality_receipt_digest="f" * 64,
                conflict_group="conflict-001",
            ),
        ),
        _policy(),
    )

    assert duplicate.status == "quarantined"
    assert "source_events_duplicate" in duplicate.reasons
    assert conflicting.status == "quarantined"
    assert conflicting.reasons == ("conflicting_labels",)


def test_duplicate_event_digests_are_not_replayed_under_new_ids() -> None:
    decision = admit_source_events(
        (_event(), _event("event-002", label_digest="d" * 64)), _policy()
    )

    assert decision.status == "quarantined"
    assert decision.reasons == ("source_event_digests_duplicate",)


def test_admitted_bundle_readback_rejects_tampering() -> None:
    decision = admit_source_events((_event(),), _policy())
    bundle = export_admission_bundle(decision)

    assert bundle["state_slice"] == STATE_SLICE
    assert bundle["claim_ceiling"] == CLAIM_CEILING
    validate_admission_bundle(bundle)

    tampered = dict(bundle)
    tampered_update = dict(bundle["update_data"])
    tampered_events = [dict(bundle["update_data"]["source_events"][0])]
    tampered_events[0]["label_digest"] = "d" * 64
    tampered_update["source_events"] = tampered_events
    tampered["update_data"] = tampered_update
    tampered["bundle_sha256"] = hashlib.sha256(
        json.dumps(
            {key: value for key, value in tampered.items() if key != "bundle_sha256"},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    with pytest.raises(SourceAdmissionError, match="update_data_digest_invalid"):
        validate_admission_bundle(tampered)


def test_quarantined_bundle_has_no_admissible_update_data() -> None:
    decision = admit_source_events((_event(poisoning_marker="marker"),), _policy())
    bundle = export_admission_bundle(decision)

    validate_admission_bundle(bundle)
    assert bundle["status"] == "quarantined"
    assert bundle["update_data"] is None
