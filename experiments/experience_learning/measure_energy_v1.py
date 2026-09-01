"""Convert a measured power trace into a digest-bound joule receipt.

State slice: ``oaklab-experience-learning-benchmark-v2``.

This tool does not estimate power from operations. It integrates a caller-
supplied trace of timestamped watts (trapezoidal rule) and writes the single
row consumed by :mod:`energy`. A trace collected with macOS ``powermetrics``
is the declared first hardware path; collection itself requires operator
privilege and is intentionally not attempted by this module.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Sequence

from .energy import _is_sha256, campaign_binding_digest


STATE_SLICE = "oaklab-experience-learning-benchmark-v2"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def integrate_power_watts(samples: Sequence[tuple[float, float]]) -> tuple[float, float]:
    """Return ``(joules, duration_seconds)`` for monotonic watt samples."""
    if len(samples) < 2:
        raise ValueError("power trace requires at least two samples")
    previous_time, previous_power = samples[0]
    if not math.isfinite(previous_time) or not math.isfinite(previous_power) or previous_power < 0:
        raise ValueError("power samples must be finite and non-negative")
    joules = 0.0
    for timestamp, power in samples[1:]:
        if not math.isfinite(timestamp) or not math.isfinite(power) or power < 0:
            raise ValueError("power samples must be finite and non-negative")
        interval = timestamp - previous_time
        if interval <= 0:
            raise ValueError("power timestamps must be strictly increasing")
        joules += interval * (previous_power + power) / 2.0
        previous_time, previous_power = timestamp, power
    return joules, samples[-1][0] - samples[0][0]


def read_power_trace(path: Path) -> list[tuple[float, float]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or not {"timestamp_s", "power_w"} <= set(rows[0]):
        raise ValueError("power trace requires timestamp_s,power_w columns")
    samples = []
    for row in rows:
        try:
            samples.append((float(row["timestamp_s"]), float(row["power_w"])))
        except (TypeError, ValueError) as error:
            raise ValueError("power trace contains non-numeric values") from error
    return samples


def write_receipt(
    output: Path,
    run_id: str,
    hardware: str,
    events: int,
    trace: Path,
    samples: Sequence[tuple[float, float]],
    campaign_manifest_sha256: str | None = None,
    matrix_digests: Sequence[str] = (),
    guard_result_digests: Sequence[str] = (),
    backend_result_digests: Sequence[str] = (),
) -> dict:
    if not run_id.strip() or not hardware.strip() or events <= 0:
        raise ValueError("run_id, hardware, and positive events are required")
    joules, duration_s = integrate_power_watts(samples)
    campaign_lists = (tuple(matrix_digests), tuple(guard_result_digests), tuple(backend_result_digests))
    if any(campaign_lists) and (not campaign_manifest_sha256 or not all(campaign_lists)):
        raise ValueError("campaign binding requires manifest, matrix, guard, and backend digests")
    if campaign_manifest_sha256 and (not _is_sha256(campaign_manifest_sha256) or
                                     not all(_is_sha256(value) for values in campaign_lists for value in values)):
        raise ValueError("campaign binding digests must be SHA-256 values")
    if campaign_manifest_sha256 and campaign_binding_digest(*campaign_lists) != campaign_manifest_sha256:
        raise ValueError("campaign manifest digest does not match bound receipts")
    row = {
        "run_id": run_id,
        "hardware": hardware,
        "joules": joules,
        "events": events,
        "trace_sha256": _sha256(trace),
        "sample_count": len(samples),
        "duration_s": duration_s,
        "state_slice": STATE_SLICE,
        "integration": "trapezoidal_watts_over_timestamp_s",
    }
    if campaign_manifest_sha256:
        row.update({
            "campaign_manifest_sha256": campaign_manifest_sha256,
            "matrix_digests_json": json.dumps(list(matrix_digests), separators=(",", ":")),
            "guard_result_digests_json": json.dumps(list(guard_result_digests), separators=(",", ":")),
            "backend_result_digests_json": json.dumps(list(backend_result_digests), separators=(",", ":")),
        })
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    row["receipt_sha256"] = _sha256(output)
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--hardware", default="macos:powermetrics:cpu_power")
    parser.add_argument("--events", type=int, required=True)
    parser.add_argument("--campaign-manifest-sha256")
    parser.add_argument("--matrix-digest", action="append", default=[])
    parser.add_argument("--guard-result-digest", action="append", default=[])
    parser.add_argument("--backend-result-digest", action="append", default=[])
    args = parser.parse_args()
    receipt = write_receipt(
        args.output, args.run_id, args.hardware, args.events, args.trace, read_power_trace(args.trace),
        args.campaign_manifest_sha256, args.matrix_digest, args.guard_result_digest,
        args.backend_result_digest,
    )
    print(json.dumps(receipt, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
