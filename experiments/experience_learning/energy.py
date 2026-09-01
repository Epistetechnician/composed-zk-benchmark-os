"""Measured-energy ingestion and explicitly separate operation proxies.

State slice: ``oaklab-experience-learning-benchmark-v2``.  No joule value is
generated here.  A measurement must come from a defined hardware path and a
caller-custodied CSV receipt; operation counts remain a separate diagnostic.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class MeasuredEnergy:
    run_id: str
    hardware: str
    joules: float
    events: int
    source_sha256: str
    status: str = "measured"
    campaign_manifest_sha256: str | None = None
    matrix_digests: tuple[str, ...] = ()
    guard_result_digests: tuple[str, ...] = ()
    backend_result_digests: tuple[str, ...] = ()

    @property
    def joules_per_event(self) -> float:
        return self.joules / self.events

    @property
    def campaign_bound(self) -> bool:
        return bool(self.campaign_manifest_sha256 and self.matrix_digests and
                    self.guard_result_digests and self.backend_result_digests)


def campaign_binding_digest(
    matrix_digests: Sequence[str],
    guard_result_digests: Sequence[str],
    backend_result_digests: Sequence[str],
) -> str:
    """Digest the exact sealed campaign receipts bound to a joule trace."""
    payload = {
        "schema": "oaklab.experience-learning.energy-campaign.v2",
        "matrix_digests": list(matrix_digests),
        "guard_result_digests": list(guard_result_digests),
        "backend_result_digests": list(backend_result_digests),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _is_sha256(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_energy_csv(path: str, expected_sha256: str | None = None,
                    require_campaign_binding: bool = False) -> MeasuredEnergy:
    """Read one joule receipt and optionally require exact campaign binding."""
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    digest = _sha256(path)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError("energy receipt digest mismatch")
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"run_id", "hardware", "joules", "events"}
    if len(rows) != 1 or not required <= set(rows[0]):
        raise ValueError("energy receipt must contain one row and the required columns")
    row = rows[0]
    run_id, hardware = row["run_id"].strip(), row["hardware"].strip()
    if not run_id or not hardware:
        raise ValueError("run_id and hardware are required")
    try:
        joules = float(row["joules"])
        events = int(row["events"])
    except (TypeError, ValueError) as exc:
        raise ValueError("joules/events have invalid types") from exc
    if not math.isfinite(joules) or joules < 0 or events <= 0:
        raise ValueError("joules must be finite and non-negative; events must be positive")
    binding_fields = {
        "campaign_manifest_sha256", "matrix_digests_json",
        "guard_result_digests_json", "backend_result_digests_json",
    }
    present = binding_fields & set(row)
    if present and present != binding_fields:
        raise ValueError("energy receipt campaign binding is incomplete")
    campaign_manifest = None
    matrix_digests: tuple[str, ...] = ()
    guard_digests: tuple[str, ...] = ()
    backend_digests: tuple[str, ...] = ()
    if present == binding_fields:
        raw_manifest = row["campaign_manifest_sha256"].strip()
        raw_lists = [row[name].strip() for name in binding_fields if name != "campaign_manifest_sha256"]
        if not raw_manifest and not any(raw_lists):
            if require_campaign_binding:
                raise ValueError("campaign-bound energy receipt is required")
        else:
            campaign_manifest = raw_manifest
            try:
                matrix_digests = tuple(json.loads(row["matrix_digests_json"]))
                guard_digests = tuple(json.loads(row["guard_result_digests_json"]))
                backend_digests = tuple(json.loads(row["backend_result_digests_json"]))
            except (TypeError, json.JSONDecodeError) as error:
                raise ValueError("energy receipt campaign digest lists are invalid") from error
            if not campaign_manifest or not matrix_digests or not guard_digests or not backend_digests:
                raise ValueError("energy receipt campaign binding lists must be non-empty")
            if (not _is_sha256(campaign_manifest) or
                    not all(_is_sha256(value) for value in matrix_digests + guard_digests + backend_digests)):
                raise ValueError("energy receipt campaign digests must be SHA-256 values")
            if campaign_manifest != campaign_binding_digest(matrix_digests, guard_digests, backend_digests):
                raise ValueError("energy receipt campaign manifest digest mismatch")
    if require_campaign_binding and present != binding_fields:
        raise ValueError("campaign-bound energy receipt is required")
    return MeasuredEnergy(run_id, hardware, joules, events, digest, "measured",
                          campaign_manifest, matrix_digests, guard_digests, backend_digests)


def operation_energy_proxy(active_synaptic_ops: int, event_count: int) -> float:
    """Return operations per event; this is not a joule measurement."""
    if active_synaptic_ops < 0 or event_count <= 0:
        raise ValueError("operation counts must be non-negative with positive events")
    return float(active_synaptic_ops) / event_count
